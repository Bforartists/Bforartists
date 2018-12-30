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
    copy_paste_uv_uvedit,
)
from ..utils.bl_class_registry import BlClassRegistry

__all__ = [
    'MUV_MT_CopyPasteUV_UVEdit',
]


@BlClassRegistry()
class MUV_MT_CopyPasteUV_UVEdit(bpy.types.Menu):
    """
    Menu class: Master menu of Copy/Paste UV coordinate on UV/ImageEditor
    """

    bl_idname = "uv.muv_copy_paste_uv_uvedit_menu"
    bl_label = "Copy/Paste UV"
    bl_description = "Copy and Paste UV coordinate among object"

    def draw(self, _):
        layout = self.layout

        layout.operator(
            copy_paste_uv_uvedit.MUV_OT_CopyPasteUVUVEdit_CopyUV.bl_idname,
            text="Copy")
        layout.operator(
            copy_paste_uv_uvedit.MUV_OT_CopyPasteUVUVEdit_PasteUV.bl_idname,
            text="Paste")
