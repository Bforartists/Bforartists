import bpy
from operator import attrgetter
import math

from .get_transform_box import get_transform_box
from .get_strip_box import get_strip_box
from .get_post_rot_bbox import get_post_rot_bbox
from .get_strip_corners import get_strip_corners


def reposition_transform_strip(strip, group_box):
    """
    Reposition a transform strip.

    After adjusting scene resolution, strip sizes will be
    discombobulated. This function will reset a strip's size and
    position to how it was relative to the group box prior to the
    resolution change.

    Args
        :strip:     A transform strip (bpy.types.Sequence)
        :group_box: The group bounding box prior to the scene resolution
                    change. (list of int: ie [left, right, bottom, top])
    """
    scene = bpy.context.scene

    min_left, max_right, min_bottom, max_top = group_box

    total_width = max_right - min_left
    total_height = max_top - min_bottom

    res_x = scene.render.resolution_x
    res_y = scene.render.resolution_y

    min_left, max_right, min_bottom, max_top = group_box

    left, right, bottom, top = get_transform_box(strip)

    width = right - left
    height = top - bottom

    rot = math.radians(strip.rotation_start)

    bl, tl, tr, br = get_strip_corners(strip)
    vectors = [bl, tl, tr, br]
    b_left = min(vectors, key=attrgetter('x')).x
    b_right = max(vectors, key=attrgetter('x')).x

    b_bottom = min(vectors, key=attrgetter('y')).y
    b_top = max(vectors, key=attrgetter('y')).y

    primary_offset_x = b_left - min_left
    primary_offset_y = b_bottom - min_bottom

    b_width = b_right - b_left
    b_height = b_top - b_bottom

    scale_ratio_x = total_width / res_x
    scale_ratio_y = total_height / res_y

    current_width = width * scale_ratio_x
    current_height = height * scale_ratio_y

    current_left = left * scale_ratio_x
    current_bottom = bottom * scale_ratio_y

    current_right = current_left + current_width
    current_top = current_bottom + current_height

    box = get_post_rot_bbox(
        current_left, current_right, current_bottom, current_top, rot)
    current_b_left = box[0]
    current_b_right = box[1]
    current_b_bottom = box[2]
    current_b_top = box[3]

    current_b_width = current_b_right - current_b_left
    current_b_height = current_b_top - current_b_bottom

    collapse_offset_x = -current_b_left
    collapse_offset_y = -current_b_bottom

    scale_offset_x = (b_width - current_b_width) / 2
    scale_offset_y = (b_height - current_b_height) / 2

    offset_x, null, offset_y, null = get_strip_box(strip)

    if strip.use_translation:
        strip.transform.offset_x = 0
        strip.transform.offset_y = 0

    if strip.translation_unit == 'PERCENT':
        primary_offset_x = (primary_offset_x / total_width) * 100
        primary_offset_y = (primary_offset_y / total_height) * 100

        collapse_offset_x = (collapse_offset_x / total_width) * 100
        collapse_offset_y = (collapse_offset_y / total_height) * 100

        scale_offset_x = (scale_offset_x / total_width) * 100
        scale_offset_y = (scale_offset_y / total_height) * 100

        offset_x = (offset_x / res_x) * 100
        offset_y = (offset_y / res_y) * 100

    combo_offset_x = sum([primary_offset_x, collapse_offset_x,
                          scale_offset_x, offset_x])
    combo_offset_y = sum([primary_offset_y, collapse_offset_y,
                          scale_offset_y, offset_y])

    strip.translate_start_x += combo_offset_x
    strip.translate_start_y += combo_offset_y

    strip.scale_start_x = strip.scale_start_x / scale_ratio_x
    strip.scale_start_y = strip.scale_start_y / scale_ratio_y
