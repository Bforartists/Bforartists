#
# Copyright (C) 2016-2019 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
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

from .utils.functions import find_neighboring_markers
from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_marker_go_to_next(bpy.types.Operator):
    """
    Moves the time cursor to the next marker
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

    target_marker: bpy.props.EnumProperty(
        items=[("left", "left", "left"), ("right", "right", "right")],
        name="Target marker",
        description="Move to the closest marker to the left or to the right of the cursor",
        default="left",
    )

    @classmethod
    def poll(cls, context):
        return context.scene

    def execute(self, context):
        if not context.scene.timeline_markers:
            self.report({"ERROR_INVALID_INPUT"}, "There are no markers. Operation cancelled.")
            return {"CANCELLED"}

        frame = context.scene.frame_current
        previous_marker, next_marker = find_neighboring_markers(context, frame)

        if (
            not previous_marker
            and self.target_marker == "left"
            or not next_marker
            and self.target_marker == "right"
        ):
            self.report({"INFO"}, "No more markers to jump to on the %s side." % self.target_marker)
            return {"CANCELLED"}

        previous_time = previous_marker.frame if previous_marker else None
        next_time = next_marker.frame if next_marker else None

        context.scene.frame_current = (
            previous_time if self.target_marker == "left" or not next_time else next_time
        )
        return {"FINISHED"}
