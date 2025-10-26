"""Facility to present media to convey information.

Media is comprised of text, images and animated sprites.
"""

### standard library imports
from collections import defaultdict, deque


### third-party imports

from pygame.math import Vector2

from pygame.display import update


### local imports

from ..config import (
    PRESENTATIONS_DIR,
    SURF_MAP,
    SOUND_MAP,
)

from ..pygamesetups.constants import SCREEN_RECT

from ..ourstdlibs.pyl import load_pyl

from ..classes2d.single import UIObject2D

from ..classes2d.collections import UIList2D

from ..ani2d.player import AnimationPlayer2D

from ..userprefsman.main import USER_PREFS



### module level objects

SCREEN_TOP_HALF = SCREEN_RECT.copy()
SCREEN_TOP_HALF.height //= 2

SCREEN_BOTTOM_HALF = SCREEN_TOP_HALF.move(0, SCREEN_TOP_HALF.height)

##

TEXT_SETTINGS = {
    'style': 'regular',
    'size': 12,
    'padding': 0,
    'foreground_color': 'white',
    'background_color': 'black',
}


### class definition

class MediaPresenter:
    """Presents text, images and animated sprites.

    Ideally, user will be able to speed up or skip presentation altogether,
    just like usually in dialogue sections in games in general.
    """

    def __init__(self):

        dm = self.data_map = {}

        for path in PRESENTATIONS_DIR.iterdir():

            if path.suffix.lower() == '.pyl':

                try:
                    data = load_pyl(path)

                except Exception as err:

                    print("Error while trying to load presentation")
                    print()
                    raise

                else:
                    dm[path.stem] = data

        ### TODO
        ###
        ### load all visual, sound and music elements here, plus
        ### textual elements for current locale;
        ###
        ### then, create function to build textual elements (if not
        ### built already) for new locale/language selected by user

        ### map for all presentation elements
        self.presentation_map = defaultdict(dict)

        ### map for textual elements, since they are dependent on the
        ### locale/language
        self.textual_presentation_map = defaultdict(dict)

        ### grab current locale
        locale = USER_PREFS['LOCALE']

        ### create presentation elements for all presentations (using current
        ### locale/language, for textual elements)

        for presentation_key in dm:
            self.create_presentation(presentation_key, locale)

        ### deque to hold and deliver sections during presentation
        self.presentation_sections_deque = deque()

        ### store method to update text surfaces when language changes
        on_language_change.append(self.on_language_change)

    def on_language_change(self):
        """Rebuild textual elements (if needed) and set them up for usage."""

        ### grab current locale
        locale = USER_PREFS['LOCALE']

        ### if textual elements were not built for it, do so

        if locale not in self.textual_presentation_map[presentation_key]:
            self.create_textual_elements(presentation_key, locale)

        ### set textual elements for usage
        ...

    def prepare(self, presentation_key):
        """Prepare objects for given presentation."""
        ### reset presentation elements
        self.reset_presentation_elements()

        ### store presentation sections in the deque

        self.presentation_sections_deque.extend(
            self.presentation_map[presentation_key]
        )

    def create_presentation(self, presentation_key, locale):
        """Create presentation elements, using given locale for text."""

        ### grab data
        data = self.data_map[presentation_key]

        ### instantiate presentation
        presentation_sections = []


        ### populate it according to data

        for section_data in data:

            ### create section
            section = {}

            ### append it to sections
            presentation_sections.append(section)

            ### populate it according to section data

            ## images

            processed_images_data = section['images'] = {}

            for loaded_image_data in section_data.get('images', ()):

                ###
                image_name = loaded_image_data['name']

                ###
                image_data = processed_images_data[image_name] = {}

                ###

                image_obj = (

                    UIObject2D.from_surface(
                        SURF_MAP[image_name]
                    )

                )

                image_data['obj'] = image_obj

                ###
                process_position_data(image_obj, loaded_image_data, image_data)


            ## animated sprites

            processed_anisprites_data = section['animated_sprites'] = {}

            for loaded_anisprite_data in (
                section_data.get('animated_sprites', ())
            ):

                ###

                anisprite_name = loaded_anisprite_data['name']

                anisprite_id_str = (

                    loaded_anisprite_data.get(
                        'id_str',
                        anisprite_name,
                    )

                )

                ###
                anisprite_data = processed_anisprites_data[anisprite_id_str] = {}

                ###
                
                anisprite_obj = UIObject2D()
                anisprite_obj.ap = (
                    AnimationPlayer2D(anisprite_obj, anim_data_name, anim_name)
                )

                anisprite_data['obj'] = anisprite_obj

                ###

                process_position_data(
                    anisprite_obj,
                    loaded_anisprite_data,
                    anisprite_data,
                )

            ## sound


            processed_sounds_data = section['sounds'] = {}

            for loaded_sound_data in section_data.get('sounds', ()):

                ###
                sound_name = loaded_sound_data['name']

                ###
                sound_data = processed_soundss_data[sound_name] = {}

                ###
                sound_obj = SOUND_MAP[sound_name]

                sound_data['sound'] = sound_obj

                ### TODO
                ### must think of ways to time triggering sound; possibilities:
                ###
                ### - at beginning of section
                ### - at end of section
                ### - on elapsed time starting from beginning of section
                ### - on animation pose
                ### - on image positioning step
                ### - on animation positioning step


            ## music

            processed_music_data = section['music'] = {}

            for loaded_music_data in section_data.get('music', ()):

                ###
                music_name = loaded_music_data['name']

                ###
                music_data = processed_music_data[music_name] = {}

                ###
                music_data['name'] = music_name

                ### TODO
                ###
                ### like sound, must think of ways to time triggering music


            ### finally store section
            presentation_sections.append(section)

        ### store the presentation
        self.presentation_map[presentation_key] = presentation_sections

        ### create textual elements
        self.create_textual_elements(presentation_key, locale)

    def create_textual_elements(self, presentation_key, locale):
        """Create textual elements of presentation."""

        presentation_sections = self.presentation_map[presentation_key]

        textual_presentation = self.textual_presentation_map[presentation_key]

        data = self.data_map[presentation_key]

        for section_data, section in zip(data, presentation_sections):
            
            processed_text_data = section['text'] = {}
            text = section_data['text']

            words = UIList2D(

                UIObject2D.from_surface(
                    render_text(word, **TEXT_SETTINGS)
                )

                for word in body_text.split()

            )

            words.rect.snap_rects_intermittently_ip(

                ### interval limit

                dimension_name='width', # either 'width' or 'height'
                dimension_unit='pixels', # either 'rects' or 'pixels'
                max_dimension_value=SCREEN_RECT.width - 20, # positive integer

                ### rect positioning

                retrieve_pos_from='topright',
                assign_pos_to='topleft',
                offset_pos_by=(5, 0),

                ### intermittent rect positioning

                intermittent_pos_from='bottomleft',
                intermittent_pos_to='topleft',
                intermittent_offset_by=(0, 2),

            )

            word_deque = deque(words)

            lines_deque = deque()

            while word_deque:
                
                line = UIList2D()

                top = word_deque[0].rect.top

                while word_deque and word_deque[0].rect.top = top:
                    line.append(word_deque.popleft())

                lines_deque.append(line)


    def reset_presentation_elements(self):
        ...

    def control(self):
        """Let user speed up presentation or skip altogether."""

    def update(self):

    def draw(self):

        SCREEN.fill(self.bg_color)
        update()


### utility functions

def process_position_data(obj, loaded_data, data)

    position_obj(obj, loaded_data['end_pos'])
    end_topleft = obj.rect.topleft

    position_obj(obj, loaded_data['start_pos'])
    start_topleft = obj.rect.topleft

    data['end_topleft'] = end_topleft
    data['start_topleft'] = start_topleft

    start_topleft_v = Vector2(start_topleft)

    steps = [

        tuple(

            start_topleft_v.lerp(
                end_topleft, # destination (end position)
                i/30,        # percentage to travel
            )

        )

        for i in range(30)

    ]

    steps.append(end_topleft)

    data['topleft_steps'] = steps


def position_obj(obj, pos_data):

    (
        rect_attr_name,
        screen_top_half_rect_attr_name,
        offset,
    ) = pos_data

    setattr(

        obj.rect,

        rect_attr_name,

        getattr(
            SCREEN_TOP_HALF.rect,
            screen_top_half_rect_attr_name,
        ) + Vector2(offset)

    )
