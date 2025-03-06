
### local imports
from itertools import repeat, chain


### third-party imports

from pygame.locals import QUIT

from pygame.display import update


### local imports

from ..config import REFS, SURF_MAP, COLORKEY, quit_game

from ..pygamesetup import SERVICES_NS

from ..pygamesetup.constants import WHITE_BG, SCREEN_RECT, blit_on_screen

from ..textman import render_text

from ..surfsman import combine_surfaces

from ..exceptions import SwitchStateException



class LogoScreen:

    def prepare(self):

        surfs = tuple(

            combine_surfaces(
                [
                    render_text(text, 'regular', 12, 0, 'black', COLORKEY),
                    SURF_MAP[key],
                ],
                retrieve_pos_from = 'midtop',
                assign_pos_to = 'midbottom',
                offset_pos_by = (0, -4),
                background_color = COLORKEY,
            )

            for key, text in (
                ('indiesmiths_logo.png', "The Indie Smiths project"),
                ('kennedy_logo.png', "A game by Kennedy R. S. Guerra"),
                ('python_logo.png', "Powered by Python"),
                ('pygame_logo.png', "Powered by pygame-ce"),
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

            if event.type == QUIT:
                quit_game()

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

            title_screen = REFS.states.title_screen
            title_screen.prepare()
            raise SwitchStateException(title_screen)

        update()
