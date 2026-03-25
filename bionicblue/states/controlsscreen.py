"""Facility to allow users to set keys/buttons for actions."""

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
    SCREEN_RECT,
    BLACK_BG,
    GAMEPADDIRECTIONALPRESSED,
    GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS,
    blit_on_screen,
)

from ..pygamesetup.gamepaddirect import setup_gamepad_if_existent

from ..ourstdlibs.behaviour import do_nothing

from ..classes2d.single import UIObject2D

from ..classes2d.collections import UIList2D

from ..textman import render_text, update_text_surface

from ..surfsman import unite_surfaces

from ..userprefsman.main import (
    KEYBOARD_CONTROL_NAMES,
    KEYBOARD_CONTROLS,
    GAMEPAD_CONTROLS,
    DEFAULT_KEYBOARD_CONTROL_NAMES,
    DEFAULT_GAMEPAD_CONTROLS,
    ALL_ACTION_KEYS,
    KEYBOARD_ACTION_KEYS,
    GAMEPAD_ACTION_KEYS,
    save_config_on_disk,
)

from ..userprefsman.validation import PYGAME_KEYS_NAME_MAP, RESERVED_KEYS

from ..promptscreen import present_prompt

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
    'size': 12,
    'padding': 1,
    'foreground_color': 'white',
    'background_color': 'black',
    
}

PROMPT_LABEL_TEXT_SETTINGS = {
    'style': 'regular',
    'size': 12,
    'padding': 1,
    'foreground_color': 'white',
    'background_color': 'red',
}

t = TRANSLATIONS.controls_screen


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

            for text in (
                TRANSLATIONS.general.reset_to_defaults,
                TRANSLATIONS.general.go_back,
            )
        )

        back_button.command = self.go_back

        self.reset_button = reset_button
        self.back_button = back_button

        self.non_control_buttons = frozenset((reset_button, back_button))

        ###

        action_caption_label = self.action_caption_label = (
            UIObject2D.from_surface(
                render_text(t.action, **TITLE_TEXT_SETTINGS)
            )
        )

        action_caption_label.rect.top = SCREEN_RECT.top + 10

        control_caption_label = self.control_caption_label = (
            UIObject2D.from_surface(
                render_text(t.trigger, **TITLE_TEXT_SETTINGS)
            )
        )

        control_caption_label.rect.top = SCREEN_RECT.top + 10

        ###


        self.groups_map = gm = {}

        action_names = t.action_names

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
                        getattr(action_names, key) + ':',
                        **LABEL_TEXT_SETTINGS,
                    ),
                    key=key,

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

            control_labels.rect.top = control_caption_label.rect.move(0, 10).bottom
            control_labels.rect.left = SCREEN_RECT.centerx

            for action, respective_control in zip(action_labels, control_labels):
                action.rect.midright = respective_control.rect.move(-10, 0).midleft

            ###
            submap['item_count'] = len(control_labels)

        ###

        action_caption_label.rect.right = action_labels.rect.right
        control_caption_label.rect.left = control_labels.rect.left

        ###
        gp = self.general_prompt = (
            UIObject2D.from_surface(recreate_general_prompt_surf())

        )

        screen_center = SCREEN_RECT.center

        gp.rect.midbottom = screen_center

        self.prompt_label_map = {

            key: UIObject2D.from_surface(
                              render_text(
                                "'" + getattr(action_names, key) + "'",
                                **PROMPT_LABEL_TEXT_SETTINGS,
                              ),
                              coordinates_name='midtop',
                              coordinates_value=screen_center,
                              key=key,
                            )

            for key in ALL_ACTION_KEYS

        }

        ###
        on_language_change.append(self.on_language_change)

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

    def on_language_change(self):

        ### update general labels

        for obj, text, text_settings, pos_to_align in (

            (
                self.reset_button,
                TRANSLATIONS.general.reset_to_defaults,
                LABEL_TEXT_SETTINGS,
                'midleft',
            ),

            (
                self.back_button,
                TRANSLATIONS.general.go_back,
                LABEL_TEXT_SETTINGS,
                'midleft',
            ),

            (
                self.action_caption_label,
                t.action,
                TITLE_TEXT_SETTINGS,
                'topright',
            ),

            (
                self.control_caption_label,
                t.trigger,
                TITLE_TEXT_SETTINGS,
                'topleft',
            ),


        ):
            update_text_surface(obj, text, text_settings, pos_to_align)

        ### update action and control labels

        action_names = t.action_names

        for controls_type, submap in self.groups_map.items():

            ## action labels

            for obj in submap['action_labels']:

                update_text_surface(
                    obj,
                    getattr(action_names, obj.key) + ':',
                    LABEL_TEXT_SETTINGS,
                    pos_to_align='midright',
                )


            ## control labels

            if controls_type == 'kbd_controls':

                control_formatter = str_from_keyboard_control
                controls = KEYBOARD_CONTROL_NAMES

            else:

                control_formatter = str_from_gamepad_control
                controls = GAMEPAD_CONTROLS

            for obj in submap['control_labels']:

                if not hasattr(obj, 'key'):
                    continue

                update_text_surface(
                    obj,
                    control_formatter(controls[obj.key]),
                    LABEL_TEXT_SETTINGS,
                    pos_to_align='midleft',
                )

        ### update general prompt

        gp = self.general_prompt
        gp.image = recreate_general_prompt_surf()
        gp.rect = gp.image.get_rect()
        gp.rect.midbottom = SCREEN_RECT.center


        ### update prompt labels

        for obj in self.prompt_label_map.values():

            update_text_surface(
                obj,
                "'" + getattr(action_names, obj.key) + "'",
                PROMPT_LABEL_TEXT_SETTINGS,
                pos_to_align='midtop'
            )

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

        must_reset = present_prompt(

            t.prompts.resetting_to_defaults.caption,
            t.prompts.resetting_to_defaults.message,

            (
                (TRANSLATIONS.general.no, False),
                (TRANSLATIONS.general.yes, True),
            ),

        )

        if not must_reset:
            return

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

        must_reset = present_prompt(

            t.prompts.resetting_to_defaults.caption,
            t.prompts.resetting_to_defaults.message,

            (
                (TRANSLATIONS.general.no, False),
                (TRANSLATIONS.general.yes, True),
            ),

        )

        if not must_reset:
            return

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

                present_prompt(
                    t.prompts.reserved_trigger.caption,
                    t.prompts.reserved_trigger.message,
                    (
                        (TRANSLATIONS.general.ok, True),
                    ),
                )

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

            present_prompt(
                t.prompts.already_set.caption,
                t.prompts.already_set.message,
                (
                    (TRANSLATIONS.general.ok, True),
                ),
            )

        elif any(
            new_value == control_label.value
            for control_label in self.control_labels
            if control_label not in non_control_buttons
        ):

            present_prompt(
                t.prompts.used_by_another.caption,
                t.prompts.used_by_another.message,
                (
                    (TRANSLATIONS.general.ok, True),
                ),
            )

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

        SCREEN.fill('black')
        self.general_prompt.draw()
        self.prompt_label.draw()

        update()


def recreate_general_prompt_surf():

    prompt_words = UIList2D(

        UIObject2D.from_surface(
            render_text(word, 'regular', 12, 1, 'orange', 'black')
        )

        for word in t.press_trigger_to_assign.split()

    )

    prompt_words.rect.snap_rects_intermittently_ip(

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

    return (

        unite_surfaces(

            surface_rect_pairs = [
                (word_obj.image, word_obj.rect)
                for word_obj in prompt_words
            ],

            padding=3,
            background_color='black',

        )

    )

def str_from_keyboard_control(control):
    return t.keyboard_key + ' ' + control[2:].upper()

def str_from_gamepad_control(control):

    return (

        '--'
        if control is None

        else t.gamepad + ' ' + str(control)

    )
