
### third-party imports

from pygame import (
    quit as quit_pygame,
    Surface,
)

from pygame.display import update as update_screen

from pygame.mixer import music

from pygame.math import Vector2

from pygame.event import get as get_events


### local imports

from ...config import (
    REFS,
    LEVELS_DIR,
    MUSIC_DIR,
)

from ...pygamesetup.constants import (
    blit_on_screen,
    SCREEN_RECT,
)

from ...ourstdlibs.behaviour import do_nothing

from ...ourstdlibs.pyl import load_pyl

from ...textman import render_text

from ...userprefsman.main import USER_PREFS

from .player import Player

from .backprops.citywall import CityWall

from .middleprops.ladder import Ladder
from .middleprops.chains import Chains

from .blocks.cityblock import CityBlock
from .blocks.spike import Spike
from .blocks.floatingplatform import FloatingPlatform

from .actors.gruntbot import GruntBot
from .actors.watcherbot import WatcherBot
from .actors.rabbiterror import Rabbiterror
from .actors.chiefsecbot import ChiefSecurityBot

from .prototypemessage import message

from .arenadoor import DOOR_1, DOOR_2

from .common import (

    LAYER_NAMES,

    LAYERS,
    NEAR_SCREEN_LAYERS,

    BACK_PROPS,
    MIDDLE_PROPS,
    BLOCKS,
    ACTORS,

    BACK_PROPS_NEAR_SCREEN,
    MIDDLE_PROPS_NEAR_SCREEN,
    BLOCKS_NEAR_SCREEN,
    ACTORS_NEAR_SCREEN,

    PROJECTILES,
    FRONT_PROPS,

    CHUNKS,

    VICINITY_RECT,
    VICINITY_WIDTH,

    scrolling,

    execute_tasks,
    group_objects,
    add_obj,
    update_chunks_and_layers,

)


scrolling_backup = Vector2()

FLOOR_LEVEL = 128

NORMAL_CAMERA_TRACKING_AREA = SCREEN_RECT.copy()
NORMAL_CAMERA_TRACKING_AREA.width //= 5
NORMAL_CAMERA_TRACKING_AREA.height += -40
NORMAL_CAMERA_TRACKING_AREA.center = SCREEN_RECT.center

BOSS_CAMERA_TRACKING_AREA = SCREEN_RECT.inflate(4, 4)


class LevelManager:

    def __init__(self):
        pass

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

        ###

    def enable_player_tracking(self):
        self.camera_tracking_routine = self.track_player

    def disable_player_tracking(self):
        self.camera_tracking_routine = do_nothing

    def prepare(self):

        self.control = self.control_player
        self.update = self.normal_update

        self.camera_tracking_area = NORMAL_CAMERA_TRACKING_AREA
        self.disable_player_tracking()

        scrolling.update(0, 0)
        scrolling_backup.update(scrolling)

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

        ###

        level_name = REFS.data['level_name']

        level_data_path = LEVELS_DIR / level_name
        level_data = load_pyl(level_data_path)

        ### instantiate and group objects

        group_objects(

            [

                instantiate(obj_data, layer_name)

                for layer_name, objs in level_data['layered_objects'].items()
                for obj_data in objs
                if layer_name != 'labels'

            ]

        )

        ### bg

        self.bg = Surface((320, 180)).convert()
        self.bg.fill(level_data['background_color'])

        ###
        VICINITY_RECT.center = SCREEN_RECT.center

        ### add custom prototype message

        message_pos = next(
            label_data
            for label_data in level_data['layered_objects']['labels']
            if label_data['text'] == 'message'
        )['pos']

        message.layer_name = 'backprops'
        message.rect.centerx = message_pos[0]
        message.rect.bottom = message_pos[1] - 20
        add_obj(message)

        ### add boss

        boss_midbottom = next(
            label_data
            for label_data in level_data['layered_objects']['labels']
            if label_data['text'] == 'boss_midb'
        )['pos']

        boss = ChiefSecurityBot('chief_sec_bot', boss_midbottom, facing_right=False)
        boss.layer_name = 'actors'
        add_obj(boss)

        ### add arena doors

        door1_pos = next(
            label_data
            for label_data in level_data['layered_objects']['labels']
            if label_data['text'] == 'door1'
        )['pos']

        door2_pos = next(
            label_data
            for label_data in level_data['layered_objects']['labels']
            if label_data['text'] == 'door2'
        )['pos']

        DOOR_1.rect.midbottom = door1_pos
        DOOR_2.rect.midbottom = door2_pos

        DOOR_1.prepare()
        DOOR_2.prepare()

        add_obj(DOOR_1)
        add_obj(DOOR_2)

        ### store position of cam_cx (centerx of boss arena and
        ### blue_midb (blue midbottom position near the boss)

        self.cam_cx_pos = next(
            label_data
            for label_data in level_data['layered_objects']['labels']
            if label_data['text'] == 'cam_cx'
        )['pos']

        self.blue_midb = next(
            label_data
            for label_data in level_data['layered_objects']['labels']
            if label_data['text'] == 'blue_midb'
        )['pos']

        ### scroll level so player ends up positioned above given label

        # temporarily using 'endpoint' for testing/development;
        #
        # normally this will be 'landing' or whichever checkpoint the player
        # reached (which may actually be 'endpoint')
        label_name = 'endpoint'

        landing_pos = next(
            label_data
            for label_data in level_data['layered_objects']['labels']
            if label_data['text'] == label_name 
        )['pos']

        dx = SCREEN_RECT.centerx - landing_pos[0]
        dy = FLOOR_LEVEL - landing_pos[1]
        self.move_level((dx, dy))

        self.player.rect.centerx = SCREEN_RECT.centerx
        self.player.rect.bottom = SCREEN_RECT.top

        ### update chunks and list objects on screen

        update_chunks_and_layers()

    def control_player(self):
        self.player.control()

    def normal_update(self):

        ### must update player first, since it may move and cause the
        ### camera to move as well, which causes the level to move
        self.player.update()
        
        ### backup scrolling
        scrolling_backup.update(scrolling)

        ### camera routine, depending on the actual routine assigned to the
        ### attribute may cause the camera to track the player (by moving
        ### the whole level so the player is near the middle of the screen)
        self.camera_tracking_routine()

        ### the floor routine moves the level gradually so the player's feet
        ### ends up in a certain vertical distance from the top of the screen,
        ### but only if the player is touching the floor and if the player
        ### isn't in that position already
        self.floor_level_routine()

        ### if the level scrolled (moved), update chunks and layers

        if scrolling_backup != scrolling:
            update_chunks_and_layers()

        ### now we update what is on the screen

        for prop in BACK_PROPS_NEAR_SCREEN:
            prop.update()

        for prop in MIDDLE_PROPS_NEAR_SCREEN:
            prop.update()

        for block in BLOCKS_NEAR_SCREEN:
            block.update()

        for actor in ACTORS_NEAR_SCREEN:
            actor.update()

        ### also update objects that are always on screen

        for projectile in PROJECTILES:
            projectile.update()

        for prop in FRONT_PROPS:
            prop.update()

        ### execute scheduled tasks
        execute_tasks()

    def moving_update(self):

        ### must update player first, since it may move and cause the
        ### camera to move as well, which causes the level to move
        self.player.update()

        ### backup scrolling
        scrolling_backup.update(scrolling)

        ### the floor routine moves the level gradually so the player's feet
        ### ends up in a certain vertical distance from the top of the screen,
        ### but only if the player is touching the floor and if the player
        ### isn't in that position already
        self.floor_level_routine()

        ###

        current_cam_cx = self.cam_cx_pos + scrolling
        current_blue_midb = self.blue_midb + scrolling

        if SCREEN_RECT.centerx != current_cam_cx[0]:

            self.move_level((-1, 0))

            player_rect = self.player.rect
            player_rect.move_ip(-3, 0)

            if abs(player_rect.centerx - current_blue_midb[0]) < 4:
                player_rect.midbottom = current_blue_midb

        else:
            self.control = self.control_player
            self.update = self.normal_update

        ### if the level scrolled (moved), update chunks and layers

        if scrolling_backup != scrolling:
            update_chunks_and_layers()

        ### now we update what is on the screen

        for prop in BACK_PROPS_NEAR_SCREEN:
            prop.update()

        for prop in MIDDLE_PROPS_NEAR_SCREEN:
            prop.update()

        for block in BLOCKS_NEAR_SCREEN:
            block.update()

        for actor in ACTORS_NEAR_SCREEN:
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

        y_diff = self.player.rect.bottom - FLOOR_LEVEL

        if y_diff:
            
            multiplier = (
                1
                if abs(y_diff) == 1
                else 2
            )

            dy = (-1 if y_diff > 0 else 1) * multiplier

            self.move_level((0, dy))

    def move_level(self, diff):

        scrolling[0] += diff[0]
        scrolling[1] += diff[1]

        self.player.rect.move_ip(diff)

        for chunk in CHUNKS:
            chunk.rect.move_ip(diff)

        for projectile in PROJECTILES:
            projectile.rect.move_ip(diff)

        for prop in FRONT_PROPS:
            prop.rect.move_ip(diff)

    def draw(self):

        blit_on_screen(self.bg, (0, 0))

        for prop in BACK_PROPS_NEAR_SCREEN:
            prop.draw()

        for prop in MIDDLE_PROPS_NEAR_SCREEN:
            prop.draw()

        for projectile in PROJECTILES:
            projectile.draw()

        for block in BLOCKS_NEAR_SCREEN:
            block.draw()

        self.player.draw()

        for actor in ACTORS_NEAR_SCREEN:
            actor.draw()

        for prop in FRONT_PROPS:
            prop.draw()

        ############################
#        from pygame.draw import rect, line
#        from ...pygamesetup.constants import SCREEN
#
#        cam_area = self.camera_tracking_area
#
#        rect(SCREEN, 'red', cam_area, 1)
#
#        line(
#            SCREEN,
#            'magenta',
#            (cam_area.left , FLOOR_LEVEL),
#            (cam_area.right-1, FLOOR_LEVEL),
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

        update_screen()

    def next(self):
        return self.state

    def passing_through_arena_door(self, door_name):

        if door_name == 'door_2':

            self.camera_tracking_area = BOSS_CAMERA_TRACKING_AREA

            self.update = self.moving_update
            self.control = get_events

def instantiate(obj_data, layer_name):

    name = obj_data['name']

    if name == 'city_wall':
        obj = CityWall(**obj_data)

    elif name == 'city_block':
        obj = CityBlock(**obj_data)

    elif name == 'spike':
        obj = Spike(**obj_data)

    elif name in (
        'floating_h_platform',
        'floating_v_platform',
    ):
        obj = FloatingPlatform(**obj_data)

    elif name == 'grunt_bot':
        obj = GruntBot(**obj_data)

    elif name == 'watcher_bot':
        obj = WatcherBot(**obj_data)

    elif name == 'rabbiterror':
        obj = Rabbiterror(**obj_data)

    elif name == 'ladder':
        obj = Ladder(**obj_data)

    elif name == 'chains':
        obj = Chains(**obj_data)

    else:
        raise RuntimeError("This block should never be reached.")

    obj.layer_name = layer_name
    return obj
