"""Facility for watcher bot enemy."""

### standard library import
from functools import partial


### local imports

from .....config import REFS

from .....pygamesetup.constants import GENERAL_NS, msecs_to_frames

from .....constants import DAMAGE_WHITENING_FRAMES

from .....ani2d.player import AnimationPlayer2D

from .....ourstdlibs.behaviour import do_nothing
from .....ourstdlibs.mathutils import get_straight_distance

from ...frontprops.defaultexplosion import DefaultExplosion

from ...common import (
    remove_obj,
    append_task,
    PROJECTILES,
    FRONT_PROPS,
)

from .shot import WatcherShot



_MSECS_BEFORE_SHOOTING = 1500
FRAME_COUNT_BEFORE_SHOOTING = msecs_to_frames(_MSECS_BEFORE_SHOOTING)

class WatcherBot:

    def __init__(self, name, pos):

        self.health = 3

        self.player = REFS.states.level_manager.player

        self.name = name

        self.aniplayer = (
            AnimationPlayer2D(
                self, name, 'idle', 'center', pos
            )
        )

        self.last_damage = GENERAL_NS.frame_index
        self.routine_check = do_nothing
        self.shooting_countdown = 0

    def update(self):

        ap = self.aniplayer

        ###

        player = self.player

        ###
        center = self.rect.center
        pcenter = player.rect.center

        dist = get_straight_distance(center, pcenter)

        if dist > 144:
            ap.ensure_animation('idle')

        else:

            if ap.anim_name == 'idle':

                ap.switch_animation('preparing_shot')
                self.shooting_countdown = FRAME_COUNT_BEFORE_SHOOTING

            if self.shooting_countdown:
                self.shooting_countdown -= 1

            else:

                ### TODO why considering when player is too close?
                ###
                ### if player is too close, maybe we should consider as though
                ### the shot will hit the player right away, but only if player
                ### can be hit (if player isn't semitransparent from being
                ### damaged recently)

                if dist < 6:
                    self.player.damage(3)

                else:

                    PROJECTILES.add(
                        WatcherShot(
                            watcher_center=center,
                            player_center=pcenter,
                        )
                    )

                    self.shooting_countdown = FRAME_COUNT_BEFORE_SHOOTING

        if self.rect.colliderect(self.player.rect):
            self.player.damage(3)

        self.routine_check()

    def check_damage_whitening(self):

        if (
            GENERAL_NS.frame_index - self.last_damage
            > DAMAGE_WHITENING_FRAMES
        ):

            self.aniplayer.restore_surface_cycling()
            self.routine_check = do_nothing

    def draw(self):
        self.aniplayer.draw()

    def damage(self, amount):

        self.health += -amount

        if self.health <= 0:

            center = self.rect.center

            FRONT_PROPS.add(DefaultExplosion('center', center))
            append_task(partial(remove_obj, self))

        else:
            self.aniplayer.set_custom_surface_cycling(('whitened', 'default'))
            self.routine_check = self.check_damage_whitening
