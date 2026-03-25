"""Facility for level manager class."""

### standard library imports
from functools import partial


### third-party imports

from pygame.display import update as update_screen

from pygame.mixer import music

from pygame.math import Vector2


### local imports

from ...config import REFS, SOUND_MAP, MUSIC_DIR

from ...pygamesetup.constants import (
    SCREEN_RECT,
    blit_on_screen,
    reset_fade_accumulator,
    apply_fade,
    msecs_to_frames,
)

from ...ourstdlibs.behaviour import CallList, do_nothing

from ...ourstdlibs.pyl import save_pyl

from ...userprefsman.main import USER_PREFS

from .middleprops.invisiblecollidingtrigger import InvisibleCollidingTrigger

from .common import (

    CLOUDS,
    BUILDINGS,

    BACK_PROPS_NEAR_SCREEN,
    MIDDLE_PROPS_NEAR_SCREEN,
    BLOCKS_NEAR_SCREEN,
    ACTORS_NEAR_SCREEN,
    FRONT_PROPS_NEAR_SCREEN,

    PROJECTILES,
    VFX_ELEMENTS,
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

from .constants import FLOOR_LEVEL, MOVE_CLOUDS_FRAMES, clouds_movement_delta



CAMERA_TRACKING_AREA = SCREEN_RECT.copy()
CAMERA_TRACKING_AREA.width //= 5
CAMERA_TRACKING_AREA.height += -40
CAMERA_TRACKING_AREA.center = SCREEN_RECT.center



class LevelManagerLoopManagement:

    def enable_camera_on_pc(self):
        """Enable camera tracking on playable character."""
        self.camera_overall_routine = self.move_level_to_keep_pc_within_area

    def disable_camera_on_pc(self):
        """Disable camera tracking on playable character."""
        self.camera_overall_routine = do_nothing

    def enable_camera_on_floor_level(self):
        """Enable camera tracking on floor level."""
        self.camera_feet_routine = self.move_level_to_align_feet

    def disable_camera_on_floor_level(self):
        """Disable camera tracking on floor level."""
        self.camera_feet_routine = do_nothing

    def enable_all_camera_tracking(self):
        """Enable all camera tracking (playable character and floor level)."""

        self.enable_camera_on_pc()
        self.enable_camera_on_floor_level()

    def disable_all_camera_tracking(self):
        """Disable all camera tracking (playable character and floor level)."""

        self.disable_camera_on_pc()
        self.disable_camera_on_floor_level()

    def control_player(self):
        self.player.control()

    def update_clouds(self):

        ### move clouds if it is time

        self.move_clouds_countdown -= 1

        if self.move_clouds_countdown <= 0:

            CLOUDS.rect.move_ip(1, 0)
            clouds_movement_delta.x += 1

            self.move_clouds_countdown = MOVE_CLOUDS_FRAMES


        ### also shift rightmost cloud to left of all clouds
        ### so it enters the screen again over time

        screen_right = SCREEN_RECT.right

        clouds_left = CLOUDS.rect.left

        moved_cloud = False

        for cloud in CLOUDS:

            if cloud.rect.left > screen_right:

                cloud.rect.right = clouds_left - cloud.rect.width
                moved_cloud = True


        if moved_cloud:

            self.clouds_topleft = CLOUDS.rect.topleft
            clouds_movement_delta.update(0, 0)

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

        self.update_clouds()

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

        for element in VFX_ELEMENTS:
            element.update()

        for prop in FRONT_PROPS_NEAR_SCREEN:
            prop.update()

        for column in HEALTH_COLUMNS:
            column.update()

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

        self.update_clouds()

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

        for element in VFX_ELEMENTS:
            element.update()

        for prop in FRONT_PROPS_NEAR_SCREEN:
            prop.update()

        for column in HEALTH_COLUMNS:
            column.update()

        ### execute scheduled tasks
        update_task_manager()

        ###

        if not cam_away_from_screen_center:

            on_scripted_scene_exit = CallList(

                [

                    partial(
                        music.load,
                        str(MUSIC_DIR / 'boss_fight_by_juhani_junkala.ogg'),
                    ),
                    partial(music.play, -1),
                    REFS.level_boss.begin_fighting,
                ]

            )
            
            if 'kane' in REFS.slot_data.get('bosses_you_talked_with', ()):

                self.control = self.control_player
                self.update = self.normal_update
                self.draw = self.draw_level

                on_scripted_scene_exit()

            else:

                self.enter_scripted_scene(
                    'kane_boss_arrival',
                    on_exit=on_scripted_scene_exit,
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

        for element in VFX_ELEMENTS:
            element.rect.move_ip(diff)

        ###
        scrolling_x, scrolling_y = scrolling

        ###

        CLOUDS.rect.topleft = self.clouds_topleft + clouds_movement_delta

        clouds_scrolling_x = scrolling_x // 300
        clouds_scrolling_y = scrolling_y // 60

        CLOUDS.rect.move_ip(clouds_scrolling_x, clouds_scrolling_y)

        ###

        BUILDINGS.rect.bottomleft = (
            SCREEN_RECT.move(0, self.buildings_y_offset).bottomleft
        )

        buildings_scrolling_x = scrolling_x // 80
        buildings_scrolling_y = scrolling_y // 15

        BUILDINGS.rect.move_ip(buildings_scrolling_x, buildings_scrolling_y)

    def draw_level(self):

        blit_on_screen(self.bg, (0, 0))

        CLOUDS.draw_on_screen()

        BUILDINGS.draw_on_screen()

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

        for element in VFX_ELEMENTS:
            element.draw()

        for prop in FRONT_PROPS_NEAR_SCREEN:
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

        ###
        self.boss_gate1.trigger_opening()

        ### place a new trigger to the right of boss gate 0 that opens it
        ### when the player walks back to the satellite after defeating the
        ### boss

        reopening_trigger = (

            InvisibleCollidingTrigger(
                on_collision=self.boss_gate0.trigger_opening,
                width=16,
                height=64,
                coordinates_name='midbottom',
                coordinates_value=self.boss_gate0.rect.move(100, 0).midbottom,
            )

        )

        append_ready_task(
            partial(add_obj, reopening_trigger)
        )

        ### disable camera on playable character and floor level, since
        ### screen will now be focused solely on the arena,
        ### not moving for the duration of the battle
        self.disable_all_camera_tracking()

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
                on_exit=self.player.health_column.trigger_health_recovery,

            ),

            delta_t=frame_duration,
            unit='frames',

        )

        ### must return True so trigger nows all succeeded
        return True

    def enter_boss_parting_scene(self):

        if 'kane' in REFS.slot_data.get('beaten_bosses', ()):

            music_volume = (
                (USER_PREFS['MASTER_VOLUME']/100)
                * (USER_PREFS['MUSIC_VOLUME']/100)
            )

            music.set_volume(music_volume)
            music.load(str(MUSIC_DIR / 'level_1_by_juhani_junkala.ogg'))
            music.play(-1)

            ### TODO should probably also:
            ###
            ### - deactivate kane and play the deactivation sound before
            ### leaving

            self.boss_gate1.trigger_opening()

            ### schedule camera pan to player

            ## it starts in 1 second
            frames_offset = msecs_to_frames(1000)

            ## and takes 2 seconds to complete
            frames = msecs_to_frames(2000)

            ##

            current_pos = scrolling

            delta_pos = (

                Vector2(SCREEN_RECT.centerx, FLOOR_LEVEL)
                - self.player.rect.midbottom

            )

            final_pos = current_pos + delta_pos

            increment = 1 / frames

            tracked_pos = tuple(map(round, current_pos))
            accumulator = 0

            for frame_delta in range(1, frames):

                accumulator += increment

                pos = tuple(
                    map(round, current_pos.lerp(final_pos, accumulator))
                )

                if pos != tracked_pos:

                    diff = Vector2(pos) - tracked_pos

                    append_timed_task(

                        CallList(

                            [
                                partial(self.move_level, diff),
                                update_chunks_and_layers,
                            ]

                        ),

                        delta_t=frames_offset+frame_delta,
                        unit='frames',
                    )

                    tracked_pos = pos


            append_timed_task(
                self.enable_all_camera_tracking,
                delta_t=frames_offset+frame_delta+1,
                unit='frames',
            )

            ###

            frame_duration = (

                self.player.act_on_given_script(

                    [
                        {
                            'type': 'wait',
                            'secs': 3,
                        }
                    ]
                )
            )

            append_timed_task(

                self.player.teleport_away,
                delta_t=frame_duration,
                unit='frames',

            )

        else:

            self.enter_scripted_scene(
                'kane_boss_parting',
                restore_camera=False,
            )

    def schedule_level_restart(self):

        append_timed_task(
            REFS.states.level_manager.restart_level,
            delta_t=4000,
            unit='milliseconds',
        )

        append_timed_task(

            reset_fade_accumulator,

            delta_t=2500,
            unit='milliseconds',

        )

        append_timed_task(

            partial(
                setattr,
                self,
                'draw',
                self.draw_fading_level
            ),

            delta_t=2500,
            unit='milliseconds',

        )

    def draw_fading_level(self):

        blit_on_screen(self.bg, (0, 0))

        CLOUDS.draw_on_screen()

        BUILDINGS.draw_on_screen()

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

        for element in VFX_ELEMENTS:
            element.draw()

        for prop in FRONT_PROPS_NEAR_SCREEN:
            prop.draw()

        for column in HEALTH_COLUMNS:
            column.draw()

        apply_fade()

        update_screen()
