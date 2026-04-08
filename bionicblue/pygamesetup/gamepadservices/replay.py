"""Utility for gamepad controls management.

Directional controls refer not only to the buttons on the D-pad,
but also the axes's controls, since they also convey direction
information.
"""

### standard library import
from collections import defaultdict


### local imports

from ..constants import GENERAL_NS

from .common import GAMEPAD_NS



DIRECTIONAL_STATE_MAP = {}

BUTTON_STATE_MAP = defaultdict(dict)

TWO_TUPLE_OF_ZEROS = (0, 0)

def set_behaviour(play_data):

    GAMEPAD_NS.setup_gamepad_if_existent = setup_gamepad_if_existent
    GAMEPAD_NS.get_button = get_button
    GAMEPAD_NS.prepare_data_and_events = _prepare_data_and_events
    GAMEPAD_NS.clear_data = clear_data

    clear_data()

    DIRECTIONAL_STATE_MAP.update(play_data['gamepad_directional_state_map'])
    BUTTON_STATE_MAP.update(play_data['gamepad_button_state_map'])


def clear_data():

    DIRECTIONAL_STATE_MAP.clear()
    BUTTON_STATE_MAP.clear()

def get_button(button_id):
    return BUTTON_STATE_MAP[GENERAL_NS.frame_index].get(button_id, False)

def setup_gamepad_if_existent():
    pass

def _prepare_data_and_events():

    GAMEPAD_NS.x_sum, GAMEPAD_NS.y_sum = (

        DIRECTIONAL_STATE_MAP.get(
            GENERAL_NS.frame_index,
            TWO_TUPLE_OF_ZEROS,
        )

    )
