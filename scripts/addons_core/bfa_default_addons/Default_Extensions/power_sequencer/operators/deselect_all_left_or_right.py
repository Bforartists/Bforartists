# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_deselect_all_strips_left_or_right(bpy.types.Operator):
    """
    Deselects all the strips at the left or right of the time cursor, based on the position
    of the mouse
    """

    doc = {
        "name": doc_name(__qualname__),
        "demo": "",
        "description": doc_description(__doc__),
        "shortcuts": [
            (
                {"type": "Q", "value": "PRESS", "alt": True},
                {"side": "left"},
                "Deselect all strips to the left of the time cursor",
            ),
            (
                {"type": "E", "value": "PRESS", "alt": True},
                {"side": "right"},
                "Deselect all strips to the right of the time cursor",
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
        description="The side to deselect",
        items=[
            (
                "mouse",
                "Mouse position",
                ("Deselect based on the mouse position relative to the" " time cursor"),
            ),
            ("left", "Left", "Left of the time cursor"),
            ("right", "Right", "Right of the time cursor"),
        ],
        default="mouse",
    )

    @classmethod
    def poll(cls, context):
        return context.selected_sequences

    def invoke(self, context, event):
        frame_current = context.scene.frame_current
        frame_mouse = context.region.view2d.region_to_view(event.mouse_region_x, 1)[0]

        for s in context.sequences:
            if self.side == "left" or frame_mouse < frame_current and self.side == "mouse":
                if s.frame_final_end < frame_current:
                    self.deselect(s)
            elif self.side == "right" or frame_mouse >= frame_current and self.side == "mouse":
                if s.frame_final_start >= frame_current:
                    self.deselect(s)
        return {"FINISHED"}

    def deselect(self, strip):
        strip.select = False
        strip.select_left_handle = False
        strip.select_right_handle = False
