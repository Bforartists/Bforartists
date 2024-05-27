# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
Current Frame Slider

Currently the only way to change the current frame is to have a Timeline
editor open, but sometimes you don't have one, or you're fullscreen.
This option adds the Current Frame slider to the Specials menu. Find it
hitting the W menu in Object mode, you can slide or click in the middle
of the button to set the frame manually.
"""

import bpy


def button_frame_current(self, context):
    get_addon = "amaranth" in context.preferences.addons.keys()
    if not get_addon:
        return

    scene = context.scene
    if context.preferences.addons["amaranth"].preferences.use_frame_current:
        self.layout.separator()
        self.layout.prop(scene, "frame_current", text="Set Current Frame")


def register():
    bpy.types.VIEW3D_MT_object_context_menu.append(button_frame_current)
    bpy.types.VIEW3D_MT_pose_context_menu.append(button_frame_current)


def unregister():
    bpy.types.VIEW3D_MT_object_context_menu.remove(button_frame_current)
    bpy.types.VIEW3D_MT_pose_context_menu.remove(button_frame_current)
