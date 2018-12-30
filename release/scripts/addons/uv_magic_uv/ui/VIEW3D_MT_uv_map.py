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

import bpy.utils

from ..op import (
    copy_paste_uv,
    transfer_uv,
    uvw,
)
from ..utils.bl_class_registry import BlClassRegistry

__all__ = [
    'MUV_MT_CopyPasteUV',
    'MUV_MT_TransferUV',
    'MUV_MT_UVW',
]


@BlClassRegistry()
class MUV_MT_CopyPasteUV(bpy.types.Menu):
    """
    Menu class: Master menu of Copy/Paste UV coordinate
    """

    bl_idname = "uv.muv_copy_paste_uv_menu"
    bl_label = "Copy/Paste UV"
    bl_description = "Copy and Paste UV coordinate"

    def draw(self, _):
        layout = self.layout

        layout.label(text="Default")
        layout.menu(copy_paste_uv.MUV_MT_CopyPasteUV_CopyUV.bl_idname,
                    text="Copy")
        layout.menu(copy_paste_uv.MUV_MT_CopyPasteUV_PasteUV.bl_idname,
                    text="Paste")

        layout.separator()

        layout.label(text="Selection Sequence")
        layout.menu(copy_paste_uv.MUV_MT_CopyPasteUV_SelSeqCopyUV.bl_idname,
                    text="Copy")
        layout.menu(copy_paste_uv.MUV_MT_CopyPasteUV_SelSeqPasteUV.bl_idname,
                    text="Paste")


@BlClassRegistry()
class MUV_MT_TransferUV(bpy.types.Menu):
    """
    Menu class: Master menu of Transfer UV coordinate
    """

    bl_idname = "uv.muv_transfer_uv_menu"
    bl_label = "Transfer UV"
    bl_description = "Transfer UV coordinate"

    def draw(self, context):
        layout = self.layout
        sc = context.scene

        layout.operator(transfer_uv.MUV_OT_TransferUV_CopyUV.bl_idname,
                        text="Copy")
        ops = layout.operator(transfer_uv.MUV_OT_TransferUV_PasteUV.bl_idname,
                              text="Paste")
        ops.invert_normals = sc.muv_transfer_uv_invert_normals
        ops.copy_seams = sc.muv_transfer_uv_copy_seams


@BlClassRegistry()
class MUV_MT_UVW(bpy.types.Menu):
    """
    Menu class: Master menu of UVW
    """

    bl_idname = "uv.muv_uvw_menu"
    bl_label = "UVW"
    bl_description = ""

    def draw(self, context):
        layout = self.layout
        sc = context.scene

        ops = layout.operator(uvw.MUV_OT_UVW_BoxMap.bl_idname, text="Box")
        ops.assign_uvmap = sc.muv_uvw_assign_uvmap

        ops = layout.operator(uvw.MUV_OT_UVW_BestPlanerMap.bl_idname,
                              text="Best Planner")
        ops.assign_uvmap = sc.muv_uvw_assign_uvmap
