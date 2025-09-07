# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from .utils.functions import slice_selection
from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_expand_to_surrounding_cuts(bpy.types.Operator):
    """
    *Brief* Expand selected strips to surrounding cuts

    Finds potential gaps surrounding each block of selected strips and extends the corresponding
    sequence handle to it
    """

    doc = {
        "name": doc_name(__qualname__),
        "demo": "",
        "description": doc_description(__doc__),
        "shortcuts": [
            (
                {"type": "E", "value": "PRESS", "ctrl": True},
                {},
                "Expand to Surrounding Cuts",
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
        description="When trimming the strips, remove gaps automatically",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        return context.selected_strips

    def invoke(self, context, event):
        sequence_blocks = slice_selection(context, context.selected_strips)
        for strips in sequence_blocks:
            strips_frame_start = min(
                strips, key=lambda s: s.frame_final_start
            ).frame_final_start
            strips_frame_end = max(strips, key=lambda s: s.frame_final_end).frame_final_end

            frame_left, frame_right = find_closest_cuts(
                context, strips_frame_start, strips_frame_end
            )
            if strips_frame_start == frame_left and strips_frame_end == frame_right:
                continue

            to_extend_left = [s for s in strips if s.frame_final_start == strips_frame_start]
            to_extend_right = [s for s in strips if s.frame_final_end == strips_frame_end]

            for s in to_extend_left:
                s.frame_final_start = (
                    frame_left if frame_left < strips_frame_start else strips_frame_start
                )
            for s in to_extend_right:
                s.frame_final_end = (
                    frame_right if frame_right > strips_frame_end else strips_frame_end
                )
        return {"FINISHED"}


def find_closest_cuts(context, frame_min, frame_max):
    frame_left = max(
        context.strips,
        key=lambda s: s.frame_final_end if s.frame_final_end <= frame_min else -1,
    ).frame_final_end
    frame_right = min(
        context.strips,
        key=lambda s: s.frame_final_start if s.frame_final_start >= frame_max else 1000000,
    ).frame_final_start
    return frame_left, frame_right
