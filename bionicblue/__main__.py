"""Facility with function to run the Bionic Blue game.

Bionic Blue (by Kennedy Guerra): to know more about this game,
visit its website: https://bionicblue.indiesmiths.com
"""

### standard library import
from argparse import ArgumentParser


### preliminary local import (needs to be executed before
### third-party library pygame-ce)

## ensure pygame used is the community edition fork (pygame-ce);
##
## this is important because the app uses services that are not available
## in the regular pygame instance
from .ensurepygamece import ensure_pygame_ce
ensure_pygame_ce()


### third-party import
from pygame import quit as quit_pygame


### local imports

from .config import (
    REFS,
    LoopException,
    save_recorded_data_if_any,
    did_player_ever,
    get_play_data,
)

from .pygamesetup import SERVICES_NS, switch_mode

from .localeprompt import LocalePrompt

from .resourceloader import ResourceLoader

from .states import setup_states



def run_game(dev_directive='', replay_directive='', replay_fps=''):
    """Run the game loop."""

    if not did_player_ever(event_name='chose_a_locale'):
        LocalePrompt().prompt_for_locale()

    ### load resources and setup states

    ResourceLoader().load_resources()
    setup_states()


    ### act according to directives

    ### if replay directive is given, try setting state and play mode
    ### according to it

    if replay_directive:

        try:
            play_data = get_play_data(replay_directive, replay_fps)

        except Exception as err:

            print("Couldn't load play data.")
            print()
            print("Error described below:")
            print(err)
            print()
            print("Starting game in normal mode instead.")

            ### XXX show prompt here telling user what went wrong

            ### pick state according to dev directive

            if dev_directive == 'title_screen':
                state = REFS.states.title_screen

            else:
                state = REFS.states.logos_screen

        else:

            switch_mode('replay', play_data)
            state = REFS.states.level_manager

    ### pick state according to dev directive

    else:

        if dev_directive == 'title_screen':
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

            ### set play mode if one is named

            if exc.play_mode_name:
                switch_mode(exc.play_mode_name)

            ###

            if exc.clear_tasks:
                REFS.clear_tasks()

            if exc.prepare:
                state.prepare()

        ## unexpected error

        except Exception:

            save_recorded_data_if_any('unexpected_error')
            quit_pygame()

            raise




if __name__ == '__main__':

    ap = ArgumentParser(
        description="Bionic Blue game launcher.",
        epilog="Play to your heart's content!",
    )

    ap.add_argument(
        '-d', '--dev-directive',
        default='',
        help="directive to enable development utilities/measures.",
    )

    ap.add_argument(
        '-r', '--replay-directive',
        default='',
        help=(
            "instruction to reproduce existing play session;"
            " can be path to play log file or a known command"
            " (used for debugging/playtest analysis)."
        ),
    )

    ap.add_argument(
        '-f', '--replay-fps',
        default='',
        help=(
            "speed of replay in frames per second;"
            " only used when replay directive is given"
        ),
    )

    parsed_args = ap.parse_args()

    run_game(
        dev_directive=parsed_args.dev_directive,
        replay_directive=parsed_args.replay_directive,
        replay_fps=parsed_args.replay_fps,
    )
