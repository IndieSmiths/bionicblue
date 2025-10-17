"""Facility to present media (text, images, sprites) to convey information."""

### standard library imports
from collections import defaultdict, deque


### third-party imports

from pygame.display import update


### local imports

from ..config import PRESENTATIONS_DIR

from ..ourstdlibs.pyl import load_pyl

from ..userprefsman.main import USER_PREFS



class MediaPresenter:
    """Presents text, images, sprites.

    Pace is controlled by user, which can skip as well.
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

        self.presentation_map = defaultdict(dict)

        self.presentation_sections_deque = deque()

    def prepare(self, presentation_key):
        """Prepare objects for given presentation.

        Or reuse, if previously created."""

        ### grab current locale
        locale = USER_PREFS['LOCALE']

        ### if requested presentation wasn't created for the current locale,
        ### do so

        if locale not in self.presentation_map[presentation_key]:
            self.create_presentation(presentation_key, locale)

        ### now store presentation sections in the deque

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

            ### TODO write this part

            ### populate it according to section data

            presentation_sections.append(section)


        ### finally store the presentation
        self.presentation_map[presentation_key][locale] = presentation


    def control(self):
        """Let user jump to next piece of content, speed up or skip content."""

    def update(self):

    def draw(self):
        SCREEN.fill(self.bg_color)
        update()
