
### standard library import
from collections import defaultdict


### third-party import
from pygame import Surface



EMPTY_SURF = Surface((0, 0)).convert()


def get_empty_surf():
    return EMPTY_SURF

OBLIVIOUS_EMPTY_GETTER = defaultdict(get_empty_surf)
