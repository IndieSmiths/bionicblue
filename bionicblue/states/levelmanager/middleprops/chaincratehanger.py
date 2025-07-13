"""Facility for chain-box hanger prop."""

### local imports

from ....config import SURF_MAP

from ....pygamesetup.constants import blit_on_screen



class ChainCrateHanger:

    def __init__(self, name, pos, facing_right=False):

        self.name = name

        image = self.image = SURF_MAP['chain_crate_hanger.png']
        rect = self.rect = image.get_rect()
        setattr(rect, 'midtop', pos)

    def update(self): pass

    def draw(self):
        blit_on_screen(self.image, self.rect)
