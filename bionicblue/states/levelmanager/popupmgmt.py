"""Facility for showing popup."""

### standard library imports

from functools import partialmethod

from itertools import cycle


### third-party imports

from pygame.locals import (

    QUIT,

    KEYDOWN,
    K_ESCAPE,
    K_RETURN,
    K_UP,
    K_DOWN,

    JOYBUTTONDOWN,

)

from pygame.display import update as update_screen

from pygame.draw import rect as draw_rect


### local imports

from .config import quit_game

from .pygamesetup import SERVICES_NS

from .pygamesetup.constants import (
    SCREEN,
    SCREEN_RECT,
    BLACK_BG,
    GAMEPADDIRECTIONALPRESSED,
    GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS,
    blit_on_screen,
)

from .pygamesetup.gamepaddirect import setup_gamepad_if_existent

from .textman import render_text

from .classes2d.single import UIObject2D

from .classes2d.collections import UIList2D

from .userprefsman.main import GAMEPAD_CONTROLS, KEYBOARD_CONTROLS

from .translatedtext import TRANSLATIONS



TEXT_SETTINGS = {
    'style': 'regular',
    'size': 12,
    'padding': 0,
    'foreground_color': 'white',
    'background_color': 'black',
}

BUTTON_TEXT_SETTINGS = {
    'style': 'regular',
    'size': 12,
    'padding': 4,
    'foreground_color': 'white',
    'background_color': 'black',
}


POPUP_BOX = SCREEN_RECT.copy()

POPUP_BOX.width *= .7
POPUP_BOX.height *= .8

TEXT_BOX = POPUP_BOX.copy()
TEXT_BOX.height -= 25
TEXT_BOX.bottom = POPUP_BOX.bottom - 5


###

NEXT_DRAW_TRIANGLE = cycle(

    (
        *((True,) * 20),
        *((False,)* 20)
    )

).__next__


TRIANGLE_POINTS = tuple(

    POPUP_BOX.move(offset).midbottom

    for offset in (
        (-5, -5),
        (0, 0),
        (5, -5),
    )

)


###

CAPTION_CACHE = {}
BODY_CACHE = {}


class PopupManagement:
    """Interface to display in-game popups."""

    def show_popup_info(
        self,
        popup_key,
    ):
        """Display popup caption and message."""

        self.control = self.popup_control
        self.update = self.popup_update
        self.draw = self.popup_draw

        self.player.stop_charging()
        self.player.reset_time_tracking_attributes()

        ###

        translation_node = getattr(TRANSLATIONS.ingame_popups, popup_key)

        caption_text = translation_node.caption
        body_text = translation_node.message

        ###

        if caption_text not in CAPTION_CACHE:

            CAPTION_CACHE[caption_text] = (
                UIObject2D.from_surface(
                    render_text(
                        caption_text,
                        **TEXT_SETTINGS,
                    )
                )
            )

        caption = self.caption = CAPTION_CACHE[caption_text]
        caption.rect.midtop = POPUP_BOX.move(0, 5).midtop

        ###

        if body_text not in BODY_CACHE:

            BODY_CACHE[body_text] = UIList2D(

                UIObject2D.from_surface(
                    render_text(word, **TEXT_SETTINGS)
                )

                for word in body_text.split()

            )

            BODY_CACHE[body_text].rect.snap_rects_intermittently_ip(

                ### interval limit

                dimension_name='width', # either 'width' or 'height'
                dimension_unit='pixels', # either 'rects' or 'pixels'
                max_dimension_value=POPUP_BOX.width - 10, # positive integer

                ### rect positioning

                retrieve_pos_from='topright',
                assign_pos_to='topleft',
                offset_pos_by=(5, 0),

                ### intermittent rect positioning

                intermittent_pos_from='bottomleft',
                intermittent_pos_to='topleft',
                intermittent_offset_by=(0, 2),

            )

        message = self.message = BODY_CACHE[body_text]

        message.rect.top = caption.rect.bottom + 3
        message.rect.left = POPUP_BOX.left + 5

    def exit_popup(self):

        self.control = self.control_player
        self.update = self.normal_update
        self.draw = self.draw_level

    def popup_control(self):

        for event in SERVICES_NS.get_events():

            if event.type == KEYDOWN:

                if event.key == K_ESCAPE:
                    self.exit_popup()

                elif event.key == K_RETURN:
                    self.exit_popup()

                elif (
                    event.key == K_UP
                    or event.key == KEYBOARD_CONTROLS['up']
                ):
                    self.move_message_up()

                elif (
                    event.key == K_DOWN
                    or event.key == KEYBOARD_CONTROLS['down']
                ):
                    self.move_message_down()

            elif event.type == JOYBUTTONDOWN:

                if event.button == GAMEPAD_CONTROLS['start_button']:
                    self.exit_popup()

            elif event.type == GAMEPADDIRECTIONALPRESSED:

                if event.direction == 'up':
                    self.move_message_up()

                elif event.direction == 'down':
                    self.move_message_down()

            elif event.type in GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS:
                setup_gamepad_if_existent()

            elif event.type == QUIT:
                quit_game()

    def move_message_vertically(self, move_up):

        rect = self.message.rect

        if rect.height <= TEXT_BOX.height: return

        if move_up:

            if rect.bottom > TEXT_BOX.bottom:
                rect.move_ip(0, -20)

        else:

            if rect.top < TEXT_BOX.top:
                rect.move_ip(0, 20)

    move_message_up = partialmethod(move_message_vertically, True)
    move_message_down = partialmethod(move_message_vertically, True)

    def popup_update(self):
        self.must_draw_triangle = self.message.rect.bottom > TEXT_BOX.bottom

    def popup_draw(self):

        blit_on_screen(BLACK_BG, (0, 0))

        self.caption.draw()
        self.message.draw()

        if self.must_draw_triangle and NEXT_DRAW_TRIANGLE():
            draw_polygon(SCREEN, 'white', TRIANGLE_POINTS)

        update_screen()

