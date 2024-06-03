

### third-party imports

from pygame import Surface

from pygame.draw import (
    rect as draw_rect,
    polygon as draw_polygon,
    circle as draw_circle,
)

from pygame.math import Vector2


### local imports

from ..classes2d.single import UIObject2D



def _get_slider_bg_surf():

    surf = Surface((110, 10)).convert()
    surf.fill('grey40')
    return surf

SLIDER_BG = _get_slider_bg_surf()

def _get_cursor_surf():

    surf = Surface((7, 7)).convert()
    return surf

CURSOR_SURF = _get_cursor_surf()



class HundredSlider(UIObject2D):

    def __init__(
        self,
        on_set_command,
        coordinates_name='topleft',
        coordinates_value=(0, 0),
    ):

        self.image = CLEAN_SLIDER_SURF.copy()
        self.rect = CLEAN_SLIDER_SURF.get_rect()
