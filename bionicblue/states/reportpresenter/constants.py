"""Facility for constants and common objects/values."""

### standard library import
from collections import defaultdict


### third-party import
from pygame import Surface


### local imports

from ...pygamesetup.constants import SCREEN_RECT

from ...classes2d.single import UIObject2D



REPORT_TEXT_SETTINGS = {
    'style': 'regular',
    'size': 12,
    'padding': 0,
    'foreground_color': 'white',
    'background_color': 'black',
}

UPPER_LIMIT = SCREEN_RECT.top + 20
LOWER_LIMIT = SCREEN_RECT.bottom - 20


PANEL_SIZE = (
    SCREEN_RECT.width - 10,
    SCREEN_RECT.height // 3,
)

def _get_panel():

    surf = Surface(PANEL_SIZE).convert()
    surf.fill('black')

    return UIObject2D.from_surface(surf)

PANEL_CACHE = defaultdict(_get_panel)
