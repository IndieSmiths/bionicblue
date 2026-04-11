
### standard library imports

from collections import defaultdict

from datetime import datetime

from copy import deepcopy


### third-party imports

from pygame.locals import KMOD_NONE

from pygame.event import clear, get, event_name as get_event_name

from pygame.key import get_pressed, get_mods

from pygame.mouse import (

    get_pos,
    get_pressed as mouse_get_pressed,

    # check note [1] at the bottom
    set_pos as set_mouse_pos,

    # check note [2] at the bottom
    set_visible as set_mouse_visibility,
)

from pygame.display import update as update_screen


### local imports

from ...config import (
    REFS,
    LoopException,
    save_and_rotate_play_data,
)

from ...classes2d.single import UIObject2D

from ...textman import render_text

from ...userprefsman.main import (
    USER_PREFS,
    KEYBOARD_CONTROL_NAMES,
    GAMEPAD_CONTROLS,
)

from ...appinfo import APP_VERSION_STRING

from ..gamepadservices.common import GAMEPAD_NS

from ..constants import (

    SCREEN_RECT, blit_on_screen,
    GENERAL_NS,
    GENERAL_SERVICE_NAMES,
    FPS, maintain_fps,

    EVENT_KEY_STRIP_MAP,
    EVENT_COMPACT_NAME_MAP,
    EVENT_KEY_COMPACT_NAME_MAP,
    KEYS_MAP,
    REVERSE_KEYS_MAP,
    SCANCODE_NAMES_MAP,
    MOD_KEYS_MAP,

    USER_EVENT_NAMES_MAP,

)



### control and data-recording objects


## constants

## namespace
REC_REFS = type("Object", (), {})()


EVENTS_MAP = defaultdict(list)

KEY_STATE_REQUESTS = []
append_key_states = KEY_STATE_REQUESTS.append

MOD_KEY_BITMASK_REQUESTS = []
append_mod_key_states = MOD_KEY_BITMASK_REQUESTS.append

MOUSE_POS_REQUESTS = []
append_mouse_pos_request = MOUSE_POS_REQUESTS.append

MOUSE_KEY_STATE_REQUESTS = []
append_mouse_key_state_request = MOUSE_KEY_STATE_REQUESTS.append


### events to keep in the recorded data;
###
### all other events aren't relevant because it is not possible for
### them to show up in recorded sessions (like video resizing events
### or QUIT) or simply because they are not used in the app, so we
### do not care to record them;
###
### this set must be updated whenever the app starts using other
### events not listed here (for instance, for new features)

NAMES_OF_EVENTS_TO_KEEP = frozenset((
    'JOYBUTTONDOWN',
    'JOYBUTTONUP',
    'KEYDOWN',
    'KEYUP',
    'MOUSEBUTTONDOWN',
    'MOUSEBUTTONUP',
    'MOUSEMOTION',
    *USER_EVENT_NAMES_MAP.values(),
))


### create frozenset holding names of user events
USER_EVENT_NAMES = frozenset(USER_EVENT_NAMES_MAP.values())

### timestamp format string
TIMESTAMP_FORMAT_STRING = 'Y%YM%mD%d_H%HM%MS%S'


###

def set_behaviour(services_namespace):
    """Setup record services and data."""

    ### grab recording services from our globals (module-level names)
    ### and set them as attributes of the services namespace

    our_globals = globals()

    for attr_name in GENERAL_SERVICE_NAMES:

        value = our_globals[attr_name]
        setattr(services_namespace, attr_name, value)

    ### create and store a filename (without extension/suffix) for file
    ### wherein we'll store data when recording is over

    REC_REFS.filename_without_extension = (
        'play_at_'
        + datetime.now().strftime(TIMESTAMP_FORMAT_STRING)
    )

    ### store copy of initial data

    ## slot data
    REC_REFS.slot_data = deepcopy(REFS.slot_data)

    ## keyboard and gamepad controls

    REC_REFS.keyboard_control_names = deepcopy(KEYBOARD_CONTROL_NAMES)
    REC_REFS.gamepad_controls = deepcopy(GAMEPAD_CONTROLS)

    ## create new dict from gamepad controls where keys and values are reversed

    REC_REFS.gamepad_button_id_to_action_name = {

        button_id: action_name
        for action_name, button_id in REC_REFS.gamepad_controls.items()

    }

    ## level to load and last_checkpoint_name

    REC_REFS.level_to_load = REFS.level_to_load
    REC_REFS.last_checkpoint_name = REFS.last_checkpoint_name

    ## locale
    REC_REFS.locale = USER_PREFS['LOCALE']

    ## app version
    REC_REFS.app_version_string = APP_VERSION_STRING


    ## clear any existing events
    clear()

    ## set frame index to -1 (so it is set to 0 at the beginning
    ## of the loop, the first frame)
    GENERAL_NS.frame_index = -1

    ## reference function to save recorded data
    GENERAL_NS.save_play_data = save_play_data


### extended session behaviours

## processing events

def get_events():

    ### handle/yield events;
    ###
    ### note that we do not handle the QUIT event here; rather,
    ### it is handled by whichever object receives the yielded
    ### event;
    ###
    ### it will usually cause a QuitAppException to be raised,
    ### which causes the app to close immediately when in record
    ### mode (in play mode as well)

    for event in get():

        ### record event

        EVENTS_MAP[GENERAL_NS.frame_index].append([
            event.type,
            event.__dict__
        ])

        ### yield it
        yield event

## processing key pressed states

def get_pressed_keys():

    # get key states
    key_states = get_pressed()

    # record them
    append_key_states((GENERAL_NS.frame_index, key_states))

    # return them
    return key_states

def get_pressed_mod_keys():

    # get mod bistmask
    mods_bitmask = get_mods()

    # record it
    append_mod_key_states((GENERAL_NS.frame_index, mods_bitmask))

    # return it
    return mods_bitmask

## processing mouse

def get_mouse_pos():

    # get mouse pos
    pos = get_pos()

    # record it
    append_mouse_pos_request(pos)

    # return it
    return pos

def get_mouse_pressed():

    # get mouse pressed tuple
    pressed_tuple = mouse_get_pressed()

    # record it
    append_mouse_key_state_request.append(pressed_tuple)

    # return it
    return pressed_tuple


### frame checkup operation

def frame_checkups():
    """Perform various checkups.

    Meant to be used at the beginning of each frame in the
    app loop.
    """
    ### keep constants fps
    maintain_fps(FPS)

    ### increment frame number
    GENERAL_NS.frame_index += 1

    ### store data and post custom events for gamepad
    ### directional triggers
    GAMEPAD_NS.prepare_data_and_events()

### session data saving operations

def save_play_data():

    session_data = {}

    ### process event map

    ## create

    events_map = session_data['events_map'] = {

        frame_index : list(yield_treated_events(events))
        for frame_index, events in EVENTS_MAP.items()

    }

    ## remove keys whose values (a list of events) ended up empty,
    ## (if any)

    keys_to_pop = [

        # item
        key

        # source
        for key, event_list in events_map.items()

        # filtering condition
        if not event_list

    ]

    for key in keys_to_pop:
        events_map.pop(key)

    ### store data

    session_data['key_name_to_frames_map'] = (
        get_key_to_frames_map(KEY_STATE_REQUESTS)
    )

    session_data['mod_key_name_to_frames_map'] = (
        get_mod_key_to_frames_map(MOD_KEY_BITMASK_REQUESTS)
    )

    session_data['mouse_pos_requests'] = tuple(MOUSE_POS_REQUESTS)

    session_data['mouse_key_state_requests'] = tuple(MOUSE_KEY_STATE_REQUESTS)

    ### store last frame index as well
    session_data['last_frame_index'] = GENERAL_NS.frame_index + 1

    ### store gamepad related data

    GAMEPAD_NS.store_play_data(
        session_data,
        REC_REFS.gamepad_button_id_to_action_name,
    )

    ### save initial context data

    session_data['slot_data'] = REC_REFS.slot_data

    ## keyboard and gamepad controls

    session_data['keyboard_control_names'] = REC_REFS.keyboard_control_names
    session_data['gamepad_controls'] = REC_REFS.gamepad_controls

    ## level to load and last_checkpoint_name

    session_data['level_to_load'] = REC_REFS.level_to_load
    session_data['last_checkpoint_name'] = REC_REFS.last_checkpoint_name

    ## locale and app version

    session_data['app_version_string'] = REC_REFS.app_version_string
    session_data['locale'] = REC_REFS.locale

    ### delegate saving and rotation of play data to specialized custom
    ### function

    save_and_rotate_play_data(
        session_data,
        REC_REFS.filename_without_extension,
    )

    ### clear collections created in this function (not really needed,
    ### but in our experience memory is freed faster when collections
    ### are cleared)

    events_map.clear()
    session_data.clear()

    ### clear recorded data
    clear_data()

def clear_data():

    ### clear collections

    for a_collection in (

        EVENTS_MAP,
        KEY_STATE_REQUESTS,
        MOD_KEY_BITMASK_REQUESTS,

        MOUSE_POS_REQUESTS,
        MOUSE_KEY_STATE_REQUESTS,

    ):
        a_collection.clear()

    ###
    GAMEPAD_NS.clear_data()


def yield_treated_events(events_type_and_dict_pairs):

    yield from (

        yield_compact_events(
            yield_named_gamepad_buttons(
                yield_named_keys_and_mod_keys(
                    yield_events_to_keep(
                        yield_named_events(
                            events_type_and_dict_pairs
                        )
                    )
                )
            )
        )

    )


def yield_named_events(events_type_and_dict_pairs):

    for event_type, event_dict in events_type_and_dict_pairs:
        
        event_name = get_event_name(event_type).upper()

        if event_name == 'USEREVENT':
            event_name = USER_EVENT_NAMES_MAP[event_type]
    
        yield (
            event_name,
            event_dict,
        )

def yield_events_to_keep(events_name_and_dict):
    """Only yield events we are interested in recording."""
    for name_and_dict in events_name_and_dict:
        if name_and_dict[0] in NAMES_OF_EVENTS_TO_KEEP:
            yield name_and_dict

def yield_named_keys_and_mod_keys(events):

    for item in events:

        if item[0] in ('KEYUP', 'KEYDOWN'):
            treat_key_event_dict(item[1])

        yield item


def yield_named_gamepad_buttons(events):

    for item in events:

        ## events which are not JOYBUTTON events are yielded as-is
        if item[0] not in ('JOYBUTTONUP', 'JOYBUTTONDOWN'):
            yield event

        ## JOYBUTTON events are yielded with the button id replaced by
        ## the respective action name, but only if that button id
        ## is associated with an action;
        ##
        ## otherwise they are not yielded at all (since they are meaningless
        ## when they do not correspond to an action in the game)
        ##
        ## we also remove the 'joy' attribute if present, which is a
        ## deprecated attribute according to pygame-ce docs

        event_dict = item[1]

        if event_dict['button'] in REC_REFS.gamepad_button_id_to_action_name:

            event_dict['button'] = (
                REC_REFS.gamepad_button_id_to_action_name[event_dict['button']]
            )

            if 'joy' in event_dict:
                event_dict.pop('joy')

            yield item

def treat_key_event_dict(event_dict):

    for key, get_treated in (

        ('key', REVERSE_KEYS_MAP.__getitem__),
        ('scancode', SCANCODE_NAMES_MAP.__getitem__),

    ):
        event_dict[key] = get_treated(event_dict[key])

    ## if mod != KMOD_NONE, process it

    bitmask = event_dict['mod']

    if bitmask != KMOD_NONE:
        event_dict['mod'] = get_mod_key_names_tuple(bitmask)

def yield_compact_events(events):

    for name, a_dict in events:

        yield [

            ## use a compact name if there's one
            EVENT_COMPACT_NAME_MAP.get(name, name),

            ## use the dict after changing it to be more compact
            get_compact_event_dict(name, a_dict),

        ]

def get_compact_event_dict(name, a_dict):

    ### strip keys with the most common values;
    ###
    ### since they are so common, removing them saves a lot of space;
    ###
    ### this doesn't cause loss of info, because since we know which
    ### values we are stripping, we just put them back when we are
    ### about to play the session in the session playing mode;

    if name in EVENT_KEY_STRIP_MAP:

        map_of_values_to_strip = EVENT_KEY_STRIP_MAP[name]

        for key, value in map_of_values_to_strip.items():
            
            if key in a_dict and a_dict[key] == value:
                a_dict.pop(key)

    ### replace some keys with compact versions of their names
    ###
    ### since they are so common, the extra characters removed by
    ### using a more compact name saves a lot of space;
    ###
    ### again, this doesn't cause loss of info, because since we know
    ### which keys we are making compact, we just invert the operation
    ### when we are about to play the session in the session playing
    ### mode;
    ###
    ### additionally, user events actually have their dicts replaced,
    ### by a new one, because they are reused rather than instantiated
    ### every time, so popping the original key would cause them to miss
    ### that key the next time they are reused

    if name in EVENT_KEY_COMPACT_NAME_MAP:

        map_of_keys_to_make_compact = EVENT_KEY_COMPACT_NAME_MAP[name]

        ## if event is an user event, we copy dict, using the compact version
        ## of the keys instead

        if name in USER_EVENT_NAMES:

            new_dict = {}

            for key, compact_key in map_of_keys_to_make_compact.items():
                new_dict[compact_key] = a_dict[key]

            ### mark the new dict as the dict to be returned
            a_dict = new_dict

        ## otherwise, we pop they keys and insert in their compact versions

        else:

            for key, compact_key in map_of_keys_to_make_compact.items():
                
                if key in a_dict:
                    a_dict[compact_key] = a_dict.pop(key)

    ### return the dict
    return a_dict


def get_key_to_frames_map(time_obj_pairs):

    ### this format is okay, but it can be more compact

    frame_to_key_names_map = {
        
        item[0]: item[1]

        for item in (

            (

                ## item 0
                frame_index,

                ## item 1
                tuple(
                    key_name # item
                    for key_name, key in KEYS_MAP.items() # source
                    if wrapper[key] # filtering condition
                )


            )

            for frame_index, wrapper in time_obj_pairs

        )

        if item[1]

    }

    ### the format below, the one we actually return, is used
    ### because it is more compact

    key_name_to_frames_map = defaultdict(list)

    for frame, key_names in frame_to_key_names_map.items():

        for key_name in key_names:
            key_name_to_frames_map[key_name].append(frame)

    ###
    return dict(key_name_to_frames_map)

def get_mod_key_to_frames_map(frame_bitmask_pairs):

    ### this format is okay, but it can be more compact

    frame_to_mod_key_names_map = {
        frame_index: mod_key_names
        for frame_index, mod_key_names
        in yield_frame_and_mod_keys_names(frame_bitmask_pairs)
    }

    ### the format below, the one we actually return, is used
    ### because it is more compact

    mod_key_name_to_frames_map = defaultdict(list)

    for frame, mod_key_names in frame_to_mod_key_names_map.items():

        for key in mod_key_names:
            mod_key_name_to_frames_map[key].append(frame)

    ###
    return dict(mod_key_name_to_frames_map)


def yield_frame_and_mod_keys_names(frame_bitmask_pairs):

    for frame_index, bitmask in frame_bitmask_pairs:

        if bitmask != KMOD_NONE:

            yield (
                frame_index,
                get_mod_key_names_tuple(bitmask),
            )


def get_mod_key_names_tuple(bitmask):

    return tuple(
        mod_key_name
        for mod_key_name, mod_key in MOD_KEYS_MAP.items()
        if bitmask & mod_key
    )



### Notes
###
### [1] note that pygame.mouse.set_pos() (aliased as set_mouse_pos())
### is not changed (overridden or extended) anywhere in this module;
### this is so because it is used as-is, we just import it so it is
### available in this module namespace;
###
### [2] read note [1] above; the same is applies to
### pygame.mouse.set_visible, which here is aliased as
### set_mouse_visibility()
