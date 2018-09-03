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

from ..op import align_uv_cursor
from ..op import uv_bounding_box
from ..op import uv_inspection


class IMAGE_PT_MUV_EE(bpy.types.Panel):
    """
    Panel class: UV/Image Editor Enhancement
    """

    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_label = "Editor Enhancement"
    bl_category = "Magic UV"
    bl_context = 'mesh_edit'
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, _):
        layout = self.layout
        layout.label(text="", icon='IMAGE_COL')

    def draw(self, context):
        layout = self.layout
        sc = context.scene
        props = sc.muv_props

        box = layout.box()
        box.prop(sc, "muv_auvc_enabled", text="Align UV Cursor")
        if sc.muv_auvc_enabled:
            box.prop(sc, "muv_auvc_align_menu", expand=True)

            col = box.column(align=True)

            row = col.row(align=True)
            ops = row.operator(align_uv_cursor.MUV_AUVCAlignOps.bl_idname,
                               text="Left Top")
            ops.position = 'LEFT_TOP'
            ops.base = sc.muv_auvc_align_menu
            ops = row.operator(align_uv_cursor.MUV_AUVCAlignOps.bl_idname,
                               text="Middle Top")
            ops.position = 'MIDDLE_TOP'
            ops.base = sc.muv_auvc_align_menu
            ops = row.operator(align_uv_cursor.MUV_AUVCAlignOps.bl_idname,
                               text="Right Top")
            ops.position = 'RIGHT_TOP'
            ops.base = sc.muv_auvc_align_menu

            row = col.row(align=True)
            ops = row.operator(align_uv_cursor.MUV_AUVCAlignOps.bl_idname,
                               text="Left Middle")
            ops.position = 'LEFT_MIDDLE'
            ops.base = sc.muv_auvc_align_menu
            ops = row.operator(align_uv_cursor.MUV_AUVCAlignOps.bl_idname,
                               text="Center")
            ops.position = 'CENTER'
            ops.base = sc.muv_auvc_align_menu
            ops = row.operator(align_uv_cursor.MUV_AUVCAlignOps.bl_idname,
                               text="Right Middle")
            ops.position = 'RIGHT_MIDDLE'
            ops.base = sc.muv_auvc_align_menu

            row = col.row(align=True)
            ops = row.operator(align_uv_cursor.MUV_AUVCAlignOps.bl_idname,
                               text="Left Bottom")
            ops.position = 'LEFT_BOTTOM'
            ops.base = sc.muv_auvc_align_menu
            ops = row.operator(align_uv_cursor.MUV_AUVCAlignOps.bl_idname,
                               text="Middle Bottom")
            ops.position = 'MIDDLE_BOTTOM'
            ops.base = sc.muv_auvc_align_menu
            ops = row.operator(align_uv_cursor.MUV_AUVCAlignOps.bl_idname,
                               text="Right Bottom")
            ops.position = 'RIGHT_BOTTOM'
            ops.base = sc.muv_auvc_align_menu

        box = layout.box()
        box.prop(sc, "muv_uvcloc_enabled", text="UV Cursor Location")
        if sc.muv_uvcloc_enabled:
            box.prop(sc, "muv_auvc_cursor_loc", text="")

        box = layout.box()
        box.prop(sc, "muv_uvbb_enabled", text="UV Bounding Box")
        if sc.muv_uvbb_enabled:
            if props.uvbb.running is False:
                box.operator(uv_bounding_box.MUV_UVBBUpdater.bl_idname,
                             text="Display", icon='PLAY')
            else:
                box.operator(uv_bounding_box.MUV_UVBBUpdater.bl_idname,
                             text="Hide", icon='PAUSE')
            box.prop(sc, "muv_uvbb_uniform_scaling", text="Uniform Scaling")
            box.prop(sc, "muv_uvbb_boundary", text="Boundary")

        box = layout.box()
        box.prop(sc, "muv_uvinsp_enabled", text="UV Inspection")
        if sc.muv_uvinsp_enabled:
            row = box.row()
            if not sc.muv_props.uvinsp.display_running:
                row.operator(uv_inspection.MUV_UVInspDisplay.bl_idname,
                             text="Display", icon='PLAY')
            else:
                row.operator(uv_inspection.MUV_UVInspDisplay.bl_idname,
                             text="Hide", icon='PAUSE')
                row.operator(uv_inspection.MUV_UVInspUpdate.bl_idname,
                             text="Update")
            row = box.row()
            row.prop(sc, "muv_uvinsp_show_overlapped")
            row.prop(sc, "muv_uvinsp_show_flipped")
            row = box.row()
            row.prop(sc, "muv_uvinsp_show_mode")
