# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Drawing utilities. A list of functions to draw common elements"""
# import bgl
import blf
from gpu_extras.batch import batch_for_shader
from mathutils import Vector
import math


def get_color_gizmo_primary(context):
    color = context.preferences.themes[0].user_interface.gizmo_primary
    return _color_to_list(color)


def get_color_gizmo_secondary(context):
    color = context.preferences.themes[0].user_interface.gizmo_secondary
    return _color_to_list(color)


def get_color_axis_x(context):
    color = context.preferences.themes[0].user_interface.axis_x
    return _color_to_list(color)


def get_color_axis_y(context):
    color = context.preferences.themes[0].user_interface.axis_y
    return _color_to_list(color)


def get_color_axis_z(context):
    color = context.preferences.themes[0].user_interface.axis_z
    return _color_to_list(color)


def draw_line(shader, start, end, color=(1.0, 1.0, 1.0, 1.0)):
    """Draws a line using two Vector-based points"""
    batch = batch_for_shader(shader, "LINES", {"pos": (start, end)})

    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)


def draw_rectangle(shader, origin, size, color=(1.0, 1.0, 1.0, 1.0)):
    vertices = (
        (origin.x, origin.y),
        (origin.x + size.x, origin.y),
        (origin.x, origin.y + size.y),
        (origin.x + size.x, origin.y + size.y),
    )
    indices = ((0, 1, 2), (2, 1, 3))
    batch = batch_for_shader(shader, "TRIS", {"pos": vertices}, indices=indices)
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)


def draw_triangle(shader, point_1, point_2, point_3, color=(1.0, 1.0, 1.0, 1.0)):
    vertices = (point_1, point_2, point_3)
    indices = ((0, 1, 2),)
    batch = batch_for_shader(shader, "TRIS", {"pos": vertices}, indices=indices)
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)


def draw_triangle_equilateral(shader, center, radius, rotation=0.0, color=(1.0, 1.0, 1.0, 1.0)):
    points = []
    for i in range(3):
        angle = i * math.pi * 2 / 3 + rotation
        offset = Vector((radius * math.cos(angle), radius * math.sin(angle)))
        points.append(center + offset)
    draw_triangle(shader, *points, color)


def draw_text(x, y, size, text, justify="left", color=(1.0, 1.0, 1.0, 1.0)):
    font_id = 0
    blf.color(font_id, *color)
    if justify == "right":
        text_width, text_height = blf.dimensions(font_id, text)
    else:
        text_width = 0
    blf.position(font_id, x - text_width, y, 0)
    blf.size(font_id, size)
    blf.draw(font_id, text)


def draw_arrow_head(shader, center, size, points_right=True, color=(1.0, 1.0, 1.0, 1.0)):
    """
    Draws a triangular arrow using two Vectors:
    - the triangle's center
    - the triangle's size
    """
    direction = 1 if points_right else -1

    point_upper = Vector([center.x - size.x / 2 * direction, center.y + size.y / 2])
    point_tip = Vector([center.x + size.x / 2 * direction, center.y])
    point_lower = Vector([center.x - size.x / 2 * direction, center.y - size.y / 2])

    draw_line(shader, point_upper, point_tip, color)
    draw_line(shader, point_tip, point_lower, color)


def _color_to_list(color):
    """Converts a Blender Color to a list of 4 color values to use with shaders and drawing"""
    return list(color) + [1.0]
