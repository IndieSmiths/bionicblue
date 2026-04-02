"""Facility with class extension for report presenter."""

### third-party imports

from pygame import Rect

from pygame.locals import (

    QUIT,

    KEYDOWN,
    K_RETURN,
    K_DOWN,
    K_UP,
    K_LEFT,
    K_RIGHT,

    JOYBUTTONDOWN,

)

from pygame.math import Vector2

from pygame.display import update

from pygame.draw import rect as draw_rect


### local imports

from ...config import REFS, LoopException, quit_game

from ...pygamesetup import SERVICES_NS

from ...pygamesetup.constants import (
    SCREEN,
    SCREEN_RECT,
    GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS,
)

from ...pygamesetup.gamepadservices import GAMEPAD_NS

from ...ourstdlibs.pyl import load_pyl

from ...textman import render_text

from ...classes2d.single import UIObject2D

from ...classes2d.collections import UIList2D

from ...ani2d.player import AnimationPlayer2D

from ...surfsman import draw_border

from ...userprefsman.main import USER_PREFS, KEYBOARD_CONTROLS, GAMEPAD_CONTROLS

from ...translatedtext import TRANSLATIONS, on_language_change

from .constants import (
    REPORT_TEXT_SETTINGS,
    UPPER_LIMIT,
    LOWER_LIMIT,
    PANEL_CACHE,
)



INSTRUCTIONAL_TEXT_SETTINGS = {
    'style': 'regular',
    'size': 12,
    'padding': 0,
    'foreground_color': 'yellow',
    'background_color': 'blue4',
}


##

##

SCROLL_SPEED = 4
OBJ_MOVE_STEPS = 70

VERTICAL_LIMIT_TO_SHOW_VISUALS = SCREEN_RECT.centery + 40

###
SCREEN_HEADER_AREA = Rect(0, 0, SCREEN_RECT.width, 14)
SCREEN_FOOTER_AREA = SCREEN_HEADER_AREA.copy()
SCREEN_FOOTER_AREA.bottom = SCREEN_RECT.bottom



### class definition

class ReportLoopManagement:
    """Loop management for report presenter class."""

    def control(self):
        """Let user navigate report or skip altogether."""

        for event in SERVICES_NS.get_events():

            if event.type == KEYDOWN:

                if event.key == K_RETURN:
                    self.leave_report()

            elif event.type == JOYBUTTONDOWN:

                if event.button == GAMEPAD_CONTROLS['start_button']:
                    self.leave_report()

            elif event.type in GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS:
                GAMEPAD_NS.setup_gamepad_if_existent()

            elif event.type == QUIT:
                quit_game()

        ###

        pressed_state = SERVICES_NS.get_pressed_keys()

        if (

            pressed_state[K_DOWN]
            or pressed_state[K_RIGHT]
            or pressed_state[KEYBOARD_CONTROLS['down']]
            or pressed_state[KEYBOARD_CONTROLS['right']]
            or GAMEPAD_NS.x_sum > 0
            or GAMEPAD_NS.y_sum > 0

        ):
            self.move_forward()

        elif (

            pressed_state[K_UP]
            or pressed_state[K_LEFT]
            or pressed_state[KEYBOARD_CONTROLS['up']]
            or pressed_state[KEYBOARD_CONTROLS['left']]
            or GAMEPAD_NS.x_sum < 0
            or GAMEPAD_NS.y_sum < 0

        ):
            self.move_backwards()

    def leave_report(self):

        self.clear_collections()


        transition_screen = REFS.states.transition_screen

        on_report_exit = self.on_report_exit
        del self.on_report_exit
        transition_screen.prepare(on_report_exit)

        raise LoopException(next_state=transition_screen)

    def update(self):

        objs_to_remove = self.objs_to_remove
        ###

        images = self.images
        images_ta = self.images_to_advance


        for obj in images:

            panel_rect = PANEL_CACHE[obj.panel_index].rect

            if panel_rect.top < VERTICAL_LIMIT_TO_SHOW_VISUALS:
                images_ta.append(obj)

        for obj in images_ta:

            panel_rect = PANEL_CACHE[obj.panel_index].rect

            if SCREEN_RECT.colliderect(panel_rect):
                advance_position(obj, panel_rect)

            if obj in images:
                objs_to_remove.append(obj)

        while objs_to_remove:
            images.remove(objs_to_remove.pop())

        ###

        anisprites = self.anisprites
        anisprites_ta = self.anisprites_to_advance

        for obj in self.anisprites:

            panel_rect = PANEL_CACHE[obj.panel_index].rect

            if panel_rect.top < VERTICAL_LIMIT_TO_SHOW_VISUALS:
                anisprites_ta.append(obj)

        for obj in anisprites_ta:

            panel_rect = PANEL_CACHE[obj.panel_index].rect

            if SCREEN_RECT.colliderect(panel_rect):
                advance_position(obj, panel_rect)

            if obj in anisprites:
                objs_to_remove.append(obj)

        while objs_to_remove:
            anisprites.remove(objs_to_remove.pop())

    def move_forward(self):

        vobjs = self.all_visible_objs
        vobjs_rect = vobjs.rect

        ## if bottom below lower limit...

        if vobjs_rect.bottom > LOWER_LIMIT:

            vobjs.rect.move_ip(0, -SCROLL_SPEED)

            ## if bottom ends up above lower limit...

            if vobjs_rect.bottom < LOWER_LIMIT:
                vobjs.rect.bottom = LOWER_LIMIT

    def move_backwards(self):

        vobjs = self.all_visible_objs
        vobjs_rect = vobjs.rect

        ## if top above upper limit...

        if vobjs_rect.top < UPPER_LIMIT:

            vobjs.rect.move_ip(0, SCROLL_SPEED)

            ## if top ends up below upper limit...

            if vobjs_rect.top > UPPER_LIMIT:
                vobjs.rect.top = UPPER_LIMIT


    def draw(self):

        SCREEN.fill('black')

        for obj in self.all_visible_objs:

            if isinstance(obj, UIList2D):
                for line in obj:
                    for word in line:
                        word.draw()

            else:
                obj.draw()

        self.images_to_advance.draw()

        for obj in self.anisprites_to_advance:
            obj.aniplayer.draw()

        SCREEN.fill('blue4', SCREEN_HEADER_AREA)
        SCREEN.fill('blue4', SCREEN_FOOTER_AREA)

        self.directionals_label.draw()

        ### progress or continue label

        report_progress = (

            1 - (

                (self.all_visible_objs.rect.bottom - LOWER_LIMIT)

                / self.report_height

            )

        )

        if report_progress < 1:
            self.draw_progress_widgets(report_progress)

        else:
            self.exit_label.draw()

        update()


    def draw_progress_widgets(self, progress):

        self.progress_label.draw()

        self.progress_fill_rect.width = (
            self.progress_outline_rect.width * progress
        )

        if progress < .3:
            progress_color = 'red'
        elif progress > .7:
            progress_color = 'green'
        else:
            progress_color = 'orangered'

        draw_rect(
            SCREEN,
            progress_color,
            self.progress_fill_rect,
        )

        draw_rect(
            SCREEN,
            'yellow',
            self.progress_outline_rect,
            1,
        )


### utility functions

def advance_position(obj, panel_rect):

    rect = obj.rect

    start_pos = get_relative_topleft(rect, panel_rect, *obj.start_pos)
    end_pos = get_relative_topleft(rect, panel_rect, *obj.end_pos)

    rect.topleft = Vector2(start_pos).lerp(end_pos, obj.step_no/OBJ_MOVE_STEPS)

    if obj.step_no < OBJ_MOVE_STEPS:
        obj.step_no += 1

def get_relative_topleft(
    rect_a,
    rect_b,
    rect_a_attr_name,
    rect_b_attr_name,
    offset,
):

    setattr(

        rect_a,

        rect_a_attr_name,

        getattr(
            rect_b.move(offset),
            rect_b_attr_name,
        ),

    )

    return rect_a.topleft
