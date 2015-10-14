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
from bpy.props import StringProperty, BoolProperty, IntProperty
from . import cpuv_common

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "3.2"
__date__ = "20 Jun 2015"


# copy UV map (sub menu operator)
class CPUVUVMapCopyUVOperation(bpy.types.Operator):
    bl_idname = "uv.cpuv_uvmap_copy_uv_op"
    bl_label = "Copy UV Map (Sub Menu Operator)"
    uv_map = bpy.props.StringProperty()

    def execute(self, context):
        props = context.scene.cpuv_props.uvmap
        self.report(
            {'INFO'},
            "Copy UV coordinate. (UV map:" + self.uv_map + ")")
        mem = cpuv_common.View3DModeMemory(context)

        # prepare for coping
        ret, props.src_obj = cpuv_common.prep_copy(context, self)
        if ret != 0:
            return {'CANCELLED'}
        # copy
        props.src_faces = cpuv_common.get_selected_faces(
            context, props.src_obj)
        ret, props.src_uv_map = cpuv_common.copy_opt(
            self, self.uv_map, props.src_obj, props.src_faces)
        if ret != 0:
            return {'CANCELLED'}
        # finish coping
        cpuv_common.fini_copy()

        return {'FINISHED'}


# copy UV map
class CPUVUVMapCopyUV(bpy.types.Menu):
    """Copying UV map coordinate on selected object."""

    bl_idname = "uv.cpuv_uvmap_copy_uv"
    bl_label = "Copy UV Map"
    bl_description = "Copy UV map data"
    bl_options = {'REGISTER', 'UNDO'}

    def draw(self, context):
        layout = self.layout
        # create sub menu
        uv_maps = context.active_object.data.uv_textures.keys()
        for m in uv_maps:
            layout.operator(
                CPUVUVMapCopyUVOperation.bl_idname,
                text=m).uv_map = m


# paste UV map (sub menu operator)
class CPUVUVMapPasteUVOperation(bpy.types.Operator):
    bl_idname = "uv.cpuv_uvmap_paste_uv_op"
    bl_label = "Paste UV Map (Sub Menu Operator)"
    uv_map = bpy.props.StringProperty()

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
        props = context.scene.cpuv_props.uvmap
        self.report(
            {'INFO'}, "Paste UV coordinate. (UV map:" + self.uv_map + ")")
        mem = cpuv_common.View3DModeMemory(context)

        # prepare for pasting
        ret, dest_obj = cpuv_common.prep_paste(
            context, self, props.src_obj, props.src_faces)
        if ret != 0:
            return {'CANCELLED'}
        # paste
        dest_faces = cpuv_common.get_selected_faces(context, dest_obj)
        cpuv_common.paste_opt(
            context, self, self.uv_map, props.src_obj, props.src_faces,
            props.src_uv_map, dest_obj, dest_faces)
        if ret != 0:
            return {'CANCELLED'}
        # finish pasting
        cpuv_common.fini_paste()

        return {'FINISHED'}


# paste UV map
class CPUVUVMapPasteUV(bpy.types.Menu):
    """Copying UV map coordinate on selected object."""

    bl_idname = "uv.cpuv_uvmap_paste_uv"
    bl_label = "Paste UV Map"
    bl_description = "Paste UV map data"
    bl_options = {'REGISTER', 'UNDO'}

    def draw(self, context):
        layout = self.layout
        # create sub menu
        uv_maps = context.active_object.data.uv_textures.keys()
        for m in uv_maps:
            layout.operator(
                CPUVUVMapPasteUVOperation.bl_idname,
                text=m).uv_map = m
