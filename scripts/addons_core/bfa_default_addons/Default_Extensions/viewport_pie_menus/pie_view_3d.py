# SPDX-FileCopyrightText: 2016-2024 Blender Foundation
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.types import Menu
from .hotkeys import register_hotkey


class PIE_MT_view_pie(Menu):
    bl_idname = "PIE_MT_view_pie"
    bl_label = "3D View"

    def draw(self, context):
        pie = self.layout.menu_pie()
        # 4 - LEFT
        pie.operator('view3d.render_border', text="Set Render Border", icon='OBJECT_HIDDEN')
        # 6 - RIGHT
        pie.operator('view3d.view_selected', text="Frame Selected", icon='ZOOM_SELECTED')
        # 2 - BOTTOM
        pie.operator('view3d.view_persportho', text="Toggle Orthographic", icon='VIEW_ORTHO')
        # 8 - TOP
        pie.operator("screen.region_quadview", text="Toggle Quad View", icon='SNAP_VERTEX')
        # 7 - TOP - LEFT
        pie.operator('view3d.clip_border', text="Toggle Clipping Border", icon='MOD_BEVEL')
        # 9 - TOP - RIGHT
        pie.operator('view3d.view_all', text="Frame All", icon='VIEWZOOM').center=False
        # 1 - BOTTOM - LEFT
        pie.operator('view3d.clear_render_border', text="Clear Render Border", icon='X')
        # 3 - BOTTOM - RIGHT
        space = context.area.spaces.active
        if space.local_view:
            pie.operator("view3d.localview", text="Leave Local View", icon='SOLO_OFF').frame_selected=False
        else:
            pie.operator("view3d.localview", text="Enter Local View", icon='SOLO_ON').frame_selected=False


registry = [
    PIE_MT_view_pie,
]


def register():
    register_hotkey(
        'wm.call_menu_pie_drag_only',
        op_kwargs={'name': 'PIE_MT_view_pie', 'fallback_operator': 'view3d.view_all', 'op_kwargs': '{"center":true}'},
        hotkey_kwargs={'type': "C", 'value': "PRESS", 'shift': True},
        key_cat="3D View",
    )
