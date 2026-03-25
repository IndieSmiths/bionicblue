
### standard library import
from itertools import product

### third-party imports

from pygame import Rect, Surface

from pygame.math import Vector2

from pygame.draw import rect as draw_rect



BUILDING_SURF_MAP = {}
window_rect = Rect()

def get_building_surf(
    window_size,
    no_of_windows_on_same_floor,
    no_of_stories,
    padding_around_windows,
    building_color=(69, 214, 255),
    window_color=(69, 184, 255),
):

    key = ( 
        window_size,
        no_of_windows_on_same_floor,
        no_of_stories,
        padding_around_windows,
        building_color,
        window_color,
    )

    if key not in BUILDING_SURF_MAP:

        width = (
            (window_size * no_of_windows_on_same_floor)
            + (padding_around_windows * (no_of_windows_on_same_floor + 1))
        )

        height = (
            (window_size * no_of_stories)
            + (padding_around_windows * (no_of_stories + 1))
        )

        building_surf = Surface((width, height)).convert()
        building_surf.fill(building_color)

        window_rect.size = (window_size,) * 2

        start = padding_around_windows
        step = padding_around_windows + window_size

        for x_index, y_index in product(
            range(no_of_windows_on_same_floor),
            range(no_of_stories),
        ):
            x = start + (x_index * step)
            y = start + (y_index * step)

            window_rect.topleft = (x, y)

            draw_rect(building_surf, window_color, window_rect)

        BUILDING_SURF_MAP[key] = building_surf

    return BUILDING_SURF_MAP[key]
