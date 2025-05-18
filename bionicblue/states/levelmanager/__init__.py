
### third-party imports

from pygame import (
    quit as quit_pygame,
    Surface,
)

from pygame.display import update as update_screen

from pygame.mixer import music


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

from .blocks.cityblock import CityBlock

from .actors.gruntbot import GruntBot

from .prototypemessage import message

from .common import (

    LAYER_NAMES,

    LAYERS,
    ONSCREEN_LAYERS,

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

    CHUNKS,

    VICINITY_RECT,
    VICINITY_WIDTH,

    scrolling,

    execute_tasks,
    group_objects,
    update_chunks_and_layers,

)


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

        scrolling.update(0, 0)

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

            ]

        )

        ### TODO reintegrate line below as appropriate
        ### (will probably just add to list of all objects)
        #BACK_PROPS.add(message)

        ### bg

        self.bg = Surface((320, 180)).convert()
        self.bg.fill(level_data['background_color'])

        ###
        VICINITY_RECT.center = SCREEN_RECT.center

        ### update chunks and list objects on screen

        update_chunks_and_layers()

    def control_player(self):
        self.player.control()

    def update(self):

        ### must update player first, since it may move and cause the
        ### camera to move as well, which causes the level to move

        self.player.update()
        self.camera_tracking_routine()

        ### the floor routine moves the level gradually so the player's feet
        ### ends up in a certain vertical distance from the top of the screen,
        ### but only if the player is touching the floor and if the player
        ### isn't in that position already
        self.floor_level_routine()

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

        self.player.rect.move_ip(diff)

        for chunk in CHUNKS:
            chunk.rect.move_ip(diff)

        for projectile in PROJECTILES:
            projectile.rect.move_ip(diff)

        for prop in FRONT_PROPS:
            prop.rect.move_ip(diff)

        update_chunks_and_layers()

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
#        from ...pygamesetup.constants import SCREEN
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

        update_screen()

    def next(self):
        return self.state

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
