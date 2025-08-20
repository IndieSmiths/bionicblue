"""Facility with objects/values to assist main module in this subpackage."""

### standard library imports
from itertools import cycle, takewhile, chain, product


### third-party import
from pygame import Rect


### local import
from .......pointsman2d.create import yield_circle_points



RADII = (
    tuple(range(1, 24, 4))
    + tuple(reversed(range(1, 24, 4)[1:-1]))
)

UNIQUE_RADII = frozenset(RADII)

SORTED_UNIQUE_RADII = sorted(UNIQUE_RADII)
MIN_RADIUS, *_, MAX_RADIUS = SORTED_UNIQUE_RADII

RADIUS_TO_AREA_MAP = {
    radius: Rect(0, 0, radius*2, radius*2)
    for radius in UNIQUE_RADII
}

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

