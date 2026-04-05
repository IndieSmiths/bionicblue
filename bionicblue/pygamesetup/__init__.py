"""Setup of different modes."""

### local imports

## constant
from .constants import GENERAL_NS

## custom services
from .services import normal, record, play

## custom gamepad services

from .gamepadservices import (
    normal as gpnormal,
    record as gprecord,
    play as gpplay,
)



### create a namespace to store the services in use
SERVICES_NS = type("Object", (), {})()

### set normal services on namespace (enables normal mode)

normal.set_behaviour(SERVICES_NS)
gpnormal.set_behaviour()


### function to switch modes

def switch_mode(input_mode_name, input_data=None):
    """Switch to named input mode.

    Parameters
    ==========
    input_mode_name (str)
        Name of input mode to switch to (either 'record', 'play' or 'normal')

    input_data (dict or NoneType)
        if dict, data is used in play mode.
    """

    GENERAL_NS.input_mode_name = input_mode_name

    if input_mode_name == 'record':

        record.set_behaviour(SERVICES_NS)
        gprecord.set_behaviour()

    elif input_mode_name == 'play':

        play.set_behaviour(SERVICES_NS, input_data)
        gprecord.set_behaviour(input_data)

    elif input_mode_name == 'normal':

        normal.set_behaviour(SERVICES_NS)
        gpnormal.set_behaviour()

    else:

        raise RuntimeError(
            "'input_mode_name' must be in previous if/elif blocks,"
            f"cannot be {input_mode_name}"
        )

