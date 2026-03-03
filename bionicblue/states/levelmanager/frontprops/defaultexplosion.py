
### standard library import
from functools import partial


### local imports

from ....config import SOUND_MAP

from ....ani2d.player import AnimationPlayer2D

from ..common import remove_obj

from ..taskmanager import append_ready_task, append_timed_task



class DefaultExplosion:

    def __init__(self, pos_name, pos_value, delta_t=0, unit='milliseconds'):

        self.name = 'explosion'

        self.layer_name = 'frontprops'

        self.aniplayer = (

            AnimationPlayer2D(
                self,
                self.name,
                'default_explosion',
                pos_name,
                pos_value,
            )

        )

        play_sound = SOUND_MAP['default_explosion.wav'].play

        if delta_t:

            append_timed_task(
                play_sound,
                delta_t=delta_t,
                unit=unit,
            )

        else:
            play_sound()

    def update(self):

        if self.aniplayer.main_timing.peek_loops_no(1) == 1:
            append_ready_task(partial(remove_obj, self))

    def draw(self):
        self.aniplayer.draw()
