# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_toggle_selected_mute(bpy.types.Operator):
    """
    Mute or unmute selected sequences
    """

    doc = {
        "name": doc_name(__qualname__),
        "demo": "",
        "description": doc_description(__doc__),
        "shortcuts": [
            (
                {"type": "H", "value": "PRESS"},
                {"use_unselected": False},
                "Mute or Unmute Selected Strips",
            ),
            (
                {"type": "H", "value": "PRESS", "alt": True},
                {"use_unselected": True},
                "Mute or Unmute Selected Strips",
            ),
        ],
        "keymap": "Sequencer",
    }
    bl_idname = doc_idname(__qualname__)
    bl_label = doc["name"]
    bl_description = doc_brief(doc["description"])
    bl_options = {"REGISTER", "UNDO"}

    use_unselected: bpy.props.BoolProperty(
        name="Use unselected", description="Toggle non selected sequences", default=False
    )

    @classmethod
    def poll(cls, context):
        return context.selected_sequences

    def execute(self, context):
        selection = context.selected_sequences

        if self.use_unselected:
            selection = [s for s in context.sequences if s not in selection]

        if not selection:
            self.report({"WARNING"}, "No sequences to toggle muted")
            return {"CANCELLED"}

        mute = not selection[0].mute
        for s in selection:
            s.mute = mute
        return {"FINISHED"}
