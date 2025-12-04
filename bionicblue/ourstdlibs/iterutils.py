"""Iteration utilities."""



def pairwise(iterable):
    """Roughly equivalent to itertools.pairwise().

    The very code was copied from its documentation.

    This replacement is to be used only when itertools's version is not
    available in the Python version used.
    """
    iterator = iter(iterable)
    a = next(iterator, None)

    for b in iterator:
        yield a, b
        a = b
