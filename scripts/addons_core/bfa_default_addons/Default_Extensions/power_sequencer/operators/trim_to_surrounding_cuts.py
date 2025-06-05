# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Find the two closest cuts, trims and deletes all strips above in the range but leaves some
margin. Removes the newly formed gap.
"""
import bpy

from .utils.functions import convert_duration_to_frames, trim_strips
from .utils.doc import doc_name, doc_idname, doc_brief, doc_description
from .utils.functions import find_closest_surrounding_cuts_frames, find_strips_in_range


class POWER_SEQUENCER_OT_trim_to_surrounding_cuts(bpy.types.Operator):
    """*Brief* Automatically trim to surrounding cuts with some time offset

    Finds the two cuts closest to the mouse cursor and trims the footage in between, leaving a
    little time offset. It's useful after you removed some bad audio but you need to keep some
    video around for a transition.

    By default, the tool leaves a 0.2 seconds margin on either side of the trim
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

        frame = context.region.view2d.region_to_view(
            x=event.mouse_region_x, y=event.mouse_region_y
        )[0]
        frame = round(frame)

        margin_frame = convert_duration_to_frames(context, self.margin)
        left_cut_frame, right_cut_frame = find_closest_surrounding_cuts_frames(context, frame)
        if abs(left_cut_frame - right_cut_frame) <= margin_frame * 2:
            self.report(
                {"WARNING"},
                ("The trim margin is larger than the gap\n" "Use snap trim or reduce the margin"),
            )
            return {"CANCELLED"}

        to_delete, to_trim = find_strips_in_range(
            left_cut_frame, right_cut_frame, context.sequences
        )
        trim_start, trim_end = (left_cut_frame + margin_frame, right_cut_frame - margin_frame)

        trim_strips(context, trim_start, trim_end, to_trim, to_delete)

        if self.gap_remove:
            frame_to_remove_gap = right_cut_frame - 1 if frame == right_cut_frame else frame
            # bpy.ops.anim.change_frame(frame_to_remove_gap)
            context.scene.frame_current = frame_to_remove_gap
            bpy.ops.power_sequencer.gap_remove()
            context.scene.frame_current = trim_start

        return {"FINISHED"}
