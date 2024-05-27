# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from .utils.doc import doc_brief, doc_description, doc_idname, doc_name
from .utils.functions import (
    get_frame_range,
    get_mouse_frame_and_channel,
    slice_selection,
    ripple_move,
)


class POWER_SEQUENCER_OT_ripple_delete(bpy.types.Operator):
    """
    Delete selected strips and remove remaining gaps
    """

    doc = {
        "name": doc_name(__qualname__),
        "demo": "",
        "description": doc_description(__doc__),
        "shortcuts": [({"type": "X", "value": "PRESS", "shift": True}, {}, "Ripple Delete")],
        "keymap": "Sequencer",
    }
    bl_idname = doc_idname(__qualname__)
    bl_label = doc["name"]
    bl_description = doc_brief(doc["description"])
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.sequences

    def invoke(self, context, event):
        # Auto select if no strip selected
        frame, channel = get_mouse_frame_and_channel(context, event)
        if not context.selected_sequences:
            bpy.ops.power_sequencer.select_closest_to_mouse(frame=frame, channel=channel)
        if not context.selected_sequences:
            return {"CANCELLED"}
        return self.execute(context)

    def execute(self, context):
        scene = context.scene
        sequencer = bpy.ops.sequencer
        selection = context.selected_sequences
        selection_length = len(selection)

        audio_scrub_active = context.scene.use_audio_scrub
        context.scene.use_audio_scrub = False

        channels = list(set([s.channel for s in selection]))
        selection_blocks = slice_selection(context, selection)

        is_single_channel = len(channels) == 1
        if is_single_channel:
            for block in selection_blocks:
                delete_start = block[0].frame_final_start
                delete_end = block[-1].frame_final_end
                ripple_duration = abs(delete_end - delete_start)
                ripple_move(context, block, -ripple_duration, delete=True)

        else:
            cursor_frame = scene.frame_current
            for block in selection_blocks:
                sequencer.select_all(action="DESELECT")
                for s in block:
                    s.select = True
                selection_start = get_frame_range(block)[0]
                sequencer.delete()

                scene.frame_current = selection_start
                bpy.ops.power_sequencer.gap_remove()
            scene.frame_current = cursor_frame

        self.report(
            {"INFO"},
            "Deleted " + str(selection_length) + " sequence" + "s" if selection_length > 1 else "",
        )

        context.scene.use_audio_scrub = audio_scrub_active
        return {"FINISHED"}
