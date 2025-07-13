
### third-party import

from pygame.locals import (

    QUIT,

    KEYDOWN,
    K_ESCAPE,
    K_RETURN,
    K_DOWN,
    K_UP,

    JOYBUTTONDOWN,

)

from pygame.display import update as update_screen


### local imports

from ..pygamesetup import SERVICES_NS

from ..pygamesetup.constants import (
    SCREEN,
    SCREEN_COPY,
    SCREEN_TRANSP_OVERLAY,
    SCREEN_RECT,
    GAMEPADDIRECTIONALPRESSED,
    blit_on_screen,
)

from ..userprefsman.main import GAMEPAD_CONTROLS

from ..config import REFS, LoopException, quit_game

from ..classes2d.single import UIObject2D

from ..classes2d.collections import UIList2D

from ..textman import render_text



PAUSED_TEXT_SURF = render_text('Pause menu', 'regular', 22, 4)
PAUSED_TEXT_RECT = PAUSED_TEXT_SURF.get_rect()


def pause():

    pm = REFS.states.pause_menu
    pm.prepare()
    raise LoopException(next_state=pm)

def resume():
    raise LoopException(next_state=REFS.states.level_manager)


class PauseMenu:

    def __init__(self):

        self.current_index = 0
        self.indicator = (
            UIObject2D.from_surface(
                render_text('>', 'regular', 12, 2, 'orange')
            )
        )

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
                ('resume', 'Resume'),
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

        items = self.items = (

            UIList2D(

                obj_map[key]

                for key in (
                    'resume',
                    'exit',
                )

            )

        )

        self.item_count = len(items)

        items.rect.snap_rects_ip(
            retrieve_pos_from='midbottom',
            assign_pos_to='midtop',
        )

        items.rect.center = SCREEN_RECT.center

        PAUSED_TEXT_RECT.midbottom = items.rect.move(0, -10).midtop

        self.highlight_selected()

    def prepare(self):

        blit_on_screen(SCREEN_TRANSP_OVERLAY, (0, 0))
        blit_on_screen(PAUSED_TEXT_SURF, PAUSED_TEXT_RECT)

        SCREEN_COPY.blit(SCREEN, (0, 0))

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
        self.indicator.rect.midright = highlighted_obj.rect.move(-5, 0).midleft

    def execute_selected(self):

        item_key = self.items[self.current_index].key

        if item_key == 'resume':
            resume()

        elif item_key == 'exit':
            quit_game()

    def update(self): pass

    def draw(self):

        blit_on_screen(SCREEN_COPY, (0, 0))

        self.items.draw()
        self.indicator.draw()

        update_screen()
