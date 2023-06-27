# SPDX-FileCopyrightText: 2018-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.6"
__date__ = "22 Apr 2022"

import bpy

from ..op.align_uv_cursor import MUV_OT_AlignUVCursor
from ..op.uv_bounding_box import (
    MUV_OT_UVBoundingBox,
)
from ..op.uv_inspection import (
    MUV_OT_UVInspection_Render,
    MUV_OT_UVInspection_Update,
    MUV_OT_UVInspection_PaintUVIsland,
)
from ..utils.bl_class_registry import BlClassRegistry
from ..utils import compatibility as compat


@BlClassRegistry()
@compat.ChangeRegionType(region_type='TOOLS')
class MUV_PT_UVEdit_EditorEnhancement(bpy.types.Panel):
    """
    Panel class: UV/Image Editor Enhancement
    """

    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_label = "Editor Enhancement"
    bl_category = "Magic UV"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, _):
        layout = self.layout
        layout.label(text="", icon=compat.icon('IMAGE'))

    def draw(self, context):
        layout = self.layout
        sc = context.scene

        box = layout.box()
        box.prop(sc, "muv_align_uv_cursor_enabled", text="Align UV Cursor")
        if sc.muv_align_uv_cursor_enabled:
            box.prop(sc, "muv_align_uv_cursor_align_method", expand=True)

            col = box.column(align=True)

            row = col.row(align=True)
            ops = row.operator(MUV_OT_AlignUVCursor.bl_idname, text="Left Top")
            ops.position = 'LEFT_TOP'
            ops.base = sc.muv_align_uv_cursor_align_method
            ops = row.operator(MUV_OT_AlignUVCursor.bl_idname,
                               text="Middle Top")
            ops.position = 'MIDDLE_TOP'
            ops.base = sc.muv_align_uv_cursor_align_method
            ops = row.operator(MUV_OT_AlignUVCursor.bl_idname,
                               text="Right Top")
            ops.position = 'RIGHT_TOP'
            ops.base = sc.muv_align_uv_cursor_align_method

            row = col.row(align=True)
            ops = row.operator(MUV_OT_AlignUVCursor.bl_idname,
                               text="Left Middle")
            ops.position = 'LEFT_MIDDLE'
            ops.base = sc.muv_align_uv_cursor_align_method
            ops = row.operator(MUV_OT_AlignUVCursor.bl_idname, text="Center")
            ops.position = 'CENTER'
            ops.base = sc.muv_align_uv_cursor_align_method
            ops = row.operator(MUV_OT_AlignUVCursor.bl_idname,
                               text="Right Middle")
            ops.position = 'RIGHT_MIDDLE'
            ops.base = sc.muv_align_uv_cursor_align_method

            row = col.row(align=True)
            ops = row.operator(MUV_OT_AlignUVCursor.bl_idname,
                               text="Left Bottom")
            ops.position = 'LEFT_BOTTOM'
            ops.base = sc.muv_align_uv_cursor_align_method
            ops = row.operator(MUV_OT_AlignUVCursor.bl_idname,
                               text="Middle Bottom")
            ops.position = 'MIDDLE_BOTTOM'
            ops.base = sc.muv_align_uv_cursor_align_method
            ops = row.operator(MUV_OT_AlignUVCursor.bl_idname,
                               text="Right Bottom")
            ops.position = 'RIGHT_BOTTOM'
            ops.base = sc.muv_align_uv_cursor_align_method

        box = layout.box()
        box.prop(sc, "muv_uv_cursor_location_enabled",
                 text="UV Cursor Location")
        if sc.muv_uv_cursor_location_enabled:
            box.prop(sc, "muv_align_uv_cursor_cursor_loc", text="")

        box = layout.box()
        box.prop(sc, "muv_uv_bounding_box_enabled", text="UV Bounding Box")
        if sc.muv_uv_bounding_box_enabled:
            box.prop(sc, "muv_uv_bounding_box_show",
                     text="Hide"
                     if MUV_OT_UVBoundingBox.is_running(context)
                     else "Show",
                     icon='RESTRICT_VIEW_OFF'
                     if MUV_OT_UVBoundingBox.is_running(context)
                     else 'RESTRICT_VIEW_ON')
            box.prop(sc, "muv_uv_bounding_box_uniform_scaling",
                     text="Uniform Scaling")
            box.prop(sc, "muv_uv_bounding_box_boundary", text="Boundary")

        box = layout.box()
        box.prop(sc, "muv_uv_inspection_enabled", text="UV Inspection")
        if sc.muv_uv_inspection_enabled:
            row = box.row()
            row.prop(
                sc, "muv_uv_inspection_show",
                text="Hide"
                if MUV_OT_UVInspection_Render.is_running(context)
                else "Show",
                icon='RESTRICT_VIEW_OFF'
                if MUV_OT_UVInspection_Render.is_running(context)
                else 'RESTRICT_VIEW_ON')
            row.operator(MUV_OT_UVInspection_Update.bl_idname, text="Update")
            row = box.row()
            row.prop(sc, "muv_uv_inspection_show_overlapped")
            row.prop(sc, "muv_uv_inspection_show_flipped")
            row = box.row()
            row.prop(sc, "muv_uv_inspection_display_in_v3d", text="3D")
            row.prop(sc, "muv_uv_inspection_show_mode")
            if sc.muv_uv_inspection_show_overlapped:
                row = box.row()
                row.prop(sc, "muv_uv_inspection_same_polygon_threshold")
            box.separator()
            box.operator(MUV_OT_UVInspection_PaintUVIsland.bl_idname)
