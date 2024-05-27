# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from .utils.doc import doc_brief, doc_description, doc_idname, doc_name
from .utils.functions import convert_duration_to_frames


class POWER_SEQUENCER_OT_value_offset(bpy.types.Operator):
    """Instantly offset selected strips, either using frames or seconds. Allows to
    nudge the selection quickly, using keyboard shortcuts
    """

    doc = {
        "name": doc_name(__qualname__),
        "demo": "",
        "description": doc_description(__doc__),
        "shortcuts": [
            (
                {"type": "LEFT_ARROW", "value": "PRESS", "shift": True, "alt": True},
                {"direction": "left"},
                "Offset the selection to the left.",
            ),
            (
                {"type": "RIGHT_ARROW", "value": "PRESS", "shift": True, "alt": True},
                {"direction": "right"},
                "Offset the selection to the right.",
            ),
        ],
        "keymap": "Sequencer",
    }
    bl_idname = doc_idname(__qualname__)
    bl_label = doc["name"]
    bl_description = doc_brief(doc["description"])
    bl_options = {"REGISTER", "UNDO"}

    direction: bpy.props.EnumProperty(
        items=[
            ("left", "left", "Move the selection to the left"),
            ("right", "right", "Move the selection to the right"),
        ],
        name="Direction",
        description="Move the selection given frames or seconds",
        default="right",
        options={"HIDDEN"},
    )
    value_type: bpy.props.EnumProperty(
        items=[
            ("seconds", "Seconds", "Move with the value as seconds"),
            ("frames", "Frames", "Move with the value as frames"),
        ],
        name="Value Type",
        description="Toggle between offset in frames or seconds",
        default="seconds",
    )
    offset: bpy.props.FloatProperty(
        name="Offset",
        description="Offset amount to apply",
        default=1.0,
        step=5,
        precision=3,
    )

    @classmethod
    def poll(cls, context):
        return context.selected_sequences

    def invoke(self, context, event):
        self.offset = abs(self.offset)
        if self.direction == "left":
            self.offset *= -1.0
        return self.execute(context)

    def execute(self, context):
        offset_frames = (
            convert_duration_to_frames(context, self.offset)
            if self.value_type == "seconds"
            else self.offset
        )
        return bpy.ops.transform.seq_slide(value=(offset_frames, 0))
