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
"""
File Browser: Libraries Bookmark

The "Libraries" panel on the File Browser displays the path to all the
libraries linked to that .blend. So you can quickly go to the folders
related to the file.

Click on any path to go to that directory.
Developed during Caminandes Open Movie Project
"""

import bpy


class AMTH_FILE_PT_libraries(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOLS"
    bl_category = "Bookmarks"
    bl_label = "Libraries"

    def draw(self, context):
        layout = self.layout

        libs = bpy.data.libraries
        libslist = []

        # Build the list of folders from libraries
        import os.path

        for lib in libs:
            directory_name = os.path.dirname(lib.filepath)
            libslist.append(directory_name)

        # Remove duplicates and sort by name
        libslist = set(libslist)
        libslist = sorted(libslist)

        # Draw the box with libs
        row = layout.row()
        box = row.box()

        if libslist:
            col = box.column()
            for filepath in libslist:
                if filepath != "//":
                    row = col.row()
                    row.alignment = "LEFT"
                    props = row.operator(
                        AMTH_FILE_OT_directory_go_to.bl_idname,
                        text=filepath, icon="BOOKMARKS",
                        emboss=False)
                    props.filepath = filepath
        else:
            box.label(text="No libraries loaded")


class AMTH_FILE_OT_directory_go_to(bpy.types.Operator):

    """Go to this library"s directory"""
    bl_idname = "file.directory_go_to"
    bl_label = "Go To"

    filepath = bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        bpy.ops.file.select_bookmark(dir=self.filepath)
        return {"FINISHED"}


def register():
    bpy.utils.register_class(AMTH_FILE_PT_libraries)
    bpy.utils.register_class(AMTH_FILE_OT_directory_go_to)


def unregister():
    bpy.utils.unregister_class(AMTH_FILE_PT_libraries)
    bpy.utils.unregister_class(AMTH_FILE_OT_directory_go_to)
