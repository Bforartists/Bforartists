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
Save & Reload File

When working with linked libraries, very often you need to save and load
again to see the changes.
This does it in one go, without asking, so be careful :)
Usage: Hit Ctrl + Shift + W or find it at the bottom of the File menu.
"""

import bpy


KEYMAPS = list()


class AMTH_WM_OT_save_reload(bpy.types.Operator):
    """Save and Reload the current blend file"""
    bl_idname = "wm.save_reload"
    bl_label = "Save & Reload"

    def save_reload(self, context, path):
        if not path:
            bpy.ops.wm.save_as_mainfile("INVOKE_AREA")
            return
        bpy.ops.wm.save_mainfile()
        self.report({"INFO"}, "Saved & Reloaded")
        bpy.ops.wm.open_mainfile("EXEC_DEFAULT", filepath=path)

    def execute(self, context):
        path = bpy.data.filepath
        self.save_reload(context, path)

        return {"FINISHED"}


def button_save_reload(self, context):
    get_addon = "amaranth" in context.preferences.addons.keys()
    if not get_addon:
        return

    if context.preferences.addons["amaranth"].preferences.use_file_save_reload:
        self.layout.separator()
        self.layout.operator(
            AMTH_WM_OT_save_reload.bl_idname,
            text="Save & Reload",
            icon="FILE_REFRESH")


def register():
    bpy.utils.register_class(AMTH_WM_OT_save_reload)
    bpy.types.TOPBAR_MT_file.append(button_save_reload)
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    km = kc.keymaps.new(name="Window")
    kmi = km.keymap_items.new("wm.save_reload", "W", "PRESS",
                              shift=True, ctrl=True)
    KEYMAPS.append((km, kmi))


def unregister():
    bpy.utils.unregister_class(AMTH_WM_OT_save_reload)
    bpy.types.TOPBAR_MT_file.remove(button_save_reload)
    for km, kmi in KEYMAPS:
        km.keymap_items.remove(kmi)
    KEYMAPS.clear()
