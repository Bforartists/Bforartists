# ##### BEGIN GPL LICENSE BLOCK #####
#
#  SCA Tree Generator,  a Blender addon
#  (c) 2013 Michel J. Anders (varkenvarken)
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License,  or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not,  write to the Free Software Foundation,
#  Inc.,  51 Franklin Street,  Fifth Floor,  Boston,  MA 02110-1301,  USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

from math import pi
from mathutils import Quaternion

rot120 = 2 * pi / 3


def rot(point, axis, angle):
    q = Quaternion(axis, angle)
    P = point.copy()
    P.rotate(q)
    #print(point, P)
    return P


def vertexnormal(d1, d2, d3):
    n1 = d1.cross(d2).normalized()
    n2 = d2.cross(d3).normalized()
    n3 = d3.cross(d1).normalized()
    n = (n1 + n2 + n3).normalized()
    if (d1 + d2 + d3).dot(n) > 0:
        return -n
    return n


def simplefork2(p0, p1, p2, p3, r0, r1, r2, r3):
    d1 = p1 - p0
    d2 = p2 - p0
    d3 = p3 - p0
    #print(d1, d2, d3)
    n = vertexnormal(d1, d2, d3)
    #print(n)

    pp1 = p0 + d1 / 3
    n1a = r1 * n
    n1b = rot(n1a, d1, rot120)
    n1c = rot(n1a, d1, -rot120)
    v1a = pp1 + n1a
    v1b = pp1 + n1b
    v1c = pp1 + n1c

    pp2 = p0 + d2 / 3
    n2a = r2 * n
    n2b = rot(n2a, d2, rot120)
    n2c = rot(n2a, d2, -rot120)
    v2a = pp2 + n2a
    v2b = pp2 + n2b
    v2c = pp2 + n2c

    pp3 = p0 + d3 / 3
    n3a = r3 * n
    n3b = rot(n3a, d3, rot120)
    n3c = rot(n3a, d3, -rot120)
    v3a = pp3 + n3a
    v3b = pp3 + n3b
    v3c = pp3 + n3c

    n0a = n * r0
    v0a = p0 + n0a
    v0c = p0 - d3.normalized() * r0 - n0a / 3
    v0d = p0 - d1.normalized() * r0 - n0a / 3
    v0b = p0 - d2.normalized() * r0 - n0a / 3

    #v0b=p0+(n1b+n2c)/2
    #v0d=p0+(n2b+n3c)/2
    #v0c=p0+(n3b+n1c)/2

    verts = (v1a, v1b, v1c, v2a, v2b, v2c, v3a, v3b, v3c, v0a, v0b, v0c, v0d)
    faces = ((0, 1, 10, 9), (1, 2, 11, 10), (2, 0, 9, 11),  # chck
        (3, 4, 11, 9), (4, 5, 12, 11), (5, 3, 9, 12),  # chck

        (6, 7, 12, 9),
        (7, 8, 10, 12),
        (8, 6, 9, 10),

        (10, 11, 12))

    return verts, faces


def simplefork(p0, p1, p2, p3, r0, r1, r2, r3):
    d1 = p1 - p0
    d2 = p2 - p0
    d3 = p3 - p0
    #print(d1, d2, d3)
    n = -vertexnormal(d1, d2, d3)
    #print(n)

    # the central tetrahedron
    n0a = n * r0 * 0.3
    v0a = n0a
    v0b = -d1 / 6 - n0a / 2
    v0c = -d2 / 6 - n0a / 2
    v0d = -d3 / 6 - n0a / 2

    n1 = v0a + v0c + v0d
    n2 = v0a + v0b + v0d
    n3 = v0a + v0b + v0c

    q1 = n1.rotation_difference(d1)
    q2 = n2.rotation_difference(d2)
    q3 = n3.rotation_difference(d3)

    pp1 = p0 + d1 / 3
    v1a = v0a.copy()
    v1b = v0c.copy()
    v1c = v0d.copy()
    v1a.rotate(q1)
    v1b.rotate(q1)
    v1c.rotate(q1)
    v1a += pp1
    v1b += pp1
    v1c += pp1

    pp2 = p0 + d2 / 3
    v2a = v0a.copy()
    v2b = v0b.copy()
    v2c = v0d.copy()
    v2a.rotate(q2)
    v2b.rotate(q2)
    v2c.rotate(q2)
    v2a += pp2
    v2b += pp2
    v2c += pp2

    pp3 = p0 + d3 / 3
    v3a = v0a.copy()
    v3b = v0b.copy()
    v3c = v0c.copy()
    v3a.rotate(q3)
    v3b.rotate(q3)
    v3c.rotate(q3)
    v3a += pp3
    v3b += pp3
    v3c += pp3

    v0a += p0
    v0b += p0
    v0c += p0
    v0d += p0

    verts = (v1a, v1b, v1c, v2a, v2b, v2c, v3a, v3b, v3c, v0a, v0b, v0c, v0d)
    faces = (
        #(1, 2, 12, 11),
        #(9, 12, 2, 0),
        #(11, 9, 0, 1),

        #(5, 4, 10, 12),
        #(4, 3, 9, 10),
        #(3, 5, 12, 9),

        (8, 7, 11, 10),
        (7, 5, 9, 11),
        (6, 8, 10, 9),

        (10, 11, 12))

    return verts, faces


def bridgequads(aquad, bquad, verts):
    "return faces,  aloop,  bloop"
    ai, bi, _ = min([(ai, bi, (verts[a] - verts[b]).length_squared) for ai, a in enumerate(aquad) for bi, b in enumerate(bquad)], key=lambda x: x[2])
    n = len(aquad)
    #print([(aquad[(ai+i)%n],  aquad[(ai+i+1)%n],  bquad[(bi+i+1)%n],  bquad[(bi+i)%n]) for i in range(n)], "\n",  [aquad[(ai+i)%n] for i in range(n)], "\n",   [aquad[(bi+i)%n] for i in range(n)])

    #print('bridgequads', aquad, bquad, ai, bi)

    return ([(aquad[(ai + i) % n], aquad[(ai + i + 1) % n], bquad[(bi + i + 1) % n], bquad[(bi + i) % n]) for i in range(n)], [aquad[(ai + i) % n] for i in range(n)], [bquad[(bi + i) % n] for i in range(n)])


def quadfork(p0, p1, p2, p3, r0, r1, r2, r3):
    d1 = p1 - p0
    d2 = p2 - p0
    d3 = p3 - p0
    a = (d3 - d2).normalized()
    n = d2.cross(d3).normalized()
    pp1 = p0 + d1 / 3
    pp2 = p0 + d2 / 3
    pp3 = p0 + d3 / 3

    v2a = pp2 + (n + a) * r2
    v2b = pp2 + (n - a) * r2
    v2c = pp2 + (-n - a) * r2
    v2d = pp2 + (-n + a) * r2

    v3a = pp3 + (n + a) * r3
    v3b = pp3 + (n - a) * r3
    v3c = pp3 + (-n - a) * r3
    v3d = pp3 + (-n + a) * r3

    a = d1.cross(n).normalized()
    n = a.cross(d1).normalized()
    v1a = pp1 + (n + a) * r1
    v1b = pp1 + (n - a) * r1
    v1c = pp1 + (-n - a) * r1
    v1d = pp1 + (-n + a) * r1

    #the top of the connecting block consist of two quads
    v0a = p0 + (n + a) * r0
    v0b = p0 + (n - a) * r0
    v0c = p0 + (-n - a) * r0
    v0d = p0 + (-n + a) * r0
    v0ab = p0 + n * r0
    v0cd = p0 - n * r0
    #the bottom is a single quad (which means the front and back are 5gons)
    d = d1.normalized() * r0 * 0.1
    vb0a = v0a + d
    vb0b = v0b + d
    vb0c = v0c + d
    vb0d = v0d + d

    verts = [v1a, v1b, v1c, v1d,             # 0 1 2 3
        v2a, v2b, v2c, v2d,             # 4 5 6 7
        v3a, v3b, v3c, v3d,             # 8 9 10 11
        v0a, v0ab, v0b, v0c, v0cd, v0d,   # 12 13 14 15 16 17
        vb0a, vb0b, vb0c, vb0d]        # 18 19 20 21

    faces = [(0, 1, 19, 18),        # p1->p0 bottom
        (1, 2, 20, 19),
        (2, 3, 21, 20),
        (3, 0, 18, 21),

        #(4, 5, 14, 13),        # p2 -> p0 top right
        #(5, 6, 15, 14),
        #(6, 7, 16, 15),
        #(7, 4, 13, 16),

        (13, 14, 5, 4),
        (14, 15, 6, 5),
        (15, 16, 7, 6),
        (16, 13, 4, 7),

        #(8, 9, 13, 12),        # p3 -> p0 top left
        #(9, 10, 16, 13),
        #(10, 11, 17, 16),
        #(11, 8, 12, 17),

        (12, 13, 9, 8),
        (13, 16, 10, 9),
        (16, 17, 11, 10),
        (17, 12, 8, 11),

        #(12, 17, 21, 18),      # connecting block
        #(14, 15, 20, 19),
        #(12, 13, 14, 19, 18),
        #(15, 16, 17, 21, 20)]

        (12, 17, 21, 18),      # connecting block
        (19, 20, 15, 14),
        (18, 19, 14, 13, 12),
        (20, 21, 17, 16, 15)]

    return verts, faces
