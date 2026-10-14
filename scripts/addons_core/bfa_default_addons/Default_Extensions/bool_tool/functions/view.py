import bpy
import mathutils
from mathutils import Vector
from bpy_extras import view3d_utils


#### ------------------------------ FUNCTIONS ------------------------------ ####

def redraw_regions(context):
    """Redraw regions to find the limits of the 3D viewport."""

    for area in context.window.screen.areas:
        if area.type != 'VIEW_3D':
            continue
        for region in area.regions:
            if region.type in {'WINDOW', 'UI'}:
                region.tag_redraw()


def distance_from_point_to_segment(point: Vector, line_p1: Vector, line_p2: Vector) -> float:
    """
    Calculates the shortest distance between the point and the finite segment.
    This is an alternative to `mathutils.geometry.intersect_point_line` (w/ clamping).
    Adapted from "Blockout" extension by niewinny (https://github.com/niewinny/blockout).
    """

    segment = line_p2 - line_p1
    start_to_point = point - line_p1

    # Projection along segment.
    c1 = start_to_point.dot(segment)
    if c1 <= 0:
        return (point - line_p1).length

    # Segment length squared.
    c2 = segment.dot(segment)
    if c2 <= c1:
        return (point - line_p2).length

    t = c1 / c2
    closest_point = line_p1 + t * segment
    distance = (point - closest_point).length

    return distance


def region_2d_to_ray_3d(region, rv3d, point_2d: Vector) -> tuple[Vector, Vector]:
    """
    Converts a 2D screen-space point into a 3D ray in the world-space.
    Returns a tuple of `ray_origin` and `ray_direction` Vectors.
    """

    origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, point_2d)
    direction = view3d_utils.region_2d_to_vector_3d(region, rv3d, point_2d)

    return origin, direction


def region_2d_to_plane_3d(region, rv3d, point_2d: Vector, plane: tuple[Vector]) -> Vector:
    """
    Converts a 2D screen-space point into a 3D point on a plane in world-space.
    Adapted from "Blockout" extension by niewinny (https://github.com/niewinny/blockout).
    """

    location, normal = plane
    p3_origin, p3_direction = region_2d_to_ray_3d(region, rv3d, point_2d)

    # Intersect the point with the plane.
    p3_on_plane = mathutils.geometry.intersect_line_plane(
        p3_origin,                  # First point of line.
        p3_origin + p3_direction,   # Second point of line.
        location,                   # `plane_co` (a point on the plane).
        normal)                     # `plane_no` (the direction the plane is facing).

    return p3_on_plane
