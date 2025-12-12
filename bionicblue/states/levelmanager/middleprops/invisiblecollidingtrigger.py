"""Facility for object to trigger call on collision with player."""

### standard library import
from functools import partial


### third-party import
from pygame import Rect


### local imports

from ....config import REFS

from ....surfsman import EMPTY_SURF

from ..common import remove_obj, append_task



class InvisibleCollidingTrigger:
    """Invisible object that triggers call when collides with player.

    That is, under specific conditions.
    """

    def __init__(
        self,
        on_collision,
        width=64,
        height=64,
        coordinates_name='midbottom',
        coordinates_value=(0, 0),
    ):
        """Store references, create and position geometry."""

        self.layer_name = 'middleprops'

        ###

        self.on_collision = on_collision
        self.player = REFS.states.level_manager.player

        ### assign image
        self.image = EMPTY_SURF

        ### create and position rect

        self.rect = Rect(0, 0, width, height)

        setattr(
            self.rect,
            coordinates_name,
            coordinates_value,
        )

        self.colliderect = self.rect.colliderect

    def update(self):

        if self.colliderect(self.player.rect) and self.on_collision():
            append_task(partial(remove_obj, self))

    def draw(self):
        """Do nothing."""
