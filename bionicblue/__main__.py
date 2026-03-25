"""Facility with function to run the Bionic Blue game.

Bionic Blue (by Kennedy Guerra): to know more about this game,
visit its website: https://bionicblue.indiesmiths.com
"""

### standard library import
from argparse import ArgumentParser


### local imports

## first ensure pygame used is the community edition fork (pygame-ce);
##
## this is important because the app uses services that are not available
## in the regular pygame instance
from .ensurepygamece import ensure_pygame_ce
ensure_pygame_ce()

## remaining local imports

from .config import REFS, MUST_LOCK_PLAY, LoopException

from .pygamesetup import SERVICES_NS, switch_mode

from .pygamesetup.gamepaddirect import setup_gamepad_if_existent

from .promptscreen import prompt_to_dismiss_with_any_button

from .resourceloader import ResourceLoader

from .states import setup_states

from .translatedtext import TRANSLATIONS



def run_game(debug_directive=False):
    """Run the game loop."""

    setup_gamepad_if_existent()

    if MUST_LOCK_PLAY:

        prompt_to_dismiss_with_any_button(
            TRANSLATIONS.soft_lock_prompt.caption,
            TRANSLATIONS.soft_lock_prompt.message,
        )

        return

    else:

        ### load resources and setup states

        ResourceLoader().load_resources()
        setup_states()

        ### pick next state according to debug directive
        ### or lack thereof

        REFS.debug_directive = debug_directive

        if debug_directive == 'level_manager':

            state = REFS.states.level_manager
            REFS.level_to_load = 'intro.lvl'

        elif debug_directive == 'title_screen':
            state = REFS.states.title_screen

        else:
            state = REFS.states.logos_screen

        ### prepare state
        state.prepare()

    while True:

        try:

            ### game loop

            while True:

                SERVICES_NS.frame_checkups()

                state.control()
                state.update()
                state.draw()

        except LoopException as exc:

            ### switch state if one is given

            if exc.state is not None:
                state = exc.state

            if exc.clear_tasks:
                REFS.clear_tasks()

            if exc.prepare:
                state.prepare()

            ### set input mode if one is named

            if exc.input_mode_name:

                switch_mode(
                    exc.input_mode_name,
                    exc.input_data,
                )


if __name__ == '__main__':

    ap = ArgumentParser(
        description="Bionic Blue game launcher.",
        epilog="Play to your heart's content!",
    )

    ap.add_argument(
        '-b', '--debug-directive',
        default='',
        help=(
            "Grabs debug directive if specified, used to facilitate debugging"
            " and other similar measures."
        ),
    )

    parsed_args = ap.parse_args()

    run_game(parsed_args.debug_directive)
