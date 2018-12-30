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
__version__ = "5.2"
__date__ = "17 Nov 2018"

import bpy

from ..op import (
    transfer_uv,
    copy_paste_uv,
)
from ...utils.bl_class_registry import BlClassRegistry

__all__ = [
    'MUV_PT_View3D_Edit_CopyPasteUV',
]


@BlClassRegistry(legacy=True)
class MUV_PT_View3D_Edit_CopyPasteUV(bpy.types.Panel):
    """
    Panel class: Copy/Paste UV on Property Panel on View3D
    """

    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_label = "Copy/Paste UV"
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
        box.prop(sc, "muv_copy_paste_uv_enabled", text="Copy/Paste UV")
        if sc.muv_copy_paste_uv_enabled:
            row = box.row(align=True)
            if sc.muv_copy_paste_uv_mode == 'DEFAULT':
                row.menu(copy_paste_uv.MUV_MT_CopyPasteUV_CopyUV.bl_idname,
                         text="Copy")
                row.menu(copy_paste_uv.MUV_MT_CopyPasteUV_PasteUV.bl_idname,
                         text="Paste")
            elif sc.muv_copy_paste_uv_mode == 'SEL_SEQ':
                row.menu(
                    copy_paste_uv.MUV_MT_CopyPasteUV_SelSeqCopyUV.bl_idname,
                    text="Copy")
                row.menu(
                    copy_paste_uv.MUV_MT_CopyPasteUV_SelSeqPasteUV.bl_idname,
                    text="Paste")
            box.prop(sc, "muv_copy_paste_uv_mode", expand=True)
            box.prop(sc, "muv_copy_paste_uv_copy_seams", text="Seams")
            box.prop(sc, "muv_copy_paste_uv_strategy", text="Strategy")

        box = layout.box()
        box.prop(sc, "muv_transfer_uv_enabled", text="Transfer UV")
        if sc.muv_transfer_uv_enabled:
            row = box.row(align=True)
            row.operator(transfer_uv.MUV_OT_TransferUV_CopyUV.bl_idname,
                         text="Copy")
            ops = row.operator(transfer_uv.MUV_OT_TransferUV_PasteUV.bl_idname,
                               text="Paste")
            ops.invert_normals = sc.muv_transfer_uv_invert_normals
            ops.copy_seams = sc.muv_transfer_uv_copy_seams
            row = box.row()
            row.prop(sc, "muv_transfer_uv_invert_normals",
                     text="Invert Normals")
            row.prop(sc, "muv_transfer_uv_copy_seams", text="Seams")
