"""Facility to present media to convey information.

Media is comprised of text, images and animated sprites.
"""

### standard library imports

from collections import defaultdict, deque

from itertools import chain, cycle, count, repeat


### third-party imports

from pygame.locals import (

    QUIT,

    KEYDOWN,
    K_ESCAPE,
    K_RETURN,
    K_DOWN,
    K_UP,
    K_LEFT,
    K_RIGHT,

    JOYBUTTONDOWN,

)

from pygame.math import Vector2

from pygame.display import update


### local imports

from ..config import (
    REFS,
    SURF_MAP,
    SOUND_MAP,
    PRESENTATIONS_DIR,
    LoopException,
    quit_game,
)

from ..pygamesetup import SERVICES_NS

from ..pygamesetup.constants import (
    SCREEN,
    SCREEN_RECT,
    GAMEPADDIRECTIONALPRESSED,
    GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS,
)

from ..pygamesetup.gamepaddirect import setup_gamepad_if_existent

from ..ourstdlibs.pyl import load_pyl

from ..textman import render_text

from ..classes2d.single import UIObject2D

from ..classes2d.collections import UIList2D

from ..ani2d.player import AnimationPlayer2D

from ..userprefsman.main import USER_PREFS, KEYBOARD_CONTROLS, GAMEPAD_CONTROLS

from ..translatedtext import TRANSLATIONS, on_language_change



### module level objects

SCREEN_TOP_HALF = SCREEN_RECT.copy()
SCREEN_TOP_HALF.height //= 2

SCREEN_BOTTOM_HALF = SCREEN_TOP_HALF.move(0, SCREEN_TOP_HALF.height)

PANEL_SIZE = SCREEN_TOP_HALF.inflate(-10, 0).size

def _get_panel():

    surf = Surface(PANEL_SIZE).convert()
    surf.fill('black')

    return UIObject2D.from_surface(surf)

PANEL_CACHE = defaultdict(_get_panel)

##

TEXT_SETTINGS = {
    'style': 'regular',
    'size': 12,
    'padding': 0,
    'foreground_color': 'white',
    'background_color': 'black',
}

##

_WORD_DEQUE = deque()

###
should_move = cycle(chain((True,), (False,)*5)).__next__


### class definition

class MediaPresenter:
    """Presents text, images and animated sprites.

    Ideally, user will be able to speed up or skip presentation altogether,
    just like usually in dialogue sections in games in general.
    """

    def __init__(self):

        dm = self.data_map = {}

        for path in PRESENTATIONS_DIR.iterdir():

            if path.suffix.lower() == '.pyl':

                try:
                    data = load_pyl(path)

                except Exception as err:

                    print("Error while trying to load presentation")
                    print()
                    raise

                else:
                    dm[path.stem] = data

        ### TODO
        ###
        ### load all visual, sound and music elements here, plus
        ### textual elements for current locale;
        ###
        ### then, create function to build textual elements (if not
        ### built already) for new locale/language selected by user

        ### map for all presentation elements
        self.presentation_map = defaultdict(dict)

        ### map for textual elements, since they are dependent on the
        ### locale/language
        self.textual_presentation_map = defaultdict(dict)

        ### grab current locale
        locale = USER_PREFS['LOCALE']

        ### create collections used to assist

        self.images = UIList2D()
        self.anisprites = UIList2D()
        self.sounds = []
        self.music = []

        self.all_visible_objs = UIList2D()

        ### create presentation elements for all presentations (using current
        ### locale/language, for textual elements)

        for presentation_key in dm:
            self.create_presentation(presentation_key, locale)

        ### store method to update text surfaces when language changes
        on_language_change.append(self.on_language_change)

    def on_language_change(self):
        """Rebuild textual elements (if needed) and set them up for usage."""

        ### grab current locale
        locale = USER_PREFS['LOCALE']

        ### if textual elements were not built for it, do so

        tpm = self.textual_presentation_map

        if any(
            locale not in submap
            for submap in tpm.values()
        ):

            for presentation_key in tpm:

                self.create_and_integrate_textual_elements(
                    presentation_key,
                    locale,
                )

        ### otherwise, just reference the existent textual elements

        else:

            pmap = self.presentation_map

            for presentation_key, submap in tpm.items():
                pmap[presentation_key]['paragraphs'] = submap[locale]

    def prepare(self, presentation_key):
        """Prepare objects for given presentation."""

        presentation = self.presentation_map[presentation_key]

        ### images

        append_image = self.images.append

        processed_images_data = presentation['images']

        for image_data in processed_images_data.values():

            obj = image_data['obj']

            obj.end_topleft = image_data['end_topleft']

            obj.next_step = (

                chain(
                    image_data['topleft_steps'],
                    repeat(obj.end_topleft),
                )

            ).__next__

            obj.rect.topleft = image_data['start_topleft']

            append_image(obj)

        ### animated sprites

        append_anisprite = self.anisprites.append

        processed_anisprites_data = presentation['animated_sprites']

        for anisprite_data in processed_anisprites_data.values():

            obj = anisprite_data['obj']

            obj.end_topleft = image_data['end_topleft']

            obj.next_step = (

                chain(
                    image_data['topleft_steps'],
                    repeat(obj.end_topleft),
                )

            ).__next__

            obj.rect.topleft = image_data['start_topleft']

            append_anisprite(obj)

        ### sound

        append_sound = self.sounds.append

        processed_sounds_data = presentation['sounds']

        for sound_data in processed_sounds_data.values():
            append_sound(sound_data['sound'])


        ### music

        append_music = self.music.append

        processed_music_data = presentation['music']

        for music_data in processed_music_data.values():
            append_music(music_data['name'])

        ### text

        ## retrieve paragraphs
        paragraphs = presentation['paragraphs']

        ## align lines one below each other

        for paragraph in paragraphs:

            paragraph.rect.snap_rects_ip(

                retrieve_pos_from='bottomleft',
                assign_pos_to='topleft',
                offset_pos_by=(0, 1),

            )

        ## align paragraphs one below each other, with
        ## the height of a panel between them (and some padding)

        paragraphs.rect.snap_rects_ip(

            retrieve_pos_from='bottomleft',
            assign_pos_to='topleft',
            offset_pos_by=(0, PANEL_SIZE[1] + 6),

        )

        paragraphs.rect.topleft = SCREEN_BOTTOM_HALF.move(5, -5).bottomleft

        vobjs = self.all_visible_objs

        for index, paragraph in enumerate(paragraphs):

            panel = PANEL_CACHE[index]
            panel.rect.topleft = paragraph.rect.move(0, 3).bottomleft

            vobjs.append(paragraph)
            vobjs.append(panel)

    def create_presentation(self, presentation_key, locale):
        """Create presentation elements, using given locale for text."""

        ### grab data
        data = self.data_map[presentation_key]

        ### create presentation
        presentation = {}

        ### populate it according to data

        ## images

        processed_images_data = presentation['images'] = {}

        for loaded_image_data in data.get('images', ()):

            ###
            image_name = loaded_image_data['name']

            ###
            image_data = processed_images_data[image_name] = {}

            ###

            image_obj = (

                UIObject2D.from_surface(
                    SURF_MAP[image_name]
                )

            )

            image_data['obj'] = image_obj

            ###
            process_position_data(image_obj, loaded_image_data, image_data)


        ## animated sprites

        processed_anisprites_data = presentation['animated_sprites'] = {}

        for loaded_anisprite_data in data.get('animated_sprites', ()):

            ###

            anisprite_name = loaded_anisprite_data['name']

            anisprite_id_str = (

                loaded_anisprite_data.get(
                    'id_str',
                    anisprite_name,
                )

            )

            ###
            anisprite_data = processed_anisprites_data[anisprite_id_str] = {}

            ###

            anim_data_name = loaded_anisprite_data['anim_data_name']
            anim_name = loaded_anisprite_data['anim_name']
            
            anisprite_obj = UIObject2D()
            anisprite_obj.aniplayer = (
                AnimationPlayer2D(anisprite_obj, anim_data_name, anim_name)
            )

            anisprite_data['obj'] = anisprite_obj

            ###

            process_position_data(
                anisprite_obj,
                loaded_anisprite_data,
                anisprite_data,
            )

        ## sound

        processed_sounds_data = presentation['sounds'] = {}

        for loaded_sound_data in data.get('sounds', ()):

            ###
            sound_name = loaded_sound_data['name']

            ###
            sound_data = processed_sounds_data[sound_name] = {}

            ###
            sound_obj = SOUND_MAP[sound_name]

            sound_data['sound'] = sound_obj

            ### TODO
            ### must think of ways to time triggering sound; possibilities:
            ###
            ### - at beginning of section
            ### - at end of section
            ### - on elapsed time starting from beginning of section
            ### - on animation pose
            ### - on image positioning step
            ### - on animation positioning step


        ## music

        processed_music_data = presentation['music'] = {}

        for loaded_music_data in data.get('music', ()):

            ###
            music_name = loaded_music_data['name']

            ###
            music_data = processed_music_data[music_name] = {}

            ###
            music_data['name'] = music_name

            ### TODO
            ###
            ### like sound, must think of ways to time triggering music


        ### store the presentation
        self.presentation_map[presentation_key] = presentation

        ### create textual elements
        self.create_and_integrate_textual_elements(presentation_key, locale)

    def create_and_integrate_textual_elements(self, presentation_key, locale):
        """Create textual elements and add to presentation."""

        paragraphs = UIList2D()

        self.presentation_map[presentation_key]['paragraphs'] = paragraphs 

        self.textual_presentation_map[presentation_key][locale] = paragraphs

        data = self.data_map[presentation_key]

        ###

        t = getattr(TRANSLATIONS, presentation_key)

        next_index = count().__next__

        while True:

            paragraph_attr_name = (
                'paragraph_'
                + str(next_index()).rjust(2, '0')
            )

            try:
                paragraph = getattr(t, paragraph_attr_name)

            except KeyError:
                break

            words = UIList2D(

                UIObject2D.from_surface(
                    render_text(word, **TEXT_SETTINGS)
                )

                for word in paragraph.split()

            )

            words.rect.snap_rects_intermittently_ip(

                ### interval limit

                dimension_name='width', # either 'width' or 'height'
                dimension_unit='pixels', # either 'rects' or 'pixels'
                max_dimension_value=SCREEN_RECT.width - 20, # posit. int.

                ### rect positioning

                retrieve_pos_from='topright',
                assign_pos_to='topleft',
                offset_pos_by=(5, 0),

                ### intermittent rect positioning

                intermittent_pos_from='bottomleft',
                intermittent_pos_to='topleft',
                intermittent_offset_by=(0, 2),

            )

            _WORD_DEQUE.extend(words)

            lines = UIList2D()

            while _WORD_DEQUE:
                
                line = UIList2D()

                top = _WORD_DEQUE[0].rect.top

                while _WORD_DEQUE and _WORD_DEQUE[0].rect.top == top:
                    line.append(_WORD_DEQUE.popleft())

                lines.append(line)

            ##
            paragraphs.append(lines)

    def control(self):
        """Let user speed up presentation or skip altogether."""

        for event in SERVICES_NS.get_events():

            if event.type == KEYDOWN:

                if event.key == K_ESCAPE:
                    quit_game()

                elif event.key == K_RETURN:
                    self.speed_up()

                elif event.key in (K_UP, K_DOWN, K_LEFT, K_RIGHT):
                    self.speed_up()

            elif event.type == JOYBUTTONDOWN:

                if event.button == GAMEPAD_CONTROLS['start_button']:
                    self.speed_up()

            elif event.type == GAMEPADDIRECTIONALPRESSED:
                self.speed_up()

            elif event.type in GAMEPAD_PLUGGING_OR_UNPLUGGING_EVENTS:
                setup_gamepad_if_existent()

            elif event.type == QUIT:
                quit_game()

        ###

        pressed_state = SERVICES_NS.get_pressed_keys()

        if (

            pressed_state[K_DOWN]
            or pressed_state[K_RIGHT]
            or pressed_state[KEYBOARD_CONTROLS['down']]
            or pressed_state[KEYBOARD_CONTROLS['right']]
            or GAMEPAD_NS.x_sum > 0
            or GAMEPAD_NS.y_sum > 0

        ):
            self.move_forward()

        elif (

            pressed_state[K_UP]
            or pressed_state[K_LEFT]
            or pressed_state[KEYBOARD_CONTROLS['up']]
            or pressed_state[KEYBOARD_CONTROLS['left']]
            or GAMEPAD_NS.x_sum < 0
            or GAMEPAD_NS.y_sum < 0

        ):
            self.move_backwards()

    def speed_up(self):
        ...

    def update(self):

        for obj in self.images:
            obj.rect.topleft = obj.next_step()

        for obj in self.anisprites:
            obj.rect.topleft = obj.next_step()

    def move_forward(self)

        vobjs = self.all_visible_objs
        vobjs_rect = vobjs.rect

        ## if last obj below bottom of screen bottom half...

        if vobjs_rect.bottom > SCREEN_BOTTOM_HALF.bottom - 5:
            vobjs.rect.move_ip(0, -2)

        ## if last obj above bottom of screen bottom half...

        elif vobjs_rect.bottom < SCREEN_BOTTOM_HALF.bottom - 5:
            vobjs.rect.bottom = SCREEN_BOTTOM_HALF.bottom - 5

        ### move words/lines;
        ###
        ### once paragraphs are finished, blink arrow to start next section
        ### on button press;
        ###
        ### if there's no next section, go to next state (start level)
        ...

    def move_backwards(self)

        vobjs = self.all_visible_objs
        vobjs_rect = vobjs.rect

        ## if first obj above top of screen top half...

        if vobjs_rect.top < SCREEN_TOP_HALF.top + 5:
            vobjs.rect.move_ip(0, 2)

        ## if first obj below top of screen top half...

        elif vobjs_rect.top > SCREEN_BOTTOM_HALF.top + 5:
            vobjs.rect.top = SCREEN_BOTTOM_HALF.top + 5


    def draw(self):

        SCREEN.fill('black')

        for obj in self.all_visible_objs:

            if isinstance(obj, UIList2D):
                for line in paragraph:
                    for word in line:
                        word.draw()

            else:
                obj.draw()

        self.images.draw()

        for obj in self.anisprites:
            obj.aniplayer.draw()

        update()


### utility functions

def process_position_data(obj, loaded_data, data):

    position_obj(obj, loaded_data['end_pos'])
    end_topleft = obj.rect.topleft

    position_obj(obj, loaded_data['start_pos'])
    start_topleft = obj.rect.topleft

    data['end_topleft'] = end_topleft
    data['start_topleft'] = start_topleft

    start_topleft_v = Vector2(start_topleft)

    steps = [

        tuple(

            start_topleft_v.lerp(
                end_topleft, # destination (end position)
                i/30,        # percentage to travel
            )

        )

        for i in range(30)

    ]

    steps.append(end_topleft)

    data['topleft_steps'] = steps


def position_obj(obj, pos_data):

    (
        rect_attr_name,
        screen_top_half_rect_attr_name,
        offset,
    ) = pos_data

    setattr(

        obj.rect,

        rect_attr_name,

        getattr(
            SCREEN_TOP_HALF,
            screen_top_half_rect_attr_name,
        ) + Vector2(offset)

    )


### TODO this will be passed to transition screen to be executed
### once the transition ends

def start_first_level():
    """Start first level."""

    level_manager = REFS.states.level_manager
    REFS.level_to_load = 'intro.lvl'
    level_manager.prepare()

    raise LoopException(next_state=level_manager)
