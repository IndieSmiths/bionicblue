"""Facility for grunt bot enemy."""

### standard library import
from functools import partial


### local imports

from ....config import REFS

from ....pygamesetup.constants import GENERAL_NS

from ....constants import DAMAGE_WHITENING_FRAMES

from ....ani2d.player import AnimationPlayer2D

from ....ourstdlibs.behaviour import do_nothing

from ..frontprops.defaultexplosion import DefaultExplosion

from ..common import (
    remove_obj,
    FRONT_PROPS,
    BLOCKS_ON_SCREEN,
    append_task,
)



WALK_SPEED = 1
FLOOR_CHECK = 10


class GruntBot:

    def __init__(self, name, pos):

        self.health = 5

        self.player = REFS.states.level_manager.player

        self.name = name

        self.x_speed = -WALK_SPEED

        self.aniplayer = (
            AnimationPlayer2D(
                self, name, 'idle_left', 'midbottom', pos
            )
        )

        self.last_damage = GENERAL_NS.frame_index
        self.routine_check = do_nothing

    def update(self):
        rect = self.rect
        tl = rect.topleft

        x_speed = self.x_speed
        colliderect = rect.colliderect

        rect.move_ip(x_speed, 0)

        for block in BLOCKS_ON_SCREEN:

            if colliderect(block.rect):

                if x_speed > 0:
                    rect.right = block.rect.left
                    self.aniplayer.switch_animation('idle_left')

                else:
                    rect.left = block.rect.right
                    self.aniplayer.switch_animation('idle_right')

                self.x_speed = -x_speed

                break

        else:

            rect.move_ip(0, 1)

            if not any(
                colliderect(block.rect)
                for block in BLOCKS_ON_SCREEN
            ):

                if x_speed > 0:
                    self.aniplayer.switch_animation('idle_left')
                else:
                    self.aniplayer.switch_animation('idle_right')

                self.x_speed = -x_speed
                rect.move_ip(-x_speed, -1)

            else:
                rect.move_ip(0, -1)


        ###

        if colliderect(self.player.rect):
            self.player.damage(3)

        self.routine_check()

        ###
        if rect.topleft != tl:

            self.delta += tuple(
                a - b
                for a, b
                in zip(rect.topleft, tl)
            )

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
