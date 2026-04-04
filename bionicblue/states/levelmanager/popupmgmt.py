"""Facility for showing popup."""

### standard library imports

from functools import partialmethod

from itertools import cycle


### third-party imports

from pygame import Surface

from pygame.locals import (

    QUIT,

    KEYDOWN,
    K_ESCAPE,
    K_RETURN,
    K_UP,
    K_DOWN,

    JOYBUTTONDOWN,

)

from pygame.draw import (
    rect as draw_rect,
    lines as draw_lines,
    polygon as draw_polygon,
)

from pygame.math import Vector2


### local imports

from ...config import SOUND_MAP, quit_game

from ...pygamesetup import SERVICES_NS

from ...pygamesetup.constants import (
    SCREEN,
    SCREEN_RECT,
    GAMEPADDIRECTIONALPRESSED,
    GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS,
    blit_on_screen,
)

from ...pygamesetup.gamepadservices.common import GAMEPAD_NS

from ...ourstdlibs.behaviour import do_nothing

from ...textman import render_text

from ...classes2d.single import UIObject2D

from ...classes2d.collections import UIList2D

from ...userprefsman.main import GAMEPAD_CONTROLS, KEYBOARD_CONTROLS

from ...translatedtext import TRANSLATIONS



CAPTION_SETTINGS = {
    'style': 'regular',
    'size': 12,
    'padding': 0,
    'foreground_color': 'yellow',
    'background_color': 'blue4',
}

TEXT_SETTINGS = {
    'style': 'regular',
    'size': 12,
    'padding': 0,
    'foreground_color': 'white',
    'background_color': 'blue4',
}


POPUP_BOX = SCREEN_RECT.copy()

POPUP_BOX.width *= .6
POPUP_BOX.height *= .6

POPUP_BOX.center = SCREEN_RECT.center

###

TEXT_BOX = POPUP_BOX.copy()
TEXT_BOX.height -= 35
TEXT_BOX.width -= 10
TEXT_BOX.midbottom = POPUP_BOX.move(0, -17).midbottom

TEXT_BOX_OFFSET = -Vector2(TEXT_BOX.topleft)
text_box_colliderect = TEXT_BOX.colliderect

TEXT_BOX_CANVAS = Surface(TEXT_BOX.size).convert()

blit_on_text_box = TEXT_BOX_CANVAS.blit
fill_text_box = TEXT_BOX_CANVAS.fill


###

MUST_DRAW_INDICATOR = cycle(

    (
        *((True,) * 20),
        *((False,)* 20)
    )

).__next__


TRIANGLE_POINTS = tuple(

    TEXT_BOX.move(offset).midbottom

    for offset in (

        (-3, 2),
        (0, 7),
        (3, 2),

    )

)

CHECKMARK_POINTS = tuple(

    TEXT_BOX.move(offset).midbottom

    for offset in (

        (-3, 4),
        (0, 7),
        (3, 1),

    )

)


###

CAPTION_CACHE = {}
BODY_CACHE = {}


class LevelManagerPopupManagement:
    """Interface to display in-game popups."""

    def show_popup_info(
        self,
        popup_key,
        on_exit=do_nothing,
    ):
        """Display popup caption and message."""

        self.control = self.popup_control
        self.update = self.popup_update
        self.draw = self.popup_draw

        self.player.stop_charging()
        self.player.reset_time_tracking_attributes()

        self.on_exit = on_exit

        ###
        self.indicator_must_be_triangle = False

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
                        **CAPTION_SETTINGS,
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
        message.rect.topleft = TEXT_BOX.topleft

    def exit_popup(self):

        self.control = self.control_player
        self.update = self.normal_update
        self.draw = self.draw_level

        self.on_exit()

        SOUND_MAP['ui_success_popup.wav'].play()

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
                    self.scroll_message_up()

                elif (
                    event.key == K_DOWN
                    or event.key == KEYBOARD_CONTROLS['down']
                ):
                    self.scroll_message_down()

            elif event.type == JOYBUTTONDOWN:

                if event.button == GAMEPAD_CONTROLS['start_button']:
                    self.exit_popup()

            elif event.type == GAMEPADDIRECTIONALPRESSED:

                if event.direction == 'up':
                    self.scroll_message_up()

                elif event.direction == 'down':
                    self.scroll_message_down()

            elif event.type in GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS:
                GAMEPAD_NS.setup_gamepad_if_existent()

            elif event.type == QUIT:
                quit_game()

    def scroll_message(self, scroll_down):

        message_rect = self.message.rect

        if message_rect.height <= TEXT_BOX.height: return

        if scroll_down:

            if message_rect.bottom > TEXT_BOX.bottom:
                message_rect.move_ip(0, -15)

        else:

            if message_rect.top < TEXT_BOX.top:
                message_rect.move_ip(0, 15)

    scroll_message_down = partialmethod(scroll_message, True)
    scroll_message_up = partialmethod(scroll_message, False)

    def popup_update(self):

        self.indicator_must_be_triangle = (
            self.message.rect.bottom > TEXT_BOX.bottom
        )

    def popup_draw(self):

        draw_rect(SCREEN, 'blue4', POPUP_BOX, border_radius=10)

        self.caption.draw()

        fill_text_box('blue4')

        for word in self.message:

            if text_box_colliderect(word.rect):

                blit_on_text_box(
                    word.image,
                    word.rect.move(TEXT_BOX_OFFSET),
                )

        blit_on_screen(TEXT_BOX_CANVAS, TEXT_BOX)

        if MUST_DRAW_INDICATOR():

            if self.indicator_must_be_triangle:
                draw_polygon(SCREEN, 'white', TRIANGLE_POINTS)

            else:
                draw_lines(SCREEN, 'green', False, CHECKMARK_POINTS, 2)

        draw_rect(SCREEN, 'yellow', POPUP_BOX, 2, border_radius=10)

        SERVICES_NS.update_screen()

