
### third-party imports
from pygame import Rect, Surface


### local imports

from .config import COLORKEY

from .rectsman.main import RectsManager



EMPTY_SURF = Surface((0, 0)).convert()


def get_larger_surf_by_repeating(surf, size):
    """Create larger surf by repeating given one."""

    rect = surf.get_rect()
    area = Rect(0, 0, *size)

    area_surf = Surface(size).convert()

    if surf.get_colorkey():

        area_surf.fill(COLORKEY)
        area_surf.set_colorkey(COLORKEY)

    blit_on_area = area_surf.blit

    while rect.top < area.bottom:

        blit_on_area(surf, rect)

        rect.left = rect.right

        if rect.left > area.right:

            rect.top = rect.bottom
            rect.left = 0

    return area_surf


def combine_surfaces(
    surfaces,
    retrieve_pos_from="midright",
    assign_pos_to="midleft",
    offset_pos_by=(0, 0),
    padding=0,
    background_color='black',
):
    """Return new surf from given ones."""
    ### obtain rects from given surfaces
    rects = [surf.get_rect() for surf in surfaces]

    ### define rects manager
    rectsman = RectsManager(rects.__iter__)

    ### position rects

    rectsman.snap_rects_ip(
        retrieve_pos_from=retrieve_pos_from,
        assign_pos_to=assign_pos_to,
        offset_pos_by=offset_pos_by,
    )

    ### get an inflated copy of the rectsman

    inflation_amount = padding * 2

    inflated_rect = rectsman.inflate(inflation_amount, inflation_amount)

    ### position inflated copy in origin and center
    ### the rectsman on it

    inflated_rect.topleft = (0, 0)
    rectsman.center = inflated_rect.center

    ### create new surface and blit surfaces on it

    new_surf = Surface(inflated_rect.size).convert()
    new_surf.fill(background_color)

    for surf, rect in zip(surfaces, rects):
        new_surf.blit(surf, rect)

    ### finally return the surf
    return new_surf


def unite_surfaces(
    surface_rect_pairs,
    padding=0,
    background_color='black',
):
    """Return a surface from surfaces' union."""
    ### separate surfaces and rects into different lists

    surfaces = []
    rects = []

    for surf, rect in surface_rect_pairs:

        surfaces.append(surf)
        rects.append(rect)

    ### obtain a rectsman for the rects
    rectsman = RectsManager(rects.__iter__)

    ### get an inflated copy of the rectsman

    inflation_amount = padding * 2

    inflated_rect = rectsman.inflate(inflation_amount, inflation_amount)

    ### obtain an offset from the inverted topleft of the
    ### inflated rect; we'll use this to obtain offset
    ### copies of each rect in order to blit the surfaces
    ### relative to the union surface
    offset = tuple(-value for value in inflated_rect.topleft)

    ### create new surface and blit surfaces on it

    new_surf = Surface(inflated_rect.size).convert()
    new_surf.fill(background_color)

    for surf, rect in zip(surfaces, rects):

        new_surf.blit(
            surf,
            rect.move(offset),
        )

    ### finally return the surf
    return new_surf
