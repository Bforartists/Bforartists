# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_fade_clear(bpy.types.Operator):
    """
    *brief* Removes fade animation from selected sequences

    Removes opacity or volume animation on selected sequences and resets the
    property to a value of 1.0. Works on all types of sequences
    """

    doc = {
        "name": doc_name(__qualname__),
        "demo": "",
        "description": doc_description(__doc__),
        "shortcuts": [
            (
                {"type": "F", "value": "PRESS", "alt": True, "ctrl": True},
                {},
                "Clear Fades",
            )
        ],
        "keymap": "Sequencer",
    }
    bl_idname = doc_idname(__qualname__)
    bl_label = doc["name"]
    bl_description = doc_brief(doc["description"])
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.selected_sequences

    def execute(self, context):
        fcurves = context.scene.animation_data.action.fcurves

        for sequence in context.selected_sequences:
            animated_property = "volume" if hasattr(sequence, "volume") else "blend_alpha"
            data_path = sequence.path_from_id() + "." + animated_property
            fcurve_map = {
                curve.data_path: curve
                for curve in fcurves
                if curve.data_path.startswith("sequence_editor.sequences_all")
            }
            curve = fcurve_map.get(data_path)
            if curve:
                fcurves.remove(curve)
            setattr(sequence, animated_property, 1.0)

        return {"FINISHED"}
