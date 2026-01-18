"""Facility with class extension for managing dialogues."""

### standard library imports

from itertools import count

from collections import deque


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

### third-party import with local import replacement
### in case it is not available from third-party lib
### (since it is a relatively new addition)

try:
    from pygame.math import smoothstep

except ImportError:
    from ...ourstdlibs.mathutils import smoothstep


### local imports

from ...config import DIALOGUE_ACTIONS_DIR

from ...pygamesetup import SERVICES_NS

from ...pygamesetup.constants import (
    SCREEN,
    GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS,
)

from ...pygamesetup.gamepaddirect import GAMEPAD_NS, setup_gamepad_if_existent

from ...ourstdlibs.pyl import load_pyl

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

                    actions = data['actions']

                    for action_data in actions:

                        index = action_data.pop('line_index')

                        try:
                            line_attr_name = line_attr_names[index]

                        except IndexError as err:
                            raise IndexError("Used nonexistent index") from err

                        action_data['line_attr_name'] = line_attr_name

                    dm[path.stem] = {

                        'line_attr_names': line_attr_names,
                        'characters': data['characters'],

                        'action_map': {

                            (
                              action_data.pop('line_attr_name'),
                              action_data.pop('before_or_after'),
                            ): action_data

                            for action_data in actions
                        }

                    }

        ###

        self.mid_dialogue = False
        self.mid_action = False

        self.remaining_lines_deque = deque()
        self.next_line = ''

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

        self.next_line = ''

        self.drive_dialogue_state = self.get_next_line

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

            or GAMEPAD_NS.get_button[GAMEPAD_CONTROLS['start_button']],
            or GAMEPAD_NS.get_button[GAMEPAD_CONTROLS['shoot']],
            or GAMEPAD_NS.get_button[GAMEPAD_CONTROLS['jump']],

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

        self.advance_dialogue_state()

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

    def update_actions(self):
        """Drive dialogue lines and actions until dialogue is exited."""

        if self.mid_dialogue:
            pass

        elif self.mid_action:
            pass

        elif self.next_line:
            pass

    def get_next_line(self):

        if self.remaining_lines_deque:

            next_line = self.next_line = self.remaining_lines_deque.popleft()

            action_before = self.action_map.get((next_line, 'before'))

            if action_before:

                self.prepare_action(action_before)
                self.drive_dialogue_state = self.carry_action

            else:
                self.drive_dialogue_state = self.present_dialogue

        else:
            ... # exit dialogue

    def prepare_action(self, action_data):

        action_description = action_data['description']
        action_type = action_description['type']

        if action_type == 'pan_camera':
            
            current_x, current_y = scrolling

            delta_x, delta_y = (
                action_description.get('delta_x', 0),
                action_description.get('delta_y', 0),
            )

            final_x, final_y = (
                current_x + _delta_x,
                current_y + _delta_y,
            )

            ...

    def carry_action(self):
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

        self.draw_dialogue_elements(self)

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

        except KeyError:
            break

        line_attr_names.append(line_attr_name)

    return line_attr_names
