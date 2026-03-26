"""Facility for screen wherin to load saved game."""

### standard library imports

from itertools import cycle

from collections import deque


### third-party imports

from pygame.locals import (

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

from pygame.display import update as update_screen

from pygame.draw import rect as draw_rect


### local imports

from ...config import (
    REFS,
    SAVE_SLOTS_DIR,
    LoopException,
    get_custom_datetime_str_for_last_played,
    quit_game,
)

from ...pygamesetup import SERVICES_NS

from ...pygamesetup.constants import (
    SCREEN,
    SCREEN_RECT,
    BLACK_BG,
    GAMEPADDIRECTIONALPRESSED,
    GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS,
    blit_on_screen,
    msecs_to_frames,
)

from ...pygamesetup.gamepaddirect import setup_gamepad_if_existent

from ...ourstdlibs.pyl import load_pyl, save_pyl

from ...ourstdlibs.behaviour import do_nothing

from ...classes2d.single import UIObject2D

from ...classes2d.collections import UIList2D

from ...textman import render_text, update_text_surface

from ...surfsman import combine_surfaces

from ...promptscreen import present_prompt

from ...translatedtext import TRANSLATIONS, on_language_change

from .slotdisplay import SlotDisplay



SLOT_BUTTON_TEXT_SETTINGS = {
    'style': 'regular',
    'size': 12,
    'padding': 0,
    'foreground_color': 'white',
    'background_color': 'black',
}

GO_BACK_TEXT_SETTINGS = {
    'style': 'regular',
    'size': 12,
    'padding': 4,
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

sort_by_less_recent_obj = lambda item: item.slot_data['last_played_date']


# blinking

_ON_TIME = 700
_ON_FRAMES = msecs_to_frames(_ON_TIME)

_OFF_TIME = 400
_OFF_FRAMES = msecs_to_frames(_OFF_TIME)

must_blink = cycle(
    (
        *((True,)  * _ON_FRAMES),
        *((False,) * _OFF_FRAMES),
    )
).__next__


t = TRANSLATIONS.load_game_screen


class LoadGameScreen:
    """Interface to allow users to load game from existing save slot."""

    def __init__(self):
        """Create objects to support load screen operations."""

        self.arrow = (
            UIObject2D.from_surface(
                render_text('->', 'regular', 12, 2, 'orange', 'black')
            )
        )

        caption = self.caption = (
            UIObject2D.from_surface(
                render_text(
                    t.load_game_caption,
                    **TITLE_TEXT_SETTINGS,
                )
            )
        )

        caption.rect.midtop = SCREEN_RECT.move(0, 5).midtop

        y = caption.rect.bottom + 10

        items = self.items = UIList2D()
        items.append(caption)

        ###

        self.button_surfs_map = {}
        recreate_button_surfs(self.button_surfs_map)

        ###

        save_slots_data = self.save_slots_data = {

            path: load_pyl(path)

            for path in SAVE_SLOTS_DIR.iterdir()
            if path.suffix.lower() == '.pyl'

        }

        ###

        sort_aid_list = self.sort_aid_list = UIList2D(

            SlotDisplay(
                slot_path,
                slot_data,
                self.button_surfs_map,
                self.trigger_slot_button,
            )

            for slot_path, slot_data in save_slots_data.items()

        )

        sort_aid_list.sort(key=sort_by_less_recent_obj, reverse=True)

        sort_aid_list.rect.snap_rects_ip(
            retrieve_pos_from='midbottom',
            assign_pos_to='midtop',
            offset_pos_by=(0, 3),
        )


        ###

        go_back_button = self.go_back_button = (

            UIObject2D.from_surface(
                render_text(
                    t.buttons.go_back,
                    **GO_BACK_TEXT_SETTINGS,
                )
            )

        )

        go_back_button.command = self.go_back

        for slot_display in reversed(sort_aid_list):
            items.insert(1, slot_display)

        sort_aid_list.clear()

        items.append(go_back_button)

        ###

        self.buttons = [
            obj
            for obj in items
            if hasattr(obj, 'command')
        ]

        self.button_count = len(self.buttons)

        ###
        self.update = do_nothing

        ### store method to call when language changes
        on_language_change.append(self.on_language_change)

    def trigger_slot_button(self, slot_path):
        """Trigger action from selected slot button."""

        slot_button_index = self.slot_button_indices[0]

        if slot_button_index == 0:
            self.load_slot(slot_path)

        elif slot_button_index == 1:
            self.rename_slot(slot_path)

        elif slot_button_index == 2:
            self.delete_slot_if_user_confirms(slot_path)

        else:
            raise RuntimeError(
                "'slot_button_index' must always be 0, 1 or 2"
            )

    def delete_slot_if_user_confirms(self, slot_path):
        """If user confirms given prompt, delete slot and perform setups."""
        slot_name = slot_path.stem

        deleting = t.prompts.deleting

        must_delete = present_prompt(

            deleting.caption,
            deleting.message.format(slot_name = slot_name),

            (
                (TRANSLATIONS.general.no, False),
                (TRANSLATIONS.general.yes, True),
            ),

        )

        if must_delete:

            ###

            try:
                slot_path.unlink()

            except Exception as err:

                error_message = t.prompts.error_message_on_removal

                present_prompt(

                    error_message.caption,
                    error_message.message.format(error=str(err)),

                    (
                        (TRANSLATIONS.general.ok, True),
                    ),
                )

                return

            ###

            slot_data = self.save_slots_data.pop(slot_path)

            for index, item in enumerate(self.items):

                if (
                    hasattr(item, 'slot_data')
                    and item.slot_data is slot_data
                ):
                    break

            self.items.pop(index)

            if self.save_slots_data:
                self.update_slot_displays()

            else:
                self.go_back()

    def update_slot_displays(self):

        sort_aid_list = self.sort_aid_list
        items = self.items

        sort_aid_list.extend(
            item
            for item in items
            if hasattr(item, 'slot_path')
        )

        for item in sort_aid_list:
            items.remove(item)

        slot_displays_to_remove = [

            item
            for item in sort_aid_list
            if not item.slot_path.exists()

        ]

        save_slots_data = self.save_slots_data

        for item in slot_displays_to_remove:

            sort_aid_list.remove(item)
            save_slots_data.pop(item.slot_path)

        ###

        all_slot_paths = {

            path

            for path in SAVE_SLOTS_DIR.iterdir()
            if path.suffix.lower() == '.pyl'

        }

        current_slot_paths = {
            slot_display.slot_path
            for slot_display in sort_aid_list
        }

        paths_not_displayed = all_slot_paths - current_slot_paths


        for slot_path in paths_not_displayed:

            save_slots_data[slot_path] = slot_data = load_pyl(slot_path)

            sort_aid_list.append(

                SlotDisplay(
                    slot_path,
                    slot_data,
                    self.button_surfs_map,
                    self.trigger_slot_button,
                )

            )

        ###

        sort_aid_list.sort(key=sort_by_less_recent_obj, reverse=True)

        sort_aid_list.rect.snap_rects_ip(
            retrieve_pos_from='bottomleft',
            assign_pos_to='topleft',
            offset_pos_by=(0, 3),
        )


        for slot_display in reversed(sort_aid_list):
            items.insert(1, slot_display)

        sort_aid_list.rect.top = self.caption.rect.bottom + 3
        sort_aid_list.rect.centerx = SCREEN_RECT.centerx

        self.go_back_button.rect.topleft = (
            sort_aid_list.rect.move(0, 5).bottomleft
        )

        sort_aid_list.clear()

        self.buttons.clear()
        self.buttons.extend(
            obj
            for obj in items
            if hasattr(obj, 'command')
        )

        self.button_count = len(self.buttons)

        for button in self.buttons:

            if hasattr(button, 'slot_path'):

                button.update_last_played_timestamp()
                button.update_beaten_bosses()
                button.update_encounters()

        self.current_index = 0
        self.highlighted_widget = self.buttons[self.current_index]

        self.slot_button_indices = deque(range(3))

        self.align_button()

    prepare = update_slot_displays

    def on_language_change(self):

        ### update text surface of caption and go back button

        update_text_surface(
            self.caption,
            t.load_game_caption,
            TITLE_TEXT_SETTINGS,
            pos_to_align='midtop',
        )

        update_text_surface(
            self.go_back_button,
            t.buttons.go_back,
            GO_BACK_TEXT_SETTINGS,
        )

        ### update slot displays

        recreate_button_surfs(self.button_surfs_map)

        for item in self.items:

            if not hasattr(item, 'slot_path'):
                continue

            item.on_language_change()

    def load_slot(self, slot_path):
        """Load slot represented by given path."""

        slot_data = self.save_slots_data[slot_path]

        # TODO when the the stage selection screen is ready,
        # this if-block can be removed

        if 'beaten_bosses' in slot_data:

            revisit_first_mission = t.prompts.revisit_first_mission

            answer = present_prompt(

                revisit_first_mission.caption,
                revisit_first_mission.message,

                (
                    (TRANSLATIONS.general.yes, True),
                    (TRANSLATIONS.general.no, False),
                ),


            )

            if not answer:
                return

        slot_data['last_played_date'] = (
            get_custom_datetime_str_for_last_played()
        )

        try:
            save_pyl(slot_data, slot_path)

        except Exception as err:

            error_message = t.prompts.error_message_on_load

            present_prompt(

                error_message.caption,
                error_message.message.format(error=str(err))

                (
                    (TRANSLATIONS.general.ok, True),
                ),

            )

            return

        REFS.slot_data = slot_data
        REFS.slot_path = slot_path

        slot_display = next(

            button

            for button in self.buttons

            if (
                hasattr(button, 'slot_path')
                and button.slot_data is slot_data
            )
        )

        # TODO when the the stage selection screen is ready,
        # use it instead of start_intro_level, but only if there
        # are beaten bosses
        callable_to_use = start_intro_level

        transition_screen = REFS.states.transition_screen
        transition_screen.prepare(callable_to_use)

        raise LoopException(next_state=transition_screen)

    def rename_slot(self, slot_path):

        slot_renaming_screen = REFS.states.slot_renaming_screen
        slot_renaming_screen.prepare(slot_path)

        raise LoopException(next_state=slot_renaming_screen)

    def load_first(self):
        """Load first slot, which is the most-recently-played one."""
        self.load_slot(self.buttons[0].slot_path)

    def align_button(self):

        centery = self.highlighted_widget.rect.centery
        screen_centery = SCREEN_RECT.centery

        y_diff = screen_centery - centery
        self.items.rect.move_ip(0, y_diff)

        slot_button_indices = self.slot_button_indices

        while slot_button_indices[0] != 0:
            slot_button_indices.rotate(1)

    def control(self):
        
        for event in SERVICES_NS.get_events():

            if event.type == KEYDOWN:

                if event.key == K_ESCAPE:
                    self.go_back()

                elif event.key in (K_UP, K_DOWN):

                    increment = -1 if event.key == K_UP else 1

                    self.current_index = (
                        (self.current_index + increment)
                        % self.button_count
                    )

                    self.highlighted_widget = (
                        self.buttons[self.current_index]
                    )

                    self.align_button()

                elif event.key == K_LEFT:
                    self.slot_button_indices.rotate(1)

                elif event.key == K_RIGHT:
                    self.slot_button_indices.rotate(-1)

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
                        % self.button_count
                    )

                    self.highlighted_widget = (
                        self.buttons[self.current_index]
                    )

                    self.align_button()

                elif event.direction == 'left':
                    self.slot_button_indices.rotate(1)

                elif event.direction == 'right':
                    self.slot_button_indices.rotate(-1)

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

        raise LoopException(next_state=main_menu)

    def on_mouse_click(self, event):

        pos = event.pos

        for index, obj in enumerate(self.buttons):

            if obj.rect.collidepoint(pos):

                self.current_index = index
                self.highlighted_widget = obj

                if hasattr(obj, 'slot_path'):

                    if obj.load_button.rect.collidepoint(pos):
                        self.load_slot(obj.slot_path)

                    elif obj.rename_button.rect.collidepoint(pos):
                        self.rename_slot(obj.slot_path)

                    elif obj.erase_button.rect.collidepoint(pos):
                        self.delete_slot_if_user_confirms(obj.slot_path)

                break

    def highlight_under_mouse(self, event):

        pos = event.pos

        for index, obj in enumerate(self.buttons):

            if obj.rect.collidepoint(pos):

                self.current_index = index
                self.highlighted_widget = obj

                if hasattr(obj, 'slot_path'):

                    if obj.load_button.rect.collidepoint(pos):
                        slot_button_index = 0

                    elif obj.rename_button.rect.collidepoint(pos):
                        slot_button_index = 1

                    elif obj.erase_button.rect.collidepoint(pos):
                        slot_button_index = 2

                    else:
                        slot_button_index = None

                    if slot_button_index is not None:

                        slot_button_indices = self.slot_button_indices

                        while slot_button_indices[0] != slot_button_index:
                            slot_button_indices.rotate(1)

                break

    def draw(self):

        blit_on_screen(BLACK_BG, (0, 0))

        for item in self.items:
            item.draw()

        hw = self.highlighted_widget

        self.arrow.rect.midright = hw.rect.midleft
        self.arrow.rect.move_ip(-4, 0)
        self.arrow.draw()

        if hasattr(hw, 'slot_path'):

            draw_rect(SCREEN, 'orange', hw.rect, 2, border_radius=10)

            if must_blink():
                
                slot_button_index = self.slot_button_indices[0]

                draw_rect(

                    SCREEN,
                    'orangered',

                    (

                        hw.load_button.rect
                        if slot_button_index == 0

                        else (

                            hw.rename_button.rect
                            if slot_button_index == 1

                            else hw.erase_button.rect

                        )

                    ),

                    1,

                )

        else:
            draw_rect(SCREEN, 'orange', hw.rect, 2, border_radius=10)

        update_screen()


def enter_stage_selection_screen():
    """Enter the stage select screen."""
    ### XXX for when stage selection screen is created and can be
    ### accessed (by players who defeated the first boss)

#    stage_selection_screen = REFS.states.stage_selection_screen
#    stage_selection_screen.prepare()
#
#    raise LoopException(next_state=stage_selection_screen)

def start_intro_level():
    """Trigger start of intro level."""

    level_manager = REFS.states.level_manager
    REFS.level_to_load = 'intro.lvl'
    level_manager.prepare()

    raise LoopException(next_state=level_manager)

def recreate_button_surfs(button_surfs_map):

    for icon_chars, icon_bg_color, button_text, key in (
        ('OK', 'blue', t.buttons.load_game, 'load_button'),
        ('__', 'darkgreen', t.buttons.rename, 'rename_button'),
        ('X', 'red', t.buttons.erase, 'erase_button'),
    ):

        _icon_surf = (
            render_text(
                icon_chars, 'regular', 12, 2, 'white', icon_bg_color,
            )
        )

        _text_surf = (
            render_text(button_text, **SLOT_BUTTON_TEXT_SETTINGS)
        )

        _final_surf = (
            combine_surfaces(
                (_icon_surf, _text_surf),
                retrieve_pos_from='midright',
                assign_pos_to='midleft',
                offset_pos_by=(2, 0),
                padding=2,
                background_color='black',
            )
        )

        button_surfs_map[key] = _final_surf
