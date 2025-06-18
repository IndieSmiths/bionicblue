
### standard library import
from itertools import cycle


### third-party import
from pygame import Surface


### local imports

from ....pygamesetup.constants import blit_on_screen

from ....ani2d.player import AnimationPlayer2D



def increment_x(r, amount):
    r.x += amount

def increment_y(r, amount):
    r.y += amount

H_PLATFORM_SURF = Surface((48, 16)).convert()
H_PLATFORM_SURF.fill('tan1')
V_PLATFORM_SURF = Surface((48, 16)).convert()
V_PLATFORM_SURF.fill('aquamarine2')

PlatformRotorBlades = type('PlatformRotorBlades', (), {})


class FloatingPlatform:

    def __init__(self, name, pos):

        self.name = name

        blades = self.blades = PlatformRotorBlades()

        blades.aniplayer = (
            AnimationPlayer2D(blades, 'platform_rotor_blades', 'moving')
        )

        if name == 'floating_h_platform':

            image = self.image = H_PLATFORM_SURF
            self.increment = increment_x

        elif name == 'floating_v_platform':

            image = self.image = V_PLATFORM_SURF
            self.increment = increment_y

        else:

            raise RuntimeError(
                "This else block should never be reached because"
                " because value must always enable one of the"
                " previous if/elif blocks."
            )

        ###

        rect = self.rect = image.get_rect()
        setattr(self.rect, 'midtop', pos)
        self.colliderect = rect.colliderect
        blades.rect.midtop = rect.midbottom

        ###
        self.touched = None

        ###
        self.next_amount_to_move = cycle(

            (
                *( ( 1,)  *32*4),
                *( (-1,)  *32*4),
            )

        ).__next__

    def touched_top(self, obj):
        self.touched = obj

    def update(self):

        rect = self.rect

        center = rect.center

        amount = self.next_amount_to_move()

        self.increment(rect, amount)

        if self.touched is not None:

            self.increment(self.touched.rect, amount)
            self.touched = None

        self.blades.rect.midtop = rect.midbottom

        if rect.center != center:

            self.delta += tuple(
                a - b
                for a, b
                in zip(rect.center, center)
            )

    def draw(self):

        blit_on_screen(self.image, self.rect)
        self.blades.aniplayer.draw()
