import bpy
import os

from .get_pos_x import get_pos_x
from .get_pos_y import get_pos_y
from .get_strip_box import get_strip_box
from .get_res_factor import get_res_factor


def get_transform_box(strip):
    """
    Gets the unrotated left, right, top, bottom of a transform strip

    Args
        :strip: A transform strip (bpy.types.Sequence) Returns
        :box:   The left, right, top, bottom of a transform strip (list
                of int)
    """
    scene = bpy.context.scene

    left, right, bottom, top = get_strip_box(strip.input_1)

    res_x = scene.render.resolution_x
    res_y = scene.render.resolution_y

    strip_in = strip.input_1
    if strip_in.use_translation:
        left = 0
        right = res_x
        bottom = 0
        top = res_y

    width = right - left
    height = top - bottom

    t_pos_x = get_pos_x(strip)
    t_pos_y = get_pos_y(strip)

    world_left = left + t_pos_x
    world_right = right + t_pos_x
    world_bottom = bottom + t_pos_y
    world_top = top + t_pos_y

    origin_x = world_left + (width / 2)
    origin_y = world_bottom + (height / 2)

    scl_x = strip.scale_start_x
    scl_y = strip.scale_start_y
    if strip.use_uniform_scale:
        scl_x = scl_y = max([scl_x, scl_y])

    scaled_left = (world_left - origin_x) * scl_x
    scaled_bottom = (world_bottom - origin_y) * scl_y

    diff_x = scaled_left - (world_left - origin_x)
    diff_y = scaled_bottom - (world_bottom - origin_y)

    left = world_left + diff_x
    right = left + (width * scl_x)
    bottom = world_bottom + diff_y
    top = bottom + (height * scl_y)

    width = right - left
    height = top - bottom

    if right - left <= 0 or top - bottom <= 0:
        left = right = bottom = top = 0

    box = [left, right, bottom, top]

    return box
