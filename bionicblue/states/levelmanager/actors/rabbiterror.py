"""Facility for grunt bot enemy."""

### standard library import

from itertools import cycle
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



Y_ACCEL = 5
JUMP_DY = -15
X_SPEED = 8


class Rabbiterror:

    def __init__(self, name, pos, facing_right=False):

        self.must_jump = cycle((1,) + (0,) * 15).__next__

        self.health = 5

        self.player = REFS.states.level_manager.player

        self.name = name

        self.x_speed = 0
        self.y_speed = 0

        animation_name = 'idle_right' if facing_right else 'idle_left'

        self.aniplayer = (
            AnimationPlayer2D(
                self, name, animation_name, 'midbottom', pos
            )
        )

        self.last_damage = GENERAL_NS.frame_index
        self.routine_check = do_nothing

    def update(self):

        center = self.rect.center

        ap = self.aniplayer
        anim_name = ap.anim_name

        if 'jump' in anim_name:
            self.y_speed = min(self.y_speed + Y_ACCEL, Y_ACCEL)

        elif self.must_jump():

            self.x_speed = X_SPEED if anim_name == 'idle_right' else -X_SPEED
            self.y_speed = JUMP_DY

            ap.switch_animation(

                'jump_right'
                if anim_name == 'idle_right'

                else 'jump_left'

            )

        self.rect.move_ip(self.x_speed, 0)

        colliderect = self.rect.colliderect

        for block in BLOCKS_ON_SCREEN:

            if colliderect(block.rect):

                if self.x_speed > 0:
                    ap.switch_animation('jump_left')
                    self.rect.right = block.rect.left

                else:
                    ap.switch_animation('jump_right')
                    self.rect.left = block.rect.right

                self.x_speed = -self.x_speed

                break

        self.rect.move_ip(0, self.y_speed)

        colliderect = self.rect.colliderect

        for block in BLOCKS_ON_SCREEN:

            if colliderect(block.rect):

                if self.y_speed < 0:
                    self.rect.top = block.rect.bottom

                else:

                    ap.switch_animation(
                        'idle_right'
                        if ap.anim_name == 'jump_right'
                        else 'idle_left'
                    )

                    self.rect.bottom = block.rect.top

                    self.x_speed = 0

                self.y_speed = 0

                break

        ###

        if self.rect.colliderect(self.player.rect):
            self.player.damage(3)

        self.routine_check()

        ###

        if self.rect.center != center:

            self.delta += tuple(
                a - b
                for a, b
                in zip(self.rect.center, center)
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
