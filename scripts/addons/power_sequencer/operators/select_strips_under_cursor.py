# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from .utils.functions import get_sequences_under_cursor
from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_select_strips_under_cursor(bpy.types.Operator):
    """
    Selects the strips that are currently under the time cursor
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

    deselect_first: bpy.props.BoolProperty(name="Deselect First")

    @classmethod
    def poll(cls, context):
        return context.sequences

    def execute(self, context):
        if self.deselect_first:
            bpy.ops.sequencer.select_all(action="DESELECT")
        for s in get_sequences_under_cursor(context):
            s.select = True
        return {"FINISHED"}
