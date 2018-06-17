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

from ..op import copy_paste_uv
from ..op import transfer_uv


class OBJECT_PT_MUV_CPUV(bpy.types.Panel):
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
        box.prop(sc, "muv_cpuv_enabled", text="Copy/Paste UV")
        if sc.muv_cpuv_enabled:
            row = box.row(align=True)
            if sc.muv_cpuv_mode == 'DEFAULT':
                row.menu(copy_paste_uv.MUV_CPUVCopyUVMenu.bl_idname,
                         text="Copy")
                row.menu(copy_paste_uv.MUV_CPUVPasteUVMenu.bl_idname,
                         text="Paste")
            elif sc.muv_cpuv_mode == 'SEL_SEQ':
                row.menu(copy_paste_uv.MUV_CPUVSelSeqCopyUVMenu.bl_idname,
                         text="Copy")
                row.menu(copy_paste_uv.MUV_CPUVSelSeqPasteUVMenu.bl_idname,
                         text="Paste")
            box.prop(sc, "muv_cpuv_mode", expand=True)
            box.prop(sc, "muv_cpuv_copy_seams", text="Seams")
            box.prop(sc, "muv_cpuv_strategy", text="Strategy")

        box = layout.box()
        box.prop(sc, "muv_transuv_enabled", text="Transfer UV")
        if sc.muv_transuv_enabled:
            row = box.row(align=True)
            row.operator(transfer_uv.MUV_TransUVCopy.bl_idname, text="Copy")
            ops = row.operator(transfer_uv.MUV_TransUVPaste.bl_idname,
                               text="Paste")
            ops.invert_normals = sc.muv_transuv_invert_normals
            ops.copy_seams = sc.muv_transuv_copy_seams
            row = box.row()
            row.prop(sc, "muv_transuv_invert_normals", text="Invert Normals")
            row.prop(sc, "muv_transuv_copy_seams", text="Seams")
