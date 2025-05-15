
### standard library import
from functools import partial


### local imports

from ....config import SOUND_MAP

from ....ani2d.player import AnimationPlayer2D

from ..common import append_task, FRONT_PROPS



class DefaultExplosion:

    def __init__(self, pos_name, pos_value):

        self.name = 'explosion'

        self.aniplayer = (

            AnimationPlayer2D(
                self,
                self.name,
                'default_explosion',
                pos_name,
                pos_value,
            )

        )

        SOUND_MAP['default_explosion.wav'].play()

    def update(self):

        if self.aniplayer.main_timing.peek_loops_no(1) == 1:
            append_task(partial(FRONT_PROPS.remove, self))

    def draw(self):
        self.aniplayer.draw()
