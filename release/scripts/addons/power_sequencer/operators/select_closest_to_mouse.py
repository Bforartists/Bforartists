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

from .utils.functions import find_strips_mouse
from .utils.functions import get_mouse_frame_and_channel
from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_select_closest_to_mouse(bpy.types.Operator):
    """
    Select the closest strip under the mouse cursor
    """

    doc = {
        "name": doc_name(__qualname__),
        "demo": "",
        "description": doc_description(__doc__),
        "shortcuts": [],
        "keymap": "Sequencer",
    }
    bl_idname = doc_idname(__qualname__)
    bl_label = doc["name"]
    bl_description = doc_brief(doc["description"])
    bl_options = {"REGISTER", "UNDO"}

    frame: bpy.props.IntProperty(name="Frame")
    channel: bpy.props.IntProperty(name="Channel")

    @classmethod
    def poll(cls, context):
        return context.sequences

    def invoke(self, context, event):
        self.frame, self.channel = get_mouse_frame_and_channel(context, event)
        return self.execute(context)

    def execute(self, context):
        try:
            strip = find_strips_mouse(context, self.frame, self.channel)[0]
            strip.select = True
        except Exception:
            return {"CANCELLED"}
        return {"FINISHED"}
