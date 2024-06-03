

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

from ..ourstdlibs.behaviour import do_nothing

from ..classes2d.single import UIObject2D

from ..classes2d.collections import UIList2D

from ..textman import render_text

from ..userprefsman.main import save_config_on_disk

from ..exceptions import SwitchStateException, BackToBeginningException



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

OPTIONS_WIDGETS_MAP = {
    "MASTER_VOLUME": Slider,
    "MUSIC_VOLUME": Slider,
    "SFX_VOLUME": Slider,
    "FULLSCREEN": Checkbutton,
    "SAVE_PLAYTEST_DATA": Checkbutton,
}



class OptionsScreen:

    def __init__(self):

        ###
        self.update = do_nothing

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

        option_labels = self.option_labels = UIList2D(

            UIObject2D.from_surface(
                render_text(
                    text,
                    **LABEL_TEXT_SETTINGS,
                ),
            )

            for text in option_texts

        )

        option_caption_label = self.option_caption_label = (
            UIObject2D.from_surface(
                render_text('Option', **TITLE_TEXT_SETTINGS)
            )
        )

        option_caption_label.rect.right = option_labels.rect.right
        option_caption_label.rect.top = SCREEN_RECT.top + 10

        value_caption_label = self.value_caption_label = (
            UIObject2D.from_surface(
                render_text('Value', **TITLE_TEXT_SETTINGS)
            )
        )

        value_caption_label.rect.left = widgets.rect.left
        value_caption_label.rect.top = SCREEN_RECT.top + 10

        ###

        widgets.append(back_button)
        widgets.append(reset_button)


        widgets.rect.snap_rects_ip(
            retrieve_pos_from='bottomleft',
            assign_pos_to='topleft',
        )

        widgets.rect.bottomleft = SCREEN_RECT.move(5, -10).midbottom

        for label, widget in zip(option_labels, widgets):
            label.rect.midright = widget.rect.move(-10, 0).midleft

        ###
        screen_center = SCREEN_RECT.center


    def prepare(self, controls_type):
        
        self.current_index = 0
        self.highlighted_control = self.control_labels[self.current_index]

        ###

        self.control = self.control_selection
        self.draw = self.draw_controls

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

                    self.highlighted_control = (
                        self.control_labels[self.current_index]
                    )

                elif event.key == K_RETURN:
                    self.highlighted_control.command()

            elif event.type == JOYBUTTONDOWN:

                if event.button == GAMEPAD_CONTROLS['start_button']:
                    self.highlighted_control.command()

            elif event.type == GAMEPADDIRECTIONALPRESSED:

                if event.direction in ('up', 'down'):

                    increment = -1 if event.direction == 'up' else 1

                    self.current_index = (
                        (self.current_index + increment)
                        % self.item_count
                    )

                    self.highlighted_control = (
                        self.control_labels[self.current_index]
                    )

            elif event.type == MOUSEBUTTONDOWN:

                if event.button == 1:
                    self.act_if_control_under_mouse(event)

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

    def act_if_control_under_mouse(self, event):

        pos = event.pos

        for index, obj in enumerate(self.control_labels):

            if obj.rect.collidepoint(pos):

                self.current_index = index
                self.highlighted_control = obj

                obj.command()

                break

    def highlight_under_mouse(self, event):

        pos = event.pos

        for index, obj in enumerate(self.control_labels):

            if obj.rect.collidepoint(pos):

                self.current_index = index
                self.highlighted_control = obj

                break

    def try_setting_new_control(self, event):

        is_key = event.type == KEYDOWN

        if is_key:
            new_value = PYGAME_KEYS_NAME_MAP[event.key]


        else:
            new_value = event.button

        ####

        highlighted_control = self.highlighted_control

        action_key = highlighted_control.key
        old_value = highlighted_control.value

        ###

        non_option_buttons = self.non_option_buttons

        if new_value == old_value:
            self.show_dialog('already_set')

        elif any(
            new_value == control_label.value
            for control_label in self.control_labels
            if control_label not in non_option_buttons
        ):
            self.show_dialog('used_by_another')

        else:

            if is_key:

                KEYBOARD_CONTROL_NAMES[action_key] = new_value
                KEYBOARD_CONTROLS[action_key] = event.key

                new_text = str_from_keyboard_control(new_value)

            else:

                GAMEPAD_CONTROLS[action_key] = new_value
                new_text = str_from_gamepad_control(new_value)

            ###

            new_control_surf = render_text(new_text, **LABEL_TEXT_SETTINGS)

            highlighted_control.image = new_control_surf
            highlighted_control.rect.size = new_control_surf.get_size()

            highlighted_control.value = new_value

            ###
            save_config_on_disk()

            ###

            self.control = self.control_selection
            self.draw = self.draw_controls

            raise BackToBeginningException

    def draw(self):

        blit_on_screen(BLACK_BG, (0, 0))

        self.option_caption_label.draw()
        self.option_labels.draw()

        self.value_caption_label.draw()
        self.widgets.draw()

        draw_rect(
            SCREEN,
            'orange',
            self.highlighted_control.rect,
            1,
        )

        update()

