"""Common objects/values/functions of the level manager subpackage."""

### third-party import
from pygame.math import Vector2


### local imports
from ...pygamesetup.constants import screen_colliderect, SCREEN_RECT



### top-level objects/collections/functions

## vector representing first point where there's content
## in the level, that is, the topleft of the topleftmost
## object, or (0, 0) if the level is empty
##
## this point is used as the starting point from where to place
## level chunks
content_origin = Vector2()

## vector to keep track of scrolling
scrolling = Vector2()

##

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

get_onscreen_layer_from_name = {
    name: set()
    for name in LAYER_NAMES
}.__getitem__

ONSCREEN_LAYERS = [get_onscreen_layer_from_name(name) for name in LAYER_NAMES]

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

## tasks

TASKS = []
append_task = TASKS.append
clear_tasks = TASKS.clear

def execute_tasks():

    if TASKS:

        for task in TASKS:
            task()

        clear_tasks()

## define a vicinity rect
##
## it is a rect equivalent to the SCREEN after we increase it in all four
## directions by its own dimensions, centered on the screen
##
## it is used to detect chunks of the level adjacent to the screen
## (the screen is the visible area)
##   _________________________________
##  |                ^                |
##  |  VICINITY      |                |
##  |  RECT          |                |
##  |           _____|_____           |
##  |          |           |          |
##  |<---------|  SCREEN   |--------->|
##  |          |   RECT    |          |
##  |          |___________|          |
##  |                |                |
##  |                |                |
##  |                |                |
##  |________________v________________|

VICINITY_RECT = (
    SCREEN_RECT.inflate(SCREEN_RECT.width * 2, SCREEN_RECT.height * 2)
)

VICINITY_WIDTH, VICINITY_HEIGHT = VICINITY_RECT.size
vicinity_colliderect = VICINITY_RECT.colliderect


CHUNKS = set()

CHUNKS_IN_VIC = set()
CHUNKS_IN_VIC_TEMP = set()


def group_objects(objs):

    n = len(objs)

    if n == 1:

        obj = objs[0]

        VICINITY_RECT.topleft = obj.topleft
        content_origin.update(obj.topleft)

        CHUNKS.add(LevelChunk(VICINITY_RECT, objs))

    elif n > 1:

        ### XXX idea, not sure if worth pursuing (certainly not now,
        ### probably never): make it so assets that collide with more than
        ### one chunk are added to the one that gets more area after
        ### cliping the asset's rect with the chunk's rect

        ## define a union rect

        first_obj, *other_objs = objs

        union_rect = first_obj.rect.unionall(

            [
                obj.rect
                for obj in other_objs
            ]

        )

        content_origin.update(union_rect.topleft)

        ## prepare to loop while evaluating whether objects
        ## and the union rect collide with the vicinity

        union_left, _ = VICINITY_RECT.topleft = union_rect.topleft

        obj_set = set(objs)

        ## while looping indefinitely

        while True:

            ## if there are objs colliding with the vicinity,
            ## store them in their own level chunk and remove
            ## them from the set of objects

            colliding_objs = {
                obj
                for obj in obj_set
                if vicinity_colliderect(obj.rect)
            }

            if colliding_objs:

                obj_set -= colliding_objs
                CHUNKS.add(LevelChunk(VICINITY_RECT, colliding_objs))

            ## if there's no obj left in the set, break out of loop

            if not obj_set:
                break

            ## reposition vicinity horizontally, as though the union
            ## rect was a table and we were moving the vicinity to the
            ## column to the right
            VICINITY_RECT.x += VICINITY_WIDTH

            ## if vicinity in new position doesn't touch the union
            ## anymore, keep thinking of the union rect as a table and
            ## reposition the vicinity at the beginning of the next
            ## imaginary row

            if not vicinity_colliderect(union_rect):

                VICINITY_RECT.left = union_left
                VICINITY_RECT.y += VICINITY_HEIGHT


def update_chunks_and_layers():

    ### check current chunks in vicinity

    CHUNKS_IN_VIC_TEMP.update(
        chunk
        for chunk in CHUNKS
        if vicinity_colliderect(chunk.rect)
    )

    ### if it is different from previous chunks in vicinity...

    if CHUNKS_IN_VIC != CHUNKS_IN_VIC_TEMP:

        ### for the chunks leaving vicinity, remove their objects
        ### from the layers

        for chunk in (CHUNKS_IN_VIC - CHUNKS_IN_VIC_TEMP):

            for layer_name in LAYER_NAMES:

                get_layer_from_name(layer_name).difference_update(
                    getattr(chunk, layer_name)
                )


        ### for the chunks entering vicinity, add their objects to the layers

        for chunk in (CHUNKS_IN_VIC_TEMP - CHUNKS_IN_VIC):

            for layer_name in LAYER_NAMES:

                get_layer_from_name(layer_name).update(
                    getattr(chunk, layer_name)
                )


        ### update the set of chunks in vicinity

        CHUNKS_IN_VIC.clear()
        CHUNKS_IN_VIC.update(CHUNKS_IN_VIC_TEMP)

    ### for each chunk in vicinity, reposition their objects

    for chunk in CHUNKS_IN_VIC:
        chunk.position_objs()

    ### clear temporary chunks collection
    CHUNKS_IN_VIC_TEMP.clear()

    ### list objects on screen

    for layer, on_screen in zip(LAYERS, ONSCREEN_LAYERS):

        on_screen.clear()

        on_screen.update(
            obj
            for obj in layer
            if screen_colliderect(obj.rect)
        )


class LevelChunk:

    def __init__(self, rect, objs):

        ### instantiate rect
        self.rect = rect.copy()

        ### store objs
        self.objs = objs

        ### create and store layers

        for layer_name in LAYER_NAMES:
            setattr(self, layer_name, set())

        ### create and store center map, a map to store the
        ### center of each object relative to this chunk's topleft
        ###
        ### also create a local reference to it and an attribute
        ### referencing its item getter method

        center_map = self.center_map = {}
        self.get_center = center_map.__getitem__

        ### iterate over objects...
        ###
        ### - storing them in layers
        ### - storing objects centers relative to level's topleft

        topleft = self.rect.topleft

        for obj in objs:

            obj.chunk = self

            getattr(self, obj.layer_name).add(obj)

            center_map[obj] = tuple(
                chunk_pos - obj_center_pos
                for chunk_pos, obj_center_pos
                in zip(topleft, obj.rect.center)
            )

        ### add deltas for actors to keep track of their travel
        ### beyond their initial positions

        for obj in self.actors:
            obj.delta = Vector2()

    def position_objs(self):

        get_center = self.get_center

        topleft = self.rect.topleft

        for obj in self.objs:

            obj.rect.center = tuple(
                chunk_pos - obj_center_offset
                for chunk_pos, obj_center_offset
                in zip(topleft, get_center(obj))
            )

        for obj in self.actors:
            obj.rect.move_ip(obj.delta)

    def add_obj(self, obj):

        obj.chunk = self

        self.objs.add(obj)

        layer = getattr(self, obj.layer_name)
        layer.add(obj)

        self.center_map[obj] = tuple(
            chunk_pos - obj_center_pos
            for chunk_pos, obj_center_pos
            in zip(self.rect.topleft, obj.rect.center)
        )

        if layer is self.actors:
            obj.delta = Vector2()

    def remove_obj(self, obj):

        self.objs.remove(obj)
        getattr(self, obj.layer_name).remove(obj)
        self.center_map.pop(obj)


def add_obj(obj):

    ### if an existing chunk collides add obj to that chunk

    rect = obj.rect

    for chunk in CHUNKS:

        if chunk.rect.colliderect(rect):

            chunk.add_obj(obj)

            ### add obj to layer
            get_layer_from_name(obj.layer_name).add(obj)

            break

    ### otherwise create a new chunk

    else:
        
        ### note: we don't need to add object to layer here,
        ### because it will be added automatically for us
        ### by update_chunks_and_layers() when the created
        ### chunk is added to the set of chunks in the vicinity

        chunk_anchor_pos = rect.center
        unscrolled_anchor_pos = chunk_anchor_pos - scrolling
        pos_from_origin = unscrolled_anchor_pos - content_origin

        left_multiplier = pos_from_origin.x // VICINITY_WIDTH
        top_multiplier = pos_from_origin.y // VICINITY_HEIGHT

        left = left_multiplier * VICINITY_WIDTH
        top = top_multiplier * VICINITY_HEIGHT

        VICINITY_RECT.topleft = (
            (left, top)
            + scrolling
            + content_origin
        )

        CHUNKS.add(LevelChunk(VICINITY_RECT, {obj}))

        VICINITY_RECT.center = SCREEN_RECT.center

    update_chunks_and_layers()

def remove_obj(obj):

    get_layer_from_name(obj.layer_name).remove(obj)
    get_onscreen_layer_from_name(obj.layer_name).remove(obj)
    obj.chunk.remove_obj(obj)
