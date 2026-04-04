"""Facility for links screen."""

### standard library imports

from webbrowser import open as open_url

from urllib.parse import urlparse


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

from pygame.draw import rect as draw_rect


### local imports

from ..config import (
    REFS,
    LINKS_FILEPATH,
    SURF_MAP,
    LoopException,
    quit_game,
)

from ..pygamesetup import SERVICES_NS

from ..pygamesetup.constants import (
    SCREEN,
    SCREEN_RECT,
    BLACK_BG,
    GAMEPADDIRECTIONALPRESSED,
    GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS,
    blit_on_screen,
)

from ..pygamesetup.gamepadservices import GAMEPAD_NS

from ..classes2d.single import UIObject2D

from ..classes2d.collections import UIList2D

from ..textman import render_text, update_text_surface

from ..translatedtext import TRANSLATIONS, on_language_change



LABEL_TEXT_SETTINGS = {
    'style': 'regular',
    'size': 12,
    'padding': 1,
    'foreground_color': 'white',
    'background_color': 'black',
}

LINK_TEXT_SETTINGS_0 = {
    'style': 'regular',
    'size': 12,
    'padding': 1,
    'foreground_color': 'cyan',
    'background_color': 'black',
}

LINK_TEXT_SETTINGS_1 = {
    'style': 'regular',
    'size': 12,
    'padding': 2,
    'foreground_color': 'white',
    'background_color': 'blue',
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

t = TRANSLATIONS.links_screen

NETLOC_TO_ICON_NAME_MAP = {

    'bsky.app': 'bluesky_icon.png',
    'github.com': 'github_icon.png',
    'ko-fi.com': 'kofi_icon.png',
    'patreon.com': 'patreon_icon.png',
    'x.com': 'xtwitter_icon.png',
    'youtube.com': 'youtube_icon.png',
    'discord.gg': 'discord_icon.png',

    # otherwise: 'domain_icon.png'

}



class LinksScreen:

    def __init__(self):

        caption = self.caption = (
            UIObject2D.from_surface(
                render_text(
                    t.caption,
                    **TITLE_TEXT_SETTINGS,
                )
            )
        )

        caption.rect.midtop = SCREEN_RECT.move(0, 5).midtop

        y = caption.rect.bottom + 10

        items = self.items = UIList2D()
        items.append(caption)

        lines = LINKS_FILEPATH.read_text(encoding='utf-8').splitlines()

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

            indentation_level = space_count // 4

            x = 5 + (indentation_level * 36)

            if first_non_space_char == '[':

                text, url = get_text_url_pair(line)

                if text[0] == '{' and text[-1] == '}':

                    translation_key = text[1:-1]
                    text = getattr(t, translation_key)

                else:
                    translation_key = ''

                obj = (
                    UIObject2D.from_surface(
                        render_text(
                            text,
                            **LINK_TEXT_SETTINGS_0,
                        ),
                        url = url,
                        translation_key = translation_key,
                    )
                )

            else:

                text = line.strip()

                if text[0] == '{' and text[-1] == '}':

                    translation_key = text[1:-1]
                    text = getattr(t, translation_key)

                else:
                    translation_key = ''

                obj = (
                    UIObject2D.from_surface(
                        render_text(
                            text,
                            **LABEL_TEXT_SETTINGS,
                        ),
                        translation_key = translation_key,
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

        ###

        self.url_to_netloc_map = url_to_netloc_map = {
            link.url: urlparse(link.url).netloc
            for link in self.links
        }

        self.netloc_to_text_obj_map = {

            netloc: (
                UIObject2D.from_surface(
                    render_text(
                        t.open_link.format(netloc=netloc),
                        **LINK_TEXT_SETTINGS_1,
                    )
                )
            )

            for netloc in set(self.url_to_netloc_map.values())

        }

        for obj in self.netloc_to_text_obj_map.values():
            obj.rect.bottomright = SCREEN_RECT.bottomright

        ###

        link_icons = self.link_icons = UIList2D()

        for link in self.links:

            netloc = url_to_netloc_map[link.url]
            icon_name = NETLOC_TO_ICON_NAME_MAP.get(netloc, 'domain_icon.png')

            icon_obj = UIObject2D.from_surface(SURF_MAP[icon_name])
            icon_obj.rect.midright = link.rect.move(-5, 0).midleft

            link_icons.append(icon_obj)

        ### store method to be called when language changes
        on_language_change.append(self.on_language_change)

    def prepare(self):

        self.current_index = 0
        self.highlighted_widget = self.links[self.current_index]
        self.align_link()
        self.update_open_link_label()

    def on_language_change(self):

        ### update caption

        update_text_surface(
            self.caption,
            t.caption,
            TITLE_TEXT_SETTINGS,
            pos_to_align='midtop',
        )

        ### update labels

        for obj in self.items:

            if (
                hasattr(obj, 'translation_key')
                and obj.translation_key
            ):

                text_settings = (

                    LINK_TEXT_SETTINGS_0
                    if hasattr(obj, 'url')

                    else LABEL_TEXT_SETTINGS

                )

                update_text_surface(
                    obj,
                    getattr(t, obj.translation_key),
                    text_settings,
                    pos_to_align='midleft',
                )

        ### update visit url labels

        for netloc, obj in self.netloc_to_text_obj_map.items():

            update_text_surface(
                obj,
                t.open_link.format(netloc=netloc),
                LINK_TEXT_SETTINGS_1,
                pos_to_align='bottomright',
            )

    def update_open_link_label(self):

        self.open_link_label = (

            self.netloc_to_text_obj_map[

                self.url_to_netloc_map[
                    self.highlighted_widget.url
                ]

            ]

        )

    def align_link(self):

        centery = self.highlighted_widget.rect.centery
        screen_centery = SCREEN_RECT.centery

        y_diff = screen_centery - centery
        self.items.rect.move_ip(0, y_diff)
        self.link_icons.rect.move_ip(0, y_diff)

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
                    self.update_open_link_label()

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
                    self.update_open_link_label()

            elif event.type == MOUSEBUTTONDOWN:

                if event.button == 1:
                    self.on_mouse_click(event)

            elif event.type == MOUSEMOTION:
                self.highlight_under_mouse(event)

            elif event.type in GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS:
                GAMEPAD_NS.setup_gamepad_if_existent()

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
                self.update_open_link_label()
                open_url(obj.url)

                break

    def highlight_under_mouse(self, event):

        pos = event.pos

        for index, obj in enumerate(self.links):

            if obj.rect.collidepoint(pos):

                self.current_index = index
                self.highlighted_widget = obj
                self.update_open_link_label()

                break

    def update(self): pass
        
    def draw(self):

        blit_on_screen(BLACK_BG, (0, 0))

        self.caption.draw()

        self.items.draw()
        self.link_icons.draw()

        draw_rect(
            SCREEN,
            'orange',
            self.highlighted_widget.rect,
            1,
        )

        self.open_link_label.draw()

        SERVICES_NS.update_screen()
