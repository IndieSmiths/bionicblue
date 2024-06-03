

### third-party imports

from pygame import Surface, Rect

from pygame.draw import lines as draw_lines


### local imports

from ..ourstdlibs.behaviour import do_nothing

from ..classes2d.single import UIObject2D



FALSE_SURF = Surface((14, 14)).convert()
FALSE_SURF.fill('grey80')

def _get_true_surf():

    surf = FALSE_SURF.copy()
    rect = FALSE_SURF.get_rect().inflate(-6, -6)

    points = tuple(

        getattr(rect, attr_name)

        for attr_name in (
            'midleft',
            'midbottom',
            'topright',
        )

    )

    draw_lines(
        surf,
        'blue',
        False, # whether last point should be connected to first one
        points,
        width=3
    )

    return surf

TRUE_SURF = _get_true_surf()

RECT_DATA = tuple(TRUE_SURF.get_rect())



class Checkbutton(UIObject2D):

    def __init__(
        self,
        value=False,
        name='checkbutton',
        on_value_change=do_nothing,
        coordinates_name='topleft',
        coordinates_value=(0, 0),
    ):
        """"""
        ###
        self.value = bool(value)
        self.image = TRUE_SURF if self.value else FALSE_SURF

        ###
        self.name = name

        ###
        self.rect = rect = Rect(RECT_DATA)

        ###
        self.on_value_change = on_value_change

        ###
        setattr(
            rect,
            coordinates_name,
            coordinates_value,
        )

        ###
        self.update = do_nothing

    def set(self, value, execute_on_value_change=True):

        new_value = bool(value)

        if new_value != self.value:

            self.value = new_value
            self.image = TRUE_SURF if new_value else FALSE_SURF

            if execute_on_value_change:
                self.on_value_change()

    def get(self):
        return self.value

    def toggle_value(self):
        self.set(not self.value)

    def on_mouse_click(self, event):
        self.toggle_value()
