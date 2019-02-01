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

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.0"
__date__ = "26 Jan 2019"

import bpy
from bpy.props import BoolProperty
import bmesh

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
    idname = "select_uv"

    @classmethod
    def init_props(cls, scene):
        scene.muv_select_uv_enabled = BoolProperty(
            name="Select UV Enabled",
            description="Select UV is enabled",
            default=False
        )

    @classmethod
    def del_props(cls, scene):
        del scene.muv_select_uv_enabled


@BlClassRegistry()
class MUV_OT_SelectUV_SelectOverlapped(bpy.types.Operator):
    """
    Operation class: Select faces which have overlapped UVs
    """

    bl_idname = "uv.muv_ot_select_uv_select_overlapped"
    bl_label = "Overlapped"
    bl_description = "Select faces which have overlapped UVs"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return _is_valid_context(context)

    def execute(self, context):
        obj = context.active_object
        bm = bmesh.from_edit_mesh(obj.data)
        if common.check_version(2, 73, 0) >= 0:
            bm.faces.ensure_lookup_table()
        uv_layer = bm.loops.layers.uv.verify()

        if context.tool_settings.use_uv_select_sync:
            sel_faces = [f for f in bm.faces]
        else:
            sel_faces = [f for f in bm.faces if f.select]

        overlapped_info = common.get_overlapped_uv_info(bm, sel_faces,
                                                        uv_layer, 'FACE')

        for info in overlapped_info:
            if context.tool_settings.use_uv_select_sync:
                info["subject_face"].select = True
            else:
                for l in info["subject_face"].loops:
                    l[uv_layer].select = True

        bmesh.update_edit_mesh(obj.data)

        return {'FINISHED'}


@BlClassRegistry()
class MUV_OT_SelectUV_SelectFlipped(bpy.types.Operator):
    """
    Operation class: Select faces which have flipped UVs
    """

    bl_idname = "uv.muv_ot_select_uv_select_flipped"
    bl_label = "Flipped"
    bl_description = "Select faces which have flipped UVs"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return _is_valid_context(context)

    def execute(self, context):
        obj = context.active_object
        bm = bmesh.from_edit_mesh(obj.data)
        if common.check_version(2, 73, 0) >= 0:
            bm.faces.ensure_lookup_table()
        uv_layer = bm.loops.layers.uv.verify()

        if context.tool_settings.use_uv_select_sync:
            sel_faces = [f for f in bm.faces]
        else:
            sel_faces = [f for f in bm.faces if f.select]

        flipped_info = common.get_flipped_uv_info(sel_faces, uv_layer)

        for info in flipped_info:
            if context.tool_settings.use_uv_select_sync:
                info["face"].select = True
            else:
                for l in info["face"].loops:
                    l[uv_layer].select = True

        bmesh.update_edit_mesh(obj.data)

        return {'FINISHED'}
