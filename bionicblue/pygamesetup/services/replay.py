
### standard library imports

from pathlib import Path

from collections import defaultdict

from functools import reduce

from itertools import cycle, repeat

from operator import or_ as bitwise_or

from copy import deepcopy

from tempfile import mkstemp


### third-party imports

from pygame.mixer import music

from pygame.locals import (

    QUIT,

    KEYDOWN,
    K_F7, K_F8, K_F9,

    MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP,

    KMOD_NONE,

)

from pygame.color import THECOLORS

from pygame import locals as pygame_locals

from pygame.math import Vector2

from pygame.event import Event, get, set_allowed, set_blocked

from pygame.mouse import set_pos, set_visible as set_mouse_visibility

from pygame.draw import rect as draw_rect

from pygame.display import update


### local imports

from ...config import REFS, MUSIC_DIR, LoopException, quit_game

from ...ourstdlibs.pyl import load_pyl, save_pyl

from ...classes2d.single import UIObject2D

from ...textman import render_text

from ...userprefsman.main import (
    USER_PREFS,
    KEYBOARD_CONTROL_NAMES,
    KEYBOARD_CONTROLS,
    GAMEPAD_CONTROLS,
)

from ...translatedtext import on_language_change

from ..gamepadservices.common import GAMEPAD_NS

from ..constants import (

    SCREEN, SCREEN_RECT, blit_on_screen,
    GENERAL_NS,
    GENERAL_SERVICE_NAMES,
    FPS,
    SIZE,
    maintain_fps,

    CancelWhenPaused, pause,

    USER_EVENT_NAMES_MAP,
    EVENT_KEY_STRIP_MAP,
    EVENT_COMPACT_NAME_MAP,
    EVENT_KEY_COMPACT_NAME_MAP,
    KEYS_MAP,
    SCANCODE_NAMES_MAP,
    MOD_KEYS_MAP,

)



### dictionary to store session data
SESSION_DATA = {}

### custom namespace for replay mode
REPLAY_REFS = type("Object", (), {})()

### map to store events
EVENTS_MAP = defaultdict(list)

## create a map to associate each frame index to the keys that were
## pressed at that frame
GETTER_FROZENSET_MAP = {}

### create a map that associates each frame index to the modifier
### keys that were pressed in that frame
BITMASK_MAP = {}

### create a list to hold all mouse position requests;
MOUSE_POSITIONS = []

### create list to hold all mouse key pressed state requests
MOUSE_PRESSED_TUPLES = []

### create virtual mouse
MOUSE_POS = Vector2(0, 0)

### create flag indicating whether real mouse must trace movements
### of virtual one
REPLAY_REFS.mouse_tracing = True

### special frozenset class

class GetterFrozenSet(frozenset):
    """frozenset subclass where "obj[item]" works like "item in obj"."""
    __getitem__ = frozenset.__contains__

## create an empty special frozenset
EMPTY_GETTER_FROZENSET = GetterFrozenSet()



### XXX collections defined below lack proper commenting

REVERSE_EVENT_COMPACT_NAME_MAP = {
    value: key
    for key, value in EVENT_COMPACT_NAME_MAP.items()
}

REVERSE_SCANCODE_NAMES_MAP = {
    value: key
    for key, value in SCANCODE_NAMES_MAP.items()
}

REVERSE_USER_EVENT_NAMES_MAP = {
    value: key
    for key, value in USER_EVENT_NAMES_MAP.items()
}

##

def set_behaviour(services_namespace, play_data):
    """Setup replay services and data."""

    ### grab replay services from our globals (module-level names)
    ### and set them as attributes of the services namespace

    our_globals = globals()

    for attr_name in GENERAL_SERVICE_NAMES:

        value = our_globals[attr_name]
        setattr(services_namespace, attr_name, value)

    SESSION_DATA.update(play_data)

    ### setup initial context

    ## slot data and path

    REFS.slot_data = slot_data = SESSION_DATA['slot_data']
    REFS.slot_path = slot_path = Path(mkstemp(suffix='.pyl', text=True)[1])

    save_pyl(slot_data, slot_path)

    ## back up current locale use the one indicated in the play data

    REPLAY_REFS.locale = USER_PREFS['LOCALE']

    if SESSION_DATA['locale'] != USER_PREFS['LOCALE']:

        USER_PREFS['LOCALE'] = SESSION_DATA['LOCALE']
        on_language_change()

    ## back up current keyboard and gamepad controls and use the ones 
    ## provided by the play data

    REPLAY_REFS.keyboard_control_names = deepcopy(KEYBOARD_CONTROL_NAMES)
    REPLAY_REFS.gamepad_controls = deepcopy(GAMEPAD_CONTROLS)

    for action_name, key_name in (
        SESSION_DATA['keyboard_control_names'].items()
    ):

        KEYBOARD_CONTROLS[action_name] = getattr(pygame_locals, key_name)

    GAMEPAD_CONTROLS.update(SESSION_DATA['gamepad_controls'])

    ## level to load and last_checkpoint_name

    REFS.level_to_load = SESSION_DATA['level_to_load']
    REFS.last_checkpoint_name = SESSION_DATA['last_checkpoint_name']

    ### retrieve playback speed and last frame index

    playback_speed = FPS
    last_frame_index = SESSION_DATA['last_frame_index']

    ### store playback speed, last frame index and recording width

    REPLAY_REFS.fps = playback_speed
    REPLAY_REFS.last_frame_index = last_frame_index

    ### print duration


    if playback_speed:

        duration = (

            get_formatted_duration(
                frame_quantity=last_frame_index,
                frames_per_second=playback_speed,
            )

        )

        duration_text = f"Duration: ~{duration}"

    else:
        duration_text = "No duration (uncapped speed)"

    print(duration_text)

    ### since the app will be replaying recorded events, we are not interested
    ### in most of the new ones generated while replaying, so we block most of
    ### them, leaving just a few that we may use during replay

    set_blocked(None)
    set_allowed([QUIT, KEYDOWN])

    ### populate events map with reference to events in the frames where they
    ### occur

    for (

        (
            event_name,
            tuplefied_event_data,
        ),

        frame_set,

    ) in SESSION_DATA['event_frames_pairs']:

        event_instance = get_processed_event(event_name, tuplefied_event_data)

        for frame_index in frame_set:
            EVENTS_MAP[frame_index].append(event_instance)

    ### prepare key states

    ## convert from compact to suitable format to use

    frame_to_keys_map = defaultdict(list)

    for key_name, frames in SESSION_DATA['key_name_to_frames_map'].items():

        for frame in frames:
            frame_to_keys_map[frame].append(key_name)


    ## update map with frozensets

    GETTER_FROZENSET_MAP.update(

        (
            frame_index,

            GetterFrozenSet(
                getattr(pygame_locals, key_name)
                for key_name in pressed_key_names
            )

        )

        for frame_index, pressed_key_names
        in frame_to_keys_map.items()

    )


    ### prepare modifier key states

    ## convert from compact to suitable format to use

    frame_to_mod_key_names = defaultdict(list)

    for mod_key_name, frames in SESSION_DATA['mod_key_name_to_frames_map'].items():

        for frame in frames:
            frame_to_mod_key_names[frame].append(mod_key_name)

    ## update map with bitmasks

    BITMASK_MAP.update(

        (
            frame_index,

            (

                ## if there's only one modifier key pressed, get its value
                ## from pygame.locals
                getattr(pygame_locals, mod_key_names[0])
                if len(mod_key_names) == 1

                ## otherwise get the bitmask that results from combining
                ## the values of all pressed modifiers
                else get_resulting_bitmask(mod_key_names)

            )

        )

        for frame_index, mod_key_names
        in frame_to_mod_key_names.items()
    )

    ### update list containing all mouse position requests;
    ###
    ### then reverse its orders so the first ones are the first
    ### ones to be popped from the list

    MOUSE_POSITIONS.extend(SESSION_DATA['mouse_pos_requests'])
    MOUSE_POSITIONS.reverse()

    ### do the same as above to list of all mouse key pressed
    ### state requests (create and reverse it)

    MOUSE_PRESSED_TUPLES.extend(SESSION_DATA['mouse_key_state_requests'])
    MOUSE_PRESSED_TUPLES.reverse()

    ### reference function to execute setups when exitting replay mode

    GENERAL_NS.perform_replay_mode_exit_setups = (
        perform_replay_mode_exit_setups
    )

    ### set frame index to -1 (so when it is incremented at the beginning
    ### of the loop it is set to 0, the first frame)
    GENERAL_NS.frame_index = -1


def get_processed_event(event_name, tuplefied_event_data):
    """Return pygame.event.Event instances from given data."""

    event_dict = {
        key: value
        for key, value in tuplefied_event_data
    }

    ### restore the event name if it was in a custom compact form

    if event_name in REVERSE_EVENT_COMPACT_NAME_MAP:
        event_name = REVERSE_EVENT_COMPACT_NAME_MAP[event_name]

    ### restore names of keys in the event name if they were in a
    ### custom compact form

    if event_name in EVENT_KEY_COMPACT_NAME_MAP:

        for full_key, compact_key in (
            EVENT_KEY_COMPACT_NAME_MAP[event_name].items()
        ):

            if compact_key in event_dict:
                event_dict[full_key] = event_dict.pop(compact_key)

    ### restore missing keys in the event using default values

    if event_name in EVENT_KEY_STRIP_MAP:

        for key, default in EVENT_KEY_STRIP_MAP[event_name].items():
            event_dict.setdefault(key, default)

    ### if dealing with KEY_... events, perform extra preprocessing
    ### in the event dict

    if event_name in ('KEYUP', 'KEYDOWN'):

        ## turn key name and scan code name into the respective
        ## values

        for key, treatment_operation in (

            ('key', KEYS_MAP.__getitem__),
            ('scancode', REVERSE_SCANCODE_NAMES_MAP.__getitem__),

        ):
            event_dict[key] = treatment_operation(event_dict[key])

        ## if the 'mod' key is a tuple, it contains names of
        ## modifiers, so replace it by the respective bitmask
        ## that represent the modifiers

        if type(event_dict['mod']) is tuple:

            ## get names
            mod_key_names = event_dict['mod']

            ## reassign value to 'mod'
            event_dict['mod'] = (

                # if there's only one name, just use the key value
                getattr(pygame_locals, mod_key_names[0])
                if len(mod_key_names) == 1

                # otherwise build the bitmask with all modifier
                # values
                else get_resulting_bitmask(mod_key_names)

            )

    ### if dealing with JOYBUTTON... events, replace action name in
    ### 'button' key by the respective button id

    if event_name in ('JOYBUTTONUP', 'JOYBUTTONDOWN'):
        event_dict['button'] = GAMEPAD_CONTROLS[event_dict['button']]

    ### obtain the event type

    event_type = (

        REVERSE_USER_EVENT_NAMES_MAP[event_name]
        if event_name in REVERSE_USER_EVENT_NAMES_MAP

        else getattr(pygame_locals, event_name)

    )

    ### return pygame.event.Event object
    return Event(event_type, event_dict)


def get_resulting_bitmask(mod_key_names):
    """Return bitmask by reducing all modifier keys with bitwise OR."""

    ### return iterable reduced to a single value...

    return reduce(

        ## with the bitwise OR operation
        bitwise_or,

        ## where the iterable contained the values
        ## of the named modifier keys

        (
            # modifier key value obtained from its name
            getattr(pygame_locals, mod_key_name)

            # modifier key names
            for mod_key_name in mod_key_names
        ),

    )



### constants


## set with mouse event types
MOUSE_EVENTS = frozenset({MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP})



### session behaviours

## processing events

def get_events():

    ### process QUIT or KEYDOWN event (for the F9 key) if
    ### they are thrown

    for event in get():

        if event.type == QUIT:
            quit_game()

        elif event.type == KEYDOWN:

            ### pause replaying

            if event.key == K_F8:

                ### pause

                try:
                    pause()

                ### if during pause user asks to cancel replaying, do
                ### it here

                except CancelWhenPaused:
                    leave_replay_mode_earlier()

            ### toggle mouse tracing

            elif event.key == K_F9:
                REPLAY_REFS.mouse_tracing = not REPLAY_REFS.mouse_tracing

            ### leave replaying mode earlier

            elif event.key == K_F7:
                leave_replay_mode_earlier()

    ### replay the recorded events

    ## if there are events for the current frame index in the event map,
    ## iterate over them

    if GENERAL_NS.frame_index in EVENTS_MAP:

        for event in EVENTS_MAP[GENERAL_NS.frame_index]:

            ## if we have a mouse event, we use it to position the mouse
            if event.type in MOUSE_EVENTS:
                set_mouse_pos(event.pos)

            ## finally yield the event, regardless of its type
            yield event


## processing key pressed states

def get_pressed_keys():
    """Emulates pygame.key.get_pressed().

    That is, the return value despite being a different object, works
    just like the return value of pygame.key.get_pressed().
    """

    return (

        ### return a GetterFrozenSet for the current
        ### frame index if there's one
        GETTER_FROZENSET_MAP[GENERAL_NS.frame_index]
        if GENERAL_NS.frame_index in GETTER_FROZENSET_MAP

        ### otherwise return an empty GetterFrozenSet
        else EMPTY_GETTER_FROZENSET

    )


## processing modifier key pressed states

def get_pressed_mod_keys():
    """Emulates pygame.key.get_mods().

    That is, the return value is also a bitmask or pygame.locals.KMOD_NONE.
    """

    return (

        ### return a bitmask for the current frame index if there's one
        BITMASK_MAP[GENERAL_NS.frame_index]
        if GENERAL_NS.frame_index in BITMASK_MAP

        ### otherwise return pygame.locals.KMOD_NONE
        else KMOD_NONE

    )


## processing mouse position getting and setting

def get_mouse_pos():
    """Emulates pygame.mouse.get_pos(); performs additional setups."""
    ### grab recorded position
    pos = MOUSE_POSITIONS.pop()

    ### set mouse pointer to the position
    set_mouse_pos(pos)

    ### return position
    return pos


def set_mouse_pos(pos):
    """Extends pygame.mouse.set_pos()."""
    ### update position of virtual mouse with given pos
    MOUSE_POS.update(pos)

    ### if mouse tracing is on, set position of real mouse as well,
    ### (using pygame.mouse.set_pos())
    ###
    ### this is done so that the real mouse traces the movement of the
    ### virtual one
    REPLAY_REFS.mouse_tracing and set_pos(pos)


## processing mouse button pressed state;
##
## this get_mouse_pressed() callable is used to emulate the
## pygame.mouse.get_pressed() function and return the same kind
## of value
get_mouse_pressed = MOUSE_PRESSED_TUPLES.pop


### screen updating

SCREEN_WIDTH = SIZE[0]

def update_screen():
    """Extends pygame.display.update()."""
    ### draw progress

    width = round(

        # progress percentage
        abs(GENERAL_NS.frame_index / REPLAY_REFS.last_frame_index)

        # full width
        * SCREEN_WIDTH
    )

    draw_rect(SCREEN, 'red', (0, 0, width, 1))

    ### update the screen
    update()

### other operations

def leave_replay_mode_earlier():

    perform_replay_mode_exit_setups()

    music_volume = (
        (USER_PREFS['MASTER_VOLUME']/100)
        * (USER_PREFS['MUSIC_VOLUME']/100)
    )

    music.set_volume(music_volume)
    music.load(str(MUSIC_DIR / 'title_screen_by_juhani_junkala.ogg'))
    music.play(-1)

    REFS.states.level_manager.cleanup()

    raise LoopException(
        next_state=REFS.states.main_menu,
        clear_tasks=True,
        prepare=True,
        next_play_mode_name='normal',
    )

def perform_replay_mode_exit_setups():

    ## restore locale if needed

    if USER_PREFS['LOCALE'] != REPLAY_REFS.locale:

        USER_PREFS['LOCALE'] = REPLAY_REFS.locale
        on_language_change()

    ### restore controls

    for action_name, key_name in REPLAY_REFS.keyboard_control_names.items():
        KEYBOARD_CONTROLS[action_name] = getattr(pygame_locals, key_name)

    GAMEPAD_CONTROLS.update(REPLAY_REFS.gamepad_controls)

    ### clear stored data
    clear_data()

    ### delete temporary file
    REFS.slot_path.unlink()

def clear_data():

    ### clear collections

    for collection in (
        EVENTS_MAP,
        GETTER_FROZENSET_MAP,
        BITMASK_MAP,
        MOUSE_POSITIONS,
        MOUSE_PRESSED_TUPLES,
    ):
        collection.clear()

    GAMEPAD_NS.clear_data()


### frame checkup operation

def frame_checkups():
    """Perform various checkups.

    Meant to be used at the beginning of each frame in the
    app loop.
    """
    ### keep constants fps
    maintain_fps(REPLAY_REFS.fps)

    ### increment frame number
    GENERAL_NS.frame_index += 1

    ### store data and post custom events for gamepad
    ### directional triggers
    GAMEPAD_NS.prepare_data_and_events()


### small utility

def get_formatted_duration(frame_quantity, frames_per_second):
    """Return specially formatted duration."""
    duration = ""

    total_seconds = round(frame_quantity/frames_per_second)

    minutes, seconds = divmod(total_seconds, 60)

    if minutes >= 1:

        duration += f"{minutes}min"

        if minutes >= 2:
            duration += "s"

    if seconds >= 1:

        duration += f"{seconds}sec"

        if seconds >= 2:
            duration += "s"

    return duration
