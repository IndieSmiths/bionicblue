"""Facility for chief security bot boss."""

### standard library imports

from functools import partial

from math import inf as INFINITY


### third-party import

from pygame import Rect

from pygame.math import Vector2


### local imports

from .....config import REFS, SOUND_MAP

from .....constants import GRAVITY_ACCEL

from .....pygamesetup.constants import GENERAL_NS, SCREEN_RECT, msecs_to_frames

from .....ani2d.player import AnimationPlayer2D

from .....ourstdlibs.behaviour import do_nothing

from ...frontprops.defaultexplosion import DefaultExplosion

from ...common import (
    remove_obj,
    FRONT_PROPS,
    PROJECTILES,
    BLOCKS_NEAR_SCREEN,
)

from ...taskmgmt import append_ready_task

from .healthcolumn import HealthColumn

from .projectiles.fallingcrate import FallingCrate
from .projectiles.electricglobe import ElectricGlobe



_HURT_WHITENING_MSECS = 2000
HURT_WHITENING_FRAMES = msecs_to_frames(_HURT_WHITENING_MSECS)

WHITENING_CYCLE = (
  *('whitened',)*2,
  *('default',)*3,
)

_CRATE_PUNCH_WAIT_MSECS = 34
CRATE_PUNCH_WAIT_FRAMES = msecs_to_frames(_CRATE_PUNCH_WAIT_MSECS)

CRATE_PUNCH_ANIM_NAMES = frozenset(('punch_left', 'punch_right'))

CRATE_FALL_AREA = Rect(0, 0, 96, 16)

OPEN_OVERHEAD_AREA = SCREEN_RECT.inflate((-16 * 2), 0)
OPEN_OVERHEAD_AREA.height = 96

CRATE_FALL_AREA.bottom = OPEN_OVERHEAD_AREA.bottom = SCREEN_RECT.top

CRATE_RECT = Rect(0, 0, 16, 16)

BOSS_MAX_Y_SPEED = 6

_SHOOT_WAIT_MSECS = 230
SHOOT_WAIT_FRAMES = msecs_to_frames(_SHOOT_WAIT_MSECS)

_HOLD_MSECS = 400
HOLD_FRAMES = msecs_to_frames(_HOLD_MSECS)

_IDLE_MSECS = 400
IDLE_FRAMES = msecs_to_frames(_IDLE_MSECS)


class ChiefSecurityBot:

    def __init__(self, name, pos, facing_right=False):

        self.health_column = HealthColumn()

        self.player = REFS.states.level_manager.player

        self.name = name

        self.x_speed = self.y_speed = 0

        self.punch_countdown = 0
        self.no_of_punched_crates = 0
        self.shoot_countdown = 0
        self.did_run_into_player = False

        animation_name = 'idle_right' if facing_right else 'idle_left'

        self.aniplayer = (
            AnimationPlayer2D(
                self, name, animation_name, 'bottomright', pos+Vector2(-12, 0),
            )
        )

        # last_damage is set to negative infinity so that the first damage is
        # always triggered (check self.damage() method to understand)
        self.last_damage = -INFINITY

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
        player = self.player

        if 'left' in ap.anim_name:

            if (
                player.rect.centerx > self.rect.centerx
                and player.rect.bottom == self.rect.bottom
            ):

                self.update = self.grab
                ap.switch_animation('grab_left')

                self.routine_check()
                return

        elif (
            self.player.rect.centerx < self.rect.centerx
            and player.rect.bottom == self.rect.bottom
        ):

            self.update = self.grab
            ap.switch_animation('grab_right')

            self.routine_check()
            return

        if ap.peek_loops_no(6) == 1:

            SOUND_MAP['chief_sec_bot_wall_punch.wav'].play()

            orientation = 'left' if 'left' in ap.anim_name else 'right'

            ###

            crate_to_punch_x = (
                self.rect.left - 15
                if orientation == 'left'
                else self.rect.right + 15
            )

            y = SCREEN_RECT.top

            PROJECTILES.add(FallingCrate((crate_to_punch_x, y)))

            ###

            player_centerx = self.player.rect.centerx

            CRATE_FALL_AREA.centerx = player_centerx

            clamped_fall_area = CRATE_FALL_AREA.clamp(OPEN_OVERHEAD_AREA)

            is_near_wall = clamped_fall_area != CRATE_FALL_AREA

            if is_near_wall:
                CRATE_FALL_AREA.topleft = clamped_fall_area.topleft

            is_near_boss = False

            if orientation == 'left':

                right_boundary = self.rect.left - 30

                if CRATE_FALL_AREA.right > right_boundary:
                    CRATE_FALL_AREA.right = right_boundary
                    is_near_boss = True

            else:

                left_boundary = self.rect.right + 30

                if CRATE_FALL_AREA.left < left_boundary:
                    CRATE_FALL_AREA.left = left_boundary
                    is_near_boss = True

            ###

            if is_near_boss:

                CRATE_RECT.centerx = player_centerx
                CRATE_RECT.clamp_ip(CRATE_FALL_AREA)

                x1 = CRATE_RECT.centerx
                x2 = x1 + (-40 if orientation == 'left' else 40)
                x3 = x2 + (-40 if orientation == 'left' else 40)

                xs = (x1, x2, x3)

            elif is_near_wall:

                CRATE_RECT.centerx = player_centerx
                CRATE_RECT.clamp_ip(CRATE_FALL_AREA)

                x1 = CRATE_RECT.centerx

                x2 = x1 + (40 if orientation == 'left' else -40)
                x3 = x2 + (40 if orientation == 'left' else -40)

                xs = (x1, x2, x3)

            else:

                p_x_speed = self.player.x_speed

                if (
                    p_x_speed > 0
                    and abs(
                        CRATE_FALL_AREA.right + 32 - self.rect.centerx
                    ) > 40
                ):

                    xs = (
                        CRATE_FALL_AREA.left + 8,
                        CRATE_FALL_AREA.centerx,
                        CRATE_FALL_AREA.right - 8,
                        CRATE_FALL_AREA.right + 32,
                    )

                elif (
                    p_x_speed < 0
                    and abs(
                        CRATE_FALL_AREA.left - 32 - self.rect.centerx
                    ) > 40
                ):

                    xs = (
                        CRATE_FALL_AREA.left - 32,
                        CRATE_FALL_AREA.left + 8,
                        CRATE_FALL_AREA.centerx,
                        CRATE_FALL_AREA.right - 8,
                    )

                else:

                    xs = (
                        CRATE_FALL_AREA.left + 8,
                        CRATE_FALL_AREA.centerx,
                        CRATE_FALL_AREA.right - 8,
                    )

            for x in xs:
                PROJECTILES.add(FallingCrate((x, y)))

        elif ap.peek_loops_no(1) == 1:

            ap.switch_animation(
                'idle_left'
                if 'left' in ap.anim_name
                else 'idle_right'
            )

            self.punch_countdown = CRATE_PUNCH_WAIT_FRAMES
            self.update = self.punch_crate_update

        if self.rect.colliderect(self.player.rect):
            self.player.damage(3)

        self.routine_check()

    def punch_crate_update(self):

        ap = self.aniplayer
        player = self.player

        if 'left' in ap.anim_name:

            if (
                player.rect.centerx > self.rect.centerx
                and player.rect.bottom == self.rect.bottom
            ):

                self.update = self.grab
                ap.switch_animation('grab_left')

                self.routine_check()
                #self.no_of_punched_crates = 0
                return

        elif (
            self.player.rect.centerx < self.rect.centerx
            and player.rect.bottom == self.rect.bottom
        ):

            self.update = self.grab
            ap.switch_animation('grab_right')

            self.routine_check()
            #self.no_of_punched_crates = 0
            return

        if ap.anim_name in CRATE_PUNCH_ANIM_NAMES:

            if ap.peek_loops_no(8) == 1:
                SOUND_MAP['chief_sec_bot_crate_punch.wav'].play()

            if ap.get_current_loops_no() == 1:

                self.no_of_punched_crates += 1

                if self.no_of_punched_crates == 3:

                    self.no_of_punched_crates = 0

                    health_percentage = (
                        self.health_column.get_health_percentage()
                    )

                    if health_percentage <= .4:

                        if 'left' in ap.anim_name:

                            ap.switch_animation('run_left')
                            self.x_speed = -7

                        else:
                            ap.switch_animation('run_right')
                            self.x_speed = 7

                        self.update = self.run

                    elif health_percentage <= .7:

                        y = self.rect.centery - 4

                        if 'left' in ap.anim_name:

                            ap.switch_animation('shoot_left')
                            x = self.rect.left - 7
                            PROJECTILES.add(ElectricGlobe((x, y), 'left'))

                        else:

                            ap.switch_animation('shoot_right')
                            x = self.rect.right + 7
                            PROJECTILES.add(ElectricGlobe((x, y), 'right'))

                        self.shoot_countdown = SHOOT_WAIT_FRAMES
                        self.update = self.shoot

                    else:

                        if 'left' in ap.anim_name:

                            ap.switch_animation('jump_left')
                            self.x_speed = -7

                        else:

                            ap.switch_animation('jump_right')
                            self.x_speed = 7

                        self.y_speed = -24

                        self.update = self.jump_to_opposite_side

                else:

                    ap.switch_animation(
                        'back_punch_left'
                        if 'left' in ap.anim_name
                        else 'back_punch_right'
                    )

                    self.update = self.punch_wall

        elif self.punch_countdown > 0:
            self.punch_countdown -= 1

        elif self.punch_countdown == 0:

            ap.switch_animation(
                'punch_left'
                if 'left' in ap.anim_name
                else 'punch_right'
            )

        if self.rect.colliderect(self.player.rect):
            self.player.damage(3)

        self.routine_check()

    def jump_to_opposite_side(self):

        y_speed = self.y_speed
        y_speed = min(y_speed + GRAVITY_ACCEL, BOSS_MAX_Y_SPEED)
        self.y_speed = y_speed

        rect = self.rect
        rect.move_ip(self.x_speed, self.y_speed)

        for block in BLOCKS_NEAR_SCREEN:

            if block.colliderect(rect):
                
                self.x_speed = self.y_speed = 0
                rect.bottom = block.rect.top

                ap = self.aniplayer

                ap.switch_animation(
                    'back_punch_right'
                    if 'left' in ap.anim_name
                    else 'back_punch_left'
                )

                self.update = self.punch_wall

                break

        if rect.colliderect(self.player.rect):
            self.player.damage(3)

        self.routine_check()

    def shoot(self):

        if self.shoot_countdown == 0:

            ap = self.aniplayer

            if 'left' in ap.anim_name:

                ap.switch_animation('jump_left')
                self.x_speed = -7

            else:

                ap.switch_animation('jump_right')
                self.x_speed = 7

            self.y_speed = -24

            self.update = self.jump_to_opposite_side

        else:
            self.shoot_countdown -= 1

        if self.rect.colliderect(self.player.rect):
            self.player.damage(3)

        self.routine_check()

    def run(self):

        rect = self.rect

        rect.move_ip(self.x_speed, 0)

        for block in BLOCKS_NEAR_SCREEN:

            if block.colliderect(rect):

                if self.x_speed < 0:

                    rect.left = block.rect.right + 10
                    self.aniplayer.switch_animation('back_punch_right')

                else:

                    rect.right = block.rect.left - 10
                    self.aniplayer.switch_animation('back_punch_left')

                self.x_speed = 0
                self.update = self.punch_wall

                break


        if (
            not self.did_run_into_player
            and self.rect.colliderect(self.player.rect)
        ):

            if 'left' in self.aniplayer.anim_name:
                self.player.be_hurled(-10, -2)

            else:
                self.player.be_hurled(10, -2)

            self.did_run_into_player = True

        self.routine_check()

        if self.update == self.punch_wall:
            self.did_run_into_player = False

    def grab(self):

        ap = self.aniplayer

        if 'grab' in ap.anim_name:

            if ap.get_current_frame() == 3:

                self.player.be_grabbed()

                if 'left' in ap.anim_name:
                    self.player.rect.midbottom = self.rect.move(8, 0).bottomright

                else:
                    self.player.rect.midbottom = self.rect.move(-8, 0).bottomleft

            elif ap.peek_loops_no(1) == 1:
                
                if 'left' in ap.anim_name:
                    ap.switch_animation('hold_left')
                    self.player.rect.center = self.rect.move(8, -2).topright

                else:
                    ap.switch_animation('hold_right')
                    self.player.rect.center = self.rect.move(-8, -2).topleft

                self.hold_countdown = HOLD_FRAMES

        elif 'hold' in ap.anim_name:

            self.hold_countdown -= 1

            if self.hold_countdown == 0:

                ap.switch_animation(
                    'throw_left'
                    if 'left' in ap.anim_name
                    else 'throw_right'
                )

        elif 'throw' in ap.anim_name:

            if ap.get_current_frame() == 8:

                player = self.player

                if 'left' in ap.anim_name:

                    player.be_hurled(-10, 0)
                    player.rect.midright = self.rect.move(0, -5).midleft

                else:

                    player.be_hurled(10, 0)
                    player.rect.midleft = self.rect.move(0, -5).midright

            elif ap.get_current_loops_no() == 1:

                ap.switch_animation(
                    'idle_left'
                    if 'left' in ap.anim_name
                    else 'idle_right'
                )

                self.idle_countdown = IDLE_FRAMES

        elif 'idle' in ap.anim_name:

            self.idle_countdown -= 1

            if self.idle_countdown == 0:

                ap.switch_animation(
                    'back_punch_left'
                    if 'left' in ap.anim_name
                    else 'back_punch_right'
                )

                self.update = self.punch_wall

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
                append_ready_task(partial(remove_obj, self))

                REFS.states.level_manager.save_beaten_boss('chief_sec_bot')

            else:
                self.aniplayer.set_custom_surface_cycling(WHITENING_CYCLE)
                self.routine_check = self.check_damage_whitening
