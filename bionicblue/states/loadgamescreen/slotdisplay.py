"""Facility w/ custom class to display and interact with save slots."""

### standard library import
from functools import partial


### third-party imports

from pygame import Surface

from pygame.draw import rect as draw_rect


### local imports

from ...config import COLORKEY, SURF_MAP

from ...classes2d.single import UIObject2D

from ...classes2d.collections import UIList2D

from ...textman import render_text, update_text_surface

from ...translatedtext import TRANSLATIONS



LABEL_TEXT_SETTINGS = {
    'style': 'regular',
    'size': 12,
    'padding': 0,
    'foreground_color': 'white',
    'background_color': 'darkblue',
}

t = TRANSLATIONS.load_game_screen


class SlotDisplay(UIList2D):
    """Represents a save slot."""

    def __init__(
        self,
        slot_path,
        slot_data,
        button_surfs_map,
        trigger_command,
    ):

        super().__init__()

        ###

        self.slot_path = slot_path
        self.slot_data = slot_data
        self.command = partial(trigger_command, slot_path)

        ###

        slot_name = slot_path.stem

        slot_name_label = (

            UIObject2D.from_surface(
                render_text(
                    slot_name,
                    **LABEL_TEXT_SETTINGS,
                )
            )

        )

        self.append(slot_name_label)

        ###

        last_played_label = self.last_played_label = (
            UIObject2D.from_surface(
                render_text(
                    t.labels.last_played + ":",
                    **LABEL_TEXT_SETTINGS,
                ),
            )
        )

        last_played_label.rect.topleft = (
            slot_name_label.rect.move(10, 0).bottomleft
        )

        self.append(last_played_label)

        ###

        timestamp_text = slot_data['last_played_date'][:19]

        timestamp_label = self.timestamp_label = (
            UIObject2D.from_surface(
                render_text(
                    timestamp_text,
                    **LABEL_TEXT_SETTINGS,
                ),
                timestamp_text = timestamp_text,
            )
        )

        self.append(timestamp_label)

        timestamp_label.rect.midleft = (
            last_played_label.rect.move(2, 0).midright
        )

        ###

        self.button_surfs_map = button_surfs_map

        load_button = self.load_button = (
            UIObject2D.from_surface(button_surfs_map['load_button'])
        )

        rename_button = self.rename_button = (
            UIObject2D.from_surface(button_surfs_map['rename_button'])
        )

        erase_button = self.erase_button = (
            UIObject2D.from_surface(button_surfs_map['erase_button'])
        )

        load_button.rect.topleft = last_played_label.rect.move(0, 5).bottomleft
        rename_button.rect.topleft = load_button.rect.move(5, 0).topright
        erase_button.rect.topleft = rename_button.rect.move(5, 0).topright

        self.append(load_button)
        self.append(rename_button)
        self.append(erase_button)


        ### beaten bosses label and objs

        beaten_bosses_label = self.beaten_bosses_label = (
            UIObject2D.from_surface(
                render_text(
                    t.labels.beaten_bosses + ":",
                    **LABEL_TEXT_SETTINGS,
                )
            )
        )

        beaten_bosses_label.rect.topleft = (
            load_button.rect.move(0, 5).bottomleft
        )

        self.append(beaten_bosses_label)

        previous_obj = beaten_bosses_label

        boss_objs = self.boss_objs = UIList2D(

            UIObject2D.from_surface(
                SURF_MAP[f'{boss_name}_head.png'],
                boss_name = boss_name,
            )

            for boss_name in slot_data.get('beaten_bosses', ())

        )

        if boss_objs:

            boss_objs.rect.snap_rects_ip(
                retrieve_pos_from='midright',
                assign_pos_to='midleft',
                offset_pos_by=(2, 0),
            )

            boss_objs.rect.midleft = (
                beaten_bosses_label.rect.move(2, 0).midright
            )

        self.extend(boss_objs)


        ### encounter label and objs

        encounters_label = self.encounters_label = (
            UIObject2D.from_surface(
                render_text(
                    t.labels.encounters + ":",
                    **LABEL_TEXT_SETTINGS,
                )
            )
        )

        encounters_label.rect.topleft = (
            beaten_bosses_label.rect.move(0, 5).bottomleft
        )

        self.append(encounters_label)

        encounter_objs = self.encounter_objs = UIList2D(

            UIObject2D.from_surface(
                SURF_MAP[f'{encounter_name}_head.png'],
                encounter_name = encounter_name,
            )

            for encounter_name in slot_data.get('encounters', ())

        )

        if encounter_objs:

            encounter_objs.rect.snap_rects_ip(
                retrieve_pos_from='midright',
                assign_pos_to='midleft',
                offset_pos_by=(2, 0),
            )

            encounter_objs.rect.midleft = (
                encounters_label.rect.move(2, 0).midright
            )

        self.extend(encounter_objs)

        ###
        self.rebuild_bg_obj()

    def on_language_change(self):

        ### update last played label's text

        update_text_surface(
            self.last_played_label,
            t.labels.last_played + ":",
            LABEL_TEXT_SETTINGS,
            pos_to_align='midleft',
        )

        ### reposition timestamp label accordingly

        self.timestamp_label.rect.midleft = (
            self.last_played_label.rect.move(2, 0).midright
        )

        ### update beaten bosses label's text

        update_text_surface(
            self.beaten_bosses_label,
            t.labels.beaten_bosses + ":",
            LABEL_TEXT_SETTINGS,
            pos_to_align='midleft',
        )

        ### reposition boss objs accordingly

        if self.boss_objs:

            self.boss_objs.rect.midleft = (
                self.beaten_bosses_label.rect.move(2, 0).midright
            )

        ### update surface and rect of buttons

        for button_name in ('load_button', 'erase_button'):

            obj = getattr(self, button_name)

            new_surf = self.button_surfs_map[button_name]
            new_rect = new_surf.get_rect()

            new_rect.midleft = obj.rect.midleft

            obj.image = new_surf
            obj.rect = new_rect

        self.erase_button.rect.topleft = (
            self.load_button.rect.move(5, 0).topright
        )

        ### update encounters label's text

        update_text_surface(
            self.encounters_label,
            t.labels.encounters + ":",
            LABEL_TEXT_SETTINGS,
            pos_to_align='midleft',
        )

        ### reposition boss objs accordingly

        if self.encounter_objs:

            self.encounter_objs.rect.midleft = (
                self.encounters_label.rect.move(2, 0).midright
            )

        ### rebuild bg
        self.rebuild_bg_obj()

    def rebuild_bg_obj(self):

        if not hasattr(self, 'bg_obj'):
            bg_obj = self.bg_obj = UIObject2D()

        else:
            bg_obj = self.pop(0)

        ###

        bg_rect = self.rect.inflate(10, 10)
        bg_surf = Surface(bg_rect.size).convert()
        bg_surf.set_colorkey(COLORKEY)
        bg_surf.fill(COLORKEY)

        draw_bg_rect = bg_surf.get_rect()

        draw_rect(bg_surf, 'darkblue', draw_bg_rect, border_radius=10)
        draw_rect(bg_surf, 'white', draw_bg_rect, 2, border_radius=10)

        bg_obj.image = bg_surf
        bg_obj.rect = bg_rect

        self.insert(0, bg_obj)

    def update_last_played_timestamp(self):

        updated_timestamp = (
            self.slot_data['last_played_date'][:19]
        )

        timestamp_label = self.timestamp_label

        if updated_timestamp == timestamp_label.timestamp_text:
            return

        update_text_surface(
            timestamp_label,
            updated_timestamp,
            LABEL_TEXT_SETTINGS,
            pos_to_align='midleft',
        )

    ### XXX this and the next update method do exactly the same thing,
    ### except they use different attributes, keys, collections;
    ###
    ### since there are only 02 instances of the same behaviour, it is okay
    ### to let then coexist; if there needs to be another instance of this
    ### kind of behaviour, though, refactor everything so a single method
    ### can be used instead

    def update_beaten_bosses(self):
        """Add new beaten bosses if any."""

        boss_objs = self.boss_objs

        no_of_beaten_bosses = len(self.slot_data.get('beaten_bosses', ()))
        no_of_boss_objs = len(boss_objs)

        diff = no_of_beaten_bosses - no_of_boss_objs

        if diff:

            for obj in boss_objs:
                self.remove(obj)

            for index, boss_name in enumerate(self.slot_data['beaten_bosses']):

                if index >= no_of_boss_objs:

                    boss_objs.append(
                        UIObject2D.from_surface(
                            SURF_MAP[f'{boss_name}_head.png'],
                            boss_name = boss_name,
                        )
                    )

            boss_objs.rect.snap_rects_ip(
                retrieve_pos_from='midright',
                assign_pos_to='midleft',
                offset_pos_by=(2, 0),
            )

            beaten_bosses_label = self.beaten_bosses_label

            boss_objs.rect.midleft = (
                beaten_bosses_label.rect.move(2, 0).midright
            )

            index_to_insert = self.index(beaten_bosses_label) + 1

            for obj in boss_objs:

                self.insert(index_to_insert, obj)
                index_to_insert += 1

    def update_encounters(self):
        """Add new encounters if any."""

        encounter_objs = self.encounter_objs

        no_of_encounters = len(self.slot_data.get('encounters', ()))
        no_of_encounter_objs = len(encounter_objs)

        diff =  no_of_encounters - no_of_encounter_objs

        if diff:

            for obj in encounter_objs:
                self.remove(obj)

            for index, encounter_name in (
                enumerate(self.slot_data['encounters'])
            ):

                if index >= no_of_encounter_objs:

                    encounter_objs.append(
                        UIObject2D.from_surface(
                            SURF_MAP[f'{encounter_name}_head.png'],
                            encounter_name = encounter_name,
                        )
                    )

            encounter_objs.rect.snap_rects_ip(
                retrieve_pos_from='midright',
                assign_pos_to='midleft',
                offset_pos_by=(2, 0),
            )

            encounters_label = self.encounters_label

            encounter_objs.rect.midleft = (
                encounters_label.rect.move(2, 0).midright
            )

            index_to_insert = self.index(self.encounters_label) + 1

            for obj in encounter_objs:

                self.insert(index_to_insert, obj)
                index_to_insert += 1
