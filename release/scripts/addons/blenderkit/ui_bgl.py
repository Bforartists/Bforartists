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

import bgl, blf

import bpy, blf
import gpu
from gpu_extras.batch import batch_for_shader


def draw_rect(x, y, width, height, color):
    xmax = x + width
    ymax = y + height
    points = [[x, y],  # [x, y]
              [x, ymax],  # [x, y]
              [xmax, ymax],  # [x, y]
              [xmax, y],  # [x, y]
              ]
    indices = ((0, 1, 2), (2, 3, 0))

    shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'TRIS', {"pos": points}, indices=indices)

    shader.bind()
    shader.uniform_float("color", color)
    bgl.glEnable(bgl.GL_BLEND)
    batch.draw(shader)


def draw_line2d(x1, y1, x2, y2, width, color):
    coords = (
        (x1, y1), (x2, y2))

    indices = (
        (0, 1),)
    bgl.glEnable(bgl.GL_BLEND)

    shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'LINES', {"pos": coords}, indices=indices)
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)


def draw_lines(vertices, indices, color):
    bgl.glEnable(bgl.GL_BLEND)

    shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'LINES', {"pos": vertices}, indices=indices)
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)


def draw_rect_3d(coords, color):
    indices = [(0, 1, 2), (2, 3, 0)]
    shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'TRIS', {"pos": coords}, indices=indices)
    shader.uniform_float("color", color)
    batch.draw(shader)


def draw_image(x, y, width, height, image, transparency, crop=(0, 0, 1, 1)):
    # draw_rect(x,y, width, height, (.5,0,0,.5))

    coords = [
        (x, y), (x + width, y),
        (x, y + height), (x + width, y + height)]

    uvs = [(crop[0], crop[1]),
           (crop[2], crop[1]),
           (crop[0], crop[3]),
           (crop[2], crop[3]),
           ]

    indices = [(0, 1, 2), (2, 1, 3)]

    shader = gpu.shader.from_builtin('2D_IMAGE')
    batch = batch_for_shader(shader, 'TRIS',
                             {"pos": coords,
                              "texCoord": uvs},
                             indices=indices)

    # send image to gpu if it isn't there already
    if image.gl_load():
        raise Exception()

    # texture identifier on gpu
    texture_id = image.bindcode

    # in case someone disabled it before
    bgl.glEnable(bgl.GL_BLEND)

    # bind texture to image unit 0
    bgl.glActiveTexture(bgl.GL_TEXTURE0)
    bgl.glBindTexture(bgl.GL_TEXTURE_2D, texture_id)

    shader.bind()
    # tell shader to use the image that is bound to image unit 0
    shader.uniform_int("image", 0)
    batch.draw(shader)

    bgl.glDisable(bgl.GL_TEXTURE_2D)


def draw_text(text, x, y, size, color=(1, 1, 1, 0.5)):
    font_id = 0
    # bgl.glColor4f(*color)
    blf.color(font_id, color[0], color[1], color[2], color[3])
    blf.position(font_id, x, y, 0)
    blf.size(font_id, size, 72)
    blf.draw(font_id, text)
