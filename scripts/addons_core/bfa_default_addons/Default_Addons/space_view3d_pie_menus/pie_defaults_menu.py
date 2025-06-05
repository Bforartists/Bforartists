# SPDX-FileCopyrightText: 2016-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

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
