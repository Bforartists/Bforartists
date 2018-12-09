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

__author__ = "Alexander Milovsky, Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "5.1"
__date__ = "24 Feb 2018"

from math import sin, cos, pi

import bpy
import bmesh
from bpy.props import (
    FloatProperty,
    FloatVectorProperty,
    BoolProperty
)
from mathutils import Vector

from .. import common


class MUV_UVWBoxMap(bpy.types.Operator):
    bl_idname = "uv.muv_uvw_box_map"
    bl_label = "Box Map"
    bl_options = {'REGISTER', 'UNDO'}

    size = FloatProperty(
        name="Size",
        default=1.0,
        precision=4
    )
    rotation = FloatVectorProperty(
        name="XYZ Rotation",
        size=3,
        default=(0.0, 0.0, 0.0)
    )
    offset = FloatVectorProperty(
        name="XYZ Offset",
        size=3,
        default=(0.0, 0.0, 0.0)
    )
    tex_aspect = FloatProperty(
        name="Texture Aspect",
        default=1.0,
        precision=4
    )
    assign_uvmap = BoolProperty(
        name="Assign UVMap",
        description="Assign UVMap when no UVmaps are available",
        default=True
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH'

    def execute(self, context):
        obj = context.active_object
        bm = bmesh.from_edit_mesh(obj.data)
        if common.check_version(2, 73, 0) >= 0:
            bm.faces.ensure_lookup_table()

        # get UV layer
        if not bm.loops.layers.uv:
            if self.assign_uvmap:
                bm.loops.layers.uv.new()
            else:
                self.report(
                    {'WARNING'}, "Object must have more than one UV map")
                return {'CANCELLED'}
        uv_layer = bm.loops.layers.uv.verify()

        scale = 1.0 / self.size

        sx = 1.0 * scale
        sy = 1.0 * scale
        sz = 1.0 * scale
        ofx = self.offset[0]
        ofy = self.offset[1]
        ofz = self.offset[2]
        rx = self.rotation[0] * pi / 180.0
        ry = self.rotation[1] * pi / 180.0
        rz = self.rotation[2] * pi / 180.0
        aspect = self.tex_aspect

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
                        v = -(y * aspect - ofy) * sin(rx) +\
                            (z * aspect - ofz) * cos(rx)
                    else:
                        u = -(y - ofy) * cos(rx) + (z - ofz) * sin(rx)
                        v = (y * aspect - ofy) * sin(rx) +\
                            (z * aspect - ofz) * cos(rx)
                # Y-plane
                elif abs(n[1]) >= abs(n[0]) and abs(n[1]) >= abs(n[2]):
                    if n[1] >= 0.0:
                        u = -(x - ofx) * cos(ry) + (z - ofz) * sin(ry)
                        v = (x * aspect - ofx) * sin(ry) +\
                            (z * aspect - ofz) * cos(ry)
                    else:
                        u = (x - ofx) * cos(ry) + (z - ofz) * sin(ry)
                        v = -(x * aspect - ofx) * sin(ry) +\
                            (z * aspect - ofz) * cos(ry)
                # Z-plane
                else:
                    if n[2] >= 0.0:
                        u = (x - ofx) * cos(rz) + (y - ofy) * sin(rz)
                        v = -(x * aspect - ofx) * sin(rz) +\
                            (y * aspect - ofy) * cos(rz)
                    else:
                        u = -(x - ofx) * cos(rz) - (y + ofy) * sin(rz)
                        v = -(x * aspect + ofx) * sin(rz) +\
                            (y * aspect - ofy) * cos(rz)

                l[uv_layer].uv = Vector((u, v))

        bmesh.update_edit_mesh(obj.data)

        return {'FINISHED'}


class MUV_UVWBestPlanerMap(bpy.types.Operator):
    bl_idname = "uv.muv_uvw_best_planer_map"
    bl_label = "Best Planer Map"
    bl_options = {'REGISTER', 'UNDO'}

    size = FloatProperty(
        name="Size",
        default=1.0,
        precision=4
    )
    rotation = FloatProperty(
        name="XY Rotation",
        default=0.0
    )
    offset = FloatVectorProperty(
        name="XY Offset",
        size=2,
        default=(0.0, 0.0)
    )
    tex_aspect = FloatProperty(
        name="Texture Aspect",
        default=1.0,
        precision=4
    )
    assign_uvmap = BoolProperty(
        name="Assign UVMap",
        description="Assign UVMap when no UVmaps are available",
        default=True
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH'

    def execute(self, context):
        obj = context.active_object
        bm = bmesh.from_edit_mesh(obj.data)
        if common.check_version(2, 73, 0) >= 0:
            bm.faces.ensure_lookup_table()

        # get UV layer
        if not bm.loops.layers.uv:
            if self.assign_uvmap:
                bm.loops.layers.uv.new()
            else:
                self.report(
                    {'WARNING'}, "Object must have more than one UV map")
                return {'CANCELLED'}

        uv_layer = bm.loops.layers.uv.verify()

        scale = 1.0 / self.size

        sx = 1.0 * scale
        sy = 1.0 * scale
        ofx = self.offset[0]
        ofy = self.offset[1]
        rz = self.rotation * pi / 180.0
        aspect = self.tex_aspect

        sel_faces = [f for f in bm.faces if f.select]

        # calculate average of normal
        n_ave = Vector((0.0, 0.0, 0.0))
        for f in sel_faces:
            n_ave = n_ave + f.normal
        q = n_ave.rotation_difference(Vector((0.0, 0.0, 1.0)))

        # update UV coordinate
        for f in sel_faces:
            for l in f.loops:
                co = q * l.vert.co
                x = co.x * sx
                y = co.y * sy

                u = x * cos(rz) - y * sin(rz) + ofx
                v = -x * aspect * sin(rz) - y * aspect * cos(rz) + ofy

                l[uv_layer].uv = Vector((u, v))

        bmesh.update_edit_mesh(obj.data)

        return {'FINISHED'}
