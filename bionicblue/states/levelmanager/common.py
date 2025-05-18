"""Common objects/values of the level manager subpackage."""



LAYER_NAMES = (
    'backprops',
    'middleprops',
    'blocks',
    'actors',
)

get_layer_from_name = {
    name: set()
    for name in LAYER_NAMES
}.__getitem__

LAYERS = [get_layer_from_name(name) for name in LAYER_NAMES]

ONSCREEN_LAYERS = [
    set()
    for name in LAYER_NAMES
]

(
BACK_PROPS,
MIDDLE_PROPS,
BLOCKS,
ACTORS,
) = LAYERS

(
BACK_PROPS_ON_SCREEN,
MIDDLE_PROPS_ON_SCREEN,
BLOCKS_ON_SCREEN,
ACTORS_ON_SCREEN,
) = ONSCREEN_LAYERS

PROJECTILES = set()
FRONT_PROPS = set()

TASKS = []
append_task = TASKS.append
clear_tasks = TASKS.clear

def execute_tasks():

    if TASKS:

        for task in TASKS:
            task()

        clear_tasks()
