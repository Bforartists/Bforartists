# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

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
