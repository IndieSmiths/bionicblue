

### third-party imports

from pygame import Surface

from pygame.draw import (
    rect as draw_rect,
    polygon as draw_polygon,
    circle as draw_circle,
)

from pygame.math import Vector2


### local imports

from ..pygamesetup import SERVICES_NS

from ..classes2d.single import UIObject2D



def _get_slider_bg_surf():

    surf = Surface((110, 10)).convert()
    surf.fill('grey40')

    thin_rectangle = surf.get_rect().inflate(-10, -8)
    draw_rect(surf, 'grey80', thin_rectangle)

    return surf

SLIDER_BG = _get_slider_bg_surf()

def _get_cursor_surf():

    surf = Surface((7, 7)).convert()
    return surf

CURSOR_SURF = _get_cursor_surf()



class HundredSlider(UIObject2D):

    def __init__(
        self,
        value=0,
        on_value_change=do_nothing,
        coordinates_name='topleft',
        coordinates_value=(0, 0),
    ):

        self.image = CLEAN_SLIDER_SURF.copy()
        self.rect = CLEAN_SLIDER_SURF.get_rect()
        self.on_value_change = on_value_change
        self.active = False

        self.set(value, False)


    ### update

    def act_on_mouse_state(self):

        if self.active:

            ### if mouse is over slider...

            mouse_pos = SERVICES_NS.get_mouse_pos()

            if self.rect.collidepoint(mouse_pos):

                ### if its first button is pressed, update value
                ### based on mouse x pos relative to slider's length

                if SERVICES_NS.get_mouse_pressed()[0]:
                    self.set_value_from_mouse_pos(mouse_pos[0])

                ### otherwise, make inactive
                else:
                    self.active = False

            ### otherwise, make inactive
            else:
                self.active = False

    update = check_mouse_state

    ###

    def set(self, value, execute_on_value_change=True):

        self.value = value

        if execute_on_value_change:
            self.on_value_change()

    def set_value_from_mouse_pos(self, mouse_x):

        ### calculate the distance between mouse x and the surf's origin x
        horiz_distance_from_surf_origin = mouse_x - self.rect.x

        ### remove 5 to compensate for left padding
        horiz_distance_from_surf_origin -= 5

        ### clamp the value so it is >= 0 and <= 100
        clamped_value = min(max(horiz_distance_from_surf_origin, 0), 100)

        ### finally set the value
        self.set(clamped_value)
