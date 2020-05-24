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

from .utils.functions import get_frame_range
from .utils.functions import set_preview_range
from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_preview_to_selection(bpy.types.Operator):
    """
    *brief* Sets the timeline preview range to match the selection

    Sets the scene frame start to the earliest frame start of selected sequences and the scene
    frame end to the last frame of selected sequences.
    Uses all sequences in the current context if no sequences are selected.
    """

    doc = {
        "name": doc_name(__qualname__),
        "demo": "https://i.imgur.com/EV1sUrn.gif",
        "description": doc_description(__doc__),
        "shortcuts": [
            ({"type": "P", "value": "PRESS", "ctrl": True, "alt": True}, {}, "Preview To Selection")
        ],
        "keymap": "Sequencer",
    }
    bl_idname = doc_idname(__qualname__)
    bl_label = doc["name"]
    bl_description = doc_brief(doc["description"])
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.sequences

    def execute(self, context):
        sequences = (
            context.selected_sequences
            if len(context.selected_sequences) >= 1
            else context.sequences
        )
        frame_start, frame_end = get_frame_range(sequences)
        set_preview_range(context, frame_start, frame_end - 1)
        return {"FINISHED"}
