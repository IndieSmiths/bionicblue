"""Constructs shared among sibling modules."""

### local import
from ...ourstdlibs.behaviour import do_nothing



### constants

## anonymous object to store gamepad state
GAMEPAD_NS = type('Object', (), {})()

## mock gamepad states, for when no gamepad is plugged

mock_gamepad_dict = {

    ## data

    '_last_x_hat': 0,
    '_last_y_hat': 0,
    '_last_x_axis': 0,
    '_last_y_axis': 0,
    'x_sum': 0,
    'y_sum': 0,

    ## behaviours

    'prepare_data_and_events': do_nothing,
    'get_button': lambda button: False,
}


### support utilities

_get_0 = lambda: 0 # XXX probably delete this and just use 'int()' instead
_get_0_0 = lambda: (0, 0)

round_axis = lambda axis: 0 if abs(axis) < .2 else (1 if axis > 0 else -1)
