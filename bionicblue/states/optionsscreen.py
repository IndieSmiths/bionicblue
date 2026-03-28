"""Facility for options screen."""

### standard library import

from random import choice

from functools import partial


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

from ..config import REFS, SOUND_MAP, LoopException, quit_game

from ..pygamesetup import SERVICES_NS

from ..pygamesetup.constants import (
    SCREEN,
    SIZE,
    SCREEN_COPY,
    SCREEN_RECT,
    BLACK_BG,
    GAMEPADDIRECTIONALPRESSED,
    GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS,
    blit_on_screen,
)

from ..pygamesetup.gamepaddirect import setup_gamepad_if_existent

from ..classes2d.single import UIObject2D

from ..classes2d.collections import UIList2D, UISet2D

from ..textman import render_text, update_text_surface

from ..userprefsman.main import (
    USER_PREFS,
    DEFAULT_USER_PREFS,
    save_config_on_disk,
)

from ..translatedtext import TRANSLATIONS, on_language_change

from ..widget.slider import HundredSlider
from ..widget.checkbutton import Checkbutton
from ..widget.languagepicker import LanguagePicker



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

t = TRANSLATIONS.options_screen


class OptionsScreen:

    def __init__(self):

        ###

        (
          data_button,
          reset_button,
          back_button,
        ) = self.non_option_buttons = [

            UIObject2D.from_surface(
                render_text(
                    text,
                    **LABEL_TEXT_SETTINGS,
                ),
            )

            for text in (
                t.data_screen,
                TRANSLATIONS.general.reset_to_defaults,
                TRANSLATIONS.general.go_back,
            )

        ]

        data_button.command = self.to_data_screen
        reset_button.command = self.reset_to_defaults
        back_button.command = self.go_back

        ###

        labels = self.option_labels = UIList2D()
        widgets = self.widgets = UIList2D()

        for key, label_text, widget_class in (
            ('MASTER_VOLUME', t.options.master_volume, HundredSlider),
            ('MUSIC_VOLUME', t.options.music_volume, HundredSlider),
            ('SOUND_VOLUME', t.options.sound_volume, HundredSlider),
            ('FULLSCREEN', t.options.full_screen, Checkbutton),
            ('LOCALE', t.options.language, LanguagePicker),
        ):

            ###

            widget = (

                widget_class(
                    value=USER_PREFS[key],
                    name=key,
                    on_value_change=self.update_value_from_changed_widget,
                )

            )

            widgets.append(widget)

            ###

            label = (

                UIObject2D.from_surface(
                    render_text(
                        label_text,
                        **LABEL_TEXT_SETTINGS,
                    ),
                )
            )
            labels.append(label)


        ###

        widgets.extend(self.non_option_buttons)

        self.widgets_to_update = tuple(
            widget
            for widget in widgets
            if hasattr(widget, 'update')
        )

        ###
        self.item_count = len(widgets)

        ###

        option_caption_label = self.option_caption_label = (
            UIObject2D.from_surface(
                render_text(t.captions.option, **TITLE_TEXT_SETTINGS)
            )
        )

        value_caption_label = self.value_caption_label = (
            UIObject2D.from_surface(
                render_text(t.captions.value, **TITLE_TEXT_SETTINGS)
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

        ### center objs
        self.center_objs_on_screen()

        ### append callback to replace text surfaces when language changes
        on_language_change.append(self.on_language_change)

    def prepare(self):
        
        self.current_index = 0
        self.highlighted_widget = self.widgets[self.current_index]

        if not hasattr(self, 'shot_sound_names'):

            self.shot_sound_names = tuple(
                sound_name
                for sound_name in SOUND_MAP
                if 'shot' in sound_name
            )

    def on_language_change(self):
        
        ### captions

        for obj, text, attr_name in (
            (self.option_caption_label, t.captions.option, 'topright'),
            (self.value_caption_label, t.captions.value, 'topleft'),
        ):

            update_text_surface(
                obj,
                text,
                TITLE_TEXT_SETTINGS,
                pos_to_align=attr_name,
            )

        ### labels

        for label_obj, label_text in zip(

            self.option_labels,

            (
              t.options.master_volume,
              t.options.music_volume,
              t.options.sound_volume,
              t.options.full_screen,
              t.options.language,
            ),

        ):

            update_text_surface(
                label_obj,
                label_text,
                LABEL_TEXT_SETTINGS,
                pos_to_align='midright',
            )


        ### non option buttons

        for button, text in zip(

            self.non_option_buttons,

            (
                t.data_screen,
                TRANSLATIONS.general.reset_to_defaults,
                TRANSLATIONS.general.go_back,
            ),

        ):

            update_text_surface(
                button,
                text,
                LABEL_TEXT_SETTINGS,
                pos_to_align='midleft',
            )

        ### center objs
        self.center_objs_on_screen()

    def center_objs_on_screen(self):
        """Offset everything so they are more or less centered on the screen."""

        all_objs = UIList2D(
            (
                self.option_labels,
                self.widgets,
                self.option_caption_label,
                self.value_caption_label,
            )
        )

        diff = tuple(
            a - b
            for a, b in zip(SCREEN_RECT.center, all_objs.rect.center)
        )

        all_objs.rect.move_ip(diff)

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

                elif event.key in (K_LEFT, K_RIGHT):

                    hw = self.highlighted_widget

                    if isinstance(hw, HundredSlider):

                        if event.key == K_LEFT:
                            hw.decrement()

                        else:
                            hw.increment()

                    elif isinstance(hw, Checkbutton):
                        hw.toggle_value()

                elif event.key == K_RETURN:

                    hw = self.highlighted_widget

                    if hasattr(hw, 'command'):
                        hw.command()

                    elif hasattr(hw, 'on_mouse_click'):
                        hw.on_mouse_click(event)


            elif event.type == JOYBUTTONDOWN:

                if event.button == GAMEPAD_CONTROLS['start_button']:

                    hw = self.highlighted_widget

                    if hasattr(hw, 'command'):
                        hw.command()

                    elif hasattr(hw, 'on_mouse_click'):
                        hw.on_mouse_click(event)


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

                elif event.direction in ('left', 'right'):

                    hw = self.highlighted_widget

                    if isinstance(hw, HundredSlider):

                        if event.direction == 'left':
                            hw.decrement()

                        else:
                            hw.increment()

                    elif isinstance(hw, Checkbutton):
                        hw.toggle_value()

            elif event.type == MOUSEBUTTONDOWN:

                if event.button == 1:
                    self.on_mouse_click(event)

            elif event.type == MOUSEMOTION:
                self.highlight_under_mouse(event)

            elif event.type in GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS:
                setup_gamepad_if_existent()

            elif event.type == QUIT:
                quit_game()

    def reset_to_defaults(self):

        ###

        for key, value in DEFAULT_USER_PREFS.items():

            ### if value is not a dict, we override it
            ###
            ### we ignore dicts cause they contain keyboard or
            ### gamepad controls, and those should be set/reset
            ### from the dedicated keyboard control or gamepad
            ### control screens

            if not isinstance(value, dict):
                USER_PREFS[key] = value

        ###
        save_config_on_disk()

    def update_value_from_changed_widget(self):

        for widget in self.widgets:

            ### ignore widgets which don't have a 'get' method

            if not hasattr(widget, 'get'):
                continue

            ### otherwise check whether its value changed,
            ### taking appropriate measures if so

            value = widget.get()
            option_key = widget.name

            if value != USER_PREFS[option_key]:

                ## update value in user preferences
                USER_PREFS[option_key] = value

                ## setup system so new value is taken into account
                self.update_system_for_option(option_key)

                ## save on disk
                save_config_on_disk()

                if option_key == 'LOCALE':
                    
                    ## perform setups in response to language change
                    on_language_change()

                break

    def update_system_for_option(self, option_key):

        if option_key == 'MASTER_VOLUME':

            self.update_music_volume()
            self.update_sound_volume()

        elif option_key == 'MUSIC_VOLUME':
            self.update_music_volume()

        elif option_key == 'SOUND_VOLUME':
            self.update_sound_volume()

        elif option_key == 'FULLSCREEN':

            flag = SCALED | (FULLSCREEN if USER_PREFS['FULLSCREEN'] else 0)
            set_mode(SIZE, flag)

    def update_music_volume(self):

        music_volume = (
            (USER_PREFS['MASTER_VOLUME']/100)
            * (USER_PREFS['MUSIC_VOLUME']/100)
        )

        music.set_volume(music_volume)

    def update_sound_volume(self):

        sound_volume = (
            (USER_PREFS['MASTER_VOLUME'] / 100)
            * (USER_PREFS['SOUND_VOLUME'] / 100)
        )

        for sound in SOUND_MAP.values():
            sound.set_volume(sound_volume)

        if not get_busy():
            SOUND_MAP[choice(self.shot_sound_names)].play()

    def go_back(self):

        main_menu = REFS.states.main_menu
        main_menu.prepare()

        raise LoopException(next_state=main_menu)

    def to_data_screen(self):
        """Go to data screen."""

        data_screen = REFS.states.data_screen 
        data_screen.prepare()

        raise LoopException(next_state=data_screen)

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

