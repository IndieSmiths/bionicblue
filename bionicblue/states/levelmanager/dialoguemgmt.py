"""Facility with class extension for managing dialogues."""

### standard library imports

from itertools import count, groupby

from collections import defaultdict, deque

### standard library import with local import replacement
### in case imported function is not available from
### standard library (since it might not be available in
### the Python version used)

try:
    from itertools import pairwise

except ImportError:
    from ...ourstdlibs.iterutils import pairwise


### third-party imports

from pygame.locals import (

    QUIT,

    KEYDOWN,
    KEYUP,
    K_ESCAPE,
    K_RETURN,

    JOYBUTTONDOWN,
    JOYBUTTONUP,

)

from pygame.display import update as update_screen

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

from ...config import DIALOGUE_ACTIONS_DIR

from ...pygamesetup import SERVICES_NS

from ...pygamesetup.constants import (
    SCREEN,
    GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS,
    msecs_to_frames,
)

from ...pygamesetup.gamepaddirect import GAMEPAD_NS, setup_gamepad_if_existent

from ...classes2d.single import UIObject2D

from ...classes2d.collections import UIList2D

from ...textman import render_text

from ...ourstdlibs.pyl import load_pyl

from ...ourstdlibs.behaviour import do_nothing

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

    execute_tasks,
    update_chunks_and_layers,

)



TEXT_SETTINGS = {
    'style': 'regular',
    'size': 12,
    'padding': 2,
    'foreground_color': 'cyan',
}

CHARACTER_PORTRAIT_BOX = (
    ...
)

TEXTBOX = (
    ...
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

                    line_attr_names = get_line_attr_names(path.stem)

                    action_map = defaultdict(list)

                    dm[path.stem] = {

                        'line_attr_names': line_attr_names,
                        'characters': data['characters'],

                        'action_map': action_map,

                    }

                    ### populate action map

                    for action_data in data['actions']:

                        line_index = action_data.pop('line_index')

                        try:
                            line_attr_name = line_attr_names[line_index]

                        except IndexError as err:

                            raise IndexError(
                                "Used nonexistent line index"
                            ) from err

                        action_map[(
                          line_attr_name,
                          action_data.pop('before_or_after'),
                        )].append(action_data)

        ###

        self.mid_dialogue = False
        self.mid_action = False

        self.remaining_lines_deque = deque()
        self.current_line = ''

        self.action_steps_deque = deque()

    def enter_dialogue(self, dialogue_name):

        self.disable_overall_tracking_for_camera()
        self.disable_feet_tracking_for_camera()

        self.control = self.dialogue_control
        self.update = self.dialogue_update
        self.draw = self.dialogue_draw

        ###

        data = self.dialogues_map[dialogue_name]

        self.characters = data['characters']
        self.remaining_lines_deque.extend(data['line_attr_names'])
        self.action_map = data['action_map']

        self.current_line = ''

        self.get_next_line()

    def exit_dialogue(self):

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
                    self.go_to_next_line_if_possible()

            elif event.type == JOYBUTTONDOWN:

                if event.button in (
                    GAMEPAD_CONTROLS['start_button'],
                    GAMEPAD_CONTROLS['shoot'],
                    GAMEPAD_CONTROLS['jump'],
                ):
                    self.go_to_next_line_if_possible()

            elif event.type == GAMEPADDIRECTIONALPRESSED:

                if event.direction in ('down', 'right'):
                    self.go_to_next_line_if_possible()

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

            or GAMEPAD_NS.get_button[GAMEPAD_CONTROLS['start_button']]
            or GAMEPAD_NS.get_button[GAMEPAD_CONTROLS['shoot']]
            or GAMEPAD_NS.get_button[GAMEPAD_CONTROLS['jump']]

        ):
            self.dialogue_full_speed = True

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

            current_line = self.current_line = (
                self.remaining_lines_deque.popleft()
            )

            actions_before = self.action_map.get((current_line, 'before'))

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
            ... # exit dialogue

    def process_actions(self, action_data):

        self.action_call_groups = []

        for action_data in actions:

            action_type = action_data['type']
            kwargs = action_data['keyword_arguments']

            if action_type == 'pan_camera':

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

                deltas = deque(
                    b - a
                    for a, b in pairwise(points)
                )

                ### create a deque with a call for each frame

                all_calls = deque()
                self.action_call_groups.append(all_calls)

                move_level_method = self.move_level

                _gap_count = 0

                for _ in range(no_of_frames):

                    call = (

                        partial(move_level_method, deltas.popleft())
                        if _gap_count == 0

                        else do_nothing

                    )

                    all_calls.append(call)

                    _gap_count += 1

                    if _gap_count > frames_between_steps:
                        _gap_count = 0

            elif action_type == 'move':

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


    def prepare_dialogue_line(self):

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

            for word in self.current_line.split()

        )

        for word in words:

            word.rect.snap_rects_ip(
                retrieve_pos_from='topright',
                assign_pos_to='topleft',
            )

        words.rect.snap_rects_intermittently_ip(

            dimension_name='width',
            dimension_unit='pixels',
            max_dimension_value=TEXTBOX.width,

            retrieve_pos_from='topright',
            assign_pos_to='topleft',
            offset_pos_by=(2, 0),

            intermittent_pos_from='bottomleft',
            intermittent_pos_to='topleft',
            intermittent_offset_by=(0, 2),

        )

        words.rect.topleft = TEXTBOX.topleft

        word_lines = UIList2D(

            UIList2D(words_with_same_top)

            for _, words_with_same_top
            in groupby(words, key=lambda word: word.rect.top)

        )

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
        ...

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

        self.draw_dialogue_elements()

        update_screen()

    def draw_dialogue_elements(self):
        """Draw dialogue elements (as needed).

        "As needed" means that dialogue may have intervals where nothing is
        said, so no dialogue element is drawn during that interval.
        """


def get_line_attr_names(dialogue_name):

    t = getattr(TRANSLATIONS, f'{dialogue_name}_dialogue')

    next_index = count().__next__

    line_attr_names = []

    while True:

        line_attr_name = (
            'line_'
            + str(next_index()).rjust(3, '0')
        )

        try:
            getattr(t, line_attr_name)

        except AttributeError:
            break

        line_attr_names.append(line_attr_name)

    return line_attr_names
