
### third-party import

from pygame.draw import (
    rect as draw_rect,
    polygon as draw_polygon,
)

### local import

from ....ani2d.player import AnimationPlayer2D

from ....pygamesetup.constants import SCREEN



class LargeDish:

    def __init__(self, animation_name, center):

        self.name = 'large_dish'
        self.layer_name = 'middleprops'

        self.aniplayer = AnimationPlayer2D(self, animation_name, 'idle')

        self.inflated_rect = self.rect.inflate(16, 16)

        setattr(self.rect, 'center', center)

    def update(self): pass

    def draw(self):

        ### TODO refactor and also add outlines

        inflated_rect = self.inflated_rect
        inflated_rect.center = self.rect.center

        draw_rect(SCREEN, 'blue', inflated_rect, border_radius=12)

        a = inflated_rect.move(-8, 0).midbottom
        b = inflated_rect.move(8, 0).midbottom
        c = inflated_rect.move(0, 8).midbottom

        draw_polygon(SCREEN, 'blue', (a, b, c))

        self.aniplayer.draw()
