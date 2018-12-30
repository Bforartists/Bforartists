# <pep8-80 compliant>

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

__author__ = "imdjs, Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "5.2"
__date__ = "17 Nov 2018"


from math import sin, cos, pi

from mathutils import Vector


def is_valid_context(context):
    obj = context.object

    # only edit mode is allowed to execute
    if obj is None:
        return False
    if obj.type != 'MESH':
        return False
    if context.object.mode != 'EDIT':
        return False

    # only 'VIEW_3D' space is allowed to execute
    for space in context.area.spaces:
        if space.type == 'VIEW_3D':
            break
    else:
        return False

    return True


def get_uv_layer(ops_obj, bm, assign_uvmap):
    # get UV layer
    if not bm.loops.layers.uv:
        if assign_uvmap:
            bm.loops.layers.uv.new()
        else:
            ops_obj.report({'WARNING'},
                           "Object must have more than one UV map")
            return None
    uv_layer = bm.loops.layers.uv.verify()

    return uv_layer


def apply_box_map(bm, uv_layer, size, offset, rotation, tex_aspect):
    scale = 1.0 / size

    sx = 1.0 * scale
    sy = 1.0 * scale
    sz = 1.0 * scale
    ofx = offset[0]
    ofy = offset[1]
    ofz = offset[2]
    rx = rotation[0] * pi / 180.0
    ry = rotation[1] * pi / 180.0
    rz = rotation[2] * pi / 180.0
    aspect = tex_aspect

    sel_faces = [f for f in bm.faces if f.select]

    # update UV coordinate
    for f in sel_faces:
        n = f.normal
        for l in f.loops:
            co = l.vert.co
            x = co.x * sx
            y = co.y * sy
            z = co.z * sz

            # X-plane
            if abs(n[0]) >= abs(n[1]) and abs(n[0]) >= abs(n[2]):
                if n[0] >= 0.0:
                    u = (y - ofy) * cos(rx) + (z - ofz) * sin(rx)
                    v = -(y * aspect - ofy) * sin(rx) + \
                        (z * aspect - ofz) * cos(rx)
                else:
                    u = -(y - ofy) * cos(rx) + (z - ofz) * sin(rx)
                    v = (y * aspect - ofy) * sin(rx) + \
                        (z * aspect - ofz) * cos(rx)
            # Y-plane
            elif abs(n[1]) >= abs(n[0]) and abs(n[1]) >= abs(n[2]):
                if n[1] >= 0.0:
                    u = -(x - ofx) * cos(ry) + (z - ofz) * sin(ry)
                    v = (x * aspect - ofx) * sin(ry) + \
                        (z * aspect - ofz) * cos(ry)
                else:
                    u = (x - ofx) * cos(ry) + (z - ofz) * sin(ry)
                    v = -(x * aspect - ofx) * sin(ry) + \
                        (z * aspect - ofz) * cos(ry)
            # Z-plane
            else:
                if n[2] >= 0.0:
                    u = (x - ofx) * cos(rz) + (y - ofy) * sin(rz)
                    v = -(x * aspect - ofx) * sin(rz) + \
                        (y * aspect - ofy) * cos(rz)
                else:
                    u = -(x - ofx) * cos(rz) - (y + ofy) * sin(rz)
                    v = -(x * aspect + ofx) * sin(rz) + \
                        (y * aspect - ofy) * cos(rz)

            l[uv_layer].uv = Vector((u, v))


def apply_planer_map(bm, uv_layer, size, offset, rotation, tex_aspect):
    scale = 1.0 / size

    sx = 1.0 * scale
    sy = 1.0 * scale
    ofx = offset[0]
    ofy = offset[1]
    rz = rotation * pi / 180.0
    aspect = tex_aspect

    sel_faces = [f for f in bm.faces if f.select]

    # calculate average of normal
    n_ave = Vector((0.0, 0.0, 0.0))
    for f in sel_faces:
        n_ave = n_ave + f.normal
    q = n_ave.rotation_difference(Vector((0.0, 0.0, 1.0)))

    # update UV coordinate
    for f in sel_faces:
        for l in f.loops:
            co = q @ l.vert.co
            x = co.x * sx
            y = co.y * sy

            u = x * cos(rz) - y * sin(rz) + ofx
            v = -x * aspect * sin(rz) - y * aspect * cos(rz) + ofy

            l[uv_layer].uv = Vector((u, v))
