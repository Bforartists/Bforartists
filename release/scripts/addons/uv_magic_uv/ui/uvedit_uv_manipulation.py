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

from ..op import uv_inspection
from ..op import align_uv
from ..op import smooth_uv
from ..op import pack_uv


class IMAGE_PT_MUV_UVManip(bpy.types.Panel):
    """
    Panel class: UV Manipulation on Property Panel on UV/ImageEditor
    """

    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_label = "UV Manipulation"
    bl_category = "Magic UV"
    bl_context = 'mesh_edit'
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, _):
        layout = self.layout
        layout.label(text="", icon='IMAGE_COL')

    def draw(self, context):
        sc = context.scene
        layout = self.layout

        box = layout.box()
        box.prop(sc, "muv_auv_enabled", text="Align UV")
        if sc.muv_auv_enabled:
            col = box.column()
            row = col.row(align=True)
            ops = row.operator(align_uv.MUV_AUVCircle.bl_idname, text="Circle")
            ops.transmission = sc.muv_auv_transmission
            ops.select = sc.muv_auv_select
            ops = row.operator(align_uv.MUV_AUVStraighten.bl_idname,
                               text="Straighten")
            ops.transmission = sc.muv_auv_transmission
            ops.select = sc.muv_auv_select
            ops.vertical = sc.muv_auv_vertical
            ops.horizontal = sc.muv_auv_horizontal
            row = col.row()
            ops = row.operator(align_uv.MUV_AUVAxis.bl_idname, text="XY-axis")
            ops.transmission = sc.muv_auv_transmission
            ops.select = sc.muv_auv_select
            ops.vertical = sc.muv_auv_vertical
            ops.horizontal = sc.muv_auv_horizontal
            ops.location = sc.muv_auv_location
            row.prop(sc, "muv_auv_location", text="")

            col = box.column(align=True)
            row = col.row(align=True)
            row.prop(sc, "muv_auv_transmission", text="Transmission")
            row.prop(sc, "muv_auv_select", text="Select")
            row = col.row(align=True)
            row.prop(sc, "muv_auv_vertical", text="Vertical")
            row.prop(sc, "muv_auv_horizontal", text="Horizontal")

        box = layout.box()
        box.prop(sc, "muv_smuv_enabled", text="Smooth UV")
        if sc.muv_smuv_enabled:
            ops = box.operator(smooth_uv.MUV_AUVSmooth.bl_idname,
                               text="Smooth")
            ops.transmission = sc.muv_smuv_transmission
            ops.select = sc.muv_smuv_select
            ops.mesh_infl = sc.muv_smuv_mesh_infl
            col = box.column(align=True)
            row = col.row(align=True)
            row.prop(sc, "muv_smuv_transmission", text="Transmission")
            row.prop(sc, "muv_smuv_select", text="Select")
            col.prop(sc, "muv_smuv_mesh_infl", text="Mesh Influence")

        box = layout.box()
        box.prop(sc, "muv_seluv_enabled", text="Select UV")
        if sc.muv_seluv_enabled:
            row = box.row(align=True)
            row.operator(uv_inspection.MUV_UVInspSelectOverlapped.bl_idname)
            row.operator(uv_inspection.MUV_UVInspSelectFlipped.bl_idname)

        box = layout.box()
        box.prop(sc, "muv_packuv_enabled", text="Pack UV (Extension)")
        if sc.muv_packuv_enabled:
            ops = box.operator(pack_uv.MUV_PackUV.bl_idname, text="Pack UV")
            ops.allowable_center_deviation = \
                sc.muv_packuv_allowable_center_deviation
            ops.allowable_size_deviation = \
                sc.muv_packuv_allowable_size_deviation
            box.label("Allowable Center Deviation:")
            box.prop(sc, "muv_packuv_allowable_center_deviation", text="")
            box.label("Allowable Size Deviation:")
            box.prop(sc, "muv_packuv_allowable_size_deviation", text="")
