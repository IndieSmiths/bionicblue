
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

from ....pygamesetup.constants import (
    GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS,
    screen_colliderect,
)

from ....pygamesetup.gamepadservices import GAMEPAD_NS

from ....userprefsman.main import GAMEPAD_CONTROLS

from ....constants import MAX_Y_SPEED



class TeleportingOut:

    def teleporting_out_control(self):

        for event in SERVICES_NS.get_events():

            if event.type == KEYDOWN:

                if event.key == K_ESCAPE:
                    REFS.pause()

                elif event.key == K_RETURN:
                    REFS.pause()

            elif event.type in GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS:
                GAMEPAD_NS.setup_gamepad_if_existent()

            elif event.type == JOYBUTTONDOWN:

                if event.button == GAMEPAD_CONTROLS['start_button']:
                    REFS.pause()

            elif event.type == QUIT:
                quit_game()

    def teleporting_out_update(self):

        ### if player is out of screen, there's nothing left to be done
        if not screen_colliderect(self.rect): return

        ### otherwise, act according to current animation and other stuff

        ap = self.aniplayer

        if ap.anim_name == 'dematerializing':

            main_timing = ap.main_timing

            if main_timing.get_original_index(0) == 0:
                SOUND_MAP['blue_shooter_man_materialization.wav'].play()

            if main_timing.peek_loops_no(1) == 1:

                self.aniplayer.switch_animation('teleporting')

        elif ap.anim_name == 'teleporting':
            self.rect.move_ip(0, -MAX_Y_SPEED)
