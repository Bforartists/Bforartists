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
from collections import OrderedDict
from itertools import combinations  # , permutations

import bpy
from bpy.props import *
import mathutils as Math
from mathutils import Matrix, Euler, Vector, Quaternion
#geo = mathutils.geometry

MIN_NUMBER = 1E-8

def is_nan(f):
    return not f == f
    #return f < f or f <= f

def is_inf(f):
    try:
        int(f)
        return False
    except OverflowError:
        return True
    except:
        return False

def saacos(fac):
    if fac <= -1.0:
        return math.pi
    elif fac >= 1.0:
        return 0.0
    else:
        return math.acos(fac)


def saasin(fac):
    if fac <= -1.0:
        return -math.pi / 2.0
    elif fac >= 1.0:
        return math.pi / 2.0
    else:
        return math.asin(fac)


def angle_normalized_v3v3(v1, v2):
    # rotation_between_vecs_to_quat用
    # 不要 v1.angle(v2)と同じ
    if v1.dot(v2) < 0.0:
        vec = Vector(-v2)
        return math.pi - 2.0 * saasin((vec - v1).length / 2.0)
    else:
        return 2.0 * saasin((v2 - v1).length / 2.0)


def cross2D(v1, v2):
    return v1.x * v2.y - v1.y * v2.x


def dot2D(v1, v2):
    return v1.x * v2.x + v1.y * v2.y


def axis_angle_to_quat(axis, angle):
    if axis.length < MIN_NUMBER:
        return Quaternion([1, 0, 0, 0])
    nor = axis.normalized()
    angle = angle / 2
    si = math.sin(angle)
    return Quaternion([math.cos(angle), nor[0] * si, nor[1] * si, nor[2] * si])


def rotation_between_vecs_to_quat(vec1, vec2):
    axis = vec1.cross(vec2)
    # angle = angle_normalized_v3v3(vec1, vec2)
    angle = vec1.angle(vec2)
    return axis_angle_to_quat(axis, angle)


def removed_same_coordinate(vecs):
    d = OrderedDict(zip((tuple(v) for v in vecs), range(len(vecs))))
    return [vecs[i] for i in d.values()]


'''def is_plane(*vecs):
    # 与えられたベクトルが同一平面上にあるか
    # 平面が定義できない場合は Noneを返す
    vecs = removed_same_coorinate(vecs)
    if len(vecs) <= 2:
        return None
    v0 = vecs[0]

    vec1 = vecs[1] - v0
    axis_list = [vec1.cross(v2 - v0).normalized() for v2 in vecs[2:]]
    return True
'''


### 旧 ###
def intersect(vec1, vec2, vec3, ray, orig, clip=1):
    v1 = vec1.copy()
    v2 = vec2.copy()
    v3 = vec3.copy()
    dir = ray.normalized()
    orig = orig.copy()

    # find vectors for two edges sharing v1
    e1 = v2 - v1
    e2 = v3 - v1

    # begin calculating determinant - also used to calculated U parameter
    pvec = dir.cross(e2)

    # if determinant is near zero, ray lies in plane of triangle
    det = e1.dot(pvec)

    if (-1E-6 < det < 1E-6):
        return None

    inv_det = 1.0 / det

    # calculate distance from v1 to ray origin
    tvec = orig - v1

    # calculate U parameter and test bounds
    u = tvec.dot(pvec) * inv_det
    if (clip and (u < 0.0 or u > 1.0)):
        return None

    # prepare to test the V parameter
    qvec = tvec.cross(e1)

    # calculate V parameter and test bounds
    v = dir.dot(qvec) * inv_det

    if (clip and (v < 0.0 or u + v > 1.0)):
        return None

    # calculate t, ray intersects triangle
    t = e2.dot(qvec) * inv_det

    dir = dir * t
    pvec = orig + dir

    return pvec


def plane_intersect(loc, normalvec, seg1, seg2, returnstatus=0):
    zaxis = Vector([0.0, 0.0, 1.0])
    normal = normalvec.copy()
    normal.normalize()
    quat = rotation_between_vecs_to_quat(normal, zaxis)
    s1 = (seg1 - loc) * quat
    s2 = (seg2 - loc) * quat
    t = crossStatus = None
    if abs(s1[2] - s2[2]) < 1E-6:
        crossPoint = None
        if abs(s1[2]) < 1E-6:
            crossStatus = 3  # 面と重なる
        else:
            crossStatus = -1  # 面と平行
    elif s1[2] == 0.0:
        crossPoint = seg1
        t = 0
    elif s2[2] == 0.0:
        crossPoint = seg2
        t = 1
    else:
        t = -(s1[2] / (s2[2] - s1[2]))
        crossPoint = (seg2 - seg1) * t + seg1
    if t is not None:
        if 0 <= t <= 1:
            crossStatus = 2  # seg
        elif t > 0:
            crossStatus = 1  # ray
        else:
            crossStatus = 0  # line
    if returnstatus:
        return crossPoint, crossStatus
    else:
        return crossPoint


def vedistance(vecp, vec1, vec2, segment=1, returnVerticalPoint=False):
    dist = None
    if segment:
        if DotVecs(vec2 - vec1, vecp - vec1) < 0.0:
            dist = (vecp - vec1).length
        elif DotVecs(vec1 - vec2, vecp - vec2) < 0.0:
            dist = (vecp - vec2).length
    vec = vec2 - vec1
    p = vecp - vec1
    zaxis = Vector([0.0, 0.0, 1.0])
    quat = rotation_between_vecs_to_quat(vec, zaxis)
    p2 = p * quat
    if dist is None:
        dist = math.sqrt(p2[0] ** 2 + p2[1] ** 2)
    t = p2[2] / (vec2 - vec1).length
    verticalPoint = vec1 + vec * t

    if returnVerticalPoint:
        return dist, verticalPoint
    else:
        return dist
