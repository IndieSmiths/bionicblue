
### local imports

from ....config import SURF_MAP

from ....pygamesetup.constants import blit_on_screen

from ....surfsman import get_larger_surf_by_repeating



class Crate:

    surf_map32 = {}
    surf_map16 = {}

    def __init__(self, name, size=(0, 0), pos=(0, 0)):

        self.name = name

        image_name = 'crate32.png' if '32' in name else 'crate16.png'

        if size != (0, 0):

            surf_map = self.surf_map32 if '32' in name else self.surf_map16

            if size in surf_map:
                self.image = surf_map[size]

            else:
                self.image = surf_map[size] = (
                    get_larger_surf_by_repeating(SURF_MAP[image_name], size)
                )

        else:
            self.image = SURF_MAP[image_name]

        pos_name = 'bottomleft' if 'bottomleft' in name else 'midtop'

        self.rect = self.image.get_rect()
        setattr(self.rect, pos_name, pos)
        self.colliderect = self.rect.colliderect

    def update(self): pass

    def draw(self):
        blit_on_screen(self.image, self.rect)
