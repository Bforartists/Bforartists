# system_project_folder.py (c) 2010 Dany Lebel (Axon_D)
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****

bl_info = {
    "name": "Project Folder",
    "author": "Dany Lebel (Axon_D), Spirou4D",
    "version": (0, 3, 1),
    "blender": (2, 61, 0),
    "location": "Info -> File Menu -> Project Folder",
    "description": "Open the project folder in a file browser",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/System/Project_Folder",
    "tracker_url": "https://developer.blender.org/T25910",
    "category": "System"}


import bpy
import os
from platform import system as currentOS


class ProjectFolder(bpy.types.Operator):
    """Open the Project Folder in a file Browser"""
    bl_idname = "file.project_folder"
    bl_label = "Project Folder"


    def execute(self, context):
        try :
            path = self.path()
        except ValueError:
            self.report({'INFO'}, "No project folder yet")
            return {'FINISHED'}

        bpy.ops.wm.path_open(filepath=path)


        return {'FINISHED'}

    def path(self):
        filepath = bpy.data.filepath
        relpath = bpy.path.relpath(filepath)
        path = filepath[0: -1 * (relpath.__len__() - 2)]
        return path


# Registration

def menu_func(self, context):
    self.layout.operator(
        ProjectFolder.bl_idname,
        text="Project Folder",
        icon="FILESEL")

def register():
    bpy.utils.register_class(ProjectFolder)
    bpy.types.INFO_MT_file.prepend(menu_func)

def unregister():
    bpy.utils.unregister_class(ProjectFolder)
    bpy.types.INFO_MT_file.remove(menu_func)

if __name__ == "__main__":
    register()
