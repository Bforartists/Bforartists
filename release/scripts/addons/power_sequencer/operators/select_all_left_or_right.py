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
        return bpy.ops.sequencer.select("INVOKE_DEFAULT", left_right=self.side)
