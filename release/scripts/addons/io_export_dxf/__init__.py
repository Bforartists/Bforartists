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

bl_info = {
    "name": "Export Autocad DXF Format (.dxf)",
    "author": "Remigiusz Fiedler (AKA migius), Vaclav Klecanda",
    "version": (2, 2, 3),
    "blender": (2, 80, 0),
    "location": "File > Export > AutoCAD DXF",
    "description": "The script exports Blender geometry to DXF format r12 version.",
    "warning": "Under construction! Visit Wiki for details.",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/import_export/scene_dxf.html",
    "category": "Import-Export",
}

if "bpy" in locals():
    from importlib import reload
    reload(operator)
    del reload

import bpy
from . import operator

def menu_func(self, context):
    self.layout.operator(operator.DXFExporter.bl_idname, text="AutoCAD DXF")

classes = (
    operator.DXFExporter,
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    bpy.types.TOPBAR_MT_file_export.append(menu_func)


def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func)

if __name__ == "__main__":
    register()
