
### third-party imports

from pygame.locals import (

    QUIT,

    KEYDOWN,
    K_ESCAPE,
    K_RETURN,

    JOYBUTTONDOWN,

)


### local imports

from ....config import REFS, SOUND_MAP, quit_game

from ....pygamesetup import SERVICES_NS

from ....pygamesetup.constants import GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS

from ....pygamesetup.gamepaddirect import setup_gamepad_if_existent

from ....userprefsman.main import GAMEPAD_CONTROLS



class TeleportingIn:

    def teleporting_in_control(self):

        for event in SERVICES_NS.get_events():

            if event.type == KEYDOWN:

                if event.key == K_ESCAPE:
                    REFS.pause()

                elif event.key == K_RETURN:
                    REFS.pause()

            elif event.type in GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS:
                setup_gamepad_if_existent()

            elif event.type == JOYBUTTONDOWN:

                if event.button == GAMEPAD_CONTROLS['start_button']:
                    REFS.pause()

            elif event.type == QUIT:
                quit_game()

    def teleporting_in_update(self):

        ap = self.aniplayer

        if ap.anim_name == 'materializing':

            main_timing = ap.main_timing

            if main_timing.get_original_index(0) == 0:
                SOUND_MAP['blue_shooter_man_materialization.wav'].play()

            if main_timing.peek_loops_no(1) == 1:

                self.set_state('idle_right')
                self.aniplayer.switch_animation('idle_right')
                REFS.enable_overall_tracking_for_camera()
                REFS.enable_feet_tracking_for_camera()

        self.react_to_gravity()
