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

from .utils.global_settings import SequenceTypes
from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_grab_sequence_handles(bpy.types.Operator):
    """
    *brief* Grabs the sequence's handle based on the mouse position


    Extends the sequence based on the mouse position. If the cursor is to the
    right of the sequence's middle, it moves the right handle. If it's on the
    left side, it moves the left handle.
    """

    doc = {
        "name": doc_name(__qualname__),
        "demo": "",
        "description": doc_description(__doc__),
        "shortcuts": [
            ({"type": "G", "value": "PRESS", "shift": True}, {}, "Grab sequence handles")
        ],
        "keymap": "Sequencer",
    }
    bl_idname = doc_idname(__qualname__)
    bl_label = doc["name"]
    bl_description = doc_brief(doc["description"])
    bl_options = {"REGISTER", "UNDO"}

    always_find_closest: bpy.props.BoolProperty(name="Always find closest", default=False)
    frame: bpy.props.IntProperty(name="Frame", default=-1, options={"HIDDEN"})
    channel: bpy.props.IntProperty(name="Channel", default=-1, options={"HIDDEN"})

    @classmethod
    def poll(cls, context):
        return context.sequences

    def invoke(self, context, event):
        self.frame, self.channel = context.region.view2d.region_to_view(
            x=event.mouse_region_x, y=event.mouse_region_y
        )
        return self.execute(context)

    def execute(self, context):
        selection = context.selected_sequences
        if self.always_find_closest or not selection:
            if self.frame == -1:
                return {"CANCELLED"}
            bpy.ops.power_sequencer.select_closest_to_mouse(frame=self.frame, channel=self.channel)
            for s in context.selected_sequences:
                self.select_closest_handle(s)
        else:
            bpy.ops.sequencer.select_all(action="DESELECT")
            for s in selection:
                if s.type in SequenceTypes.EFFECT and not s.type == "COLOR":
                    self.select_closest_handle(s.input_1)
                    try:
                        self.select_closest_handle(s.input_2)
                    except AttributeError:
                        pass
                else:
                    self.select_closest_handle(s)
        return bpy.ops.transform.seq_slide("INVOKE_DEFAULT")

    def select_closest_handle(self, sequence):
        middle = sequence.frame_final_start + sequence.frame_final_duration / 2
        if self.frame >= middle:
            sequence.select_right_handle = True
        else:
            sequence.select_left_handle = True
        sequence.select = True
