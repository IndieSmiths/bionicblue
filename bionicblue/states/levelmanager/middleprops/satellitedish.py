"""Facility for satellite dish checkpoint."""

### standard library import
from itertools import chain, cycle, repeat


### third-party import
from pygame.draw import circle as draw_circle


### local imports

from ....config import REFS, SOUND_MAP

from ....pygamesetup.constants import SCREEN, msecs_to_frames

from ....ani2d.player import AnimationPlayer2D

from ....ourstdlibs.behaviour import do_nothing

from ..common import VFX_ELEMENTS

from ..otherprops.hoveringtext import HoveringText



_SIGNAL_DURATION_MSECS = 5000
SIGNAL_DURATION_FRAMES = msecs_to_frames(_SIGNAL_DURATION_MSECS)


class SatelliteDish:
    """A satellite dish representing a level checkpoint."""

    def __init__(self, checkpoint_name, midbottom, animation_name):

        self.layer_name = 'middleprops'

        self.checkpoint_name = checkpoint_name

        self.aniplayer = (

            AnimationPlayer2D(
                self,
                'satellite_dish',
                animation_name,
                'midbottom',
                midbottom,
            )

        )

        self.update = do_nothing
        self.draw = self.normal_draw

        self.next_radius = chain(

            range(4, 28, 2),
            repeat(0, 8),
            range(4, 28, 2),
            repeat(0, 8),
            range(4, 28, 2),
            repeat(0),

        ).__next__

    def trigger_activation(self):

        self.aniplayer.switch_animation('activating')

        SOUND_MAP['satellite_dish_moving.wav'].play()

        self.update = self.check_activation

        VFX_ELEMENTS.add(

            HoveringText(
                'Checkpoint!',
                pos_name='midbottom',
                pos_value=self.rect.midtop,
            )

        )

        REFS.last_checkpoint_name = self.checkpoint_name

        return True

    def check_activation(self):

        if self.aniplayer.main_timing.peek_loops_no(1) == 1:

            self.aniplayer.switch_animation('activated')

            self.signal_countdown = SIGNAL_DURATION_FRAMES
            self.update = self.check_signal
            self.draw = self.draw_with_signal

    def check_signal(self):

        self.signal_countdown -= 1

        if self.signal_countdown <= 0:

            self.update = do_nothing
            self.draw = self.normal_draw

    def normal_draw(self):
        self.aniplayer.draw()

    def draw_with_signal(self):

        self.aniplayer.draw()

        # pulse effect with expanding circle

        radius = self.next_radius()

        if radius:

            center = self.rect.move(-6, 13).midtop,

            draw_circle(
                SCREEN,
                'yellow',
                center,
                radius,
                1,
            )
