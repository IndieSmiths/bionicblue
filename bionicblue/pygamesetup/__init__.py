"""Setup of different modes."""

### local imports

## constant
from .constants import GENERAL_NS

## custom services
from .services import normal, record, replay

## custom gamepad services

from .gamepadservices import (
    normal as gpnormal,
    record as gprecord,
    replay as gpreplay,
)



### create a namespace to store the services in use
SERVICES_NS = type("Object", (), {})()

### set normal services on namespace (enables normal mode)

normal.set_behaviour(SERVICES_NS)
gpnormal.set_behaviour()


### function to switch modes

def switch_mode(play_mode_name, play_data=None):
    """Switch to named play mode.

    Parameters
    ==========
    play_mode_name (str)
        Name of play mode to switch to (either 'record', 'replay' or 'normal')

    play_data (dict or NoneType)
        if play_mode_name=='replay', must be a dict containing data used in
        replay mode.
    """

    GENERAL_NS.play_mode_name = play_mode_name

    if play_mode_name == 'record':

        record.set_behaviour(SERVICES_NS)
        gprecord.set_behaviour()

    elif play_mode_name == 'replay':

        replay.set_behaviour(SERVICES_NS, play_data)
        gpreplay.set_behaviour(play_data)

    elif play_mode_name == 'normal':

        normal.set_behaviour(SERVICES_NS)
        gpnormal.set_behaviour()

    else:

        raise RuntimeError(
            "'play_mode_name' must be in previous if/elif blocks,"
            f"cannot be {play_mode_name}"
        )

