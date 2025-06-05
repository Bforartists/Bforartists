# SPDX-FileCopyrightText: 2016-2024 Blender Foundation
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.types import Menu
from .hotkeys import register_hotkey


class PIE_MT_animation(Menu):
    bl_idname = "PIE_MT_animation"
    bl_label = "Animation"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        # 4 - LEFT
        pie.operator("screen.frame_jump", text="Jump to Start", icon='REW').end = False
        # 6 - RIGHT
        pie.operator("screen.frame_jump", text="Jump to End", icon='FF').end = True
        # 2 - BOTTOM
        pie.operator(
            "screen.animation_play", text="Play Reverse", icon='PLAY_REVERSE'
        ).reverse = True
        # 8 - TOP
        if not context.screen.is_animation_playing:  # Play / Pause
            pie.operator("screen.animation_play", text="Play", icon='PLAY')
        else:
            pie.operator("screen.animation_play", text="Stop", icon='PAUSE')
        # 7 - TOP - LEFT
        pie.operator(
            "screen.keyframe_jump", text="Previous Keyframe", icon='PREV_KEYFRAME'
        ).next = False
        # 9 - TOP - RIGHT
        pie.operator(
            "screen.keyframe_jump", text="Next Keyframe", icon='NEXT_KEYFRAME'
        ).next = True
        # 1 - BOTTOM - LEFT
        pie.prop(context.tool_settings, "use_keyframe_insert_auto", text="Auto Keying")
        # 3 - BOTTOM - RIGHT
        pie.menu("VIEW3D_MT_object_animation", text="Keyframe Menu", icon="KEYINGSET")


registry = [
    PIE_MT_animation,
]


def register():
    register_hotkey(
        'wm.call_menu_pie_drag_only',
        op_kwargs={'name': 'PIE_MT_animation', 'fallback_operator': 'screen.animation_play'},
        hotkey_kwargs={'type': "SPACE", 'value': "PRESS", 'shift': True},
        key_cat='Object Non-modal',
    )
