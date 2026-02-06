"""Facility with class extension for managing dialogues."""

### standard library imports

from itertools import chain, count, groupby, zip_longest, cycle, repeat

from collections import defaultdict, deque

from functools import partial

from math import floor

### standard library import with local import replacement
### in case imported function is not available from
### standard library (since it might not be available in
### the Python version used)

try:
    from itertools import pairwise

except ImportError:
    from ...ourstdlibs.iterutils import pairwise


### third-party imports

from pygame import Rect, Surface

from pygame.locals import (

    QUIT,

    KEYDOWN,
    KEYUP,

    K_ESCAPE,
    K_RETURN,
    K_DOWN,
    K_RIGHT,

    JOYBUTTONDOWN,
    JOYBUTTONUP,

)

from pygame.display import update as update_screen

from pygame.draw import rect as draw_rect, polygon as draw_polygon

from pygame.math import Vector2

### third-party imports with local import replacements
### in case imported functions are not available from
### third-party lib (since it might not be available in
### the pygame version used)

try:
    from pygame.math import lerp, smoothstep

except ImportError:
    from ...ourstdlibs.mathutils import lerp, smoothstep


### local imports

from ...config import DIALOGUE_ACTIONS_DIR, REFS, quit_game

from ...pygamesetup import SERVICES_NS

from ...pygamesetup.constants import (
    SCREEN,
    SCREEN_RECT,
    FPS,
    GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS,
    GAMEPADDIRECTIONALPRESSED,
    msecs_to_frames,
)

from ...pygamesetup.gamepaddirect import GAMEPAD_NS, setup_gamepad_if_existent

from ...classes2d.single import UIObject2D

from ...classes2d.collections import UIList2D, UIDeque2D

from ...textman import render_text

from ...ourstdlibs.pyl import load_pyl

from ...ourstdlibs.behaviour import CallList, do_nothing

from ...userprefsman.main import KEYBOARD_CONTROLS, GAMEPAD_CONTROLS

from ...translatedtext import TRANSLATIONS

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

    update_chunks_and_layers,

)



TEXT_SETTINGS = {
    'style': 'regular',
    'size': 12,
    'padding': 2,
    'foreground_color': 'cyan',
}

_PADDING = 5

BOTTOMLEFT_ANCHOR = SCREEN_RECT.move(_PADDING, -_PADDING).bottomleft
BOTTOMRIGHT_ANCHOR = SCREEN_RECT.move(-_PADDING, -_PADDING).bottomright

PORTRAIT_BOX = Rect(0, 0, 32, 48)


TEXT_BOX = SCREEN_RECT.copy()

TEXT_BOX.height = PORTRAIT_BOX.height
TEXT_BOX.width -= (PORTRAIT_BOX.width + (3 * _PADDING)) 
text_box_colliderect = TEXT_BOX.colliderect


DIALOGUE_BOX = (
    Rect(
        0,
        0,
        SCREEN_RECT.width,
        PORTRAIT_BOX.height + (_PADDING*2),
    )
)

DIALOGUE_BOX.bottom = SCREEN_RECT.bottom


NEXT_CHAR_NORMAL_SPEED = cycle((True, False)).__next__
NEXT_CHAR_FULL_SPEED = repeat(True).__next__

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

class DialogueManagement:
    """Methods to help drive dialogue encounters."""

    def load_dialogues(self):

        self.dialogues_map = dm = {}

        for path in DIALOGUE_ACTIONS_DIR.iterdir():

            if path.suffix.lower() == '.pyl':

                try:
                    data = load_pyl(path)

                except Exception as err:

                    print("Error while trying to load dialogue data")
                    print()
                    raise

                else:

                    lines_data = (
                        get_lines_data(path.stem, data['characters'])
                    )

                    action_map = defaultdict(list)

                    dm[path.stem] = {

                        'lines_data': lines_data,
                        'characters': data['characters'],

                        'action_map': action_map,

                    }

                    ### populate action map

                    cueing_data = (
                        REFS.dialogue_action_cueing_data[path.stem]
                    )

                    for action_id, action_data in data['action_map'].items():

                        cue = cueing_data[action_id]
                        action_map[cue].append(action_data)

        ###

        self.mid_dialogue = False
        self.mid_action = False

        self.remaining_lines_deque = deque()
        self.current_line = ''
        self.current_character = ''

        self.action_steps_deque = deque()

        self.character_portrait_map = {
            'Blue': REFS.blue_boy,
            'Giovanni': REFS.giovanni,
            'Kane': REFS.kane,
        }

        self.character_portrait_map = {
            'Blue': REFS.blue_boy,
            'Giovanni': REFS.giovanni,
            'Kane': REFS.kane,
        }

        self.character_retrieval_map = {
            'Blue': (REFS, ('states', 'level_manager', 'player')),
            'Giovanni': (REFS, ('states', 'level_manager', 'npc')),
            'Kane': (REFS, ('level_boss',)), 
        }

        self.character_map = {}

        self.text_box_obj = (
            UIObject2D.from_surface(Surface(TEXT_BOX.size).convert())
        )
        self.text_box_obj.rect = TEXT_BOX

        text_canvas = self.text_canvas = self.text_box_obj.image
        text_canvas.fill('black')
        self.blit_on_text_canvas = text_canvas.blit

    def enter_dialogue(self, dialogue_name):

        self.disable_overall_tracking_for_camera()
        self.disable_feet_tracking_for_camera()

        self.control = self.dialogue_control
        self.update = self.dialogue_update
        self.draw = self.dialogue_draw

        ###

        data = self.dialogues_map[dialogue_name]

        self.remaining_lines_deque.extend(data['lines_data'])
        self.action_map = data['action_map']

        self.current_line = ''
        self.current_character = ''

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
        ### entering dialogue succeeded
        return True

    def exit_dialogue(self):

        print("Exiting the dialogue")

        self.control = self.control_player
        self.update = self.normal_update
        self.draw = self.draw_level

        self.enable_overall_tracking_for_camera()
        self.enable_feet_tracking_for_camera()

    def dialogue_control(self):
        
        if self.drive_dialogue_state == self.present_dialogue:
            self.process_mid_dialogue_input()

        else:
            self.process_non_dialogue_input()

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
            self.next_char = NEXT_CHAR_FULL_SPEED


        else:
            self.next_char = NEXT_CHAR_NORMAL_SPEED


    def process_non_dialogue_input(self):

        for event in SERVICES_NS.get_events():

            if event.type in GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS:
                setup_gamepad_if_existent()

            elif event.type == QUIT:
                quit_game()

    def dialogue_update(self):

        ### backup scrolling
        scrolling_backup.update(scrolling)

        self.drive_dialogue_state()

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

    def get_next_line(self):

        if self.remaining_lines_deque:

            current_line, line_contents, current_character = (
                self.remaining_lines_deque.popleft()
            )

            self.current_line = current_line
            self.line_contents = line_contents
            self.current_character = current_character

            ###

            self.character_portrait = (
                self.character_portrait_map[current_character]
            )

            self.in_game_character = self.character_map[current_character]

            ###

            actions_before = self.action_map.get((current_line, 'before'), ())

            self.process_actions(actions_before)

            if self.action_call_groups:

                self.drive_dialogue_state = self.carry_actions

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
            self.exit_dialogue()

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

            elif action_type == 'move':

                kwargs = action_data['keyword_arguments']

                character = kwargs['character']

                if character == 'Blue':

                    no_of_frames = self.player.move_on_dialogue(kwargs)
                    all_calls = [do_nothing,] * no_of_frames

                else:

                    raise ValueError(
                        "value of 'character' argument must be one used"
                        " in either of the previous if-elif blocks"
                    )

                self.action_call_groups.append(all_calls)

            elif action_type == 'record_encounter':
                ...
                print("Recorded encounter")


            elif action_type == 'npc_gate_closes':
                self.npc_gate.trigger_closing()

            else:

                raise ValueError(
                    "'action_type' value must be one used"
                    " in either of the previous if-elif blocks"
                )


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
                offset_pos_by=(-2, 0),
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

        self.waiting_for_user_to_advance = False

        ###
        self.next_char = NEXT_CHAR_NORMAL_SPEED

        ###
        self.drive_dialogue_state = self.present_dialogue

    def carry_actions(self):

        try:
            next_calls = self.advance_actions()

        except StopIteration:
            self.after_actions()

        else:

            for call in next_calls:
                call()

    def present_dialogue(self):

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

            if self.next_char():
                self.all_chars_2d.append(self.current_line_2d_deque.popleft())

        elif self.remaining_lines_2d_deque:

            self.current_line_2d_deque = (
                self.remaining_lines_2d_deque.popleft()
            )

            if self.next_char():
                self.all_chars_2d.append(self.current_line_2d_deque.popleft())


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

        self.waiting_for_user_to_advance = False

        actions_after = self.action_map.get((self.current_line, 'after'), ())
        self.process_actions(actions_after)

        if self.action_call_groups:

            self.drive_dialogue_state = self.carry_actions

            self.advance_actions = (

                zip_longest(
                    *self.action_call_groups,
                    fillvalue=do_nothing,
                ).__next__

            )

            self.after_actions = self.get_next_line

        else:
            self.get_next_line()

    def dialogue_draw(self):
        """Draw level elements and dialogue elements on top."""

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

        if self.drive_dialogue_state == self.present_dialogue:
            self.draw_dialogue_elements()

        update_screen()

    def draw_dialogue_elements(self):
        """Draw dialogue elements (as needed).

        "As needed" means that dialogue may have intervals where nothing is
        said, so no dialogue element is drawn during that interval.
        """
        draw_rect(SCREEN, 'black', DIALOGUE_BOX)
        draw_rect(SCREEN, 'orange', DIALOGUE_BOX, 1)

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


def get_lines_data(dialogue_name, character_names):

    t = getattr(TRANSLATIONS, f'{dialogue_name}_dialogue')

    next_index = count().__next__

    lines_data = []

    while True:

        line_attr_name = (
            'line_'
            + str(next_index()).rjust(3, '0')
        )

        try:
            translation_node = getattr(t, line_attr_name)

        except AttributeError:
            break

        for character_name in character_names:

            try:
                line_contents = getattr(translation_node, character_name)
            except AttributeError:
                pass
            else:
                break

        lines_data.append(

            (
                line_attr_name,
                line_contents,
                character_name,
            )

        )

    return lines_data

def get_character_reference(obj, attr_names):

    for attr_name in attr_names:
        obj = getattr(obj, attr_name)

    return obj
