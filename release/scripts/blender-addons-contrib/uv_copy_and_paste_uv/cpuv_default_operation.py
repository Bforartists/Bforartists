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

import bpy
from bpy.props import BoolProperty, IntProperty
from . import cpuv_common

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "3.2"
__date__ = "20 Jun 2015"


# copy UV
class CPUVCopyUV(bpy.types.Operator):
    """Copying UV coordinate on selected object."""

    bl_idname = "uv.cpuv_copy_uv"
    bl_label = "Copy UV"
    bl_description = "Copy UV data"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.cpuv_props.default
        self.report({'INFO'}, "Copy UV coordinate.")
        mem = cpuv_common.View3DModeMemory(context)

        # prepare for coping
        ret, props.src_obj = cpuv_common.prep_copy(context, self)
        if ret != 0:
            return {'CANCELLED'}
        # copy
        props.src_faces = cpuv_common.get_selected_faces(
            context, props.src_obj)
        ret, props.src_uv_map = cpuv_common.copy_opt(
            self, "", props.src_obj, props.src_faces)
        if ret != 0:
            return {'CANCELLED'}
        # finish coping
        cpuv_common.fini_copy()

        return {'FINISHED'}


# paste UV
class CPUVPasteUV(bpy.types.Operator):
    """Paste UV coordinate which is copied."""

    bl_idname = "uv.cpuv_paste_uv"
    bl_label = "Paste UV"
    bl_description = "Paste UV data"
    bl_options = {'REGISTER', 'UNDO'}

    flip_copied_uv = BoolProperty(
        name="Flip Copied UV",
        description="Flip Copied UV...",
        default=False)

    rotate_copied_uv = IntProperty(
        default=0,
        name="Rotate Copied UV",
        min=0,
        max=30)

    def execute(self, context):
        props = context.scene.cpuv_props.default
        self.report({'INFO'}, "Paste UV coordinate.")
        mem = cpuv_common.View3DModeMemory(context)

        # prepare for pasting
        ret, dest_obj = cpuv_common.prep_paste(
            context, self, props.src_obj, props.src_faces)
        if ret != 0:
            return {'CANCELLED'}
        # paste
        dest_faces = cpuv_common.get_selected_faces(context, dest_obj)
        ret = cpuv_common.paste_opt(
            context, self, "", props.src_obj, props.src_faces,
            props.src_uv_map, dest_obj, dest_faces)
        if ret != 0:
            return {'CANCELLED'}
        # finish pasting
        cpuv_common.fini_paste()

        return {'FINISHED'}
