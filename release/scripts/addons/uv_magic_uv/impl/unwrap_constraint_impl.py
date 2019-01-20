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

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "5.2"
__date__ = "17 Nov 2018"

import bpy
import bmesh

from .. import common


def _is_valid_context(context):
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


class UnwrapConstraintImpl:
    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return _is_valid_context(context)

    def execute(self, ops_obj, context):
        obj = context.active_object
        bm = bmesh.from_edit_mesh(obj.data)
        if common.check_version(2, 73, 0) >= 0:
            bm.faces.ensure_lookup_table()

        # bpy.ops.uv.unwrap() makes one UV map at least
        if not bm.loops.layers.uv:
            ops_obj.report({'WARNING'},
                           "Object must have more than one UV map")
            return {'CANCELLED'}
        uv_layer = bm.loops.layers.uv.verify()

        # get original UV coordinate
        faces = [f for f in bm.faces if f.select]
        uv_list = []
        for f in faces:
            uvs = [l[uv_layer].uv.copy() for l in f.loops]
            uv_list.append(uvs)

        # unwrap
        bpy.ops.uv.unwrap(
            method=ops_obj.method,
            fill_holes=ops_obj.fill_holes,
            correct_aspect=ops_obj.correct_aspect,
            use_subsurf_data=ops_obj.use_subsurf_data,
            margin=ops_obj.margin)

        # when U/V-Constraint is checked, revert original coordinate
        for f, uvs in zip(faces, uv_list):
            for l, uv in zip(f.loops, uvs):
                if ops_obj.u_const:
                    l[uv_layer].uv.x = uv.x
                if ops_obj.v_const:
                    l[uv_layer].uv.y = uv.y

        # update mesh
        bmesh.update_edit_mesh(obj.data)

        return {'FINISHED'}
