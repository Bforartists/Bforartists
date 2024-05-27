# SPDX-FileCopyrightText: 2018-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.6"
__date__ = "22 Apr 2022"

import bpy

from ..op.align_uv import (
    MUV_OT_AlignUV_Circle,
    MUV_OT_AlignUV_Straighten,
    MUV_OT_AlignUV_Axis,
    MUV_OT_AlignUV_SnapToPoint,
    MUV_OT_AlignUV_Snap_SetPointTargetToCursor,
    MUV_OT_AlignUV_Snap_SetPointTargetToVertexGroup,
    MUV_OT_AlignUV_SnapToEdge,
    MUV_OT_AlignUV_Snap_SetEdgeTargetToEdgeCenter,
)
from ..op.smooth_uv import (
    MUV_OT_SmoothUV,
)
from ..op.select_uv import (
    MUV_OT_SelectUV_SelectOverlapped,
    MUV_OT_SelectUV_SelectFlipped,
    MUV_OT_SelectUV_ZoomSelectedUV,
)
from ..op.pack_uv import MUV_OT_PackUV
from ..op.clip_uv import MUV_OT_ClipUV
from ..utils.bl_class_registry import BlClassRegistry
from ..utils import compatibility as compat


@BlClassRegistry()
@compat.ChangeRegionType(region_type='TOOLS')
class MUV_PT_UVEdit_UVManipulation(bpy.types.Panel):
    """
    Panel class: UV Manipulation on Property Panel on UV/ImageEditor
    """

    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_label = "UV Manipulation"
    bl_category = "Magic UV"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, _):
        layout = self.layout
        layout.label(text="", icon=compat.icon('IMAGE'))

    def draw(self, context):
        sc = context.scene
        layout = self.layout

        box = layout.box()
        box.prop(sc, "muv_align_uv_enabled", text="Align UV")
        if sc.muv_align_uv_enabled:
            box.label(text="Align:")

            col = box.column()
            row = col.row(align=True)
            ops = row.operator(MUV_OT_AlignUV_Circle.bl_idname, text="Circle")
            ops.transmission = sc.muv_align_uv_transmission
            ops.select = sc.muv_align_uv_select
            ops = row.operator(MUV_OT_AlignUV_Straighten.bl_idname,
                               text="Straighten")
            ops.transmission = sc.muv_align_uv_transmission
            ops.select = sc.muv_align_uv_select
            ops.vertical = sc.muv_align_uv_vertical
            ops.horizontal = sc.muv_align_uv_horizontal
            ops.mesh_infl = sc.muv_align_uv_mesh_infl
            row = col.row()
            ops = row.operator(MUV_OT_AlignUV_Axis.bl_idname, text="XY-axis")
            ops.transmission = sc.muv_align_uv_transmission
            ops.select = sc.muv_align_uv_select
            ops.vertical = sc.muv_align_uv_vertical
            ops.horizontal = sc.muv_align_uv_horizontal
            ops.location = sc.muv_align_uv_location
            ops.mesh_infl = sc.muv_align_uv_mesh_infl
            row.prop(sc, "muv_align_uv_location", text="")

            col = box.column(align=True)
            row = col.row(align=True)
            row.prop(sc, "muv_align_uv_transmission", text="Transmission")
            row.prop(sc, "muv_align_uv_select", text="Select")
            row = col.row(align=True)
            row.prop(sc, "muv_align_uv_vertical", text="Vertical")
            row.prop(sc, "muv_align_uv_horizontal", text="Horizontal")
            col.prop(sc, "muv_align_uv_mesh_infl", text="Mesh Influence")

            box.separator()

            sp = compat.layout_split(box, factor=0.5)
            sp.label(text="Snap:")
            sp = compat.layout_split(sp, factor=1.0)
            sp.prop(sc, "muv_align_uv_snap_method", text="")

            if sc.muv_align_uv_snap_method == 'POINT':
                row = box.row(align=True)
                ops = row.operator(MUV_OT_AlignUV_SnapToPoint.bl_idname,
                                   text="Snap to Point")
                ops.group = sc.muv_align_uv_snap_point_group
                ops.target = sc.muv_align_uv_snap_point_target

                col = box.column(align=True)
                row = col.row(align=True)
                row.prop(sc, "muv_align_uv_snap_point_group", text="Group")

                col.label(text="Target Point:")
                row = col.row(align=True)
                row.prop(sc, "muv_align_uv_snap_point_target", text="")
                row.operator(
                    MUV_OT_AlignUV_Snap_SetPointTargetToCursor.bl_idname,
                    text="", icon=compat.icon('CURSOR'))
                row.operator(
                    MUV_OT_AlignUV_Snap_SetPointTargetToVertexGroup.bl_idname,
                    text="", icon=compat.icon('UV_VERTEXSEL'))

            elif sc.muv_align_uv_snap_method == 'EDGE':
                row = box.row(align=True)
                ops = row.operator(MUV_OT_AlignUV_SnapToEdge.bl_idname,
                                   text="Snap to Edge")
                ops.group = sc.muv_align_uv_snap_edge_group
                ops.target_1 = sc.muv_align_uv_snap_edge_target_1
                ops.target_2 = sc.muv_align_uv_snap_edge_target_2

                col = box.column(align=True)
                row = col.row(align=True)
                row.prop(sc, "muv_align_uv_snap_edge_group", text="Group")

                col.label(text="Target Edge:")
                sp = compat.layout_split(col, factor=0.33)
                subcol = sp.column()
                subcol.label(text="Vertex 1:")
                subcol.prop(sc, "muv_align_uv_snap_edge_target_1", text="")
                sp = compat.layout_split(sp, factor=0.5)
                subcol = sp.column()
                subcol.label(text="Vertex 2:")
                subcol.prop(sc, "muv_align_uv_snap_edge_target_2", text="")
                sp = compat.layout_split(sp, factor=1.0)
                sp.operator(
                    MUV_OT_AlignUV_Snap_SetEdgeTargetToEdgeCenter.bl_idname,
                    text="", icon=compat.icon('UV_EDGESEL'))

        box = layout.box()
        box.prop(sc, "muv_smooth_uv_enabled", text="Smooth UV")
        if sc.muv_smooth_uv_enabled:
            ops = box.operator(MUV_OT_SmoothUV.bl_idname, text="Smooth")
            ops.transmission = sc.muv_smooth_uv_transmission
            ops.select = sc.muv_smooth_uv_select
            ops.mesh_infl = sc.muv_smooth_uv_mesh_infl
            col = box.column(align=True)
            row = col.row(align=True)
            row.prop(sc, "muv_smooth_uv_transmission", text="Transmission")
            row.prop(sc, "muv_smooth_uv_select", text="Select")
            col.prop(sc, "muv_smooth_uv_mesh_infl", text="Mesh Influence")

        box = layout.box()
        box.prop(sc, "muv_select_uv_enabled", text="Select UV")
        if sc.muv_select_uv_enabled:
            row = box.row(align=True)
            ops = row.operator(MUV_OT_SelectUV_SelectOverlapped.bl_idname)
            MUV_OT_SelectUV_SelectOverlapped.setup_argument(ops, sc)
            ops = row.operator(MUV_OT_SelectUV_SelectFlipped.bl_idname)
            MUV_OT_SelectUV_SelectFlipped.setup_argument(ops, sc)

            col = box.column()
            col.label(text="Same Polygon Threshold:")
            col.prop(sc, "muv_select_uv_same_polygon_threshold", text="")
            col.prop(sc, "muv_select_uv_selection_method")
            col.prop(sc, "muv_select_uv_sync_mesh_selection")

            box.separator()

            box.operator(MUV_OT_SelectUV_ZoomSelectedUV.bl_idname)

        box = layout.box()
        box.prop(sc, "muv_pack_uv_enabled", text="Pack UV (Extension)")
        if sc.muv_pack_uv_enabled:
            ops = box.operator(MUV_OT_PackUV.bl_idname, text="Pack UV")
            ops.allowable_center_deviation = \
                sc.muv_pack_uv_allowable_center_deviation
            ops.allowable_size_deviation = \
                sc.muv_pack_uv_allowable_size_deviation
            ops.accurate_island_copy = \
                sc.muv_pack_uv_accurate_island_copy
            ops.stride = sc.muv_pack_uv_stride
            ops.apply_pack_uv = sc.muv_pack_uv_apply_pack_uv
            box.prop(sc, "muv_pack_uv_apply_pack_uv")
            box.prop(sc, "muv_pack_uv_accurate_island_copy")
            box.label(text="Allowable Center Deviation:")
            box.prop(sc, "muv_pack_uv_allowable_center_deviation", text="")
            box.label(text="Allowable Size Deviation:")
            box.prop(sc, "muv_pack_uv_allowable_size_deviation", text="")
            box.label(text="Stride:")
            box.prop(sc, "muv_pack_uv_stride", text="")

        box = layout.box()
        box.prop(sc, "muv_clip_uv_enabled", text="Clip UV")
        if sc.muv_clip_uv_enabled:
            ops = box.operator(MUV_OT_ClipUV.bl_idname, text="Clip UV")
            ops.clip_uv_range_max = sc.muv_clip_uv_range_max
            ops.clip_uv_range_min = sc.muv_clip_uv_range_min
            box.label(text="Range:")
            row = box.row()
            col = row.column()
            col.prop(sc, "muv_clip_uv_range_max", text="Max")
            col = row.column()
            col.prop(sc, "muv_clip_uv_range_min", text="Min")
