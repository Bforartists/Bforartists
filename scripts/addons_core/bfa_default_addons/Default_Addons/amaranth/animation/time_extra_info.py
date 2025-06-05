# SPDX-FileCopyrightText: 2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
Time Extra Info

Display amount of frames left until Frame End, very handy especially when
rendering an animation or playblast.
Display current/end time on SMPTE. Find it on the Frame Range panel in Output Properties.
"""

import bpy


def time_extra_info(self, context):
    get_addon = "amaranth" in context.preferences.addons.keys()
    if not get_addon:
        return

    scene = context.scene

    frame_count = "%s" % ((scene.frame_end - scene.frame_start) + 1)
    frame_count_preview = "%s" % ((scene.frame_preview_end - scene.frame_preview_start) + 1)

    layout = self.layout
    layout.use_property_split = True
    layout.use_property_decorate = False

    layout.separator()
    box = layout.box()
    col = box.column(align=True)
    col.active = False
    split = col.split(factor=0.4)

    col = split.column(align=True)
    row = col.row()
    row.alignment = 'RIGHT'
    row.label(text="Total Duration")
    row = col.row()
    row.alignment = 'RIGHT'
    row.label(text="Frames")

    if scene.use_preview_range:
        col.separator()
        row = col.row()
        row.alignment = 'RIGHT'
        row.label(text="Preview Duration")
        row = col.row()
        row.alignment = 'RIGHT'
        row.label(text="Frames")

    col = split.column(align=True)
    col.label(
        text="%s" %
        bpy.utils.smpte_from_frame(
            scene.frame_end -
            scene.frame_start))
    col.label(text=frame_count)

    if scene.use_preview_range:
        col.separator()
        col.label(
            text="%s" %
            bpy.utils.smpte_from_frame(
                scene.frame_preview_end -
                scene.frame_preview_start))
        col.label(text=frame_count_preview)


def register():
    bpy.types.RENDER_PT_frame_range.append(time_extra_info)


def unregister():
    bpy.types.RENDER_PT_frame_range.remove(time_extra_info)
