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
__version__ = "6.2"
__date__ = "31 Jul 2019"

import bmesh
import bpy
from bpy.props import (
    StringProperty,
    BoolProperty,
)

from .copy_paste_uv import (
    get_copy_uv_layers,
    get_src_face_info,
    get_paste_uv_layers,
    get_dest_face_info,
    paste_uv,
)
from .. import common
from ..utils.bl_class_registry import BlClassRegistry
from ..utils.property_class_registry import PropertyClassRegistry
from ..utils import compatibility as compat


def _is_valid_context(context):
    obj = context.object

    # only object mode is allowed to execute
    if obj is None:
        return False
    if obj.type != 'MESH':
        return False
    if context.object.mode != 'OBJECT':
        return False

    # only 'VIEW_3D' space is allowed to execute
    for space in context.area.spaces:
        if space.type == 'VIEW_3D':
            break
    else:
        return False

    return True


@PropertyClassRegistry()
class _Properties:
    idname = "copy_paste_uv_object"

    @classmethod
    def init_props(cls, scene):
        class Props():
            src_info = None

        scene.muv_props.copy_paste_uv_object = Props()

        scene.muv_copy_paste_uv_object_copy_seams = BoolProperty(
            name="Seams",
            description="Copy Seams",
            default=True
        )

    @classmethod
    def del_props(cls, scene):
        del scene.muv_props.copy_paste_uv_object
        del scene.muv_copy_paste_uv_object_copy_seams


def memorize_view_3d_mode(fn):
    def __memorize_view_3d_mode(self, context):
        mode_orig = bpy.context.object.mode
        result = fn(self, context)
        bpy.ops.object.mode_set(mode=mode_orig)
        return result
    return __memorize_view_3d_mode


@BlClassRegistry()
@compat.make_annotations
class MUV_OT_CopyPasteUVObject_CopyUV(bpy.types.Operator):
    """
    Operation class: Copy UV coordinate among objects
    """

    bl_idname = "object.muv_copy_paste_uv_object_copy_uv"
    bl_label = "Copy UV (Among Objects)"
    bl_description = "Copy UV coordinate (Among Objects)"
    bl_options = {'REGISTER', 'UNDO'}

    uv_map = StringProperty(default="__default", options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return _is_valid_context(context)

    @memorize_view_3d_mode
    def execute(self, context):
        props = context.scene.muv_props.copy_paste_uv_object
        bpy.ops.object.mode_set(mode='EDIT')
        obj = context.active_object
        bm = common.create_bmesh(obj)

        # get UV layer
        uv_layers = get_copy_uv_layers(self, bm, self.uv_map)
        if not uv_layers:
            return {'CANCELLED'}

        # get selected face
        src_info = get_src_face_info(self, bm, uv_layers)
        if src_info is None:
            return {'CANCELLED'}
        props.src_info = src_info

        self.report({'INFO'},
                    "{}'s UV coordinates are copied".format(obj.name))

        return {'FINISHED'}


@BlClassRegistry()
class MUV_MT_CopyPasteUVObject_CopyUV(bpy.types.Menu):
    """
    Menu class: Copy UV coordinate among objects
    """

    bl_idname = "MUV_MT_CopyPasteUVObject_CopyUV"
    bl_label = "Copy UV (Among Objects) (Menu)"
    bl_description = "Menu of Copy UV coordinate (Among Objects)"

    @classmethod
    def poll(cls, context):
        return _is_valid_context(context)

    def draw(self, _):
        layout = self.layout
        # create sub menu
        uv_maps = compat.get_object_uv_layers(bpy.context.active_object).keys()

        ops = layout.operator(MUV_OT_CopyPasteUVObject_CopyUV.bl_idname,
                              text="[Default]")
        ops.uv_map = "__default"

        ops = layout.operator(MUV_OT_CopyPasteUVObject_CopyUV.bl_idname,
                              text="[All]")
        ops.uv_map = "__all"

        for m in uv_maps:
            ops = layout.operator(MUV_OT_CopyPasteUVObject_CopyUV.bl_idname,
                                  text=m)
            ops.uv_map = m


@BlClassRegistry()
@compat.make_annotations
class MUV_OT_CopyPasteUVObject_PasteUV(bpy.types.Operator):
    """
    Operation class: Paste UV coordinate among objects
    """

    bl_idname = "object.muv_copy_paste_uv_object_paste_uv"
    bl_label = "Paste UV (Among Objects)"
    bl_description = "Paste UV coordinate (Among Objects)"
    bl_options = {'REGISTER', 'UNDO'}

    uv_map = StringProperty(default="__default", options={'HIDDEN'})
    copy_seams = BoolProperty(
        name="Seams",
        description="Copy Seams",
        default=True
    )

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        sc = context.scene
        props = sc.muv_props.copy_paste_uv_object
        if not props.src_info:
            return False
        return _is_valid_context(context)

    @memorize_view_3d_mode
    def execute(self, context):
        props = context.scene.muv_props.copy_paste_uv_object
        if not props.src_info:
            self.report({'WARNING'}, "Need copy UV at first")
            return {'CANCELLED'}

        for o in bpy.data.objects:
            if not compat.object_has_uv_layers(o):
                continue
            if not compat.get_object_select(o):
                continue

            bpy.ops.object.mode_set(mode='OBJECT')
            compat.set_active_object(o)
            bpy.ops.object.mode_set(mode='EDIT')

            obj = context.active_object
            bm = common.create_bmesh(obj)

            # get UV layer
            uv_layers = get_paste_uv_layers(self, obj, bm, props.src_info,
                                            self.uv_map)
            if not uv_layers:
                return {'CANCELLED'}

            # get selected face
            dest_info = get_dest_face_info(self, bm, uv_layers,
                                           props.src_info, 'N_N')
            if dest_info is None:
                return {'CANCELLED'}

            # paste
            ret = paste_uv(self, bm, props.src_info, dest_info, uv_layers,
                           'N_N', 0, 0, self.copy_seams)
            if ret:
                return {'CANCELLED'}

            bmesh.update_edit_mesh(obj.data)

            if compat.check_version(2, 80, 0) < 0:
                if self.copy_seams is True:
                    obj.data.show_edge_seams = True

            self.report(
                {'INFO'}, "{}'s UV coordinates are pasted".format(obj.name))

        return {'FINISHED'}


@BlClassRegistry()
class MUV_MT_CopyPasteUVObject_PasteUV(bpy.types.Menu):
    """
    Menu class: Paste UV coordinate among objects
    """

    bl_idname = "MUV_MT_CopyPasteUVObject_PasteUV"
    bl_label = "Paste UV (Among Objects) (Menu)"
    bl_description = "Menu of Paste UV coordinate (Among Objects)"

    @classmethod
    def poll(cls, context):
        sc = context.scene
        props = sc.muv_props.copy_paste_uv_object
        if not props.src_info:
            return False
        return _is_valid_context(context)

    def draw(self, context):
        sc = context.scene
        layout = self.layout
        # create sub menu
        uv_maps = []
        for obj in bpy.data.objects:
            if not compat.object_has_uv_layers(obj):
                continue
            if not compat.get_object_select(obj):
                continue
            uv_maps.extend(compat.get_object_uv_layers(obj).keys())

        ops = layout.operator(MUV_OT_CopyPasteUVObject_PasteUV.bl_idname,
                              text="[Default]")
        ops.uv_map = "__default"
        ops.copy_seams = sc.muv_copy_paste_uv_object_copy_seams

        ops = layout.operator(MUV_OT_CopyPasteUVObject_PasteUV.bl_idname,
                              text="[New]")
        ops.uv_map = "__new"
        ops.copy_seams = sc.muv_copy_paste_uv_object_copy_seams

        ops = layout.operator(MUV_OT_CopyPasteUVObject_PasteUV.bl_idname,
                              text="[All]")
        ops.uv_map = "__all"
        ops.copy_seams = sc.muv_copy_paste_uv_object_copy_seams

        for m in uv_maps:
            ops = layout.operator(MUV_OT_CopyPasteUVObject_PasteUV.bl_idname,
                                  text=m)
            ops.uv_map = m
            ops.copy_seams = sc.muv_copy_paste_uv_object_copy_seams
