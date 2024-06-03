

### third-party imports

from pygame.locals import (

    QUIT,

    KEYDOWN,
    K_ESCAPE,
    K_RETURN,
    K_DOWN,
    K_UP,

    JOYBUTTONDOWN,

)

from pygame.display import update

from pygame.mixer import music


### local imports

from ..config import (
    REFS, SOUND_MAP, MUSIC_DIR, quit_game
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

from ..pygamesetup.gamepaddirect import setup_gamepad_if_existent

from ..constants import CHARGED_SHOT_SPEED

from ..ourstdlibs.behaviour import do_nothing

from ..exceptions import SwitchStateException

from ..textman import render_text

from ..classes2d.single import UIObject2D

from ..classes2d.collections import UIList2D

from ..userprefsman.main import GAMEPAD_CONTROLS



class MainMenu:

    def __init__(self):

        self.current_index = 0

        ###

        labels_data_tuples = [

            # a 3-tuple containing a string key and 02 surfaces
            # representing it (unhighlighted and highlighted

            (

                key,

                *(
                    render_text(label_title, 'regular', 12, 2, color)
                    for color in ('cyan', 'orange')
                )

            )

            for key, label_title in (
                ('continue', 'Continue'),
                ('new_game', 'New game (demo)'),
                ('load_game', 'Load game'),
                ('kbd_controls', 'Keyboard controls'),
                ('gp_controls', 'Gamepad controls'),
                ('options', 'Options'),
                ('exit', 'Exit game'),
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
                    'exit',
                )

            )

        )

        self.control = self.control_item_selection
        self.update = do_nothing

    def prepare(self):

        items = self.items = self.compact_items

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

        REFS.blue_boy.ap.switch_animation('idle_right')

        self.highlight_selected()

    def highlight_selected(self):

        unhighlighted_surf_map = self.unhighlighted_surf_map

        for obj in self.items:
            obj.image = unhighlighted_surf_map[obj.key]

        highlighted_obj = self.items[self.current_index]
        highlighted_obj.image = self.highlighted_surf_map[highlighted_obj.key]

        REFS.blue_boy.rect.centery = highlighted_obj.rect.centery
        REFS.blue_boy.rect.right = self.items_left - 10

    def execute_selected(self):

        item_key = self.compact_items[self.current_index].key

        if item_key == 'new_game':

            game_state = REFS.get_game_state()
            game_state.prepare()

            raise SwitchStateException(game_state)

        elif 'controls' in item_key :

            controls_screen = REFS.states.controls_screen
            controls_screen.prepare(item_key)

            raise SwitchStateException(controls_screen)

        elif item_key == 'options':

            options_screen = REFS.states.options_screen
            options_screen.prepare()

            raise SwitchStateException(options_screen)

        elif item_key == 'exit':
            quit_game()

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

            elif event.type == JOYBUTTONDOWN:

                if event.button == GAMEPAD_CONTROLS['start_button']:
                    self.start_shooting_animation()

            elif event.type == GAMEPADDIRECTIONALPRESSED:

                if event.direction in ('up', 'down'):

                    steps = -1 if event.direction == 'up' else 1
                    self.select_another(steps)

            elif event.type in GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS:
                setup_gamepad_if_existent()

            elif event.type == QUIT:
                quit_game()

    def select_another(self, steps):

        self.current_index = (self.current_index + steps) % self.item_count
        self.highlight_selected()

    def start_shooting_animation(self):

        self.control = self.control_wait_shot_animation
        self.update  = self.update_shot_appearing

        REFS.blue_boy.ap.blend('+shooting')
        REFS.middle_shot.ap.switch_animation('appearing_right')

        shot_center = REFS.blue_boy.rect.move(7, -2).midright
        REFS.middle_shot.rect.center = shot_center

    def control_wait_shot_animation(self):

        for event in SERVICES_NS.get_events():

            if event.type == QUIT:
                quit_game()

    def update_shot_appearing(self):

        ap = REFS.middle_shot.ap

        if ap.main_timing.peek_loops_no(1) == 1:

            ap.switch_animation('idle_right')
            SOUND_MAP['middle_charged_shot_shot.wav'].play()

            self.update = self.update_shot_leaving_screen

    def update_shot_leaving_screen(self):

        shot_rect = REFS.middle_shot.rect

        shot_rect.x += CHARGED_SHOT_SPEED

        if not SCREEN_RECT.colliderect(shot_rect):

            self.control = self.control_item_selection
            self.update = do_nothing
            REFS.blue_boy.ap.switch_animation('idle_right')

            shot_rect.right = SCREEN_RECT.left

            self.execute_selected()

    def draw(self):

        blit_on_screen(BLACK_BG, (0, 0))

        REFS.bb_title.draw()

        self.items.draw()

        REFS.blue_boy.ap.draw()

        REFS.middle_shot.ap.draw()

        update()
