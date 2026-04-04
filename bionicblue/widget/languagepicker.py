"""Facility for language picker widget."""

### standard library import
from collections import deque

### third-party imports

from pygame import Surface

from pygame.locals import (

    QUIT,

    KEYDOWN,
    K_ESCAPE,
    K_RETURN,
    K_UP,
    K_DOWN,
    MOUSEMOTION,
    MOUSEBUTTONDOWN,

    JOYBUTTONDOWN,

)

from pygame.draw import rect as draw_rect, polygon as draw_polygon


### local imports

from ..config import LANGUAGE_NAMES_FILEPATH, quit_game

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

from ..ourstdlibs.behaviour import do_nothing

from ..textman import render_text

from ..classes2d.single import UIObject2D

from ..classes2d.collections import UIList2D

from ..userprefsman.main import USER_PREFS, GAMEPAD_CONTROLS

from ..translatedtext import AVAILABLE_LOCALES, LANGUAGE_NAMES_MAP



IDLE_BUTTON_TEXT_SETTINGS = {
    'style': 'regular',
    'size': 12,
    'padding': 2,
    'foreground_color': 'white',
    'background_color': 'blue',
}

SELECTED_BUTTON_TEXT_SETTINGS = {
    'style': 'regular',
    'size': 12,
    'padding': 2,
    'foreground_color': 'white',
    'background_color': 'orangered',
}

def formatted_text_from_value(value):
    lang_code, _, country_code = value.partition('_')
    return lang_code + '-' + country_code.upper()


class LanguagePicker(UIObject2D):
    """Interface to present languages/locale codes for user to pick.

    Not meant for in-game usage.
    """

    def __init__(
        self,
        value='en_us',
        name='language_picker',
        on_value_change=do_nothing,
        coordinates_name='topleft',
        coordinates_value=(0, 0),
    ):
        
        self.value = value
        self.on_value_change = on_value_change
        self.name = name

        vtt = self.value_to_text = {

            v: (
                LANGUAGE_NAMES_MAP[v]
                if v in LANGUAGE_NAMES_MAP
                else formatted_text_from_value(v)
            )

            for v in AVAILABLE_LOCALES

        }

        ttv = self.text_to_value = {

            v: k
            for k, v in self.value_to_text.items()

        }

        ttibs = self.text_to_idle_button_surf = {
            text: render_text(text, **IDLE_BUTTON_TEXT_SETTINGS)
            for text in ttv.keys()
        }

        ttubs = self.text_to_unselected_button_surf = {
            text: render_text(text, **IDLE_BUTTON_TEXT_SETTINGS)
            for text in ttv.keys()
        }

        ttsbs = self.text_to_selected_button_surf = {
            text: render_text(text, **SELECTED_BUTTON_TEXT_SETTINGS)
            for text in ttv.keys()
        }

        widths, heights = zip(

            *(
                surf.get_size()
                for surf in ttibs.values()
            )

        )

        highest_width = max(widths)
        highest_height = max(heights)

        ###

        arrow_surf = Surface((highest_height, highest_height)).convert()
        arrow_rect = arrow_surf.get_rect()

        arrow_surf.fill('blue')

        smaller_arrow_rect = arrow_rect.inflate(-8, -8)

        points = tuple(
            getattr(smaller_arrow_rect, point_name)
            for point_name in (
                'topleft',
                'topright',
                'midbottom',
            )
        )

        draw_polygon(arrow_surf, 'white', points)

        ###

        width = arrow_rect.width + highest_width
        height = highest_height

        ttdbs = self.text_to_deselected_button_surf = {}

        for text in ttv.keys():

            ### ttibs

            surf = ttibs[text]
            rect = surf.get_rect()

            new_surf = Surface((width, height)).convert()

            new_surf.fill('blue')
            new_surf.blit(arrow_surf, arrow_rect)

            rect.midleft = arrow_rect.midright
            new_surf.blit(arrow_surf, arrow_rect)
            new_surf.blit(surf, rect)

            ttibs[text] = new_surf

            ## ttubs

            surf = ttubs[text]
            rect = surf.get_rect()

            new_surf = Surface((highest_width, highest_height)).convert()
            new_surf.fill('blue')
            new_rect = new_surf.get_rect()
            rect.center = new_rect.center
            new_surf.blit(surf, rect)

            ttubs[text] = new_surf

            ## ttsbs

            surf = ttsbs[text]
            rect = surf.get_rect()

            new_surf = Surface((highest_width, highest_height)).convert()
            new_surf.fill('orangered')
            new_rect = new_surf.get_rect()
            rect.center = new_rect.center
            new_surf.blit(surf, rect)

            ttsbs[text] = new_surf

        ###

        options = self.options = UIList2D(

            UIObject2D.from_surface(
                ttubs[text],
                value=v,
                text=text,
            )

            for text, v in ttv.items()
        )

        options.sort(key=lambda item: item.value)

        options.rect.snap_rects_ip(
            retrieve_pos_from='midbottom',
            assign_pos_to='midtop',
        )

        ###
        self.options_deque = deque(options)

        ###

        text = vtt[self.value]

        self.image = ttibs[text]
        self.rect = self.image.get_rect()

        setattr(
            self.rect,
            coordinates_name,
            coordinates_value,
        )

        ###

        bg_column_size = (ttibs['English (USA)'].get_width(), SCREEN_RECT.height)
        bg_column_surf = Surface((bg_column_size)).convert()

        self.bg_column = (
            UIObject2D.from_surface(bg_column_surf)
        )

        bg_column_surf.fill('white')
        bg_column_surf.fill('blue', self.bg_column.rect.inflate(-2, 0))

    def get(self):
        """Return widget's value."""
        return self.value

    def present_options(self):

        options_deque = self.options_deque

        value = self.value

        while True:

            if options_deque[0].value == value:
                break

            options_deque.rotate(-1)

        self.update_images()
        self.align_options()

        ###

        self.options.rect.center = self.rect.center
        self.bg_column.rect.centerx = self.rect.centerx

        self.running = True

        while self.running:

            SERVICES_NS.frame_checkups()

            self.control()
            self.draw()

        self.on_value_change()

    command = present_options

    def control(self):

        for event in SERVICES_NS.get_events():

            if event.type == KEYDOWN:

                if event.key == K_ESCAPE:
                    self.pick_selected_option()

                elif event.key == K_RETURN:
                    self.pick_selected_option()

                elif event.key in (K_UP, K_DOWN):

                    rotation = 1 if event.key == K_UP else -1
                    self.options_deque.rotate(rotation)

                    self.update_images()
                    self.align_options()

            elif event.type == JOYBUTTONDOWN:

                if event.button == GAMEPAD_CONTROLS['start_button']:
                    self.pick_selected_option()

            elif event.type == GAMEPADDIRECTIONALPRESSED:

                if event.direction in ('up', 'down'):

                    rotation = 1 if event.direction == 'up' else -1
                    self.options_deque.rotate(rotation)

                    self.update_images()
                    self.align_options()

            elif event.type in GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS:
                GAMEPAD_NS.setup_gamepad_if_existent()

            elif event.type == MOUSEMOTION:
                self.on_mouse_motion(event)

            elif event.type == MOUSEBUTTONDOWN:

                if event.button == 1:
                    self.on_mouse_click(event)

            elif event.type == QUIT:
                quit_game()

    def update_images(self):

        ttubs = self.text_to_unselected_button_surf

        for option in self.options:
            option.image = ttubs[option.text]

        first_button = self.options_deque[0]

        first_button.image = (
            self.text_to_selected_button_surf[first_button.text]
        )

    def align_options(self):

        option_centery = self.options_deque[0].rect.centery

        y_diff = self.rect.centery - option_centery
        self.options.rect.move_ip(0, y_diff)

    def pick_selected_option(self):

        value = self.value = self.options_deque[0].value

        self.image = (

            self.text_to_idle_button_surf[
                self.value_to_text[value]
            ]

        )

        self.running = False

    def set(self, value, execute_on_value_change=True):

        for item in self.options_deque:

            if value == item.value:
                break

        else:
            return

        self.image = (

            self.text_to_idle_button_surf[
                self.value_to_text[value]
            ]

        )

        if execute_on_value_change:
            self.on_value_change()

    def on_mouse_motion(self, event):

        pos = event.pos

        for option in self.options:

            if option.rect.collidepoint(pos):
                chosen_option = option
                break
        else:
            return

        options_deque = self.options_deque

        while True:

            if options_deque[0] is chosen_option:
                break

            options_deque.rotate(-1)

        self.update_images()

    def on_mouse_click(self, event):

        pos = event.pos

        for option in self.options:

            if option.rect.collidepoint(pos):
                chosen_option = option
                break
        else:
            return

        options_deque = self.options_deque

        while True:

            if options_deque[0] is chosen_option:
                break

            options_deque.rotate(-1)

        self.pick_selected_option()

    def draw(self):

        self.bg_column.draw()
        self.options.draw()
        draw_rect(SCREEN, 'orange', self.options_deque[0].rect, 1)
        SERVICES_NS.update_screen()
