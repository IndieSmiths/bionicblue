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

from .constants import TEXT_BOX



class ScriptedScenePreprocessing:
    """Method(s) to load and preprocess scripted scene data."""

    def load_scripted_scenes(self):

        self.scripted_scene_map = ssm = {}

        for path in SCRIPTED_SCENES_DATA_DIR.iterdir():

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

                    ssm[path.stem] = {

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

        found_character_name = False

        for character_name in character_names:

            try:
                line_contents = getattr(translation_node, character_name)
            except AttributeError:
                pass
            else:
                found_character_name = True
                break

        if not found_character_name:

            ### TODO make it so characters don't need to be mentioned in the
            ### scene data to begin with (after all, we can retrieve the names
            ### from the dialogue itself)

            raise ValueError(
                "A character used in the dialogue wasn't mentioned"
                " on the scene data."
            )

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
