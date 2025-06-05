# SPDX-FileCopyrightText: 2018-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.6"
__date__ = "22 Apr 2022"

import bpy

from ..op.copy_paste_uv_uvedit import (
    MUV_OT_CopyPasteUVUVEdit_CopyUV,
    MUV_OT_CopyPasteUVUVEdit_PasteUV,
    MUV_OT_CopyPasteUVUVEdit_CopyUVIsland,
    MUV_OT_CopyPasteUVUVEdit_PasteUVIsland,
)
from ..op.align_uv_cursor import MUV_OT_AlignUVCursor
from ..op.align_uv import (
    MUV_OT_AlignUV_Circle,
    MUV_OT_AlignUV_Straighten,
    MUV_OT_AlignUV_Axis,
    MUV_OT_AlignUV_SnapToPoint,
    MUV_OT_AlignUV_SnapToEdge,
)
from ..op.select_uv import (
    MUV_OT_SelectUV_SelectOverlapped,
    MUV_OT_SelectUV_SelectFlipped,
)
from ..op.uv_inspection import (
    MUV_OT_UVInspection_Update,
    MUV_OT_UVInspection_PaintUVIsland,
)
from ..utils.bl_class_registry import BlClassRegistry


@BlClassRegistry()
class MUV_MT_CopyPasteUV_UVEdit(bpy.types.Menu):
    """
    Menu class: Master menu of Copy/Paste UV coordinate on UV/ImageEditor
    """

    bl_idname = "MUV_MT_CopyPasteUV_UVEdit"
    bl_label = "Copy/Paste UV"
    bl_description = "Copy and Paste UV coordinate among object"

    def draw(self, context):
        layout = self.layout
        sc = context.scene

        layout.label(text="Face")
        layout.operator(MUV_OT_CopyPasteUVUVEdit_CopyUV.bl_idname, text="Copy")
        layout.operator(MUV_OT_CopyPasteUVUVEdit_PasteUV.bl_idname,
                        text="Paste")

        layout.label(text="Island")
        layout.operator(MUV_OT_CopyPasteUVUVEdit_CopyUVIsland.bl_idname,
                        text="Copy")
        ops = layout.operator(MUV_OT_CopyPasteUVUVEdit_PasteUVIsland.bl_idname,
                              text="Paste")
        ops.unique_target = sc.muv_copy_paste_uv_uvedit_unique_target


@BlClassRegistry()
class MUV_MT_AlignUV(bpy.types.Menu):
    """
    Menu class: Master menu of Align UV
    """

    bl_idname = "MUV_MT_AlignUV"
    bl_label = "Align UV"
    bl_description = "Align UV"

    def draw(self, context):
        layout = self.layout
        sc = context.scene

        layout.label(text="Align")

        ops = layout.operator(MUV_OT_AlignUV_Circle.bl_idname, text="Circle")
        ops.transmission = sc.muv_align_uv_transmission
        ops.select = sc.muv_align_uv_select

        ops = layout.operator(MUV_OT_AlignUV_Straighten.bl_idname,
                              text="Straighten")
        ops.transmission = sc.muv_align_uv_transmission
        ops.select = sc.muv_align_uv_select
        ops.vertical = sc.muv_align_uv_vertical
        ops.horizontal = sc.muv_align_uv_horizontal

        ops = layout.operator(MUV_OT_AlignUV_Axis.bl_idname, text="XY-axis")
        ops.transmission = sc.muv_align_uv_transmission
        ops.select = sc.muv_align_uv_select
        ops.vertical = sc.muv_align_uv_vertical
        ops.horizontal = sc.muv_align_uv_horizontal
        ops.location = sc.muv_align_uv_location

        layout.label(text="Snap")

        ops = layout.operator(MUV_OT_AlignUV_SnapToPoint.bl_idname,
                              text="Snap to Point")
        ops.group = sc.muv_align_uv_snap_point_group
        ops.target = sc.muv_align_uv_snap_point_target

        ops = layout.operator(MUV_OT_AlignUV_SnapToEdge.bl_idname,
                              text="Snap to Edge")
        ops.group = sc.muv_align_uv_snap_edge_group
        ops.target_1 = sc.muv_align_uv_snap_edge_target_1
        ops.target_2 = sc.muv_align_uv_snap_edge_target_2


@BlClassRegistry()
class MUV_MT_SelectUV(bpy.types.Menu):
    """
    Menu class: Master menu of Select UV
    """

    bl_idname = "MUV_MT_SelectUV"
    bl_label = "Select UV"
    bl_description = "Select UV"

    def draw(self, context):
        sc = context.scene
        layout = self.layout

        ops = layout.operator(MUV_OT_SelectUV_SelectOverlapped.bl_idname,
                              text="Overlapped")
        MUV_OT_SelectUV_SelectOverlapped.setup_argument(ops, sc)
        ops = layout.operator(MUV_OT_SelectUV_SelectFlipped.bl_idname,
                              text="Flipped")
        MUV_OT_SelectUV_SelectFlipped.setup_argument(ops, sc)


@BlClassRegistry()
class MUV_MT_AlignUVCursor(bpy.types.Menu):
    """
    Menu class: Master menu of Align UV Cursor
    """

    bl_idname = "MUV_MT_AlignUVCursor"
    bl_label = "Align UV Cursor"
    bl_description = "Align UV cursor"

    def draw(self, context):
        layout = self.layout
        sc = context.scene

        ops = layout.operator(MUV_OT_AlignUVCursor.bl_idname, text="Left Top")
        ops.position = 'LEFT_TOP'
        ops.base = sc.muv_align_uv_cursor_align_method

        ops = layout.operator(MUV_OT_AlignUVCursor.bl_idname,
                              text="Middle Top")
        ops.position = 'MIDDLE_TOP'
        ops.base = sc.muv_align_uv_cursor_align_method

        ops = layout.operator(MUV_OT_AlignUVCursor.bl_idname, text="Right Top")
        ops.position = 'RIGHT_TOP'
        ops.base = sc.muv_align_uv_cursor_align_method

        ops = layout.operator(MUV_OT_AlignUVCursor.bl_idname,
                              text="Left Middle")
        ops.position = 'LEFT_MIDDLE'
        ops.base = sc.muv_align_uv_cursor_align_method

        ops = layout.operator(MUV_OT_AlignUVCursor.bl_idname, text="Center")
        ops.position = 'CENTER'
        ops.base = sc.muv_align_uv_cursor_align_method

        ops = layout.operator(MUV_OT_AlignUVCursor.bl_idname,
                              text="Right Middle")
        ops.position = 'RIGHT_MIDDLE'
        ops.base = sc.muv_align_uv_cursor_align_method

        ops = layout.operator(MUV_OT_AlignUVCursor.bl_idname,
                              text="Left Bottom")
        ops.position = 'LEFT_BOTTOM'
        ops.base = sc.muv_align_uv_cursor_align_method

        ops = layout.operator(MUV_OT_AlignUVCursor.bl_idname,
                              text="Middle Bottom")
        ops.position = 'MIDDLE_BOTTOM'
        ops.base = sc.muv_align_uv_cursor_align_method

        ops = layout.operator(MUV_OT_AlignUVCursor.bl_idname,
                              text="Right Bottom")
        ops.position = 'RIGHT_BOTTOM'
        ops.base = sc.muv_align_uv_cursor_align_method


@BlClassRegistry()
class MUV_MT_UVInspection(bpy.types.Menu):
    """
    Menu class: Master menu of UV Inspection
    """

    bl_idname = "MUV_MT_UVInspection"
    bl_label = "UV Inspection"
    bl_description = "UV Inspection"

    def draw(self, context):
        layout = self.layout
        sc = context.scene

        layout.prop(sc, "muv_uv_inspection_show",
                    text="Show Overlapped/Flipped")
        layout.operator(MUV_OT_UVInspection_Update.bl_idname, text="Update")
        layout.separator()
        layout.operator(MUV_OT_UVInspection_PaintUVIsland.bl_idname)
