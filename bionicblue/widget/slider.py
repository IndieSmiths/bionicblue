

### standard library import
from functools import partialmethod


### third-party imports

from pygame import Surface

from pygame.draw import rect as draw_rect

from pygame.math import Vector2


### local imports

from ..pygamesetup import SERVICES_NS

from ..ourstdlibs.behaviour import do_nothing

from ..classes2d.single import UIObject2D

from ..textman import render_text



def _get_slider_bg_surf():

    surf = Surface((135, 14)).convert()
    surf.fill('black')

    draw_rect(surf, 'grey40', (0, 0, 110, 14))

    thin_rectangle = surf.get_rect().inflate(-10, -8)
    thin_rectangle.width = 100
    draw_rect(surf, 'grey80', thin_rectangle)

    return surf

SLIDER_BG = _get_slider_bg_surf()


def _get_cursor_surf():

    surf = Surface((2, 6)).convert()
    surf.fill('blue')

    return surf


CURSOR_SURF = _get_cursor_surf()
CURSOR_RECT = CURSOR_SURF.get_rect()

###

LABEL_TEXT_SETTINGS = {
    'style': 'regular',
    'size': 12,
    'padding': 1,
    'foreground_color': 'white',
    'background_color': 'black',
}

###



class HundredSlider(UIObject2D):

    def __init__(
        self,
        value=0,
        name='slider',
        on_value_change=do_nothing,
        coordinates_name='topleft',
        coordinates_value=(0, 0),
    ):

        self.image = SLIDER_BG.copy()
        self.rect = rect = SLIDER_BG.get_rect()
        self.name = name
        self.on_value_change = on_value_change
        self.active = False

        self.value = int(value)
        self.update_image()

        setattr(
            rect,
            coordinates_name,
            coordinates_value,
        )


    ### update

    def update(self):

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

    #update = act_on_mouse_state

    ###

    def set(self, value, execute_on_value_change=True):

        if value != self.value:

            self.value = value
            self.update_image()

            if execute_on_value_change:
                self.on_value_change()

    def get(self):
        return self.value

    def add(self, amount):

        new_value = self.get() + amount
        clamped_new_value = max(0, min(100, new_value))
        self.set(clamped_new_value)

    decrement = partialmethod(add, -1)
    increment = partialmethod(add, 1)

    def set_value_from_mouse_pos(self, mouse_x):

        ### calculate the distance between mouse x and the surf's origin x
        horiz_distance_from_surf_origin = mouse_x - self.rect.x

        ### remove 5 to compensate for left padding
        horiz_distance_from_surf_origin -= 5

        ### clamp the value so it is >= 0 and <= 100
        clamped_value = min(max(horiz_distance_from_surf_origin, 0), 100)

        ### finally set the value
        self.set(clamped_value)

    def update_image(self):

        image = self.image
        image.blit(SLIDER_BG, (0, 0))

        CURSOR_RECT.centery = self.rect.height // 2
        CURSOR_RECT.centerx = 5 + self.value
        image.blit(CURSOR_SURF, CURSOR_RECT)

        number_text = str(self.value).rjust(3, ' ')

        text_surf = render_text(number_text, **LABEL_TEXT_SETTINGS)
        image.blit(text_surf, (110, 0))

    def on_mouse_click(self, event):
        self.active = True
