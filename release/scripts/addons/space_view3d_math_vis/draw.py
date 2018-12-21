# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

import bpy
import blf
import gpu
from gpu_extras.batch import batch_for_shader

from . import utils
from mathutils import Vector

SpaceView3D = bpy.types.SpaceView3D
callback_handle = []

single_color_shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
smooth_color_shader = gpu.shader.from_builtin('3D_SMOOTH_COLOR')

def tag_redraw_areas():
    context = bpy.context

    # Py cant access notifers
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
    blf.size(font_id, 12, 72)

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
        loc = context.scene.cursor_location.copy()
        for key, mat in data_quat.items():
            draw_text(key, loc, dy=-offset_y)
            offset_y += 20

    if data_euler:
        loc = context.scene.cursor_location.copy()
        for key, mat in data_euler.items():
            draw_text(key, loc, dy=-offset_y)
            offset_y += 20

def draw_callback_view():
    settings = bpy.context.window_manager.MathVisProp
    scale = settings.bbox_scale
    with_bounding_box = not settings.bbox_hide

    data_matrix, data_quat, data_euler, data_vector, data_vector_array = utils.console_math_data()

    if data_vector:
        coords = [tuple(vec.to_3d()) for vec in data_vector.values()]
        draw_points(coords)

    if data_vector_array:
        for line in data_vector_array.values():
            coords = [tuple(vec.to_3d()) for vec in line]
            draw_line(coords)

    if data_matrix:
        draw_matrices(list(data_matrix.values()), scale, with_bounding_box)

    if data_euler or data_quat:
        cursor = bpy.context.scene.cursor_location.copy()
        derived_matrices = []
        for quat in data_quat.values():
            matrix = quat.to_matrix().to_4x4()
            matrix.translation = cursor
            derived_matrices.append(matrix)
        for eul in data_euler.values():
            matrix = eul.to_matrix().to_4x4()
            matrix.translation = cursor
            derived_matrices.append(matrix)
        draw_matrices(derived_matrices, scale, with_bounding_box)


def draw_points(points):
    batch = batch_from_points(points, "POINTS")
    single_color_shader.bind()
    single_color_shader.uniform_float("color", (0.5, 0.5, 1, 1))
    batch.draw(single_color_shader)

def draw_line(points):
    batch = batch_from_points(points, "LINE_STRIP")
    single_color_shader.bind()
    single_color_shader.uniform_float("color", (0.5, 0.5, 1, 1))
    batch.draw(single_color_shader)

def batch_from_points(points, type):
    return batch_for_shader(single_color_shader, type, {"pos" : points})

def draw_matrices(matrices, scale, with_bounding_box):
    x_p = Vector(( scale,   0.0,   0.0))
    x_n = Vector((-scale,   0.0,   0.0))
    y_p = Vector((0.0,    scale,   0.0))
    y_n = Vector((0.0,   -scale,   0.0))
    z_p = Vector((0.0,      0.0,  scale))
    z_n = Vector((0.0,      0.0, -scale))

    red_dark =    (0.2, 0.0, 0.0, 1.0)
    red_light =   (1.0, 0.2, 0.2, 1.0)
    green_dark =  (0.0, 0.2, 0.0, 1.0)
    green_light = (0.2, 1.0, 0.2, 1.0)
    blue_dark =   (0.0, 0.0, 0.2, 1.0)
    blue_light =  (0.4, 0.4, 1.0, 1.0)

    coords = []
    colors = []
    for matrix in matrices:
        coords.append(matrix @ x_n)
        coords.append(matrix @ x_p)
        colors.extend((red_dark, red_light))
        coords.append(matrix @ y_n)
        coords.append(matrix @ y_p)
        colors.extend((green_dark, green_light))
        coords.append(matrix @ z_n)
        coords.append(matrix @ z_p)
        colors.extend((blue_dark, blue_light))

    batch = batch_for_shader(smooth_color_shader, "LINES", {
        "pos" : coords,
        "color" : colors
    })
    batch.draw(smooth_color_shader)

    if with_bounding_box:
        draw_bounding_boxes(matrices, scale, (1.0, 1.0, 1.0, 1.0))

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