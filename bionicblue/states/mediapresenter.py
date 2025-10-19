"""Facility to present media to convey information.

Media is comprised of text, images and animations.
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

from ..userprefsman.main import USER_PREFS



### module level objects

SCREEN_TOP_HALF = SCREEN_RECT.copy()
SCREEN_TOP_HALF.height //= 2

SCREEN_BOTTOM_HALF = SCREEN_TOP_HALF.move(0, SCREEN_TOP_HALF.height)


### class definition

class MediaPresenter:
    """Presents text, images and animations.

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
            self.presentation_map[presentation_key][locale]
        )

    def create_presentation(self, presentation_key, locale):

        ### grab data
        data = self.data_map[presentation_key]

        ### instantiate presentation
        presentation_sections = []


        ### populate it according to data

        for section_data in data:

            ### create section
            section = {}

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

                position_obj(image_obj, loaded_image_data['end_pos'])
                end_topleft = image_obj.rect.topleft

                position_obj(image_obj, loaded_image_data['start_pos'])
                start_topleft = image_obj.rect.topleft

                image_data['end_topleft'] = end_topleft
                image_data['start_topleft'] = start_topleft

                start_topleft_v = Vector2(start_topleft)

                steps = [

                    tuple(

                        start_topleft_v.lerp(
                            end_topleft, # destination (end position)
                            i/30,        # percentage to travel from start to end
                        )

                    )

                    for i in range(30)

                ]

                steps.append(end_topleft)

                image_data['topleft_steps'] = steps

            ## animations
            ...

            ## sound
            ...

            ## music
            ...

            ### finally store section
            presentation_sections.append(section)


        ### finally store the presentation
        self.presentation_map[presentation_key][locale] = presentation

    def create_textual_elements(self, presentation_key, locale):
        ...

    def reset_presentation_elements(self):
        ...

    def control(self):
        """Let user speed up presentation or skip altogether."""

    def update(self):

    def draw(self):

        SCREEN.fill(self.bg_color)
        update()


### utility functions

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
