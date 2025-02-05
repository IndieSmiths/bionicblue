
### standard library import
from ast import literal_eval


### third-party import
from pygame import locals as pygame_locals



DICT_KEY_ERROR_FORMATTER = ("{!r} key not present in user preferences").format


### keys which can only be used for their original purpose, that is, they
### cannot be assigned to another action

RESERVED_KEYS = frozenset((

    # used to confirm things
    'K_RETURN',


    # used to cancel/go back

    'K_ESCAPE',
    'K_BACKSPACE',

))


### keys in the controls dictionaries for keyboard and gamepad
### (represent actions that can be assign to keys on the keyboard
### or buttons on a gamepad)

KEYBOARD_CONTROL_NAMES_DICT_KEYS = (

    'up',
    'down',
    'left',
    'right',

    'shoot',
    'jump',

    'previous_power',
    'next_power',

)

GAMEPAD_CONTROLS_DICT_KEYS = (

    'shoot',
    'jump',

    'previous_power',
    'next_power',

    'start_button',

)

### pygame keys name map

PYGAME_KEYS_NAME_MAP = {
    getattr(pygame_locals, name): name
    for name in dir(pygame_locals)
    if name.startswith('K_')
}

PYGAME_KEYS_NAMES = frozenset(PYGAME_KEYS_NAME_MAP.values())



### main function

def validate_prefs_dict(prefs_dict):
    """Raise exception if dict doesn't validate."""

    ### key existence

    for key in (
        "MASTER_VOLUME",
        "MUSIC_VOLUME",
        "SOUND_VOLUME",
        "FULLSCREEN",
        "LAST_USED_SAVE_SLOT",
        "KEYBOARD_CONTROL_NAMES",
        "GAMEPAD_CONTROLS",
    ):

        if key not in prefs_dict:
            raise KeyError(DICT_KEY_ERROR_FORMATTER(key))


    ### volumes values

    for key in ("MASTER_VOLUME", "MUSIC_VOLUME", "SOUND_VOLUME"):

        vol = prefs_dict[key]

        if not isinstance(vol, int):
            raise TypeError(f"'{key}' option must be an integer")

        if not 0 <= vol <= 100:
            raise ValueError(f"'{key}' option's value must be from 0 to 100")


    ### fullscreen

    if not isinstance(prefs_dict['FULLSCREEN'], bool):
        raise TypeError(f"FULLSCREEN option must be a boolean (False or True)")


    ### save slots

    value = prefs_dict['LAST_USED_SAVE_SLOT']

    if value is None or isinstance(value, str):
        pass

    else:
        raise TypeError("LAST_USED_SAVE_SLOT must be None or a string")



    ### keyboard controls
    validate_keyboard_controls(prefs_dict['KEYBOARD_CONTROL_NAMES'])

    ### gamepad controls
    validate_gamepad_controls(prefs_dict['GAMEPAD_CONTROLS'])


def validate_keyboard_controls(controls):

    if not isinstance(controls, dict):
        raise TypeError("KEYBOARD_CONTROL_NAMES must be a dictionary")

    if controls.keys() != frozenset(KEYBOARD_CONTROL_NAMES_DICT_KEYS):

        raise ValueError(
            "The KEYBOARD_CONTROL_NAMES dict must have exactly"
            f" these keys: {KEYBOARD_CONTROL_NAMES_DICT_KEYS}"
        )

    for value in controls.values():

        if not isinstance(value, str):

            raise ValueError(
                "Any value in the KEYBOARD_CONTROL_NAMES dict must be either"
                " a string or None"
            )

        elif value not in PYGAME_KEYS_NAMES:

            raise ValueError(
                "If a value in the KEYBOARD_CONTROL_NAMES dict is a string,"
                " it must be a name available in the pygame.locals module"
                " that starts with 'K_'."
            )

def validate_gamepad_controls(controls):

    if not isinstance(controls, dict):
        raise TypeError("GAMEPAD_CONTROLS must be a dictionary")

    if controls.keys() != frozenset(GAMEPAD_CONTROLS_DICT_KEYS):

        raise ValueError(
            "The GAMEPAD_CONTROLS dict must have exactly"
            f" these keys: {GAMEPAD_CONTROLS_DICT_KEYS}"
        )

    NoneType = type(None)

    for value in controls.values():

        if not isinstance(value, (int, NoneType)):

            raise ValueError(
                "Any value in the GAMEPAD_CONTROLS dict must be either"
                " an int or None"
            )
