"""General configuration for game."""

### standard library import

from pathlib import Path

from datetime import datetime


### third-party imports

from pygame import quit as quit_pygame

from pygame.system import get_pref_path


### local imports

from .appinfo import ORG_DIR_NAME, APP_DIR_NAME

from .ourstdlibs.pyl import save_pyl, load_pyl



###
COLORKEY = (192, 192, 192)

###

class LoopException(Exception):
    """Raised for a variety of purposes.

    The purposes may be one or more of these:

    1. simply skip back to the beginning of the loop
    2. switch to a new state (loop holder)
    3. switch to a new input mode (normal, input recording, input playing)
    """

    def __init__(
        self,
        *,
        next_state=None,
        next_input_mode_name='',
        input_data=None,
        prepare=False,
        clear_tasks=False,
    ):

        self.state = next_state

        self.input_mode_name = next_input_mode_name
        self.input_data = input_data

        self.prepare = prepare
        self.clear_tasks = clear_tasks

        super().__init__("Interrupting loop.")

## anonymous object builder
Object = type('Object', (), {})

##

REFS = Object()

REFS.__dict__.update(dict(

    states = Object(),

    last_checkpoint_name = 'landing',

    dialogue_action_cueing_data = {},
    dialogue_character_names_set_map = {},

    clear_tasks = None,

))



###

DATA_DIR = Path(__file__).parent / 'data'

CREDITS_FILEPATH = DATA_DIR / 'credits.txt'
LINKS_FILEPATH = DATA_DIR / 'links.txt'

FONTS_DIR = DATA_DIR / 'fonts'
IMAGES_DIR = DATA_DIR / 'images'
ANIMATIONS_DIR = DATA_DIR / 'animations'
SOUNDS_DIR = DATA_DIR / 'sounds'
MUSIC_DIR = DATA_DIR / 'music'
LEVELS_DIR = DATA_DIR / 'levels'
PARTICLES_DIR = DATA_DIR / 'particles'
MOTION_PATHS_DIR = DATA_DIR / 'motion_paths'
SCRIPTED_SCENES_DATA_DIR = DATA_DIR / 'scripted_scenes_data'
PARALLAX_POSITIONING_DIR = DATA_DIR / 'parallax_positioning'

TRANSLATIONS_DIR = DATA_DIR / 'translations'
LANGUAGE_NAMES_FILEPATH = TRANSLATIONS_DIR / 'language_native_names.pyl'

REPORTS_DIR = DATA_DIR / 'reports'

NO_COLORKEY_IMAGES_DIR = IMAGES_DIR  / 'no_colorkey'
COLORKEY_IMAGES_DIR = IMAGES_DIR  / 'colorkey'

MUST_LOCK_PLAY = not (DATA_DIR.parent.parent / 'play').exists()

###

SURF_MAP = {}
ANIM_DATA_MAP = {}
SOUND_MAP = {}

### writeable folder and subfolders used to store user data
### (configuration, save files, logs, etc.)

# get_pref_path already creates the directory if it doesn't
# exist already
WRITEABLE_PATH = Path(get_pref_path(ORG_DIR_NAME, APP_DIR_NAME))

SAVE_SLOTS_DIR = WRITEABLE_PATH / 'save_slots'
LOGS_DIR = WRITEABLE_PATH / 'logs'
REGULAR_PLAY_LOGS_DIR = LOGS_DIR / 'regular_play_logs'
FIRST_PLAY_LOGS_DIR = LOGS_DIR / 'first_play_logs'

## the others must be created by us if they don't exist already

for dir_path in (
    SAVE_SLOTS_DIR,
    LOGS_DIR,
    REGULAR_PLAY_LOGS_DIR,
    FIRST_PLAY_LOGS_DIR,
):

    try:
        dir_path.mkdir(exist_ok=True)

    except FileExistsError as err:

        path_name = str(dir_path)

        raise RuntimeError(
            "A path that is required by the game to be a folder"
            f" has a file in its place {path_name}. Deleting it,"
            " if possible, should solve the problem."
        ) from err




def has_save_slots():

    return any(

        path

        for path in SAVE_SLOTS_DIR.iterdir()
        if path.suffix.lower() == '.pyl'

    )

def get_custom_datetime_str_for_last_played():

    now = datetime.now().astimezone()

    timestamp = now.isoformat()[:19].replace('T', ' ')
    tz = now.tzname()
    signal = tz[0]
    signal_name = 'minus' if signal == '-' else 'plus'
    offset = tz[1:]

    return f'{timestamp} {signal_name} {offset}'

def get_custom_datetime_str_for_default_slot_name():
    return datetime.now().strftime('Y%Y_M%m_D%d_H%H_M%M')


### constructs to keep track of events that happen for the first time
### in the game
###
### this data is useful to trigger events that only happen once, when
### something happens for the first time. For instance, the "thank you"
### message is presented only when the player clears a mission for the
### first time since the app was installed

FIRST_TIME_FILEPATH = WRITEABLE_PATH / 'first_time.pyl'

DEFAULT_FIRST_TIME_DATA = {
    'cleared_a_mission': True,
    'chose_a_locale_on_startup': True,
}

if FIRST_TIME_FILEPATH.exists():

    try:
        data = load_pyl(FIRST_TIME_FILEPATH)

    except Exception:

        print("Couldn't load first time data, using defaults instead.")

        FIRST_TIME_DATA = DEFAULT_FIRST_TIME_DATA.copy()
        save_pyl(FIRST_TIME_DATA, FIRST_TIME_FILEPATH)

    else:

        if (

            not isinstance(data, dict)
            or data.keys() == DEFAULT_FIRST_TIME_DATA.keys()
            or any(
                not isinstance(value, bool)
                for value in data.values()
            )

        ):

            FIRST_TIME_DATA = DEFAULT_FIRST_TIME_DATA.copy()
            save_pyl(FIRST_TIME_DATA, FIRST_TIME_FILEPATH)

        else:
            FIRST_TIME_DATA = data

else:

    FIRST_TIME_DATA = DEFAULT_FIRST_TIME_DATA.copy()
    save_pyl(FIRST_TIME_DATA, FIRST_TIME_FILEPATH)

###

def save_first_time_data():
    save_pyl(FIRST_TIME_DATA, FIRST_TIME_FILEPATH)

def is_it_the_first_time(event_name):

    ## if it is the first time...

    if FIRST_TIME_DATA[event_name]:

        ### this is the first time, so we set the event to false
        ### and save the data so next time we know it is not the
        ### first time anymore

        FIRST_TIME_DATA[event_name] = False
        save_first_time_data()

        ### since this is the first time, we return True
        return True

    ## if it is not the first time, return False
    else:
        return False

def quit_game():

    quit_pygame()
    quit()
