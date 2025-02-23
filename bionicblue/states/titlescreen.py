
### standard library import
from itertools import cycle


### third-party imports

from pygame.locals import QUIT

from pygame.display import update

from pygame.mixer import music


### local imports

from ..config import REFS, MUSIC_DIR, quit_game

from ..pygamesetup import SERVICES_NS

from ..pygamesetup.constants import (
    SCREEN_RECT,
    BLACK_BG,
    FPS,
    GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS,
    KEYBOARD_OR_GAMEPAD_PRESSED_EVENTS,
    blit_on_screen,
)

from ..pygamesetup.gamepaddirect import setup_gamepad_if_existent

from ..exceptions import SwitchStateException

from ..textman import render_text

from ..surfsman import unite_surfaces

from ..classes2d.single import UIObject2D
from ..classes2d.collections import UIList2D

from ..userprefsman.main import USER_PREFS



class TitleScreen:

    def prepare(self):

        ###

        title_rect = self.title_rect = REFS.bb_title.rect

        # get copy of screen representing its first half
        # when split from midtop to midbottom
        _scopy = SCREEN_RECT.copy()
        _scopy.width /= 2

        ###
        title_rect.centerx = _scopy.move(5, 0).centerx
        title_rect.bottom = _scopy.top

        self.start_top = title_rect.top
        self.end_top = _scopy.move(0, 45).top

        _movement_duration_msecs = 2400 # milliseconds
        self.movement_duration_frames = round(_movement_duration_msecs / 1000 * FPS)

        self.current_movement_frame = 0
        self.last_movement_frame = self.movement_duration_frames - 1

        ###

        self.update = self.update_title_position

        ###

        any_button_words = 'Press any button'.split()

        uilist = UIList2D(

            UIObject2D.from_surface(render_text(word, 'regular', 16))
            for word in any_button_words

        )

        max_width = SCREEN_RECT.w * .5 * .5 # 50% of half the screen

        uilist.rect.snap_rects_intermittently_ip(

            dimension_name = 'width',
            dimension_unit = 'pixels',
            max_dimension_value = max_width,

            retrieve_pos_from='topright',
            assign_pos_to='topleft',
            offset_pos_by = (5, 0),

            intermittent_pos_from='bottomleft',
            intermittent_pos_to='topleft',
            intermittent_offset_by = (0, 0),

        )

        self.press_any_button = (

            UIObject2D.from_surface(

                unite_surfaces(
                    [(obj.image, obj.rect) for obj in uilist],
                    background_color='black',
                )

            )

        )

        _scopy.midleft = _scopy.midright

        self.press_any_button.rect.center = _scopy.center

        _show_duration_msecs = 1000
        _hide_duration_msecs = 500

        show_duration_frames = round(_show_duration_msecs / 1000 * FPS)
        hide_duration_frames = round(_hide_duration_msecs / 1000 * FPS)

        self.must_draw_label = cycle(
            ((True,) * show_duration_frames)
            + ((False,) * hide_duration_frames)
        ).__next__

        self.draw_label_flag = False

        ###

        music_volume = (
            (USER_PREFS['MASTER_VOLUME']/100)
            * (USER_PREFS['MUSIC_VOLUME']/100)
        )

        music.set_volume(music_volume)
        music.load(str(MUSIC_DIR / 'title_screen_by_juhani_junkala.ogg'))
        music.play(-1)

    def control(self):

        for event in SERVICES_NS.get_events():

            if event.type in KEYBOARD_OR_GAMEPAD_PRESSED_EVENTS:

                if self.update == self.update_draw_label_flag:

                    main_menu = REFS.states.main_menu
                    main_menu.prepare()

                    raise SwitchStateException(main_menu)

            elif event.type in GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS:
                setup_gamepad_if_existent()

            elif event.type == QUIT:
                quit_game()

    def update_title_position(self):

        if self.current_movement_frame <= self.last_movement_frame:

            progress = self.current_movement_frame / self.movement_duration_frames
            top_increment = ((self.end_top - self.start_top) * progress)
            self.title_rect.top = self.start_top +  top_increment

            REFS.blue_boy.rect.bottomleft = self.title_rect.move(12, -11).bottomleft

            self.current_movement_frame += 1

        else:
            self.update = self.update_draw_label_flag

    def update_draw_label_flag(self):
        self.draw_label_flag = self.must_draw_label()

    def draw(self):

        blit_on_screen(BLACK_BG, (0, 0))

        REFS.bb_title.draw()

        REFS.blue_boy.ap.draw()

        if self.draw_label_flag:
            self.press_any_button.draw()

        update()
