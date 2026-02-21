"""Facility w/ class extension for assisting in loop update operations."""

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
    from ....ourstdlibs.iterutils import pairwise


### third-party imports

from pygame.math import Vector2

from pygame.mixer import music

### third-party imports with local import replacements
### in case imported functions are not available from
### third-party lib (since it might not be available in
### the pygame version used)

try:
    from pygame.math import lerp, smoothstep

except ImportError:
    from ....ourstdlibs.mathutils import lerp, smoothstep


### local imports

from .....config import MUSIC_DIR, SOUND_MAP

from .....pygamesetup.constants import msecs_to_frames

from .....classes2d.single import UIObject2D

from .....classes2d.collections import UIList2D, UIDeque2D

from .....textman import render_text

from .....ourstdlibs.behaviour import CallList, do_nothing

from ...middleprops.largedish import LargeDish

from ...common import (

    scrolling,

    add_obj,
    remove_obj,
    update_chunks_and_layers,

)

from ...taskmanager import append_conditional_task

from ..constants import (

    PORTRAIT_BOX,
    TEXT_BOX,

    BOTTOMLEFT_ANCHOR,
    BOTTOMRIGHT_ANCHOR,
)

from .constants import ONE_ITEM_RANGE



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


class UpdateAssistance:
    """Methods to assist in update operations within loop management."""

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
                                    partial(
                                        move_level_method,
                                        step_deltas.popleft(),
                                    ),
                                    update_chunks_and_layers,
                                ]

                            )
                            if step_deltas[0][0] or step_deltas[0][1]

                            else (
                                partial(
                                    move_level_method,
                                    step_deltas.popleft(),
                                )
                            )

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

            elif action_type == 'set_animation_blend':

                kwargs = action_data['keyword_arguments']

                anim_blend = kwargs['animation_blend']
                target = kwargs['target']

                self.character_map[target].aniplayer.blend(f'+{anim_blend}')

                if not kwargs.get('once', False):
                    self.animation_blend_map[target] = anim_blend

            elif action_type == 'play_music':

                music_filename = (
                    action_data['keyword_arguments']['music_filename']
                )

                music.load(str(MUSIC_DIR / music_filename))
                music.play(-1)

            elif action_type == 'play_sound':

                sound_filename = (
                    action_data['keyword_arguments']['sound_filename']
                )

                SOUND_MAP[sound_filename].play()

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

            ### TODO probably reduce all these record options into
            ### a single record instructions;
            ###
            ### also, for all the recording use same call that records
            ### boss defeat

            elif action_type == 'record_encounter':
                ...
                print("Recorded encounter")

            elif action_type == 'record_intro_talk_with_boss':
                ...
                print("Talked with boss when arrived")

            elif action_type == 'record_parting_talk_with_boss':
                ...
                print("Talked with boss before leaving")

            elif action_type == 'npc_gate_closes':
                self.npc_gate.trigger_closing()

            elif action_type == 'place_food_box':

                food_box_pos = self.food_box_pos + scrolling
                food_box = self.food_box
                food_box.rect.midbottom = food_box_pos

                add_obj(food_box)

                # also add trigger for consuming food box
                self.add_food_box_trigger()

            else:

                raise ValueError(
                    "'action_type' value must be one used"
                    " in either of the previous if-elif blocks"
                )

    def check_line_index(self, line_index):
        return self.line_index == line_index

    def prepare_dialogue_line(self):

        in_game_aniplayer = self.in_game_character.aniplayer
        portrait_aniplayer = self.character_portrait.aniplayer

        ## positioning for dialogue elements depends on direction the
        ## character is facing

        is_character_facing_right = self.is_character_facing_right = (
            'right' in in_game_aniplayer.aniplayer.anim_name
        )

        if is_character_facing_right:

            PORTRAIT_BOX.bottomleft = BOTTOMLEFT_ANCHOR
            TEXT_BOX.bottomright = BOTTOMRIGHT_ANCHOR

            portrait_aniplayer.switch_animation('portrait_speaking_right')
            in_game_aniplayer.aniplayer.switch_animation('speaking_idle_right')

        else:

            TEXT_BOX.bottomleft = BOTTOMLEFT_ANCHOR
            PORTRAIT_BOX.bottomright = BOTTOMRIGHT_ANCHOR

            portrait_aniplayer.switch_animation('portrait_speaking_left')
            in_game_aniplayer.aniplayer.switch_animation('speaking_idle_left')

        if self.current_character in self.animation_blend_map:

            anim_blend = self.animation_blend_map[self.current_character]

            portrait_aniplayer.blend(f'+{anim_blend}')
            in_game_aniplayer.aniplayer.blend(f'+{anim_blend}')

        ###
        self.character_portrait.rect.center = PORTRAIT_BOX.center

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

            portrait_aniplayer = self.character_portrait.aniplayer
            in_game_aniplayer = self.in_game_character.aniplayer

            if 'right' in self.in_game_character.aniplayer.anim_name:

                portrait_aniplayer.switch_animation(
                    'portrait_idle_right'
                )

                in_game_aniplayer.switch_animation('idle_right')

            else:

                portrait_aniplayer.switch_animation(
                    'portrait_idle_left'
                )

                in_game_aniplayer.switch_animation('idle_left')

            if self.current_character in self.animation_blend_map:

                anim_blend = self.animation_blend_map[self.current_character]

                portrait_aniplayer.blend(f'+{anim_blend}')
                in_game_aniplayer.blend(f'+{anim_blend}')

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
