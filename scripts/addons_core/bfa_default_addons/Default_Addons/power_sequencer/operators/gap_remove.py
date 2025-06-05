# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from operator import attrgetter

from .utils.doc import doc_name, doc_idname, doc_brief, doc_description
from .utils.functions import slice_selection


class POWER_SEQUENCER_OT_gap_remove(bpy.types.Operator):
    """
    Remove gaps, starting from the first frame, with the ability to ignore locked strips
    """

    doc = {
        "name": doc_name(__qualname__),
        "demo": "",
        "description": doc_description(__doc__),
        "shortcuts": [],
        "keymap": "Sequencer",
    }
    bl_idname = doc_idname(__qualname__)
    bl_label = doc["name"]
    bl_description = doc_brief(doc["description"])
    bl_options = {"REGISTER", "UNDO"}

    ignore_locked: bpy.props.BoolProperty(
        name="Ignore Locked Strips",
        description="Remove gaps without moving locked strips",
        default=True,
    )
    all: bpy.props.BoolProperty(
        name="Remove All",
        description="Remove all gaps starting from the time cursor",
        default=False,
    )
    frame: bpy.props.IntProperty(
        name="Frame",
        description="Frame to remove gaps from, defaults at the time cursor",
        default=-1,
    )
    move_time_cursor: bpy.props.BoolProperty(
        name="Move Time Cursor",
        description="Move the time cursor when closing the gap",
        default=False,
    )

    @classmethod
    def poll(cls, context):
        return context.sequences

    def execute(self, context):
        frame = self.frame if self.frame >= 0 else context.scene.frame_current
        sequences = (
            [s for s in context.sequences if not s.lock]
            if self.ignore_locked
            else context.sequences
        )
        sequences = [
            s for s in sequences if s.frame_final_start >= frame or s.frame_final_end > frame
        ]
        sequence_blocks = slice_selection(context, sequences)
        if not sequence_blocks:
            return {"FINISHED"}

        gap_frame = self.find_gap_frame(context, frame, sequence_blocks[0])
        if gap_frame == -1:
            return {"FINISHED"}

        first_block_start = min(
            sequence_blocks[0], key=attrgetter("frame_final_start")
        ).frame_final_start
        blocks_after_gap = (
            sequence_blocks[1:] if first_block_start <= gap_frame else sequence_blocks
        )

        self.gaps_remove(context, blocks_after_gap, gap_frame)
        if self.move_time_cursor:
            context.scene.frame_current = gap_frame
        return {"FINISHED"}

    def find_gap_frame(self, context, frame, sorted_sequences):
        """
        Finds and returns the frame at which the gap starts.
        Takes a list sequences sorted by frame_final_start.
        """
        strips_start = min(sorted_sequences, key=attrgetter("frame_final_start")).frame_final_start
        strips_end = max(sorted_sequences, key=attrgetter("frame_final_end")).frame_final_end

        gap_frame = -1
        if strips_start > frame:
            strips_before_frame_start = [s for s in context.sequences if s.frame_final_end <= frame]
            frame_target = 0
            if strips_before_frame_start:
                frame_target = max(
                    strips_before_frame_start, key=attrgetter("frame_final_end")
                ).frame_final_end
            gap_frame = frame_target if frame_target < strips_start else frame
        else:
            gap_frame = strips_end
        return gap_frame

    def gaps_remove(self, context, sequence_blocks, gap_frame_start):
        """
        Recursively removes gaps between blocks of sequences.
        """

        gap_frame = gap_frame_start
        for block in sequence_blocks:
            gap_size = block[0].frame_final_start - gap_frame
            if gap_size < 1:
                continue

            for s in block:
                try:
                    s.frame_start -= gap_size
                except AttributeError:
                    continue

            self.move_markers(context, gap_frame, gap_size)
            if not self.all:
                break
            gap_frame = block[-1].frame_final_end

    def move_markers(self, context, gap_frame, gap_size):
        markers = (m for m in context.scene.timeline_markers if m.frame > gap_frame)
        for m in markers:
            m.frame -= min({gap_size, m.frame - gap_frame})
