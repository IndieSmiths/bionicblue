"""Facility w/ class extension for managing the loop during scripted scenes."""

### standard library import
from itertools import cycle


### third-party imports

from pygame import Rect

from pygame.locals import (

    QUIT,

    KEYDOWN,

    K_ESCAPE,
    K_RETURN,
    K_DOWN,
    K_RIGHT,

    JOYBUTTONDOWN,

)

from pygame.display import update as update_screen

from pygame.draw import (
    rect as draw_rect,
    polygon as draw_polygon,
)

from pygame.math import Vector2


### local imports

from .....config import REFS, quit_game

from .....pygamesetup import SERVICES_NS

from .....pygamesetup.constants import (
    SCREEN,
    GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS,
    GAMEPADDIRECTIONALPRESSED,
)

from .....pygamesetup.gamepadservices import GAMEPAD_NS

from .....ourstdlibs.behaviour import do_nothing

from .....userprefsman.main import (
    USER_PREFS,
    KEYBOARD_CONTROLS,
    GAMEPAD_CONTROLS,
)

from ...common import (

    CLOUDS,
    BUILDINGS,

    BACK_PROPS_NEAR_SCREEN,
    MIDDLE_PROPS_NEAR_SCREEN,
    BLOCKS_NEAR_SCREEN,
    ACTORS_NEAR_SCREEN,
    FRONT_PROPS_NEAR_SCREEN,

    PROJECTILES,
    VFX_ELEMENTS,

    scrolling,
    scrolling_backup,

)

from ...taskmanager import update_task_manager

from ..constants import (

    DIALOGUE_BOX,
    TEXT_BOX,

    text_box_colliderect,

)

from .updateassistance import UpdateAssistance



ONE_ITEM_RANGE = range(1)
THREE_ITEMS_RANGE = range(3)

NEXT_DRAW_TRIANGLE = cycle(

    (
        *((True,) * 20),
        *((False,)* 20)
    )

).__next__


_SMALL_SQUARE = Rect(0, 0, 8, 5)


def draw_triangle(last_char):

    _SMALL_SQUARE.bottomleft = last_char.rect.bottomright

    draw_polygon(

        SCREEN,
        'white',

        (
            _SMALL_SQUARE.topleft,
            _SMALL_SQUARE.topright,
            _SMALL_SQUARE.midbottom,
        ),

    )


class ScriptedSceneLoopManagement(UpdateAssistance):
    """Methods to manage the loop during scripted scenes."""

    def enter_scripted_scene(
        self,
        scripted_scene_name,
        on_exit=do_nothing,
        restore_camera=True,
    ):

        self.disable_all_camera_tracking()

        self.control = self.scene_control
        self.update = self.scene_update
        self.draw = self.scene_draw

        self.on_exit = on_exit
        self.restore_camera = restore_camera

        ###
        self.player.stop_charging()
        self.player.reset_time_tracking_attributes()

        ###

        ## XXX
        ##
        ## instead of performing cleanup measures here (like calling
        ## clear() on collections), should probably do cleanup in more
        ## appropriate spots, like when leaving the scene or when the
        ## play leaves the level (including via the pause menu);
        ##
        ## also, there may be other stuff to clean up that we are missing
        ## (although nothing that is causing a bug right now); one instance
        ## is the iterators holding functions to perform scripted actions;
        ## check this when you have time

        data = self.scripted_scene_map[scripted_scene_name]

        locale = USER_PREFS['LOCALE']

        self.remaining_lines_deque.clear()
        self.remaining_lines_deque.extend(data['lines_data'][locale])

        self.action_map = data['action_map']

        self.current_line = ''
        self.current_character = ''
        self.line_index = -1

        self.character_map.clear()

        self.character_map.update(

            (
                character_name,
                get_character_reference(
                    *self.character_retrieval_map[character_name]
                )
            )

            for character_name in data['characters']

        )

        ###

        player = REFS.states.level_manager.player

        player.x_speed = 0

        state_name = anim_name = (
            'idle_right'
            if 'right' in player.aniplayer.anim_name
            else 'idle_left'
        )

        player.set_state(state_name)
        player.aniplayer.switch_animation(anim_name)

        ###
        self.get_next_line()

        ### must return True so trigger knows
        ### entering scripted scene succeeded
        return True

    def exit_scripted_scene(self):

        self.control = self.control_player
        self.update = self.normal_update
        self.draw = self.draw_level

        ### clean up
        self.animation_blend_map.clear()
        ###

        if self.restore_camera:
            self.enable_all_camera_tracking()

        ### execute on exit action
        self.on_exit()

    def scene_control(self):
        
        if self.drive_scene_state == self.present_dialogue:
            self.process_mid_dialogue_input()

        else:
            self.process_mid_action_input()

    def process_mid_dialogue_input(self):

        ### we have to grab the state of pressed keys before
        ### entering the for-loop where we process the events;
        ###
        ### however, since the call to pygame.event.get() (indirectly
        ### called by SERVICES_NS.get_events()) must be made before
        ### the call to pygame.key.get_pressed() (indirectly called
        ### by SERVICES_NS.get_pressed_keys()) in order for pygame
        ### internals to work correctly, we call SERVICES_NS.get_events()
        ### before and store the events so we can start procesing then
        ### in the for-loop

        events = SERVICES_NS.get_events()
        pressed_state = SERVICES_NS.get_pressed_keys()

        ### process events

        for event in events:

            if event.type == KEYDOWN:

                if event.key == K_ESCAPE:
                    REFS.pause()

                elif event.key in (
                    K_DOWN,
                    K_RIGHT,
                    KEYBOARD_CONTROLS['down'],
                    KEYBOARD_CONTROLS['right'],
                    KEYBOARD_CONTROLS['shoot'],
                    KEYBOARD_CONTROLS['jump'],
                    K_RETURN,
                ):
                    self.advance_dialogue_if_possible()

            elif event.type == JOYBUTTONDOWN:

                if event.button in (
                    GAMEPAD_CONTROLS['start_button'],
                    GAMEPAD_CONTROLS['shoot'],
                    GAMEPAD_CONTROLS['jump'],
                ):
                    self.advance_dialogue_if_possible()

            elif event.type == GAMEPADDIRECTIONALPRESSED:

                if event.direction in ('down', 'right'):
                    self.advance_dialogue_if_possible()

            elif event.type in GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS:
                GAMEPAD_NS.setup_gamepad_if_existent()

            elif event.type == QUIT:
                quit_game()


        ### process state of keyboard/gamepad triggers

        ## if some of the keyboard/gamepad directional or action buttons are
        ## pressed, accelerate dialogue

        if (

            ## keyboard directionals

            pressed_state[K_DOWN]
            or pressed_state[K_RIGHT]
            or pressed_state[KEYBOARD_CONTROLS['down']]
            or pressed_state[KEYBOARD_CONTROLS['right']]

            ## keyboard action buttons

            or pressed_state[KEYBOARD_CONTROLS['shoot']]
            or pressed_state[KEYBOARD_CONTROLS['jump']]
            or pressed_state[K_RETURN]

            ## gamepad directionals

            or GAMEPAD_NS.x_sum > 0
            or GAMEPAD_NS.y_sum > 0

            ## gamepad action buttons

            or GAMEPAD_NS.get_button(GAMEPAD_CONTROLS['start_button'])
            or GAMEPAD_NS.get_button(GAMEPAD_CONTROLS['shoot'])
            or GAMEPAD_NS.get_button(GAMEPAD_CONTROLS['jump'])

        ):
            self.char_quantity_range = THREE_ITEMS_RANGE


        else:
            self.char_quantity_range = ONE_ITEM_RANGE


    def process_mid_action_input(self):

        for event in SERVICES_NS.get_events():

            if event.type in GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS:
                setup_gamepad_if_existent()

            elif event.type == QUIT:
                quit_game()

    def scene_update(self):

        ### backup scrolling
        scrolling_backup.update(scrolling)

        self.drive_scene_state()

        self.player.update()

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

        ### execute scheduled tasks
        update_task_manager()

    def scene_draw(self):
        """Draw level elements (and dialogue elements when applicable)."""

        SCREEN.fill(self.bg_color)

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

        if self.drive_scene_state == self.present_dialogue:
            self.draw_dialogue_elements()

        update_screen()

    def draw_dialogue_elements(self):
        """Draw dialogue elements."""

        draw_rect(SCREEN, 'black', DIALOGUE_BOX, border_radius=8)
        draw_rect(SCREEN, 'orange', DIALOGUE_BOX, 1, border_radius=8)

        text_canvas = self.text_canvas
        text_canvas.fill('black')
        offset = -Vector2(TEXT_BOX.topleft)
        blit_on_text_canvas = self.blit_on_text_canvas

        for obj in self.all_chars_2d:
            if text_box_colliderect(obj.rect):
                blit_on_text_canvas(obj.image, obj.rect.move(offset))

        self.text_box_obj.draw()
        self.character_portrait.aniplayer.draw()

        if self.waiting_for_user_to_advance and NEXT_DRAW_TRIANGLE():
            draw_triangle(self.all_chars_2d[-1])


def get_character_reference(obj, attr_names):

    for attr_name in attr_names:
        obj = getattr(obj, attr_name)

    return obj
