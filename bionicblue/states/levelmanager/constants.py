"""Facility for constant values."""

### third-party import
from pygame.math import Vector2


### local import
from ...pygamesetup.constants import msecs_to_frames



FLOOR_LEVEL = 128

_MOVE_CLOUDS_MSECS = 12000
MOVE_CLOUDS_FRAMES = msecs_to_frames(_MOVE_CLOUDS_MSECS)

clouds_movement_delta = Vector2()
