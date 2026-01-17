"""Facility with class extension for managing dialogues."""

### standard library imports

from itertools import count

from collections import deque


### third-party imports

from pygame.display import update as update_screen


### local imports

from ...config import DIALOGUE_ACTIONS_DIR

from ...pygamesetup.constants import SCREEN

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

                    for action_data in data['actions']:

                        index = action_data.pop('line_index')

                        try:
                            line_attr_name = line_attr_names[index]

                        except IndexError as err:
                            raise IndexError("Used nonexistent index") from err

                        action_data['line_attr_name'] = line_attr_name

                    dm[path.stem] = {
                        'line_attr_names': line_attr_names,
                        **data,
                    }

        ###

        self.remaining_lines_deque = deque()
        self.next_line = ''

    def enter_dialogue(self, dialogue_name):

        self.disable_overall_tracking_for_camera()
        self.disable_feet_tracking_for_camera()

        self.control = self.dialogue_control
        self.update = self.dialogue_update
        self.draw = self.dialogue_draw

        ###

        data = self.dialogues_map[dialogue_name]
        self.remaining_lines_deque.extend(data['line_attr_names'])
        self.next_line = ''

    def exit_dialogue(self):

        self.control = self.control_player
        self.update = self.normal_update
        self.draw = self.draw_level

        self.enable_overall_tracking_for_camera()
        self.enable_feet_tracking_for_camera()

    def dialogue_control(self):
        ...

    def dialogue_update(self):

        self.player.update()

        ### backup scrolling
        scrolling_backup.update(scrolling)

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

        self.update_actions()

    def update_actions(self):
        """Drive dialogue lines and actions until dialogue is exited."""

        if self.mid_dialogue:
            pass

        elif self.mid_action:
            pass

        elif not self.next_line:

            if not self.remaining_lines_deque:
                ... # exit dialogue

            else:
                self.next_line = self.remaining_lines_deque.popleft()

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
