
### third-party imports

from pygame.math import Vector2

from pygame.draw import (
    rect as draw_rect,
    polygon as draw_polygon,
    lines as draw_lines,
)


### local imports

from ....ani2d.player import AnimationPlayer2D

from ....pygamesetup.constants import SCREEN



FILL_COLOR = 'royalblue'
OUTLINE_COLOR = 'yellow'

class Smartphone:
    
    def __init__(self):
        
        self.name = 'smartphone'
        self.layer_name = 'middleprops'
        self.aniplayer = AnimationPlayer2D(self, 'smartphone', 'ringing')

        self.inflated_rect = self.rect.inflate(10, 10)
        self.inflated_rect_pos_name = 'bottomleft'
        self.tail_points_offsets = (
            (0, 0),
            (0, 0),
            (0, 0),
        )

    def position_relative_to_player(self, player_pos_name, pos_value):
        
        x_offset = 8
        
        (

            inflated_rect_pos_name,
            chosen_x_offset,

        ) = (

            (
                'bottomleft',
                x_offset,
            )

            if player_pos_name == 'topright'

            else (
                'bottomright',
                -x_offset,
            )
        )

        self.inflated_rect_pos_name = inflated_rect_pos_name

        inflated_rect = self.inflated_rect

        y_offset = -x_offset
        bubble_offset = Vector2(chosen_x_offset, y_offset)

        setattr(
            inflated_rect,
            inflated_rect_pos_name,
            pos_value + bubble_offset,
        ),

        self.rect.center = inflated_rect.center

        self.tail_points_offsets = (

            Vector2(0, -6),

            Vector2(

                (
                    (-4 if player_pos_name == 'topright' else 4),
                    4
                )

            ),

            Vector2(

                (
                    (6 if player_pos_name == 'topright' else -6),
                    0
                )

            ),

        )


    def update(self): pass

    def draw(self):
        
        inflated_rect = self.inflated_rect
        inflated_rect.center = self.rect.center

        draw_rect(SCREEN, FILL_COLOR, inflated_rect, border_radius=6)
        draw_rect(SCREEN, OUTLINE_COLOR, inflated_rect, 1, border_radius=6)

        pos_name = self.inflated_rect_pos_name

        triangle_points = tuple(

            getattr(inflated_rect.move(offset), pos_name)
            for offset in self.tail_points_offsets

        )

        draw_polygon(SCREEN, FILL_COLOR, triangle_points)

        draw_lines(SCREEN, OUTLINE_COLOR, False, triangle_points, 1)

        self.aniplayer.draw()
