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
from operator import attrgetter

from .utils.doc import doc_name, doc_idname, doc_brief, doc_description
from .utils.functions import (
    slice_selection,
    get_frame_range,
    get_channel_range,
    trim_strips,
    find_strips_in_range,
)


class POWER_SEQUENCER_OT_channel_offset(bpy.types.Operator):
    """
    Move selected strip to the nearest open channel above/down
    """

    doc = {
        "name": doc_name(__qualname__),
        "demo": "",
        "description": doc_description(__doc__),
        "shortcuts": [
            (
                {"type": "UP_ARROW", "value": "PRESS", "alt": True},
                {"direction": "up"},
                "Move to Open Channel Above",
            ),
            (
                {"type": "UP_ARROW", "value": "PRESS", "ctrl": True, "alt": True},
                {"direction": "up", "trim_target_channel": True},
                "Move to Channel Above and Trim",
            ),
            (
                {"type": "DOWN_ARROW", "value": "PRESS", "alt": True},
                {"direction": "down"},
                "Move to Open Channel Below",
            ),
            (
                {"type": "DOWN_ARROW", "value": "PRESS", "ctrl": True, "alt": True},
                {"direction": "down", "trim_target_channel": True},
                "Move to Channel Below and Trim",
            ),
        ],
        "keymap": "Sequencer",
    }
    bl_idname = doc_idname(__qualname__)
    bl_label = doc["name"]
    bl_description = doc_brief(doc["description"])
    bl_options = {"REGISTER", "UNDO"}

    direction: bpy.props.EnumProperty(
        items=[
            ("up", "up", "Move the selection 1 channel up"),
            ("down", "down", "Move the selection 1 channel down"),
        ],
        name="Direction",
        description="Move the sequences up or down",
        default="up",
    )
    trim_target_channel: bpy.props.BoolProperty(
        name="Trim strips",
        description="Trim strips to make space in the target channel",
        default=False,
    )

    @classmethod
    def poll(cls, context):
        return context.selected_sequences

    def execute(self, context):
        selection = [s for s in context.selected_sequences if not s.lock]
        if not selection:
            return {"FINISHED"}

        selection_blocks = slice_selection(context, selection)
        for block in selection_blocks:
            sequences = sorted(block, key=attrgetter("channel", "frame_final_start"))
            frame_start, frame_end = get_frame_range(sequences)
            channel_start, channel_end = get_channel_range(sequences)

            if self.trim_target_channel:
                to_delete, to_trim = find_strips_in_range(frame_start, frame_end, context.sequences)
                channel_trim = (
                    channel_end + 1 if self.direction == "up" else max(1, channel_start - 1)
                )
                to_trim = [s for s in to_trim if s.channel == channel_trim]
                to_delete = [s for s in to_delete if s.channel == channel_trim]
                trim_strips(context, frame_start, frame_end, to_trim, to_delete)

            if self.direction == "up":
                for s in reversed(sequences):
                    s.channel += 1
            elif self.direction == "down":
                for s in sequences:
                    s.channel = max(1, s.channel - 1)
        return {"FINISHED"}
