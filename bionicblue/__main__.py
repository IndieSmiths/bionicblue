"""Facility with function to run the Bionic Blue game.

Bionic Blue (by Kennedy Guerra): to know more about this game,
visit its website: https://bionicblue.indiesmiths.com
"""

### local imports

## first ensure pygame used is the community edition fork (pygame-ce);
##
## this is important because the app uses services that are not available
## in the regular pygame instance
from .ensurepygamece import ensure_pygame_ce
ensure_pygame_ce()

## remaining local imports

from .config import REFS

from .pygamesetup import SERVICES_NS, switch_mode

from .pygamesetup.gamepaddirect import setup_gamepad_if_existent

from .states import setup_states

from .exceptions import (
    SwitchStateException,
    BackToBeginningException,
    SwitchModeException,
)



def run_game():
    """Run the game loop."""

    setup_states()

    state = REFS.states.resource_loader

    setup_gamepad_if_existent()

    running = True

    while True:

        try:

            ### game loop

            while True:

                SERVICES_NS.frame_checkups()

                state.control()
                state.update()
                state.draw()

        except SwitchStateException as obj:
            state = obj.state

        except BackToBeginningException as obj:
            pass

        except SwitchModeException as obj:
            switch_mode(obj)

if __name__ == '__main__':
    run_game()
