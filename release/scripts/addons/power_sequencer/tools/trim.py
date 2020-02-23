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
from bpy.types import WorkSpaceTool


class POWER_SEQUENCER_TOOL_Trim(WorkSpaceTool):
    bl_space_type = "SEQUENCE_EDITOR"
    bl_context_mode = "SEQUENCER"

    bl_idname = "power_sequencer.trim"
    bl_label = "Trim"
    bl_description = "Cut and trim strips with the mouse"
    bl_icon = "ops.mesh.knife_tool"
    bl_widget = None
    bl_keymap = (
        (
            "power_sequencer.mouse_trim",
            {"type": "LEFTMOUSE", "value": "PRESS"},
            {"select_mode": "CONTEXT", "gap_remove": False},
        ),
        (
            "power_sequencer.mouse_trim",
            {"type": "LEFTMOUSE", "value": "PRESS", "shift": True},
            {"select_mode": "CURSOR", "gap_remove": True},
        ),
    )

    def draw_settings(context, layout, tool):
        props = tool.operator_properties("power_sequencer.mouse_trim")
        layout.prop(props, "mode")
