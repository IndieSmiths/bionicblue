"""General configuration for game."""

### standard library import

from pathlib import Path

from contextlib import suppress


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

    msecs = 0,

    data = {
        'level_name': 'intro.lvl',
        'health': 100,
    },

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

FONTS_DIR = DATA_DIR / 'fonts'
IMAGES_DIR = DATA_DIR / 'images'
ANIMATIONS_DIR = DATA_DIR / 'animations'
SOUNDS_DIR = DATA_DIR / 'sounds'
MUSIC_DIR = DATA_DIR / 'music'
LEVELS_DIR = DATA_DIR / 'levels'
PARTICLES_DIR = DATA_DIR / 'particles'

NO_COLORKEY_IMAGES_DIR = IMAGES_DIR  / 'no_colorkey'
COLORKEY_IMAGES_DIR = IMAGES_DIR  / 'colorkey'

###

SURF_MAP = {}
ANIM_DATA_MAP = {}
SOUND_MAP = {}

###

WRITEABLE_PATH = Path(get_pref_path(ORG_DIR_NAME, APP_DIR_NAME))

SAVE_SLOTS_DIR = WRITEABLE_PATH / 'save_slots'

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
