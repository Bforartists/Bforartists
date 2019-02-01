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
__version__ = "6.0"
__date__ = "26 Jan 2019"

import bpy

from ..op.copy_paste_uv import (
    MUV_MT_CopyPasteUV_CopyUV,
    MUV_MT_CopyPasteUV_PasteUV,
    MUV_MT_CopyPasteUV_SelSeqCopyUV,
    MUV_MT_CopyPasteUV_SelSeqPasteUV,
)
from ..op.transfer_uv import (
    MUV_OT_TransferUV_CopyUV,
    MUV_OT_TransferUV_PasteUV,
)
from ..utils.bl_class_registry import BlClassRegistry
from ..utils import compatibility as compat


@BlClassRegistry()
@compat.ChangeRegionType(region_type='TOOLS')
class MUV_PT_CopyPasteUVEditMode(bpy.types.Panel):
    """
    Panel class: Copy/Paste UV on Property Panel on View3D
    """

    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Copy/Paste UV"
    bl_category = "Magic UV"
    bl_context = 'mesh_edit'
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, _):
        layout = self.layout
        layout.label(text="", icon=compat.icon('IMAGE'))

    def draw(self, context):
        sc = context.scene
        layout = self.layout

        box = layout.box()
        box.prop(sc, "muv_copy_paste_uv_enabled", text="Copy/Paste UV")
        if sc.muv_copy_paste_uv_enabled:
            row = box.row(align=True)
            if sc.muv_copy_paste_uv_mode == 'DEFAULT':
                row.menu(MUV_MT_CopyPasteUV_CopyUV.bl_idname, text="Copy")
                row.menu(MUV_MT_CopyPasteUV_PasteUV.bl_idname, text="Paste")
            elif sc.muv_copy_paste_uv_mode == 'SEL_SEQ':
                row.menu(MUV_MT_CopyPasteUV_SelSeqCopyUV.bl_idname,
                         text="Copy")
                row.menu(MUV_MT_CopyPasteUV_SelSeqPasteUV.bl_idname,
                         text="Paste")
            box.prop(sc, "muv_copy_paste_uv_mode", expand=True)
            box.prop(sc, "muv_copy_paste_uv_copy_seams", text="Seams")
            box.prop(sc, "muv_copy_paste_uv_strategy", text="Strategy")

        box = layout.box()
        box.prop(sc, "muv_transfer_uv_enabled", text="Transfer UV")
        if sc.muv_transfer_uv_enabled:
            row = box.row(align=True)
            row.operator(MUV_OT_TransferUV_CopyUV.bl_idname, text="Copy")
            ops = row.operator(MUV_OT_TransferUV_PasteUV.bl_idname,
                               text="Paste")
            ops.invert_normals = sc.muv_transfer_uv_invert_normals
            ops.copy_seams = sc.muv_transfer_uv_copy_seams
            row = box.row()
            row.prop(sc, "muv_transfer_uv_invert_normals",
                     text="Invert Normals")
            row.prop(sc, "muv_transfer_uv_copy_seams", text="Seams")
