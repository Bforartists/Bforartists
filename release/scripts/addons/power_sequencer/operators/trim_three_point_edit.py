#
# Copyright (C) 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
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

from .utils.functions import get_mouse_frame_and_channel
from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_trim_three_point_edit(bpy.types.Operator):
    """
    Trim the closest strip under the mouse cursor in or out
    """

    doc = {
        "name": doc_name(__qualname__),
        "demo": "",
        "description": doc_description(__doc__),
        "shortcuts": [
            ({"type": "I", "value": "PRESS"}, {"side": "LEFT"}, "Trim In"),
            ({"type": "O", "value": "PRESS"}, {"side": "RIGHT"}, "Trim Out"),
        ],
        "keymap": "Sequencer",
    }
    bl_idname = doc_idname(__qualname__)
    bl_label = doc["name"]
    bl_description = doc_brief(doc["description"])
    bl_options = {"REGISTER", "UNDO"}

    side: bpy.props.EnumProperty(
        items=[("LEFT", "Left", "Left side"), ("RIGHT", "Right", "Right side")],
        name="Trim side",
        description="Side of the strip(s) to trim, either LEFT or RIGHT",
        default="LEFT",
    )

    @classmethod
    def poll(cls, context):
        return context.sequences

    def invoke(self, context, event):
        frame, channel = get_mouse_frame_and_channel(context, event)
        bpy.ops.sequencer.select_all(action="DESELECT")
        bpy.ops.power_sequencer.select_closest_to_mouse(frame=frame, channel=channel)
        if not context.selected_sequences:
            bpy.ops.power_sequencer.select_strips_under_cursor()
        return self.execute(context)

    def execute(self, context):
        if not context.selected_sequences:
            return {"CANCELLED"}
        bpy.ops.power_sequencer.trim_left_or_right_handles(side=self.side)
        return {"FINISHED"}
