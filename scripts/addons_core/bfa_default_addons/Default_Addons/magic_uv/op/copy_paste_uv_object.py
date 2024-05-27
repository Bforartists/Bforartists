# SPDX-FileCopyrightText: 2018-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.6"
__date__ = "22 Apr 2022"

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
    # only 'VIEW_3D' space is allowed to execute
    if not common.is_valid_space(context, ['VIEW_3D']):
        return False

    # Only object mode is allowed to execute.
    ob = context.object
    if ob is not None and ob.mode != 'OBJECT':
        return False

    # Multiple objects editing mode is not supported in this feature.
    objs = common.get_uv_editable_objects(context)
    if len(objs) != 1:
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

        objs = common.get_uv_editable_objects(context)
        # poll() method ensures that only one object is selected.
        obj = objs[0]
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

    def draw(self, context):
        layout = self.layout
        objs = common.get_uv_editable_objects(context)
        # poll() method ensures that only one object is selected.
        obj = objs[0]

        # create sub menu
        uv_maps = compat.get_object_uv_layers(obj).keys()

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

        objs = common.get_uv_editable_objects(context)
        for o in objs:
            if not compat.object_has_uv_layers(o):
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
        objs = common.get_uv_editable_objects(context)
        for obj in objs:
            if not compat.object_has_uv_layers(obj):
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
