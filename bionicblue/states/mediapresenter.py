"""Facility to present media to convey information.

Media is comprised of text, images and animated sprites.
"""

### standard library imports

from collections import defaultdict, deque

from itertools import count


### third-party imports

from pygame import Rect, Surface

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

from pygame.draw import rect as draw_rect


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

from ..pygamesetup.gamepaddirect import GAMEPAD_NS, setup_gamepad_if_existent

from ..ourstdlibs.pyl import load_pyl

from ..textman import render_text

from ..classes2d.single import UIObject2D

from ..classes2d.collections import UIList2D

from ..ani2d.player import AnimationPlayer2D

from ..surfsman import draw_border

from ..userprefsman.main import USER_PREFS, KEYBOARD_CONTROLS, GAMEPAD_CONTROLS

from ..translatedtext import TRANSLATIONS, on_language_change



### module level objects

PANEL_SIZE = (
    SCREEN_RECT.width - 10,
    SCREEN_RECT.height // 3,
)

def _get_panel():

    surf = Surface(PANEL_SIZE).convert()
    surf.fill('black')

    return UIObject2D.from_surface(surf)

PANEL_CACHE = defaultdict(_get_panel)

##

INSTRUCTIONAL_TEXT_SETTINGS = {
    'style': 'regular',
    'size': 12,
    'padding': 0,
    'foreground_color': 'yellow',
    'background_color': 'blue4',
}

REPORT_DESCRIPTION_TEXT_SETTINGS = {
    'style': 'regular',
    'size': 12,
    'padding': 4,
    'foreground_color': 'white',
    'background_color': 'black',
}

REPORT_ID_TEXT_SETTINGS = {
    'style': 'regular',
    'size': 12,
    'padding': 0,
    'foreground_color': 'darkorange',
    'background_color': 'black',
}

REPORT_TEXT_SETTINGS = {
    'style': 'regular',
    'size': 12,
    'padding': 0,
    'foreground_color': 'white',
    'background_color': 'black',
}

##

_WORD_DEQUE = deque()

##

UPPER_LIMIT = SCREEN_RECT.top + 20
LOWER_LIMIT = SCREEN_RECT.bottom - 20

SCROLL_SPEED = 4
OBJ_MOVE_STEPS = 70

VERTICAL_LIMIT_TO_SHOW_VISUALS = SCREEN_RECT.centery + 40

###
SCREEN_HEADER_AREA = Rect(0, 0, SCREEN_RECT.width, 14)
SCREEN_FOOTER_AREA = SCREEN_HEADER_AREA.copy()
SCREEN_FOOTER_AREA.bottom = SCREEN_RECT.bottom



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
        self.images_to_advance = UIList2D()

        self.anisprites = UIList2D()
        self.anisprites_to_advance = UIList2D()

        self.objs_to_remove = []

        self.sounds = []
        self.music = []

        self.all_visible_objs = UIList2D()

        ### create presentation elements for all presentations (using current
        ### locale/language, for textual elements)

        for presentation_key in dm:
            self.create_presentation(presentation_key, locale)

        ### labels

        ## report label

        self.report_label = (

            UIObject2D.from_surface(
                render_text(
                    TRANSLATIONS.media_presenter.report + ':',
                    **REPORT_TEXT_SETTINGS,
                )
            )
        )

        ## instructions

        self.directionals_label = (

            UIObject2D.from_surface(
                render_text(
                    TRANSLATIONS.media_presenter.directionals_to_advance,
                    **INSTRUCTIONAL_TEXT_SETTINGS,
                )
            )

        )

        ## progress

        self.progress_label = (

            UIObject2D.from_surface(
                render_text(
                    TRANSLATIONS.media_presenter.progress + ':',
                    **INSTRUCTIONAL_TEXT_SETTINGS,
                )
            )

        )

        ## exit label

        self.exit_label = (

            UIObject2D.from_surface(
                render_text(
                    TRANSLATIONS.media_presenter.press_to_advance,
                    **INSTRUCTIONAL_TEXT_SETTINGS,
                )
            )

        )

        ## rects to assist in displaying report

        self.progress_outline_rect = (
            Rect(0, 0, SCREEN_RECT.width * .5, 12)
        )

        self.progress_fill_rect = self.progress_outline_rect.copy()

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

                locale_map = submap[locale]
                pdata = pmap[presentation_key]

                pdata['paragraphs'] = locale_map['paragraphs']
                pdata['description_label'] = locale_map['description_label']

        ### update labels

        ## report label

        rlabel = self.report_label

        rlabel.image = (

            render_text(
                TRANSLATIONS.media_presenter.report + ':',
                **REPORT_TEXT_SETTINGS,
            )

        )
        rlabel.rect = rlabel.image.get_rect()

        ## instructions

        dlabel = self.directionals_label

        dlabel.image = (

            render_text(
                TRANSLATIONS.media_presenter.directionals_to_advance,
                **INSTRUCTIONAL_TEXT_SETTINGS,
            )

        )

        dlabel.rect = dlabel.image.get_rect()

        ###

        plabel = self.progress_label

        plabel.image = (

            render_text(
                TRANSLATIONS.media_presenter.progress + ':',
                **INSTRUCTIONAL_TEXT_SETTINGS,
            )

        )

        plabel.rect = plabel.image.get_rect()

        ###

        elabel = self.exit_label

        elabel.image = (

            render_text(
                TRANSLATIONS.media_presenter.press_to_advance,
                **INSTRUCTIONAL_TEXT_SETTINGS,
            )

        )

        elabel.rect = elabel.image.get_rect()

    def prepare(self, presentation_key):
        """Prepare objects for given presentation."""

        presentation = self.presentation_map[presentation_key]

        ### images

        append_image = self.images.append

        processed_images_data = presentation['images']

        for image_data in processed_images_data.values():

            obj = image_data['obj']
            obj.rect.right = SCREEN_RECT.left
            obj.step_no = 0
            append_image(obj)

        ### animated sprites

        append_anisprite = self.anisprites.append

        processed_anisprites_data = presentation['animated_sprites']

        for anisprite_data in processed_anisprites_data.values():

            obj = anisprite_data['obj']
            obj.rect.right = SCREEN_RECT.left
            obj.step_no = 0
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

        ## align lines in each paragraph one below the other

        for paragraph in paragraphs:

            paragraph.rect.snap_rects_ip(

                retrieve_pos_from='bottomleft',
                assign_pos_to='topleft',
                offset_pos_by=(0, 1),

            )

        ## align paragraphs one below the other, with extra space
        ## below the panel (so visually, each panel is much closer
        ## to the paragraph above it, which is the one associated
        ## with it; our goal is to make it easier for users to spot the
        ## paragraph to which each panel is associated with)

        paragraphs.rect.snap_rects_ip(

            retrieve_pos_from='bottomleft',
            assign_pos_to='topleft',
            offset_pos_by=(0, PANEL_SIZE[1] + 30),

        )

        ## add report description, report label, id and paragraphs to
        ## collection of visible objs

        report_label = self.report_label
        id_label = presentation['id_label']
        description_label = presentation['description_label']

        report_label.rect.top = UPPER_LIMIT

        paragraphs.rect.centerx = description_label.rect.centerx = (
            SCREEN_RECT.centerx
        )

        report_label.rect.left = paragraphs.rect.left
        id_label.rect.bottomleft = report_label.rect.move(2, 0).bottomright
        
        description_label.rect.top = report_label.rect.bottom + 15

        paragraphs.rect.top = description_label.rect.bottom + 15

        vobjs = self.all_visible_objs

        vobjs.append(report_label)
        vobjs.append(id_label)
        vobjs.append(description_label)

        for index, paragraph in enumerate(paragraphs):

            panel = PANEL_CACHE[index]

            panel.rect.top = paragraph.rect.bottom + 1
            panel.rect.centerx = SCREEN_RECT.centerx

            vobjs.append(paragraph)
            vobjs.append(panel)


        ### reposition labels and progress rects

        self.directionals_label.rect.topleft = SCREEN_RECT.move(2, 1).topleft

        self.progress_label.rect.bottomleft = (
            SCREEN_RECT.move(2, -1).bottomleft
        )

        self.exit_label.rect.bottomleft = self.progress_label.rect.bottomleft

        ## 

        self.progress_outline_rect.left = self.progress_label.rect.right + 2
        self.progress_outline_rect.bottom = SCREEN_RECT.bottom - 1

        self.progress_fill_rect.bottomleft = (
            self.progress_outline_rect.bottomleft
        )

        ### measure total distance from bottom of visual objects to the lower
        ### limit of the screen, which will be used to calculate percentage of
        ### report that was scrolled
        self.report_height = vobjs.rect.bottom - LOWER_LIMIT

        ### set report's progress to 0, since we are just about to begin
        ### presenting the report
        self.report_progress = 0.0

    def create_presentation(self, presentation_key, locale):
        """Create presentation elements, using given locale for text."""

        ### grab data
        data = self.data_map[presentation_key]

        ### create presentation
        presentation = {}

        ### populate it according to data

        ## report id (fictional id, has nothing to do with game internals)

        presentation['id_label'] = (

            UIObject2D.from_surface(
                render_text(
                    data['report_id'],
                    **REPORT_ID_TEXT_SETTINGS,
                )
            )

        )

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

            for key in (
                'panel_index',
                'end_pos',
                'start_pos',
            ):
                setattr(image_obj, key, loaded_image_data[key])



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

            anim_data_name = (
                loaded_anisprite_data.get('anim_data_name', anisprite_name)
            )
            anim_name = loaded_anisprite_data['anim_name']
            
            anisprite_obj = UIObject2D()
            anisprite_obj.aniplayer = (
                AnimationPlayer2D(anisprite_obj, anim_data_name, anim_name)
            )

            anisprite_data['obj'] = anisprite_obj

            for key in (
                'panel_index',
                'end_pos',
                'start_pos',
            ):
                setattr(anisprite_obj, key, loaded_anisprite_data[key])

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

        pdata = self.presentation_map[presentation_key]
        tpm = self.textual_presentation_map

        plocale_data = tpm[presentation_key][locale] = {}

        paragraphs = pdata['paragraphs'] = plocale_data['paragraphs'] = UIList2D()

        pdata['paragraphs'] = paragraphs

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
                    render_text(word, **REPORT_TEXT_SETTINGS)
                )

                for word in paragraph.split()

            )

            words.rect.snap_rects_intermittently_ip(

                ### interval limit

                dimension_name='width', # either 'width' or 'height'
                dimension_unit='pixels', # either 'rects' or 'pixels'
                max_dimension_value=int(SCREEN_RECT.width * .8), # posit. int.

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

        ###

        description_label = (

            UIObject2D.from_surface(
                render_text(
                    t.report_description,
                    **REPORT_DESCRIPTION_TEXT_SETTINGS,
                )
            )

        )

        draw_border(
            surf=description_label.image,
            color=REPORT_DESCRIPTION_TEXT_SETTINGS['foreground_color'],
            width=1,
        )

        pdata['description_label'] = plocale_data['description_label'] = (
            description_label
        )

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

        objs_to_remove = self.objs_to_remove
        ###

        images = self.images
        images_ta = self.images_to_advance


        for obj in images:

            panel_rect = PANEL_CACHE[obj.panel_index].rect

            if panel_rect.top < VERTICAL_LIMIT_TO_SHOW_VISUALS:
                images_ta.append(obj)

        for obj in images_ta:

            panel_rect = PANEL_CACHE[obj.panel_index].rect

            if SCREEN_RECT.colliderect(panel_rect):
                advance_position(obj, panel_rect)

            if obj in images:
                objs_to_remove.append(obj)

        while objs_to_remove:
            images.remove(objs_to_remove.pop())

        ###

        anisprites = self.anisprites
        anisprites_ta = self.anisprites_to_advance

        for obj in self.anisprites:

            panel_rect = PANEL_CACHE[obj.panel_index].rect

            if panel_rect.top < VERTICAL_LIMIT_TO_SHOW_VISUALS:
                anisprites_ta.append(obj)

        for obj in anisprites_ta:

            panel_rect = PANEL_CACHE[obj.panel_index].rect

            if SCREEN_RECT.colliderect(panel_rect):
                advance_position(obj, panel_rect)

            if obj in anisprites:
                objs_to_remove.append(obj)

        while objs_to_remove:
            anisprites.remove(objs_to_remove.pop())

    def move_forward(self):

        vobjs = self.all_visible_objs
        vobjs_rect = vobjs.rect

        ## if bottom below lower limit...

        if vobjs_rect.bottom > LOWER_LIMIT:

            vobjs.rect.move_ip(0, -SCROLL_SPEED)

            ## if bottom ends up above lower limit...

            if vobjs_rect.bottom < LOWER_LIMIT:
                vobjs.rect.bottom = LOWER_LIMIT

        ### move words/lines;
        ###
        ### once paragraphs are finished, blink arrow to start next section
        ### on button press;
        ###
        ### if there's no next section, go to next state (start level)
        ...

    def move_backwards(self):

        vobjs = self.all_visible_objs
        vobjs_rect = vobjs.rect

        ## if top above upper limit...

        if vobjs_rect.top < UPPER_LIMIT:

            vobjs.rect.move_ip(0, SCROLL_SPEED)

            ## if top ends up below upper limit...

            if vobjs_rect.top > UPPER_LIMIT:
                vobjs.rect.top = UPPER_LIMIT


    def draw(self):

        SCREEN.fill('black')

        for obj in self.all_visible_objs:

            if isinstance(obj, UIList2D):
                for line in obj:
                    for word in line:
                        word.draw()

            else:
                obj.draw()

        self.images_to_advance.draw()

        for obj in self.anisprites_to_advance:
            obj.aniplayer.draw()

        SCREEN.fill('blue4', SCREEN_HEADER_AREA)
        SCREEN.fill('blue4', SCREEN_FOOTER_AREA)

        self.directionals_label.draw()

        ### progress or continue label

        self.report_progress = (

            1 - (

                (self.all_visible_objs.rect.bottom - LOWER_LIMIT)

                / self.report_height

            )

        )

        if self.report_progress < 1:
            self.draw_progress_widgets()

        else:
            self.exit_label.draw()

        update()


    def draw_progress_widgets(self):

        progress = self.report_progress

        self.progress_label.draw()

        self.progress_fill_rect.width = (
            self.progress_outline_rect.width * progress
        )

        if progress < .3:
            progress_color = 'red'
        elif progress > .7:
            progress_color = 'green'
        else:
            progress_color = 'orangered'

        draw_rect(
            SCREEN,
            progress_color,
            self.progress_fill_rect,
        )

        draw_rect(
            SCREEN,
            'yellow',
            self.progress_outline_rect,
            1,
        )


### utility functions

def advance_position(obj, panel_rect):

    rect = obj.rect

    start_pos = get_relative_topleft(rect, panel_rect, *obj.start_pos)
    end_pos = get_relative_topleft(rect, panel_rect, *obj.end_pos)

    rect.topleft = Vector2(start_pos).lerp(end_pos, obj.step_no/OBJ_MOVE_STEPS)

    if obj.step_no < OBJ_MOVE_STEPS:
        obj.step_no += 1

def get_relative_topleft(
    rect_a,
    rect_b,
    rect_a_attr_name,
    rect_b_attr_name,
    offset,
):

    setattr(

        rect_a,

        rect_a_attr_name,

        getattr(
            rect_b.move(offset),
            rect_b_attr_name,
        ),

    )

    return rect_a.topleft


### TODO this will be passed to transition screen to be executed
### once the transition ends

def start_first_level():
    """Start first level."""

    level_manager = REFS.states.level_manager
    REFS.level_to_load = 'intro.lvl'
    level_manager.prepare()

    raise LoopException(next_state=level_manager)
