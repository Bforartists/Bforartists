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
    "name": "Hotkey: 'Ctrl U'",
    "description": "Save/Open & File Menus",
    "blender": (2, 80, 0),
    "location": "All Editors",
    "warning": "",
    "doc_url": "",
    "category": "Interface"
    }

import bpy
from bpy.types import (
        Menu,
        Operator,
        )
import os


# Pie Save/Open
class PIE_MT_Load_Defaults(Menu):
    bl_idname = "PIE_MT_loaddefaults"
    bl_label = "Save Defaults"

    def draw(self, context):
        layout = self.layout
        prefs = context.preferences
        pie = layout.menu_pie()
        # 4 - LEFT
        pie.operator("wm.read_factory_settings", text="Load Factory Settings", icon='IMPORT')
        # 6 - RIGHT
        pie.operator("wm.read_factory_userpref", text="Load Factory Preferences", icon='RECOVER_LAST')
        # 2 - BOTTOM
        pie.operator("wm.read_userpref", text="Revert to Saved Prefs", icon='NONE')
        # 8 - TOP
        pie.operator("wm.save_homefile", text="Save StartUp File", icon='FILE_NEW')
        # 7 - TOP - LEFT
        pie.prop(prefs, "use_preferences_save", text="Auto-Save Preferences", icon='LINK_BLEND')
        # 9 - TOP - RIGHT
        pie.operator("wm.save_userpref", text="Save User Preferences", icon='NONE')
        # 1 - BOTTOM - LEFT
        pie.separator()
        # 3 - BOTTOM - RIGHT
        pie.separator()



classes = (
    PIE_MT_Load_Defaults,
    )

addon_keymaps = []


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    wm = bpy.context.window_manager
    if wm.keyconfigs.addon:
        # Save/Open/...
        km = wm.keyconfigs.addon.keymaps.new(name='Window')
        kmi = km.keymap_items.new('wm.call_menu_pie', 'U', 'PRESS', ctrl=True)
        kmi.properties.name = "PIE_MT_loaddefaults"
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
