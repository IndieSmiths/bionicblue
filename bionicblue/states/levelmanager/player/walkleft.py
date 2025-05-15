
### third-party imports

from pygame.locals import (

    QUIT,

    KEYDOWN,
    KEYUP,
    K_ESCAPE,
    K_k,

    JOYBUTTONDOWN,
    JOYBUTTONUP,

)


### local imports

from ....config import quit_game

from ....constants import (
    MAX_X_SPEED,
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



class WalkLeft:

    def walk_left_control(self):

        ### process events

        for event in SERVICES_NS.get_events():

            if event.type == KEYDOWN:

                if event.key == K_ESCAPE:
                    quit_game()

                elif event.key == KEYBOARD_CONTROLS['shoot']:
                    self.walk_left_shoot()

                elif event.key == KEYBOARD_CONTROLS['jump']:
                    self.jump()

                elif event.key == KEYBOARD_CONTROLS['up']:

                    self.check_ladder()

                    if self.ladder:

                        self.set_state('idle_left')
                        self.aniplayer.switch_animation('climbing')

                        return

            elif event.type == JOYBUTTONDOWN:

                if event.button == GAMEPAD_CONTROLS['shoot']:
                    self.walk_left_shoot()

                elif event.button == GAMEPAD_CONTROLS['jump']:
                    self.jump()

            elif event.type == GAMEPADDIRECTIONALPRESSED:

                if event.direction == 'up':

                    self.check_ladder()

                    if self.ladder:

                        self.set_state('idle_left')
                        self.aniplayer.switch_animation('climbing')

                        return

            elif event.type == KEYUP:

                if event.key == KEYBOARD_CONTROLS['shoot'] and self.charge_start:

                    result = self.stop_charging()

                    if result:
                        self.walk_left_release_charge(result)

            elif event.type == JOYBUTTONUP:

                if event.button == GAMEPAD_CONTROLS['shoot'] and self.charge_start:

                    result = self.stop_charging()

                    if result:
                        self.walk_left_release_charge(result)

            elif event.type in GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS:
                setup_gamepad_if_existent()

            elif event.type == QUIT:
                quit_game()


        ### process state of keyboard/gamepad triggers

        pressed_state = SERVICES_NS.get_pressed_keys()

        if pressed_state[KEYBOARD_CONTROLS['left']] or (GAMEPAD_NS.x_sum < 0):
            self.x_accel = max(self.x_accel - 1, -2)

        elif pressed_state[KEYBOARD_CONTROLS['right']] or (GAMEPAD_NS.x_sum > 0):

            self.x_accel += 1

            if self.aniplayer.anim_name == 'shooting_walk_left':
                self.set_state('decelerate_left')
                self.aniplayer.switch_animation('decelerate_left')
                self.aniplayer.blend('+shooting')

            else:
                self.set_state('decelerate_left')
                self.aniplayer.switch_animation('decelerate_left')

        else:
            self.x_accel = max(self.x_accel + 1, 0)

    def walk_left_update(self):

        x = self.rect.x

        if self.x_speed < 0:
            self.x_speed += -1

        self.x_speed += self.x_accel
        self.x_speed = min(max(self.x_speed, -MAX_X_SPEED), 0)

        self.rect.x += self.x_speed

        if not self.x_speed:
            self.set_state('idle_left')
            self.aniplayer.switch_animation('idle_left')

        current_frame = GENERAL_NS.frame_index

        if current_frame - self.last_shot >= SHOOTING_STANCE_FRAMES:
            self.aniplayer.blend('-shooting')

        if self.charge_start:
            self.check_charge()

        if self.rect.x != x:
            self.avoid_blocks_horizontally()

        self.react_to_gravity()

        if current_frame - self.last_damage > DAMAGE_REBOUND_FRAMES:
            self.check_invisibility()

    def walk_left_shoot(self):

        pos_value = self.rect.move(-2, -2).midleft

        PROJECTILES.add(
            DefaultProjectile(
                x_orientation=-1,
                pos_name='center',
                pos_value=pos_value,
            )
        )

        self.aniplayer.blend('+shooting')
        self.charge_start = self.last_shot = GENERAL_NS.frame_index

    def walk_left_release_charge(self, charge_type):

        pos_value = self.rect.move(-10, -2).midleft

        PROJECTILES.add(
            ChargedShot(
                charge_type,
                x_orientation=-1,
                pos_name='center',
                pos_value=pos_value,
            )
        )

        self.aniplayer.blend('+shooting')

        self.last_shot = GENERAL_NS.frame_index
