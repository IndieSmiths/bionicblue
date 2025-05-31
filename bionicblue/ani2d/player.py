
### standard library imports

from copy import deepcopy

from itertools import chain, cycle


### third-party imports

from pygame import Rect

from pygame.math import Vector2


### local imports

from ..config import ANIM_DATA_MAP

from ..pygamesetup.constants import blit_on_screen



DEFAULT_CYCLE_VALUES = ('default',)
GET_DEFAULT = cycle(DEFAULT_CYCLE_VALUES).__next__



class AnimationPlayer2D:

    def __init__(
        self,
        obj,
        anim_data_key,
        anim_name,
        pos_name='topleft',
        pos_value=(0, 0),
    ):

        self.obj = obj

        anim_data = ANIM_DATA_MAP[anim_data_key]

        self.structure = anim_data['structure']
        self.blending = anim_data['blending']
        self.values = anim_data['values']
        self.root_pos_exchange_map = anim_data['root_pos_exchange_map']
        self.timing = deepcopy(anim_data['timing'])

        self.walking_data = []
        self.drawing_methods = []

        self.object_map = {
            obj_name : AnimationObject2D(obj_data)
            for obj_name, obj_data in anim_data['objects'].items()
        }

        ###
        self.anim_names = self.structure.keys()
        self.anim_name = anim_name

        ###

        self.root = root = self.object_map[self.structure[anim_name]['tree']['name']]
        obj.rect = root.rect
        setattr(obj.rect, pos_name, pos_value)

        ###
        self.cycle_values = DEFAULT_CYCLE_VALUES
        self.next_surf_version = GET_DEFAULT
        self.switch_animation(anim_name)

    def switch_animation(self, anim_name):
        ###
        prev_anim = self.anim_name
        self.anim_name = anim_name

        ###
        self.clear_rotations()

        ###
        self.set_structure(prev_anim)

        ###
        self.store_values_and_timing()

        ###
        for obj, *_ in self.walking_data:
            obj.set_positioning()

        ###
        self.draw = self.no_walk_draw

    def clear_rotations(self):

        for obj_timing in self.timing[self.anim_name].values():
            for key in ('surface_indices', 'position_indices'):
                obj_timing[key].restore_walking()

    def set_structure(self, prev_anim_name):

        structure = self.structure[self.anim_name]
        tree = structure['tree']

        root = self.object_map[tree['name']]

        rect = root.rect

        if root is not self.root:

            self.exchange_root_pos(self.root, root, prev_anim_name)
            self.obj.rect = root.rect

        self.root = root

        ###

        self.root.parent = None
        self.set_parent_references(root, tree.get('children', ()))

        ###
        for key in ('updating_order','drawing_order','object_names'):
            setattr(self, key, structure[key])

    def store_values_and_timing(self):

        walking_data = self.walking_data
        walking_data.clear()

        anim_name = self.anim_name

        anim_values = self.values[anim_name]
        anim_timing = self.timing[anim_name]

        obmap = self.object_map

        for obj_name in self.updating_order:

            walking_data.append(

                (

                  obmap[obj_name],

                  anim_values[obj_name]['surface_collections_map'],
                  anim_timing[obj_name]['surface_indices'],

                  anim_values[obj_name]['positions'],
                  anim_timing[obj_name]['position_indices'],

                )

            )

        ###

        self.main_timing = max(

            chain.from_iterable(

                (
                    (surface_indices, position_indices)
                    for _, _, surface_indices, _, position_indices,
                    in walking_data
                ),

            ),

            key = lambda indices: len(indices)

        )

        ###

        drawing_methods = self.drawing_methods
        drawing_methods.clear()

        drawing_methods.extend(
            obmap[obj_name].draw
            for obj_name in self.drawing_order
        )

    def exchange_root_pos(self, previous_root, new_root, prev_anim_name):

        exchange_map = self.root_pos_exchange_map
        prev_attr_name, new_attr_name, offset = exchange_map[prev_anim_name][self.anim_name]
        pos = getattr(previous_root.rect, prev_attr_name)
        setattr(new_root.rect, new_attr_name, pos + offset)

    def set_parent_references(self, parent, children_data):

        obmap = self.object_map

        for child_data in children_data:

            child = obmap[child_data['name']]

            child.parent = parent

            self.set_parent_references(
                child,
                child_data.get('children', ())
            )

    def blend(self, directive):

        try: anim_name = self.blending[self.anim_name][directive]
        except KeyError:
            return

        self.ensure_animation(anim_name)

    def ensure_animation(self, anim_name):
        if self.anim_name != anim_name:
            self.switch_animation(anim_name)

    def restore_surface_cycling(self):

        self.cycle_values = DEFAULT_CYCLE_VALUES
        self.next_surf_version = GET_DEFAULT

    def set_custom_surface_cycling(self, cycle_values):

        self.cycle_values = cycle_values
        self.next_surf_version = cycle(cycle_values).__next__

    def walk_and_draw(self):

        version = self.next_surf_version()

        for (

            obj,

            surface_collections_map,
            surface_indices,

            positions,
            position_indices,

        ) in self.walking_data:

            surface_indices.walk(1)
            obj.image = surface_collections_map[version][surface_indices[0]]

            position_indices.walk(1)
            obj.set_pos(positions[position_indices[0]])

        ###
        for method in self.drawing_methods:
            method()

    def no_walk_draw(self):

        version = self.next_surf_version()

        for (

            obj,

            surface_collections_map,
            surface_indices,

            positions,
            position_indices,

        ) in self.walking_data:

            obj.image = surface_collections_map[version][surface_indices[0]]

            obj.set_pos(positions[position_indices[0]])

        ###

        for method in self.drawing_methods:
            method()

        ###
        self.draw = self.walk_and_draw



class AnimationObject2D:

    def __init__(self, obj_data):

        size = obj_data['size']
        self.rect = Rect(0, 0, *size)
        self.art_rect = Rect(0, 0, *obj_data.get('art_size', size))
        self.art_anchorage = obj_data.get('art_anchorage', ('center', 'center'))
        self.anchorage_offset = Vector2(obj_data.get('anchorage_offset', (0, 0)))

    def draw(self):
        blit_on_screen(self.image, self.art_rect)

    def set_positioning(self):

        if self.parent:
            self.set_pos = self.position_self_and_art

        else:
            self.set_pos = self.position_art

    def position_art(self, pos):

        pos_from, pos_to = self.art_anchorage
        art_pos = getattr(self.rect, pos_from) + self.anchorage_offset
        setattr(self.art_rect, pos_to, art_pos)

    def position_self_and_art(self, pos):

        self.rect.center = self.parent.rect.move(pos).center

        pos_from, pos_to = self.art_anchorage
        art_pos = getattr(self.rect, pos_from) + self.anchorage_offset
        setattr(self.art_rect, pos_to, art_pos)
