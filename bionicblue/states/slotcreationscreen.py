"""Facility for creating new save slot.

That is, for player to enter name for new save slot.
"""

### standard library imports

from string import ascii_uppercase, ascii_lowercase, digits

from functools import partialmethod


### third-party imports

from pygame.locals import (

    QUIT,

    KEYDOWN,
    K_ESCAPE,
    K_RETURN,
    K_BACKSPACE,
    K_SPACE,
    K_UP,
    K_DOWN,
    K_LEFT,
    K_RIGHT,
    TEXTINPUT,

    JOYBUTTONDOWN,

)

from pygame.display import update

from pygame.draw import rect as draw_rect

from pygame.key import start_text_input, stop_text_input


### local imports

from ..config import (
    REFS,
    SAVE_SLOTS_DIR,
    SOUND_MAP,
    LoopException,
    get_custom_formated_current_datetime_str,
    quit_game,
)

from ..pygamesetup import SERVICES_NS

from ..pygamesetup.constants import (
    SCREEN,
    SCREEN_RECT,
    BLACK_BG,
    GAMEPADDIRECTIONALPRESSED,
    GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS,
    FPS,
    blit_on_screen,
    msecs_to_frames,
)

from ..pygamesetup.gamepaddirect import setup_gamepad_if_existent

from ..constants import CHARGED_SHOT_SPEED

from ..ourstdlibs.behaviour import do_nothing

from ..ourstdlibs.pyl import save_pyl

from ..textman import render_text, update_text_surface

from ..surfsman import EMPTY_SURF

from ..classes2d.single import UIObject2D

from ..classes2d.collections import UIList2D

from ..classes2d.surfaceswitcher import get_surface_switcher_class

from ..userprefsman.main import GAMEPAD_CONTROLS

from ..translatedtext import TRANSLATIONS, on_language_change



t = TRANSLATIONS.slot_creation_screen

ALLOWED_CHARS = (

    frozenset(

        (
            *digits,
            *ascii_uppercase,
            *ascii_lowercase,
            *'_',
        )

    )

)

MAX_LENGTH = 20

CHAR_X_OFFSET = 4
CHAR_Y_OFFSET = 3

_ERROR_MESSAGE_MSECS = 4000
ERROR_MESSAGE_FRAMES = msecs_to_frames(_ERROR_MESSAGE_MSECS)

GENERAL_TEXT_SETTINGS = {
    'style': 'regular',
    'size': 12,
    'padding': 2,
    'foreground_color': 'cyan',
}

NORMAL_TEXT_SETTINGS = {
    'style': 'regular',
    'size': 12,
    'padding': 2,
    'foreground_color': 'cyan'
}

SELECTED_TEXT_SETTINGS = {
    'style': 'regular',
    'size': 12,
    'padding': 2,
    'foreground_color': 'orange'
}


class SlotCreationScreen:
    """Interface for player to create new save slot by inputting name."""

    def __init__(self):

        ### caption

        caption = self.caption = (
            UIObject2D.from_surface(
                render_text(t.caption, **GENERAL_TEXT_SETTINGS)
            )
        )

        caption.rect.midtop = SCREEN_RECT.move(0, 5).midtop

        ### chosen name label

        chosen_name_label = self.chosen_name_label = (
            UIObject2D.from_surface(
                render_text(t.chosen_name_label, **GENERAL_TEXT_SETTINGS)
            )
        )

        chosen_name_label.rect.top = caption.rect.bottom + 3
        chosen_name_label.rect.left = 5

        ### text for specific buttons

        backspace_text = t.buttons.backspace
        ok_text = t.buttons.ok
        cancel_go_back_text = t.buttons.cancel_go_back

        ### surface maps for all objects

        buttons_surf_maps = self.buttons_surf_maps = {


            text: {

                surf_name: render_text(text, **text_settings)

                for surf_name, text_settings in (
                    ('normal', NORMAL_TEXT_SETTINGS),
                    ('selected', SELECTED_TEXT_SETTINGS),
                )

            }

            for text in (
                ' ', # space (not allowed, but useful as placeholder)
                '_', # underscore
                *ascii_uppercase,
                *ascii_lowercase,
                *digits,
                backspace_text,
                ok_text,
                cancel_go_back_text,
            )

        }

        ### collection to hold characters chosen by the user (starts with
        ### a space character, just as a placeholder, since it is an invisible
        ### character)

        slot_name_chars = self.slot_name_chars = UIList2D()

        self.space_placeholder_obj = space_placeholder_obj = (
            UIObject2D.from_surface(
                buttons_surf_maps[' ']['selected'],
                text=' ',
            )
        )

        slot_name_chars.append(space_placeholder_obj)

        slot_name_chars.rect.midleft = (
            chosen_name_label.rect.move(2, 0).midright
        )


        ### now we create the buttons

        button_class = (
            get_surface_switcher_class(frozenset(('normal', 'selected')))
        )

        buttons = self.buttons = UIList2D(

            button_class(

                # surf map for that button's text
                buttons_surf_maps[text],
                text=text,

            )

            for text in (

                # note that we don't use the space here, since it is not
                # allowed and will thus not get a button

                '_',
                *ascii_uppercase,
                *ascii_lowercase,
                *digits,
                backspace_text,
                ok_text,
                cancel_go_back_text,
            )

        )

        ## store references of the last 3 buttons in a collection
        self.bspace_ok_back_buttons = buttons[-3:]

        ## align buttons
        self.align_buttons()

        ### buttons map

        self.buttons_map = {

            button.text: button

            for button in buttons
            if button.text in ALLOWED_CHARS
        }

        ### store a standard char rect to use for calculations
        self.char_rect = buttons_surf_maps[' ']['normal'].get_rect()

        ### prepare obj to display error messages 

        self.error_label = UIObject2D.from_surface(EMPTY_SURF)
        self.error_label.message_surf_rect_pairs = {}

        ### update operation
        self.update = do_nothing

        ### store operation to update text surfaces when language changes
        on_language_change.append(self.on_language_change)

    def prepare(self):

        slot_name_chars = self.slot_name_chars

        slot_name_chars.clear()
        slot_name_chars.append(self.space_placeholder_obj)
        self.reposition_slot_name_chars()

        self.selected_button = self.buttons[0]
        self.update_selected_state()

        start_text_input()

        self.error_label.image = EMPTY_SURF

        self.update = do_nothing

    def on_language_change(self):

        ### update caption and chosen name label

        update_text_surface(
            self.caption,
            t.caption,
            GENERAL_TEXT_SETTINGS,
            pos_to_align='midtop',
        )

        update_text_surface(
            self.chosen_name_label,
            t.chosen_name_label,
            GENERAL_TEXT_SETTINGS,
            pos_to_align='topleft',
        )

        ### update buttons

        for button, text in zip(

            self.bspace_ok_back_buttons,

            (
                t.buttons.backspace,
                t.buttons.ok,
                t.buttons.cancel_go_back,
            ),

        ):

            for attr_name, text_settings in (
                ('normal', NORMAL_TEXT_SETTINGS),
                ('selected', SELECTED_TEXT_SETTINGS),
            ):

                setattr(
                    button,
                    attr_name,
                    render_text(text, **text_settings),
                )

            button.rect = button.normal.get_rect()

        self.align_buttons()

    def align_buttons(self):

        buttons = self.buttons

        buttons.rect.snap_rects_intermittently_ip(

            ### interval limit

            dimension_name='width', # either 'width' or 'height'
            dimension_unit='pixels', # either 'rects' or 'pixels'
            max_dimension_value=SCREEN_RECT.width - 20, # positive integer

            ### rect positioning

            retrieve_pos_from='topright',
            assign_pos_to='topleft',
            offset_pos_by=(CHAR_X_OFFSET, 0),

            ### intermittent rect positioning

            intermittent_pos_from='bottomleft',
            intermittent_pos_to='topleft',
            intermittent_offset_by=(0, CHAR_Y_OFFSET),

        )

        buttons.rect.top = self.chosen_name_label.rect.bottom + 15
        buttons.rect.centerx = SCREEN_RECT.centerx

    def update_selected_state(self):

        for obj in self.buttons:
            obj.switch_to_surface('normal')

        self.selected_button.switch_to_surface('selected')

    def control(self):

        for event in SERVICES_NS.get_events():

            if event.type == TEXTINPUT:

                if event.text in ALLOWED_CHARS:

                    self.add_char(event.text)
                    self.selected_button = self.buttons_map[event.text]
                    self.update_selected_state()

            elif event.type == KEYDOWN:

                if event.key == K_ESCAPE:
                    self.go_back()

                elif event.key == K_RETURN:
                    self.push_selected_button()

                elif event.key == K_BACKSPACE:
                    self.pop_last_char()

                elif event.key == K_SPACE:

                    self.add_char('_')
                    self.selected_button = self.buttons_map['_']
                    self.update_selected_state()

                elif event.key in (K_UP, K_DOWN):
                    self.go_up() if event.key == K_UP else self.go_down()

                elif event.key in (K_LEFT, K_RIGHT):
                    self.go_left() if event.key == K_LEFT else self.go_right()

            elif event.type == JOYBUTTONDOWN:

                if event.button == GAMEPAD_CONTROLS['start_button']:
                    self.push_selected_button()

            elif event.type == GAMEPADDIRECTIONALPRESSED:

                if event.direction in ('up', 'down'):
                    self.go_up() if event.direction == 'up' else self.go_down()

                elif event.direction in ('left', 'right'):

                    (
                        self.go_left()
                        if event.direction == 'left'
                        else self.go_right()
                    )

            elif event.type in GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS:
                setup_gamepad_if_existent()

            elif event.type == QUIT:
                quit_game()

    def add_char(self, char):

        slot_name_chars = self.slot_name_chars

        if len(slot_name_chars) == 1 and slot_name_chars[0].text == ' ':

            slot_name_chars.pop()

            slot_name_chars.append(

                UIObject2D.from_surface(

                    self.buttons_surf_maps[char]['selected'],
                    text=char,

                )

            )

            self.reposition_slot_name_chars()

        elif len(slot_name_chars) < MAX_LENGTH:

            slot_name_chars.append(

                UIObject2D.from_surface(

                    self.buttons_surf_maps[char]['selected'],
                    text=char,

                )

            )

            self.reposition_slot_name_chars()

    def reposition_slot_name_chars(self):

        self.slot_name_chars.rect.snap_rects_ip(
            retrieve_pos_from='topright',
            assign_pos_to='topleft',
            offset_pos_by=(-2, 0),
        )

        self.slot_name_chars.rect.midleft = (
            self.chosen_name_label.rect.move(2, 0).midright
        )

    def push_selected_button(self):

        text = self.selected_button.text

        if text in ALLOWED_CHARS:
            self.add_char(text)

        elif text == t.buttons.backspace:
            self.pop_last_char()

        elif text == t.buttons.ok:
            self.validate_and_proceed()

        elif text == t.buttons.cancel_go_back:
            self.go_back()

    def pop_last_char(self):

        self.slot_name_chars.pop()

        if not len(self.slot_name_chars):

            self.slot_name_chars.append
            self.slot_name_chars.append(self.space_placeholder_obj)
            self.reposition_slot_name_chars()

    def validate_and_proceed(self):
        """Validate folder name.

        If validates, proceed to story screen, if not, play error sound and
        show problem as a message in red.
        """
        slot_name_chars = self.slot_name_chars

        if len(slot_name_chars) == 1 and slot_name_chars[0].text == ' ':

            self.prepare_and_trigger_error_message(
                t.error_messages.must_input_some_name
            )

            return

        ###

        save_slot_name = ''.join(obj.text for obj in slot_name_chars)
        new_save_slot_file = SAVE_SLOTS_DIR / f'{save_slot_name}.pyl'

        if new_save_slot_file.exists():

            self.prepare_and_trigger_error_message(
                t.error_messages.save_slot_with_name_exists
            )

            return

        ### save data

        slot_data = {
            'last_played_date': get_custom_formated_current_datetime_str(),
        }

        ### try writing save data

        try:
            save_pyl(slot_data, new_save_slot_file)

        except Exception as err:

            unexpected_error_text = t.error_messages.unexpected_error
            self.prepare_and_trigger_error_message(
                f"{unexpected_error_text}: {err}"
            )

        else:

            REFS.slot_data = slot_data
            REFS.slot_path = new_save_slot_file

            SOUND_MAP['ui_success.wav'].play()

            transition_screen = REFS.states.transition_screen
            transition_screen.prepare(start_intro_level)

            raise LoopException(next_state=transition_screen)

    def prepare_and_trigger_error_message(self, error_message):

        error_label = self.error_label
        message_surf_rect_pairs = error_label.message_surf_rect_pairs

        if error_message not in message_surf_rect_pairs:

            message_surf = (
                render_text(
                    error_message,
                    'regular',
                    12,
                    2,
                    'red',
                )
            )
            message_rect = message_surf.get_rect()

            message_surf_rect_pairs[error_message] = (
                message_surf,
                message_rect,
            )

        else:

            message_surf, message_rect = (
                message_surf_rect_pairs[error_message]
            )

        error_label.image = message_surf
        error_label.rect = message_rect
        message_rect.bottomleft = SCREEN_RECT.move(5, -5).bottomleft

        self.error_message_countdown = ERROR_MESSAGE_FRAMES
        self.update = self.remove_error_message_after_countdown
        SOUND_MAP['ui_error.wav'].play()

    def go_back(self):

        main_menu = REFS.states.main_menu
        main_menu.prepare()
        stop_text_input()

        raise LoopException(next_state=main_menu)

    def go_to_next_char(self, x_steps, y_steps):

        current_selected_button = self.selected_button

        if x_steps:

            cache_attr_name = 'right' if x_steps > 0 else 'left'

            next_button = (
                getattr(current_selected_button, cache_attr_name, None)
            )

            if next_button:

                self.selected_button = next_button
                self.update_selected_state()
                return

            counter_cache_attr_name = (
                'left'
                if cache_attr_name == 'right'
                else 'right'
            )

            buttons = self.buttons
            buttons_union = buttons.rect.copy()

            char_rect = self.char_rect

            if x_steps > 0:

                char_rect.topleft = current_selected_button.rect.topright
                char_rect.move_ip(CHAR_X_OFFSET, 0)

            else:

                char_rect.topright = current_selected_button.rect.topleft
                char_rect.move_ip(-CHAR_X_OFFSET, 0)

            ###

            x_offset = CHAR_X_OFFSET + char_rect.width

            if x_steps < 0:
                x_offset *= -1

            ###

            while True:

                for obj in buttons:

                    if obj.rect.colliderect(char_rect):

                        setattr(
                            current_selected_button,
                            cache_attr_name,
                            obj,
                        )

                        setattr(
                            obj,
                            counter_cache_attr_name,
                            current_selected_button,
                        )

                        self.selected_button = obj
                        break

                else:

                    char_rect.move_ip(x_offset, 0)

                    if not buttons_union.colliderect(char_rect):

                        if x_steps > 0:
                            char_rect.left = buttons_union.left

                        else:
                            char_rect.right = buttons_union.right

                    continue

                self.update_selected_state()
                return


        elif y_steps:

            cache_attr_name = 'down' if y_steps > 0 else 'up'

            next_button = (
                getattr(current_selected_button, cache_attr_name, None)
            )

            if next_button:

                self.selected_button = next_button
                self.update_selected_state()
                return

            counter_cache_attr_name = (
                'up'
                if cache_attr_name == 'down'
                else 'down'
            )

            buttons = self.buttons
            buttons_union = buttons.rect.copy()

            char_rect = self.char_rect

            if y_steps > 0:

                char_rect.midtop = self.selected_button.rect.midbottom
                char_rect.move_ip(0, CHAR_Y_OFFSET)

            else:

                char_rect.midbottom = self.selected_button.rect.midtop
                char_rect.move_ip(0, -CHAR_X_OFFSET)

            ###

            y_offset = CHAR_Y_OFFSET + char_rect.height

            if y_steps < 0:
                y_offset *= -1

            ###

            while True:

                for obj in buttons:

                    if obj.rect.colliderect(char_rect):

                        setattr(
                            current_selected_button,
                            cache_attr_name,
                            obj,
                        )

                        setattr(
                            obj,
                            counter_cache_attr_name,
                            current_selected_button,
                        )

                        self.selected_button = obj
                        break

                else:

                    char_rect.move_ip(0, y_offset)

                    if not buttons_union.colliderect(char_rect):

                        if y_steps > 0:
                            char_rect.top = buttons_union.top

                        else:
                            char_rect.bottom = buttons_union.bottom

                    continue

                self.update_selected_state()
                return
        else:
            raise RuntimeError("Either 'x_steps' or 'y_steps' must be != 0.")

    go_up = partialmethod(go_to_next_char, 0, -1)
    go_down = partialmethod(go_to_next_char, 0, 1)
    go_left = partialmethod(go_to_next_char, -1, 0)
    go_right = partialmethod(go_to_next_char, 1, 0)

    def remove_error_message_after_countdown(self):
        """Remove error message once countdown finishes."""

        self.error_message_countdown -= 1

        if self.error_message_countdown <= 0:

            self.error_label.image = EMPTY_SURF
            self.update = do_nothing

    def draw(self):

        blit_on_screen(BLACK_BG, (0, 0))

        self.caption.draw()
        self.error_label.draw()
        self.chosen_name_label.draw()
        self.buttons.draw()
        draw_rect(SCREEN, 'orange', self.selected_button.rect, 1)
        self.slot_name_chars.draw()

        update()


def start_intro_level():
    """Trigger start of intro level."""

    ### TODO here, instead of starting the intro level, we
    ### should proceed to the story screen, to present the
    ### plot (which the player should be able to skip if desired)

    level_manager = REFS.states.level_manager
    REFS.level_to_load = 'intro.lvl'
    level_manager.prepare()

    raise LoopException(next_state=level_manager)
