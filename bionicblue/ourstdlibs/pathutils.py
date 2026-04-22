"""Extra utilities for working with paths, temporary or not."""

### standard library imports

from pathlib import Path

from itertools import count

from tempfile import gettempdir



_TEMP_DIR = Path(gettempdir())


def get_available_path_on_dir(
    *,
    suffix='',
    prefix='',
    base_name='temp',
    dirpath=None,
):

    if dirpath is None:
        dirpath = _TEMP_DIR

    if not base_name:
        raise ValueError("'base_name' must be a non-empty string.")

    numbering_string = ''

    next_index = count().__next__

    while True:

        pathname = (
            prefix
            + base_name
            + numbering_string
            + suffix
        )
        
        path = dirpath / pathname

        if path.exists():
            numbering_string = '_' + str(next_index()).rjust(3, '0')

        else:
            break


    return path

