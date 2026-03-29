"""Facility for prompting user for action."""

### standard library import
from collections import deque


### third-party imports

from pygame.locals import (

    QUIT,

    KEYDOWN,
    K_ESCAPE,
    K_RETURN,
    K_LEFT,
    K_RIGHT,

    JOYBUTTONDOWN,

)

from pygame.display import update

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
    KEYBOARD_OR_GAMEPAD_PRESSED_EVENTS,
    blit_on_screen,
)

from .pygamesetup.gamepaddirect import setup_gamepad_if_existent

from .textman import render_text

from .classes2d.single import UIObject2D

from .classes2d.collections import UIList2D

from .userprefsman.main import GAMEPAD_CONTROLS

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

class PromptScreen:
    """Interface to ask the player a question, usually to confirm a choice.

    Not meant for in-game usage.
    """

    def __init__(self):

        ### cache

        self.caption_cache = {}
        self.body_cache = {}
        self.button_cache = {}

        ### deque to hold buttons and keep track of selected one
        ### (first one)
        self.buttons_deque = deque()

    def present_prompt(
        self,
        caption_text,
        body_text,
        button_text_value_pairs,
        value_on_escape=None,
        dismissable_with_any=False,
    ):

        self.dismissable_with_any = dismissable_with_any

        caption_cache = self.caption_cache
        
        if caption_text not in caption_cache:

            caption_cache[caption_text] = (
                UIObject2D.from_surface(
                    render_text(
                        caption_text,
                        **TEXT_SETTINGS,
                    )
                )
            )

        caption = self.caption = caption_cache[caption_text]
        caption.rect.midtop = SCREEN_RECT.move(0, 5).midtop

        ###

        body_cache = self.body_cache

        if body_text not in body_cache:

            body_cache[body_text] = UIList2D(

                UIObject2D.from_surface(
                    render_text(word, **TEXT_SETTINGS)
                )

                for word in body_text.split()

            )

            body_cache[body_text].rect.snap_rects_intermittently_ip(

                ### interval limit

                dimension_name='width', # either 'width' or 'height'
                dimension_unit='pixels', # either 'rects' or 'pixels'
                max_dimension_value=SCREEN_RECT.width - 20, # positive integer

                ### rect positioning

                retrieve_pos_from='topright',
                assign_pos_to='topleft',
                offset_pos_by=(5, 0),

                ### intermittent rect positioning

                intermittent_pos_from='bottomleft',
                intermittent_pos_to='topleft',
                intermittent_offset_by=(0, 2),

            )

        message = self.message = body_cache[body_text]
        message.rect.center = SCREEN_RECT.center

        ###

        button_cache = self.button_cache

        if button_text_value_pairs not in button_cache:

            button_cache[button_text_value_pairs] = UIList2D(

                UIObject2D.from_surface(
                    render_text(button_text, **BUTTON_TEXT_SETTINGS),
                    value = button_value,
                )

                for button_text, button_value in button_text_value_pairs

            )

            (
                button_cache[button_text_value_pairs]
                .rect
                .snap_rects_intermittently_ip(

                    ### interval limit

                    dimension_name='width', # either 'width' or 'height'
                    dimension_unit='pixels', # either 'rects' or 'pixels'
                    max_dimension_value=SCREEN_RECT.width - 20, # positive int

                    ### rect positioning

                    retrieve_pos_from='topright',
                    assign_pos_to='topleft',
                    offset_pos_by=(20, 0),

                    ### intermittent rect positioning

                    intermittent_pos_from='bottomleft',
                    intermittent_pos_to='topleft',
                    intermittent_offset_by=(0, 5),
                )

            )

        self.buttons = button_cache[button_text_value_pairs]
        self.buttons.rect.midtop = message.rect.move(0, 10).midbottom

        self.buttons_deque.clear()
        self.buttons_deque.extend(self.buttons)

        ###

        self.value_on_escape = value_on_escape

        ###

        self.running = True

        while self.running:

            SERVICES_NS.frame_checkups()

            self.control()
            self.draw()

        return self.value

    def prompt_to_dismiss_with_any_button(self, caption, message):
        """Present a prompt that can be dismissed with any button."""

        self.present_prompt(

            caption,
            message,

            (
                (
                    TRANSLATIONS.general_prompts.press_any_button,
                    None,
                ),
            ),

            dismissable_with_any=True,

        )

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

_ps = PromptScreen()
present_prompt = _ps.present_prompt
prompt_to_dismiss_with_any_button = _ps.prompt_to_dismiss_with_any_button
