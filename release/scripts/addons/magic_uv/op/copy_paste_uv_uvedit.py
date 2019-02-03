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
__version__ = "6.0"
__date__ = "26 Jan 2019"

import math
from math import atan2, sin, cos

import bpy
import bmesh
from mathutils import Vector

from .. import common
from ..utils.bl_class_registry import BlClassRegistry
from ..utils.property_class_registry import PropertyClassRegistry


def _is_valid_context(context):
    obj = context.object

    # only edit mode is allowed to execute
    if obj is None:
        return False
    if obj.type != 'MESH':
        return False
    if context.object.mode != 'EDIT':
        return False

    # 'IMAGE_EDITOR' and 'VIEW_3D' space is allowed to execute.
    # If 'View_3D' space is not allowed, you can't find option in Tool-Shelf
    # after the execution
    for space in context.area.spaces:
        if (space.type == 'IMAGE_EDITOR') or (space.type == 'VIEW_3D'):
            break
    else:
        return False

    return True


@PropertyClassRegistry()
class _Properties:
    idname = "copy_paste_uv_uvedit"

    @classmethod
    def init_props(cls, scene):
        class Props():
            src_uvs = None

        scene.muv_props.copy_paste_uv_uvedit = Props()

    @classmethod
    def del_props(cls, scene):
        del scene.muv_props.copy_paste_uv_uvedit


@BlClassRegistry()
class MUV_OT_CopyPasteUVUVEdit_CopyUV(bpy.types.Operator):
    """
    Operation class: Copy UV coordinate on UV/Image Editor
    """

    bl_idname = "uv.muv_ot_copy_paste_uv_uvedit_copy_uv"
    bl_label = "Copy UV (UV/Image Editor)"
    bl_description = "Copy UV coordinate (only selected in UV/Image Editor)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return _is_valid_context(context)

    def execute(self, context):
        props = context.scene.muv_props.copy_paste_uv_uvedit
        obj = context.active_object
        bm = bmesh.from_edit_mesh(obj.data)
        uv_layer = bm.loops.layers.uv.verify()
        if common.check_version(2, 73, 0) >= 0:
            bm.faces.ensure_lookup_table()

        props.src_uvs = []
        for face in bm.faces:
            if not face.select:
                continue
            skip = False
            for l in face.loops:
                if not l[uv_layer].select:
                    skip = True
                    break
            if skip:
                continue
            props.src_uvs.append([l[uv_layer].uv.copy() for l in face.loops])

        return {'FINISHED'}


@BlClassRegistry()
class MUV_OT_CopyPasteUVUVEdit_PasteUV(bpy.types.Operator):
    """
    Operation class: Paste UV coordinate on UV/Image Editor
    """

    bl_idname = "uv.muv_ot_copy_paste_uv_uvedit_paste_uv"
    bl_label = "Paste UV (UV/Image Editor)"
    bl_description = "Paste UV coordinate (only selected in UV/Image Editor)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        sc = context.scene
        props = sc.muv_props.copy_paste_uv_uvedit
        if not props.src_uvs:
            return False
        return _is_valid_context(context)

    def execute(self, context):
        props = context.scene.muv_props.copy_paste_uv_uvedit
        obj = context.active_object
        bm = bmesh.from_edit_mesh(obj.data)
        uv_layer = bm.loops.layers.uv.verify()
        if common.check_version(2, 73, 0) >= 0:
            bm.faces.ensure_lookup_table()

        dest_uvs = []
        dest_face_indices = []
        for face in bm.faces:
            if not face.select:
                continue
            skip = False
            for l in face.loops:
                if not l[uv_layer].select:
                    skip = True
                    break
            if skip:
                continue
            dest_face_indices.append(face.index)
            uvs = [l[uv_layer].uv.copy() for l in face.loops]
            dest_uvs.append(uvs)

        for suvs, duvs in zip(props.src_uvs, dest_uvs):
            src_diff = suvs[1] - suvs[0]
            dest_diff = duvs[1] - duvs[0]

            src_base = suvs[0]
            dest_base = duvs[0]

            src_rad = atan2(src_diff.y, src_diff.x)
            dest_rad = atan2(dest_diff.y, dest_diff.x)
            if src_rad < dest_rad:
                radian = dest_rad - src_rad
            elif src_rad > dest_rad:
                radian = math.pi * 2 - (src_rad - dest_rad)
            else:       # src_rad == dest_rad
                radian = 0.0

            ratio = dest_diff.length / src_diff.length
            break

        for suvs, fidx in zip(props.src_uvs, dest_face_indices):
            for l, suv in zip(bm.faces[fidx].loops, suvs):
                base = suv - src_base
                radian_ref = atan2(base.y, base.x)
                radian_fin = (radian + radian_ref)
                length = base.length
                turn = Vector((length * cos(radian_fin),
                               length * sin(radian_fin)))
                target_uv = Vector((turn.x * ratio, turn.y * ratio)) + \
                    dest_base
                l[uv_layer].uv = target_uv

        bmesh.update_edit_mesh(obj.data)

        return {'FINISHED'}
