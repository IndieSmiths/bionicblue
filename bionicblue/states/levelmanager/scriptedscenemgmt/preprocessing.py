"""Facility with class extension for managing dialogues."""

### standard library imports

from itertools import count

from collections import defaultdict, deque


### third-party import
from pygame import Surface


### local imports

from ....config import SCRIPTED_SCENES_DATA_DIR, REFS

from ....classes2d.single import UIObject2D

from ....ourstdlibs.pyl import load_pyl

from ....translatedtext import TRANSLATIONS

from ....userprefsman.main import USER_PREFS

from .constants import TEXT_BOX



class ScriptedScenePreprocessing:
    """Method(s) to load and preprocess scripted scene data."""

    def load_scripted_scenes(self):

        self.scripted_scene_map = ssm = {}

        locale = USER_PREFS['LOCALE']

        self.locales_of_retrieved_lines = [locale]

        for path in SCRIPTED_SCENES_DATA_DIR.iterdir():

            if path.suffix.lower() == '.pyl':

                try:
                    data = load_pyl(path)

                except Exception as err:

                    print("Error while trying to load dialogue data")
                    print()
                    raise

                else:

                    dialogue_names = data.get('dialogue_names', [path.stem])

                    for dialogue_name in dialogue_names:

                        character_names = (
                            REFS
                            .dialogue_character_names_set_map[dialogue_name]
                        )

                        lines_data = (
                            get_lines_data(dialogue_name, character_names)
                        )

                        ### create and populate action map

                        action_map = defaultdict(list)

                        cueing_data = (
                            REFS.dialogue_action_cueing_data[dialogue_name]
                        )

                        for action_id, action_data in (
                            data['action_map'].items()
                        ):

                            cue = cueing_data[action_id]
                            action_map[cue].append(action_data)

                        ### store everything

                        ssm[dialogue_name] = {

                            'characters': character_names,
                            'lines_data': {
                                locale: lines_data,
                            },
                            'action_map': action_map,

                        }

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
            'Newton': REFS.newton_portrait,
        }

        self.character_retrieval_map = {
            'Blue': (REFS, ('states', 'level_manager', 'player')),
            'Giovanni': (REFS, ('states', 'level_manager', 'npc')),
            'Kane': (REFS, ('level_boss',)), 
            'Newton': (REFS, ('newton',)), 
        }

        self.animation_blend_map = {}

        self.character_map = {}

        self.text_box_obj = (
            UIObject2D.from_surface(Surface(TEXT_BOX.size).convert())
        )
        self.text_box_obj.rect = TEXT_BOX

        text_canvas = self.text_canvas = self.text_box_obj.image
        text_canvas.fill('black')
        self.blit_on_text_canvas = text_canvas.blit

    def update_lines_data_for_current_locale_if_needed(self):

        locale = USER_PREFS['LOCALE']

        if locale in self.locales_of_retrieved_lines:
            return

        another_locale = self.locales_of_retrieved_lines[0]

        for dialogue_name, dialogue_data in self.scripted_scene_map.items():

            lines_data_from_another_locale = (
                dialogue_data['lines_data'][another_locale]
            )

            t = getattr(TRANSLATIONS, f'{dialogue_name}_dialogue')

            lines_data_from_current_locale = [

                (

                    line_attr_name,

                    getattr(
                        getattr(t, line_attr_name),
                        character_name,
                    ),

                    character_name,
                    line_index,
                )

                for (
                    line_attr_name,
                    line_contents,
                    character_name,
                    line_index,
                ) in lines_data_from_another_locale

            ]

            dialogue_data['lines_data'][locale] = (
                lines_data_from_current_locale
            )

        self.locales_of_retrieved_lines.append(locale)

### helper function

def get_lines_data(dialogue_name, character_names):

    t = getattr(TRANSLATIONS, f'{dialogue_name}_dialogue')

    lines_data = []

    for line_index in count():

        line_attr_name = (
            'line_'
            + str(line_index).rjust(3, '0')
        )

        try:
            translation_node = getattr(t, line_attr_name)

        except AttributeError:
            break

        ###

        for character_name in character_names:

            try:
                line_contents = getattr(translation_node, character_name)

            except AttributeError:
                pass

            else:
                break

        ###

        lines_data.append(

            (
                line_attr_name,
                line_contents,
                character_name,
                line_index,
            )

        )

    return lines_data
