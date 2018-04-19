import bpy
import math
from operator import attrgetter

from .get_strip_box import get_strip_box
from .get_transform_box import get_transform_box
from .get_strip_corners import get_strip_corners


def get_group_box(strips):
    """
    Get the bounding box of a group of strips

    Parameters
    ----------
    strips: list of bpy.types.Sequence

    Returns
    -------
    box: list of int
        The bounding box of all the strips ie: left, right, bottom, top
    """
    scene = bpy.context.scene
    boxes = []

    nontransforms = []
    for i in range(len(strips)):
        if strips[i].type != "TRANSFORM" and strips[i].type != "SOUND":
            nontransforms.append(strips[i])

    for strip in nontransforms:
        boxes.append(get_strip_box(strip))

    transforms = []
    for i in range(len(strips)):
        if strips[i].type == "TRANSFORM":
            transforms.append(strips[i])

    for strip in transforms:
        bl, tl, tr, br = get_strip_corners(strip)
        vectors = [bl, tl, tr, br]

        left = min(vectors, key=attrgetter('x')).x
        right = max(vectors, key=attrgetter('x')).x

        bottom = min(vectors, key=attrgetter('y')).y
        top = max(vectors, key=attrgetter('y')).y

        boxes.append([left, right, bottom, top])

    res_x = scene.render.resolution_x
    res_y = scene.render.resolution_y

    min_left = res_x
    max_right = 0
    min_bottom = res_y
    max_top = 0

    for box in boxes:
        if box[0] < min_left:
            min_left = box[0]
        if box[1] > max_right:
            max_right = box[1]
        if box[2] < min_bottom:
            min_bottom = box[2]
        if box[3] > max_top:
            max_top = box[3]

    return [min_left, max_right, min_bottom, max_top]
