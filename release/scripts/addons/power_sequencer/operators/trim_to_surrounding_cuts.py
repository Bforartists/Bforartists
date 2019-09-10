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
"""
Find the two closest cuts, trims and deletes all strips above in the range but leaves some
margin. Removes the newly formed gap.
"""
import bpy
from math import floor

from .utils.functions import convert_duration_to_frames
from .utils.doc import doc_name, doc_idname, doc_brief, doc_description
from .utils.functions import (
    find_closest_surrounding_cuts_frames,
    sequencer_workaround_2_80_audio_bug,
)


class POWER_SEQUENCER_OT_trim_to_surrounding_cuts(bpy.types.Operator):
    """
    *Brief* Automatically trim to surrounding cuts with some time offset

    Finds the two cuts closest to the mouse cursor and trims the footage in between, leaving a little time offset. It's useful after you removed some bad audio but you need to keep some video around for a transition.
    By default, the tool leaves 0.2 a seconds margin on either side of the trim.
    """

    doc = {
        "name": doc_name(__qualname__),
        "demo": "",
        "description": doc_description(__doc__),
        "shortcuts": [
            (
                {"type": "LEFTMOUSE", "value": "PRESS", "shift": True, "alt": True},
                {},
                "Trim to Surrounding Cuts",
            )
        ],
        "keymap": "Sequencer",
    }
    bl_idname = doc_idname(__qualname__)
    bl_label = doc["name"]
    bl_description = doc_brief(doc["description"])
    bl_options = {"REGISTER", "UNDO"}

    margin: bpy.props.FloatProperty(
        name="Trim margin",
        description="Margin to leave on either sides of the trim in seconds",
        default=0.2,
        min=0,
    )
    gap_remove: bpy.props.BoolProperty(
        name="Remove gaps",
        description="When trimming the sequences, remove gaps automatically",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        return context

    def invoke(self, context, event):
        if not context.sequences:
            return {"CANCELLED"}

        sequencer = bpy.ops.sequencer

        # Convert mouse position to frame, channel
        x = context.region.view2d.region_to_view(x=event.mouse_region_x, y=event.mouse_region_y)[0]
        frame = round(x)

        left_cut_frame, right_cut_frame = find_closest_surrounding_cuts_frames(context, frame)
        surrounding_cut_frames_duration = abs(left_cut_frame - right_cut_frame)

        margin_frame = convert_duration_to_frames(context, self.margin)

        if surrounding_cut_frames_duration <= margin_frame * 2:
            self.report(
                {"WARNING"},
                ("The trim margin is larger than the gap\n" "Use snap trim or reduce the margin"),
            )
            return {"CANCELLED"}

        to_delete, to_trim = self.find_strips_in_range(context, left_cut_frame, right_cut_frame)
        trim_start, trim_end = (left_cut_frame + margin_frame, right_cut_frame - margin_frame)

        for s in to_trim:
            # If the strip is larger than the range to trim cut it in three
            if s.frame_final_start < trim_start and s.frame_final_end > trim_end:
                sequencer.select_all(action="DESELECT")
                s.select = True
                sequencer.cut(frame=trim_start, type="SOFT", side="RIGHT")
                sequencer.cut(frame=trim_end, type="SOFT", side="LEFT")
                to_delete.append(context.selected_sequences[0])
                continue

            if s.frame_final_start < trim_end and s.frame_final_end > trim_end:
                s.frame_final_start = trim_end
            elif s.frame_final_end > trim_start and s.frame_final_start < trim_start:
                s.frame_final_end = trim_start

        # Delete all sequences that are between the cuts
        sequencer.select_all(action="DESELECT")
        for s in to_delete:
            s.select = True
        sequencer.delete()

        if self.gap_remove:
            frame_to_remove_gap = right_cut_frame - 1 if frame == right_cut_frame else frame
            # bpy.ops.anim.change_frame(frame_to_remove_gap)
            context.scene.frame_current = frame_to_remove_gap
            bpy.ops.power_sequencer.gap_remove()
            context.scene.frame_current = trim_start

        # FIXME: Workaround Blender 2.80's audio bug, remove when fixed in Blender
        sequencer_workaround_2_80_audio_bug(context)

        return {"FINISHED"}

    def find_strips_in_range(
        self, context, start_frame, end_frame, sequences=None, find_overlapping=True
    ):
        """
        Returns strips which start and end within a certain frame range, or that overlap a
        certain frame range
        Args:
        - start_frame, the start of the frame range
        - end_frame, the end of the frame range
        - sequences (optional): only work with these sequences.
        If it doesn't receive any, the function works with all the sequences in the current context
        - find_overlapping (optional): find and return a list of strips that overlap the
          frame range

        Returns a tuple of two lists:
        [0], strips entirely in the frame range
        [1], strips that only overlap the frame range
        """
        strips_in_range = []
        strips_overlapping_range = []
        if not sequences:
            sequences = context.sequences
        for s in sequences:
            if start_frame <= s.frame_final_start <= end_frame:
                if start_frame <= s.frame_final_end <= end_frame:
                    strips_in_range.append(s)
                elif find_overlapping:
                    strips_overlapping_range.append(s)
            elif find_overlapping and start_frame <= s.frame_final_end <= end_frame:
                strips_overlapping_range.append(s)
            if s.frame_final_start < start_frame and s.frame_final_end > end_frame:
                strips_overlapping_range.append(s)
        return strips_in_range, strips_overlapping_range
