"""Facility for user preferences management."""

### standard library imports

from os import environ

from pathlib import Path

from copy import deepcopy

from pprint import pformat


### third-party import
from pygame import locals as pygame_locals


### local imports

from ..config import WRITEABLE_PATH

from ..ourstdlibs.pyl import load_pyl

from .validation import validate_prefs_dict

#from ..logman.main import get_new_logger


### module level logger
#logger = get_new_logger(__name__)


### messages

ERROR_LOADING_USER_PREFS_MESSAGE = """
Error while trying to load user configuration. Default
configuration will be used instead
""".strip()

INVALID_USER_PREFS_MESSAGE = """
User configuration loaded didn't validate; Default
configuration will be used instead
""".strip()

UNEXISTENT_USER_PREFS_MESSAGE = """
User configuration doesn't exist. Default configuration
will be used instead
""".strip()


### default controls

DEFAULT_KEYBOARD_CONTROL_NAMES = {

    'up': 'K_w',
    'down': 'K_s',
    'left': 'K_a',
    'right': 'K_d',

    'shoot': 'K_j',
    'jump': 'K_k',

    'previous_power': 'K_u',
    'next_power': 'K_o',

}

DEFAULT_GAMEPAD_CONTROLS = {

    'shoot': None,
    'jump': None,

    'previous_power': None,
    'next_power': None,

    'start_button': None,

}


### dictionary wherein to store user preferences; initially
### populated with default values

DEFAULT_USER_PREFS = {
    "MASTER_VOLUME": 20,
    "MUSIC_VOLUME": 20,
    "SOUND_VOLUME": 40,
    "FULLSCREEN": False,
    "LAST_USED_SAVE_SLOT": None,
    "KEYBOARD_CONTROL_NAMES": DEFAULT_KEYBOARD_CONTROL_NAMES,
    "GAMEPAD_CONTROLS": DEFAULT_GAMEPAD_CONTROLS,
}


USER_PREFS = deepcopy(DEFAULT_USER_PREFS)

KEYBOARD_CONTROL_NAMES = USER_PREFS['KEYBOARD_CONTROL_NAMES']
GAMEPAD_CONTROLS = USER_PREFS['GAMEPAD_CONTROLS']



### validate user preference defaults
validate_prefs_dict(USER_PREFS)


### define path to config file
CONFIG_FILEPATH = WRITEABLE_PATH / "config.pyl"


### utility function

def save_config_on_disk():

    CONFIG_FILEPATH.write_text(
        pformat(USER_PREFS, indent=2),
        encoding='utf-8',
    )


### if file exists, try loading it

if CONFIG_FILEPATH.exists():

    try:
        user_config_data = load_pyl(CONFIG_FILEPATH)

    except Exception:

        #logger.exception(ERROR_LOADING_USER_PREFS_MESSAGE)
        pass

    else:

        try:
            validate_prefs_dict(user_config_data)

        except Exception:

            #logger.exception(INVALID_USER_PREFS_MESSAGE)
            pass

        else:

            for key, value in user_config_data.items():

                if isinstance(value, dict):
                    USER_PREFS[key].update(value)

                else:
                    USER_PREFS[key] = value

else:

    #logger.info(UNEXISTENT_USER_PREFS_MESSAGE)
    save_config_on_disk()


KEYBOARD_CONTROLS = {
    action_name: getattr(pygame_locals, key_name)
    for action_name, key_name in KEYBOARD_CONTROL_NAMES.items()
}
