
### third-party import
from pygame import Rect


### local imports
from ....pygamesetup.constants import SCREEN_RECT




_PADDING = 5

BOTTOMLEFT_ANCHOR = SCREEN_RECT.move(_PADDING, -_PADDING).bottomleft
BOTTOMRIGHT_ANCHOR = SCREEN_RECT.move(-_PADDING, -_PADDING).bottomright

PORTRAIT_BOX = Rect(0, 0, 32, 48)


TEXT_BOX = SCREEN_RECT.copy()

TEXT_BOX.height = PORTRAIT_BOX.height
TEXT_BOX.width -= (PORTRAIT_BOX.width + (3 * _PADDING)) 
text_box_colliderect = TEXT_BOX.colliderect


DIALOGUE_BOX = (
    Rect(
        0,
        0,
        SCREEN_RECT.width,
        PORTRAIT_BOX.height + (_PADDING*2),
    )
)

DIALOGUE_BOX.bottom = SCREEN_RECT.bottom
