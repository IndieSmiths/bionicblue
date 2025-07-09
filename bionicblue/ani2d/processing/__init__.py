
### standard library imports

from collections import defaultdict

from itertools import permutations


### third-party imports

from pygame import Surface

from pygame.math import Vector2


### local imports

from ...config import COLORKEY

from ...ourstdlibs.pyl import load_pyl

from ...ourstdlibs.wdeque.main import WalkingDeque

from ...ourstdlibs.tree import get_tree_values

from .constants import OBLIVIOUS_EMPTY_GETTER

from .recolor import get_recolored_sprites_data
from .derived import process_derived_animations



DEFAULT_VERSIONS = frozenset({'default', 'invisible'})


KEY_DEFAULT_PAIRS = (

    # surfaces

    (
        # key
        'surfaces',
        # value
        {
            #
            'default': OBLIVIOUS_EMPTY_GETTER,
            #
            'invisible': OBLIVIOUS_EMPTY_GETTER
        },
    ),

    # positions
    ('positions', ((0, 0),)),

)


def process_animation_data(animation_dir):

    metadata_path = next(p for p in animation_dir.iterdir() if p.suffix.lower() == '.pyl')
    metadata = load_pyl(str(metadata_path))

    ###

    geometry_data = metadata['geometry']

    objects = {}

    for obj_name, obj_data in metadata['objects'].items():
        objects[obj_name] = geometry_data[obj_data['geometry']]


    ###
    existing_structures = metadata['existing_structures']

    for struct_data in existing_structures.values():

        ###
        tree = struct_data['tree']
        optional_order = tuple(get_tree_values(tree, 'name', 'children'))

        ###

        for key in ('updating_order', 'drawing_order'):

            try: struct_data[key]
            except KeyError:
                struct_data[key] = optional_order

        ###
        struct_data['object_names'] = optional_order

    structures = {
        anim_name: existing_structures[anim_data['structure']]
        for anim_name, anim_data in metadata['animations'].items()
    }

    ### prepare recoloring instructions if requested

    try:
        recoloring_data = metadata['recolored_surface_versions']

    except KeyError:
        non_default_versions = set()
        #
        recolor_instructions_map = {}

    else:
        non_default_versions = recoloring_data.keys()
        #
        recolor_instructions_map = defaultdict(dict)

        for key, recolor_instructions in recoloring_data.items():

            if key in DEFAULT_VERSIONS:

                raise ValueError(
                    "Recolored versions cannot be named"
                    f" either of {DEFAULT_VERSIONS}"
                )

            recolor_effects = recolor_instructions['effects']

            sprites_identifiers = recolor_instructions['surface_collections']

            for sprites_identifier in sprites_identifiers:

                recolor_instructions_map[sprites_identifier][key] = (
                    recolor_effects
                )

    ### pxa value grabbing

    pxa_paths = [
        path
        for path in animation_dir.iterdir()
        if path.suffix.lower() == '.pxa'
    ]

    all_pxa_values = {}
    all_pxa_timing = {}

    for path in pxa_paths:

        pxa_data = load_pyl(str(path))

        stem = path.stem

        pxa_values = all_pxa_values[stem] = {}
        pxa_timing = all_pxa_timing[stem] = {}


        ###
        surfaces = []
        append_surface = surfaces.append
        clear_surfaces = surfaces.clear

        for anim_name, anim_data in pxa_data['animations'].items():

            size = anim_data['size']

            anim_values = pxa_values[anim_name] = {}

            ###
            versions = list(DEFAULT_VERSIONS)

            ###

            sprites_identifier = f'{stem}.{anim_name}'

            if sprites_identifier in recolor_instructions_map:

                version_instructions_map = (
                    recolor_instructions_map[sprites_identifier]
                )

                versions.extend(version_instructions_map)

            ###

            surfc_map = anim_values['surface_collections_map'] = {}

            default_sprites_data = anim_data['sprites']

            ###
            base_surf = Surface((size, size)).convert()
            base_surf.fill(COLORKEY)
            base_surf.set_colorkey(COLORKEY)
            ###

            for version in versions:

                if version == 'invisible':

                    surfc_map[version] = OBLIVIOUS_EMPTY_GETTER
                    continue

                ###

                if version == 'default':
                    sprites_data = default_sprites_data

                else:
                    sprites_data = (
                        get_recolored_sprites_data(
                            default_sprites_data,
                            version_instructions_map[version],
                        )
                    )


                ###
                for sprite_data in sprites_data:

                    ## create and append surface

                    surf = base_surf.copy()
                    append_surface(surf)

                    ## paint surface

                    for color, points in sprite_data.items():
                        for point in points:
                            surf.set_at(tuple(map(int, point)), color)

                surfc_map[version] = tuple(surfaces)
                clear_surfaces()

            ### set default surfaces as default for missing non-default
            ### versions

            default_surfaces = surfc_map['default']
            for version in non_default_versions:
                surfc_map.setdefault(version, default_surfaces)

            ###
            anim_values['positions'] = ((0, 0),)

            ###

            anim_timing = pxa_timing[anim_name] = {}

            ###

            no_of_frames = anim_data['number_of_frames']
            sprite_placement = anim_data['sprite_placement']

            surf_indices = []

            for frame_index in range(no_of_frames):

                if frame_index in sprite_placement:
                    sprite_index = sprite_placement[frame_index]

                surf_indices.append(sprite_index)


            anim_timing['surface_indices'] = tuple(surf_indices)
            ###
            anim_timing['position_indices'] = (0,)

    ### pos value grabbing

    pos_paths = [
        path
        for path in animation_dir.iterdir()
        if path.suffix.lower() == '.pos'
    ]

    all_pos_values = {}
    all_pos_timing = {}

    for path in pos_paths:

        pos_data = load_pyl(str(path))

        all_pos_values[path.stem] = pos_data
        all_pos_timing[path.stem] = tuple(range(len(pos_data)))


    ### storing grabbed values and timing

    ## values

    raw_values = metadata['values']

    values = {}

    for anim_name, raw_data in raw_values.items():

        anim_values = values[anim_name] = {}

        for obj_name, raw_obj_values in raw_data.items():

            obj_values = anim_values[obj_name] = {}

            for key, default in KEY_DEFAULT_PAIRS:

                if key in raw_obj_values:

                    if key == 'surfaces':

                        stem, pxa_anim_name = raw_obj_values[key].split('.')

                        obj_values['surface_collections_map'] = (
                            all_pxa_values
                            [stem][pxa_anim_name]
                            ['surface_collections_map']
                        )

                    elif key == 'positions':

                        stem = raw_obj_values[key]
                        obj_values[key] = all_pos_values[stem]

                else:

                    if key == 'surfaces':
                        obj_values['surface_collections_map'] = default

                    else:
                        obj_values[key] = default

    ## timing

    keys = ('surface_indices', 'position_indices')

    raw_timing = metadata['timing']

    timing = {}

    for anim_name, raw_data in raw_timing.items():

        anim_timing = timing[anim_name] = {}

        for obj_name, raw_obj_timing in raw_data.items():

            obj_timing = anim_timing[obj_name] = {}

            for key in keys:

                if key in raw_obj_timing:

                    if key == 'surface_indices':
                        stem, pxa_anim_name = raw_obj_timing[key].split('.')
                        obj_timing[key] = WalkingDeque(all_pxa_timing[stem][pxa_anim_name][key])

                    else:
                        stem = raw_obj_timing[key]
                        obj_timing[key] = WalkingDeque(all_pos_timing[stem])

                else:
                    obj_timing[key] = WalkingDeque((0,))

    ###
    process_derived_animations(metadata, values, timing)

    ###

    anim_names = tuple(metadata['animations'])
    pairs = permutations(anim_names, 2)

    exchange_map = defaultdict(dict)

    for anim_a, anim_b in pairs:
        exchange_map[anim_a][anim_b] = 'midbottom', 'midbottom', (0, 0)

    exchange_map = dict(exchange_map)
    exchange_map.update(metadata.get('root_pos_exchange_map', {}))

    for value_dict in exchange_map.values():

        for key, value in value_dict.items():

            a, b, c = value
            value_dict[key] = a, b, Vector2(c)

    ###

    return {
      'objects': objects,
      'structure': structures,
      'blending': metadata.get('blending', {}),
      'values': values,
      'timing': timing,
      'root_pos_exchange_map': exchange_map,
    }
