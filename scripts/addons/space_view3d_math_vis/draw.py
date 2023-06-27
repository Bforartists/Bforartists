# SPDX-FileCopyrightText: 2010-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
import blf
import gpu
from gpu_extras.batch import batch_for_shader

from . import utils
from mathutils import Vector

SpaceView3D = bpy.types.SpaceView3D
callback_handle = []

if not bpy.app.background:
    single_color_shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    smooth_color_shader = gpu.shader.from_builtin('SMOOTH_COLOR')
else:
    single_color_shader = None
    smooth_color_shader = None

COLOR_POINT = (1.0, 0.0, 1.0, 1)
COLOR_LINE = (0.5, 0.5, 1, 1)
COLOR_LINE_ACTIVE = (1.0, 1.0, 0.5, 1)
COLOR_BOUNDING_BOX = (1.0, 1.0, 1.0, 1.0)
COLOR_BOUNDING_BOX_ACTIVE = (1.0, 0.5, 0.0, 1.0)


def tag_redraw_areas():
    context = bpy.context

    # Py can't access notifers
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type in ['VIEW_3D', 'PROPERTIES']:
                area.tag_redraw()


def callback_enable():
    if callback_handle:
        return

    handle_pixel = SpaceView3D.draw_handler_add(draw_callback_px, (), 'WINDOW', 'POST_PIXEL')
    handle_view = SpaceView3D.draw_handler_add(draw_callback_view, (), 'WINDOW', 'POST_VIEW')
    callback_handle[:] = handle_pixel, handle_view

    tag_redraw_areas()


def callback_disable():
    if not callback_handle:
        return

    handle_pixel, handle_view = callback_handle
    SpaceView3D.draw_handler_remove(handle_pixel, 'WINDOW')
    SpaceView3D.draw_handler_remove(handle_view, 'WINDOW')
    callback_handle[:] = []

    tag_redraw_areas()


def draw_callback_px():
    context = bpy.context

    if context.window_manager.MathVisProp.name_hide:
        return

    font_id = 0
    ui_scale = context.preferences.system.ui_scale
    blf.size(font_id, round(12 * ui_scale))

    data_matrix, data_quat, data_euler, data_vector, data_vector_array = utils.console_math_data()
    if not data_matrix and not data_quat and not data_euler and not data_vector and not data_vector_array:
        return

    region = context.region
    region3d = context.space_data.region_3d

    region_mid_width = region.width / 2.0
    region_mid_height = region.height / 2.0

    perspective_matrix = region3d.perspective_matrix.copy()

    def draw_text(text, vec, dx=3.0, dy=-4.0):
        vec_4d = perspective_matrix @ vec.to_4d()
        if vec_4d.w > 0.0:
            x = region_mid_width + region_mid_width * (vec_4d.x / vec_4d.w)
            y = region_mid_height + region_mid_height * (vec_4d.y / vec_4d.w)

            blf.position(font_id, x + dx, y + dy, 0.0)
            blf.draw(font_id, text)

    if data_vector:
        for key, vec in data_vector.items():
            draw_text(key, vec)

    if data_vector_array:
        for key, vec in data_vector_array.items():
            if vec:
                draw_text(key, vec[0])

    if data_matrix:
        for key, mat in data_matrix.items():
            loc = Vector((mat[0][3], mat[1][3], mat[2][3]))
            draw_text(key, loc, dx=10, dy=-20)

    offset_y = 20
    if data_quat:
        loc = context.scene.cursor.location.copy()
        for key, mat in data_quat.items():
            draw_text(key, loc, dy=-offset_y)
            offset_y += 20

    if data_euler:
        loc = context.scene.cursor.location.copy()
        for key, mat in data_euler.items():
            draw_text(key, loc, dy=-offset_y)
            offset_y += 20


def draw_callback_view():
    settings = bpy.context.window_manager.MathVisProp
    prop_states = bpy.context.window_manager.MathVisStatePropList

    scale = settings.bbox_scale
    with_bounding_box = not settings.bbox_hide

    if settings.in_front:
        gpu.state.depth_test_set('ALWAYS')
    else:
        gpu.state.depth_test_set('LESS')

    data_matrix, data_quat, data_euler, data_vector, data_vector_array = utils.console_math_data()
    if settings.index in range(0,len(prop_states)):
        active_index = settings.index
        active_key = prop_states[active_index].name
    else:
        active_index = -1
        active_key = None

    if data_vector:
        coords = [tuple(vec.to_3d()) for vec in data_vector.values()]
        draw_points(coords)

    if data_vector_array:
        for key, line in data_vector_array.items():
            coords = [tuple(vec.to_3d()) for vec in line]
            if key == active_key:
                draw_line(coords,  COLOR_LINE_ACTIVE)
            else:
                draw_line(coords,  COLOR_LINE)

    if data_matrix:
        draw_matrices(data_matrix, scale, with_bounding_box, active_key)

    if data_euler or data_quat:
        cursor = bpy.context.scene.cursor.location.copy()
        derived_matrices = []
        for key, quat in data_quat.values():
            matrix = quat.to_matrix().to_4x4()
            matrix.translation = cursor
            derived_matrices[key] = matrix
        for key, eul in data_euler.values():
            matrix = eul.to_matrix().to_4x4()
            matrix.translation = cursor
            derived_matrices[key] = matrix
        draw_matrices(derived_matrices, scale, with_bounding_box, active_key)


def draw_points(points):
    batch = batch_from_points(points, "POINTS")
    single_color_shader.bind()
    single_color_shader.uniform_float("color", COLOR_POINT)
    batch.draw(single_color_shader)


def draw_line(points, color):
    batch = batch_from_points(points, "LINE_STRIP")
    single_color_shader.bind()
    single_color_shader.uniform_float("color", color)
    batch.draw(single_color_shader)


def batch_from_points(points, type):
    return batch_for_shader(single_color_shader, type, {"pos": points})


def draw_matrices(matrices, scale, with_bounding_box, active_key):
    x_p = Vector((scale, 0.0, 0.0))
    x_n = Vector((-scale, 0.0, 0.0))
    y_p = Vector((0.0, scale, 0.0))
    y_n = Vector((0.0, -scale, 0.0))
    z_p = Vector((0.0, 0.0, scale))
    z_n = Vector((0.0, 0.0, -scale))

    red_dark = (0.2, 0.0, 0.0, 1.0)
    red_light = (1.0, 0.2, 0.2, 1.0)
    green_dark = (0.0, 0.2, 0.0, 1.0)
    green_light = (0.2, 1.0, 0.2, 1.0)
    blue_dark = (0.0, 0.0, 0.2, 1.0)
    blue_light = (0.4, 0.4, 1.0, 1.0)

    coords = []
    colors = []
    selected = []
    active = []
    for key, matrix in matrices.items():
        coords.append(matrix @ x_n)
        coords.append(matrix @ x_p)
        colors.extend((red_dark, red_light))
        coords.append(matrix @ y_n)
        coords.append(matrix @ y_p)
        colors.extend((green_dark, green_light))
        coords.append(matrix @ z_n)
        coords.append(matrix @ z_p)
        colors.extend((blue_dark, blue_light))
        if key == active_key:
            active.append(matrix)
        else:
            selected.append(matrix)

    batch = batch_for_shader(smooth_color_shader, "LINES", {
        "pos": coords,
        "color": colors
    })
    batch.draw(smooth_color_shader)

    if with_bounding_box:
        if selected:
            draw_bounding_boxes(selected, scale, COLOR_BOUNDING_BOX)
        if active:
            draw_bounding_boxes(active, scale, COLOR_BOUNDING_BOX_ACTIVE)


def draw_bounding_boxes(matrices, scale, color):
    boundbox_points = []
    for x in (-scale, scale):
        for y in (-scale, scale):
            for z in (-scale, scale):
                boundbox_points.append(Vector((x, y, z)))

    boundbox_lines = [
        (0, 1), (1, 3), (3, 2), (2, 0), (0, 4), (4, 5),
        (5, 7), (7, 6), (6, 4), (1, 5), (2, 6), (3, 7)
    ]

    points = []
    for matrix in matrices:
        for v1, v2 in boundbox_lines:
            points.append(matrix @ boundbox_points[v1])
            points.append(matrix @ boundbox_points[v2])

    batch = batch_from_points(points, "LINES")

    single_color_shader.bind()
    single_color_shader.uniform_float("color", color)
    batch.draw(single_color_shader)
