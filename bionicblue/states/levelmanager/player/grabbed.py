
### third-party imports

from pygame.locals import (

    QUIT,

    KEYDOWN,
    K_ESCAPE,
    K_RETURN,

    JOYBUTTONDOWN,

)


### local imports

from ....config import REFS, quit_game

from ....constants import DAMAGE_REBOUND_FRAMES

from ....pygamesetup import SERVICES_NS

from ....pygamesetup.constants import (
    GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS,
    GENERAL_NS,
)

from ....pygamesetup.gamepadservices import GAMEPAD_NS

from ....userprefsman.main import GAMEPAD_CONTROLS



class Grabbed:

    def grabbed_control(self):

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

    def grabbed_update(self):

        if GENERAL_NS.frame_index - self.last_damage > DAMAGE_REBOUND_FRAMES:
            self.check_invisibility()
