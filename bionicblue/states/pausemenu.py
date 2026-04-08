
### third-party import

from pygame import Surface

from pygame.locals import (

    QUIT,

    KEYDOWN,
    K_ESCAPE,
    K_RETURN,
    K_DOWN,
    K_UP,

    JOYBUTTONDOWN,

)

from pygame.draw import rect as draw_rect

from pygame.mixer import music


### local imports

from ..pygamesetup import SERVICES_NS

from ..pygamesetup.constants import (
    GENERAL_NS,
    SCREEN,
    SCREEN_COPY,
    SCREEN_TRANSP_OVERLAY,
    SCREEN_RECT,
    GAMEPADDIRECTIONALPRESSED,
    blit_on_screen,
)

from ..userprefsman.main import GAMEPAD_CONTROLS

from ..config import (
    REFS,
    COLORKEY,
    SOUND_MAP,
    MUSIC_DIR,
    LoopException,
    quit_game,
)

from ..classes2d.single import UIObject2D

from ..classes2d.collections import UIList2D

from ..textman import render_text, update_text_surface

from ..userprefsman.main import USER_PREFS

from ..translatedtext import TRANSLATIONS, on_language_change



t = TRANSLATIONS.pause_menu

TITLE_TEXT_SETTINGS = {
    'style': 'regular',
    'size': 12,
    'padding': 4,
}

NORMAL_LABEL_TEXT_SETTINGS = {
    'style': 'regular',
    'size': 12,
    'padding': 4,
    'foreground_color': 'cyan',
}

SELECTED_LABEL_TEXT_SETTINGS = {
    'style': 'regular',
    'size': 12,
    'padding': 4,
    'foreground_color': 'orange',
}

ITEM_KEYS = (
    'resume',
    'main_menu',
    'quit_game',
)


def resume():

    SOUND_MAP['pause_out.wav'].play()
    raise LoopException(next_state=REFS.states.level_manager)


def pause():

    SOUND_MAP['pause_in.wav'].play()

    pm = REFS.states.pause_menu
    pm.prepare()
    raise LoopException(next_state=pm)

def leave_to_main_menu():

    REFS.states.level_manager.cleanup()

    ###

    play_mode_name = GENERAL_NS.play_mode_name

    if play_mode_name == 'record':
        GENERAL_NS.save_play_data()

    elif play_mode_name == 'replay':
        GENERAL_NS.perform_replay_mode_exit_setups()

    else:

        raise RuntimeError(
            "'play_mode_name' must be in if/elif blocks."
            f" '{play_mode_name}' is not."
        )

    ###

    transition_screen = REFS.states.transition_screen
    transition_screen.prepare(go_to_main_menu)

    raise LoopException(
        next_state=transition_screen,
        next_play_mode_name='normal',
    )

def go_to_main_menu():

    music_volume = (
        (USER_PREFS['MASTER_VOLUME']/100)
        * (USER_PREFS['MUSIC_VOLUME']/100)
    )

    music.set_volume(music_volume)
    music.load(str(MUSIC_DIR / 'title_screen_by_juhani_junkala.ogg'))
    music.play(-1)

    raise LoopException(
        next_state=REFS.states.main_menu,
        clear_tasks=True,
        prepare=True,
    )


class PauseMenu:

    def __init__(self):


        labels_data_tuples = [

            # a 3-tuple containing a string key and 02 surfaces
            # representing it (unhighlighted and highlighted

            (

                key,

                *(

                    render_text(
                        getattr(t.labels, key),
                        **text_settings,
                    )

                    for text_settings in (
                        NORMAL_LABEL_TEXT_SETTINGS,
                        SELECTED_LABEL_TEXT_SETTINGS,
                    )
                )

            )

            for key in ITEM_KEYS

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

        items = self.items = (

            UIList2D(

                obj_map[key]

                for key in ITEM_KEYS

            )

        )

        self.item_count = len(items)

        items.rect.snap_rects_ip(
            retrieve_pos_from='midbottom',
            assign_pos_to='midtop',
        )

        caption = self.caption = (
            UIObject2D.from_surface(
                render_text(t.caption, **TITLE_TEXT_SETTINGS)
            )
        )

        caption.rect.midbottom = items[0].rect.move(0, -10).midtop

        items.insert(0, caption)
        items.rect.center = SCREEN_RECT.center
        items.pop(0)

        self.items_bg = items_bg = UIObject2D()
        self.reset_items_bg()

        self.current_index = 0
        self.highlight_selected()

        ###
        on_language_change.append(self.on_language_change)

    def reset_items_bg(self):

        items = self.items

        items.insert(0, self.caption)
        new_rect = items.rect.inflate(10, 10)
        items.pop(0)

        surf = Surface(new_rect.size).convert()
        surf.set_colorkey(COLORKEY)
        surf.fill(COLORKEY)

        rect_for_drawing = surf.get_rect()

        draw_rect(surf, 'black', rect_for_drawing, border_radius=10)
        draw_rect(surf, 'white', rect_for_drawing, 1, border_radius=10)

        self.items_bg.image = surf
        self.items_bg.rect = new_rect

    def prepare(self):

        blit_on_screen(SCREEN_TRANSP_OVERLAY, (0, 0))

        SCREEN_COPY.blit(SCREEN, (0, 0))

        self.current_index = 0
        self.highlight_selected()

    def on_language_change(self):

        ### update caption

        update_text_surface(
            self.caption,
            t.caption,
            TITLE_TEXT_SETTINGS,
            pos_to_align='midbottom',
        )

        ### update remaining items

        usm = self.unhighlighted_surf_map
        hsm = self.highlighted_surf_map

        for obj in self.items:

            ## update object

            key = obj.key

            text = getattr(t.labels, key)

            # maps

            for map_obj, text_settings in (
                (usm, NORMAL_LABEL_TEXT_SETTINGS),
                (hsm, SELECTED_LABEL_TEXT_SETTINGS),
            ):
                map_obj[key] = render_text(text, **text_settings)

            # current image and rect

            obj.image = usm[key]

            midtop = obj.rect.midtop
            obj.rect = obj.image.get_rect()
            obj.rect.midtop = midtop

        ### now that all items are updated, reset background for items
        self.reset_items_bg()

    def control(self):

        for event in SERVICES_NS.get_events():

            if event.type == KEYDOWN:

                if event.key == K_ESCAPE:
                    resume()

                elif event.key == K_RETURN:
                    self.execute_selected()

                elif event.key in (K_UP, K_DOWN):

                    steps = -1 if event.key == K_UP else 1
                    self.select_another(steps)

            elif event.type == JOYBUTTONDOWN:

                if event.button == GAMEPAD_CONTROLS['start_button']:
                    self.execute_selected()

            elif event.type == GAMEPADDIRECTIONALPRESSED:

                if event.direction in ('up', 'down'):

                    steps = -1 if event.direction == 'up' else 1
                    self.select_another(steps)

            elif event.type == QUIT:
                quit_game()

    def select_another(self, steps):

        self.current_index = (self.current_index + steps) % self.item_count
        self.highlight_selected()

    def highlight_selected(self):

        unhighlighted_surf_map = self.unhighlighted_surf_map

        for obj in self.items:
            obj.image = unhighlighted_surf_map[obj.key]

        highlighted_obj = self.items[self.current_index]
        highlighted_obj.image = self.highlighted_surf_map[highlighted_obj.key]
        self.selected_rect = self.items[self.current_index].rect

    def execute_selected(self):

        item_key = self.items[self.current_index].key

        if item_key == 'resume':
            resume()

        elif item_key == 'main_menu':
            leave_to_main_menu()

        elif item_key == 'quit_game':
            quit_game()

        else:
            raise ValueError("'item_key' must be among if/elif clauses above")

    def update(self): pass

    def draw(self):

        blit_on_screen(SCREEN_COPY, (0, 0))

        self.items_bg.draw()
        self.caption.draw()
        self.items.draw()

        draw_rect(
            SCREEN,
            'orange',
            self.selected_rect,
            1,
            border_radius=8,
        )

        SERVICES_NS.update_screen()
