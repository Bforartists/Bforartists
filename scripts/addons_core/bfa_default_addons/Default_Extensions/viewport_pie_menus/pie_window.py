# SPDX-FileCopyrightText: 2016-2024 Blender Foundation
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.types import Menu, Operator
from .hotkeys import register_hotkey
from sys import platform


class PIE_MT_window(Menu):
    bl_idname = "PIE_MT_window"
    bl_label = "Window"

    def draw(self, context):
        pie = self.layout.menu_pie()

        # 4 - LEFT
        pie.operator('screen.userpref_show', text="Preferences", icon='PREFERENCES')
        # 6 - RIGHT
        if not context.screen.show_fullscreen:
            pie.operator(
                "screen.screen_full_area", text="Fullscreen Area", icon='PIVOT_BOUNDBOX'
            )
        else:
            pie.operator("wm.exit_area_fullscreen", icon='SCREEN_BACK')
        # 2 - BOTTOM
        pie.prop(context.screen, 'show_statusbar', text="Status Bar")
        # 8 - TOP
        pie.operator(
            "wm.window_fullscreen_toggle",
            text="Window Fullscreen",
            icon='FULLSCREEN_ENTER',
        )
        # 7 - TOP - LEFT
        pie.operator("screen.area_dupli", text="Pop Out Window", icon='WINDOW')
        # 9 - TOP - RIGHT
        if not context.screen.show_fullscreen:
            pie.operator(
                "screen.screen_full_area", text="Maximize Area", icon='PIVOT_BOUNDBOX'
            ).use_hide_panels = True
        else:
            pie.separator()
        # 1 - BOTTOM - LEFT
        if platform == 'win32':
            pie.operator("wm.console_toggle", icon='CONSOLE')
        else:
            pie.separator()
        # 3 - BOTTOM - RIGHT


class WM_OT_exit_area_fullscreen(Operator):
    """Exit area fullscreen"""

    bl_idname = "wm.exit_area_fullscreen"
    bl_label = "Exit Area Fullscreen"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.screen.show_fullscreen:
            bpy.ops.screen.screen_full_area()
        if context.screen.show_fullscreen:
            bpy.ops.screen.screen_full_area(use_hide_panels=True)

        return {'FINISHED'}


registry = [
    PIE_MT_window,
    WM_OT_exit_area_fullscreen,
]


def register():
    # NOTE: This sadly results in a console warning from wm_gizmo_map.c, but it seems harmless.
    register_hotkey(
        'wm.call_menu_pie_drag_only',
        op_kwargs={
            'name': 'PIE_MT_window',
            'fallback_operator': 'screen.screen_full_area',
        },
        hotkey_kwargs={'type': "SPACE", 'value': "PRESS", 'ctrl': True},
        key_cat="Window",
    )
