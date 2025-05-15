
### third-party imports

from pygame.locals import (

    QUIT,
    K_w, K_a, K_s, K_d,

    KEYDOWN,
    KEYUP,
    K_ESCAPE,
    K_j, K_k,

    JOYBUTTONDOWN,
    JOYBUTTONUP,

)


### local imports

from ....config import quit_game

from ....constants import (
    SHOOTING_STANCE_FRAMES,
    DAMAGE_REBOUND_FRAMES,
)

from ....pygamesetup import SERVICES_NS

from ....pygamesetup.constants import (
    GENERAL_NS,
    GAMEPADDIRECTIONALPRESSED,
    GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS,
)

from ....pygamesetup.gamepaddirect import GAMEPAD_NS, setup_gamepad_if_existent

from ....userprefsman.main import KEYBOARD_CONTROLS, GAMEPAD_CONTROLS

from ..common import PROJECTILES

from .projectiles.default import DefaultProjectile
from .projectiles.chargedshot import ChargedShot



class IdleLeft:

    def idle_left_control(self):

        ### we have to grab the state of pressed keys before
        ### entering the for-loop where we process the events;
        ###
        ### however, since the call to pygame.event.get() (indirectly
        ### called by SERVICES_NS.get_events()) must be made before
        ### the call to pygame.key.get_pressed() (indirectly called
        ### by SERVICES_NS.get_pressed_keys()) in order for pygame
        ### internals to work correctly, we call SERVICES_NS.get_events()
        ### before and store the events so we can start procesing then
        ### in the for-loop

        events = SERVICES_NS.get_events()
        pressed_state = SERVICES_NS.get_pressed_keys()

        ### process events

        for event in events:

            if event.type == KEYDOWN:

                if event.key == K_ESCAPE:
                    quit_game()

                elif event.key == KEYBOARD_CONTROLS['shoot']:
                    self.idle_left_shoot()

                elif event.key == KEYBOARD_CONTROLS['jump']:

                    if (
                        self.ladder
                        and pressed_state[KEYBOARD_CONTROLS['down']]
                    ):
                        self.release_ladder()

                    else:
                        self.jump()

                elif event.key == KEYBOARD_CONTROLS['up']:
                    self.check_ladder()

            elif event.type == JOYBUTTONDOWN:

                if event.button == GAMEPAD_CONTROLS['shoot']:
                    self.idle_left_shoot()

                elif event.button == GAMEPAD_CONTROLS['jump']:

                    if self.ladder and pressed_state[KEYBOARD_CONTROLS['down']]:
                        self.release_ladder()

                    else:
                        self.jump()

            elif event.type == GAMEPADDIRECTIONALPRESSED:

                if event.direction == 'up':
                    self.check_ladder()

            elif event.type == KEYUP:

                if event.key == KEYBOARD_CONTROLS['shoot'] and self.charge_start:

                    result = self.stop_charging()

                    if result:
                        self.idle_left_release_charge(result)

            elif event.type == JOYBUTTONUP:

                if event.button == GAMEPAD_CONTROLS['shoot'] and self.charge_start:

                    result = self.stop_charging()

                    if result:
                        self.idle_left_release_charge(result)

            elif event.type in GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS:
                setup_gamepad_if_existent()

            elif event.type == QUIT:
                quit_game()


        ### process state of keyboard/gamepad triggers

        if self.ladder:

            ap = self.aniplayer

            if (
                (GENERAL_NS.frame_index - self.last_shot)
                < SHOOTING_STANCE_FRAMES
            ):
                dy = 0

            elif (
                pressed_state[KEYBOARD_CONTROLS['up']]
                or (GAMEPAD_NS.y_sum < 0)
            ):

                dy = -1
                ap.ensure_animation('climbing')

            elif (
                pressed_state[KEYBOARD_CONTROLS['down']]
                or (GAMEPAD_NS.y_sum > 0)
            ):

                dy = 3
                ap.ensure_animation('descending')

            else:
                dy = 0

            if dy:

                moved_rect = self.rect.move(0, dy)

                if self.ladder.rect.contains(moved_rect):
                    self.rect.y += dy

                else:

                    if moved_rect.bottom > self.ladder.rect.bottom:

                        self.ladder = None
                        self.set_state('idle_left')
                        ap.switch_animation('idle_left')

            else:

                if (
                    pressed_state[KEYBOARD_CONTROLS['right']]
                    or (GAMEPAD_NS.x_sum > 0)
                ):

                    self.set_state('idle_right')
                    ap.switch_animation('idle_climbing_right')

                elif 'shooting' in ap.anim_name:
                    ap.ensure_animation('shooting_climbing_left')

                else:
                    ap.ensure_animation('idle_climbing_left')

        elif (
            pressed_state[KEYBOARD_CONTROLS['left']]
            or (GAMEPAD_NS.x_sum < 0)
        ):

            self.x_accel += -1
            self.set_state('walk_left')
            self.aniplayer.switch_animation('walk_left')

        elif (
            pressed_state[KEYBOARD_CONTROLS['right']]
            or (GAMEPAD_NS.x_sum > 0)
        ):

            self.x_accel += 1
            self.set_state('walk_right')
            self.aniplayer.switch_animation('walk_right')

    def idle_left_update(self):

        current_frame = GENERAL_NS.frame_index

        if current_frame - self.last_shot >= SHOOTING_STANCE_FRAMES:
            self.aniplayer.blend('-shooting')

        if self.charge_start:
            self.check_charge()

        if not self.ladder:
            self.react_to_gravity()

        if current_frame - self.last_damage > DAMAGE_REBOUND_FRAMES:
            self.check_invisibility()

    def idle_left_shoot(self):

        pos_value = self.rect.move(2, -2).midleft

        PROJECTILES.add(
            DefaultProjectile(
                x_orientation=-1,
                pos_name='center',
                pos_value=pos_value,
            )
        )

        if self.ladder:
            self.aniplayer.ensure_animation('shooting_climbing_left')
        else:
            self.aniplayer.blend('+shooting')

        self.charge_start = self.last_shot = GENERAL_NS.frame_index

    def idle_left_release_charge(self, charge_type):

        pos_value = self.rect.move(-7, -2).midleft

        PROJECTILES.add(
            ChargedShot(
                charge_type,
                x_orientation=-1,
                pos_name='center',
                pos_value=pos_value,
            )
        )

        if self.ladder:
            self.aniplayer.ensure_animation('shooting_climbing_left')
        else:
            self.aniplayer.blend('+shooting')

        self.last_shot = GENERAL_NS.frame_index
