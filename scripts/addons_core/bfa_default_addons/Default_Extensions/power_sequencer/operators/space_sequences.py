# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from .utils.functions import convert_duration_to_frames
from .utils.global_settings import SequenceTypes
from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_space_sequences(bpy.types.Operator):
    """
    *brief* Offsets all strips to the right of the time cursor by a given duration, ignoring locked sequences
    """

    doc = {
        "name": doc_name(__qualname__),
        "demo": "",
        "description": doc_description(__doc__),
        "shortcuts": [({"type": "EQUAL", "value": "PRESS"}, {}, "")],
        "keymap": "Sequencer",
    }
    bl_idname = doc_idname(__qualname__)
    bl_label = doc["name"]
    bl_description = doc_brief(doc["description"])
    bl_options = {"REGISTER", "UNDO"}

    gap_to_insert: bpy.props.FloatProperty(
        name="Duration", description="The time offset to apply to the strips", default=1.0
    )

    @classmethod
    def poll(cls, context):
        return context.sequences

    def invoke(self, context, event):
        sequences = [
            s
            for s in context.sequences
            if s.type in SequenceTypes.CUTABLE
            and s.frame_final_start >= context.scene.frame_current
            and not s.lock
        ]

        gap_frames = convert_duration_to_frames(context, self.gap_to_insert)
        sorted_sequences = sorted(sequences, key=lambda s: s.frame_final_start, reverse=True)
        for s in sorted_sequences:
            s.frame_start += gap_frames

        markers = context.scene.timeline_markers
        for m in [m for m in markers if m.frame >= context.scene.frame_current]:
            m.frame += gap_frames
        return {"FINISHED"}
