"""Facility for special languae/locale-related prompt."""

### standard library import
from collections import deque


### third-party imports

from pygame import Surface

from pygame.locals import (

    QUIT,

    KEYDOWN,
    K_ESCAPE,
    K_RETURN,
    K_LEFT,
    K_RIGHT,

    JOYBUTTONDOWN,

)

from pygame.image import load as load_image

from pygame.display import update

from pygame.draw import polygon as draw_polygon


### local imports

from .config import NO_COLORKEY_IMAGES_DIR, quit_game

from .pygamesetup import SERVICES_NS

from .pygamesetup.constants import (
    SCREEN,
    SCREEN_RECT,
    BLACK_BG,
    GAMEPADDIRECTIONALPRESSED,
    GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS,
    KEYBOARD_OR_GAMEPAD_PRESSED_EVENTS,
    blit_on_screen,
)

from .pygamesetup.gamepaddirect import setup_gamepad_if_existent

from .textman import render_text

from .classes2d.single import UIObject2D

from .classes2d.collections import UIList2D

from .userprefsman.main import GAMEPAD_CONTROLS

from .translatedtext import AVAILABLE_LOCALES, LANGUAGE_NAMES_MAP



BUTTON_TEXT_SETTINGS = {
    'style': 'regular',
    'size': 12,
    'padding': 2,
    'foreground_color': 'white',
    'background_color': 'black',
}


class LocalePrompt:
    """Special one-off interface to prompt player for language/locale.

    It is presented only once, the very first time the player launches the
    game.
    """

    def __init__(self):

        ### language icon

        self.languages_icon = (

            UIObject2D.from_surface(

                load_image(
                    str(NO_COLORKEY_IMAGES_DIR / 'language_icon.png')
                )

            )

        )

        self.languages_icon.rect.midtop = SCREEN_RECT.move(0, 5).midtop

        ### arrow for users to select language

        self.arrow = UIObject2D.from_surface(Surface((42, 14)).convert())

        arrow_rect = self.arrow.rect

        points = [

            getattr(arrow_rect.move(offset), point_name)

            for point_name, offset in (

                ('midright', (0, 0)),
                ('midtop', (14, 0)),
                ('center', (14, -4)),
                ('midleft', (0, -4)),
                ('midleft', (0, 4)),
                ('center', (14, 4)),
                ('midbottom', (14, 0)),
            )

        ]

        draw_polygon(
            self.arrow.image,
            'orange',
            points,
        )

        ### languages/locales to choose from

        items = self.items = UIList2D(

            UIObject2D.from_surface(

                render_text(
                    LANGUAGE_NAMES_MAP.get(locale, locale),
                    **BUTTON_TEXT_SETTINGS,
                ),

                locale=locale,

            )

            for locale in AVAILABLE_LOCALES

        )

        items.rect.snap_rects_ip(
            retrieve_pos_from='midbottom',
            assign_pos_to='midtop',
        )

        items.rect.midtop = self.language_icon.rect.move(0, 4).midbottom

        value = self.value = 'en_us'

        for i, item in enumerate(items):

            if item.locale == 'en_us':
                break

        self.current_index = i
        self.no_of_available_items = len(items)

    def prompt_for_locale(self):

        self.running = True

        while self.running:

            SERVICES_NS.frame_checkups()

            self.control()
            self.draw()

        return self.value

    ### TODO keep working from here (also review the imports to make sure
    ### none is missing or unused)

    def control(self):

        for event in SERVICES_NS.get_events():

            if (
                self.dismissable_with_any
                and event.type in KEYBOARD_OR_GAMEPAD_PRESSED_EVENTS
            ):

                self.value = self.value_on_escape
                self.running = False

            elif event.type == KEYDOWN:

                if event.key == K_ESCAPE:

                    self.value = self.value_on_escape
                    self.running = False

                elif event.key == K_RETURN:
                    self.push_selected_button()

                elif event.key in (K_LEFT, K_RIGHT):

                    rotation = 1 if event.key == K_LEFT else -1
                    self.buttons_deque.rotate(rotation)

            elif event.type == JOYBUTTONDOWN:

                if event.button == GAMEPAD_CONTROLS['start_button']:
                    self.push_selected_button()

            elif event.type == GAMEPADDIRECTIONALPRESSED:

                if event.direction in ('left', 'right'):

                    rotation = 1 if event.direction == 'left' else -1
                    self.buttons_deque.rotate(rotation)

            elif event.type in GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS:
                setup_gamepad_if_existent()

            elif event.type == QUIT:
                quit_game()

    def push_selected_button(self):

        self.value = self.buttons_deque[0].value
        self.running = False

    def draw(self):

        blit_on_screen(BLACK_BG, (0, 0))

        self.caption.draw()
        self.message.draw()
        self.buttons.draw()

        draw_rect(SCREEN, 'orange', self.buttons_deque[0].rect, 1)

        update()



prompt_for_locale = LocalePrompt().prompt_for_locale
