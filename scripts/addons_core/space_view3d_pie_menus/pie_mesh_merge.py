# SPDX-FileCopyrightText: 2016-2024 Blender Foundation
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.types import Menu
from .hotkeys import register_hotkey


class PIE_MT_mesh_merge(Menu):
    bl_idname = "PIE_MT_mesh_merge"
    bl_label = "Mesh Merge"

    def draw(self, context):
        pie = self.layout.menu_pie()

        # 4 - LEFT
        pie.operator('mesh.remove_doubles', text="By Distance", icon='PROP_ON')

        # 6 - RIGHT
        pie.operator('mesh.merge', text="At Center", icon='SNAP_FACE_CENTER').type = (
            'CENTER'
        )

        # 2 - BOTTOM
        op = pie.operator('mesh.merge', text="Collapse", icon='FULLSCREEN_EXIT')
        op.type = 'COLLAPSE'

        # 8 - TOP
        pie.separator()

        # The implementation of Blender's built-in Merge operator is weird as hell:
        # If no geo is selected, the "At First" and "At Last" options cannot be drawn,
        # even though in such a case, NONE of the options will do ANYTHING anyways.
        # But it is what it is, I choose to be consistent.
        try:
            # This will raise an error if the option isn't available.
            op.type = 'FIRST'
            # 7 - TOP - LEFT
            pie.operator(
                'mesh.merge', text="At First", icon='TRACKING_REFINE_BACKWARDS'
            ).type = 'FIRST'
            # 9 - TOP - RIGHT
            pie.operator(
                'mesh.merge', text="At Last", icon='TRACKING_REFINE_FORWARDS'
            ).type = 'LAST'
        except:
            op.type = 'COLLAPSE'
            pie.separator()
            pie.separator()

        # 1 - BOTTOM - LEFT
        pie.separator()
        # 3 - BOTTOM - RIGHT
        pie.operator('mesh.merge', text="At 3D Cursor", icon='PIVOT_CURSOR').type = (
            'CURSOR'
        )


registry = [PIE_MT_mesh_merge]


def register():
    register_hotkey(
        'wm.call_menu_pie',
        op_kwargs={'name': 'PIE_MT_mesh_merge'},
        hotkey_kwargs={'type': "M", 'value': "PRESS"},
        key_cat="Mesh",
    )
