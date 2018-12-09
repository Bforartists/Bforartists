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

# <pep8-80 compliant>

import bpy
import gpu
import bgl
from mathutils import Vector, Matrix
from mathutils.geometry import tessellate_polygon
from gpu_extras.batch import batch_for_shader

def export(filepath, face_data, colors, width, height, opacity):
    offscreen = gpu.types.GPUOffScreen(width, height)
    offscreen.bind()

    try:
        bgl.glClear(bgl.GL_COLOR_BUFFER_BIT)
        draw_image(face_data, opacity)

        pixel_data = get_pixel_data_from_current_back_buffer(width, height)
        save_pixels(filepath, pixel_data, width, height)
    finally:
        offscreen.unbind()
        offscreen.free()

def draw_image(face_data, opacity):
    bgl.glLineWidth(1)
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glEnable(bgl.GL_LINE_SMOOTH)
    bgl.glHint(bgl.GL_LINE_SMOOTH_HINT, bgl.GL_NICEST)

    with gpu.matrix.push_pop():
        gpu.matrix.load_matrix(get_normalize_uvs_matrix())
        gpu.matrix.load_projection_matrix(Matrix.Identity(4))

        draw_background_colors(face_data, opacity)
        draw_lines(face_data)

    bgl.glDisable(bgl.GL_BLEND)
    bgl.glDisable(bgl.GL_LINE_SMOOTH)

def get_normalize_uvs_matrix():
    '''matrix maps x and y coordinates from [0, 1] to [-1, 1]'''
    matrix = Matrix.Identity(4)
    matrix.col[3][0] = -1
    matrix.col[3][1] = -1
    matrix[0][0] = 2
    matrix[1][1] = 2
    return matrix

def draw_background_colors(face_data, opacity):
    coords = [uv for uvs, _ in face_data for uv in uvs]
    colors = [(*color, opacity) for uvs, color in face_data for _ in range(len(uvs))]

    indices = []
    offset = 0
    for uvs, _ in face_data:
        triangles = tessellate_uvs(uvs)
        indices.extend([index + offset for index in triangle] for triangle in triangles)
        offset += len(uvs)

    shader = gpu.shader.from_builtin('2D_FLAT_COLOR')
    batch = batch_for_shader(shader, 'TRIS',
        {"pos" : coords,
         "color" : colors},
        indices=indices)
    batch.draw(shader)

def tessellate_uvs(uvs):
    return tessellate_polygon([[Vector(uv) for uv in uvs]])

def draw_lines(face_data):
    coords = []
    for uvs, _ in face_data:
        for i in range(len(uvs)):
            start = uvs[i]
            end = uvs[(i+1) % len(uvs)]
            coords.append((start[0], start[1]))
            coords.append((end[0], end[1]))

    shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'LINES', {"pos" : coords})
    shader.bind()
    shader.uniform_float("color", (0, 0, 0, 1))
    batch.draw(shader)

def get_pixel_data_from_current_back_buffer(width, height):
    buffer = bgl.Buffer(bgl.GL_BYTE, width * height * 4)
    bgl.glReadBuffer(bgl.GL_BACK)
    bgl.glReadPixels(0, 0, width, height, bgl.GL_RGBA, bgl.GL_UNSIGNED_BYTE, buffer)
    return buffer

def save_pixels(filepath, pixel_data, width, height):
    image = bpy.data.images.new("temp", width, height, alpha=True)
    image.filepath = filepath
    image.pixels = [v / 255 for v in pixel_data]
    image.save()
    bpy.data.images.remove(image)
