"""Facility with function for getting animation clock data."""

### standard library imports

from types import SimpleNamespace
from operator import attrgetter



### small utilities

length_getter = attrgetter('length')
ZERO_LENGTH_OBJ = SimpleNamespace(length=0)
TIME_SEQUENCE_KEYS = ('surface_indices', 'position_indices')


### function


def get_anim_clock_keys(timing):
    """Get keys to retrieve an animation clock.

    timing
        Dictionary containing timing information about
        for each object.

    For each animation, we measure the length of all timing sequences.
    The ones with the largest length for each animation have the object name
    and sequence name stored so that such sequence can be retrieved later.

    Such 'sequence' is in fact an instance of a collections.deque subclass
    defined on common/wdeque/main.py module.

    The largest one among them is called an animation clock, because we can
    use it to infer data like the current frame being played, how much frames
    it will take for the animation to complete the current loop and how many
    loops the animation performed (including backwards, if it is the case).

    Storing a reference to the deque itself would work too, but since all
    timing sequences are meant to be 'deepcopied' on the game package, we use
    the alternative approach of storing the keys instead.
    """
    ### create map to store anim clock keys
    anim_clock_keys = {}

    for anim_name, anim_timing_values in timing.items():

        ### assign dummy as current largest deque
        largest_deque = ZERO_LENGTH_OBJ

        ### iterate over object' deques to find largest one

        for obj_name, obj_sequences_map in anim_timing_values.items():

            ## group time deques together
            ## and retrieve largest

            deques = [largest_deque]

            for key in TIME_SEQUENCE_KEYS:
                deques.append(obj_sequences_map[key])

            largest_deque = max(deques, key=length_getter)

            ## If a deque from the obj end up being the largest one,
            ## store the keys in a 2-tuple; this will execute at least once,
            ## since the initial value of the largest deque is always a dummy
            ## value of length 0, and any timing sequence is at least of
            ## length 1

            for key in TIME_SEQUENCE_KEYS:

                if largest_deque == obj_sequences_map[key]:
                    anim_clock_key_pair = (obj_name, key)

        ### create map to store keys for the largest deque
        ### in the current animation
        anim_clock_keys[anim_name] = anim_clock_key_pair


    return anim_clock_keys
