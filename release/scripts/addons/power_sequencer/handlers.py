# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors

# This file is part of Power Sequencer.

import bpy
from bpy.app.handlers import persistent


@persistent
def power_sequencer_load_file_post(arg):
    """
    Called after loading the blend file
    """
    for scene in bpy.data.scenes:
        scene.power_sequencer.frame_pre = bpy.context.scene.frame_current


@persistent
def power_sequencer_playback_speed_post(scene):
    """
    Handler function for faster playback
    Skips keyframes after a frame change based on the playback_speed value
    It steps over frame rather than increase the playback speed smoothly,
    but it's still useful for faster editing
    """
    if bpy.context.screen and not bpy.context.screen.is_animation_playing:
        return

    playback_speed = scene.power_sequencer.playback_speed

    frame_start = scene.frame_current
    frame_post = scene.frame_current

    if playback_speed == "FAST" and frame_start % 3 == 0:
        frame_post += 1
    elif playback_speed == "FASTER" and frame_start % 2 == 0:
        frame_post += 1
    elif playback_speed == "DOUBLE":
        # 2.5x -> skip 5 frames for 2. 2 then 3 then 2 etc.
        frame_post += 1
    elif playback_speed == "TRIPLE":
        frame_post += 2

    if frame_start != frame_post:
        bpy.ops.screen.frame_offset(delta=frame_post - frame_start)
    scene.power_sequencer.frame_pre = scene.frame_current


def draw_playback_speed(self, context):
    layout = self.layout
    scene = context.scene
    layout.prop(scene.power_sequencer, "playback_speed")


def draw_ui_menu(self, context):
    layout = self.layout
    layout.menu("POWER_SEQUENCER_MT_main")


def register_handlers():
    # Menus
    bpy.types.SEQUENCER_HT_header.append(draw_ui_menu)
    bpy.types.SEQUENCER_HT_header.append(draw_playback_speed)

    # Handlers
    bpy.app.handlers.load_post.append(power_sequencer_load_file_post)
    bpy.app.handlers.frame_change_post.append(power_sequencer_playback_speed_post)


def unregister_handlers():
    # Menus
    bpy.types.SEQUENCER_HT_header.remove(draw_ui_menu)
    bpy.types.SEQUENCER_HT_header.remove(draw_playback_speed)

    # Handlers
    bpy.app.handlers.load_post.remove(power_sequencer_load_file_post)
    bpy.app.handlers.frame_change_post.remove(power_sequencer_playback_speed_post)
