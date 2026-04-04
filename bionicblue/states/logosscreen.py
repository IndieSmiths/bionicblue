"""Facility for screen where relevant logos and icons are presented."""

### local imports
from itertools import repeat, chain


### third-party imports

from pygame.locals import (

    QUIT,

    KEYDOWN,
    K_RETURN,

    JOYBUTTONDOWN,

)


### local imports

from ..config import REFS, SURF_MAP, COLORKEY, LoopException, quit_game

from ..pygamesetup import SERVICES_NS

from ..pygamesetup.gamepadservices import GAMEPAD_NS

from ..pygamesetup.constants import (
    WHITE_BG,
    SCREEN_RECT,
    GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS,
    blit_on_screen,
)

from ..textman import render_text

from ..surfsman import combine_surfaces

from ..translatedtext import TRANSLATIONS



captions = TRANSLATIONS.logos_screen.captions

class LogosScreen:
    """Presents relevant logos and icons.

    Used before presenting the title screen and main menu to players.
    Can be skipped.
    """

    def prepare(self):

        surfs = tuple(

            combine_surfaces(

                [

                    render_text(
                        getattr(captions, attr_name),
                        'regular', 12, 0, 'black', COLORKEY,
                    ),

                    SURF_MAP[key],

                ],

                retrieve_pos_from = 'midtop',
                assign_pos_to = 'midbottom',
                offset_pos_by = (0, -4),
                background_color = COLORKEY,

            )

            for key, attr_name in (
                ('indiesmiths_logo.png', 'indiesmiths'),
                ('kennedy_logo.png', 'kennedy'),
                ('python_logo.png', 'python'),
                ('pygame_logo.png', 'pygame_ce'),
                ('no_ai.png', 'no_ai'),
            )

        )

        rmap = self.rect_map = {}

        for surf in surfs:

            surf.set_colorkey(COLORKEY)

            rect = surf.get_rect()
            rect.center = SCREEN_RECT.center
            rmap[surf] = rect

#        self.get_next_surf = iter(range(0)).__next__

        self.get_next_surf = chain.from_iterable(

            repeat(surf, 70)
            for surf in surfs

        ).__next__

    def control(self):

        for event in SERVICES_NS.get_events():

            if event.type == KEYDOWN:

                if event.key == K_RETURN:
                    self.leave_logos_screen()

            elif event.type == JOYBUTTONDOWN:

                if event.button == GAMEPAD_CONTROLS['start_button']:
                    self.leave_logos_screen()

            elif event.type in GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS:
                GAMEPAD_NS.setup_gamepad_if_existent()

            elif event.type == QUIT:
                quit_game()

    def leave_logos_screen(self):

        title_screen = REFS.states.title_screen
        title_screen.prepare()

        raise LoopException(next_state=title_screen)

    def update(self):
        pass

    def draw(self):

        blit_on_screen(WHITE_BG, (0, 0))

        try:

            surf = self.get_next_surf()

            rect_or_pos = (
                self.rect_map[surf]
                if surf in self.rect_map
                else (0, 0)
            )

            blit_on_screen(surf, rect_or_pos)

        except StopIteration:
            self.leave_logos_screen()

        SERVICES_NS.update_screen()
