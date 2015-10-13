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

import bpy

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "3.2"
__date__ = "20 Jun 2015"

from . import cpuv_default_operation
from . import cpuv_selseq_operation
from . import cpuv_uvmap_operation
from . import cpuv_fliprot_operation
from . import cpuv_transfer_uv_operation


# master menu
class CPUVMenu(bpy.types.Menu):
    bl_idname = "uv.cpuv_menu"
    bl_label = "Copy/Paste UV"
    bl_description = "Copy and Paste UV Menu"

    def draw(self, context):
        self.layout.operator(cpuv_default_operation.CPUVCopyUV.bl_idname)
        self.layout.operator(cpuv_default_operation.CPUVPasteUV.bl_idname)
        self.layout.operator(cpuv_selseq_operation.CPUVSelSeqCopyUV.bl_idname)
        self.layout.operator(cpuv_selseq_operation.CPUVSelSeqPasteUV.bl_idname)
        self.layout.menu(cpuv_uvmap_operation.CPUVUVMapCopyUV.bl_idname)
        self.layout.menu(cpuv_uvmap_operation.CPUVUVMapPasteUV.bl_idname)
        self.layout.operator(cpuv_fliprot_operation.CPUVFlipRotate.bl_idname)
        self.layout.operator(
            cpuv_transfer_uv_operation.CPUVTransferUVCopy.bl_idname)
        self.layout.operator(
            cpuv_transfer_uv_operation.CPUVTransferUVPaste.bl_idname)
