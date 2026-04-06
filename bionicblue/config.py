"""General configuration for game."""

### standard library import

from pathlib import Path

from datetime import datetime

from shutils import copyfile


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
LANGUAGE_ICON_FILEPATH = DATA_DIR / 'language_icon.png'

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


def manage_play_data_rotation(latest_added_path):
    """Ensure old play data files are deleted and first ones are backed up."""

    ### if first play logs doesn't have 10 files yet (it must not exceed this
    ### quantity), copy latest added path into it;
    ###
    ### first play logs are the very first 10 play sessions and are used for
    ### playtesting; but attention: no data ever leaves your disk; the only
    ### way for the developer to access this data is if you share it yourself,
    ### which I'd appreciate a lot ;) - you just contact me via social
    ### networks or discord and I'll get back to you on how to do that

    if len([

        path
        for path in FIRST_PLAY_LOGS_DIR.iterdir()

        if path.suffix.lower() == '.pyl'
        if path.name.startswith('play_at_')

    ]) < 10:

        source = latest_added_path
        destination = FIRST_PLAY_LOGS_DIR / latest_added_path.name

        copyfile(str(source), str(destination))

    ### ensure regular play logs only has at most 20 files, making sure to
    ### erase the older ones in case this number is exceeded

    ## sort regular log paths by name

    sorted_regular_log_paths = sorted(

        (
            path
            for path in REGULAR_PLAY_LOGS_DIR

            if path.suffix.lower() == '.pyl'
            if path.name.startswith('play_at_')
        ),

        key = lambda item: item.name.lower()

    )

    ## grab set with paths of 10 most recent paths
    most_recent_paths = set(sorted_regular_log_paths[-10:])

    ## delete existing paths not listed among most recent ones

    for path in sorted_regular_log_paths:

        if path not in most_recent_paths:
            path.unlink()


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


### constructs to keep track of one-off events
###
### this data is useful to trigger measures that only happen once, when
### something happens for the first time.
###
### For instance, the "thank you for playing" message is presented only
### when the player clears a mission for the first time since the app was
### installed

ONE_OFF_FILEPATH = WRITEABLE_PATH / 'one_off_events.pyl'

DEFAULT_ONE_OFF_DATA = {
    'cleared_a_mission': False,
    'chose_a_locale': False,
}

ONE_OFF_DATA = {}

def save_one_off_data():
    save_pyl(ONE_OFF_DATA, ONE_OFF_FILEPATH)

if ONE_OFF_FILEPATH.exists():

    try:
        data = load_pyl(ONE_OFF_FILEPATH)

    except Exception:

        print("Couldn't load one off events data, using defaults instead.")

        ONE_OFF_DATA.update(DEFAULT_ONE_OFF_DATA)
        save_one_off_data()

    else:

        if (

            not isinstance(data, dict)
            or not data.keys() == DEFAULT_ONE_OFF_DATA.keys()
            or any(
                not isinstance(value, bool)
                for value in data.values()
            )

        ):

            ONE_OFF_DATA = DEFAULT_ONE_OFF_DATA.copy()
            save_one_off_data()

        else:
            ONE_OFF_DATA = data

else:

    ONE_OFF_DATA = DEFAULT_ONE_OFF_DATA.copy()
    save_pyl(ONE_OFF_DATA, ONE_OFF_FILEPATH)


def did_player_ever(event_name):

    ## if player already performed the event...

    if ONE_OFF_DATA[event_name]:
        return True

    ## otherwise, this is the first time, so...

    else:

        ### set the event to True so next time it is check it is marked
        ### as having happened before (this very time)

        ONE_OFF_DATA[event_name] = True
        save_one_off_data()

        ## return False to indicate the player didn't do it before (it
        ## is happening for the firs time now)
        return False

def quit_game():

    quit_pygame()
    quit()
