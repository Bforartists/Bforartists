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

from .utils.doc import doc_name, doc_idname, doc_brief, doc_description
from .utils.functions import get_mouse_frame_and_channel


class POWER_SEQUENCER_OT_split_strips_under_cursor(bpy.types.Operator):
    """
    Splits all strips under cursor including muted strips, but excluding locked strips.
    Auto selects sequences under the time cursor when you don't have a selection
    """

    doc = {
        "name": doc_name(__qualname__),
        "demo": "https://i.imgur.com/ZyEd0jD.gif",
        "description": doc_description(__doc__),
        "shortcuts": [({"type": "K", "value": "PRESS"}, {}, "Cut All Strips Under Cursor")],
        "keymap": "Sequencer",
    }
    bl_idname = doc_idname(__qualname__)
    bl_label = doc["name"]
    bl_description = doc_brief(doc["description"])
    bl_options = {"REGISTER", "UNDO"}

    side: bpy.props.EnumProperty(
        items=[("LEFT", "", ""), ("RIGHT", "", "")],
        name="Side",
        default="LEFT",
        options={"HIDDEN"},
    )

    @classmethod
    def poll(cls, context):
        return context.sequences

    def invoke(self, context, event):
        frame, channel = get_mouse_frame_and_channel(context, event)
        self.side = "LEFT" if frame < context.scene.frame_current else "RIGHT"
        return self.execute(context)

    def execute(self, context):
        # Deselect to trigger a call to select_strips_under_cursor below if the
        # time cursor doesn't overlap any of the selected strip: if so, it
        # can't cut anything!
        deselect = True
        for s in bpy.context.selected_sequences:
            if s.frame_final_start <= context.scene.frame_current <= s.frame_final_end:
                deselect = False
        if deselect:
            bpy.ops.sequencer.select_all(action="DESELECT")
        (context.selected_sequences or bpy.ops.power_sequencer.select_strips_under_cursor())
        return bpy.ops.sequencer.split(frame=context.scene.frame_current, side=self.side)
