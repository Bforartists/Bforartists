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

from ..op.copy_paste_uv_object import (
    MUV_MT_CopyPasteUVObject_CopyUV,
    MUV_MT_CopyPasteUVObject_PasteUV,
)
from ..utils.bl_class_registry import BlClassRegistry
from ..utils import compatibility as compat


@BlClassRegistry()
@compat.ChangeRegionType(region_type='TOOLS')
class MUV_PT_View3D_Object_CopyPasteUV(bpy.types.Panel):
    """
    Panel class: Copy/Paste UV on Property Panel on View3D
    """

    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Copy/Paste UV"
    bl_category = "Magic UV"
    bl_context = 'objectmode'
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, _):
        layout = self.layout
        layout.label(text="", icon=compat.icon('IMAGE'))

    def draw(self, context):
        sc = context.scene
        layout = self.layout

        row = layout.row(align=True)
        row.menu(MUV_MT_CopyPasteUVObject_CopyUV.bl_idname, text="Copy")
        row.menu(MUV_MT_CopyPasteUVObject_PasteUV.bl_idname, text="Paste")
        layout.prop(sc, "muv_copy_paste_uv_object_copy_seams",
                    text="Seams")
