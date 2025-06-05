# SPDX-FileCopyrightText: 2016-2024 Blender Foundation
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.types import Menu
from .hotkeys import register_hotkey


class PIE_MT_preferences(Menu):
    bl_idname = "PIE_MT_preferences"
    bl_label = "Preferences"

    def draw(self, context):
        layout = self.layout
        prefs = context.preferences
        pie = layout.menu_pie()
        # 4 - LEFT
        pie.operator("wm.read_userpref", text="Revert to Saved Prefs", icon='LOOP_BACK')
        # 6 - RIGHT
        pie.operator("wm.save_userpref", text="Save User Preferences", icon='FILE_TICK')
        # 2 - BOTTOM
        pie.separator()
        # 8 - TOP
        pie.separator()
        # 7 - TOP - LEFT
        pie.operator(
            "wm.read_factory_userpref",
            text="Load Factory Preferences",
            icon='RECOVER_LAST',
        )
        # 9 - TOP - RIGHT
        pie.operator("wm.save_homefile", text="Save Startup File", icon='FILE_NEW')
        # 1 - BOTTOM - LEFT
        pie.operator("wm.read_factory_settings", text="Load Factory Startup & Prefs", icon='RECOVER_LAST')
        # 3 - BOTTOM - RIGHT
        pie.prop(
            prefs,
            "use_preferences_save",
            text="Auto-Save Preferences",
            icon='NONE',
        )


registry = [
    PIE_MT_preferences,
]


def register():
    register_hotkey(
        'wm.call_menu_pie',
        op_kwargs={'name': 'PIE_MT_preferences'},
        hotkey_kwargs={'type': "U", 'value': "PRESS", 'ctrl': True},
        key_cat="Window",
    )
