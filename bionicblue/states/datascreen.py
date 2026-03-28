"""Facility for local data services."""

### standard library imports

from pathlib import Path

from shutil import make_archive

from itertools import count


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

from ..config import REFS, PLAYTEST_DATA_DIR, LoopException, quit_game

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

from ..surfsman import unite_surfaces

from ..translatedtext import TRANSLATIONS, on_language_change



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


t = TRANSLATIONS.data_screen

class DataScreen:
    """Displays buttons for useful data-related operations and related info."""

    def __init__(self):

        ###

        self.caption = (
            UIObject2D.from_surface(
                render_text(
                    "Data screen",
                    **TITLE_TEXT_SETTINGS
                )
            )
        )

        ###

        self.buttons = UIList2D(

            UIObject2D.from_surface(

                render_text(
                    getattr(t.buttons, attr_name),
                    **LABEL_TEXT_SETTINGS,
                ),

                button_name = attr_name,

            )

            for attr_name in (
                'copy_data',
                'erase_data',
                'go_back',
            )
        )


        ###

        self.message_labels = (

            UIList2D(
                get_message_obj(text)
                for text in self.get_translated_text()
            )

        )

        ###
        self.widgets = UIList2D()

        ###
        on_language_change.append(self.on_language_change)

    def on_language_change(self):

        self.messages = self.message_labels = (

            UIList2D(
                get_message_obj(text)
                for text in self.get_translated_text()
            )

        )

        self.buttons = UIList2D(

            UIObject2D.from_surface(

                render_text(
                    getattr(t.buttons, attr_name),
                    **LABEL_TEXT_SETTINGS,
                ),

                button_name = attr_name,

            )

            for attr_name in (
                'copy_data',
                'erase_data',
                'go_back',
            )
        )

    def get_translated_text(self):

        return (

            t.two_button_explanation,

            *yield_paragraphs(t.first_button_explanation),
            *yield_paragraphs(t.second_button_explanation),

        )


    def prepare(self):

        self.message_labels.rect.snap_rects_ip(
            retrieve_pos_from='bottomleft',
            assign_pos_to='topleft',
        )

        self.buttons.rect.snap_rects_ip(
            retrieve_pos_from='midbottom',
            assign_pos_to='midtop',
        )

        ###

        self.caption.rect.midtop = SCREEN_RECT.move(0, 2).midtop
        self.message_labels.rect.midtop = self.caption.rect.move(0, 10).midbottom
        self.buttons.rect.midtop = self.message_labels.rect.move(0, 10).midbottom

        ###

        self.widgets.clear()

        self.widgets.extend(

            (
                self.caption,
                self.message_labels,
                self.buttons,
            )

        )

        self.current_index = None
        self.highlighted_widget = None

    ### TODO keep working from this spot (there might be stuff before this
    ### point that needs to be updated, but I don't think so)

    def control(self):
        
        for event in SERVICES_NS.get_events():

            if event.type == KEYDOWN:

                if event.key == K_ESCAPE:
                    self.go_back()

                elif event.key in (K_UP, K_DOWN):

                    increment = -1 if event.key == K_UP else 1

                    self.current_index = (
                        (self.current_index + increment)
                        % self.item_count
                    )

                    self.highlighted_widget = (
                        self.widgets[self.current_index]
                    )

                elif event.key == K_RETURN:

                    self.highlighted_widget.command()


            elif event.type == JOYBUTTONDOWN:

                if event.button == GAMEPAD_CONTROLS['start_button']:

                    self.highlighted_widget.command()

            elif event.type == GAMEPADDIRECTIONALPRESSED:

                if event.direction in ('up', 'down'):

                    increment = -1 if event.direction == 'up' else 1

                    self.current_index = (
                        (self.current_index + increment)
                        % self.item_count
                    )

                    self.highlighted_widget = (
                        self.widgets[self.current_index]
                    )

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

        options_screen = REFS.states.options_screen
        options_screen.prepare()

        raise LoopException(next_state=options_screen)

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
        """Do nothing."""

    def draw(self):

        blit_on_screen(BLACK_BG, (0, 0))

        self.caption.draw()
        self.message_labels.draw()
        self.widgets.draw()

        draw_rect(
            SCREEN,
            'orange',
            self.highlighted_widget.rect,
            1,
        )

        update()


def yield_paragraphs(t):

    for i in count():

        parag_attr_name = 'paragraph' + str(i).rjust(2, '0')

        try:
            yield getattr(t, parag_attr_name)

        except AttributeError:
            return
