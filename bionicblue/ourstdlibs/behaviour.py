"""Facility for common behaviour.


### definitions for doctests

>>> from functools   import partial
>>> from collections import deque

"""

from functools import partial, reduce
from operator import methodcaller
from collections import deque


class CallList(list):
    """A list of callable objects to be executed in order."""

    def __init__(self, *args, **kwargs):
        """Check callable state of items.

        Extends list.__init__
        """
        super().__init__(*args, **kwargs)
        if not all(map(callable, self)):
            raise ValueError("All items must be callable")

    def __call__(self):
        """Call all items."""
        for item in self:
            item()

    def append(self, item):
        """Append item if callable. Extends list.append."""
        if not callable(item):
            raise ValueError("All items must be callable")
        else:
            super().append(item)

    def insert(self, index, item):
        """Insert item if callable. Extends list.insert."""
        if not callable(item):
            raise ValueError("All items must be callable")
        else:
            super().insert(index, item)

    def extend(self, iterable):
        """Extend call list if all in iterable are callable.

        Overrides list.extend.
        """

        ## we cannot use the "all(map(callable..." check from the
        ## __init__ method here because this method also accept
        ## iterators, and in such case, this means "all(map(callable..."
        ## would consume the iterator, not leaving any items to be
        ## added in a posterior super().extend call;
        ##
        ## this means we need to check and append one by one
        ## instead

        super_append = super().append

        for item in iterable:

            if not callable(item):
                raise ValueError("All items must be callable")

            super_append(item)

class NestedPartial(partial):
    """A partial which retrieves return values from args.

    Instances of this class can be nested in a tree like
    structure. Useful to stack the execution of multiple
    functions when their return values serve as arguments
    for each other.

    >>> def get_value(value): return value

    >>> get_me  = partial(get_value,  'me')
    >>> get_you = partial(get_value, 'you')
    >>> get_we  = partial(get_value,  'we')

    >>> print_me = NestedPartial(
    ...            print, get_me, get_you, end=get_we)
    >>> print_me()
    me youwe

    Notice in the doctest above that since get_me and
    get_wehee functions are in the end of the 'tree-like'
    nesting, they don't need the extra functionality of
    a NestedPartial and can be partials or any other
    callable (as long as you don't need to provided extra
    arguments, in which case partials are required).
    """

    def __call__(self):
        """Return func return value after executing args."""
        ### retrieve positional arguments' return values if
        ### they are callable, otherwise just use themselves
        args = (arg() if callable(arg) else arg for arg in self.args)

        ### retrieve keyword arguments' return values if they
        ### are callable, otherwise just use themselves
        kwargs = {
            key: value() if callable(value) else value
            for key, value in self.keywords.items()
        }

        ### return the return value of self.func called
        ### with the resulting arguments
        return self.func(*args, **kwargs)


def do_nothing():
    """Do nothing. An empty function.

    Replaces 'lambda:None' solution.

    Some respected members in the pygame community don't
    recommend the usage of lambda functions for the sake
    of clarity. I'm still divided about it, but for such
    simple function declaration there's no cost at all
    to declare and keep it and when it is imported it has
    the advantage of communicating that some behaviour in
    the module has a 'switched off' state.

    Profiling have shown a very tiny and practically
    insignificant speed gain (less than fractions of
    microseconds) over the lambda solution, though not
    consistent through many tests.

    Try yourself on your command line:

    python -m timeit --setup "f = lambda:None" "f()"
    python -m timeit --setup "def f():pass"    "f()"

    Doctest of my life

    >>> do_nothing()
    >>>

    Disclaimer: for a function which does nothing, I know
    it has quite the docstring (including its doctest),
    but the discussion and design considerations are always
    important; you don't need to be as detailed as I am,
    but reviewing your design decisions and documenting them
    is a very constructive habit and helps to develop your
    analytical thinking.
    """


def get_nested_value(d, *strings):
    """Return inner value from nested dict.

    d (dict)
        Dictionary containing other nested dictionaries.
    strings (string arguments)
        Strings used to retrieve innermost item.

    >>> d = {
    ...   "john" : {
    ...     "id" : 22,
    ...     "school" : {
    ...       "id" : 1043,
    ...       "name" : "St. Lewis"
    ...     }
    ...   }
    ... }
    >>> get_nested_value(d, "john", "school", "id")
    1043

    ### curiosity

    A higher level version, could work with any nested
    objects with a __getitem__ method,
    and instead of strings could receive any arbitrary
    value, as long as it could be used by __getitem__ to
    retrieve the next one

    get_nested_value(obj, values):
        for item in values: obj = obj[item]
        return obj

    this would allows us to retrieve deep nested values
    within dicts, lists, tuples, etc.

    Maybe I should profile this with the higher level version
    to see if it is worth to use the more general approach
    of the higher level version.
    """
    return reduce(dict.__getitem__, strings, d)


### attribute utilities

## routine setting


def get_routine_caller(obj, routine_name, starting_value=do_nothing):
    """Return function which calls an specific routine.

    Also sets an initial value for the routine in the
    attribute.

    obj (any object which can have attributes set on it)
    routine_name (string)
        name of the attribute where to store the routine.
    starting_value (callable)
        any callable to be used as the starting value of the
        routine. If no value is passed, do_nothing()
        is called instead.

    >>> class Obj: pass
    ...
    >>> obj = Obj()
    >>> def a(): print("a")
    ...
    >>> def b(): print("b")
    ...
    >>> routine_caller = get_routine_caller(obj, "printer")
    >>> routine_caller()
    >>> obj.printer = a
    >>> routine_caller()
    a
    >>> obj.printer = b
    >>> routine_caller()
    b
    >>>

    """
    setattr(obj, routine_name, starting_value)

    return partial(methodcaller(routine_name), obj)


## toggling utilities


def get_attribute_rotator(obj, attr_name, values):
    """Return a function to rotate obj attribute values.

    Creates a partial from the provided arguments and the
    rotate_attribute function.

    obj (any object which can have attributes set on it)
        object whose attribute is used to hold the value.
    attr_name (string)
        name of the attribute where to store a value.
    values (iterable containing any python objects/values)
        values between which to toggle.

    Also sets the first value on the obj attribute.

    >>> values = [12, 32, 45, 26]
    >>> rotate = get_attribute_rotator
    """
    values_deque = deque(values)

    setattr(obj, attr_name, values_deque[0])

    return partial(rotate_attribute, obj, attr_name, values_deque)


def rotate_attribute(obj, attr_name, values_deque):
    """Rotate attribute value between those provided.

    This function is meant to be turned into partials
    by the get_attribute_rotator function for more efficient
    usage.

    Tip: passing a deque with two values creates a simple
    very useful toggle.

    obj (any object which can have attributes set on it)
        object whose attribute is used to hold the value.
    attr_name (string)
        name of the attribute where to store the value.
    values_deque (deque containing any python object/values)
        values between which to toggle.

    >>> class Obj: pass
    ...
    >>> obj = Obj()
    >>> d = deque(["a", "b", "c"])
    >>> rotate = partial(rotate_attribute, obj, "char", d)

    >>> rotate()
    >>> obj.char
    'b'
    >>> rotate()
    >>> obj.char
    'c'

    >>> obj.char = "b"
    >>> rotate()
    >>> obj.char
    'a'

    Notice in the last doctest section that even when we
    set the char attribute to "b" the next value of char
    after rotating is "a". This is because the assignement
    follows the rotation of the deque, without taking into
    consideration the current value.

    If you need a function that takes into account the
    current value before assigning a new one you should use
    the get attribute toggler function.
    """
    values_deque.rotate(-1)
    setattr(obj, attr_name, values_deque[0])


def get_attribute_toggler(
    obj, attr_name, starting_value, mapping_or_value, default=None
):
    """Return function to toggle obj atribute values.

    Creates a partial from the provided arguments using
    the toggle_attribute function.

    obj (any object which can have attributes set on it)
        object whose attribute is used to hold the value.
    attr_name (string)
        name of the attribute where to store a value.
    starting_value (any hashable obj/value),
        starting value to be assigned to the attribute.

    mapping_or_value (a dict or any hashable obj/value)
        The type of mapping_or_value may be different depending
        on two scenarios:

        1) If you have more than two values between which
           you desired to toggle though, you must then
           provide a mapping which associates the current
           value of the attribute with the desired value to
           be assigned when toggling.


        2) value to which we should toggle when executing
           the partial returned. Executing the partial
           returned again should set the previous value
           in the attribute again and so on.

        Either way the arguments are stored in a mapping
        so they fit the first scenario, thus complying with
        the underlying toggle_attribute function.

        The first scenario is just a simplification, since
        having two values to toggle would mean you want to
        toggle between them in this context. There's no
        absolute need to make each value reference each other,
        though. The work of the toggle is just to set a
        value for the attribute based on the current value
        stored there. If no value is found in the dict which
        is associated with the current value, the toggler
        (partial) will do nothing.
    default (any python value/object)
        Value to use only in case no key is found.

    >>> class Obj: pass
    ...
    >>> obj = Obj()
    >>> toggle_char = get_attribute_toggler(
    ...                   obj, 'char', 'a', 'b')
    >>> obj.char
    'a'
    >>> toggle_char()
    >>> obj.char
    'b'
    >>> obj.char = 'c'
    >>> toggle_char()
    >>> obj.char # without default it returns None
    >>>

    >>> obj.char = 'a'
    >>> toggle_char()
    >>> obj.char
    'b'
    >>> d = {1:5, 5:22, 22:13, 13:1}
    >>> toggle_number = get_attribute_toggler(
    ...                     obj, 'number', 22, d, 100)
    >>> obj.number
    22
    >>> toggle_number()
    >>> obj.number
    13
    >>> toggle_number()
    >>> obj.number
    1
    >>> obj.number = 342
    >>> toggle_number()
    >>> obj.number # 342 isn't a key, so returns default
    100

    """
    ### set the starting value of the attribute
    setattr(obj, attr_name, starting_value)

    ### now check the type of the arguments so you can
    ### create or reference the cross_mapped_values dict

    ## if mapping_or_value is a dict, reference it
    if isinstance(mapping_or_value, dict):
        cross_mapped_values = mapping_or_value

    ## otherwise, mapping_or_value is actually a value,
    ## so just use it to build a new dict
    else:
        another_value = mapping_or_value

        cross_mapped_values = {
            starting_value: another_value,
            another_value: starting_value,
        }

    ### return function
    return partial(toggle_attribute, obj, attr_name, cross_mapped_values, default)


def toggle_attribute(obj, attr_name, cross_mapped_values, default=None):
    """Toggle attribute between values a and b.

    This function is meant to be turned into partials
    by the get_attribute_toggler function for more efficient
    usage.

    It is slightly different from the toggler achievable with
    the get_attribute_rotator function because it checks the
    value of the attribute before toggling, so there is no
    intrinsic order. The value set depends solely on the
    current value.

    obj (any object which can have attributes set on it)
        object whose attribute is used to hold the value.
    attr_name (string)
        name of the attribute where to store the value.
    cross_mapped_values (dict)
        its keys reference each other. Such keys represent
        values from which and to which to toggle.
    default (any python value/object)
        Value to use only in case no key is found.

    >>> class Obj: pass
    ...
    >>> obj = Obj()
    >>> d = {"a":"b", "b":"a"}
    >>> toggler = partial(toggle_attribute, obj, "char", d)

    >>> obj.char = "a"
    >>> toggler()
    >>> obj.char
    'b'
    >>> toggler()
    >>> obj.char
    'a'
    """
    ### retrieve current attribute value to use as key
    key = getattr(obj, attr_name)

    ### retrieve value using key, also defining a default
    ### to be returned if needed
    value = cross_mapped_values.get(key, default)

    ### assign value to the attribute
    setattr(obj, attr_name, value)
