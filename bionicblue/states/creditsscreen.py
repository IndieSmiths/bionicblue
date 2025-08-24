"""Facility for credits screen."""

### standard library import
from webbrowser import open as open_url


### third-party imports

from pygame.locals import (

    QUIT,
    KEYDOWN,
    K_ESCAPE,
    K_UP, K_DOWN,
    K_RETURN,
    JOYBUTTONDOWN,
    MOUSEMOTION,
    MOUSEBUTTONDOWN,
)

from pygame.display import update

from pygame.draw import rect as draw_rect


### local imports

from ..config import REFS, CREDITS_FILEPATH, LoopException, quit_game

from ..pygamesetup import SERVICES_NS

from ..pygamesetup.constants import (
    SCREEN,
    SCREEN_RECT,
    BLACK_BG,
    GAMEPADDIRECTIONALPRESSED,
    GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS,
    blit_on_screen,
)

from ..pygamesetup.gamepaddirect import setup_gamepad_if_existent

from ..classes2d.single import UIObject2D

from ..classes2d.collections import UIList2D

from ..textman import render_text



LABEL_TEXT_SETTINGS = {
    'style': 'regular',
    'size': 12,
    'padding': 1,
    'foreground_color': 'white',
    'background_color': 'black',
}

LINK_TEXT_SETTINGS = {
    'style': 'regular',
    'size': 12,
    'padding': 1,
    'foreground_color': 'cyan',
    'background_color': 'black',
}

TITLE_TEXT_SETTINGS = {
    'style': 'regular',
    'size': 16,
    'padding': 1,
    'foreground_color': 'white',
    'background_color': 'black',
}

def get_text_url_pair(link_text):
    """Return 2-tuple with text and url from given link.

    >>> get_text_url_pair('[text](link)')
    ('text', 'link')

    >>> get_text_url_pair('  [text](link)')
    ('text', 'link')
    """

    (
      text_start,
      text_end,
      link_start,
      link_end,
    ) = (
      
      link_text.index(char) + increment

      for char, increment in (
        ('[', 1),
        (']', 0),
        ('(', 1),
        (')', 0),
      )

    )

    return link_text[text_start:text_end], link_text[link_start:link_end]



class CreditsScreen:

    def __init__(self):

        lines = CREDITS_FILEPATH.read_text(encoding='utf-8').splitlines()

        caption = self.caption = (
            UIObject2D.from_surface(
                render_text(
                    "Credits",
                    **TITLE_TEXT_SETTINGS,
                )
            )
        )

        caption.rect.midtop = SCREEN_RECT.move(0, 5).midtop

        y = caption.rect.bottom + 10

        items = self.items = UIList2D()
        items.append(caption)

        for line in lines:

            if not line:

                y += 10

                continue

            space_count = 0

            first_non_space_char = ''

            for char in line:

                if char == ' ':
                    space_count += 1
                else:
                    first_non_space_char = char
                    break

            x = 5 + (space_count * 6)

            if first_non_space_char == '[':

                text, url = get_text_url_pair(line)

                obj = (
                    UIObject2D.from_surface(
                        render_text(
                            text,
                            **LINK_TEXT_SETTINGS,
                        )
                    )
                )

                obj.url = url

            else:

                text = line.strip()

                obj = (
                    UIObject2D.from_surface(
                        render_text(
                            text,
                            **LABEL_TEXT_SETTINGS,
                        )
                    )
                )

            obj.rect.topleft = (x, y)
            items.append(obj)

            y = obj.rect.bottom + 3

        self.links = [
            obj
            for obj in items
            if hasattr(obj, 'url')
        ]

        self.link_count = len(self.links)

    def prepare(self):

        self.current_index = 0
        self.highlighted_widget = self.links[self.current_index]
        self.align_link()

    def align_link(self):

        centery = self.highlighted_widget.rect.centery
        screen_centery = SCREEN_RECT.centery

        y_diff = screen_centery - centery
        self.items.rect.move_ip(0, y_diff)

    def control(self):
        
        for event in SERVICES_NS.get_events():

            if event.type == KEYDOWN:

                if event.key == K_ESCAPE:
                    self.go_back()

                elif event.key in (K_UP, K_DOWN):

                    increment = -1 if event.key == K_UP else 1

                    self.current_index = (
                        (self.current_index + increment)
                        % self.link_count
                    )

                    self.highlighted_widget = (
                        self.links[self.current_index]
                    )

                    self.align_link()

                elif event.key == K_RETURN:

                    hw = self.highlighted_widget
                    open_url(hw.url)

            elif event.type == JOYBUTTONDOWN:

                if event.button == GAMEPAD_CONTROLS['start_button']:

                    hw = self.highlighted_widget
                    open_url(hw.url)

            elif event.type == GAMEPADDIRECTIONALPRESSED:

                if event.direction in ('up', 'down'):

                    increment = -1 if event.direction == 'up' else 1

                    self.current_index = (
                        (self.current_index + increment)
                        % self.link_count
                    )

                    self.highlighted_widget = (
                        self.links[self.current_index]
                    )

                    self.align_link()

            elif event.type == MOUSEBUTTONDOWN:

                if event.button == 1:
                    self.on_mouse_click(event)

            elif event.type == MOUSEMOTION:
                self.highlight_under_mouse(event)

            elif event.type in GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS:
                setup_gamepad_if_existent()

            elif event.type == QUIT:
                quit_game()

    def go_back(self):

        main_menu = REFS.states.main_menu
        main_menu.prepare()

        raise LoopException(next_state=main_menu)

    def to_playtesters_screen(self):

        playtesters_screen = REFS.states.playtesters_screen 
        playtesters_screen.prepare()

        raise LoopException(next_state=playtesters_screen)

    def on_mouse_click(self, event):

        pos = event.pos

        for index, obj in enumerate(self.links):

            if obj.rect.collidepoint(pos):

                self.current_index = index
                self.highlighted_widget = obj
                open_url(obj.url)

                break

    def highlight_under_mouse(self, event):

        pos = event.pos

        for index, obj in enumerate(self.links):

            if obj.rect.collidepoint(pos):

                self.current_index = index
                self.highlighted_widget = obj

                break

    def update(self): pass
        
    def draw(self):

        blit_on_screen(BLACK_BG, (0, 0))

        self.caption.draw()

        self.items.draw()

        draw_rect(
            SCREEN,
            'orange',
            self.highlighted_widget.rect,
            1,
        )

        update()
