"""Facility to present media to convey information.

Media is comprised of text, images and animated sprites.
"""

### standard library import
from collections import defaultdict


### third-party import
from pygame import Rect


### local imports

from ...config import REPORTS_DIR

from ...pygamesetup.constants import SCREEN_RECT

from ...ourstdlibs.pyl import load_pyl

from ...textman import render_text

from ...classes2d.single import UIObject2D

from ...classes2d.collections import UIList2D

from ...userprefsman.main import USER_PREFS

from ...translatedtext import TRANSLATIONS, on_language_change

from .constants import (
    REPORT_TEXT_SETTINGS,
    UPPER_LIMIT,
    LOWER_LIMIT,
    PANEL_SIZE,
    PANEL_CACHE,
)

# extension classes 
from .preprocessing import ReportPreprocessing
from .loopmanagement import ReportLoopManagement



### module level object

INSTRUCTIONAL_TEXT_SETTINGS = {
    'style': 'regular',
    'size': 12,
    'padding': 0,
    'foreground_color': 'yellow',
    'background_color': 'blue4',
}


### class definition

class ReportPresenter(ReportPreprocessing, ReportLoopManagement):
    """Presents text, images and animated sprites as a report.

    Used to present lore to users.
    """

    def __init__(self):

        dm = self.data_map = {}

        for path in REPORTS_DIR.iterdir():

            if path.suffix.lower() == '.pyl':

                try:
                    data = load_pyl(path)

                except Exception as err:

                    print("Error while trying to load report")
                    print()
                    raise

                else:
                    dm[path.stem] = data

        ### map for all report elements
        self.report_map = defaultdict(dict)

        ### map for textual elements, since they are dependent on the
        ### locale/language
        self.textual_report_map = defaultdict(dict)

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

        ### create report elements for all reports (using current
        ### locale/language, for textual elements)

        for report_key in dm:
            self.create_report(report_key, locale)

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

        trm = self.textual_report_map

        if any(
            locale not in submap
            for submap in trm.values()
        ):

            for report_key in trm:

                self.create_and_integrate_textual_elements(
                    report_key,
                    locale,
                )

        ### otherwise, just reference the existent textual elements

        else:

            rmap = self.report_map

            for report_key, submap in trm.items():

                locale_map = submap[locale]
                rdata = rmap[report_key]

                rdata['paragraphs'] = locale_map['paragraphs']
                rdata['description_label'] = locale_map['description_label']

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

    def prepare(self, report_key):
        """Prepare objects for given report."""

        report = self.report_map[report_key]

        ### images

        append_image = self.images.append

        processed_images_data = report['images']

        for image_data in processed_images_data.values():

            obj = image_data['obj']
            obj.rect.right = SCREEN_RECT.left
            obj.step_no = 0
            append_image(obj)

        ### animated sprites

        append_anisprite = self.anisprites.append

        processed_anisprites_data = report['animated_sprites']

        for anisprite_data in processed_anisprites_data.values():

            obj = anisprite_data['obj']
            obj.rect.right = SCREEN_RECT.left
            obj.step_no = 0
            append_anisprite(obj)

        ### sound

        append_sound = self.sounds.append

        processed_sounds_data = report['sounds']

        for sound_data in processed_sounds_data.values():
            append_sound(sound_data['sound'])


        ### music

        append_music = self.music.append

        processed_music_data = report['music']

        for music_data in processed_music_data.values():
            append_music(music_data['name'])

        ### text

        ## retrieve paragraphs
        paragraphs = report['paragraphs']

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
        id_label = report['id_label']
        description_label = report['description_label']

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
