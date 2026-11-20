"""Bone frames for mechanism parts (pure; tuples, no mathutils).

A frame is (y, z): y is the bone direction (head -> tail) and z is the vector
build.py hands to ``EditBone.align_roll``. The bone's X axis is y × z.
"""
import math


class GeometryError(ValueError):
    """A zero-length axis or coincident points."""


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def scale(v, s):
    return tuple(x * s for x in v)


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def length(v):
    return math.sqrt(dot(v, v))


def normalize(v):
    n = length(v)
    if n < 1e-9:
        raise GeometryError("zero-length direction %r" % (tuple(v),))
    return tuple(x / n for x in v)


def _perp(v, ref):
    return normalize(sub(ref, scale(v, dot(ref, v))))


def frame_for_hinge(axis):
    """Bone X = the hinge axis, so the hinge turns on local X rotation."""
    x = normalize(axis)
    ref = (0.0, 0.0, 1.0) if abs(x[2]) < 0.9 else (0.0, 1.0, 0.0)
    y = _perp(x, ref)
    return y, cross(x, y)


def frame_for_slide(axis):
    """Bone Y = the slide axis, so the part slides on local Y location."""
    y = normalize(axis)
    ref = (0.0, 0.0, 1.0) if abs(y[2]) < 0.9 else (1.0, 0.0, 0.0)
    return y, _perp(y, ref)


def frame_toward(head, target):
    return frame_for_slide(sub(target, head))


def tail(head, y, size):
    return add(tuple(head), scale(y, size))
