
### standard library import

from functools import partial

from itertools import cycle


### third-party imports

from pygame import Surface, Rect

from pygame.draw import circle as draw_circle


### local imports

from ......config import REFS, COLORKEY

from ......pygamesetup.constants import blit_on_screen, msecs_to_frames

from ....common import PROJECTILES, append_task



RADII = (
    tuple(range(1, 24, 4))
    + tuple(reversed(range(1, 24, 4)[1:-1]))
)

RADIUS_TO_AREA_MAP = {
    radius: Rect(0, 0, radius*2, radius*2)
    for radius in set(RADII)
}

_RADIUS_SWITCH_MSECS = 200
RADIUS_SWITCH_FRAMES = msecs_to_frames(_RADIUS_SWITCH_MSECS)

_LIFESPAN_MSECS = 6000
LIFESPAN_FRAMES = msecs_to_frames(_LIFESPAN_MSECS)

MAX_RADIUS = max(RADII)
_max_area = RADIUS_TO_AREA_MAP[MAX_RADIUS]
FULL_SIZE = _max_area.size
CENTER = _max_area.center


class ElectricGlobe:

    def __init__(self, center, orientation):

        image = self.image = Surface(FULL_SIZE).convert()

        image.set_colorkey(COLORKEY)
        image.fill(COLORKEY)

        self.radius_switch_countdown = RADIUS_SWITCH_FRAMES
        self.lifespan_countdown = LIFESPAN_FRAMES

        self.next_radius = cycle(RADII).__next__

        self.radius = self.next_radius()

        self.update_image()

        self.rect = image.get_rect()
        setattr(self.rect, 'center', center)

        self.x_speed = -1 if orientation == 'left' else 1

    def update(self):

        self.lifespan_countdown -= 1
        self.radius_switch_countdown -= 1

        if self.lifespan_countdown == 0:

            self.trigger_kill()
            return

        if self.radius_switch_countdown == 0:

            self.radius_switch_countdown = RADIUS_SWITCH_FRAMES
            self.radius = self.next_radius()
            self.update_image()

        rect = self.rect
        rect.move_ip(self.x_speed, 0)

        ### destroy if hits player...

        player = REFS.states.level_manager.player

        if rect.colliderect(player.rect) and self.confirm_radius(player.rect):

            player.damage(4)
            self.trigger_kill()
            return

    def update_image(self):

        image = self.image

        image.fill(COLORKEY)
        draw_circle(image, 'white', CENTER, self.radius, 1)

    def trigger_kill(self):
        append_task(partial(PROJECTILES.remove, self))

    def confirm_radius(self, colliding_rect):

        if self.radius != MAX_RADIUS:

            area = RADIUS_TO_AREA_MAP[self.radius]
            area.center = self.rect.center

            return area.colliderect(colliding_rect)

        return True

    def draw(self):
        blit_on_screen(self.image, self.rect)

