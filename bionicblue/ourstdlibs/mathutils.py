"""Facility for general mathematic utilities."""

from math import hypot


# XXX
# use the divmod approach here;
# also, maybe having the order of
# parameters reversed would be more intuitive?
def get_reaching_multiple(step_length, total_distance):
    """Return first multiple to reach or surpass distance.

    step_length
        An int describing the length of the step.
    total_distance
        An int describing the total distance to cover.

    This functions is very useful for simple scrolling
    features and was first implemented on the load game
    menu (in the main menu).

    >>> get_reaching_multiple(2, 11)
    12
    >>> get_reaching_multiple(10, 101)
    110
    >>> get_reaching_multiple(10, 100)
    100
    >>> get_reaching_multiple(10, 10)
    10
    >>> get_reaching_multiple(10, 9)
    10
    """
    if step_length >= total_distance:
        return step_length
    else:
        steps_no = total_distance // step_length
        rest = total_distance % step_length
        if rest:
            return step_length * (steps_no + 1)
        else:
            return step_length * steps_no


def unscroll_coordinates(coordinates):
    """Return unscrolled coordinates.

    The unscrolled coordinates are the coordinates a point
    in the game world would have if it were scrolled to the
    current screen keeping the same distance from the edges
    of the screen. That is, in the diagram below, it would
    be the coordinates of A if it were scrolled back to
    the current screen (as if it were the point B, a point
    which has the same distance of the edges of the screen
    that point A has)).

    current screen (player sees this region)
        |
        |             another neighbouring screen
        |             |   (player can't see this region)
        |             |
        v             v
    __________________________
    |            |            |
    |   . B      |   . A      |
    |            |            |
    |            |            |
    |____________|____________|

    unscroll_coordinates(coordinates) -> point

    coordinates
        Just a point consisting of a list or tuple with
        two integer coordinates.
    """
    abs_x, abs_y = coordinates

    rest_x = abs_x % SCREEN_WIDTH
    rest_y = abs_y % SCREEN_HEIGHT

    unscrolled_coordinates = (rest_x, rest_y)

    return unscrolled_coordinates


def get_straight_distance(point_a, point_b):
    """Calculate the straight distance between two points.

    get_straight_distance(point_a, point_b) -> float

    point_a, point_b
        Each is represented by a list or tuple with two
        values: x and y respectively. For instance: (x, y).

    Illustration:
                 ._ _
        (point a)|\   |
                 | \s |
              dy |  \ |
                 |   \|
                 |_ _ .(point b)
                   dx

        where:
        s  = the straight distance  (straight_distance)
        dy = the distance on y axis (distance_x)
        dx = the distance on x axis (distance_y)

    >>> a, b = (10, 10), (20, 20)
    >>> round(get_straight_distance(a, b), 2)
    14.14
    """
    x_a, y_a = point_a
    x_b, y_b = point_b

    distance_x = x_b - x_a
    distance_y = y_b - y_a

    straight_distance = hypot(distance_x, distance_y)

    return straight_distance


# XXX
# Both offset_point and invert_point functions
# could be further abstracted in a Point or Vector2d class.
# I've already faced some situations where such
# associations were quite intuitive, so I just maybe
# I could see into it in the near future.
# If so, and only if, probably the existing
# pygame.math.Vector2d class
def offset_point(point, offset):
    """Return offset point (an int tuple of length 2).

    offset_point(point, offset) -> point

    point
        A list or tuple containing two integers representing
        a point's coordinates in space.
    offset
        A list or tuple containing two integers representing
        amounts to be added to each point coordinate.

    >>> offset_point((10, 10), (5, 5))
    (15, 15)
    >>> offset_point((10, 10), (-5, 5))
    (5, 15)
    >>> offset_point((10, 10), (5, -5))
    (15, 5)
    >>> offset_point((10, 10), (-5, -5))
    (5, 5)
    """
    x, y = point
    x_offset, y_offset = offset

    offset_point = [x + x_offset, y + y_offset]

    return offset_point


def invert_point(point, invert_x, invert_y):
    """Return point with inverted coordinates as requested.

    Inverting a coordinates means changing the signal.

    point
        A list or tuple with two integers representing
        x and y coordinates of a point.
    invert_x
    invert_y
        Booleans indicating whether the x and y coordinates
        should be inverted, respectively.

    >>> invert_point((10, 10), True, True)
    (-10, -10)
    >>> invert_point((10, 10), True, False)
    (-10, 10)
    >>> invert_point((10, 10), False, True)
    (10, -10)
    >>> invert_point((10, 10), False, False)
    (10, 10)
    """
    x, y = point
    new_x = -x if invert_x else x
    new_y = -y if invert_y else y
    inverted_point = (new_x, new_y)

    return inverted_point

def get_rect_from_points(point_a, point_b):
    """Return rect-like tuple from given points.

    Each of the four elements of the tuple is an integer
    representing, respectively, the left coordinate, the
    top coordinate, the width and the height.
    """
    ### get tuples gathering x's and y's from both points
    xs, ys = zip(point_a, point_b)

    ### calculate left and right, then width

    left, right = (func(xs) for func in (min, max))

    width = right - left

    ### calculate top and bottom, then height

    top, bottom = (func(ys) for func in (min, max))

    height = bottom - top

    ### finally return the tuple
    return (left, top, width, height)
