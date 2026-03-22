"""Facility for screen wherin to load saved game."""

### standard library imports

from functools import partial

from itertools import cycle


### third-party imports

from pygame import Surface

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

from pygame.display import update

from pygame.draw import rect as draw_rect


### local imports

from ..config import (
    REFS,
    COLORKEY,
    SAVE_SLOTS_DIR,
    SOUND_MAP,
    SURF_MAP,
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
    blit_on_screen,
    msecs_to_frames,
)

from ..pygamesetup.gamepaddirect import setup_gamepad_if_existent

from ..ourstdlibs.pyl import load_pyl, save_pyl

from ..ourstdlibs.behaviour import do_nothing

from ..classes2d.single import UIObject2D

from ..classes2d.collections import UIList2D

from ..textman import render_text, update_text_surface

from ..surfsman import combine_surfaces

from ..promptscreen import present_prompt

from ..translatedtext import TRANSLATIONS, on_language_change




LABEL_TEXT_SETTINGS = {
    'style': 'regular',
    'size': 12,
    'padding': 0,
    'foreground_color': 'white',
    'background_color': 'darkblue',
}

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

        if self.slot_button_index == 0:
            self.load_slot(slot_path)

        elif self.slot_button_index == 1:
            self.delete_slot_if_user_confirms(slot_path)

        else:
            raise RuntimeError(
                "'slot_button_index' must always be 0 or 1"
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
                self.resort_slots()

            else:
                self.go_back()

    def resort_slots(self):

        sort_aid_list = self.sort_aid_list
        items = self.items

        sort_aid_list.extend(
            item
            for item in items
            if hasattr(item, 'slot_path')
        )

        for item in sort_aid_list:
            items.remove(item)

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
        self.slot_button_index = 0
        self.highlighted_widget = self.buttons[self.current_index]
        self.align_button()

    prepare = resort_slots

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
            get_custom_formated_current_datetime_str()
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

        SOUND_MAP['ui_success.wav'].play()

        # TODO when the the stage selection screen is ready,
        # use it instead of start_intro_level, but only if there
        # are beaten bosses
        callable_to_use = start_intro_level

        transition_screen = REFS.states.transition_screen
        transition_screen.prepare(callable_to_use)

        raise LoopException(next_state=transition_screen)

    def load_first(self):
        """Load first slot, which is the most-recently-played one."""
        self.load_slot(self.buttons[0].slot_path)

    def align_button(self):

        centery = self.highlighted_widget.rect.centery
        screen_centery = SCREEN_RECT.centery

        y_diff = screen_centery - centery
        self.items.rect.move_ip(0, y_diff)
        self.slot_button_index = 0

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

                elif event.key in (K_LEFT, K_RIGHT):

                    self.slot_button_index = (
                        0 if self.slot_button_index == 1 else 1
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
                        % self.button_count
                    )

                    self.highlighted_widget = (
                        self.buttons[self.current_index]
                    )

                    self.align_button()

                elif event.direction in ('left', 'right'):

                    self.slot_button_index = (
                        0 if self.slot_button_index == 1 else 1
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

                    if obj.erase_button.rect.collidepoint(pos):
                        self.slot_button_index = 1

                    else:
                        self.slot_button_index = 0

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

                draw_rect(
                    SCREEN,
                    'orangered',
                    (
                        hw.load_button.rect
                        if self.slot_button_index == 0
                        else hw.erase_button.rect
                    ),
                    1,
                )

        else:
            draw_rect(SCREEN, 'orange', hw.rect, 2, border_radius=10)

        update()


def enter_stage_selection_screen():
    """Enter the stage select screen."""

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

class SlotDisplay(UIList2D):

    def __init__(
        self,
        slot_path,
        slot_data,
        button_surfs_map,
        trigger_command,
    ):

        super().__init__()

        ###

        self.slot_path = slot_path
        self.slot_data = slot_data
        self.command = partial(trigger_command, slot_path)

        ###

        slot_name = slot_path.stem

        slot_name_label = (

            UIObject2D.from_surface(
                render_text(
                    slot_name,
                    **LABEL_TEXT_SETTINGS,
                )
            )

        )

        self.append(slot_name_label)

        ###

        last_played_label = self.last_played_label = (
            UIObject2D.from_surface(
                render_text(
                    t.labels.last_played + ":",
                    **LABEL_TEXT_SETTINGS,
                ),
            )
        )

        last_played_label.rect.topleft = (
            slot_name_label.rect.move(10, 0).bottomleft
        )

        self.append(last_played_label)

        ###

        timestamp_text = slot_data['last_played_date'][:19]

        timestamp_label = self.timestamp_label = (
            UIObject2D.from_surface(
                render_text(
                    timestamp_text,
                    **LABEL_TEXT_SETTINGS,
                ),
                timestamp_text = timestamp_text,
            )
        )

        self.append(timestamp_label)

        timestamp_label.rect.midleft = (
            last_played_label.rect.move(2, 0).midright
        )

        ###

        self.button_surfs_map = button_surfs_map

        load_button = self.load_button = (
            UIObject2D.from_surface(button_surfs_map['load_button'])
        )

        erase_button = self.erase_button = (
            UIObject2D.from_surface(button_surfs_map['erase_button'])
        )

        load_button.rect.topleft = last_played_label.rect.move(0, 5).bottomleft
        erase_button.rect.topleft = load_button.rect.move(5, 0).topright

        self.append(load_button)
        self.append(erase_button)


        ### beaten bosses label and objs

        beaten_bosses_label = self.beaten_bosses_label = (
            UIObject2D.from_surface(
                render_text(
                    t.labels.beaten_bosses + ":",
                    **LABEL_TEXT_SETTINGS,
                )
            )
        )

        beaten_bosses_label.rect.topleft = (
            load_button.rect.move(0, 5).bottomleft
        )

        self.append(beaten_bosses_label)

        previous_obj = beaten_bosses_label

        boss_objs = self.boss_objs = UIList2D(

            UIObject2D.from_surface(
                SURF_MAP[f'{boss_name}_head.png'],
                boss_name = boss_name,
            )

            for boss_name in slot_data.get('beaten_bosses', ())

        )

        if boss_objs:

            boss_objs.rect.snap_rects_ip(
                retrieve_pos_from='midright',
                assign_pos_to='midleft',
                offset_pos_by=(2, 0),
            )

            boss_objs.rect.midleft = (
                beaten_bosses_label.rect.move(2, 0).midright
            )

        self.extend(boss_objs)


        ### encounter label and objs

        encounters_label = self.encounters_label = (
            UIObject2D.from_surface(
                render_text(
                    t.labels.encounters + ":",
                    **LABEL_TEXT_SETTINGS,
                )
            )
        )

        encounters_label.rect.topleft = (
            beaten_bosses_label.rect.move(0, 5).bottomleft
        )

        self.append(encounters_label)

        encounter_objs = self.encounter_objs = UIList2D(

            UIObject2D.from_surface(
                SURF_MAP[f'{encounter_name}_head.png'],
                encounter_name = encounter_name,
            )

            for encounter_name in slot_data.get('encounters', ())

        )

        if encounter_objs:

            encounter_objs.rect.snap_rects_ip(
                retrieve_pos_from='midright',
                assign_pos_to='midleft',
                offset_pos_by=(2, 0),
            )

            encounter_objs.rect.midleft = (
                encounters_label.rect.move(2, 0).midright
            )

        self.extend(encounter_objs)

        ###
        self.rebuild_bg_obj()

    def on_language_change(self):

        ### update last played label's text

        update_text_surface(
            self.last_played_label,
            t.labels.last_played + ":",
            LABEL_TEXT_SETTINGS,
            pos_to_align='midleft',
        )

        ### reposition timestamp label accordingly

        self.timestamp_label.rect.midleft = (
            self.last_played_label.rect.move(2, 0).midright
        )

        ### update beaten bosses label's text

        update_text_surface(
            self.beaten_bosses_label,
            t.labels.beaten_bosses + ":",
            LABEL_TEXT_SETTINGS,
            pos_to_align='midleft',
        )

        ### reposition boss objs accordingly

        if self.boss_objs:

            self.boss_objs.rect.midleft = (
                self.beaten_bosses_label.rect.move(2, 0).midright
            )

        ### update surface and rect of buttons

        for button_name in ('load_button', 'erase_button'):

            obj = getattr(self, button_name)

            new_surf = self.button_surfs_map[button_name]
            new_rect = new_surf.get_rect()

            new_rect.midleft = obj.rect.midleft

            obj.image = new_surf
            obj.rect = new_rect

        self.erase_button.rect.topleft = (
            self.load_button.rect.move(5, 0).topright
        )

        ### update encounters label's text

        update_text_surface(
            self.encounters_label,
            t.labels.encounters + ":",
            LABEL_TEXT_SETTINGS,
            pos_to_align='midleft',
        )

        ### reposition boss objs accordingly

        if self.encounter_objs:

            self.encounter_objs.rect.midleft = (
                self.encounters_label.rect.move(2, 0).midright
            )

        ### rebuild bg
        self.rebuild_bg_obj()

    def rebuild_bg_obj(self):

        if not hasattr(self, 'bg_obj'):
            bg_obj = self.bg_obj = UIObject2D()

        else:
            bg_obj = self.pop(0)

        ###

        bg_rect = self.rect.inflate(10, 10)
        bg_surf = Surface(bg_rect.size).convert()
        bg_surf.set_colorkey(COLORKEY)
        bg_surf.fill(COLORKEY)

        draw_bg_rect = bg_surf.get_rect()

        draw_rect(bg_surf, 'darkblue', draw_bg_rect, border_radius=10)
        draw_rect(bg_surf, 'white', draw_bg_rect, 2, border_radius=10)

        bg_obj.image = bg_surf
        bg_obj.rect = bg_rect

        self.insert(0, bg_obj)

    def update_last_played_timestamp(self):

        updated_timestamp = (
            self.slot_data['last_played_date'][:19]
        )

        timestamp_label = self.timestamp_label

        if updated_timestamp == timestamp_label.timestamp_text:
            return

        update_text_surface(
            timestamp_label,
            updated_timestamp,
            LABEL_TEXT_SETTINGS,
            pos_to_align='midleft',
        )

    ### XXX this and the next update method do exactly the same thing,
    ### except they use different attributes, keys, collections;
    ###
    ### since there are only 02 instances of the same behaviour, it is okay
    ### to let then coexist; if there needs to be another instance of this
    ### kind of behaviour, though, refactor everything so a single method
    ### can be used instead

    def update_beaten_bosses(self):
        """Add new beaten bosses if any."""

        boss_objs = self.boss_objs

        no_of_beaten_bosses = len(self.slot_data.get('beaten_bosses', ()))
        no_of_boss_objs = len(boss_objs)

        diff =  no_of_beaten_bosses - no_of_boss_objs

        if diff:

            for index, boss_name in enumerate(self.slot_data['beaten_bosses']):

                if index >= no_of_boss_objs:

                    boss_objs.append(
                        UIObject2D.from_surface(
                            SURF_MAP[f'{boss_name}_head.png'],
                            boss_name = boss_name,
                        )
                    )

            for obj in boss_objs:
                self.remove(obj)

            boss_objs.rect.snap_rects_ip(
                retrieve_pos_from='midright',
                assign_pos_to='midleft',
                offset_pos_by=(2, 0),
            )

            beaten_bosses_label = self.beaten_bosses_label

            boss_objs.rect.midleft = (
                beaten_bosses_label.rect.move(2, 0).midright
            )

            index_to_insert = self.index(beaten_bosses_label) + 1

            for obj in boss_objs:

                self.insert(index_to_insert, obj)
                index_to_insert += 1

    def update_encounters(self):
        """Add new encounters if any."""

        encounter_objs = self.encounter_objs

        no_of_encounters = len(self.slot_data.get('encounters', ()))
        no_of_encounter_objs = len(encounter_objs)

        diff =  no_of_encounters - no_of_encounter_objs

        if diff:

            for index, encounter_name in (
                enumerate(self.slot_data['encounters'])
            ):

                if index >= no_of_encounter_objs:

                    encounter_objs.append(
                        UIObject2D.from_surface(
                            SURF_MAP[f'{encounter_name}_head.png'],
                            encounter_name = encounter_name,
                        )
                    )

            for obj in encounter_objs:
                self.remove(obj)

            encounter_objs.rect.snap_rects_ip(
                retrieve_pos_from='midright',
                assign_pos_to='midleft',
                offset_pos_by=(2, 0),
            )

            encounters_label = self.encounters_label

            index_to_insert = self.index(self.encounters_label) + 1

            for obj in encounter_objs:

                self.insert(index_to_insert, obj)
                index_to_insert += 1
