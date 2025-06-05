# SPDX-FileCopyrightText: 2018-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.6"
__date__ = "22 Apr 2022"

import bpy

from ..op.uvw import (
    MUV_OT_UVW_BoxMap,
    MUV_OT_UVW_BestPlanerMap,
)
from ..op.texture_projection import (
    MUV_OT_TextureProjection,
    MUV_OT_TextureProjection_Project,
)
from ..op.unwrap_constraint import MUV_OT_UnwrapConstraint
from ..utils.bl_class_registry import BlClassRegistry
from ..utils import compatibility as compat


@BlClassRegistry()
@compat.ChangeRegionType(region_type='TOOLS')
class MUV_PT_View3D_UVMapping(bpy.types.Panel):
    """
    Panel class: UV Mapping on Property Panel on View3D
    """

    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "UV Mapping"
    bl_category = "Edit"
    bl_context = 'mesh_edit'
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, _):
        layout = self.layout
        layout.label(text="", icon=compat.icon('IMAGE'))

    def draw(self, context):
        sc = context.scene
        layout = self.layout

        box = layout.box()
        box.prop(sc, "muv_unwrap_constraint_enabled", text="Unwrap Constraint")
        if sc.muv_unwrap_constraint_enabled:
            ops = box.operator(MUV_OT_UnwrapConstraint.bl_idname,
                               text="Unwrap")
            ops.u_const = sc.muv_unwrap_constraint_u_const
            ops.v_const = sc.muv_unwrap_constraint_v_const
            row = box.row(align=True)
            row.prop(sc, "muv_unwrap_constraint_u_const", text="U-Constraint")
            row.prop(sc, "muv_unwrap_constraint_v_const", text="V-Constraint")

        box = layout.box()
        box.prop(sc, "muv_texture_projection_enabled",
                 text="Texture Projection")
        if sc.muv_texture_projection_enabled:
            row = box.row()
            row.prop(
                sc, "muv_texture_projection_enable",
                text="Disable"
                if MUV_OT_TextureProjection.is_running(context)
                else "Enable",
                icon='RESTRICT_VIEW_OFF'
                if MUV_OT_TextureProjection.is_running(context)
                else 'RESTRICT_VIEW_ON')
            row.prop(sc, "muv_texture_projection_tex_image", text="")
            box.prop(sc, "muv_texture_projection_tex_transparency",
                     text="Transparency")
            col = box.column(align=True)
            row = col.row()
            row.prop(sc, "muv_texture_projection_adjust_window",
                     text="Adjust Window")
            if not sc.muv_texture_projection_adjust_window:
                sp = compat.layout_split(col, factor=0.5)
                sub = sp.column()
                sub.prop(sc, "muv_texture_projection_tex_scaling",
                         text="Scaling")
                sp = compat.layout_split(sp, factor=1.0)
                sub = sp.column()
                sub.prop(sc, "muv_texture_projection_tex_translation",
                         text="Translation")
                row = col.row()
                row.label(text="Rotation:")
                row.prop(sc, "muv_texture_projection_tex_rotation", text="")
                col.separator()
            col.prop(sc, "muv_texture_projection_apply_tex_aspect",
                     text="Texture Aspect Ratio")
            col.prop(sc, "muv_texture_projection_assign_uvmap",
                     text="Assign UVMap")
            box.operator(
                MUV_OT_TextureProjection_Project.bl_idname,
                text="Project")

        box = layout.box()
        box.prop(sc, "muv_uvw_enabled", text="UVW")
        if sc.muv_uvw_enabled:
            row = box.row(align=True)
            ops = row.operator(MUV_OT_UVW_BoxMap.bl_idname, text="Box")
            ops.assign_uvmap = sc.muv_uvw_assign_uvmap
            ops = row.operator(MUV_OT_UVW_BestPlanerMap.bl_idname,
                               text="Best Planner")
            ops.assign_uvmap = sc.muv_uvw_assign_uvmap
            box.prop(sc, "muv_uvw_assign_uvmap", text="Assign UVMap")
