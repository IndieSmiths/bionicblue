"""Facility for Player class."""

### standard library imports

from itertools import chain

from math import inf as INFINITY

from collections import deque


### local imports

from ....config import REFS, SOUND_MAP

from ....constants import (
    GRAVITY_ACCEL,
    X_SPEED,
    MAX_Y_SPEED,
    DAMAGE_REBOUND_FRAMES,
    MIDDLE_CHARGE_FRAMES,
    FULL_CHARGE_FRAMES,
)

from ....pygamesetup.constants import (
    GENERAL_NS,
    SCREEN_RECT,
    SCREEN,
    blit_on_screen,
    msecs_to_frames,
)

from ....ourstdlibs.behaviour import do_nothing

## classes for composition

from ....ani2d.player import AnimationPlayer2D

from ..common import MIDDLE_PROPS_NEAR_SCREEN, BLOCKS_NEAR_SCREEN

from .healthcolumn import HealthColumn


## states

from .teleportingin import TeleportingIn
from .teleportingout import TeleportingOut

from .idleright import IdleRight
from .idleleft import IdleLeft

from .walkright import WalkRight
from .walkleft import WalkLeft

from .hurt import Hurt
from .dead import Dead

from .grabbed import Grabbed
from .hurled import Hurled

from .scriptedacting import ScriptedActing

## function
from .chargingparticles import draw_charging_particles



UNDAMAGEABLE_STATES = frozenset(('dead', 'grabbed'))
UNHURLEABLE_STATES = frozenset(('dead', 'hurled'))

class Player(
    TeleportingIn,
    TeleportingOut,
    IdleRight,
    IdleLeft,
    WalkRight,
    WalkLeft,
    Hurt,
    Dead,
    Grabbed,
    Hurled,
    ScriptedActing,
):

    def __init__(self):

        draw_charging_particles.player = self

        self.midair = False

        self.ladder = None

        self.death_rings_aniplayer = (
            AnimationPlayer2D(self, 'death_rings', 'expanding')
        )

        self.blue_shooter_man_aniplayer = (
            AnimationPlayer2D(
                self, 'blue_shooter_man', 'teleporting', 'center'
            )
        )

        ###
        self.draw_charging_fx = do_nothing

        ### set initial values for time tracking attributes
        self.reset_time_tracking_attributes()

        ###

        self.x_speed = 0
        self.y_speed = MAX_Y_SPEED
        self.y_accel = 10

        self.jump_dy = -15

        ###
        self.scripted_actions_deque = deque()

    def prepare(self):

        if not hasattr(self, 'health_column'):
            self.health_column = HealthColumn()

        self.y_speed = MAX_Y_SPEED

        self.aniplayer = self.blue_shooter_man_aniplayer
        self.rect = self.aniplayer.root.rect

        self.aniplayer.switch_animation('teleporting')
        self.set_state('teleporting_in')

    def set_state(self, state_name):

        self.state_name = state_name

        for operation_name in ('control', 'update'):

            method = getattr(self, f'{state_name}_{operation_name}')
            setattr(self, operation_name, method)

    def draw(self):
        self.draw_charging_fx()
        self.aniplayer.draw()

    def avoid_blocks_horizontally(self):

        rect = self.rect

        for block in BLOCKS_NEAR_SCREEN:

            if block.colliderect(rect):

                if rect.left < block.rect.left:
                    rect.right = block.rect.left

                else:
                    rect.left = block.rect.right

                x_speed = 0

                break

    def react_to_gravity(self):

        ### react_to_blocks on y axis

        rect = self.rect

        y_speed = self.y_speed

        y_speed = min(y_speed + GRAVITY_ACCEL, MAX_Y_SPEED)

        rect.y += y_speed

        self.midair = True

        for block in BLOCKS_NEAR_SCREEN:

            if block.colliderect(rect):

                if rect.bottom < block.rect.bottom:

                    rect.bottom = block.rect.top
                    self.midair = False

                    if hasattr(block, 'touched_top'):
                        block.touched_top(self)

                else:
                    rect.top = block.rect.bottom

                y_speed = 0

                break

        self.y_speed = y_speed

        ###

        ap = self.aniplayer
        anim_name = ap.anim_name

        orient = 'right' if anim_name.endswith('right') else 'left'

        if self.midair:

            if anim_name in {'teleporting', 'hurt_right', 'hurt_left'}: return

            blend_shooting = 'shooting' in anim_name

            if orient == 'right':
                ap.ensure_animation('jump_right')

            else:
                ap.ensure_animation('jump_left')

            if blend_shooting: ap.blend('+shooting')

        else:

            if 'jump' in anim_name:

                if self.x_speed > 0: anim_name = 'walk'
                elif self.x_speed < 0: anim_name = 'walk'
                else: anim_name = 'idle'

                ap.ensure_animation(f'{anim_name}_{orient}')

            else:
                ap.blend('+grounded')

    def jump(self):

        if not self.midair:

            self.ladder = None

            self.y_speed += self.jump_dy

            SOUND_MAP['blue_shooter_man_jump.wav'].play()

            self.aniplayer.switch_animation(
                'jump_right'
                if 'right' in self.state_name
                else 'jump_left'
            )

    def release_ladder(self):

        self.ladder = None

        self.aniplayer.switch_animation(
            'jump_right'
            if 'right' in self.state_name
            else 'jump_left'
        )

    def damage(self, amount):

        if self.state_name in UNDAMAGEABLE_STATES: return

        now = GENERAL_NS.frame_index

        if now - self.last_damage <= DAMAGE_REBOUND_FRAMES:

            if self.state_name == 'hurled':

                new_anim = new_state = (
                    'idle_right'
                    if self.x_speed > 0
                    else 'idle_left'
                )

                self.x_speed = self.y_speed = 0

                self.aniplayer.switch_animation(new_anim)
                self.set_state(new_state)

            return

        self.health_column.damage(amount)

        if self.health_column.is_depleted():

            self.die()
            return

        else: SOUND_MAP['blue_shooter_man_hurt.wav'].play()

        ap = self.aniplayer

        new_anim = (
            'hurt_right'
            if 'right' in self.state_name
            else 'hurt_left'
        )

        ap.switch_animation(new_anim)

        if not self.ladder:

            if new_anim == 'hurt_right':
                self.x_speed = -1

            else:
                self.x_speed = 1

            self.y_speed = -5

        self.set_state('hurt')

        self.last_damage = now

        ap.set_custom_surface_cycling(

            list(

                chain.from_iterable(

                    ('invisible', item)
                    for item in ap.cycle_values

                )

            )

        )

    def reset_time_tracking_attributes(self):
        """(Re)set initial value for time tracking attributes

        We set some of them to negative infinity so next time they are
        checked it is as though an infinite amount of time elapsed.
        """
        ### -INFINITY frame
        self.last_shot = self.last_damage = -INFINITY

        ### frame 0
        self.charge_start = 0

    def check_invisibility(self):

        if 'invisible' in self.aniplayer.cycle_values:

            l = list(self.aniplayer.cycle_values)

            while 'invisible' in l:
                l.remove('invisible')

            self.aniplayer.set_custom_surface_cycling(l)

    def check_ladder(self):

        if self.ladder:
            return

        rect = self.rect

        ladders = tuple(
            prop
            for prop in MIDDLE_PROPS_NEAR_SCREEN
            if getattr(prop, 'climbable', False)
            if prop.rect.colliderect(rect)
        )

        if not ladders: return

        closest_ladder = min(

            ##
            ladders,
            ##
            key=lambda ladder: abs(ladder.rect.x - rect.x)

        )

        rect.clamp_ip(closest_ladder.rect)
        rect.centerx = closest_ladder.rect.centerx

        self.ladder = closest_ladder

        self.x_speed = self.y_speed = 0

        self.midair = False

        self.aniplayer.switch_animation('climbing')

    def check_charge(self):

        diff = GENERAL_NS.frame_index - self.charge_start

        if diff >= FULL_CHARGE_FRAMES:

            if self.draw_charging_fx != do_nothing:

                self.aniplayer.set_custom_surface_cycling(
                    ('caustic_blue', 'invisible', 'caustic_green', 'invisible')
                    if 'invisible' in self.aniplayer.cycle_values
                    else ('caustic_blue', 'caustic_green', 'caustic_blue')
                )

                self.draw_charging_fx = do_nothing
                SOUND_MAP['blue_shooter_man_full_charge.wav'].play(-1)

        elif diff >= MIDDLE_CHARGE_FRAMES:

            if self.draw_charging_fx != draw_charging_particles:

                self.draw_charging_fx = draw_charging_particles
                draw_charging_particles.restore_animation()

                self.aniplayer.set_custom_surface_cycling(
                    ('default', 'invisible', 'caustic_blue', 'invisible', 'default')
                    if 'invisible' in self.aniplayer.cycle_values
                    else ('default', 'caustic_blue', 'default')
                )

                SOUND_MAP['blue_shooter_man_middle_charge.wav'].play()


    def stop_charging(self):

        diff = GENERAL_NS.frame_index - self.charge_start

        if 'invisible' in self.aniplayer.cycle_values:

            self.aniplayer.set_custom_surface_cycling(
                ('invisible', 'default')
            )

        else:
            self.aniplayer.restore_surface_cycling()

        self.charge_start = 0
        SOUND_MAP['blue_shooter_man_full_charge.wav'].stop()
        SOUND_MAP['blue_shooter_man_middle_charge.wav'].stop()
        self.draw_charging_fx = do_nothing

        if diff >= FULL_CHARGE_FRAMES:
            return 'full'

        elif diff >= MIDDLE_CHARGE_FRAMES:
            return 'middle'

    def die(self):

        self.stop_charging()
        self.set_state('dead')
        self.aniplayer = self.death_rings_aniplayer

        center = self.rect.center
        self.rect = self.aniplayer.root.rect
        self.rect.center = center

        REFS.disable_overall_tracking_for_camera()
        REFS.disable_feet_tracking_for_camera()
        SOUND_MAP['blue_shooter_man_death.wav'].play()

    def be_grabbed(self):

        self.stop_charging()
        self.aniplayer.switch_animation('grabbed')
        self.set_state('grabbed')

    def be_hurled(self, x_speed, y_speed):
        """Hurl playable character. Only stops after taking damage.

        In this states, the character can be damaged by hitting block as
        well.

        Extra care must be taken when hurling the character at
        x_speed >= width or y_speed >= height. Depending on how the
        interaction with blocks is calculated, the character may end up
        at the other side of a block.
        """

        if self.state_name in UNHURLEABLE_STATES: return

        self.x_speed = x_speed
        self.y_speed = y_speed

        self.aniplayer.switch_animation(
            'hurled_left'
            if x_speed < 0
            else 'hurled_right'
        )

        self.set_state('hurled')

    def act_on_given_script(self, scripted_actions_data, dry_run=False):
        """Enter state where Blue moves, return frame count duration.

        If dry_run is True, we only calculate the frame count duration, never
        entering the scripted acting state.
        """

        total_scripted_frames = 0
        actions_deque = self.scripted_actions_deque

        for data in scripted_actions_data:

            type_ = data['type']

            if type_ == 'walk':

                delta_x = data['delta_x']

                x_speed = -X_SPEED if delta_x < 0 else X_SPEED
                y_speed = 0

                anim_name = 'walk_left' if delta_x < 0 else 'walk_right'

                scripted_frames_count = round(abs(delta_x) / X_SPEED)

                total_scripted_frames += scripted_frames_count

                actions_deque.append(
                    {
                        'x_speed': x_speed,
                        'y_speed': y_speed,
                        'anim_name': anim_name,
                        'scripted_frames_count': scripted_frames_count
                    }
                )

            elif type_ == 'wait':

                x_speed = 0
                y_speed = 0

                anim_name = (

                    'idle_left'
                    if 'left' in self.aniplayer.anim_name

                    else 'idle_right'

                )

                scripted_frames_count = msecs_to_frames(data['secs'] * 1000)

                total_scripted_frames += scripted_frames_count

                actions_deque.append(

                    {
                        'x_speed': x_speed,
                        'y_speed': y_speed,
                        'anim_name': anim_name,
                        'anim_blend': data.get('animation_blend', ''),
                        'scripted_frames_count': scripted_frames_count
                    }

                )

            elif type_ == 'walk_away_and_face':

                if data.get('target', '') == 'boss':

                    boss_rect = REFS.level_boss.rect
                    abs_delta_x = data['abs_delta_x']

                    centerx = boss_rect.centerx + (
                        abs_delta_x
                        if boss_rect.centerx < SCREEN_RECT.centerx
                        else -abs_delta_x
                    )

                    delta_x = centerx - self.rect.centerx

                    orientation_to_face = (
                        'right' if centerx < boss_rect.centerx else 'left'
                    )

                else:
                    raise ValueError("'target' must be 'boss'")

                x_speed = -X_SPEED if delta_x < 0 else X_SPEED
                y_speed = 0

                anim_name = 'walk_left' if delta_x < 0 else 'walk_right'

                scripted_frames_count = round(abs(delta_x) / X_SPEED)

                total_scripted_frames += scripted_frames_count

                actions_deque.append(

                    {
                        'x_speed': x_speed,
                        'y_speed': y_speed,
                        'anim_name': anim_name,
                        'scripted_frames_count': scripted_frames_count,
                        'orientation_to_face': orientation_to_face,
                    }

                )

            else:

                raise ValueError(
                    "'type_' must be one used in previous if/elif clauses."
                )

        if not dry_run:

            self.set_state('scripted_acting')
            self._set_next_scripted_action(actions_deque.popleft())

        return total_scripted_frames

    def _set_next_scripted_action(self, action_data):

        self.aniplayer.switch_animation(action_data['anim_name'])
        anim_blend = self.anim_blend = action_data.get('anim_blend', '')

        if anim_blend:
            self.aniplayer.blend(f'+{anim_blend}')

        orientation_to_face = self.orientation_to_face = (
            action_data.get('orientation_to_face', '')
        )

        self.scripted_frames_count = action_data['scripted_frames_count']
        self.x_speed = action_data['x_speed']
        self.y_speed = action_data['y_speed']

    def teleport_away(self):

        self.aniplayer.switch_animation('dematerializing')
        self.set_state('teleporting_out')
