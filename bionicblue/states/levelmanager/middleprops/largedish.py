
### third-party import

from pygame.draw import (
    rect as draw_rect,
    polygon as draw_polygon,
    lines as draw_lines,
)

### local imports

from ....ani2d.player import AnimationPlayer2D

from ....pygamesetup.constants import SCREEN



FILL_COLOR = 'indianred'
OUTLINE_COLOR = 'yellow'

class LargeDish:

    def __init__(self, animation_name, center):

        self.name = 'large_dish'
        self.layer_name = 'middleprops'

        self.aniplayer = AnimationPlayer2D(self, animation_name, 'idle')

        self.inflated_rect = self.rect.inflate(16, 16)

        setattr(self.rect, 'center', center)

    def update(self): pass

    def draw(self):

        inflated_rect = self.inflated_rect
        inflated_rect.center = self.rect.center

        draw_rect(SCREEN, FILL_COLOR, inflated_rect, border_radius=16)
        draw_rect(SCREEN, OUTLINE_COLOR, inflated_rect, 2, border_radius=16)

        triangle_points = tuple(

            inflated_rect.move(offset).midbottom

            for offset in (
                (-8, -2),
                (0, 6),
                (8, -2),
            )

        )

        draw_polygon(SCREEN, FILL_COLOR, triangle_points)

        draw_lines(SCREEN, OUTLINE_COLOR, False, triangle_points, 2)

        self.aniplayer.draw()
