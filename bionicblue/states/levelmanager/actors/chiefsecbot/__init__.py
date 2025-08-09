"""Facility for chief security bot boss."""

### standard library import
from functools import partial


### third-party import
from pygame.math import Vector2


### local imports

from .....config import REFS

from .....pygamesetup.constants import GENERAL_NS, SCREEN_RECT, msecs_to_frames

from .....ani2d.player import AnimationPlayer2D

from .....ourstdlibs.behaviour import do_nothing

from ...frontprops.defaultexplosion import DefaultExplosion

from ...common import (
    remove_obj,
    FRONT_PROPS,
    PROJECTILES,
    BLOCKS_NEAR_SCREEN,
    append_task,
)

from .healthcolumn import HealthColumn

from .projectiles.fallingcrate import FallingCrate



_HURT_WHITENING_MSECS = 2000
HURT_WHITENING_FRAMES = msecs_to_frames(_HURT_WHITENING_MSECS)

WHITENING_CYCLE = (
  *('whitened',)*2,
  *('default',)*3,
)

_CRATE_PUNCH_WAIT_MSECS = 50
CRATE_PUNCH_WAIT_FRAMES = msecs_to_frames(_CRATE_PUNCH_WAIT_MSECS)

CRATE_PUNCH_ANIM_NAMES = frozenset(('punch_left', 'punch_right'))


class ChiefSecurityBot:

    def __init__(self, name, pos, facing_right=False):

        self.health_column = HealthColumn()

        self.player = REFS.states.level_manager.player

        self.name = name

        self.x_speed = 0

        animation_name = 'idle_right' if facing_right else 'idle_left'

        self.aniplayer = (
            AnimationPlayer2D(
                self, name, animation_name, 'bottomright', pos+Vector2(-12, 0),
            )
        )

        self.last_damage = GENERAL_NS.frame_index
        self.routine_check = do_nothing
        self.update = self.idle_update

        REFS.level_boss = self

    @property
    def health(self):
        return self.health_column.health

    def begin_fighting(self):

        ap = self.aniplayer

        ap.switch_animation(
            'back_punch_left'
            if 'left' in ap.anim_name
            else 'back_punch_right'
        )

        self.update = self.punch_wall

    def idle_update(self):

        ap = self.aniplayer

        ###

        if self.rect.colliderect(self.player.rect):
            self.player.damage(3)

        self.routine_check()

    def punch_wall(self):

        ap = self.aniplayer

        if ap.get_current_loops_no() == 1:

            ap.switch_animation(
                'idle_left'
                if 'left' in ap.anim_name
                else 'idle_right'
            )

            _arena_area = SCREEN_RECT.inflate((-16 * 2), 0)
            right = _arena_area.right

            x = _arena_area.left + 8
            y = SCREEN_RECT.top + -12

            while x < right:

                PROJECTILES.add(
                    FallingCrate((x, y))
                )

                x += 32

            ap.switch_animation(
                'punch_left'
                if 'left' in ap.anim_name
                else 'punch_right'
            )

            self.update = self.punch_crate_update

            return

        if self.rect.colliderect(self.player.rect):
            self.player.damage(3)

        self.routine_check()

    def punch_crate_update(self):

        ap = self.aniplayer

        if ap.anim_name in CRATE_PUNCH_ANIM_NAMES:

            if ap.get_current_loops_no() == 1:

                ap.switch_animation(
                    'back_punch_left'
                    if 'left' in ap.anim_name
                    else 'back_punch_right'
                )

                self.update = self.punch_wall
                return

        if self.rect.colliderect(self.player.rect):
            self.player.damage(3)

        self.routine_check()

    def check_damage_whitening(self):

        if (
            GENERAL_NS.frame_index - self.last_damage
            > HURT_WHITENING_FRAMES
        ):

            self.aniplayer.restore_surface_cycling()
            self.routine_check = do_nothing

    def draw(self):
        self.aniplayer.draw()

    def damage(self, amount):

        if (
            GENERAL_NS.frame_index - self.last_damage
            > HURT_WHITENING_FRAMES
        ):

            self.health_column.damage(amount)
            self.last_damage = GENERAL_NS.frame_index

            if self.health_column.is_depleted():

                center = self.rect.center

                FRONT_PROPS.add(DefaultExplosion('center', center))
                append_task(partial(remove_obj, self))

            else:
                self.aniplayer.set_custom_surface_cycling(WHITENING_CYCLE)
                self.routine_check = self.check_damage_whitening

### XXX backed up code
#
#        rect = self.rect
#        center = rect.center
#
#        x_speed = self.x_speed
#        colliderect = rect.colliderect
#
#        rect.move_ip(x_speed, 0)
#
#        for block in BLOCKS_NEAR_SCREEN:
#
#            if colliderect(block.rect):
#
#                if x_speed > 0:
#                    rect.right = block.rect.left
#                    self.aniplayer.switch_animation('idle_left')
#
#                else:
#                    rect.left = block.rect.right
#                    self.aniplayer.switch_animation('idle_right')
#
#                self.x_speed = -x_speed
#
#                break
#
#        else:
#
#            rect.move_ip(0, 1)
#
#            if not any(
#                colliderect(block.rect)
#                for block in BLOCKS_NEAR_SCREEN
#            ):
#
#                if x_speed > 0:
#                    self.aniplayer.switch_animation('idle_left')
#                else:
#                    self.aniplayer.switch_animation('idle_right')
#
#                self.x_speed = -x_speed
#                rect.move_ip(-x_speed, -1)
#
#            else:
#                rect.move_ip(0, -1)

