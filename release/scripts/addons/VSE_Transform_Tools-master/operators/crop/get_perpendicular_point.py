from mathutils import Vector
from mathutils.geometry import intersect_point_quad_2d
from mathutils.geometry import intersect_line_line_2d


def get_perpendicular_point(pt, bl, tl, tr, br):
    '''
    Return the point if it is inside the quad, else, return
    a point on the border of the quad.

    This function helps prevent the user from dragging crop handles
    outside the strip's area.
    '''

    intersects = intersect_point_quad_2d(
        pt, bl, tl, tr, br)

    if intersects:
        return pt

    elif pt.x <= bl.x and pt.y <= bl.y:
        return Vector(bl)
    elif pt.x <= tl.x and pt.y >= tl.y:
        return Vector(tl)
    elif pt.x >= tr.x and pt.y >= tr.y:
        return Vector(tr)
    elif pt.x >= br.x and pt.y <= br.y:
        return Vector(br)

    max_x = max([tr.x, br.x])
    min_x = min([tl.x, bl.x])

    max_y = max([tl.y, tr.y])
    min_y = min([bl.y, br.y])

    # pt left of left side
    if (pt.x <= tl.x or pt.x <= bl.x) and (pt.y >= bl.y and pt.y <= tl.y):
        right = Vector([max_x, pt.y])
        intersection = intersect_line_line_2d(bl, tl, pt, right)

    # pt right of right side
    elif (pt.x >= br.x or pt.x >= tr.x) and (pt.y >= br.y and pt.y <= tr.y):
        left = Vector([min_x, pt.y])
        intersection = intersect_line_line_2d(br, tr, pt, left)

    # pt above top side
    elif (pt.y >= tl.y or pt.y >= tr.y) and (pt.x >= tl.x and pt.x <= tr.x):
        bottom = Vector([pt.x, min_y])
        intersection = intersect_line_line_2d(tl, tr, pt, bottom)

    # pt below bottom side
    elif (pt.y <= bl.y or pt.y <= br.y) and (pt.x >= bl.x and pt.x <= br.x):
        top = Vector([pt.x, max_y])
        intersection = intersect_line_line_2d(bl, br, pt, top)

    return intersection
