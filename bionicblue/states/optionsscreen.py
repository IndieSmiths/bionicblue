

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

from ..config import REFS, quit_game

from ..pygamesetup import SERVICES_NS

from ..pygamesetup.constants import (
    SCREEN,
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

from ..userprefsman.main import save_config_on_disk

from ..exceptions import SwitchStateException, BackToBeginningException

from ..widgets.slider import HundredSlider
from ..widgets.checkbutton import Checkbutton



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



class OptionsScreen:

    def __init__(self):

        ###

        reset_button, back_button = (

            UIObject2D.from_surface(
                render_text(
                    text,
                    **LABEL_TEXT_SETTINGS,
                )
            )

            for text in ('Reset to defaults', 'Back')

        )

        back_button.command = self.go_back

        self.reset_button = reset_button
        self.back_button = back_button

        self.non_option_buttons = frozenset((reset_button, back_button))

        ###

        labels = self.option_labels = UIList2D()
        widgets = self.widgets = UIList2D()
        rows = self.widget_rows = UIList2D()

        for key, text, widget_class, value in (
            ('MASTER_VOLUME', "Master volume", HundredSlider, 100),
            ('MUSIC_VOLUME', "Music volume", HundredSlider, 100),
            ('SFX_VOLUME', "Sound volume", HundredSlider, 100),
            ('FULLSCREEN', "Enable full screen", Checkbutton, True),
            ('SAVE_PLAYTEST_DATA', "Save playtest data", Checkbutton, True),
        ):

            ###

            widget = (

                widget_class(
                    value=value,
                    on_value_change=self.update_value_from_changed_widget,
                )

            )
            widgets.append(widget)

            ###

            label = (

                UIObject2D.from_surface(
                    render_text(
                        text,
                        **LABEL_TEXT_SETTINGS,
                    ),
                )
            )
            labels.append(label)

            ###
            rows.append(UISet2D((label, widget)))

        ###

        widgets.append(back_button)
        widgets.append(reset_button)

        self.widgets_to_update = [
            widget
            for widget in widgets
            if hasattr(widget, 'update')
        ]

        rows.append(UISet2D([back_button]))
        rows.append(UISet2D([reset_button]))

        ###
        self.item_count = len(widgets)

        ###

        option_caption_label = self.option_caption_label = (
            UIObject2D.from_surface(
                render_text('Option', **TITLE_TEXT_SETTINGS)
            )
        )

        value_caption_label = self.value_caption_label = (
            UIObject2D.from_surface(
                render_text('Value', **TITLE_TEXT_SETTINGS)
            )
        )

        ###

        value_caption_label.rect.topleft = SCREEN_RECT.move(5, 2).midtop

        option_caption_label.rect.midright = (
            value_caption_label.rect.move(-10, 0).midleft
        )

        ###

        widgets.rect.snap_rects_ip(
            retrieve_pos_from='bottomleft',
            assign_pos_to='topleft',
            offset_pos_by=(0, 4),
        )

        widgets.rect.topleft = value_caption_label.rect.move(0, 2).bottomleft

        for label, widget in zip(labels, widgets):
            label.rect.midright = widget.rect.move(-10, 0).midleft

    def update_value_from_changed_widget(self):
        ...

    def prepare(self):
        
        self.current_index = 0
        self.highlighted_widget = self.widgets[self.current_index]

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

                    try:
                        command = self.highlighted_widget.command

                    except AttributeError:

                        try:
                            on_mouse_click = self.highlighted_widget.on_mouse_click
                        except AttributeError:
                            pass

                        else:
                            on_mouse_click(event)

                    else:
                        command()

            elif event.type == JOYBUTTONDOWN:

                if event.button == GAMEPAD_CONTROLS['start_button']:

                    try:
                        command = self.highlighted_widget.command
                    except AttributeError:
                        pass
                    else:
                        command()

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

        main_menu = REFS.states.main_menu
        main_menu.prepare()

        raise SwitchStateException(main_menu)

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

        for widget in self.widgets_to_update:
            widget.update()
        
    def draw(self):

        blit_on_screen(BLACK_BG, (0, 0))

        self.option_caption_label.draw()
        self.option_labels.draw()

        self.value_caption_label.draw()
        self.widgets.draw()

        draw_rect(
            SCREEN,
            'orange',
            self.highlighted_widget.rect,
            1,
        )

        update()

