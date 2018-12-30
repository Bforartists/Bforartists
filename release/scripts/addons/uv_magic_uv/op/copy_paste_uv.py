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

__author__ = "Nutti <nutti.metro@gmail.com>, Jace Priester"
__status__ = "production"
__version__ = "5.2"
__date__ = "17 Nov 2018"


import bmesh
import bpy.utils
from bpy.props import (
    StringProperty,
    BoolProperty,
    IntProperty,
    EnumProperty,
)

from ..impl import copy_paste_uv_impl as impl
from .. import common
from ..utils.bl_class_registry import BlClassRegistry
from ..utils.property_class_registry import PropertyClassRegistry

__all__ = [
    'Properties',
    'MUV_OT_CopyPasteUV_CopyUV',
    'MUV_MT_CopyPasteUV_CopyUV',
    'MUV_OT_CopyPasteUV_PasteUV',
    'MUV_MT_CopyPasteUV_PasteUV',
    'MUV_OT_CopyPasteUV_SelSeqCopyUV',
    'MUV_MT_CopyPasteUV_SelSeqCopyUV',
    'MUV_OT_CopyPasteUV_SelSeqPasteUV',
    'MUV_MT_CopyPasteUV_SelSeqPasteUV',
]


@PropertyClassRegistry()
class Properties:
    idname = "copy_paste_uv"

    @classmethod
    def init_props(cls, scene):
        class Props():
            src_info = None

        scene.muv_props.copy_paste_uv = Props()
        scene.muv_props.copy_paste_uv_selseq = Props()

        scene.muv_copy_paste_uv_enabled = BoolProperty(
            name="Copy/Paste UV Enabled",
            description="Copy/Paste UV is enabled",
            default=False
        )
        scene.muv_copy_paste_uv_copy_seams = BoolProperty(
            name="Seams",
            description="Copy Seams",
            default=True
        )
        scene.muv_copy_paste_uv_mode = EnumProperty(
            items=[
                ('DEFAULT', "Default", "Default Mode"),
                ('SEL_SEQ', "Selection Sequence", "Selection Sequence Mode")
            ],
            name="Copy/Paste UV Mode",
            description="Copy/Paste UV Mode",
            default='DEFAULT'
        )
        scene.muv_copy_paste_uv_strategy = EnumProperty(
            name="Strategy",
            description="Paste Strategy",
            items=[
                ('N_N', 'N:N', 'Number of faces must be equal to source'),
                ('N_M', 'N:M', 'Number of faces must not be equal to source')
            ],
            default='N_M'
        )

    @classmethod
    def del_props(cls, scene):
        del scene.muv_props.copy_paste_uv
        del scene.muv_props.copy_paste_uv_selseq
        del scene.muv_copy_paste_uv_enabled
        del scene.muv_copy_paste_uv_copy_seams
        del scene.muv_copy_paste_uv_mode
        del scene.muv_copy_paste_uv_strategy


@BlClassRegistry()
class MUV_OT_CopyPasteUV_CopyUV(bpy.types.Operator):
    """
    Operation class: Copy UV coordinate
    """

    bl_idname = "uv.muv_copy_paste_uv_operator_copy_uv"
    bl_label = "Copy UV"
    bl_description = "Copy UV coordinate"
    bl_options = {'REGISTER', 'UNDO'}

    uv_map: StringProperty(default="__default", options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return impl.is_valid_context(context)

    def execute(self, context):
        props = context.scene.muv_props.copy_paste_uv
        obj = context.active_object
        bm = common.create_bmesh(obj)

        # get UV layer
        uv_layers = impl.get_copy_uv_layers(self, bm, self.uv_map)
        if not uv_layers:
            return {'CANCELLED'}

        # get selected face
        src_info = impl.get_src_face_info(self, bm, uv_layers)
        if src_info is None:
            return {'CANCELLED'}
        props.src_info = src_info

        face_count = len(props.src_info[list(props.src_info.keys())[0]])
        self.report({'INFO'}, "{} face(s) are copied".format(face_count))

        return {'FINISHED'}


@BlClassRegistry()
class MUV_MT_CopyPasteUV_CopyUV(bpy.types.Menu):
    """
    Menu class: Copy UV coordinate
    """

    bl_idname = "uv.muv_copy_paste_uv_menu_copy_uv"
    bl_label = "Copy UV (Menu)"
    bl_description = "Menu of Copy UV coordinate"

    @classmethod
    def poll(cls, context):
        return impl.is_valid_context(context)

    def draw(self, context):
        layout = self.layout
        # create sub menu
        obj = context.active_object
        bm = common.create_bmesh(obj)
        uv_maps = bm.loops.layers.uv.keys()

        ops = layout.operator(MUV_OT_CopyPasteUV_CopyUV.bl_idname,
                              text="[Default]")
        ops.uv_map = "__default"

        ops = layout.operator(MUV_OT_CopyPasteUV_CopyUV.bl_idname,
                              text="[All]")
        ops.uv_map = "__all"

        for m in uv_maps:
            ops = layout.operator(MUV_OT_CopyPasteUV_CopyUV.bl_idname, text=m)
            ops.uv_map = m


@BlClassRegistry()
class MUV_OT_CopyPasteUV_PasteUV(bpy.types.Operator):
    """
    Operation class: Paste UV coordinate
    """

    bl_idname = "uv.muv_copy_paste_uv_operator_paste_uv"
    bl_label = "Paste UV"
    bl_description = "Paste UV coordinate"
    bl_options = {'REGISTER', 'UNDO'}

    uv_map: StringProperty(default="__default", options={'HIDDEN'})
    strategy: EnumProperty(
        name="Strategy",
        description="Paste Strategy",
        items=[
            ('N_N', 'N:N', 'Number of faces must be equal to source'),
            ('N_M', 'N:M', 'Number of faces must not be equal to source')
        ],
        default="N_M"
    )
    flip_copied_uv: BoolProperty(
        name="Flip Copied UV",
        description="Flip Copied UV...",
        default=False
    )
    rotate_copied_uv: IntProperty(
        default=0,
        name="Rotate Copied UV",
        min=0,
        max=30
    )
    copy_seams: BoolProperty(
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
        props = sc.muv_props.copy_paste_uv
        if not props.src_info:
            return False
        return impl.is_valid_context(context)

    def execute(self, context):
        props = context.scene.muv_props.copy_paste_uv
        if not props.src_info:
            self.report({'WARNING'}, "Need copy UV at first")
            return {'CANCELLED'}
        obj = context.active_object
        bm = common.create_bmesh(obj)

        # get UV layer
        uv_layers = impl.get_paste_uv_layers(self, obj, bm, props.src_info,
                                             self.uv_map)
        if not uv_layers:
            return {'CANCELLED'}

        # get selected face
        dest_info = impl.get_dest_face_info(self, bm, uv_layers,
                                            props.src_info, self.strategy)
        if dest_info is None:
            return {'CANCELLED'}

        # paste
        ret = impl.paste_uv(self, bm, props.src_info, dest_info, uv_layers,
                            self.strategy, self.flip_copied_uv,
                            self.rotate_copied_uv, self.copy_seams)
        if ret:
            return {'CANCELLED'}

        face_count = len(props.src_info[list(dest_info.keys())[0]])
        self.report({'INFO'}, "{} face(s) are pasted".format(face_count))

        bmesh.update_edit_mesh(obj.data)

        return {'FINISHED'}


@BlClassRegistry()
class MUV_MT_CopyPasteUV_PasteUV(bpy.types.Menu):
    """
    Menu class: Paste UV coordinate
    """

    bl_idname = "uv.muv_copy_paste_uv_menu_paste_uv"
    bl_label = "Paste UV (Menu)"
    bl_description = "Menu of Paste UV coordinate"

    @classmethod
    def poll(cls, context):
        sc = context.scene
        props = sc.muv_props.copy_paste_uv
        if not props.src_info:
            return False
        return impl.is_valid_context(context)

    def draw(self, context):
        sc = context.scene
        layout = self.layout
        # create sub menu
        obj = context.active_object
        bm = common.create_bmesh(obj)
        uv_maps = bm.loops.layers.uv.keys()

        ops = layout.operator(MUV_OT_CopyPasteUV_PasteUV.bl_idname,
                              text="[Default]")
        ops.uv_map = "__default"
        ops.copy_seams = sc.muv_copy_paste_uv_copy_seams
        ops.strategy = sc.muv_copy_paste_uv_strategy

        ops = layout.operator(MUV_OT_CopyPasteUV_PasteUV.bl_idname,
                              text="[New]")
        ops.uv_map = "__new"
        ops.copy_seams = sc.muv_copy_paste_uv_copy_seams
        ops.strategy = sc.muv_copy_paste_uv_strategy

        ops = layout.operator(MUV_OT_CopyPasteUV_PasteUV.bl_idname,
                              text="[All]")
        ops.uv_map = "__all"
        ops.copy_seams = sc.muv_copy_paste_uv_copy_seams
        ops.strategy = sc.muv_copy_paste_uv_strategy

        for m in uv_maps:
            ops = layout.operator(MUV_OT_CopyPasteUV_PasteUV.bl_idname, text=m)
            ops.uv_map = m
            ops.copy_seams = sc.muv_copy_paste_uv_copy_seams
            ops.strategy = sc.muv_copy_paste_uv_strategy


@BlClassRegistry()
class MUV_OT_CopyPasteUV_SelSeqCopyUV(bpy.types.Operator):
    """
    Operation class: Copy UV coordinate by selection sequence
    """

    bl_idname = "uv.muv_copy_paste_uv_operator_selseq_copy_uv"
    bl_label = "Copy UV (Selection Sequence)"
    bl_description = "Copy UV data by selection sequence"
    bl_options = {'REGISTER', 'UNDO'}

    uv_map: StringProperty(default="__default", options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return impl.is_valid_context(context)

    def execute(self, context):
        props = context.scene.muv_props.copy_paste_uv_selseq
        obj = context.active_object
        bm = common.create_bmesh(obj)

        # get UV layer
        uv_layers = impl.get_copy_uv_layers(self, bm, self.uv_map)
        if not uv_layers:
            return {'CANCELLED'}

        # get selected face
        src_info = impl.get_select_history_src_face_info(self, bm, uv_layers)
        if src_info is None:
            return {'CANCELLED'}
        props.src_info = src_info

        face_count = len(props.src_info[list(props.src_info.keys())[0]])
        self.report({'INFO'}, "{} face(s) are selected".format(face_count))

        return {'FINISHED'}


@BlClassRegistry()
class MUV_MT_CopyPasteUV_SelSeqCopyUV(bpy.types.Menu):
    """
    Menu class: Copy UV coordinate by selection sequence
    """

    bl_idname = "uv.muv_copy_paste_uv_menu_selseq_copy_uv"
    bl_label = "Copy UV (Selection Sequence) (Menu)"
    bl_description = "Menu of Copy UV coordinate by selection sequence"

    @classmethod
    def poll(cls, context):
        return impl.is_valid_context(context)

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        bm = common.create_bmesh(obj)
        uv_maps = bm.loops.layers.uv.keys()

        ops = layout.operator(MUV_OT_CopyPasteUV_SelSeqCopyUV.bl_idname,
                              text="[Default]")
        ops.uv_map = "__default"

        ops = layout.operator(MUV_OT_CopyPasteUV_SelSeqCopyUV.bl_idname,
                              text="[All]")
        ops.uv_map = "__all"

        for m in uv_maps:
            ops = layout.operator(MUV_OT_CopyPasteUV_SelSeqCopyUV.bl_idname,
                                  text=m)
            ops.uv_map = m


@BlClassRegistry()
class MUV_OT_CopyPasteUV_SelSeqPasteUV(bpy.types.Operator):
    """
    Operation class: Paste UV coordinate by selection sequence
    """

    bl_idname = "uv.muv_copy_paste_uv_operator_selseq_paste_uv"
    bl_label = "Paste UV (Selection Sequence)"
    bl_description = "Paste UV coordinate by selection sequence"
    bl_options = {'REGISTER', 'UNDO'}

    uv_map: StringProperty(default="__default", options={'HIDDEN'})
    strategy: EnumProperty(
        name="Strategy",
        description="Paste Strategy",
        items=[
            ('N_N', 'N:N', 'Number of faces must be equal to source'),
            ('N_M', 'N:M', 'Number of faces must not be equal to source')
        ],
        default="N_M"
    )
    flip_copied_uv: BoolProperty(
        name="Flip Copied UV",
        description="Flip Copied UV...",
        default=False
    )
    rotate_copied_uv: IntProperty(
        default=0,
        name="Rotate Copied UV",
        min=0,
        max=30
    )
    copy_seams: BoolProperty(
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
        props = sc.muv_props.copy_paste_uv_selseq
        if not props.src_info:
            return False
        return impl.is_valid_context(context)

    def execute(self, context):
        props = context.scene.muv_props.copy_paste_uv_selseq
        if not props.src_info:
            self.report({'WARNING'}, "Need copy UV at first")
            return {'CANCELLED'}
        obj = context.active_object
        bm = common.create_bmesh(obj)

        # get UV layer
        uv_layers = impl.get_paste_uv_layers(self, obj, bm, props.src_info,
                                             self.uv_map)
        if not uv_layers:
            return {'CANCELLED'}

        # get selected face
        dest_info = impl.get_select_history_dest_face_info(self, bm, uv_layers,
                                                           props.src_info,
                                                           self.strategy)
        if dest_info is None:
            return {'CANCELLED'}

        # paste
        ret = impl.paste_uv(self, bm, props.src_info, dest_info, uv_layers,
                            self.strategy, self.flip_copied_uv,
                            self.rotate_copied_uv, self.copy_seams)
        if ret:
            return {'CANCELLED'}

        face_count = len(props.src_info[list(dest_info.keys())[0]])
        self.report({'INFO'}, "{} face(s) are pasted".format(face_count))

        bmesh.update_edit_mesh(obj.data)

        return {'FINISHED'}


@BlClassRegistry()
class MUV_MT_CopyPasteUV_SelSeqPasteUV(bpy.types.Menu):
    """
    Menu class: Paste UV coordinate by selection sequence
    """

    bl_idname = "uv.muv_copy_paste_uv_menu_selseq_paste_uv"
    bl_label = "Paste UV (Selection Sequence) (Menu)"
    bl_description = "Menu of Paste UV coordinate by selection sequence"

    @classmethod
    def poll(cls, context):
        sc = context.scene
        props = sc.muv_props.copy_paste_uv_selseq
        if not props.src_uvs or not props.src_pin_uvs:
            return False
        return impl.is_valid_context(context)

    def draw(self, context):
        sc = context.scene
        layout = self.layout
        # create sub menu
        obj = context.active_object
        bm = common.create_bmesh(obj)
        uv_maps = bm.loops.layers.uv.keys()

        ops = layout.operator(MUV_OT_CopyPasteUV_SelSeqPasteUV.bl_idname,
                              text="[Default]")
        ops.uv_map = "__default"
        ops.copy_seams = sc.muv_copy_paste_uv_copy_seams
        ops.strategy = sc.muv_copy_paste_uv_strategy

        ops = layout.operator(MUV_OT_CopyPasteUV_SelSeqPasteUV.bl_idname,
                              text="[New]")
        ops.uv_map = "__new"
        ops.copy_seams = sc.muv_copy_paste_uv_copy_seams
        ops.strategy = sc.muv_copy_paste_uv_strategy

        ops = layout.operator(MUV_OT_CopyPasteUV_SelSeqPasteUV.bl_idname,
                              text="[All]")
        ops.uv_map = "__all"
        ops.copy_seams = sc.muv_copy_paste_uv_copy_seams
        ops.strategy = sc.muv_copy_paste_uv_strategy

        for m in uv_maps:
            ops = layout.operator(MUV_OT_CopyPasteUV_SelSeqPasteUV.bl_idname,
                                  text=m)
            ops.uv_map = m
            ops.copy_seams = sc.muv_copy_paste_uv_copy_seams
            ops.strategy = sc.muv_copy_paste_uv_strategy
