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

# <pep8 compliant>

bl_info = {
    "name": "Hotkey: 'Ctrl S'",
    "description": "Save/Open & File Menus",
    "blender": (2, 80, 0),
    "location": "All Editors",
    "warning": "",
    "doc_url": "",
    "category": "Save Open Pie"
    }

import bpy
from bpy.types import (
        Menu,
        Operator,
        )
import os


# Pie Save/Open
class PIE_MT_SaveOpen(Menu):
    bl_idname = "PIE_MT_saveopen"
    bl_label = "Pie Save/Open"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        # 4 - LEFT
        pie.operator("wm.read_homefile", text="New", icon='FILE_NEW')
        # 6 - RIGHT
        pie.menu("PIE_MT_link", text="Link Menu", icon='LINK_BLEND')
        # 2 - BOTTOM
        pie.menu("PIE_MT_fileio", text="Import/Export Menu", icon='IMPORT')
        # 8 - TOP
        pie.operator("wm.open_mainfile", text="Open File", icon='FILE_FOLDER')
        # 7 - TOP - LEFT
        pie.operator("wm.save_mainfile", text="Save", icon='FILE_TICK')
        # 9 - TOP - RIGHT
        pie.operator("wm.save_as_mainfile", text="Save As...", icon='NONE')
        # 1 - BOTTOM - LEFT
        pie.operator("file.save_incremental", text="Incremental Save", icon='NONE')
        # 3 - BOTTOM - RIGHT
        pie.menu("PIE_MT_recover", text="Recovery Menu", icon='RECOVER_LAST')


class PIE_MT_link(Menu):
    bl_idname = "PIE_MT_link"
    bl_label = "Link"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        box = pie.split().column()
        box.operator("wm.link", text="Link", icon='LINK_BLEND')
        box.operator("wm.append", text="Append", icon='APPEND_BLEND')
        box.separator()
        box.operator("file.autopack_toggle", text="Automatically Pack Into .blend")
        box.operator("file.pack_all", text="Pack All Into .blend")
        box.operator("file.unpack_all", text="Unpack All Into Files")
        box.separator()
        box.operator("file.make_paths_relative", text="Make All Paths Relative")
        box.operator("file.make_paths_absolute", text="Make All Paths Absolute")


class PIE_MT_recover(Menu):
    bl_idname = "PIE_MT_recover"
    bl_label = "Recovery"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        box = pie.split().column()
        box.operator("wm.recover_auto_save", text="Recover Auto Save...", icon='NONE')
        box.operator("wm.recover_last_session", text="Recover Last Session", icon='RECOVER_LAST')
        box.operator("wm.revert_mainfile", text="Revert", icon='FILE_REFRESH')
        box.separator()
        box.operator("file.report_missing_files", text="Report Missing Files")
        box.operator("file.find_missing_files", text="Find Missing Files")

class PIE_MT_fileio(Menu):
    bl_idname = "PIE_MT_fileio"
    bl_label = "Import/Export"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        box = pie.split().column()
        box.menu("TOPBAR_MT_file_import", icon='IMPORT')
        box.separator()
        box.menu("TOPBAR_MT_file_export", icon='EXPORT')


# Save Incremental
class PIE_OT_FileIncrementalSave(Operator):
    bl_idname = "file.save_incremental"
    bl_label = "Save Incremental"
    bl_description = "Save First! then Incremental, .blend will get _001 extension"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return (bpy.data.filepath != "")

    def execute(self, context):
        f_path = bpy.data.filepath
        b_name = bpy.path.basename(f_path)

        if b_name and b_name.find("_") != -1:
            # except in cases when there is an underscore in the name like my_file.blend
            try:
                str_nb = b_name.rpartition("_")[-1].rpartition(".blend")[0]
                int_nb = int(str(str_nb))
                new_nb = str_nb.replace(str(int_nb), str(int_nb + 1))
                output = f_path.replace(str_nb, new_nb)

                i = 1
                while os.path.isfile(output):
                    str_nb = b_name.rpartition("_")[-1].rpartition(".blend")[0]
                    i += 1
                    new_nb = str_nb.replace(str(int_nb), str(int_nb + i))
                    output = f_path.replace(str_nb, new_nb)
            except ValueError:
                output = f_path.rpartition(".blend")[0] + "_001" + ".blend"
        else:
            # no underscore in the name or saving a nameless (.blend) file
            output = f_path.rpartition(".blend")[0] + "_001" + ".blend"

        # fix for saving in a directory without privileges
        try:
            bpy.ops.wm.save_as_mainfile(filepath=output)
        except:
            self.report({'WARNING'},
                        "File could not be saved. Check the System Console for errors")
            return {'CANCELLED'}

        self.report(
                {'INFO'}, "File: {0} - Created at: {1}".format(
                    output[len(bpy.path.abspath("//")):],
                    output[:len(bpy.path.abspath("//"))]),
                )
        return {'FINISHED'}


classes = (
    PIE_MT_SaveOpen,
    PIE_OT_FileIncrementalSave,
    PIE_MT_fileio,
    PIE_MT_recover,
    PIE_MT_link,
    )

addon_keymaps = []


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    wm = bpy.context.window_manager
    if wm.keyconfigs.addon:
        # Save/Open/...
        km = wm.keyconfigs.addon.keymaps.new(name='Window')
        kmi = km.keymap_items.new('wm.call_menu_pie', 'S', 'PRESS', ctrl=True)
        kmi.properties.name = "PIE_MT_saveopen"
        addon_keymaps.append((km, kmi))


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        for km, kmi in addon_keymaps:
            km.keymap_items.remove(kmi)
    addon_keymaps.clear()


if __name__ == "__main__":
    register()
