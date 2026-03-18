"""Facility for transitioning effects.

That is, for us to present another state to the player smoothly,
in some cases (this isn't supposed to be used all the time).
"""

### third-party imports

from pygame.locals import QUIT

from pygame.display import update


### local imports

from ..config import REFS, SOUND_MAP, LoopException, quit_game

from ..pygamesetup import SERVICES_NS

from ..pygamesetup.constants import (
    SCREEN,
    SCREEN_RECT,
    GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS,
    msecs_to_frames,
)

from ..pygamesetup.gamepaddirect import setup_gamepad_if_existent



_FILLING_SCREEN_MSECS = 1500
FILLING_SCREEN_FRAMES = msecs_to_frames(_FILLING_SCREEN_MSECS)

HEIGHT_STEP, _substeps = divmod(SCREEN_RECT.height, FILLING_SCREEN_FRAMES)

if _substeps:
    HEIGHT_STEP += 1


class TransitionScreen:
    """Brief state to show a screen transition.

    Used to switch between some specific states, just for the sake of
    showmanship/cinematography.
    """

    def prepare(self, to_call_on_exit):
        """Store given callable and make extra preparations."""

        SOUND_MAP['ui_success.wav'].play()

        self.to_call_on_exit = to_call_on_exit

        self.remaining_height = SCREEN_RECT.height
        self.screen_filling_countdown = FILLING_SCREEN_FRAMES

    def control(self):

        for event in SERVICES_NS.get_events():

            if event.type == QUIT:
                quit_game()

            elif event.type in GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS:
                setup_gamepad_if_existent()


    def update(self):

        self.screen_filling_countdown -= 1
        self.remaining_height -= HEIGHT_STEP

        if self.screen_filling_countdown == 0:
            self.to_call_on_exit()

    def draw(self):

        SCREEN.fill(
            'blue',
            SCREEN_RECT.move(0, self.remaining_height),
        )

        update()
