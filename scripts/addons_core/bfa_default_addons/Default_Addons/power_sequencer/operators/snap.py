# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from .utils.functions import get_sequences_under_cursor
from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_snap(bpy.types.Operator):
    """
    *Brief* Snaps selected strips to the time cursor ignoring locked strips.

    Automatically selects strips if there is no active selection
    """

    doc = {
        "name": doc_name(__qualname__),
        "demo": "",
        "description": doc_description(__doc__),
        "shortcuts": [
            (
                {"type": "S", "value": "PRESS", "shift": True},
                {},
                "Snap strips to cursor",
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
        return context.strips

    def execute(self, context):
        strips = (
            context.selected_strips
            if len(context.selected_strips) > 0
            else get_sequences_under_cursor(context)
        )
        frame = context.scene.frame_current
        for s in strips:
            s.select = True
        bpy.ops.sequencer.snap(frame=frame)
        return {"FINISHED"}
