
### third-party import
from pygame import Surface


### local imports

from ....config import SURF_MAP

from ....pygamesetup.constants import blit_on_screen

from ....surfsman import get_larger_surf_by_repeating


class CityWall:

    surf_map = {}

    def __init__(self, name, size, pos):

        self.name = name

        surf_map = self.surf_map

        if size in surf_map:
            self.image = surf_map[size]

        else:
            self.image = surf_map[size] = (
                get_larger_surf_by_repeating(SURF_MAP['city_wall.png'], size)
            )

        self.rect = self.image.get_rect()
        setattr(self.rect, 'bottomleft', pos)

    def update(self): pass

    def draw(self):
        blit_on_screen(self.image, self.rect)
