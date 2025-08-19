"""Facility for 2d point creation."""

### standard library imports
from math import pi, sin, cos


def yield_circle_points(quantity, radius, center=(0, 0)):
    """Yield points forming a circle of given radius around given center."""
    xc, yc = center

    for k in range(quantity):

        value = (k * 2 * pi) / quantity

        x = radius * cos(value)
        y = radius * sin(value)

        yield (x + xc, y + yc)
