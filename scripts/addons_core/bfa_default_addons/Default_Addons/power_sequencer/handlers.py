# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.app.handlers import persistent


@persistent
def power_sequencer_playback_speed_post(scene):
    """
    Handler function for faster playback
    Skips keyframes after a frame change based on the playback_speed value
    It steps over frame rather than increase the playback speed smoothly,
    but it's still useful for faster editing
    """

    # Calling this function triggers a callback to this function via the frame
    # changed handler, causing a stack overflow. We use a property to prevent
    # errors.
    if bpy.context.screen and not bpy.context.screen.is_animation_playing:
        return

    playback_speed = scene.power_sequencer.playback_speed

    target_frame = scene.frame_current
    if playback_speed == "DOUBLE":
        target_frame += 1
    elif playback_speed == "TRIPLE":
        target_frame += 2

    if target_frame != scene.frame_current:
        bpy.ops.screen.frame_offset(delta=target_frame - scene.frame_current)


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
    bpy.app.handlers.frame_change_post.append(power_sequencer_playback_speed_post)


def unregister_handlers():
    # Menus
    bpy.types.SEQUENCER_HT_header.remove(draw_ui_menu)
    bpy.types.SEQUENCER_HT_header.remove(draw_playback_speed)

    # Handlers
    bpy.app.handlers.frame_change_post.remove(power_sequencer_playback_speed_post)
