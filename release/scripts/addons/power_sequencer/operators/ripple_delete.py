#
# Copyright (C) 2016-2019 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# This file is part of Power Sequencer.
#
# Power Sequencer is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Power Sequencer is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with Power Sequencer. If
# not, see <https://www.gnu.org/licenses/>.
#
import bpy
from operator import attrgetter

from .utils.doc import doc_brief, doc_description, doc_idname, doc_name
from .utils.functions import get_frame_range
from .utils.functions import get_mouse_frame_and_channel
from .utils.global_settings import SequenceTypes
from .utils.functions import slice_selection


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

        audio_scrub_active = context.scene.use_audio_scrub
        context.scene.use_audio_scrub = False

        channels = list(set([s.channel for s in selection]))
        selection_blocks = slice_selection(context, selection)

        is_single_channel = len(channels) == 1
        if is_single_channel:
            first_strip = selection_blocks[0][0]
            for block in selection_blocks:
                sequencer.select_all(action="DESELECT")
                block_strip_start = block[0]
                delete_start = block_strip_start.frame_final_start
                delete_end = block[-1].frame_final_end
                ripple_length = delete_end - delete_start
                assert ripple_length > 0

                for s in block:
                    s.select = True
                sequencer.delete()

                strips_in_channel = [
                    s
                    for s in bpy.context.sequences
                    if s.channel == channels[0]
                    and s.frame_final_start >= first_strip.frame_final_start
                ]
                strips_in_channel = sorted(strips_in_channel, key=attrgetter("frame_final_start"))
                to_ripple = [s for s in strips_in_channel if s.frame_final_start > delete_start]
                for s in to_ripple:
                    s.frame_start -= ripple_length

        else:
            for block in selection_blocks:
                sequencer.select_all(action="DESELECT")
                for s in block:
                    s.select = True
                selection_start, _ = get_frame_range(context, block)
                sequencer.delete()

                scene.frame_current = selection_start
                bpy.ops.power_sequencer.gap_remove()

        self.report(
            {"INFO"},
            "Deleted " + str(len(selection)) + " sequence" + "s" if len(selection) > 1 else "",
        )

        context.scene.use_audio_scrub = audio_scrub_active
        return {"FINISHED"}
