"""Facility for providing custom command line argument parsing and entry.

By entry, we mean launching the game.
"""

### standard library utility to grab command line arguments
from argparse import ArgumentParser


### setup argument parser

parser = ArgumentParser(
    description="Bionic Blue game launcher.",
    epilog="Play to your heart's content!",
)

parser.add_argument(
    '-d', '--dev-directive',
    default='',
    help="directive to enable development utilities/measures.",
)

parser.add_argument(
    '-r', '--replay-directive',
    default='',
    help=(
        "instruction to reproduce existing play session;"
        " can be path to play log file or a known command"
        " (used for debugging/playtest analysis)."
    ),
)

parser.add_argument(
    '-f', '--replay-fps',
    default='',
    help=(
        "speed of replay in frames per second;"
        " only used when replay directive is given"
    ),
)


def run_game_with_args():

    ### parse arguments
    parsed_args = parser.parse_args()


    ### import local function to run game loop and run it with the parsed
    ### arguments

    from .gameloop import run_game

    run_game(
        dev_directive=parsed_args.dev_directive,
        replay_directive=parsed_args.replay_directive,
        replay_fps=parsed_args.replay_fps,
    )
