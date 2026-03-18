
### standard library imports

from itertools import cycle

from functools import partial


### local imports

from ....pygamesetup.constants import msecs_to_frames, blit_on_screen

from ....ourstdlibs.behaviour import do_nothing

from ....textman import render_text_with_shadow

from ..common import VFX_ELEMENTS

from ..taskmanager import append_ready_task



_LIFE_DURATION_MSECS = 2300
LIFE_DURATION_FRAMES = msecs_to_frames(_LIFE_DURATION_MSECS)


class HoveringText:
    """Text that hovers then disappears"""

    def __init__(self, text, pos_name, pos_value):

        self.image = render_text_with_shadow(text, 'regular', 10)
        self.rect = self.image.get_rect()

        setattr(
            self.rect,
            pos_name,
            pos_value,
        )

        self.life_countdown = LIFE_DURATION_FRAMES
        self.update = self.advance_countdown

        self.next_delta_y = cycle(

            (-1,)
            + ((0,)* 10)

        ).__next__

    def advance_countdown(self):

        self.life_countdown -= 1

        self.rect.y += self.next_delta_y()

        if self.life_countdown <= 0:

            self.update = do_nothing

            append_ready_task(

                partial(
                    VFX_ELEMENTS.remove,
                    self,
                )

            )

    def draw(self):
        blit_on_screen(self.image, self.rect)
