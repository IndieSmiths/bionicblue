
### third-party imports

from pygame.event import get as get_events, set_allowed

from pygame.key import (
    get_pressed as get_pressed_keys,
    get_mods as get_pressed_mod_keys,
    stop_text_input,
)

from pygame.mouse import (
    set_visible as set_mouse_visibility,
    get_pos as get_mouse_pos,
    set_pos as set_mouse_pos,
    get_pressed as get_mouse_pressed,
)

from pygame.display import update as update_screen


### local imports

from ..constants import (
    SCREEN,
    SCREEN_RECT,
    GENERAL_NS,
    GENERAL_SERVICE_NAMES,
    FPS,
    maintain_fps,
)

from ..gamepadservices.common import GAMEPAD_NS



### create and use function to activate normal behaviour

def set_behaviour(services_namespace, reset_window_mode=True):
    """Setup normal mode."""

    ### grab normal services from our globals (module-level names)
    ### and set them as attributes of the services namespace

    our_globals = globals()

    for attr_name in GENERAL_SERVICE_NAMES:

        value = our_globals[attr_name]
        setattr(services_namespace, attr_name, value)

    ### allow all kinds of events (by passing None to
    ### pygame.event.set_allowed), except text input ones (by
    ### stopping text input events),
    ### which should be enabled only when appropriate

    set_allowed(None)
    stop_text_input()


def frame_checkups():
    """Perform various checkups.

    Meant to be used at the beginning of each frame in the
    app loop.
    """
    ### keep a constants framerate
    maintain_fps(FPS)

    ### increment frame number
    GENERAL_NS.frame_index += 1

    ### store data and post custom events for gamepad
    ### directional triggers
    GAMEPAD_NS.prepare_data_and_events()
