"""Facility for special languae/locale-related prompt."""

### third-party imports

from pygame import Surface

from pygame.locals import (

    QUIT,

    KEYDOWN,
    K_ESCAPE,
    K_RETURN,
    K_UP,
    K_DOWN,

)

from pygame.image import load as load_image

from pygame.display import update as update_screen

from pygame.draw import (
    polygon as draw_polygon,
    rect as draw_rect,
)


### local imports

from .config import LANGUAGE_ICON_FILEPATH, quit_game

from .pygamesetup import SERVICES_NS

from .pygamesetup.constants import (
    SCREEN_RECT,
    BLACK_BG,
    GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS,
    blit_on_screen,
)

from .pygamesetup.gamepaddirect import setup_gamepad_if_existent

from .textman import render_text

from .classes2d.single import UIObject2D

from .classes2d.collections import UIList2D

from .translatedtext import AVAILABLE_LOCALES, LANGUAGE_NAMES_MAP

from .userprefsman.main import USER_PREFS, save_config_on_disk



TEXT_SETTINGS = {
    'style': 'regular',
    'size': 20,
    'padding': 2,
    'foreground_color': 'dodgerblue',
    'background_color': 'black',
}

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

        ### Bionic Blue label

        self.bblue_label = (

            UIObject2D.from_surface(
                render_text("Bionic Blue", **TEXT_SETTINGS)
            )

        )

        self.bblue_label.rect.midtop = SCREEN_RECT.move(0, 5).midtop

        ### language icon

        self.language_icon = (

            UIObject2D.from_surface(
                load_image(str(LANGUAGE_ICON_FILEPATH))
            )

        )

        self.language_icon.rect.midtop = (
            self.bblue_label.rect.move(0, 5).midbottom
        )

        ### arrow for users to select language

        arrow = self.arrow = (
            UIObject2D.from_surface(Surface((28, 14)).convert())
        )

        arrow_rect = arrow.rect

        arrow_head = arrow_rect.copy()

        arrow_head.width = 14
        arrow_head.topright = arrow_rect.topright

        arrow_body = arrow_rect.copy()
        arrow_body.width = 14
        arrow_body.height = 6
        arrow_body.midright = arrow_head.midleft

        arrow_image = arrow.image

        arrow_image.fill((192, 192, 192))
        arrow_image.set_colorkey((192, 192, 192))

        draw_polygon(
            arrow_image,
            'orange',
            (
                arrow_head.midright,
                arrow_head.topleft,
                arrow_head.bottomleft,
            ),
        )

        draw_rect(arrow_image, 'orange', arrow_body)

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
            self.update()
            self.draw()


        USER_PREFS['LOCALE'] = self.value
        save_config_on_disk()

    def control(self):

        for event in SERVICES_NS.get_events():

            if event.type == KEYDOWN:

                if event.key == K_ESCAPE:
                    self.running = False

                elif event.key == K_RETURN:
                    self.pick_selected_locale()

                elif event.key in (K_UP, K_DOWN):

                    increment = 1 if event.key == K_UP else -1

                    self.current_index = (
                        (
                            self.current_index
                            + increment
                        ) % self.no_of_available_items
                    )

            elif event.type in GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS:
                setup_gamepad_if_existent()

            elif event.type == QUIT:
                quit_game()

    def pick_selected_locale(self):

        self.value = self.items[self.current_index].locale
        self.running = False

    def update(self):
        """Snap arrow to selected locale."""

        self.arrow.rect.midright = (
            self.items[self.current_index].rect.move(-5, 0).midleft
        )

    def draw(self):

        blit_on_screen(BLACK_BG, (0, 0))

        self.bblue_label.draw()
        self.language_icon.draw()
        self.arrow.draw()
        self.items.draw()

        update_screen()



prompt_for_locale = LocalePrompt().prompt_for_locale
