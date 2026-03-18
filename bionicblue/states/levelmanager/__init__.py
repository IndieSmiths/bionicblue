"""Facility for level manager class."""

### standard library import
from functools import partial


### third-party imports

from pygame import Surface

from pygame.mixer import music

from pygame.math import Vector2


### local imports

from ...config import (
    REFS,
    LEVELS_DIR,
    MUSIC_DIR,
)

from ...pygamesetup.constants import SCREEN_RECT

from ...ourstdlibs.pyl import load_pyl

from ...userprefsman.main import USER_PREFS

from .player import Player

from .backprops.citywall import CityWall
from .backprops.lightpolefront import LightPoleFront

from .middleprops.ladder import Ladder
from .middleprops.chains import Chains
from .middleprops.chaincratehanger import ChainCrateHanger
from .middleprops.invisiblecollidingtrigger import InvisibleCollidingTrigger
from .middleprops.foodbox import FoodBox
from .middleprops.smartphone import Smartphone
from .middleprops.satellitedish import SatelliteDish

from .blocks.cityblock import CityBlock
from .blocks.spike import Spike
from .blocks.floatingplatform import FloatingPlatform
from .blocks.crate import Crate
from .blocks.gate import Gate

from .actors.gruntbot import GruntBot
from .actors.watcherbot import WatcherBot
from .actors.rabbiterror import Rabbiterror
from .actors.chiefsecbot import ChiefSecurityBot
from .actors.giovanni import Giovanni

from .frontprops.lightpoleback import LightPoleBack

from .prototypemessage import message

from .common import (

    HEALTH_COLUMNS,

    VICINITY_RECT,

    scrolling,
    scrolling_backup,

    group_objects,
    add_obj,
    update_chunks_and_layers,

)

from .loopmgmt import LevelManagerLoopManagement

from .popupmgmt import LevelManagerPopupManagement

from .scriptedscenemgmt import ScriptedSceneManagement

from .constants import FLOOR_LEVEL



class LevelManager(
    LevelManagerLoopManagement,
    LevelManagerPopupManagement,
    ScriptedSceneManagement,
):

    def __init__(self):

#        from ...textman import render_text
#
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
        self.load_scripted_scenes()

        self.control = self.control_player

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
            if label_data['text'] == 'npc'
        )['pos']

        npc = Giovanni(npc_midbottom)
        npc.layer_name = 'actors'
        add_obj(npc)

        self.npc = npc

        ### add boss

        boss_bottomright = next(
            label_data
            for label_data in level_data['layered_objects']['labels']
            if label_data['text'] == 'boss_br'
        )['pos']

        boss = ChiefSecurityBot('chief_sec_bot', boss_bottomright, facing_right=False)
        boss.layer_name = 'actors'
        add_obj(boss)

        ### add gates and related objs

        ## npc gate

        # whether npc was visited previously or not
        was_npc_visited = 'giovanni' in REFS.slot_data.get('encounters', ())

        # pos
        npc_gate_pos = next(
            label_data
            for label_data in level_data['layered_objects']['labels']
            if label_data['text'] == 'ngate'
        )['pos']

        # whether gate must be closed
        npc_gate_closed = True if was_npc_visited else False

        npc_gate = self.npc_gate = (
            Gate(midbottom=npc_gate_pos, closed=npc_gate_closed)
        )

        add_obj(npc_gate)

        # food box
        #
        # (note that although we might not use food_box_pos here,
        # we must still extract it, since we store it as an attribute
        # for later use);

        food_box = self.food_box = FoodBox()

        food_box_pos = self.food_box_pos = next(
            label_data
            for label_data in level_data['layered_objects']['labels']
            if label_data['text'] == 'food_box'
        )['pos']

        if npc_gate_closed:

            food_box.rect.midbottom = food_box_pos
            add_obj(food_box)
            self.add_food_box_trigger()

        ## boss gates

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

        boss_gate0 = Gate(midbottom=bgate0_pos, closed=True)
        boss_gate1 = Gate(midbottom=bgate1_pos, closed=True)

        add_obj(boss_gate0)
        add_obj(boss_gate1)

        self.boss_gate1 = boss_gate1

        ### add colliding trigger for npc encounter

        npc_scene_trg_pos = next(
            label_data
            for label_data in level_data['layered_objects']['labels']
            if label_data['text'] == 'npc_scene_trg'
        )['pos']

        npc_dialogue_name = (

            'giovanni_post_boss'
            if 'kane' in REFS.slot_data.get('beaten_bosses', ())

            else 'giovanni_pre_boss'

        )

        npc_scene_trigger = (

            InvisibleCollidingTrigger(

                on_collision=(
                    partial(self.enter_scripted_scene, npc_dialogue_name)
                ),
                width=16,
                height=64,
                coordinates_name='midbottom',
                coordinates_value=npc_scene_trg_pos,

            )

        )

        add_obj(npc_scene_trigger)

        ### add colliding triggers for boss gates

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

        ### store smartphone instance
        self.smartphone = Smartphone()

        ### scroll level so player ends up positioned above given label

        satellite_dish_offset = Vector2(48, 0)

        last_checkpoint_name = REFS.last_checkpoint_name

        for label_name in ('landing', 'midpoint', 'endpoint'):

            pos = next(
                label_data
                for label_data in level_data['layered_objects']['labels']
                if label_data['text'] == label_name 
            )['pos']

            if label_name == 'landing':

                satdish = (

                    SatelliteDish(
                        checkpoint_name=label_name,
                        midbottom=(pos + satellite_dish_offset),
                        animation_name='activated',
                    )

                )

            elif last_checkpoint_name == 'landing':

                satdish = (

                    SatelliteDish(
                        checkpoint_name=label_name,
                        midbottom=(pos + satellite_dish_offset),
                        animation_name='deactivated',
                    )

                )

            elif label_name == 'midpoint':

                satdish = (

                    SatelliteDish(
                        checkpoint_name=label_name,
                        midbottom=(pos + satellite_dish_offset),
                        animation_name='activated',
                    )

                )

            else:

                animation_name = (
                    'deactivated'
                    if last_check_point == 'midpoint'
                    else 'activated'
                )

                satdish = (

                    SatelliteDish(
                        checkpoint_name=label_name,
                        midbottom=(pos + satellite_dish_offset),
                        animation_name=animation_name,
                    )

                )

            add_obj(satdish)

            if satdish.aniplayer.anim_name == 'deactivated':

                satellite_trigger = (

                    InvisibleCollidingTrigger(

                        on_collision=satdish.trigger_activation,
                        width=32,
                        height=40,
                        coordinates_name='midbottom',
                        coordinates_value=satdish.rect.midbottom,
                    )

                )

                add_obj(satellite_trigger)

            if label_name == last_checkpoint_name:
                landing_pos = pos

        dx = SCREEN_RECT.centerx - landing_pos[0]
        dy = FLOOR_LEVEL - landing_pos[1]
        self.move_level((dx, dy))

        self.player.rect.centerx = SCREEN_RECT.centerx
        self.player.rect.bottom = SCREEN_RECT.top

        ### update chunks and list objects on screen
        update_chunks_and_layers()


def instantiate(obj_data, layer_name):

    name = obj_data['name']

    if name == 'city_wall':
        obj = CityWall(**obj_data)

    elif name == 'light_pole_front':
        obj = LightPoleFront(**obj_data)

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

    elif name == 'light_pole_back':
        obj = LightPoleBack(**obj_data)

    else:
        raise RuntimeError("This block should never be reached.")

    obj.layer_name = layer_name
    return obj
