"""Facility for playtesters screen."""

### standard library import
from random import choice


### third-party imports

from pygame.locals import (

    SCALED,
    FULLSCREEN,

    QUIT,
    KEYDOWN,
    K_ESCAPE,
    K_UP, K_DOWN,
    K_LEFT, K_RIGHT,
    K_RETURN,
    JOYBUTTONDOWN,
    MOUSEMOTION,
    MOUSEBUTTONDOWN,
)

from pygame.display import set_mode, update

from pygame.mixer import music, get_busy

from pygame.draw import rect as draw_rect


### local imports

from ..config import REFS, SOUND_MAP, quit_game

from ..pygamesetup import SERVICES_NS

from ..pygamesetup.constants import (
    SCREEN,
    SIZE,
    SCREEN_COPY,
    SCREEN_RECT,
    BLACK_BG,
    GAMEPADDIRECTIONALPRESSED,
    GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS,
    KEYBOARD_OR_GAMEPAD_PRESSED_EVENTS,
    blit_on_screen,
)

from ..pygamesetup.gamepaddirect import setup_gamepad_if_existent

from ..classes2d.single import UIObject2D

from ..classes2d.collections import UIList2D, UISet2D

from ..textman import render_text

from ..surfsman import unite_surfaces

from ..userprefsman.main import (
    USER_PREFS,
    DEFAULT_USER_PREFS,
    save_config_on_disk,
)

from ..exceptions import SwitchStateException, BackToBeginningException

from ..widget.slider import HundredSlider
from ..widget.checkbutton import Checkbutton



LABEL_TEXT_SETTINGS = {
    'style': 'regular',
    'size': 12,
    'padding': 1,
    'foreground_color': 'white',
    'background_color': 'black',
}

TITLE_TEXT_SETTINGS = {
    'style': 'regular',
    'size': 16,
    'padding': 1,
    'foreground_color': 'white',
    'background_color': 'black',
}

MESSAGES = (
    "- After you play a few times, a button appears below",
    (
        "- just click the button and the play data is copied to"
        " your HOME FOLDER"
    ),
    (
        "- then please, contact me so we can figure out how to send"
        " the data to me"
    ),
)

def get_message_obj(text):

    word_objs = UIList2D(

        UIObject2D.from_surface(
                render_text(
                    word,
                    **LABEL_TEXT_SETTINGS,
                )
        )

        for word in text.split()

    )

    word_objs.rect.snap_rects_intermittently_ip(

        dimension_name = 'width',
        dimension_unit = 'pixels',
        max_dimension_value = SCREEN_RECT.width * .8,

        retrieve_pos_from='topright',
        assign_pos_to='topleft',
        offset_pos_by = (5, 0),

        intermittent_pos_from='bottomleft',
        intermittent_pos_to='topleft',
        intermittent_offset_by = (0, 0),

    )

    message_obj = (
        UIObject2D.from_surface(
            unite_surfaces(
                [(obj.image, obj.rect) for obj in word_objs]
            )
        )
    )

    return message_obj


class PlaytestersScreen:

    def __init__(self):

        ###

        back_button = (

            UIObject2D.from_surface(
                render_text(
                    'back',
                    **LABEL_TEXT_SETTINGS,
                )
            )

        )

        back_button.command = self.go_back

        ###

        messages = self.message_labels = (
            UIList2D(
                get_message_obj(text) for text in MESSAGES
            )
        )

        messages.rect.snap_rects_ip(
            retrieve_pos_from='bottomleft',
            assign_pos_to='topleft',
        )


    def control(self):
        
        for event in SERVICES_NS.get_events():

            if event.type == KEYDOWN:

                if event.key == K_ESCAPE:
                    self.go_back()

#                elif event.key in (K_UP, K_DOWN):
#
#                    increment = -1 if event.key == K_UP else 1
#
#                    self.current_index = (
#                        (self.current_index + increment)
#                        % self.item_count
#                    )
#
#                    self.highlighted_widget = (
#                        self.widgets[self.current_index]
#                    )
#
#                elif event.key in (K_LEFT, K_RIGHT):
#
#                    hw = self.highlighted_widget
#
#                    if isinstance(hw, HundredSlider):
#
#                        if event.key == K_LEFT:
#                            hw.decrement()
#
#                        else:
#                            hw.increment()
#
#                    elif isinstance(hw, Checkbutton):
#                        hw.toggle_value()
#
#                elif event.key == K_RETURN:
#
#                    hw = self.highlighted_widget
#
#                    if hasattr(hw, 'command'):
#                        hw.command()
#
#                    elif hasattr(hw, 'on_mouse_click'):
#                        hw.on_mouse_click(event)
#
#
#            elif event.type == JOYBUTTONDOWN:
#
#                if event.button == GAMEPAD_CONTROLS['start_button']:
#
#                    hw = self.highlighted_widget
#
#                    if hasattr(hw, 'command'):
#                        hw.command()
#
#                    elif hasattr(hw, 'on_mouse_click'):
#                        hw.on_mouse_click(event)
#
#
#            elif event.type == GAMEPADDIRECTIONALPRESSED:
#
#                if event.direction in ('up', 'down'):
#
#                    increment = -1 if event.direction == 'up' else 1
#
#                    self.current_index = (
#                        (self.current_index + increment)
#                        % self.item_count
#                    )
#
#                    self.highlighted_widget = (
#                        self.widgets[self.current_index]
#                    )
#
#                elif event.direction in ('left', 'right'):
#
#                    hw = self.highlighted_widget
#
#                    if isinstance(hw, HundredSlider):
#
#                        if event.direction == 'left':
#                            hw.decrement()
#
#                        else:
#                            hw.increment()
#
#                    elif isinstance(hw, Checkbutton):
#                        hw.toggle_value()
#
#            elif event.type == MOUSEBUTTONDOWN:
#
#                if event.button == 1:
#                    self.on_mouse_click(event)
#
#            elif event.type == MOUSEMOTION:
#                self.highlight_under_mouse(event)
#
#            elif event.type in GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS:
#                setup_gamepad_if_existent()
#
#            elif event.type == QUIT:
#                quit_game()

    def go_back(self):

        options_screen = REFS.states.options_screen
        options_screen.prepare()

        raise SwitchStateException(options_screen)

    def on_mouse_click(self, event):

        pos = event.pos

        for index, obj in enumerate(self.widgets):

            if obj.rect.collidepoint(pos):

                self.current_index = index
                self.highlighted_widget = obj

                if hasattr(obj, 'command'):
                    obj.command()

                elif hasattr(obj, 'on_mouse_click'):
                    obj.on_mouse_click(event)

                break

    def highlight_under_mouse(self, event):

        pos = event.pos

        for index, obj in enumerate(self.widgets):

            if obj.rect.collidepoint(pos):

                self.current_index = index
                self.highlighted_widget = obj

                break

    def update(self):
        ...

    def draw(self):

        blit_on_screen(BLACK_BG, (0, 0))
        self.message_labels.draw()

#        self.option_caption_label.draw()
#        self.option_labels.draw()
#
#        self.value_caption_label.draw()
#        self.widgets.draw()
#
#        draw_rect(
#            SCREEN,
#            'orange',
#            self.highlighted_widget.rect,
#            1,
#        )

        update()

