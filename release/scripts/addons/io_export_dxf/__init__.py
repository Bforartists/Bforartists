#  ***** GPL LICENSE BLOCK *****
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#  All rights reserved.
#  ***** GPL LICENSE BLOCK *****

bl_info = {
    "name": "Export Autocad DXF Format (.dxf)",
    "author": "Remigiusz Fiedler (AKA migius), Vaclav Klecanda",
    "version": (2, 1, 3),
    "blender": (2, 63, 0),
    "location": "File > Export > Autodesk (.dxf)",
    "description": "The script exports Blender geometry to DXF format r12 version.",
    "warning": "Under construction! Visit Wiki for details.",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
        "Scripts/Import-Export/DXF_Exporter",
    "category": "Import-Export",
}


import bpy
from .operator import DXFExporter

def menu_func(self, context):
    self.layout.operator(DXFExporter.bl_idname, text="Autocad (.dxf)")

def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_export.append(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_export.remove(menu_func)

if __name__ == "__main__":
    register()
