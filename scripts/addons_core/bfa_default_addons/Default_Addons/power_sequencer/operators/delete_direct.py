# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from .utils.functions import get_mouse_frame_and_channel
from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_delete_direct(bpy.types.Operator):
    """
    Deletes strips without confirmation, and cleans up crossfades nicely
    """

    doc = {
        "name": doc_name(__qualname__),
        "demo": "",
        "description": doc_description(__doc__),
        "shortcuts": [
            ({"type": "X", "value": "PRESS"}, {}, "Delete Direct"),
            (
                {"type": "X", "alt": True, "value": "PRESS"},
                {"is_removing_transitions": True},
                "Delete Direct with Transitions",
            ),
            ({"type": "DEL", "value": "PRESS"}, {}, "Delete Direct"),
            (
                {"type": "DEL", "alt": True, "value": "PRESS"},
                {"is_removing_transitions": True},
                "Delete Direct with Transitions",
            ),
        ],
        "keymap": "Sequencer",
    }
    bl_idname = doc_idname(__qualname__)
    bl_label = doc["name"]
    bl_description = doc_brief(doc["description"])
    bl_options = {"REGISTER", "UNDO"}

    is_removing_transitions: bpy.props.BoolProperty(name="Remove Transitions", default=False)

    @classmethod
    def poll(cls, context):
        return context.selected_sequences

    def invoke(self, context, event):
        frame, channel = get_mouse_frame_and_channel(context, event)
        if not context.selected_sequences:
            bpy.ops.power_sequencer.select_closest_to_mouse(frame=frame, channel=channel)
        return self.execute(context)

    def execute(self, context):
        selection = context.selected_sequences
        if self.is_removing_transitions and bpy.ops.power_sequencer.transitions_remove.poll():
            bpy.ops.power_sequencer.transitions_remove()
        bpy.ops.sequencer.delete()

        report_message = "Deleted " + str(len(selection)) + " sequence"
        report_message += "s" if len(selection) > 1 else ""
        self.report({"INFO"}, report_message)
        return {"FINISHED"}
