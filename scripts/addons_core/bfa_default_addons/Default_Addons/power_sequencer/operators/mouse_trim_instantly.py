# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from math import floor

from .utils.functions import find_strips_mouse
from .utils.functions import trim_strips
from .utils.functions import get_frame_range
from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_mouse_trim_instantly(bpy.types.Operator):
    """
    *brief* Trim strip from a start to an end frame instantly


    Trims a frame range or a selection from a start to an end frame.
    If there's no precise time range, auto trims based on the closest cut

    Args:
    - frame_start and frame_end (int) define the frame range to trim
    """

    doc = {
        "name": doc_name(__qualname__),
        "demo": "",
        "description": doc_description(__doc__),
        "shortcuts": [
            (
                {"type": "RIGHTMOUSE", "value": "PRESS", "ctrl": True, "alt": True},
                {"select_mode": "CONTEXT"},
                "Trim strip, keep gap",
            ),
            (
                {"type": "RIGHTMOUSE", "value": "PRESS", "ctrl": True, "alt": True, "shift": True},
                {"select_mode": "CURSOR"},
                "Trim strip, remove gap",
            ),
        ],
        "keymap": "Sequencer",
    }
    bl_idname = doc_idname(__qualname__)
    bl_label = doc["name"]
    bl_description = doc_brief(doc["description"])
    bl_options = {"REGISTER", "UNDO"}

    select_mode: bpy.props.EnumProperty(
        items=[
            ("CONTEXT", "Smart", "Uses the selection if possible, else uses the other modes"),
            ("CURSOR", "Time cursor", "Select all of the strips the time cursor overlaps"),
        ],
        name="Selection mode",
        description="Auto-select the strip you click on or that the time cursor overlaps",
        default="CONTEXT",
    )
    select_linked: bpy.props.BoolProperty(
        name="Use linked time",
        description="If auto-select, cut linked strips if checked",
        default=False,
    )
    gap_remove: bpy.props.BoolProperty(
        name="Remove gaps",
        description="When trimming the sequences, remove gaps automatically",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        return context.sequences

    def invoke(self, context, event):
        to_trim = []
        frame, channel = -1, -1
        x, y = context.region.view2d.region_to_view(x=event.mouse_region_x, y=event.mouse_region_y)
        frame, channel = round(x), floor(y)

        mouse_clicked_strip = find_strips_mouse(context, frame, channel, self.select_linked)
        to_trim += mouse_clicked_strip
        if self.select_mode == "CURSOR" or (self.select_mode == "CONTEXT" and to_trim == []):
            to_trim += [
                s
                for s in context.sequences
                if s.frame_final_start <= frame <= s.frame_final_end and not s.lock
            ]
        if not to_trim:
            return {"FINISHED"}

        frame_cut_closest = min(get_frame_range(to_trim), key=lambda f: abs(frame - f))
        frame_start = min(frame, frame_cut_closest)
        frame_end = max(frame, frame_cut_closest)

        trim_strips(context, frame_start, frame_end, to_trim=to_trim)

        context.scene.frame_current = frame

        if self.gap_remove and self.select_mode == "CURSOR":
            bpy.ops.power_sequencer.gap_remove(frame=frame_start, move_time_cursor=True)

        return {"FINISHED"}
