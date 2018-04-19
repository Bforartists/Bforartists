import math
from mathutils import Vector


def rotate_point(point, angle, origin=Vector([0, 0])):
    """
    Rotate a point around an origin and return it's new position

    Args
        :point: The point that will be rotated (mathutils.Vector)
    Returns
        :rotated_vector: A point that has been rotated about an origin
                         (mathutils.Vector)
    """

    pos = point - origin

    sin = math.sin(angle)
    cos = math.cos(angle)

    pos_x = (pos.x * cos) - (pos.y * sin)
    pos_y = (pos.x * sin) + (pos.y * cos)

    rotated_vector = origin + Vector([pos_x, pos_y])

    return rotated_vector
