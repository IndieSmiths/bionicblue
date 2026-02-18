"""Facility for level manager class."""

### standard library imports
from functools import partial, partialmethod


### third-party imports

from pygame.display import update as update_screen

from pygame.mixer import music


### local imports

from ...config import REFS, SOUND_MAP, MUSIC_DIR

from ...pygamesetup.constants import SCREEN_RECT, blit_on_screen

from ...ourstdlibs.behaviour import CallList, do_nothing

from ...ourstdlibs.pyl import save_pyl

from .middleprops.invisiblecollidingtrigger import InvisibleCollidingTrigger

from .common import (

    BACK_PROPS_NEAR_SCREEN,
    MIDDLE_PROPS_NEAR_SCREEN,
    BLOCKS_NEAR_SCREEN,
    ACTORS_NEAR_SCREEN,

    PROJECTILES,
    FRONT_PROPS,
    HEALTH_COLUMNS,

    CHUNKS,

    scrolling,
    scrolling_backup,

    add_obj,
    remove_obj,
    update_chunks_and_layers,

)

from .taskmanager import (
    append_ready_task,
    append_timed_task,
    update_task_manager,
)

from .constants import FLOOR_LEVEL



CAMERA_TRACKING_AREA = SCREEN_RECT.copy()
CAMERA_TRACKING_AREA.width //= 5
CAMERA_TRACKING_AREA.height += -40
CAMERA_TRACKING_AREA.center = SCREEN_RECT.center


class LevelManagerLoopManagement:

    def enable_overall_tracking_for_camera(self):
        self.camera_overall_routine = self.move_level_to_keep_pc_within_area

    def disable_overall_tracking_for_camera(self):
        self.camera_overall_routine = do_nothing

    def enable_feet_tracking_for_camera(self):
        self.camera_feet_routine = self.move_level_to_align_feet

    def disable_feet_tracking_for_camera(self):
        self.camera_feet_routine = do_nothing

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
        update_task_manager()

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

        cam_away_from_screen_center = (
            abs(SCREEN_RECT.centerx - current_cam_cx[0]) > 2
        )

        if cam_away_from_screen_center:
            self.move_level((-3, 0))

        else:

            diff = SCREEN_RECT.centerx - current_cam_cx[0]
            self.move_level((diff, 0))

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
        update_task_manager()

        ###

        ### TODO must enter dialogue only if we didn't play it
        ### already, otherwise set the music and enter the fight

        if not cam_away_from_screen_center:

            on_exit = CallList(

                [

                    partial(
                        music.load,
                        str(MUSIC_DIR / 'boss_fight_by_juhani_junkala.ogg'),
                    ),
                    partial(music.play, -1),
                    REFS.level_boss.begin_fighting,
                ]

            )

            self.enter_scripted_scene(
                'kane_boss_arrival',
                on_exit=on_exit,
                restore_camera=False,
            )

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

        self.player.act_on_given_script(

            [
                {
                    'type':'walk',
                    'delta_x': 150,
                },

                {
                    'type': 'wait',
                    'secs': 1.7,
                },
            ]

        )

        return True

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

    def add_food_box_trigger(self):
        """Add trigger to consume food box."""

        food_box_trigger = (

            InvisibleCollidingTrigger(
                on_collision=self.consume_food_box,
                width=8,
                height=8,
                coordinates_name='midbottom',
                coordinates_value=self.food_box.rect.midbottom,
            )

        )

        add_obj(food_box_trigger)

    def consume_food_box(self):
        """"""

        ### remove food box immediately and trigger sound

        append_ready_task(

            CallList(

                (
                    partial(remove_obj, self.food_box),
                    SOUND_MAP['triumph_on_getting_food_box.wav'].play,
                )

            )

        )

        ### trigger muscle flexing animation measuring time the
        ### animation will take

        frame_duration = self.player.act_on_given_script(

            [

                {
                    'type': 'wait',
                    'animation_blend': 'muscle_flex',
                    'secs': 2,
                },

            ]

        )

        append_timed_task(

            partial(

                self.show_popup_info,
                'after_meal_power_up',

            ),

            delta_t=frame_duration,
            unit='frames',

        )

        ### must return True so trigger nows all succeeded
        return True
