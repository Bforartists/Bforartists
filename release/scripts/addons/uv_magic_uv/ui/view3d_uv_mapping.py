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
__version__ = "5.1"
__date__ = "24 Feb 2018"

import bpy

from ..op import texture_projection
from ..op import unwrap_constraint
from ..op import uvw


class OBJECT_PT_MUV_UVMapping(bpy.types.Panel):
    """
    Panel class: UV Mapping on Property Panel on View3D
    """

    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_label = "UV Mapping"
    bl_category = "Magic UV"
    bl_context = 'mesh_edit'
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, _):
        layout = self.layout
        layout.label(text="", icon='IMAGE_COL')

    def draw(self, context):
        sc = context.scene
        props = sc.muv_props
        layout = self.layout

        box = layout.box()
        box.prop(sc, "muv_unwrapconst_enabled", text="Unwrap Constraint")
        if sc.muv_unwrapconst_enabled:
            ops = box.operator(
                unwrap_constraint.MUV_UnwrapConstraint.bl_idname,
                text="Unwrap")
            ops.u_const = sc.muv_unwrapconst_u_const
            ops.v_const = sc.muv_unwrapconst_v_const
            row = box.row(align=True)
            row.prop(sc, "muv_unwrapconst_u_const", text="U-Constraint")
            row.prop(sc, "muv_unwrapconst_v_const", text="V-Constraint")

        box = layout.box()
        box.prop(sc, "muv_texproj_enabled", text="Texture Projection")
        if sc.muv_texproj_enabled:
            row = box.row()
            if not props.texproj.running:
                row.operator(texture_projection.MUV_TexProjStart.bl_idname,
                             text="Start", icon='PLAY')
            else:
                row.operator(texture_projection.MUV_TexProjStop.bl_idname,
                             text="Stop", icon='PAUSE')
            row.prop(sc, "muv_texproj_tex_image", text="")
            box.prop(sc, "muv_texproj_tex_transparency", text="Transparency")
            col = box.column(align=True)
            row = col.row()
            row.prop(sc, "muv_texproj_adjust_window", text="Adjust Window")
            if not sc.muv_texproj_adjust_window:
                row.prop(sc, "muv_texproj_tex_magnitude", text="Magnitude")
            col.prop(sc, "muv_texproj_apply_tex_aspect",
                     text="Texture Aspect Ratio")
            col.prop(sc, "muv_texproj_assign_uvmap", text="Assign UVMap")
            if props.texproj.running:
                box.operator(texture_projection.MUV_TexProjProject.bl_idname,
                             text="Project")

        box = layout.box()
        box.prop(sc, "muv_uvw_enabled", text="UVW")
        if sc.muv_uvw_enabled:
            row = box.row(align=True)
            ops = row.operator(uvw.MUV_UVWBoxMap.bl_idname, text="Box")
            ops.assign_uvmap = sc.muv_uvw_assign_uvmap
            ops = row.operator(uvw.MUV_UVWBestPlanerMap.bl_idname,
                               text="Best Planner")
            ops.assign_uvmap = sc.muv_uvw_assign_uvmap
            box.prop(sc, "muv_uvw_assign_uvmap", text="Assign UVMap")
