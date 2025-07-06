

### third-party imports

from pygame import locals as pygame_locals

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

from ..config import REFS, LoopException, quit_game

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

from ..surfsman import combine_surfaces

from ..userprefsman.main import (
    KEYBOARD_CONTROL_NAMES,
    KEYBOARD_CONTROLS,
    GAMEPAD_CONTROLS,
    DEFAULT_KEYBOARD_CONTROL_NAMES,
    DEFAULT_GAMEPAD_CONTROLS,
    save_config_on_disk,
)

from ..userprefsman.validation import PYGAME_KEYS_NAME_MAP, RESERVED_KEYS



ACTION_TITLE_MAP = {
    'up': 'Up',
    'down': 'Down',
    'left': 'Left',
    'right': 'Right',

    'shoot': 'Shoot',
    'jump': 'Jump',

    'previous_power': 'Previous power',
    'next_power': 'Next power',

    'start_button': 'Start/confirm',
}


KEYBOARD_ACTION_KEYS = (

    'up',
    'down',
    'left',
    'right',

    'shoot',
    'jump',

    'previous_power',
    'next_power',

)

GAMEPAD_ACTION_KEYS = (

    'shoot',
    'jump',

    'previous_power',
    'next_power',

    'start_button',

)


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



class ControlsScreen:

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

        self.non_control_buttons = frozenset((reset_button, back_button))

        ###

        
        self.groups_map = gm = {}

        for controls_type, action_keys, controls, control_formatter in (

            (
                'kbd_controls',
                KEYBOARD_ACTION_KEYS,
                KEYBOARD_CONTROL_NAMES,
                str_from_keyboard_control,
            ),

            (
                'gp_controls',
                GAMEPAD_ACTION_KEYS,
                GAMEPAD_CONTROLS,
                str_from_gamepad_control,
            ),
        ):

            submap = gm[controls_type] = {}

            action_labels = submap['action_labels'] = UIList2D(

                UIObject2D.from_surface(
                    render_text(
                        f'{ACTION_TITLE_MAP[key]}:',
                        **LABEL_TEXT_SETTINGS,
                    ),
                )

                for key in action_keys

            )

            control_labels = submap['control_labels'] = UIList2D(

                UIObject2D.from_surface(
                    render_text(
                        control_formatter(controls[key]),
                        **LABEL_TEXT_SETTINGS,
                    ),
                    key=key,
                    value=controls[key],
                    command=self.wait_for_new_control,
                )

                for key in action_keys

            )

            control_labels.append(back_button)
            control_labels.append(reset_button)


            control_labels.rect.snap_rects_ip(
                retrieve_pos_from='bottomleft',
                assign_pos_to='topleft',
            )

            control_labels.rect.bottomleft = SCREEN_RECT.move(5, -10).midbottom

            for action, respective_control in zip(action_labels, control_labels):
                action.rect.midright = respective_control.rect.move(-10, 0).midleft

            ###
            submap['item_count'] = len(control_labels)

        ###

        action_caption_label = self.action_caption_label = (
            UIObject2D.from_surface(
                render_text('Action', **TITLE_TEXT_SETTINGS)
            )
        )

        action_caption_label.rect.right = action_labels.rect.right
        action_caption_label.rect.top = SCREEN_RECT.top + 10

        control_caption_label = self.control_caption_label = (
            UIObject2D.from_surface(
                render_text('Trigger', **TITLE_TEXT_SETTINGS)
            )
        )

        control_caption_label.rect.left = control_labels.rect.left
        control_caption_label.rect.top = SCREEN_RECT.top + 10

        ###


        general_prompt_surf = (

            combine_surfaces(

                surfaces=[

                    render_text(line, 'regular', 18, 1, 'white', 'blue')

                    for line in (
                        "Press any trigger to assign",
                        "it to the following action:",
                    )

                ],

                retrieve_pos_from='bottomleft',
                assign_pos_to='topleft',
                padding=3,
                background_color='blue',
            )

        )

        screen_center = SCREEN_RECT.center

        gp = self.general_prompt = UIObject2D.from_surface(general_prompt_surf)
        gp.rect.midbottom = screen_center

        self.prompt_label_map = {

            key: UIObject2D.from_surface(
                              render_text(
                                f"'{action_title}'",
                                'regular',
                                18,
                                1,
                                'white',
                                'blue',
                              ),
                              coordinates_name='midtop',
                              coordinates_value=screen_center,
                            )

            for key, action_title in ACTION_TITLE_MAP.items()

        }

        ###

        self.dialog_map = dm = {}

        for dialog_name, lines in (

            (

                'reserved',

                (
                    "This is a reserved",
                    "trigger. Please, use",
                    "another one",
                ),

            ),

            (

                'used_by_another',

                (
                    "This trigger is being used",
                    "for another action",
                ),
            ),

            (

                'already_set',

                (
                    "This trigger is already set",
                    "for this action",
                ),
            ),

        ):


            dialog_surfs = tuple(

                render_text(line, 'regular', 18, 1, 'white', 'red')
                for line in lines

            )

            dialog_surf = (
                combine_surfaces(
                    surfaces=dialog_surfs,
                    retrieve_pos_from='bottomleft',
                    assign_pos_to='topleft',
                    padding=3,
                    background_color='red',
                )
            )

            draw_rect(dialog_surf, 'white', dialog_surf.get_rect(), 1)

            dialog_obj = dialog_obj = UIObject2D.from_surface(dialog_surf)
            dialog_obj.rect.center = screen_center
            dm[dialog_name] = dialog_obj


    def prepare(self, controls_type):
        
        submap = self.groups_map[controls_type]

        self.action_labels = submap['action_labels']
        self.control_labels = submap['control_labels']
        self.item_count = submap['item_count']

        if controls_type == 'kbd_controls':

            self.control_event = KEYDOWN
            self.reset_button.command = self.reset_keyboard_controls


        else:

            self.control_event = JOYBUTTONDOWN
            self.reset_button.command = self.reset_gamepad_controls

        self.current_index = 0
        self.highlighted_control = self.control_labels[self.current_index]

        ###

        back_button = self.back_button
        reset_button = self.reset_button

        back_button.rect.topleft = self.control_labels[-3].rect.bottomleft
        reset_button.rect.topleft = back_button.rect.bottomleft

        ###

        self.control = self.control_selection
        self.draw = self.draw_controls

    def control_selection(self):
        
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

        raise LoopException(next_state=main_menu)

    def act_if_control_under_mouse(self, event):

        pos = event.pos

        for index, obj in enumerate(self.control_labels):

            if obj.rect.collidepoint(pos):

                self.current_index = index
                self.highlighted_control = obj

                obj.command()

                break

    def reset_keyboard_controls(self):
        """Reset current controls to defaults."""

        ### reset controls to defaults

        for obj in self.control_labels:

            if hasattr(obj, 'key'):

                ### reset control

                action_key = obj.key

                key_name = DEFAULT_KEYBOARD_CONTROL_NAMES[action_key]

                KEYBOARD_CONTROL_NAMES[action_key] = key_name

                KEYBOARD_CONTROLS[action_key] = (
                    getattr(pygame_locals, key_name)
                )

                obj.value = key_name

                ### update control surface

                new_text = str_from_keyboard_control(key_name)

                new_surf = render_text(new_text, **LABEL_TEXT_SETTINGS)
                obj.image = new_surf
                obj.rect.size = new_surf.get_size()

        ### save configurations
        save_config_on_disk()

    def reset_gamepad_controls(self):
        """Reset current controls to defaults."""

        ### reset controls to defaults

        for obj in self.control_labels:

            if hasattr(obj, 'key'):

                ### reset control

                action_key = obj.key

                value = DEFAULT_GAMEPAD_CONTROLS[action_key]

                GAMEPAD_CONTROLS[action_key] = value

                obj.value = value

                ### update control surface

                new_text = str_from_gamepad_control(value)

                new_surf = render_text(new_text, **LABEL_TEXT_SETTINGS)
                obj.image = new_surf
                obj.rect.size = new_surf.get_size()

        ### save configurations
        save_config_on_disk()

    def highlight_under_mouse(self, event):

        pos = event.pos

        for index, obj in enumerate(self.control_labels):

            if obj.rect.collidepoint(pos):

                self.current_index = index
                self.highlighted_control = obj

                break

    def wait_for_new_control(self):

        self.control = self.control_wait_trigger
        self.draw = self.draw_prompt

        SCREEN_COPY.blit(SCREEN, (0, 0))

        self.prompt_label = (
            self.prompt_label_map[self.highlighted_control.key]
        )

        raise LoopException

    def control_wait_trigger(self):

        for event in SERVICES_NS.get_events():

            if event.type == KEYDOWN and event.key == K_ESCAPE:

                self.control = self.control_selection
                self.draw = self.draw_controls

                raise LoopException

            elif (
                event.type == KEYDOWN
                and PYGAME_KEYS_NAME_MAP[event.key] in RESERVED_KEYS
            ):
                self.show_dialog('reserved')

            elif event.type == self.control_event:
                self.try_setting_new_control(event)

            elif event.type in GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS:
                setup_gamepad_if_existent()

            elif event.type == QUIT:
                quit_game()


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

        non_control_buttons = self.non_control_buttons

        if new_value == old_value:
            self.show_dialog('already_set')

        elif any(
            new_value == control_label.value
            for control_label in self.control_labels
            if control_label not in non_control_buttons
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

            raise LoopException

    def draw_controls(self):

        blit_on_screen(BLACK_BG, (0, 0))

        self.action_caption_label.draw()
        self.action_labels.draw()

        self.control_caption_label.draw()
        self.control_labels.draw()

        draw_rect(
            SCREEN,
            'orange',
            self.highlighted_control.rect,
            1,
        )

        update()

    def draw_prompt(self):

        blit_on_screen(SCREEN_COPY, (0, 0))

        self.general_prompt.draw()
        self.prompt_label.draw()

        update()

    def show_dialog(self, dialog_name):

        self.control = self.control_dialog
        self.draw = self.draw_dialog

        self.dialog_obj = self.dialog_map[dialog_name]

        raise LoopException

    def control_dialog(self):

        for event in SERVICES_NS.get_events():

            if event.type in KEYBOARD_OR_GAMEPAD_PRESSED_EVENTS:

                self.control = self.control_selection
                self.draw = self.draw_controls

                raise LoopException

            elif event.type in GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS:
                setup_gamepad_if_existent()

            elif event.type == QUIT:
                quit_game()


    def draw_dialog(self):

        blit_on_screen(SCREEN_COPY, (0, 0))
        self.dialog_obj.draw()
        update()



def str_from_keyboard_control(control):
    return f'Keyboard {control[2:].upper()}'


def str_from_gamepad_control(control):

    return (

        '--'
        if control is None

        else f'Gamepad {control}'

    )
