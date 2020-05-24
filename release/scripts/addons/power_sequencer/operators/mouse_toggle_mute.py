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
"""Toggle mute a sequence as you click on it"""
import bpy
from math import floor

from .utils.functions import find_strips_mouse
from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_mouse_toggle_mute(bpy.types.Operator):
    """
    Toggle mute a sequence as you click on it
    """

    doc = {
        "name": doc_name(__qualname__),
        "demo": "",
        "description": doc_description(__doc__),
        "shortcuts": [
            ({"type": "LEFTMOUSE", "value": "PRESS", "alt": True}, {}, "Mouse Toggle Mute")
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

    def invoke(self, context, event):
        sequencer = bpy.ops.sequencer

        # get current frame and channel the mouse hovers
        x, y = context.region.view2d.region_to_view(x=event.mouse_region_x, y=event.mouse_region_y)
        frame, channel = round(x), floor(y)

        # Strip selection
        sequencer.select_all(action="DESELECT")
        to_select = find_strips_mouse(context, frame, channel)

        if not to_select:
            return {"CANCELLED"}

        for s in to_select:
            s.mute = not s.mute
        return {"FINISHED"}
