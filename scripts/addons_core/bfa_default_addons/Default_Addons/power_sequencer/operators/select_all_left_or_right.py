# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_select_all_left_or_right(bpy.types.Operator):
    """
    *Brief* Selects all strips left or right of the time cursor
    """

    doc = {
        "name": doc_name(__qualname__),
        "demo": "",
        "description": doc_description(__doc__),
        "shortcuts": [
            (
                {"type": "Q", "value": "PRESS", "shift": True},
                {"side": "LEFT"},
                "Select all strips to the LEFT of the time cursor",
            ),
            (
                {"type": "E", "value": "PRESS", "shift": True},
                {"side": "RIGHT"},
                "Select all strips to the right of the time cursor",
            ),
        ],
        "keymap": "Sequencer",
    }
    bl_idname = doc_idname(__qualname__)
    bl_label = doc["name"]
    bl_description = doc_brief(doc["description"])
    bl_options = {"REGISTER", "UNDO"}

    side: bpy.props.EnumProperty(
        name="Side",
        description=("Side to select"),
        items=[
            ("LEFT", "Left", "Move strips back in time, to the left"),
            ("RIGHT", "Right", "Move strips forward in time, to the right"),
        ],
        default="LEFT",
    )

    @classmethod
    def poll(cls, context):
        return context.sequences

    def execute(self, context):
        if self.side == "LEFT":
            for s in context.sequences:
                s.select = s.frame_final_end < context.scene.frame_current
        else:
            for s in context.sequences:
                s.select = s.frame_final_start > context.scene.frame_current
        return {"FINISHED"}
