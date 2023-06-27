# SPDX-FileCopyrightText: 2016-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Hotkey: 'Shift Spacebar'",
    "description": "Pie menu for Timeline controls",
    "author": "pitiwazou, meta-androcto",
    "version": (0, 1, 1),
    "blender": (2, 80, 0),
    "location": "3D View",
    "warning": "",
    "doc_url": "",
    "category": "Animation Pie"
}

import bpy
from bpy.types import (
    Menu,
    Operator,
)

# Pie Animation


class PIE_MT_PieAnimation(Menu):
    bl_idname = "PIE_MT_animation"
    bl_label = "Pie Animation"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        # 4 - LEFT
        pie.operator("screen.frame_jump", text="Jump REW", icon='REW').end = False
        # 6 - RIGHT
        pie.operator("screen.frame_jump", text="Jump FF", icon='FF').end = True
        # 2 - BOTTOM
        pie.operator("screen.animation_play", text="Reverse", icon='PLAY_REVERSE').reverse = True
        # 8 - TOP
        if not context.screen.is_animation_playing:  # Play / Pause
            pie.operator("screen.animation_play", text="Play", icon='PLAY')
        else:
            pie.operator("screen.animation_play", text="Stop", icon='PAUSE')
        # 7 - TOP - LEFT
        pie.operator("screen.keyframe_jump", text="Previous FR", icon='PREV_KEYFRAME').next = False
        # 9 - TOP - RIGHT
        pie.operator("screen.keyframe_jump", text="Next FR", icon='NEXT_KEYFRAME').next = True
        # 1 - BOTTOM - LEFT
        pie.operator("insert.autokeyframe", text="Auto Keyframe", icon='REC')
        # 3 - BOTTOM - RIGHT
        pie.menu("VIEW3D_MT_object_animation", text="Keyframe Menu", icon="KEYINGSET")


# Insert Auto Keyframe
class PIE_OT_InsertAutoKeyframe(Operator):
    bl_idname = "insert.autokeyframe"
    bl_label = "Insert Auto Keyframe"
    bl_description = "Toggle Insert Auto Keyframe"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ts = context.tool_settings

        ts.use_keyframe_insert_auto ^= 1

        for area in context.screen.areas:
            if area.type == 'TIMELINE':
                area.tag_redraw()

        return {'FINISHED'}


classes = (
    PIE_MT_PieAnimation,
    PIE_OT_InsertAutoKeyframe
)

addon_keymaps = []


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    wm = bpy.context.window_manager
    if wm.keyconfigs.addon:
        # Animation
        km = wm.keyconfigs.addon.keymaps.new(name='Object Non-modal')
        kmi = km.keymap_items.new('wm.call_menu_pie', 'SPACE', 'PRESS', shift=True)
        kmi.properties.name = "PIE_MT_animation"
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
