
### third-party imports

from pygame.locals import (

    QUIT,

    KEYDOWN,
    KEYUP,
    K_ESCAPE,

    JOYBUTTONDOWN,
    JOYBUTTONUP,

)


### local imports

from ....config import quit_game

from ....constants import DAMAGE_REBOUND_FRAMES

from ....pygamesetup import SERVICES_NS

from ....pygamesetup.constants import (
    GENERAL_NS,
    GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS,
)

from ....pygamesetup.gamepaddirect import GAMEPAD_NS, setup_gamepad_if_existent

from ....userprefsman.main import KEYBOARD_CONTROLS, GAMEPAD_CONTROLS

from ..common import PROJECTILES

from .projectiles.default import DefaultProjectile
from .projectiles.chargedshot import ChargedShot



class DecelerateRight:

    def decelerate_right_control(self):

        ### process events

        for event in SERVICES_NS.get_events():

            if event.type == KEYDOWN:

                if event.key == K_ESCAPE:
                    quit_game()

                elif event.key == KEYBOARD_CONTROLS['shoot']:
                    self.decelerate_right_shoot()

                elif event.key == KEYBOARD_CONTROLS['jump']:

                    if not self.midair:
                        self.y_speed += self.jump_dy

            elif event.type == JOYBUTTONDOWN:

                if event.button == GAMEPAD_CONTROLS['shoot']:
                    self.decelerate_right_shoot()

                elif event.button == GAMEPAD_CONTROLS['jump']:

                    if not self.midair:
                        self.y_speed += self.jump_dy

            elif event.type == KEYUP:

                if event.key == KEYBOARD_CONTROLS['shoot'] and self.charge_start:

                    result = self.stop_charging()

                    if result:
                        self.decelerate_right_release_charge(result)

            elif event.type == JOYBUTTONUP:

                if event.button == GAMEPAD_CONTROLS['shoot'] and self.charge_start:

                    result = self.stop_charging()

                    if result:
                        self.decelerate_right_release_charge(result)

            elif event.type in GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS:
                setup_gamepad_if_existent()

            elif event.type == QUIT:
                quit_game()

        ### process state of keyboard/gamepad triggers

        pressed_state = SERVICES_NS.get_pressed_keys()

        if pressed_state[KEYBOARD_CONTROLS['left']] or (GAMEPAD_NS.x_sum < 0):

            self.x_accel = max(self.x_accel - 1, 0)

            if self.x_speed <= 0:

                self.set_state('walk_left')
                self.aniplayer.switch_animation('walk_left')

        elif pressed_state[KEYBOARD_CONTROLS['right']] or (GAMEPAD_NS.x_sum > 0):

            self.x_accel += 1
            self.set_state('walk_right')
            self.aniplayer.switch_animation('walk_right')

        elif self.x_speed == 0:

            self.set_state('idle_right')
            self.aniplayer.switch_animation('idle_right')

    def decelerate_right_update(self):

        x = self.rect.x

        self.x_speed += self.x_accel
        self.rect.x += self.x_speed

        if self.x_speed > 0:
            self.x_speed += -1
        elif self.x_speed < 0:
            self.x_speed += 1

        current_frame = GENERAL_NS.frame_index

        if self.charge_start:
            self.check_charge()

        if self.rect.x != x:
            self.avoid_blocks_horizontally()

        self.react_to_gravity()

        if current_frame - self.last_damage > DAMAGE_REBOUND_FRAMES:
            self.check_invisibility()

    def decelerate_right_shoot(self):

        pos_value = self.rect.move(0, -2).midright

        PROJECTILES.add(
            DefaultProjectile(
                x_orientation=1,
                pos_name='center',
                pos_value=pos_value,
            )
        )

        self.aniplayer.blend('+shooting')
        self.charge_start = GENERAL_NS.frame_index

    def decelerate_right_release_charge(self, charge_type):

        pos_value = self.rect.move(10, -2).midright

        PROJECTILES.add(
            ChargedShot(
                charge_type,
                x_orientation=1,
                pos_name='center',
                pos_value=pos_value,
            )
        )

        self.aniplayer.blend('+shooting')

        self.last_shot = GENERAL_NS.frame_index
