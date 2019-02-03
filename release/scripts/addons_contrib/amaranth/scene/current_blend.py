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
File Browser > Go to Current Blend's Folder

For when you're lost browsing files and want to go back to the currently
open blend's directory. Look for it on the File Browser's header, only
shows up if the file is saved.
"""

import bpy


class AMTH_FILE_OT_directory_current_blend(bpy.types.Operator):

    """Go to the directory of the currently open blend file"""
    bl_idname = "file.directory_current_blend"
    bl_label = "Current Blend's Folder"

    def execute(self, context):
        bpy.ops.file.select_bookmark(dir="//")
        return {"FINISHED"}


def button_directory_current_blend(self, context):
    if bpy.data.filepath:
        self.layout.operator(
            AMTH_FILE_OT_directory_current_blend.bl_idname,
            text="Current Blend's Folder",
            icon="APPEND_BLEND")


def register():
    bpy.utils.register_class(AMTH_FILE_OT_directory_current_blend)
    bpy.types.FILEBROWSER_HT_header.append(button_directory_current_blend)


def unregister():
    bpy.utils.unregister_class(AMTH_FILE_OT_directory_current_blend)
    bpy.types.FILEBROWSER_HT_header.remove(button_directory_current_blend)
