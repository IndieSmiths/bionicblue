"""Facility for satellite dish checkpoint."""

### third-party import
from pygame.draw import circle as draw_circle


### local imports

from ....config import REFS, SCREEN, SOUND_MAP

from ....ani2d.player import AnimationPlayer2D

from ....ourstdlibs.behaviour import do_nothing

from ..common import VFX_ELEMENTS

from ..otherprops.hoveringtext import HoveringText



class SatelliteDish:
    """A satellite dish representing a level checkpoint."""

    def __init__(self, checkpoint_name, midbottom, animation_name):

        self.layer_name = 'middleprops'

        self.checkpoint_name = checkpoint_name

        self.aniplayer = (
            AnimationPlayer2D(
                self, 'satellite_dish', animation_name, 'midbottom', pos
            )
        )

        self.rect.midbottom = midbottom

        self.update = do_nothing
        self.draw = self.normal_draw

    def trigger_activation(self):

        self.aniplayer.switch_animation('activating')
        SOUND_MAP['satellite_dish_moving'].play()

        self.update = self.check_activation

        return True

    def check_activation(self):

        if self.aniplayer.main_timing.peek_loops_no(1) == 1:

            self.aniplayer.switch_animation('activated')

            VFX_ELEMENTS.add(

                HoveringText(
                    'Checkpoint!',
                    pos_name = 'midbottom'
                    pos_value = self.rect.midtop
                )

            )

            REFS.last_checkpoint_name = self.checkpoint_name

            self.signal_countdown = 200
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

        # TODO make pulse effect with circles

        draw_circle(
            SCREEN,
            'yellow',
            self.rect.move(0, 10).midtop,
            8,
            1,
        )
