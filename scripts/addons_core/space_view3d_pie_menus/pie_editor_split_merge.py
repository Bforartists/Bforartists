# SPDX-FileCopyrightText: 2016-2024 Blender Foundation
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.types import Menu, Operator
from bpy.props import StringProperty
from .hotkeys import register_hotkey
from .op_pie_wrappers import WM_OT_call_menu_pie_drag_only


class PIE_MT_area_split_join(Menu):
    bl_idname = "PIE_MT_area_split_join"
    bl_label = "Area Split/Join"

    def draw(self, context):
        pie = self.layout.menu_pie()
        pie.scale_y = 1.2

        # 4 - LEFT
        pie.operator('wm.area_join_from_pie', text="Join Left", icon='TRIA_LEFT').direction='LEFT'
        # 6 - RIGHT
        pie.operator('wm.area_join_from_pie', text="Join Right", icon='TRIA_RIGHT').direction='RIGHT'
        # 2 - BOTTOM
        pie.operator('wm.area_join_from_pie', text="Join Down", icon='TRIA_DOWN').direction='DOWN'
        # 8 - TOP
        pie.operator('wm.area_join_from_pie', text="Join Up", icon='TRIA_UP').direction='UP'

        # 7 - TOP - LEFT
        pie.separator()
        # 9 - TOP - RIGHT
        pie.separator()
        # 1 - BOTTOM - LEFT
        pie.separator()
        # 3 - BOTTOM - RIGHT
        area = context.area
        icon = 'SPLIT_HORIZONTAL'
        direction = 'HORIZONTAL'
        if area.width > area.height:
            icon = 'SPLIT_VERTICAL'
            direction = 'VERTICAL'
        pie.operator('screen.area_split', text="Split Area", icon=icon).direction=direction


class WM_OT_area_join_from_pie(Operator):
    """Join two editor areas into one"""
    bl_idname = "wm.area_join_from_pie"
    bl_label = "Join Areas"
    bl_options = {'REGISTER', 'UNDO'}

    direction: StringProperty()

    def invoke(self, context, event):
        active = context.area
        if not active:
            return

        # Thanks to Harley Acheson for explaining: 
        # https://devtalk.blender.org/t/join-two-areas-by-python-area-join-what-arguments-blender-2-80/18165/2
        cursor = None
        mouse_x, mouse_y = event.mouse_x, event.mouse_y
        if self.direction == 'LEFT':
            cursor = (active.x+2, mouse_y)
        elif self.direction == 'RIGHT':
            cursor = (active.x+active.width, mouse_y)
        elif self.direction == 'UP':
            cursor = (mouse_x, active.y+active.height)
        elif self.direction == 'DOWN':
            cursor = (mouse_x, active.y)

        if 'cursor' in bpy.ops.screen.area_join.get_rna_type().properties:
            # Pre-4.3
            return bpy.ops.screen.area_join('INVOKE_DEFAULT', cursor=cursor)
        else:
            # 4.3 has WIP changes about area joining.
            # https://devtalk.blender.org/t/interactive-editor-docking-is-now-experimental/35800
            print("Editor Split Pie: This operator is not currently supported by Blender 4.3")


registry = [
    PIE_MT_area_split_join,
    WM_OT_area_join_from_pie,
]


def register():
    if 'cursor' in bpy.ops.screen.area_join.get_rna_type().properties:
        # Pre-4.3
        WM_OT_call_menu_pie_drag_only.register_drag_hotkey(
            keymap_name="Window",
            pie_name=PIE_MT_area_split_join.bl_idname,
            hotkey_kwargs={'type': "ACCENT_GRAVE", 'value': "PRESS", 'alt': True},
            on_drag=False,
        )
    else:
        # 4.3 and beyond: Just call the new UI Docking operator
        register_hotkey(
            'screen.area_join',
            hotkey_kwargs={'type': "ACCENT_GRAVE", 'value': "PRESS", 'alt': True},
            keymap_name="Window",
        )
