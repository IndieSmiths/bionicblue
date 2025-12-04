
### local imports

from ....config import SURF_MAP

from ....pygamesetup.constants import blit_on_screen


class LightPoleFront:

    def __init__(self, name, pos):

        self.name = name

        self.image = SURF_MAP['light_pole_front.png']

        self.rect = self.image.get_rect()

        setattr(self.rect, 'bottomleft', pos)

    def update(self): pass

    def draw(self):
        blit_on_screen(self.image, self.rect)
