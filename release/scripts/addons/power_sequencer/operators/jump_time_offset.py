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

from .utils.functions import convert_duration_to_frames
from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_jump_time_offset(bpy.types.Operator):
    """
    *brief* Jump forward or backward in time


    Move the time cursor forward or backward, using a duration in seconds.

    The equivalent tool in Blender only works with frames, meaning the jump
    will be different if your project's framerate is different. This tool
    fixes that issue.
    """

    doc = {
        "name": doc_name(__qualname__),
        "demo": "",
        "description": doc_description(__doc__),
        "shortcuts": [
            (
                {"type": "RIGHT_ARROW", "value": "PRESS", "shift": True},
                {"direction": "forward"},
                "Jump Forward",
            ),
            (
                {"type": "LEFT_ARROW", "value": "PRESS", "shift": True},
                {"direction": "backward"},
                "Jump Backward",
            ),
        ],
        "keymap": "Frames",
    }
    bl_idname = doc_idname(__qualname__)
    bl_label = doc["name"]
    bl_description = doc_brief(doc["description"])
    bl_options = {"REGISTER"}

    duration: bpy.props.FloatProperty(
        name="Duration",
        description="The length of the jump in seconds (default: 1.0)",
        default=1.0,
        min=0,
    )
    direction: bpy.props.EnumProperty(
        name="Direction",
        description="Jump direction, either forward or backward",
        items=[
            ("forward", "Forward", "Jump forward in time"),
            ("backward", "Backward", "Jump backward in time"),
        ],
    )

    @classmethod
    def poll(cls, context):
        return context.scene

    def execute(self, context):
        direction = 1 if self.direction == "forward" else -1
        context.scene.frame_current += (
            convert_duration_to_frames(context, self.duration) * direction
        )
        return {"FINISHED"}
