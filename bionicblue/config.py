"""General configuration for game."""

### standard library import

from pathlib import Path

from datetime import datetime

from shutil import copyfile



### third-party imports

from pygame import quit as quit_pygame

from pygame.system import get_pref_path


### local imports

from .appinfo import ORG_DIR_NAME, APP_DIR_NAME, APP_VERSION_STRING

from .ourstdlibs.pyl import save_pyl, load_pyl

from .ourstdlibs.ziputils import ZIP_COMPRESSION_AVAILABLE


### further conditional standard library imports
###
### if zip compression is available, import utilities from zipfile,
### pprint and ast, which we'll use to save compressed Python literals
### as .zip files

if ZIP_COMPRESSION_AVAILABLE:

    from zipfile import ZIP_DEFLATED, ZipFile

    from pprint import pformat
    from ast import literal_eval



###
COLORKEY = (192, 192, 192)

###

class LoopException(Exception):
    """Raised for a variety of purposes.

    The purposes may be one or more of these:

    1. simply skip back to the beginning of the loop
    2. indicate next state (loop holder)
    3. indicate next play mode (normal, record, replay)
    4. indicate need to prepare state
    5. indicate need to clear tasks
    """

    def __init__(
        self,
        *,
        next_state=None,
        next_play_mode_name='',
        prepare=False,
        clear_tasks=False,
    ):

        self.state = next_state
        self.play_mode_name = next_play_mode_name
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

    replay_fps = None,

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


### playlogging compressing (when available), saving and rotating

if ZIP_COMPRESSION_AVAILABLE:

    NO_OF_REGULAR_LOGS = 40
    NO_OF_FIRST_LOGS = 20

else:

    NO_OF_REGULAR_LOGS = 20
    NO_OF_FIRST_LOGS = 10

POSSIBLE_LOG_EXTENSIONS = frozenset(

    (
        ('.pyl',),
        ('.pyl', '.zip'),
    )

)

def has_play_log_extension(path):

    return tuple(

        item.lower()
        for item in path.suffixes

    ) in POSSIBLE_LOG_EXTENSIONS

def remove_extensions(filename):

    return (

        filename[:filename.index('.')]
        if '.' in filename

        else filename

    )

# keyword arguments for pprint.pformat() and functions that use it

PFORMAT_KWARGS = {
  'indent': 2,
  'width': 180,
  'compact': True,
}


def save_and_rotate_play_data(play_data, filename_without_extension):
    """Manage compression, saving and rotation of play data as logs."""

    ## save play data, with or without compression, depending on availability
    ## of compression

    if ZIP_COMPRESSION_AVAILABLE:

        ## build log path

        latest_log_path = (
            REGULAR_PLAY_LOGS_DIR
            / f'{filename_without_extension}.pyl.zip'

        )

        filename = f'{filename_without_extension}.pyl'

        ## create archive and save play data in it after turning such data
        ## into pretty-formatted string

        with ZipFile(

            str(latest_log_path),
            mode='w',
            compression=ZIP_DEFLATED,

        ) as archive:

            archive.writestr(

                filename,

                ## formatted string representing play data
                pformat(play_data, **PFORMAT_KWARGS)

            )


    else:

        ## save data (save_pyl() already takes care of turning the data into
        ## a formatted string)

        latest_log_path = (
            REGULAR_PLAY_LOGS_DIR
            / f'{filename_without_extension}.pyl'

        )

        save_pyl(play_data, latest_log_path, **PFORMAT_KWARGS)

    ### if first play logs don't add up to specified number of files yet
    ### (it must not exceed this quantity), copy latest added path into it;
    ###
    ### first play logs are the very first play sessions and are used for
    ### playtesting; but attention: no data ever leaves your disk; the only
    ### way for the developer to access this data is if you share it yourself,
    ### which I'd appreciate a lot ;) - you just contact me via social
    ### networks or discord and I'll get back to you on how to do that

    if len([

        path
        for path in FIRST_PLAY_LOGS_DIR.iterdir()

        if path.name.startswith('play_at_')
        if has_play_log_extension(path)

    ]) < NO_OF_FIRST_LOGS:

        source = latest_log_path
        destination = FIRST_PLAY_LOGS_DIR / latest_log_path.name

        copyfile(str(source), str(destination))

    ### ensure regular play logs only has at most the specified number
    ### of files, making sure to erase the older ones in case this number
    ### is exceeded

    ## sort regular log paths by name

    sorted_regular_log_paths = sorted(

        (
            path
            for path in REGULAR_PLAY_LOGS_DIR.iterdir()

            if path.name.startswith('play_at_')
            if has_play_log_extension(path)

        ),

        key = lambda item: remove_extensions(item.stem.lower())

    )

    ## grab set with paths of "n" most recent paths

    n = NO_OF_REGULAR_LOGS
    most_recent_paths = set(sorted_regular_log_paths[-n:])

    ## delete existing paths not listed among most recent ones

    for path in sorted_regular_log_paths:

        if path not in most_recent_paths:
            path.unlink()



def get_play_data(directive, replay_fps=''):

    if replay_fps:

        try:
            replay_fps = int(replay_fps)

        except Exception:
            raise ValueError("given fps for replay must be an integer")

        else:
            REFS.replay_fps = replay_fps
    ###

    try:

        path = Path(directive)

        is_play_log_file = (
            path.is_file()
            and has_play_log_extension(path)
        )

    except Exception:
        is_play_log_file = False


    if not is_play_log_file:

        try:
            index = int(directive)

        except Exception:

            if directive == 'last':

                folder = REGULAR_PLAY_LOGS_DIR
                index = -1

            else:

                raise ValueError(
                    "Couldn't find play data with provided directive."
                )

        else:

            if index >= 0:

                raise ValueError(
                    "If directive represents integer, it must be negative,"
                    " representing the most recent sessions."
                )

            folder = REGULAR_PLAY_LOGS_DIR


        sorted_paths = sorted(

            (

                path
                for path in folder.iterdir()

                if path.name.startswith('play_at_')
                if has_play_log_extension(path)

            ),

            key = lambda item: remove_extensions(item.stem.lower())

        )

        try:
            path = sorted_paths[index]

        except IndexError:
            raise ValueError(f"No play data with provided index: {index}")

    ### create flag indicating whether the path has a zip extension
    has_zip_extension = path.suffix.lower() == '.zip'

    ### in case the path has indeed a zip extension, only proceed if
    ### compression/decompression is available

    if has_zip_extension and not ZIP_COMPRESSION_AVAILABLE:

        raise ValueError(
            "Can't replay log file because it is a zip file and we don't"
            " have zip decompression available via zlib.decompress();"
            " perhaps if you decompress the file on your end (turning it"
            " into a '.pyl' file rather than a '.pyl.zip' file) it may be"
            " possible to replay it"
        )

    ### if file has a zip extension, safely turn a string obtained from
    ### the decompressed contents into a Python literal with literal_eval()

    if has_zip_extension:

        ## the contents are inside a file with similar name, but without the
        ## zip extension; we can use the stem for that, the part without the
        ## last extension
        filename = path.stem

        ## open the archive, extract the decompressed data and turn it into
        ## the play data

        with ZipFile(str(path), mode='r') as archive:

            play_data = (

                literal_eval(

                    ## get the contents as bytes
                    archive.read(filename)

                    ## then decode as an utf-8 string
                    .decode(encoding='utf-8')
                )

            )

    ### otherwise, the load the content of the file with a custom function
    ### that reads the text of the file and turns it into a Python literal
    ### for us (also using literal_eval())

    else:
        play_data = load_pyl(path)

    ### replaying play data doesn't make sense unless the play is
    ### reproduced in the same version where it was recorded; so
    ### abort replay if the version isn't the same as the current one;
    ###
    ### why this is important:
    ###
    ### say you are loading play data from a previous version where
    ### the level layout was different: the playable character would
    ### act in a different space; many other different factors also
    ### cause problems like that, like enemies requiring a different
    ### amount of damage to be destroyed, etc.; even strictly visual
    ### changes make a difference: since play data is used for
    ### playtesting analysis as well, we want to make sure all the
    ### actions performed by the player are reactions to what the
    ### player sees in that version, so we can make more accurate
    ### assumptions; changes in the play logging system may also
    ### cause play data from different versions to be incompatible;
    ### in the end, play data produced in a specific version can only
    ### be safely/accurately reproduced in that same version;

    app_version_string = play_data['app_version_string']

    if app_version_string != APP_VERSION_STRING:

        raise ValueError(
            "Play data recorded in different version."
            f" Ours: {APP_VERSION_STRING};"
            f" Play data's: {app_version_string}"
        )

    return play_data


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

def save_recorded_data_if_any(reason_for_stopping):

    gns = REFS._general_ns

    if gns.play_mode_name == 'record':
        gns.save_play_data(reason_for_stopping)

def quit_game():

    save_recorded_data_if_any(reason_for_stopping='quitting_game')

    if REFS._general_ns.play_mode_name == 'replay':
        REFS._general_ns.leave_to_main_menu('red')

    else:

        quit_pygame()
        quit()
