"""Facility for local data services."""

### standard library imports

from itertools import count

from shutil import copytree, rmtree

from pathlib import Path


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

from ..config import REFS, WRITEABLE_PATH, LoopException, quit_game

from ..pygamesetup import SERVICES_NS

from ..pygamesetup.constants import (
    SCREEN,
    SCREEN_RECT,
    BLACK_BG,
    GAMEPADDIRECTIONALPRESSED,
    GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS,
    blit_on_screen,
)

from ..pygamesetup.gamepadservices.common import GAMEPAD_NS

from ..classes2d.single import UIObject2D

from ..classes2d.collections import UIList2D

from ..textman import render_text

from ..surfsman import unite_surfaces

from ..userprefsman.main import KEYBOARD_CONTROLS, GAMEPAD_CONTROLS

from ..translatedtext import TRANSLATIONS, on_language_change

from ..promptscreen import present_prompt


###

SCROLL_SPEED = 8

UPPER_LIMIT = SCREEN_RECT.top + 2
LOWER_LIMIT = SCREEN_RECT.bottom - 16

###

PARAGRAPH_TEXT_SETTINGS = {
    'style': 'regular',
    'size': 12,
    'padding': 1,
    'foreground_color': 'white',
    'background_color': 'black',
}

BUTTON_TEXT_SETTINGS = {
    'style': 'regular',
    'size': 12,
    'padding': 1,
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

###

def get_message_obj(text):

    word_objs = UIList2D(

        UIObject2D.from_surface(
                render_text(
                    word,
                    **PARAGRAPH_TEXT_SETTINGS,
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


###
t = TRANSLATIONS.data_screen


### class definition

class DataScreen:
    """Displays buttons for useful data-related operations and related info."""

    def __init__(self):

        self.widgets = UIList2D()

        self.create_widgets()
        self.position_widgets()
        self.store_widgets()

        self.buttons_bg_rect = self.buttons.rect.inflate(18, 18)

        ###
        on_language_change.append(self.on_language_change)

    def create_widgets(self):

        self.caption = (
            UIObject2D.from_surface(
                render_text(
                    t.caption,
                    **TITLE_TEXT_SETTINGS
                )
            )
        )

        ###

        self.paragraphs = (

            UIList2D(
                get_message_obj(text)
                for text in self.get_translated_text()
            )

        )

        ###

        self.buttons = UIList2D(

            UIObject2D.from_surface(

                render_text(
                    getattr(t.buttons, attr_name),
                    **BUTTON_TEXT_SETTINGS,
                ),

                command=command,

            )

            for attr_name, command in (

                ('copy_data', self.copy_data_to_home_folder),
                ('erase_data', self.erase_all_data_on_confirmation),
                ('go_back', self.go_back),

            )

        )

        for button in self.buttons:
            button.inflated_rect = button.rect.inflate(10, 10)

    def position_widgets(self):

        self.paragraphs.rect.snap_rects_ip(
            retrieve_pos_from='bottomleft',
            assign_pos_to='topleft',
            offset_pos_by=(0, 20),
        )

        self.buttons.rect.snap_rects_ip(
            retrieve_pos_from='midbottom',
            assign_pos_to='midtop',
            offset_pos_by=(0, 5),
        )

        ###

        self.caption.rect.midtop = SCREEN_RECT.move(0, 2).midtop
        self.paragraphs.rect.midtop = self.caption.rect.move(0, 10).midbottom
        self.buttons.rect.midtop = self.paragraphs.rect.move(0, 20).midbottom

    def on_language_change(self):

        self.create_widgets()
        self.position_widgets()
        self.store_widgets()

        self.buttons_bg_rect = self.buttons.rect.inflate(18, 18)

    def store_widgets(self):

        self.widgets.clear()

        self.widgets.extend(

            (
                self.caption,
                self.paragraphs,
                self.buttons,
            )

        )


    def get_translated_text(self):

        return (

            *yield_paragraphs(t.introduction),
            *yield_paragraphs(t.first_button_explanation),
            *yield_paragraphs(t.second_button_explanation),

        )

    def prepare(self):

        self.widgets.rect.top = SCREEN_RECT.top + 2

        self.button_index = 0
        self.highlighted_button = None

    def control(self):
        
        for event in SERVICES_NS.get_events():

            if event.type == KEYDOWN:

                if event.key == K_ESCAPE:
                    self.go_back()

                elif self.highlighted_button is not None:

                    if event.key in (
                        K_UP,
                        K_DOWN,
                        KEYBOARD_CONTROLS['up'],
                        KEYBOARD_CONTROLS['down'],
                    ):

                        self.act_on_action_representing_motion(

                            True
                            if event.key in (K_UP, KEYBOARD_CONTROLS['up'])

                            else False

                        )

                    elif event.key == K_RETURN:
                        self.highlighted_button.command()

            elif event.type == JOYBUTTONDOWN:

                if event.button == GAMEPAD_CONTROLS['start_button']:

                    if self.highlighted_button is not None:
                        self.highlighted_button.command()

            elif event.type == GAMEPADDIRECTIONALPRESSED:

                if (
                    self.highlighted_button is not None
                    and event.direction in ('up', 'down')
                ):

                    self.act_on_action_representing_motion(
                        True if event.direction == 'up' else False
                    )

            elif event.type == MOUSEBUTTONDOWN:

                if (
                    self.highlighted_button is not None
                    and event.button == 1
                ):
                    self.on_mouse_click(event)

            elif event.type == MOUSEMOTION:

                if self.highlighted_button is not None:
                    self.highlight_under_mouse(event)

            elif event.type in GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS:
                GAMEPAD_NS.setup_gamepad_if_existent()

            elif event.type == QUIT:
                quit_game()

        ###

        if self.highlighted_button is None:

            pressed_state = SERVICES_NS.get_pressed_keys()

            if (

                pressed_state[K_DOWN]
                or pressed_state[KEYBOARD_CONTROLS['down']]
                or GAMEPAD_NS.y_sum > 0

            ):
                self.scroll_down()

            elif (

                pressed_state[K_UP]
                or pressed_state[KEYBOARD_CONTROLS['up']]
                or GAMEPAD_NS.y_sum < 0

            ):
                self.scroll_up()

    def act_on_action_representing_motion(self, up=True):

        if up:

            if self.button_index == 0:

                self.highlighted_button = None
                self.scroll_up()

            else:

                self.button_index -= 1

                self.highlighted_button = (
                    self.buttons[self.button_index]
                )

        else:

            if self.button_index < 2:

                self.button_index += 1

                self.highlighted_button = (
                    self.buttons[self.button_index]
                )

    def scroll_up(self):

        widgets = self.widgets
        widgets_rect = widgets.rect

        ## if top above upper limit...

        if widgets_rect.top < UPPER_LIMIT:

            widgets.rect.move_ip(0, SCROLL_SPEED)

            ## if top ends up below upper limit...

            if widgets_rect.top > UPPER_LIMIT:
                widgets.rect.top = UPPER_LIMIT

    def scroll_down(self):

        widgets = self.widgets
        widgets_rect = widgets.rect

        ## if bottom below lower limit...

        if widgets_rect.bottom > LOWER_LIMIT:

            widgets.rect.move_ip(0, -SCROLL_SPEED)

            ## if bottom ends up above lower limit...

            if widgets_rect.bottom < LOWER_LIMIT:
                widgets.rect.bottom = LOWER_LIMIT

        if widgets_rect.bottom == LOWER_LIMIT:
            self.highlighted_button = self.buttons[self.button_index]

    def on_mouse_click(self, event):

        pos = event.pos

        button_to_click = None

        for button in self.buttons:

            if button.rect.collidepoint(pos):

                button_to_click = button
                break

        if button_to_click:
            button_to_click.command()

    def highlight_under_mouse(self, event):

        pos = event.pos

        for index, button in enumerate(self.buttons):

            if button.rect.collidepoint(pos):

                self.button_index = index
                self.highlighted_button = button

                break

    def go_back(self):

        options_screen = REFS.states.options_screen
        options_screen.prepare()

        raise LoopException(next_state=options_screen)

    def copy_data_to_home_folder(self):

        copytree(
            str(WRITEABLE_PATH),
            get_available_path_in_home(),
        )

    def erase_all_data_on_confirmation(self):

        must_erase_everything = (

            present_prompt(

                t.erase_data_prompt.caption,
                t.erase_data_prompt.message,

                (
                    (TRANSLATIONS.general.no, False),
                    (TRANSLATIONS.general.yes, True),
                ),

            )

        )

        if must_erase_everything:

            rmtree(str(WRITEABLE_PATH))
            quit_game()

    def update(self):
        """Do nothing."""

    def draw(self):

        blit_on_screen(BLACK_BG, (0, 0))

        self.caption.draw_on_screen()
        self.paragraphs.draw_on_screen()

        hb = self.highlighted_button

        if hb is None:
            self.buttons.draw_on_screen()

        else:

            self.buttons_bg_rect.center = self.buttons.rect.center

            draw_rect(
                SCREEN,
                'blue',
                self.buttons_bg_rect,
                border_radius=10,
            )

            draw_rect(
                SCREEN,
                'white',
                self.buttons_bg_rect,
                2,
                border_radius=10,
            )

            self.buttons.draw()

            hb.inflated_rect.center = hb.rect.center

            draw_rect(
                SCREEN,
                'orangered',
                hb.inflated_rect,
                2,
                border_radius=8,
            )

        SERVICES_NS.update_screen()


def yield_paragraphs(t):

    for i in count():

        parag_attr_name = 'paragraph' + str(i).rjust(2, '0')

        try:
            yield getattr(t, parag_attr_name)

        except AttributeError:
            return

def get_available_path_in_home():

    home_dir = Path.home()

    chosen_name = base_name = 'bionic_blue_user_data'

    next_index = count().__next__

    while True:

        destination_path = home_dir / chosen_name

        if destination_path.exists():

            chosen_name = (
                base_name
                + '_'
                + str(next_index()).rjust(3, '0')
            )

        else:
            break

    return str(destination_path)
