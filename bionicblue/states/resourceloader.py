
### standard library imports
from itertools import repeat, chain


### third-party imports

from pygame import Surface

from pygame.locals import QUIT

from pygame.time import get_ticks as get_msecs

from pygame.display import update

from pygame.image import load as load_image

from pygame.mixer import Sound


### local imports

from ..config import (
    REFS,
    COLORKEY,
    SURF_MAP,
    ANIM_DATA_MAP,
    SOUND_MAP,
    ALPHA_IMAGES_DIR,
    NO_ALPHA_IMAGES_DIR,
    ANIMATIONS_DIR,
    SOUNDS_DIR,
    quit_game,
)

from ..pygamesetup import SERVICES_NS

from ..pygamesetup.constants import FPS, WHITE_BG, SCREEN_RECT, blit_on_screen

from ..textman import render_text

from ..surfsman import combine_surfaces

from ..ani2d.player import AnimationPlayer2D
from ..ani2d.processing import process_animation_data

from ..classes2d.single import UIObject2D

from ..exceptions import SwitchStateException

from ..userprefsman.main import USER_PREFS



ALLOWED_SOUND_FILE_EXTENSIONS = frozenset(('.ogg', '.wav'))

MSECS_PER_FRAME = 1000 / FPS



### gather animation resources

class ResourceLoader:

    def __init__(self):

        self.loading_surf = (
            render_text('loading...', 'regular', 16, 0, 'black', 'white')
        )

        self.resources_to_process = chain(

            zip(
                repeat(SURF_MAP),
                ALPHA_IMAGES_DIR.iterdir(),
                repeat(load_alpha_image_from_filepath),
            ),

            zip(
                repeat(SURF_MAP),
                NO_ALPHA_IMAGES_DIR.iterdir(),
                repeat(load_image_from_filepath),
            ),

            zip(
                repeat(ANIM_DATA_MAP),
                (path for path in ANIMATIONS_DIR.iterdir() if path.is_dir()),
                repeat(load_anim_from_dir),
            ),

            zip(
                repeat(SOUND_MAP),
                (
                    path for path in SOUNDS_DIR.iterdir()
                    if path.is_file()
                    if path.suffix.lower() in ALLOWED_SOUND_FILE_EXTENSIONS
                ),
                repeat(load_sound_from_filepath),
            ),

        )


    def control(self):

        for event in SERVICES_NS.get_events():

            if event.type == QUIT:
                quit_game()

    def update(self):

        now = get_msecs()

        resources_to_process = self.resources_to_process

        try:

            while True:

                a_map, filepath, processing_op = next(resources_to_process)
                a_map[filepath.name] = processing_op(filepath)

                if (get_msecs() - now) >= MSECS_PER_FRAME:

                    blit_on_screen(WHITE_BG, (0, 0))
                    blit_on_screen(self.loading_surf, (10, 10))

                    break

        except StopIteration:

            ### store animated objects

            for attr_name, anim_data_name, anim_name in (
                ('blue_boy', 'blue_shooter_man', 'walk_right'),
                ('middle_shot', 'middle_charged_shot', 'idle_right'),
            ):

                obj = UIObject2D()
                setattr(REFS, attr_name, obj)
                obj.ap = AnimationPlayer2D(obj, anim_data_name, anim_name)

                obj.rect.right = SCREEN_RECT.left # place out of screen for now

            ### create title label

            text_settings = 'regular', 38, 0, 'dodgerblue'

            _bionic_text_surf = render_text('Bionic', *text_settings)
            _blue_text_surf = render_text('Blue', *text_settings)

            bionic_blue_text_surf = (
                combine_surfaces(
                    [_bionic_text_surf, _blue_text_surf],
                    retrieve_pos_from='bottomright',
                    assign_pos_to='topright',
                    offset_pos_by=(0, -7),
                )
            )

            author_name_surf = (
                render_text("Kennedy Guerra's", 'regular', 12, 0, 'white')
            )

            REFS.bb_title = (
                UIObject2D.from_surface(
                    combine_surfaces(
                        [bionic_blue_text_surf, author_name_surf],
                        retrieve_pos_from ='topleft',
                        assign_pos_to ='bottomleft',
                        offset_pos_by =(0, 5),
                    )
                )
            )

            ### make it so volume settings take effect on system

            sound_volume = (
                (USER_PREFS['MASTER_VOLUME'] / 100)
                * (USER_PREFS['SOUND_VOLUME'] / 100)
            )

            for sound in SOUND_MAP.values():
                sound.set_volume(sound_volume)

            ### if on debug mode, use title screen
            ### as next state

            if REFS.debug_mode:
                next_state = REFS.states.title_screen

            ### otherwise, use the logo screen

            else:
                next_state = REFS.states.logo_screen

            ### prepare state and switch to it

            next_state.prepare()
            raise SwitchStateException(next_state)


    def draw(self):
        update()


### utility functions

def load_alpha_image_from_filepath(filepath):
    image = load_image(str(filepath)).convert_alpha()
    surf = Surface(image.get_size()).convert()
    surf.set_colorkey(COLORKEY)
    surf.fill(COLORKEY)
    surf.blit(image, (0, 0))
    return surf

def load_image_from_filepath(filepath):
    return load_image(str(filepath)).convert()

def load_anim_from_dir(dirpath):
    return process_animation_data(dirpath)

def load_sound_from_filepath(filepath):
    sound = Sound(str(filepath))
    return sound
