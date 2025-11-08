"""Facility to instantiate and store state managers."""

### local imports

from ..config import REFS

from .logoscreen import LogoScreen

from .titlescreen import TitleScreen

from .levelmanager import LevelManager

from .hqmanager import HeadQuartersManager

from .mainmenu import MainMenu

from .controlsscreen import ControlsScreen

from .optionsscreen import OptionsScreen

from .playtestersscreen import PlaytestersScreen

from .pausemenu import PauseMenu, pause

from .creditsscreen import CreditsScreen

from .slotcreationscreen import SlotCreationScreen

from .loadgamescreen import LoadGameScreen

from .transitionscreen import TransitionScreen

from .mediapresenter import MediaPresenter



def setup_states():
    """Instantiate and store states."""

    states = REFS.states

    states.logo_screen = LogoScreen()
    states.level_manager = LevelManager()
    states.hq_manager = HeadQuartersManager()

    states.title_screen = TitleScreen()
    states.main_menu = MainMenu()
    states.controls_screen = ControlsScreen()
    states.options_screen = OptionsScreen()
    states.playtesters_screen = PlaytestersScreen()

    states.pause_menu = PauseMenu()
    REFS.pause = pause

    states.credits_screen = CreditsScreen()

    states.slot_creation_screen = SlotCreationScreen()
    states.load_game_screen = LoadGameScreen()
    states.transition_screen = TransitionScreen()
    states.media_presenter = MediaPresenter()
