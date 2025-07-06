"""Setup of different modes."""

### local imports

## constants

from .constants import (
    SCREEN,
    SCREEN_RECT,
    GENERAL_NS,
    GENERAL_SERVICE_NAMES,
    blit_on_screen,
)

## custom services
from .services import normal, record, play


### create a namespace to store the services in use
SERVICES_NS = type("Object", (), {})()

### set normal services on namespace (enables normal mode)
###
### there's no need to reset the window mode this first time,
### because it was already properly set in the constants.py
### sibling module
normal.set_behaviour(SERVICES_NS, reset_window_mode=False)


### function to switch modes

def switch_mode(input_mode_name):
    """Switch to named input mode.

    Parameters
    ==========
    input_mode_name (str)
        Name of input mode to switch to (either 'record', 'play' or 'normal')
    """
    GENERAL_NS.input_mode_name = input_mode_name

    if input_mode_name == 'record':
        record.set_behaviour(SERVICES_NS)

    elif input_mode_name == 'play':
        play.set_behaviour(SERVICES_NS)

    elif input_mode_name == 'normal':
        normal.set_behaviour(SERVICES_NS)
