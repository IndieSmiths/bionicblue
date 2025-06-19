
### local imports

from ....config import SURF_MAP

from ....pygamesetup.constants import blit_on_screen

from ....surfsman import get_larger_surf_by_repeating



class Ladder:

    surf_map = {}
    climbable = True

    def __init__(self, name, size, pos):

        self.name = name

        surf_map = self.surf_map

        if size in surf_map:

            self.image = surf_map[size]
            rect = self.rect = self.image.get_rect()

        else:

            _surf = get_larger_surf_by_repeating(SURF_MAP['ladder.png'], size)
            rect = self.rect = _surf.get_rect()
            rect.inflate_ip(-2, 0)
            surf = _surf.subsurface(rect)
            self.image = surf_map[size] = surf

        self.rect = self.image.get_rect()
        setattr(self.rect, 'midbottom', pos)
        self.colliderect = self.rect.colliderect

    def update(self): pass

    def draw(self):
        blit_on_screen(self.image, self.rect)
