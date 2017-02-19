# coding: utf-8

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

import math

import bpy
from bpy.props import *
import blf
import mathutils as Math
from mathutils import Matrix, Euler, Vector, Quaternion
import bgl
#geo = mathutils.geometry

class GLSettings:
    def __init__(self, context):
        rv3d = context.region_data
        persmat = rv3d.perspective_matrix
        flatten_persmat = [persmat[i][j] for i in range(4) for j in range(4)]
        self.persmat_buffer = bgl.Buffer(bgl.GL_FLOAT, 16, flatten_persmat)

        # GL_BLEND
        blend = bgl.Buffer(bgl.GL_BYTE, [1])
        bgl.glGetFloatv(bgl.GL_BLEND, blend)
        self.blend = blend[0]

        # GL_COLOR
        color = bgl.Buffer(bgl.GL_FLOAT, [4])
        bgl.glGetFloatv(bgl.GL_COLOR, color)
        self.color = color

        # GL_LINE_WIDTH
        line_width = bgl.Buffer(bgl.GL_FLOAT, [1])
        bgl.glGetFloatv(bgl.GL_LINE_WIDTH, line_width)
        self.line_width = line_width[0]

        # GL_Matrix_MODE
        matrix_mode = bgl.Buffer(bgl.GL_INT, [1])
        bgl.glGetIntegerv(bgl.GL_MATRIX_MODE, matrix_mode)
        self.matrix_mode = matrix_mode[0]

        # GL_PROJECTION_MATRIX
        projection_matrix = bgl.Buffer(bgl.GL_DOUBLE, [16])
        bgl.glGetFloatv(bgl.GL_PROJECTION_MATRIX, projection_matrix)
        self.projection_matrix = projection_matrix

        # blf: size, dpi
        self.size_dpi = (11, context.user_preferences.system.dpi)

    def prepare_3D(self):
        bgl.glLoadIdentity()
        bgl.glMatrixMode(bgl.GL_PROJECTION)
        bgl.glLoadMatrixf(self.persmat_buffer)

    def restore_3D(self):
        bgl.glLoadIdentity()
        bgl.glMatrixMode(self.matrix_mode)
        bgl.glLoadMatrixf(self.projection_matrix)

    def restore(self):
        if not self.blend:
            bgl.glDisable(bgl.GL_BLEND)
        bgl.glColor4f(*self.color)
        bgl.glLineWidth(self.line_width)
        blf.size(0, self.size_dpi[0], self.size_dpi[1])


def draw_circle(x, y, radius, subdivide, poly=False):
    r = 0.0
    dr = math.pi * 2 / subdivide
    if poly:
        subdivide += 1
        bgl.glBegin(bgl.GL_TRIANGLE_FAN)
        bgl.glVertex2f(x, y)
    else:
        bgl.glBegin(bgl.GL_LINE_LOOP)
    for i in range(subdivide):
        bgl.glVertex2f(x + radius * math.cos(r), y + radius * math.sin(r))
        r += dr
    bgl.glEnd()


def draw_box(xmin, ymin, w, h, poly=False):
    bgl.glBegin(bgl.GL_QUADS if poly else bgl.GL_LINE_LOOP)
    bgl.glVertex2f(xmin, ymin)
    bgl.glVertex2f(xmin + w, ymin)
    bgl.glVertex2f(xmin + w, ymin + h)
    bgl.glVertex2f(xmin, ymin + h)
    bgl.glEnd()


def draw_triangles(verts, poly=False):
    bgl.glBegin(bgl.GL_TRIANGLES if poly else bgl.GL_LINE_LOOP)
    for v in verts:
        bgl.glVertex2f(v[0], v[1])
    bgl.glEnd()


def triangle_relative_to_verts(top, base_relative, base_length):
    v1 = Vector(top)
    v = Vector([-base_relative[1] / 2, base_relative[0] / 2])
    v.normalize()
    v *= base_length / 2
    vb = Vector(base_relative)
    v2 = v1 + vb + v
    v3 = v1 + vb - v
    return v1, v2, v3


def draw_triangle_relative(top, base_relative, base_length,
                           mode=bgl.GL_TRIANGLES):
    v1, v2, v3 = triangle_relative_to_verts(top, base_relative, base_length)
    bgl.glBegin(mode)
    bgl.glVertex2f(*v1)
    bgl.glVertex2f(*v2)
    bgl.glVertex2f(*v3)
    bgl.glEnd()


def draw_triangle_get_vectors(base, base_length, top_relative):
    # triangle_relative_to_vertsの書き直し
    # base左, base右, top
    v0 = Vector(base)
    v = (Vector([-top_relative[1], top_relative[0]])).normalized()
    v *= base_length / 2
    v1 = v0 + v
    v2 = v0 - v
    v3 = v0 + Vector(top_relative)
    return v1, v2, v3


def draw_triangle(base, base_length, top_relative, poly=False):
    # draw_triangle_relativeの書き直し
    # base左, base右, top
    v1, v2, v3 = draw_triangle_get_vectors(base, base_length, top_relative)
    bgl.glBegin(bgl.GL_TRIANGLES if poly else bgl.GL_LINE_LOOP)
    bgl.glVertex2f(*v1)
    bgl.glVertex2f(*v2)
    bgl.glVertex2f(*v3)
    bgl.glEnd()


def draw_trapezoid_get_vectors(base, top_relative, base_length, top_length):
    # base左, base右, top右, top左
    v0 = Vector(base)
    v = (Vector([-top_relative[1], top_relative[0]])).normalized()
    vb = v * base_length / 2
    v1 = v0 + vb
    v2 = v0 - vb
    vt = v * top_length / 2
    v3 = v0 + Vector(top_relative) - vt
    v4 = v0 + Vector(top_relative) + vt
    return v1, v2, v3, v4


def draw_trapezoid(base, top_relative, base_length, top_length, poly=False):
    # base左, base右, top右, top左
    v1, v2, v3, v4 = draw_trapezoid_get_vectors(base, top_relative,
                                                base_length, top_length)
    bgl.glBegin(bgl.GL_QUADS if poly else bgl.GL_LINE_LOOP)
    bgl.glVertex2f(*v1)
    bgl.glVertex2f(*v2)
    bgl.glVertex2f(*v3)
    bgl.glVertex2f(*v4)
    bgl.glEnd()


def draw_arc12(x, y, radius, start_angle, end_angle, subdivide):  # いずれ削除
    # 十二時から時計回りに描画
    v = Vector([0, 1, 0])
    e = Euler((0, 0, -start_angle))
    m = e.to_matrix()
    v = v * m
    if end_angle >= start_angle:
        a = (end_angle - start_angle) / (subdivide + 1)
    else:
        a = (end_angle + math.pi * 2 - start_angle) / (subdivide + 1)
    e = Euler((0, 0, -a))
    m = e.to_matrix()

    bgl.glBegin(bgl.GL_LINE_STRIP)
    for i in range(subdivide + 2):
        v1 = v * radius
        bgl.glVertex2f(x + v1[0], y + v1[1])
        v = v * m
    bgl.glEnd()


def normalize_angle(angle):
    while angle < 0.0:
        angle += math.pi * 2
    while angle > math.pi * 2:
        angle -= math.pi * 2
    return angle


def draw_quad_fan(x, y, inner_radius, outer_radius,
                  start_angle, end_angle, edgenum=16):
    # 三時から反時計回りに描画
    start = normalize_angle(start_angle)
    end = normalize_angle(end_angle)
    if end < start:
        end += math.pi * 2
    d = (end - start) / edgenum
    a = start
    bgl.glBegin(bgl.GL_QUAD_STRIP)
    for i in range(edgenum + 1):
        bgl.glVertex2f(x + inner_radius * math.cos(a),
                       y + inner_radius * math.sin(a))
        bgl.glVertex2f(x + outer_radius * math.cos(a),
                       y + outer_radius * math.sin(a))
        a += d
    bgl.glEnd()


def draw_arc_get_vectors(x, y, radius, start_angle, end_angle, edgenum=16):
    # 三時から反時計回りに描画 angle:radians
    start = normalize_angle(start_angle)
    end = normalize_angle(end_angle)
    if end < start:
        end += math.pi * 2
    d = (end - start) / edgenum
    a = start
    l = []
    for i in range(edgenum + 1):
        l.append(Vector([x + radius * math.cos(a), y + radius * math.sin(a)]))
        a += d
    return l


def draw_arc(x, y, radius, start_angle, end_angle, edgenum=16):
    # 三時から反時計回りに描画 angle:radians
    l = draw_arc_get_vectors(x, y, radius, start_angle, end_angle, edgenum)
    bgl.glBegin(bgl.GL_LINE_STRIP)
    for v in l:
        bgl.glVertex2f(*v)
    bgl.glEnd()


def draw_arrow(nockx, nocky, headx, heady, headlength=10, \
               headangle=math.radians(70), headonly=False):
    '''
    nockx, nocky: 筈
    headx, heady: 鏃
    headangle: 0 <= headangle <= 180
    headlength: nockとhead上での距離
    '''
    if nockx == headx and nocky == heady or headonly and headlength == 0:
        return
    angle = max(min(math.pi / 2, headangle / 2), 0)  # 箆との角度
    vn = Vector((nockx, nocky))
    vh = Vector((headx, heady))
    '''if headonly:
        vh = vh + (vh - vn).normalized() * headlength
        headx, heady = vh
    '''
    bgl.glBegin(bgl.GL_LINES)
    # shaft
    if not headonly:
        bgl.glVertex2f(nockx, nocky)
        bgl.glVertex2f(headx, heady)
    # head
    if headlength:
        length = headlength / math.cos(angle)
        vec = (vn - vh).normalized() * length
        vec.resize_3d()
        q = Quaternion((0, 0, 0, -1))
        q.angle = angle
        v = vec * q
        bgl.glVertex2f(headx, heady)
        bgl.glVertex2f(headx + v[0], heady + v[1])
        q.angle = -angle
        v = vec * q
        bgl.glVertex2f(headx, heady)
        bgl.glVertex2f(headx + v[0], heady + v[1])
    bgl.glEnd()


def draw_sun(x, y, radius, subdivide=16, raydirections=[],
             raylength=10, raystartoffset=0):
    draw_circle(x, y, radius, subdivide)
    bgl.glBegin(bgl.GL_LINES)
    if isinstance(raylength, (int, float)):
        llist = [raylength for i in range(len(raydirections))]
    else:
        llist = raylength
    for i, angle in enumerate(raydirections):
        bgl.glVertex2f(x + (radius + raystartoffset) * math.cos(angle), \
                       y + (radius + raystartoffset) * math.sin(angle))
        bgl.glVertex2f(x + (radius + llist[i]) * math.cos(angle), \
                       y + (radius + llist[i]) * math.sin(angle))
    bgl.glEnd()


def draw_rounded_box(xmin, ymin, xmax, ymax, round_radius, poly=False):
    r = min(round_radius, (xmax - xmin) / 2, (ymax - ymin) / 2)
    bgl.glBegin(bgl.GL_POLYGON if poly else bgl.GL_LINE_LOOP)
    if round_radius > 0.0:
        pi = math.pi
        l = []
        # 左下
        l += draw_arc_get_vectors(xmin + r, ymin + r, r, pi, pi * 3 / 2, 4)
        # 右下
        l += draw_arc_get_vectors(xmax - r, ymin + r, r, pi * 3 / 2, 0.0, 4)
        # 右上
        l += draw_arc_get_vectors(xmax - r, ymax - r, r, 0.0, pi / 2, 4)
        # 左上
        l += draw_arc_get_vectors(xmin + r, ymax - r, r, pi / 2, pi, 4)
        for v in l:
            bgl.glVertex2f(*v)
    else:
        bgl.glVertex2f(xmin, ymin)
        bgl.glVertex2f(xmax, ymin)
        bgl.glVertex2f(xmax, ymax)
        bgl.glVertex2f(xmin, ymax)
    bgl.glEnd()
