# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors

# This file is part of Power Sequencer.

import bpy

from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_playback_speed_set(bpy.types.Operator):
    """
    Change the playback_speed property using an operator property. Used with keymaps
    """

    doc = {
        "name": doc_name(__qualname__),
        "demo": "",
        "description": doc_description(__doc__),
        "shortcuts": [
            ({"type": "ONE", "ctrl": True, "value": "PRESS"}, {"speed": "NORMAL"}, "Speed to 1x"),
            ({"type": "TWO", "ctrl": True, "value": "PRESS"}, {"speed": "FAST"}, "Speed to 1.33x"),
            (
                {"type": "THREE", "ctrl": True, "value": "PRESS"},
                {"speed": "FASTER"},
                "Speed to 1.66x",
            ),
            ({"type": "FOUR", "ctrl": True, "value": "PRESS"}, {"speed": "DOUBLE"}, "Speed to 2x"),
            ({"type": "FIVE", "ctrl": True, "value": "PRESS"}, {"speed": "TRIPLE"}, "Speed to 3x"),
        ],
        "keymap": "Sequencer",
    }
    bl_idname = doc_idname(__qualname__)
    bl_label = doc["name"]
    bl_description = doc_brief(doc["description"])
    bl_options = {"REGISTER"}

    speed: bpy.props.EnumProperty(
        items=[
            ("NORMAL", "Normal (1x)", ""),
            ("FAST", "Fast (1.33x)", ""),
            ("FASTER", "Faster (1.66x)", ""),
            ("DOUBLE", "Double (2x)", ""),
            ("TRIPLE", "Triple (3x)", ""),
        ],
        name="Speed",
        description="Change the playback speed",
        default="DOUBLE",
    )

    @classmethod
    def poll(cls, context):
        return context.sequences

    def execute(self, context):
        context.scene.power_sequencer.playback_speed = self.speed
        return {"FINISHED"}
