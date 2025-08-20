"""Facility for electric globe projectile."""

### standard library import

from functools import partial

from itertools import cycle, takewhile, chain, product


### third-party imports

from pygame import Surface, Rect

from pygame.draw import (
    circle as draw_circle,
    lines as draw_lines,
)


### local imports

from ......config import REFS, COLORKEY

from ......pointsman2d.create import yield_circle_points

from ......pygamesetup.constants import blit_on_screen, msecs_to_frames

from ....common import PROJECTILES, append_task



RADII = (
    tuple(range(1, 24, 4))
    + tuple(reversed(range(1, 24, 4)[1:-1]))
)

UNIQUE_RADII = frozenset(RADII)

RADIUS_TO_AREA_MAP = {
    radius: Rect(0, 0, radius*2, radius*2)
    for radius in UNIQUE_RADII
}

_RADIUS_SWITCH_MSECS = 200
RADIUS_SWITCH_FRAMES = msecs_to_frames(_RADIUS_SWITCH_MSECS)

_LIFESPAN_MSECS = 6000
LIFESPAN_FRAMES = msecs_to_frames(_LIFESPAN_MSECS)

MAX_RADIUS = max(UNIQUE_RADII)
_max_area = RADIUS_TO_AREA_MAP[MAX_RADIUS]
FULL_SIZE = _max_area.size
CENTER = _max_area.center

NO_OF_POINTS = 18
NO_OF_LIGHTNING_BOLTS = 3
INDEX_JUMP = NO_OF_POINTS // NO_OF_LIGHTNING_BOLTS

LIGHTNING_BOLT_INDICES = tuple(

    chain.from_iterable(
        [

            (
                (i-1) % NO_OF_POINTS,
                i,
                (i+1) % NO_OF_POINTS,
            )

            for i in range(NO_OF_POINTS)
        ]
    )

)

CIRCLE_POINTS_MAP = {
    radius: list(yield_circle_points(NO_OF_POINTS, radius, CENTER))
    for radius in UNIQUE_RADII
}

SORTED_UNIQUE_RADII = sorted(UNIQUE_RADII)

ORDERED_UNIQUE_UP_TO_RADIUS = {
    radius: list(takewhile(lambda item: item <= radius, SORTED_UNIQUE_RADII))
    for radius in UNIQUE_RADII
}

ORDERED_CIRCLE_POINTS_MAP = {

    radius:  [

        CIRCLE_POINTS_MAP[r]
        for r in ORDERED_UNIQUE_UP_TO_RADIUS[radius]

    ]

    for radius in SORTED_UNIQUE_RADII

}

OFFSETS = cycle((-1, 1))


lbi = [] # lightning bolt indices

lpts = [] # lightning points

def _get_lightning_points(radius_bolt_index_pair):

    radius, bolt_index = radius_bolt_index_pair
    
    circles = ORDERED_CIRCLE_POINTS_MAP[radius]

    all_lightning_points = []

    n = bolt_index

    lbi.clear()
    lbi.append(n)

    for _ in range(NO_OF_LIGHTNING_BOLTS-1):
        n = (n + INDEX_JUMP) % NO_OF_POINTS
        lbi.append(n)

    for i in lbi:

        lpts.clear()

        for circle, offset in zip(circles, OFFSETS):

            offset = (offset + i) % NO_OF_POINTS
            lpts.append(circle[offset])

        all_lightning_points.append(tuple(lpts))

    lbi.clear()
    lpts.clear()

    return all_lightning_points


LIGHTNING_POINTS_MAP = {

    radius_bolt_index_pair: _get_lightning_points(radius_bolt_index_pair)

    for radius_bolt_index_pair
    in product(SORTED_UNIQUE_RADII[1:], range(NO_OF_POINTS))

}

MIN_RADIUS = min(UNIQUE_RADII)


class ElectricGlobe:

    def __init__(self, center, orientation):

        image = self.image = Surface(FULL_SIZE).convert()

        image.set_colorkey(COLORKEY)
        image.fill(COLORKEY)

        self.radius_switch_countdown = RADIUS_SWITCH_FRAMES
        self.lifespan_countdown = LIFESPAN_FRAMES

        self.next_radius = cycle(RADII).__next__
        self.next_lightning_bolt = cycle(LIGHTNING_BOLT_INDICES).__next__
        self.lightning_bolt_indices = []
        self.lightning_points = []

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

        if self.radius != MIN_RADIUS:

            for lightning_points in (
                LIGHTNING_POINTS_MAP[(self.radius, self.next_lightning_bolt())]
            ):

                draw_lines(image, 'yellow', False, lightning_points, 2)
                draw_lines(image, 'cyan', False, lightning_points, 1)

        draw_circle(image, 'yellow', CENTER, self.radius, 1)

    def trigger_kill(self):
        append_task(partial(PROJECTILES.remove, self))

    def confirm_radius(self, colliding_rect):

        if self.radius != MAX_RADIUS:

            area = RADIUS_TO_AREA_MAP[self.radius]
            area.center = self.rect.center

            return area.colliderect(colliding_rect)

        return True

    def draw(self):
        self.update_image()
        blit_on_screen(self.image, self.rect)
