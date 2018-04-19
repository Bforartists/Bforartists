import bpy
import math
from mathutils import Vector

from ..utils.selection import get_visible_strips

from ..utils.geometry import rotate_point
from ..utils.geometry import get_transform_box
from ..utils.geometry import get_strip_box
from ..utils.geometry import get_strip_corners


def get_important_edge_points():
    """
    Get the edge locations for where a user may want to snap the cursor
    to.

    This is the top left, top middle, top right, right middle, bottom
    right, bottom middle, bottom left, left middle, and center points of
    all visible strips in the preview window.::

        x------x------x
        |             |
        x      x      x
        |             |
        x------x------x

    Returns
    -------
    list of mathutils.Vector
    """
    scene = bpy.context.scene

    strips = get_visible_strips()

    res_x = scene.render.resolution_x
    res_y = scene.render.resolution_y

    bl = Vector([0, 0])
    l = Vector([0, res_y / 2])
    tl = Vector([0, res_y])
    t = Vector([res_x / 2, res_y])
    tr = Vector([res_x, res_y])
    r = Vector([res_x, res_y / 2])
    br = Vector([res_x, 0])
    b = Vector([res_x / 2, 0])
    origin = Vector([res_x / 2, res_y / 2])

    vectors = [bl, l, tl, t, tr, r, br, b, origin]

    for vec in vectors:
        vec.x -= (res_x / 2)
        vec.y -= (res_y / 2)


    important_edge_points = vectors
    for strip in strips:
        if strip.type == "TRANSFORM":
            left, right, bottom, top = get_transform_box(strip)

        else:
            left, right, bottom, top = get_strip_box(strip)

        mid_x = left+ ((right - left) / 2)
        mid_y = bottom + ((top - bottom) / 2)

        l = Vector([left, mid_y])
        r = Vector([right, mid_y])
        t = Vector([mid_x, top])
        b = Vector([mid_x, bottom])

        origin = Vector([mid_x, mid_y])

        if strip.type == "TRANSFORM":
            angle = math.radians(strip.rotation_start)

            l = rotate_point(l, angle, origin=origin)
            r = rotate_point(r, angle, origin=origin)
            t = rotate_point(t, angle, origin=origin)
            b = rotate_point(b, angle, origin=origin)

        bl, tl, tr, br = get_strip_corners(strip)

        vectors = [bl, l, tl, t, tr, r, br, b, origin]

        for vec in vectors:
            vec.x -= (res_x / 2)
            vec.y -= (res_y / 2)

        important_edge_points.extend(vectors)

    return important_edge_points
