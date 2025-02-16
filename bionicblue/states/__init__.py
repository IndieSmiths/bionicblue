
### local imports

from ..config import REFS

from .resourceloader import ResourceLoader

from .logoscreen import LogoScreen

from .titlescreen import TitleScreen

from .levelmanager import LevelManager

from .hqmanager import HeadQuartersManager

from .mainmenu import MainMenu

from .controlsscreen import ControlsScreen

from .optionsscreen import OptionsScreen

from .playtestersscreen import PlaytestersScreen

#from .creditsroller import CreditsRoller



def setup_states():
    """Instantiate and store states."""

    states = REFS.states

    states.resource_loader = ResourceLoader()
    states.logo_screen = LogoScreen()
    states.level_manager = LevelManager()
    states.hq_manager = HeadQuartersManager()

    REFS.get_game_state = get_game_state

    states.title_screen = TitleScreen()
    states.main_menu = MainMenu()
    states.controls_screen = ControlsScreen()
    states.options_screen = OptionsScreen()
    states.playtesters_screen = PlaytestersScreen()
    #states.credits_roller = CreditsRoller()


def get_game_state():
    """Pick appropriate gameplay state, prepare and return it."""

    return (
        REFS.states.level_manager
        if REFS.data['level_name'] == 'intro.lvl'
        else None # REFS.hq_loader
    )
