"""General configuration for game."""

### standard library import

from pathlib import Path

from contextlib import suppress

from datetime import datetime


### third-party imports

from pygame import quit as quit_pygame

from pygame.system import get_pref_path


### local import
from .appinfo import ORG_DIR_NAME, APP_DIR_NAME 



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
    ):

        self.state = next_state
        self.input_mode_name = next_input_mode_name
        self.input_data = input_data

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

    enable_overall_tracking_for_camera = (
        lambda: REFS.states.level_manager.enable_overall_tracking_for_camera()
    ),

    disable_overall_tracking_for_camera = (
        lambda: REFS.states.level_manager.disable_overall_tracking_for_camera()
    ),

    enable_feet_tracking_for_camera = (
        lambda: REFS.states.level_manager.enable_feet_tracking_for_camera()
    ),

    disable_feet_tracking_for_camera = (
        lambda: REFS.states.level_manager.disable_feet_tracking_for_camera()
    ),

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

###

WRITEABLE_PATH = Path(get_pref_path(ORG_DIR_NAME, APP_DIR_NAME))

SAVE_SLOTS_DIR = WRITEABLE_PATH / 'save_slots'

def has_save_slots():

    return any(

        path

        for path in SAVE_SLOTS_DIR.iterdir()
        if path.suffix.lower() == '.pyl'

    )

def get_custom_formated_current_datetime_str():

    now = datetime.now().astimezone()

    timestamp = now.isoformat()[:19].replace('T', ' ')
    tz = now.tzname()
    signal = tz[0]
    signal_name = 'minus' if signal == '-' else 'plus'
    offset = tz[1:]

    return f'{timestamp} {signal_name} {offset}'

# XXX what if path exists but is a file instead? I know, unlikely scenario,
# but not covered; same for playtest data dir and probably other paths
# (files/directories) as well; ponder and act on it.

if not SAVE_SLOTS_DIR.exists():

    try:
        SAVE_SLOTS_DIR.mkdir()

    except Exception as err:
        print("Couldn't create folder for save slots")

###

PLAYTEST_DATA_DIR = WRITEABLE_PATH / 'playtest_data'

if not PLAYTEST_DATA_DIR.exists():

    with suppress(Exception):
        PLAYTEST_DATA_DIR.mkdir()



###

def quit_game():

    quit_pygame()
    quit()
