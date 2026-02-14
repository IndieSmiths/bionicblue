"""Facility w/ class extension for managing the loop during scripted scenes."""

### standard library imports

from itertools import (
    chain,
    cycle,
    groupby,
    zip_longest,
)

from collections import deque

from functools import partial

from math import floor

from contextlib import suppress

### standard library import with local import replacement
### in case imported function is not available from
### standard library (since it might not be available in
### the Python version used)

try:
    from itertools import pairwise

except ImportError:
    from ...ourstdlibs.iterutils import pairwise


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

from pygame.draw import rect as draw_rect, polygon as draw_polygon

from pygame.math import Vector2

from pygame.mixer import music

### third-party imports with local import replacements
### in case imported functions are not available from
### third-party lib (since it might not be available in
### the pygame version used)

try:
    from pygame.math import lerp, smoothstep

except ImportError:
    from ...ourstdlibs.mathutils import lerp, smoothstep


### local imports

from ....config import REFS, MUSIC_DIR, quit_game

from ....pygamesetup import SERVICES_NS

from ....pygamesetup.constants import (
    SCREEN,
    GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS,
    GAMEPADDIRECTIONALPRESSED,
    msecs_to_frames,
)

from ....pygamesetup.gamepaddirect import GAMEPAD_NS, setup_gamepad_if_existent

from ....classes2d.single import UIObject2D

from ....classes2d.collections import UIList2D, UIDeque2D

from ....textman import render_text

from ....ourstdlibs.behaviour import CallList, do_nothing

from ....userprefsman.main import KEYBOARD_CONTROLS, GAMEPAD_CONTROLS

from ..middleprops.largedish import LargeDish

from ..common import (

    BACK_PROPS_NEAR_SCREEN,
    MIDDLE_PROPS_NEAR_SCREEN,
    BLOCKS_NEAR_SCREEN,
    ACTORS_NEAR_SCREEN,

    PROJECTILES,
    FRONT_PROPS,

    scrolling,
    scrolling_backup,

    add_obj,
    remove_obj,
    update_chunks_and_layers,

)

from ..taskmgmt import append_conditional_task, update_task_manager

from .constants import (

    DIALOGUE_BOX,
    PORTRAIT_BOX,
    TEXT_BOX,

    BOTTOMLEFT_ANCHOR,
    BOTTOMRIGHT_ANCHOR,

    text_box_colliderect,

)



TEXT_SETTINGS = {
    'style': 'regular',
    'size': 12,
    'padding': 2,
    'foreground_color': 'cyan',
}

_WAIT_BEFORE_LINE_ADVANCE_MSECS = 600

_WAIT_BEFORE_LINE_ADVANCE_FRAMES = (
    msecs_to_frames(_WAIT_BEFORE_LINE_ADVANCE_MSECS)
)

NEXT_CHARS = cycle((True, False)).__next__

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


class ScriptedSceneLoopManagement:
    """Methods to manage the loop during scripted scenes."""

    def enter_scripted_scene(
        self,
        scripted_scene_name,
        on_exit=do_nothing,
        restore_camera=True,
    ):

        self.disable_overall_tracking_for_camera()
        self.disable_feet_tracking_for_camera()

        self.control = self.scene_control
        self.update = self.scene_update
        self.draw = self.scene_draw

        self.on_exit = on_exit
        self.restore_camera = restore_camera

        ###
        self.player.stop_charging()
        self.player.reset_time_tracking_attributes()

        ###

        data = self.scripted_scene_map[scripted_scene_name]

        self.remaining_lines_deque.extend(data['lines_data'])
        self.action_map = data['action_map']

        self.current_line = ''
        self.current_character = ''
        self.line_index = -1

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

        print("Exiting scripted scene")

        self.control = self.control_player
        self.update = self.normal_update
        self.draw = self.draw_level

        ###

        if self.restore_camera:

            self.enable_overall_tracking_for_camera()
            self.enable_feet_tracking_for_camera()

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
                setup_gamepad_if_existent()

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

    def get_next_line(self):

        if self.remaining_lines_deque:

            current_line, line_contents, current_character, line_index = (
                self.remaining_lines_deque.popleft()
            )

            self.current_line = current_line
            self.line_contents = line_contents
            self.current_character = current_character
            self.line_index = line_index

            ###

            self.character_portrait = (
                self.character_portrait_map[current_character]
            )

            self.in_game_character = self.character_map[current_character]

            ###

            actions_before = self.action_map.get((current_line, 'before'), ())

            self.process_actions(actions_before)

            if self.action_call_groups:

                self.drive_scene_state = self.carry_actions

                self.advance_actions = (

                    zip_longest(
                        *self.action_call_groups,
                        fillvalue=do_nothing,
                    ).__next__

                )

                self.after_actions = self.prepare_dialogue_line

            else:
                self.prepare_dialogue_line()

        else:
            self.exit_scripted_scene()

    def process_actions(self, actions_data):

        self.action_call_groups = []

        for action_data in actions_data:

            action_type = action_data['type']

            if action_type == 'pan_camera':

                kwargs = action_data['keyword_arguments']

                current_x, current_y = scrolling

                _delta_x, _delta_y = (
                    kwargs.get('delta_x', 0),
                    kwargs.get('delta_y', 0),
                )

                final_x, final_y = (
                    current_x + _delta_x,
                    current_y + _delta_y,
                )

                interpol_func = (
                    lerp
                    if kwargs['linear_or_smooth'] == 'linear'
                    else smoothstep
                )

                no_of_frames = msecs_to_frames(kwargs['duration_value'] * 1000)
                frames_between_steps = kwargs['frames_between_steps']

                ### calculate number of steps

                no_of_steps = 0
                _gap_count = 0

                for _ in range(no_of_frames):

                    if _gap_count == 0:
                        no_of_steps += 1

                    _gap_count += 1

                    if _gap_count > frames_between_steps:
                        _gap_count = 0


                ### calculate deltas between points

                points = (

                    Vector2(
                        interpol_func(current_x, final_x, i/no_of_steps),
                        interpol_func(current_y, final_y, i/no_of_steps),
                    )

                    for i in range(no_of_steps+1)

                )

                deltas = [
                    b - a
                    for a, b in pairwise(points)
                ]

                step_deltas = deque()

                v = Vector2()

                for delta in deltas:

                    next_step = v + delta

                    x_diff = floor(next_step.x) - floor(v.x)
                    y_diff = floor(next_step.y) - floor(v.y)

                    step_deltas.append((x_diff, y_diff))

                    v = next_step

                ### create a deque with a call for each frame

                all_calls = deque()
                self.action_call_groups.append(all_calls)

                move_level_method = self.move_level

                _gap_count = 0

                for _ in range(no_of_frames):

                    call = (

                        (

                            CallList(

                                [
                                    partial(move_level_method, step_deltas.popleft()),
                                    update_chunks_and_layers,
                                ]

                            )

                            if step_deltas[0][0] or step_deltas[0][1]
                            else partial(move_level_method, step_deltas.popleft())

                        )

                        if _gap_count == 0

                        else do_nothing

                    )

                    all_calls.append(call)

                    _gap_count += 1

                    if _gap_count > frames_between_steps:
                        _gap_count = 0

            elif action_type == 'scripted_acting':

                kwargs = action_data['keyword_arguments']

                character = kwargs['character']
                scripted_actions = kwargs['scripted_actions']

                if character == 'Blue':

                    no_of_frames = (
                        self.player.act_on_given_script(scripted_actions)
                    )

                    all_calls = [do_nothing,] * no_of_frames

                else:

                    raise ValueError(
                        "value of 'character' argument must be one used"
                        " in either of the previous if-elif blocks"
                    )

                self.action_call_groups.append(all_calls)

            elif action_type == 'play_music':

                music_filename = (
                    action_data['keyword_arguments']['music_filename']
                )

                music.load(str(MUSIC_DIR / music_filename))
                music.play(-1)

            elif action_type == 'display_dish':

                kwargs = action_data['keyword_arguments']

                animation_name = kwargs['animation_name']

                ## add objs

                # positions

                food_box_midbottom = self.player.rect.move(20, 0).bottomright

                dish_center = (
                    food_box_midbottom[0],
                    food_box_midbottom[1] - 56,
                )

                # food box

                food_box = self.food_box
                food_box.rect.midbottom = food_box_midbottom

                add_obj(food_box)

                # dish

                dish = LargeDish(animation_name, dish_center)
                add_obj(dish)

                ## append task we'll use to remove them

                awaited_line = self.line_index + kwargs['lines_to_wait']

                condition_checker = (
                    partial(self.check_line_index, awaited_line)
                )

                append_conditional_task(
                    partial(remove_obj, dish),
                    condition_checker,
                )

                append_conditional_task(
                    partial(remove_obj, food_box),
                    condition_checker,
                )

            elif action_type == 'record_encounter':
                ...
                # TODO use same call that records boss defeat
                print("Recorded encounter")

            elif action_type == 'record_talk_with_boss':
                ...
                # TODO use same call that records boss defeat
                print("Talked with boss")

            elif action_type == 'npc_gate_closes':
                self.npc_gate.trigger_closing()

            elif action_type == 'place_food_box':

                food_box_pos = self.food_box_pos + scrolling
                food_box = self.food_box
                food_box.rect.midbottom = food_box_pos

                add_obj(food_box)

                ### TODO also add trigger to eat it

            else:

                raise ValueError(
                    "'action_type' value must be one used"
                    " in either of the previous if-elif blocks"
                )

    def check_line_index(self, line_index):
        return self.line_index == line_index

    def prepare_dialogue_line(self):

        in_game_character = self.in_game_character
        portrait = self.character_portrait

        ## positioning for dialogue elements depends on direction the
        ## character is facing

        is_character_facing_right = self.is_character_facing_right = (
            'right' in in_game_character.aniplayer.anim_name
        )

        if is_character_facing_right:

            PORTRAIT_BOX.bottomleft = BOTTOMLEFT_ANCHOR
            TEXT_BOX.bottomright = BOTTOMRIGHT_ANCHOR

            portrait.aniplayer.switch_animation('portrait_speaking_right')
            in_game_character.aniplayer.switch_animation('speaking_idle_right')

        else:

            TEXT_BOX.bottomleft = BOTTOMLEFT_ANCHOR
            PORTRAIT_BOX.bottomright = BOTTOMRIGHT_ANCHOR

            portrait.aniplayer.switch_animation('portrait_speaking_left')
            in_game_character.aniplayer.switch_animation('speaking_idle_left')

        ###
        portrait.rect.center = PORTRAIT_BOX.center

        ###

        ### XXX instead of rendering individual characters, could
        ### render whole word and divided it, even roughly, into
        ### surfaces; don't know if this would look pleasing, but
        ### rendering the word whole will likely provide the best
        ### end result (since in some cases characters merged together
        ### when rendered beside each other); the result for each
        ### word could be cached as well; this sort of thing could even be
        ### a requirement in specific languages/scripts; ponder;

        words = UIList2D(

            UIList2D(

                UIObject2D.from_surface(

                    render_text(
                        char,
                        **TEXT_SETTINGS,
                    )

                )

                for char in word

            )

            for word in self.line_contents.split()

        )

        for word in words:

            word.rect.snap_rects_ip(
                retrieve_pos_from='topright',
                assign_pos_to='topleft',
                offset_pos_by=(-3, 0),
            )

        words.rect.snap_rects_intermittently_ip(

            dimension_name='width',
            dimension_unit='pixels',
            max_dimension_value=TEXT_BOX.width,

            retrieve_pos_from='topright',
            assign_pos_to='topleft',
            offset_pos_by=(4, 0),

            intermittent_pos_from='bottomleft',
            intermittent_pos_to='topleft',
            intermittent_offset_by=(0, -2),

        )

        words.rect.topleft = TEXT_BOX.topleft

        word_lines = [

            UIDeque2D(
                chain(*words_in_same_line)
            )

            for _, words_in_same_line
            in groupby(words, key=lambda word: word.rect.top)

        ]

        ###

        self.all_chars_2d = UIList2D()

        self.current_line_2d_deque, *remaining_lines = word_lines
        self.remaining_lines_2d_deque = UIDeque2D(remaining_lines)

        self.append_2d_char = self.all_chars_2d.append
        self.popleft_2d_char = self.current_line_2d_deque.popleft

        self.waiting_for_user_to_advance = False

        self.frames_since_start_of_line = 0

        ###
        self.char_quantity_range = ONE_ITEM_RANGE

        ###
        self.drive_scene_state = self.present_dialogue

    def carry_actions(self):

        try:
            next_calls = self.advance_actions()

        except StopIteration:
            self.after_actions()

        else:

            for call in next_calls:
                call()

    def present_dialogue(self):

        self.frames_since_start_of_line += 1

        if self.waiting_for_user_to_advance: return


        if (
            self.all_chars_2d
            and self.all_chars_2d.rect.bottom >= TEXT_BOX.bottom
        ):

            for collection in (
                self.all_chars_2d,
                self.current_line_2d_deque,
                self.remaining_lines_2d_deque,
            ):
                if collection:
                    collection.rect.move_ip(0, -1)

        ###

        elif self.current_line_2d_deque:

            if NEXT_CHARS():

                append = self.append_2d_char
                popleft = self.popleft_2d_char

                with suppress(IndexError):

                    for _ in self.char_quantity_range:
                        append(popleft())

        elif self.remaining_lines_2d_deque:

            self.current_line_2d_deque.extend(
                self.remaining_lines_2d_deque.popleft()
            )

            if NEXT_CHARS():

                append = self.append_2d_char
                popleft = self.popleft_2d_char

                with suppress(IndexError):

                    for _ in self.char_quantity_range:
                        append(popleft())


        else:

            if 'right' in self.in_game_character.aniplayer.anim_name:

                self.character_portrait.aniplayer.switch_animation(
                    'portrait_idle_right'
                )

                self.in_game_character.aniplayer.switch_animation('idle_right')

            else:

                self.character_portrait.aniplayer.switch_animation(
                    'portrait_idle_left'
                )

                self.in_game_character.aniplayer.switch_animation('idle_left')

            self.waiting_for_user_to_advance = True

    def advance_dialogue_if_possible(self):

        if not self.waiting_for_user_to_advance: return

        if self.frames_since_start_of_line < _WAIT_BEFORE_LINE_ADVANCE_FRAMES:
            return

        self.waiting_for_user_to_advance = False

        actions_after = self.action_map.get((self.current_line, 'after'), ())
        self.process_actions(actions_after)

        if self.action_call_groups:

            self.drive_scene_state = self.carry_actions

            self.advance_actions = (

                zip_longest(
                    *self.action_call_groups,
                    fillvalue=do_nothing,
                ).__next__

            )

            self.after_actions = self.get_next_line

        else:
            self.get_next_line()

    def scene_draw(self):
        """Draw level elements (and dialogue elements when applicable)."""

        SCREEN.fill(self.bg_color)

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
