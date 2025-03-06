
### standard library import

from pathlib import Path

## for temporary stdout suppression

from io import StringIO

from contextlib import redirect_stdout


### local imports
from .appinfo import TITLE, ABBREVIATED_TITLE



PYGAME_CE_REQUIRED_MESSAGE = """
Please, make sure regular pygame is uninstalled and pygame-ce (pygame community edition) is installed in the Python instance running the Bionic Blue game by executing the following commands:

pip uninstall pygame
pip install pygame-ce --upgrade

This is needed because the game uses services that are not available in the regular pygame instance.
""".strip()


def ensure_pygame_ce():
    """Ensure pygame is available and is the community edition fork.

    If pygame is available but not the community edition, a dialog window with
    instructions is displayed instead.
    """

    try:

        ## here we suppress the pygame-ce message that appears when it is
        ## imported the first time so it is easier to read other messages
        ## that may be printed when debugging;
        ##
        ## (but don't worry, we'll properly credit the library both in the
        ## game itself and its online content, like we already do in other
        ## apps of the Indie Smiths project)

        with StringIO() as temp_stream:

            with redirect_stdout(temp_stream):

                import pygame

    except ImportError:

        logger.exception(
            "pygame-ce doesn't seem to be available."
            " Reraising."
        )

        raise

    else:

        ## if pygame is not pygame-ce, display message saying the app cannot be
        ## used because pygame-ce is a requirement;
        ##
        ## the message is both printed and displayed in a dialog and the app is
        ## exited once user closes window or dismiss it by pressing the escape key

        if not getattr(pygame, 'IS_CE', False):
            display_dialog_and_quit(pygame)



def display_dialog_and_quit(pygame_module):

    pg = pygame_module

    pg.init()

    ###
    data_dir = Path(__file__).parent.parent / 'data'

    ### set icon and caption for window

    #pg.display.set_icon(pg.image.load(str(data_dir / "app_icon.png")))
    pg.display.set_caption(TITLE, ABBREVIATED_TITLE)

    ###

    screen = pg.display.set_mode((640, 220))

    screen.fill('grey10')
    screen_rect = screen.get_rect()
    blit_on_screen = screen.blit

#    bb_logo = (
#        pg.image.load(str(data_dir / 'images' / 'bb_logo.png'))
#    ).convert_alpha()
#
#    bb_logo_rect = bb_logo.get_rect().move(10, 30)
#    blit_on_screen(bb_logo, bb_logo_rect)

    top = 30
    left = 30
    #left = bb_logo_rect.move(10, 0).right

    width = screen_rect.width - left - 10

    blitting_area = pg.Rect(left, top, width, screen_rect.height-10)

    render_text = pg.font.Font(None, 24).render

    space_width, line_height = render_text(' ', True, 'black').get_size()

    topleft = blitting_area.topleft

    ###

    for line in PYGAME_CE_REQUIRED_MESSAGE.splitlines():

        for word in line.split():

            text_surf = render_text(word, True, 'white')
            text_rect = text_surf.get_rect().move(topleft)

            if not blitting_area.contains(text_rect):

                text_rect.left = blitting_area.left
                text_rect.top += line_height

            blit_on_screen(text_surf, text_rect)

            topleft = text_rect.move(space_width, 0).topright

        topleft = (
            blitting_area.left,
            topleft[1] + line_height
        )

    maintain_fps = pg.time.Clock().tick

    running = True

    while running:

        maintain_fps(24)

        for event in pg.event.get():

            if (
                event.type == pg.QUIT
                or (
                    event.type == pg.KEYDOWN
                    and event.key == pg.K_ESCAPE
                )
            ):

                running = False

        pg.display.update()

    pg.quit()
    quit()

