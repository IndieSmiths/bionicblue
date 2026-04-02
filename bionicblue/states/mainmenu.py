"""Facility for main menu."""

### standard library import
from itertools import count


### third-party imports

from pygame.locals import (

    QUIT,

    KEYDOWN,
    K_ESCAPE,
    K_RETURN,
    K_DOWN,
    K_UP,

    JOYBUTTONDOWN,

    MOUSEBUTTONDOWN,
    MOUSEMOTION,

)

from pygame.display import update


### local imports

from ..config import (
    REFS,
    SOUND_MAP,
    MUSIC_DIR,
    SAVE_SLOTS_DIR,
    LoopException,
    has_save_slots,
    get_custom_datetime_str_for_default_slot_name,
    get_custom_datetime_str_for_last_played,
    quit_game,
)

from ..pygamesetup import SERVICES_NS

from ..pygamesetup.constants import (
    SCREEN_RECT,
    BLACK_BG,
    GAMEPADDIRECTIONALPRESSED,
    GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS,
    FPS,
    blit_on_screen,
)

from ..pygamesetup.gamepadservices import GAMEPAD_NS

from ..constants import CHARGED_SHOT_SPEED

from ..ourstdlibs.behaviour import do_nothing

from ..ourstdlibs.pyl import save_pyl

from ..textman import render_text

from ..classes2d.single import UIObject2D

from ..classes2d.collections import UIList2D

from ..userprefsman.main import KEYBOARD_CONTROLS, GAMEPAD_CONTROLS

from ..translatedtext import TRANSLATIONS, on_language_change



t = TRANSLATIONS.main_menu

NORMAL_TEXT_SETTINGS = {
    'style': 'regular',
    'size': 12,
    'padding': 2,
    'foreground_color': 'cyan',
}

SELECTED_TEXT_SETTINGS = {
    'style': 'regular',
    'size': 12,
    'padding': 2,
    'foreground_color': 'orange',
}


class MainMenu:

    def __init__(self):

        self.current_index = 0

        ###

        labels_data_tuples = [

            # a 3-tuple containing a string key and 02 surfaces
            # representing it (unhighlighted and highlighted)

            (

                text_identifier,

                *(

                    render_text(

                        # text
                        getattr(t, text_identifier),

                        # text settings
                        **text_settings,

                    )

                    for text_settings in (
                        NORMAL_TEXT_SETTINGS,
                        SELECTED_TEXT_SETTINGS,
                    )

                )

            )

            for text_identifier in (
                'continue',
                'new_game',
                'load_game',
                'kbd_controls',
                'gp_controls',
                'options',
                'links',
                'credits',
                'exit',
            )

        ]

        ###

        self.unhighlighted_surf_map = unhighlighted_surf_map = {}
        self.highlighted_surf_map = highlighted_surf_map = {}

        obj_map = {}

        for (
            key,
            unhighlighted_surf,
            highlighted_surf,
        ) in labels_data_tuples:

            unhighlighted_surf_map[key] = unhighlighted_surf
            highlighted_surf_map[key] = highlighted_surf

            obj = UIObject2D.from_surface(unhighlighted_surf)
            obj.key = key
            obj_map[key] = obj

        ###

        self.compact_items = (

            UIList2D(

                obj_map[key]

                for key in (
                    'new_game',
                    'kbd_controls',
                    'gp_controls',
                    'options',
                    'links',
                    'credits',
                    'exit',
                )

            )

        )

        self.full_items = (

            UIList2D(

                obj_map[key]

                for key in (
                    'continue',
                    'new_game',
                    'load_game',
                    'kbd_controls',
                    'gp_controls',
                    'options',
                    'links',
                    'credits',
                    'exit',
                )

            )

        )

        self.control = self.control_item_selection
        self.update = do_nothing

        ### store method to update text surfaces when language changes
        on_language_change.append(self.on_language_change)

    def prepare(self):

        REFS.last_checkpoint_name = 'landing'

        there_are_save_slots = has_save_slots()

        ### need to do update the slot displays because they are used to
        ### load the most recent slot in the "continue" item in the
        ### main menu, but this is needed only when there are save slots;

        ### XXX
        ### strictly speaking, though, when the load game screen is
        ### created, this kind of stuff is already checked, so this is
        ### actually only needed after revisiting the main menu once
        ### you leave the level (since the load game screen was already
        ### created before and now the slots really need to be updated)
        ###
        ### because of that, make sure to review the related code in order
        ### to prevent needless reprocessing; for now, the redundant checks
        ### (when they happen) are very negligible and seem unnoticeable

        if there_are_save_slots:
            REFS.states.load_game_screen.update_slot_displays()

        ###

        items = self.items = (

            self.full_items
            if there_are_save_slots

            else self.compact_items

        )

        ###

        self.item_count = len(items)

        items.rect.snap_rects_ip(
            retrieve_pos_from='midbottom',
            assign_pos_to='midtop', 
        )

        ### put items centered on the second horizontal
        ### half of the screen

        _scopy = SCREEN_RECT.copy()
        _scopy.width /= 2
        _scopy.left = _scopy.right

        items.rect.center = _scopy.center

        ###

        self.items_left = items.rect.left

        if self.current_index >= self.item_count:
            self.current_index = self.item_count - 1

        REFS.blue_boy.aniplayer.switch_animation('idle_right')

        self.highlight_selected()

    def on_language_change(self):
        
        ### update surf maps

        labels_data_tuples = [

            # a 3-tuple containing a string key and 02 surfaces
            # representing it (unhighlighted and highlighted)

            (

                text_identifier,

                *(

                    render_text(

                        # text
                        getattr(t, text_identifier),

                        # text settings
                        **text_settings,

                    )

                    for text_settings in (
                        NORMAL_TEXT_SETTINGS,
                        SELECTED_TEXT_SETTINGS,
                    )

                )

            )

            for text_identifier in (
                'continue',
                'new_game',
                'load_game',
                'kbd_controls',
                'gp_controls',
                'options',
                'links',
                'credits',
                'exit',
            )

        ]

        unhighlighted_surf_map = self.unhighlighted_surf_map
        highlighted_surf_map = self.highlighted_surf_map

        for (
            key,
            unhighlighted_surf,
            highlighted_surf,
        ) in labels_data_tuples:

            unhighlighted_surf_map[key] = unhighlighted_surf
            highlighted_surf_map[key] = highlighted_surf

        ### update items's rects

        for obj in self.full_items:
            obj.rect = unhighlighted_surf_map[obj.key].get_rect()

    def highlight_selected(self):

        unhighlighted_surf_map = self.unhighlighted_surf_map

        for obj in self.items:
            obj.image = unhighlighted_surf_map[obj.key]

        highlighted_obj = self.items[self.current_index]
        highlighted_obj.image = self.highlighted_surf_map[highlighted_obj.key]

        REFS.blue_boy.rect.centery = highlighted_obj.rect.centery
        REFS.blue_boy.rect.right = self.items_left - 10

    def execute_selected(self):

        item_key = self.items[self.current_index].key

        if item_key == 'continue':
            REFS.states.load_game_screen.load_first()

        elif item_key == 'load_game':

            load_game_screen = REFS.states.load_game_screen
            load_game_screen.prepare()

            raise LoopException(next_state=load_game_screen)

        elif item_key == 'new_game':
            start_new_game()

        elif 'controls' in item_key :

            controls_screen = REFS.states.controls_screen
            controls_screen.prepare(item_key)

            raise LoopException(next_state=controls_screen)

        elif item_key == 'options':

            options_screen = REFS.states.options_screen
            options_screen.prepare()

            raise LoopException(next_state=options_screen)

        elif item_key == 'links':

            links_screen = REFS.states.links_screen
            links_screen.prepare()

            raise LoopException(next_state=links_screen)

        elif item_key == 'credits':

            credits_screen = REFS.states.credits_screen
            credits_screen.prepare()

            raise LoopException(next_state=credits_screen)

        elif item_key == 'exit':
            quit_game()

        else:

            raise ValueError(
                "'item_key' must be listed in one"
                " of the previous if/elif clauses."
            )

    def control_item_selection(self):

        for event in SERVICES_NS.get_events():

            if event.type == KEYDOWN:

                if event.key == K_ESCAPE:
                    quit_game()

                elif event.key == K_RETURN:
                    self.start_shooting_animation()

                elif event.key in (K_UP, K_DOWN):

                    steps = -1 if event.key == K_UP else 1
                    self.select_another(steps)

                elif event.key in (
                    KEYBOARD_CONTROLS['up'],
                    KEYBOARD_CONTROLS['down'],
                ):

                    steps = -1 if event.key == KEYBOARD_CONTROLS['up'] else 1
                    self.select_another(steps)

            elif event.type == JOYBUTTONDOWN:

                if event.button == GAMEPAD_CONTROLS['start_button']:
                    self.start_shooting_animation()

            elif event.type == GAMEPADDIRECTIONALPRESSED:

                if event.direction in ('up', 'down'):

                    steps = -1 if event.direction == 'up' else 1
                    self.select_another(steps)

            elif event.type == MOUSEBUTTONDOWN:

                if event.button == 1:
                    self.on_mouse_click(event)

            elif event.type == MOUSEMOTION:
                self.highlight_under_mouse(event)

            elif event.type in GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS:
                GAMEPAD_NS.setup_gamepad_if_existent()

            elif event.type == QUIT:
                quit_game()

    def select_another(self, steps):

        self.current_index = (self.current_index + steps) % self.item_count
        self.highlight_selected()

    def highlight_under_mouse(self, event):

        pos = event.pos

        for index, item in enumerate(self.items):

            if item.rect.collidepoint(pos):
                break

        else:
            return

        self.current_index = index
        self.highlight_selected()

    def on_mouse_click(self, event):

        pos = event.pos

        for index, item in enumerate(self.items):

            if item.rect.collidepoint(pos):
                break

        else:
            return

        self.current_index = index
        self.highlight_selected()
        self.start_shooting_animation()

    def start_shooting_animation(self):

        self.control = self.control_wait_shot_animation
        self.update  = self.update_shot_appearing

        REFS.blue_boy.aniplayer.blend('+shooting')
        REFS.middle_shot.aniplayer.switch_animation('appearing_right')

        shot_center = REFS.blue_boy.rect.move(7, -2).midright
        REFS.middle_shot.rect.center = shot_center

    def control_wait_shot_animation(self):

        for event in SERVICES_NS.get_events():

            if event.type == QUIT:
                quit_game()

    def update_shot_appearing(self):

        aniplayer = REFS.middle_shot.aniplayer

        if aniplayer.main_timing.peek_loops_no(1) == 1:

            aniplayer.switch_animation('idle_right')
            SOUND_MAP['middle_charged_shot_shot.wav'].play()

            self.update = self.update_shot_leaving_screen

    def update_shot_leaving_screen(self):

        shot_rect = REFS.middle_shot.rect

        shot_rect.x += CHARGED_SHOT_SPEED

        if not SCREEN_RECT.colliderect(shot_rect):

            self.control = self.control_item_selection
            self.update = do_nothing
            REFS.blue_boy.aniplayer.switch_animation('idle_right')

            shot_rect.right = SCREEN_RECT.left

            self.execute_selected()

    def draw(self):

        blit_on_screen(BLACK_BG, (0, 0))

        REFS.bb_title.draw()

        self.items.draw()

        REFS.blue_boy.aniplayer.draw()

        REFS.middle_shot.aniplayer.draw()

        update()


def start_new_game():

    timestamp_slot_name = get_custom_datetime_str_for_default_slot_name()
    last_played_date = get_custom_datetime_str_for_last_played()

    save_slot_name = timestamp_slot_name

    next_index = count().__next__

    while True:

        new_save_slot_file = SAVE_SLOTS_DIR / f'{save_slot_name}.pyl'

        if new_save_slot_file.exists():

            save_slot_name = (
                timestamp_slot_name
                + '_'
                + str(next_index()).rjust(3, '0')
            )

        else:
            break

    slot_data = {
        'last_played_date': last_played_date,
    }

    save_pyl(slot_data, new_save_slot_file)


    REFS.slot_data = slot_data
    REFS.slot_path = new_save_slot_file

    transition_screen = REFS.states.transition_screen
    transition_screen.prepare(present_intro)

    raise LoopException(next_state=transition_screen)


def present_intro():
    """Trigger presentation of game's introduction."""

    report_presenter = REFS.states.report_presenter
    report_presenter.prepare('story_intro', on_report_exit=start_first_level)

    raise LoopException(next_state=report_presenter)

def start_first_level():
    """Start first level."""

    level_manager = REFS.states.level_manager
    REFS.level_to_load = 'intro.lvl'
    level_manager.prepare()

    raise LoopException(next_state=level_manager)
