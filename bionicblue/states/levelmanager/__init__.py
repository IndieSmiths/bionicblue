
### third-party imports

from pygame import (
    quit as quit_pygame,
    Surface,
)

from pygame.color import THECOLORS

from pygame.display import update

from pygame.mixer import music


### local imports

from ...config import (
    REFS,
    LEVELS_DIR,
    MUSIC_DIR,
    BACK_PROPS, BACK_PROPS_ON_SCREEN,
    MIDDLE_PROPS, MIDDLE_PROPS_ON_SCREEN,
    BLOCKS, BLOCKS_ON_SCREEN,
    ACTORS, ACTORS_ON_SCREEN,
    PROJECTILES,
    FRONT_PROPS,
    execute_tasks
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



LAYER_DATA_PAIRS = [
    (BACK_PROPS, 'backprops'),
    (MIDDLE_PROPS, 'middleprops'),
    (BLOCKS, 'blocks'),
    (ACTORS, 'actors'),
]


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

        level_name = REFS.data['level_name']

        level_data_path = LEVELS_DIR / level_name
        level_data = load_pyl(level_data_path)

        ### bg

        self.bg = Surface((320, 180)).convert()
        self.bg.fill(level_data['background_color'])

        ###
        layered_objects = level_data['layered_objects']

        for layer, layer_name in LAYER_DATA_PAIRS:

            try: objs_data = layered_objects[layer_name]
            except KeyError: continue

            for obj_data in objs_data:
                layer.add(instantiate(obj_data))

        ###
        BACK_PROPS.add(message)

    def control_player(self):
        self.player.control()

    def update(self):

        ### must update player first, since it may move and cause the
        ### camera to move as well, which causes the level to move

        self.player.update()
        self.camera_tracking_routine()

        ### now that the level may or may not have moved, we
        ### update what ended up on the screen

        BACK_PROPS_ON_SCREEN.clear()
        BACK_PROPS_ON_SCREEN.update(
            prop
            for prop in BACK_PROPS
            if screen_colliderect(prop.rect)
        )

        for prop in BACK_PROPS_ON_SCREEN:
            prop.update()

        MIDDLE_PROPS_ON_SCREEN.clear()
        MIDDLE_PROPS_ON_SCREEN.update(
            prop
            for prop in MIDDLE_PROPS
            if screen_colliderect(prop.rect)
        )

        for prop in MIDDLE_PROPS_ON_SCREEN:
            prop.update()
        
        BLOCKS_ON_SCREEN.clear()
        BLOCKS_ON_SCREEN.update(
            block
            for block in BLOCKS
            if screen_colliderect(block.rect)
        )

        for block in BLOCKS_ON_SCREEN:
            block.update()

        ACTORS_ON_SCREEN.clear()
        ACTORS_ON_SCREEN.update(
            actor
            for actor in ACTORS
            if screen_colliderect(actor.rect)
        )

        for actor in ACTORS_ON_SCREEN:
            actor.update()

        for projectile in PROJECTILES:
            projectile.update()

        for prop in FRONT_PROPS:
            prop.update()


        ###
        execute_tasks()

        ###
        self.floor_level_routine()

    def track_player(self):

        player_rect = self.player.rect

        clamped_rect = player_rect.clamp(self.camera_tracking_area)

        if clamped_rect != player_rect:

            diff = tuple(a - b for a, b in zip(clamped_rect.topleft, player_rect.topleft))
            self.move_level(diff)

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


def instantiate(obj_data):

    name = obj_data['name']

    if name == 'city_wall':
        return CityWall(**obj_data)

    elif name == 'city_block':
        return CityBlock(**obj_data)

    elif name == 'grunt_bot':
        return GruntBot(**obj_data)

    elif name == 'ladder':
        return Ladder(**obj_data)

    raise RuntimeError(
        "function should return before reaching this spot"
    )
