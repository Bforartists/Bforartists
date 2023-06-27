# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from .utils.functions import get_sequences_under_cursor, move_selection
from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_snap_selection(bpy.types.Operator):
    """
    *Brief* Snap the entire selection to the time cursor.

    Automatically selects sequences if there is no active selection.
    To snap each strip individually, see Snap
    """

    doc = {
        "name": doc_name(__qualname__),
        "demo": "",
        "description": doc_description(__doc__),
        "shortcuts": [
            (
                {"type": "S", "value": "PRESS", "alt": True},
                {},
                "Snap selection to cursor",
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
        return context.sequences

    def execute(self, context):
        sequences = (
            context.selected_sequences
            if context.selected_sequences
            else get_sequences_under_cursor(context)
        )
        frame_first = min(sequences, key=lambda s: s.frame_final_start).frame_final_start
        time_offset = context.scene.frame_current - frame_first
        move_selection(context, sequences, time_offset)
        return {"FINISHED"}
