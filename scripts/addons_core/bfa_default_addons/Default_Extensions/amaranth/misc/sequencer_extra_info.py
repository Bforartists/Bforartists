# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
Sequencer: Display Image File Name

When seeking through an image sequence, display the active strips' file name
for the current frame, and it's [playhead].

Find it on the VSE header.
"""
import bpy


# FEATURE: Sequencer Extra Info
def act_strip(context):
    try:
        return context.scene.sequence_editor.active_strip
    except AttributeError:
        return None


def ui_sequencer_extra_info(self, context):
    layout = self.layout
    strip = act_strip(context)
    if strip:
        seq_type = strip.type
        if seq_type and seq_type == 'IMAGE':
            elem = strip.strip_elem_from_frame(context.scene.frame_current)
            if elem:
                layout.label(
                    text="%s %s" %
                    (elem.filename, "[%s]" %
                     (context.scene.frame_current - strip.frame_start)))

# // FEATURE: Sequencer Extra Info


def register():
    bpy.types.SEQUENCER_HT_header.append(ui_sequencer_extra_info)


def unregister():
    bpy.types.SEQUENCER_HT_header.remove(ui_sequencer_extra_info)
