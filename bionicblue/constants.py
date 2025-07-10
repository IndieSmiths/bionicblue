
### local import
from .pygamesetup.constants import FPS, msecs_to_frames


### acceleration (pixels per frame squared)
GRAVITY_ACCEL = 2

### speed (pixels/frame)

MAX_Y_SPEED = 10
MAX_X_SPEED = 4

CHARGED_SHOT_SPEED = 10


### time-based constants

_MSECS_TO_DAMAGE_WHITENING = 70
DAMAGE_WHITENING_FRAMES = msecs_to_frames(_MSECS_TO_DAMAGE_WHITENING)

_SHOOTING_STANCE_MSECS = 300
SHOOTING_STANCE_FRAMES = msecs_to_frames(_SHOOTING_STANCE_MSECS)

_DAMAGE_STANCE_MSECS = 400
DAMAGE_STANCE_FRAMES = msecs_to_frames(_DAMAGE_STANCE_MSECS)

_DAMAGE_REBOUND_MSECS = 800
DAMAGE_REBOUND_FRAMES = msecs_to_frames(_DAMAGE_REBOUND_MSECS)

_MIDDLE_CHARGE_MSECS = 710
MIDDLE_CHARGE_FRAMES = msecs_to_frames(_MIDDLE_CHARGE_MSECS)

_FULL_CHARGE_MSECS = 2700
FULL_CHARGE_FRAMES = msecs_to_frames(_FULL_CHARGE_MSECS)
