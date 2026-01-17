"""Facility for level manager class."""

### standard library import
from functools import partialmethod

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
    LoopException,
)

from ...pygamesetup.constants import (
    blit_on_screen,
    SCREEN_RECT,
)

from ...pygamesetup.inputgen import generate_input_data

from ...ourstdlibs.behaviour import do_nothing

from ...ourstdlibs.pyl import load_pyl, save_pyl

from ...textman import render_text

from ...userprefsman.main import USER_PREFS, KEYBOARD_CONTROLS

from .player import Player

from .backprops.citywall import CityWall

from .middleprops.ladder import Ladder
from .middleprops.chains import Chains
from .middleprops.chaincratehanger import ChainCrateHanger
from .middleprops.invisiblecollidingtrigger import InvisibleCollidingTrigger

from .blocks.cityblock import CityBlock
from .blocks.spike import Spike
from .blocks.floatingplatform import FloatingPlatform
from .blocks.crate import Crate
from .blocks.gate import Gate

from .actors.gruntbot import GruntBot
from .actors.watcherbot import WatcherBot
from .actors.rabbiterror import Rabbiterror
from .actors.chiefsecbot import ChiefSecurityBot
from .actors.mark import Mark

from .prototypemessage import message

from .common import (

    BACK_PROPS_NEAR_SCREEN,
    MIDDLE_PROPS_NEAR_SCREEN,
    BLOCKS_NEAR_SCREEN,
    ACTORS_NEAR_SCREEN,

    PROJECTILES,
    FRONT_PROPS,
    HEALTH_COLUMNS,

    CHUNKS,

    VICINITY_RECT,

    scrolling,
    scrolling_backup,

    execute_tasks,
    group_objects,
    add_obj,
    update_chunks_and_layers,

)

from .dialoguemgmt import DialogueManagement



FLOOR_LEVEL = 128

CAMERA_TRACKING_AREA = SCREEN_RECT.copy()
CAMERA_TRACKING_AREA.width //= 5
CAMERA_TRACKING_AREA.height += -40
CAMERA_TRACKING_AREA.center = SCREEN_RECT.center



class LevelManager(DialogueManagement):

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

        ###
        self.load_dialogues()

        self.control = self.control_player

    def enable_overall_tracking_for_camera(self):
        self.camera_overall_routine = self.move_level_to_keep_pc_within_area

    def disable_overall_tracking_for_camera(self):
        self.camera_overall_routine = do_nothing

    def enable_feet_tracking_for_camera(self):
        self.camera_feet_routine = self.move_level_to_align_feet

    def disable_feet_tracking_for_camera(self):
        self.camera_feet_routine = do_nothing

    def prepare(self):

        self.update = self.normal_update
        self.draw = self.draw_level

        self.disable_overall_tracking_for_camera()
        self.disable_feet_tracking_for_camera()

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

        HEALTH_COLUMNS.clear()
        HEALTH_COLUMNS.add(self.player.health_column)

        ###

        level_name = REFS.level_to_load

        level_data_path = LEVELS_DIR / level_name
        level_data = load_pyl(level_data_path)
        self.bg_color = level_data['background_color']

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

        ### add npc

        npc_midbottom = next(
            label_data
            for label_data in level_data['layered_objects']['labels']
            if label_data['text'] == 'mark'
        )['pos']

        npc = Mark(npc_midbottom)
        npc.layer_name = 'actors'
        add_obj(npc)

        ### add boss

        boss_bottomright = next(
            label_data
            for label_data in level_data['layered_objects']['labels']
            if label_data['text'] == 'boss_br'
        )['pos']

        boss = ChiefSecurityBot('chief_sec_bot', boss_bottomright, facing_right=False)
        boss.layer_name = 'actors'
        add_obj(boss)

        ### add gates

        npc_gate_pos = next(
            label_data
            for label_data in level_data['layered_objects']['labels']
            if label_data['text'] == 'ngate'
        )['pos']

        bgate0_pos = next(
            label_data
            for label_data in level_data['layered_objects']['labels']
            if label_data['text'] == 'bgate0'
        )['pos']

        bgate1_pos = next(
            label_data
            for label_data in level_data['layered_objects']['labels']
            if label_data['text'] == 'bgate1'
        )['pos']

        npc_gate_closed = (
            True
            if 'giovanni' in REFS.slot_data.get('encounters', ())
            else False
        )

        npc_gate = Gate(midbottom=npc_gate_pos, closed=npc_gate_closed)
        boss_gate0 = Gate(midbottom=bgate0_pos, closed=True)
        boss_gate1 = Gate(midbottom=bgate1_pos, closed=True)

        add_obj(npc_gate)
        add_obj(boss_gate0)
        add_obj(boss_gate1)

        self.boss_gate1 = boss_gate1

        ### add colliding triggers for gates

        for (

            boss_gate,
            opening_offset,
            opening_trigger_func,
            closing_offset,
            closing_trigger_func,

        ) in (

            (
                boss_gate0,
                -64,
                boss_gate0.trigger_opening,
                110,
                boss_gate0.trigger_closing,
            ),

            (
                boss_gate1,
                -64,
                self.getting_to_boss_area,
                84,
                boss_gate1.trigger_closing,
            ),

        ):

            opening_pos = boss_gate.rect.move(opening_offset, 0).midbottom
            closing_pos = boss_gate.rect.move(closing_offset, 0).midbottom

            opening_trigger = (

                InvisibleCollidingTrigger(

                    on_collision=opening_trigger_func,
                    width=16,
                    height=64,
                    coordinates_name='midbottom',
                    coordinates_value=opening_pos,

                )

            )

            closing_trigger = (

                InvisibleCollidingTrigger(

                    on_collision=closing_trigger_func,
                    width=16,
                    height=64,
                    coordinates_name='midbottom',
                    coordinates_value=closing_pos,

                )

            )

            add_obj(opening_trigger)
            add_obj(closing_trigger)

        ### store position of cam_cx (centerx of boss arena)

        self.cam_cx_pos = next(
            label_data
            for label_data in level_data['layered_objects']['labels']
            if label_data['text'] == 'cam_cx'
        )['pos']

        ### scroll level so player ends up positioned above given label

        # can be be 'landing', 'midpoint' or 'endpoint' depending on which
        # checkpoint the player reached
        #
        # for now, while we are still adding content to the first level,
        # we'll hardcode this value to specific areas of interest
        label_name = 'landing'

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

        ### overall camera routine, depending on the actual routine assigned
        ### to the attribute, may cause the camera to track the player
        ### (by moving the whole level so the player is near the middle of the
        ### screen)
        self.camera_overall_routine()

        ### the feet routine, depending on the actual routine assigned to the
        ### attribute, may move the level gradually so the player's feet
        ### ends up in a certain vertical distance from the top of the screen,
        ### but only if the player is touching the floor and if the player
        ### isn't in that position already
        self.camera_feet_routine()

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

        ### the feet routine, depending on the actual routine assigned to the
        ### attribute, may move the level gradually so the player's feet
        ### ends up in a certain vertical distance from the top of the screen,
        ### but only if the player is touching the floor and if the player
        ### isn't in that position already
        self.camera_feet_routine()

        ###

        current_cam_cx = self.cam_cx_pos + scrolling

        if abs(SCREEN_RECT.centerx - current_cam_cx[0]) > 2:
            self.move_level((-3, 0))

        else:

            diff = SCREEN_RECT.centerx - current_cam_cx[0]
            self.move_level((diff, 0))

            self.update = self.normal_update
            REFS.level_boss.begin_fighting()
            music.load(str(MUSIC_DIR / 'boss_fight_by_juhani_junkala.ogg'))
            music.play(-1)

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

        for projectile in PROJECTILES:
            projectile.update()

        for prop in FRONT_PROPS:
            prop.update()

        ### execute scheduled tasks
        execute_tasks()

    def move_level_to_keep_pc_within_area(self):
        """Move the level so playable character (pc) is always inside area.

        That is, the camera tracking area.
        """

        player_rect = self.player.rect

        clamped_rect = player_rect.clamp(CAMERA_TRACKING_AREA)

        if clamped_rect != player_rect:

            self.move_level(

                tuple(
                    a - b
                    for a, b
                    in zip(clamped_rect.topleft, player_rect.topleft)
                )

            )

    def move_level_to_align_feet(self):

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

    def draw_level(self):

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
#        cam_area = CAMERA_TRACKING_AREA
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

        for column in HEALTH_COLUMNS:
            column.draw()

        update_screen()

    def getting_to_boss_area(self):

        # TODO this method, which is used by an invisible colliding trigger,
        # actually raises and exception instead of returning a bool (a bool would
        # be the return value the colliding trigger expects);
        #
        # for now it is fine cause it all works, but we must do some about it;
        # perhaps we should change the invisible colliding trigger's API so that
        # it watches for exceptions as well if requested

        ###
        self.boss_gate1.trigger_opening()

        ### disable camera overall and feet tracking, since
        ### screen will now be focused solely on the arena,
        ### not moving for the duration of the battle

        self.disable_overall_tracking_for_camera()
        self.disable_feet_tracking_for_camera()

        ###

        self.update = self.moving_update
        HEALTH_COLUMNS.add(REFS.level_boss.health_column)

        self.player.stop_charging()
        self.player.reset_time_tracking_attributes()

        # TODO probaby use time in milliseconds, converting to
        # frames before feeding to function

        input_data = (

            generate_input_data(
                key_range_pairs = (
                    (KEYBOARD_CONTROLS['right'], (33,)),
                ),
                no_of_frames=30*3,
            )

        )

        raise LoopException(
            next_input_mode_name='play',
            input_data=input_data,
        )

    def save_progress(self, progress_collection_name, progress_value):

        progress_collection = (
            REFS.slot_data.setdefault(progress_collection_name, [])
        )

        if progress_value in progress_collection:
            return

        progress_collection.append(progress_value)

        ### TODO must move this call into a try/except clause (after
        ### pondering what to do)
        save_pyl(REFS.slot_data, REFS.slot_path)

    save_beaten_boss = partialmethod(save_progress, 'beaten_bosses')
    save_encounter = partialmethod(save_progress, 'encounters')


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

    elif name.startswith('crate'):
        obj = Crate(**obj_data)

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

    elif name == 'chain_crate_hanger':
        obj = ChainCrateHanger(**obj_data)

    else:
        raise RuntimeError("This block should never be reached.")

    obj.layer_name = layer_name
    return obj
