
### third-party imports

from pygame import (
    quit as quit_pygame,
    Surface,
)

from pygame.math import Vector2

from pygame.color import THECOLORS

from pygame.display import update

from pygame.mixer import music


### local imports

from ...config import (
    REFS,
    LEVELS_DIR,
    MUSIC_DIR,
)

from ...pygamesetup.constants import (
    screen_colliderect, blit_on_screen, SCREEN_RECT, SCREEN
)

from ...ourstdlibs.behaviour import do_nothing

from ...ourstdlibs.pyl import load_pyl

from ...textman import render_text

from ...userprefsman.main import USER_PREFS

from .player import Player

from .backprops.citywall import CityWall

from .middleprops.ladder import Ladder

from .blocks.cityblock import CityBlock

from .actors.gruntbot import GruntBot

from .prototypemessage import message

from .common import (
    LAYERS,
    ONSCREEN_LAYERS,
    LAYER_NAMES,
    BACK_PROPS,
    MIDDLE_PROPS,
    BLOCKS,
    ACTORS,
    BACK_PROPS_ON_SCREEN,
    MIDDLE_PROPS_ON_SCREEN,
    BLOCKS_ON_SCREEN,
    ACTORS_ON_SCREEN,
    PROJECTILES,
    FRONT_PROPS,
    get_layer_from_name,
    execute_tasks,
)


### module level objs


##

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


### define a vicinity rect
###
### it is a rect equivalent to the SCREEN after we increase it in all four
### directions by its own dimensions, centered on the screen
###
### it is used to detect chunks of the level adjacent to the screen
### (the screen is the visible area)
###   _________________________________
###  |                ^                |
###  |  VICINITY      |                |
###  |  RECT          |                |
###  |           _____|_____           |
###  |          |           |          |
###  |<---------|  SCREEN   |--------->|
###  |          |   RECT    |          |
###  |          |___________|          |
###  |                |                |
###  |                |                |
###  |                |                |
###  |________________v________________|

VICINITY_RECT = (
    SCREEN_RECT.inflate(SCREEN_RECT.width * 2, SCREEN_RECT.height * 2)
)

VICINITY_WIDTH, VICINITY_HEIGHT = VICINITY_RECT.size
vicinity_colliderect = VICINITY_RECT.colliderect

CHUNKS = set()

CHUNKS_IN = set()
CHUNKS_IN_TEMP = set()

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
                for chunk_pos, obj_center_pos in zip(topleft, obj.rect.center)
            )

    def position_objs(self):

        get_center = self.get_center

        topleft = self.rect.topleft

        for obj in self.objs:

            obj.rect.center = tuple(
                chunk_pos - obj_center_offset
                for chunk_pos, obj_center_offset in zip(topleft, get_center(obj))
            )

    def add_obj(self, obj):

        obj.chunk = self

        self.objs.add(obj)

        getattr(self, obj.layer_name).add(obj)

        self.center_map[obj] = tuple(
            chunk_pos - obj_center_pos
            for chunk_pos, obj_center_pos in zip(self.rect.topleft, obj.rect.center)
        )

    def remove_obj(self, obj):

        self.objs.remove(obj)
        getattr(self, obj.layer_name).remove(obj)
        self.center_map.pop(obj)


class LevelManager:

    def __init__(self):

#        self.controls_panels = [
#
#            render_text(f' {text} ', 'regular', 12)
#
#            for text in (
#                'a,d : left/right',
#                'j,k : shoot/jump',
#                'w,s : up/down ladder',
#                'ESC : quit',
#            )
#
#        ]
#
#        self.controls_panels.reverse()

        self.control = self.control_player

        ###

        self.camera_tracking_area = SCREEN_RECT.copy()
        self.camera_tracking_area.w //= 5
        self.camera_tracking_area.h += -40
        self.camera_tracking_area.center = SCREEN_RECT.center

        self.disable_player_tracking()

        ###
        self.floor_level = 128

    def enable_player_tracking(self):
        self.camera_tracking_routine = self.track_player

    def disable_player_tracking(self):
        self.camera_tracking_routine = do_nothing

    def prepare(self):

        music_volume = (
            (USER_PREFS['MASTER_VOLUME']/100)
            * (USER_PREFS['MUSIC_VOLUME']/100)
        )

        music.set_volume(music_volume)
        music.load(str(MUSIC_DIR / 'level_1_by_juhani_junkala.ogg'))
        music.play(-1)

        if not hasattr(self, 'player'):
            self.player = Player()

        self.player.prepare()

        self.state = self

        ### get level data and instantiate objects
        instantiate_and_group_objects()

        ###
        VICINITY_RECT.center = SCREEN_RECT.center

        ### update chunks and list objects on screen

        update_chunks_and_layers()
        list_objects_on_screen()

    def instantiate_and_group_objects(self):

        level_name = REFS.data['level_name']

        level_data_path = LEVELS_DIR / level_name
        level_data = load_pyl(level_data_path)

        ### bg

        self.bg = Surface((320, 180)).convert()
        self.bg.fill(level_data['background_color'])

        ###
        layered_objects = level_data['layered_objects']

        ### instantiate all objects

        objs = [

            instantiate(obj_data, layer_name)

            for layer_name, objs in layered_objects.items()
            for obj_data in objs

        ]

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

        # TODO reintegrate line below as appropriate
        # (will probably just add to list of all objects)
        #BACK_PROPS.add(message)

    def control_player(self):
        self.player.control()

    def update(self):

        ### backup scrolling
        scrolling_before_camera_tracking = tuple(scrolling)

        ### must update player first, since it may move and cause the
        ### camera to move as well, which causes the level to move

        self.player.update()
        self.camera_tracking_routine()

        ### the floor routine moves the level gradually so the player's feet
        ### ends up in a certain vertical distance from the top of the screen,
        ### but only if the player is touching the floor and if the player
        ### isn't in that position already
        self.floor_level_routine()

        ### if scrolling changed, update chunks and objects on screen

        if scrolling_before_camera_tracking != tuple(scrolling):

            update_chunks_and_layers()
            list_objects_on_screen()

        ### now we update what is on the screen

        for prop in BACK_PROPS_ON_SCREEN:
            prop.update()

        for prop in MIDDLE_PROPS_ON_SCREEN:
            prop.update()

        for block in BLOCKS_ON_SCREEN:
            block.update()

        for actor in ACTORS_ON_SCREEN:
            actor.update()

        ### also update objects that are always on screen

        for projectile in PROJECTILES:
            projectile.update()

        for prop in FRONT_PROPS:
            prop.update()

        ### execute scheduled tasks
        execute_tasks()

    def track_player(self):

        player_rect = self.player.rect

        clamped_rect = player_rect.clamp(self.camera_tracking_area)

        if clamped_rect != player_rect:

            self.move_level(

                tuple(
                    a - b
                    for a, b
                    in zip(clamped_rect.topleft, player_rect.topleft)
                )

            )

    def floor_level_routine(self):

        if self.player.midair: return

        y_diff = self.player.rect.bottom - self.floor_level

        if y_diff:
            
            multiplier = (
                1
                if abs(y_diff) == 1
                else 2
            )

            dy = (-1 if y_diff > 0 else 1) * multiplier

            self.move_level((0, dy))

    def move_level(self, diff):

        scrolling.update(diff)

        for prop in BACK_PROPS:
            prop.rect.move_ip(diff)

        for prop in MIDDLE_PROPS:
            prop.rect.move_ip(diff)

        for block in BLOCKS:
            block.rect.move_ip(diff)

        for actor in ACTORS:
            actor.rect.move_ip(diff)

        self.player.rect.move_ip(diff)

        for projectile in PROJECTILES:
            projectile.rect.move_ip(diff)

        for prop in FRONT_PROPS:
            prop.rect.move_ip(diff)

    def draw(self):

        blit_on_screen(self.bg, (0, 0))

        for prop in BACK_PROPS_ON_SCREEN:
            prop.draw()

        for prop in MIDDLE_PROPS_ON_SCREEN:
            prop.draw()

        for projectile in PROJECTILES:
            projectile.draw()

        for block in BLOCKS_ON_SCREEN:
            block.draw()

        self.player.draw()

        for actor in ACTORS_ON_SCREEN:
            actor.draw()

        for prop in FRONT_PROPS:
            prop.draw()

        ############################
#        from pygame.draw import rect, line
#
#        cam_area = self.camera_tracking_area
#
#        rect(SCREEN, 'red', cam_area, 1)
#
#        line(
#            SCREEN,
#            'magenta',
#            (cam_area.left , self.floor_level),
#            (cam_area.right-1, self.floor_level),
#            1,
#        )
        ############################

#        x = 1
#        y = 180 - 18
#
#        for surf in self.controls_panels:
#
#            blit_on_screen(surf, (x, y))
#            y += -12

        self.player.health_column.draw()

        update()

    def next(self):
        return self.state

def update_chunks_and_layers():

    ### check current chunks in vicinity

    CHUNKS_IN_TEMP.update(
        chunk
        for chunk in CHUNKS
        if vicinity_colliderect(chunk.rect)
    )

    ### if it is different from previous chunks in vicinity...

    if CHUNKS_IN != CHUNKS_IN_TEMP:

        ### for the chunks leaving vicinity, remove their objects
        ### from the layers

        for chunk in (CHUNKS_IN - CHUNKS_IN_TEMP):

            for layer_name in LAYER_NAMES:

                get_layer_from_name(layer_name).difference_update(
                    getattr(chunk, layer_name)
                )


        ### for the chunks entering vicinity, add their objects to the layers

        for chunk in (CHUNKS_IN_TEMP - CHUNKS_IN):

            for layer_name in LAYER_NAMES:

                get_layer_from_name(layer_name).update(
                    getattr(chunk, layer_name)
                )


        ### update the set of chunks in vicinity

        CHUNKS_IN.clear()
        CHUNKS_IN.update(CHUNKS_IN_TEMP)

    ### for each chunk in vicinity, reposition their objects

    for chunk in CHUNKS_IN:
        chunk.position_objs()

    ### clear temporary chunks collection
    CHUNKS_IN_TEMP.clear()

def list_objects_on_screen():

    for layer, on_screen in zip(LAYERS, ONSCREEN_LAYERS):

        on_screen.clear()

        on_screen.update(
            obj
            for obj in layer
            if screen_colliderect(obj.rect)
        )

def instantiate(obj_data, layer_name):

    name = obj_data['name']

    if name == 'city_wall':
        obj = CityWall(**obj_data)

    elif name == 'city_block':
        obj = CityBlock(**obj_data)

    elif name == 'grunt_bot':
        obj = GruntBot(**obj_data)

    elif name == 'ladder':
        obj = Ladder(**obj_data)

    else:
        raise RuntimeError("This block should never be reached.")

    obj.layer_name = layer_name
    return obj
