"""Facility for Mark NPC."""

### standard library import
from functools import partial


### local imports

from ....config import REFS

from ....pygamesetup.constants import GENERAL_NS

from ....constants import DAMAGE_WHITENING_FRAMES

from ....ani2d.player import AnimationPlayer2D

from ....ourstdlibs.behaviour import do_nothing

from ..frontprops.defaultexplosion import DefaultExplosion

from ..common import (
    remove_obj,
    append_task,
)



WALK_SPEED = 1


class Mark:

    def __init__(self, pos):

        self.player = REFS.states.level_manager.player

        self.name = 'mark'

        self.x_speed = 0

        animation_name = 'idle_right'

        self.aniplayer = (
            AnimationPlayer2D(
                self, 'mark_npc', animation_name, 'midbottom', pos
            )
        )

        self.update = self.idle_update

    def idle_update(self):
        """Do nothing."""

    def leaving_update(self):

        rect = self.rect
        center = rect.center

        x_speed = self.x_speed
        colliderect = rect.colliderect

        rect.move_ip(x_speed, 0)

        ###

        if rect.center != center:

            self.delta += tuple(
                a - b
                for a, b
                in zip(rect.center, center)
            )

    def draw(self):
        self.aniplayer.draw()
