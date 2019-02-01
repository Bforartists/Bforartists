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
    "name": "PCD",
    "author": "Aurel Wildfellner",
    "version": (0, 2),
    "blender": (2, 57, 0),
    "location": "File > Import-Export > Point Cloud Data",
    "description": "Imports and Exports PCD (Point Cloud Data) files. PCD files are the default format used by  pcl (Point Cloud Library).",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php?title=Extensions:2.6/Py/Scripts/Import-Export/Point_Cloud_Data_IO",
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
#    "support": 'OFFICAL',
    "category": "Import-Export"}


if "bpy" in locals():
    import imp
    imp.reload(pcd_utils)
else:
    from . import pcd_utils

import itertools
import os


import bpy
from bpy.props import *
from bpy_extras.io_utils import ExportHelper, ImportHelper


class ImportPCD(bpy.types.Operator, ImportHelper):
    """Load PCD (Point Cloud Data) files"""
    bl_idname = "import_points.stl"
    bl_label = "Import PCD"

    filename_ext = ".pcd"

    filter_glob: StringProperty(default="*.pcd", options={'HIDDEN'})
    object_name: StringProperty(default="", options={'HIDDEN'})

    files: CollectionProperty(name="File Path",
                          description="File path used for importing "
                                      "the PCD file",
                          type=bpy.types.OperatorFileListElement)

    directory: StringProperty(subtype='DIR_PATH')

    def execute(self, context):
        paths = [os.path.join(self.directory, name.name) for name in self.files]
        if not paths:
            paths.append(self.filepath)

        for path in paths:

            objname = ""

            if self.object_name == "":
                # name the object with the filename exluding .pcd
                objname = os.path.basename(path)[:-4]
            else:
                # use name set by calling the operator with the arg
                objname = self.object_name

            pcd_utils.import_pcd(path, objname)

        return {'FINISHED'}




class ExportPCD(bpy.types.Operator, ExportHelper):
    """Save PCD (Point Cloud Data) files"""
    bl_idname = "export_points.pcd"
    bl_label = "Export PCD"

    filename_ext = ".pcd"

    filter_glob: StringProperty(default="*.pcd", options={'HIDDEN'})


    def execute(self, context):
        pcd_utils.export_pcd(self.filepath)

        return {'FINISHED'}




def menu_func_import(self, context):
    self.layout.operator(ImportPCD.bl_idname, text="Point Cloud Data (.pcd)").filepath = "*.pcd"


def menu_func_export(self, context):
    self.layout.operator(ExportPCD.bl_idname, text="Point Cloud Data (.pcd)")


def register():
    bpy.utils.register_module(__name__)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
    register()
