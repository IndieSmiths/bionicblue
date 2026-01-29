"""Facility with class extension for report presenter."""

### standard library imports

from collections import deque

from itertools import count


### local imports

from ...config import SURF_MAP, SOUND_MAP

from ...pygamesetup.constants import SCREEN_RECT

from ...textman import render_text

from ...classes2d.single import UIObject2D

from ...classes2d.collections import UIList2D

from ...ani2d.player import AnimationPlayer2D

from ...surfsman import draw_border

from ...translatedtext import TRANSLATIONS

from .constants import REPORT_TEXT_SETTINGS



### module level objects

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

_WORD_DEQUE = deque()


### class definition

class ReportPreprocessing:
    """Preprocessing operations for report presenter class."""

    def create_report(self, report_key, locale):
        """Create report elements, using given locale for text."""

        ### grab data
        data = self.data_map[report_key]

        ### create report
        report = {}

        ### populate it according to data

        ## report id (fictional id, has nothing to do with game internals)

        report['id_label'] = (

            UIObject2D.from_surface(
                render_text(
                    data['report_id'],
                    **REPORT_ID_TEXT_SETTINGS,
                )
            )

        )

        ## images

        processed_images_data = report['images'] = {}

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

        processed_anisprites_data = report['animated_sprites'] = {}

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

        ## XXX sound will be implemented at a later data,
        ## if at all
        ##
        ## also, must think of ways to time triggering sound;
        ##
        ## possibilities:
        ##
        ## - at beginning of section
        ## - at end of section
        ## - on elapsed time starting from beginning of section
        ## - on animation pose
        ## - on image positioning step
        ## - on animation positioning step

        ## sound

#        processed_sounds_data = report['sounds'] = {}
#
#        for loaded_sound_data in data.get('sounds', ()):
#
#            ###
#            sound_name = loaded_sound_data['name']
#
#            ###
#            sound_data = processed_sounds_data[sound_name] = {}
#
#            ###
#            sound_obj = sound_map[sound_name]
#
#            sound_data['sound'] = sound_obj



        ## music

        if 'music' in data:
            report['music'] = data['music']


        ### store the report
        self.report_map[report_key] = report

        ### create textual elements
        self.create_and_integrate_textual_elements(report_key, locale)

    def create_and_integrate_textual_elements(self, report_key, locale):
        """Create textual elements and add to report."""

        rdata = self.report_map[report_key]

        plocale_data = self.textual_report_map[report_key][locale] = {}

        paragraphs = rdata['paragraphs'] = plocale_data['paragraphs'] = (
            UIList2D()
        )

        rdata['paragraphs'] = paragraphs

        ###

        t = getattr(TRANSLATIONS, f'{report_key}_report')

        next_index = count().__next__

        while True:

            paragraph_attr_name = (
                'paragraph_'
                + str(next_index()).rjust(2, '0')
            )

            try:
                paragraph = getattr(t, paragraph_attr_name)

            except AttributeError:
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

        rdata['description_label'] = plocale_data['description_label'] = (
            description_label
        )
