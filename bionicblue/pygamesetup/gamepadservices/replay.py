"""Utility for gamepad controls management.

Directional controls refer not only to the buttons on the D-pad,
but also the axes's controls, since they also convey direction
information.
"""

### standard library import
from collections import defaultdict


### local imports

from ..constants import GENERAL_NS, yield_unrangefied_integers

from .common import GAMEPAD_NS



DIRECTION_TO_FRAMES_MAP = {}

BUTTON_STATE_MAP = {}

TWO_TUPLE_OF_ZEROS = (0, 0)

EMPTY_FROZENSET = frozenset()


def set_behaviour(play_data):

    GAMEPAD_NS.setup_gamepad_if_existent = setup_gamepad_if_existent
    GAMEPAD_NS.get_button = get_button
    GAMEPAD_NS.prepare_data_and_events = _prepare_data_and_events
    GAMEPAD_NS.clear_data = clear_data

    clear_data()

    DIRECTION_TO_FRAMES_MAP.update(

        (k, set(yield_unrangefied_integers(rangefied_integers)))

        for k, rangefied_integers in (
            play_data['gamepad_direction_to_frames_map'].items()
        )

    )

    load_pressed_buttons_to_frames_map(
        play_data['gamepad_pressed_buttons_to_frames_map'],
        play_data['gamepad_controls'],
    )

def clear_data():

    DIRECTION_TO_FRAMES_MAP.clear()
    BUTTON_STATE_MAP.clear()

def load_pressed_buttons_to_frames_map(data, gamepad_controls):

    for pressed_buttons, rangefied_frame_indices in data.items():

        for frame_index in yield_unrangefied_integers(rangefied_frame_indices):

            BUTTON_STATE_MAP[frame_index] = {

                gamepad_controls[action_name]
                for action_name in pressed_buttons

            }


def get_button(button_id):

    return (

        GENERAL_NS.frame_index in BUTTON_STATE_MAP
        and button_id in BUTTON_STATE_MAP[GENERAL_NS.frame_index]

    )

def setup_gamepad_if_existent():
    pass

def _prepare_data_and_events():

    for direction, frame_set in DIRECTION_TO_FRAMES_MAP.items():

        if GENERAL_NS.frame_index in frame_set:

            GAMEPAD_NS.x_sum, GAMEPAD_NS.y_sum = direction
            break

    else:
        GAMEPAD_NS.x_sum, GAMEPAD_NS.y_sum = TWO_TUPLE_OF_ZEROS
