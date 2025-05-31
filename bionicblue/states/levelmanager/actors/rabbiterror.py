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


class Rabbiterror:

    def __init__(self, name, pos, facing_right=False):

        self.must_jump = cycle((1,) + (0,) * 30).__next__

        self.health = 5

        self.player = REFS.states.level_manager.player

        self.name = name

        self.x_speed = 3 if facing_right else -3
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

        rect = self.rect
        mb = rect.midbottom

        colliderect = rect.colliderect

        ap = self.aniplayer
        anim_name = ap.anim_name

        if anim_name == 'idle_right':

            if self.must_jump():

                self.y_speed = JUMP_DY
                ap.switch_animation('jump_right')

        elif anim_name == 'idle_left':

            if self.must_jump():
                self.y_speed = JUMP_DY
                ap.switch_animation('jump_left')

        else:
            self.y_speed = min(self.y_speed + Y_ACCEL, Y_ACCEL)

        rect.move_ip(self.x_speed, 0)

        for block in BLOCKS_ON_SCREEN:

            if colliderect(block.rect):

                if self.x_speed > 0:
                    rect.right = block.rect.left
                    ap.switch_animation('jump_left')

                else:
                    rect.left = block.rect.right
                    ap.switch_animation('jump_right')

                self.x_speed = -self.x_speed

                break

        rect.move_ip(0, self.y_speed)

        for block in BLOCKS_ON_SCREEN:

            if colliderect(block.rect):

                if self.y_speed < 0:
                    rect.top = block.rect.bottom

                else:
                    rect.bottom = block.rect.top

                    ap.switch_animation(
                        'idle_right'
                        if ap.anim_name == 'jump_right'
                        else 'idle_left'
                    )

                self.y_speed = 0

                break

        ###

        if colliderect(self.player.rect):
            self.player.damage(3)

        self.routine_check()

        ###

        if rect.midbottom != mb:

            self.delta += tuple(
                a - b
                for a, b
                in zip(rect.midbottom, mb)
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
