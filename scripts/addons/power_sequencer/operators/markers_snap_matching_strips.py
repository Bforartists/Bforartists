# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_markers_snap_matching_strips(bpy.types.Operator):
    """
    Snap selected strips to markers with the same name
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

    @classmethod
    def poll(cls, context):
        return context.scene.timeline_markers

    def execute(self, context):
        timeline_markers = context.scene.timeline_markers

        for strip in context.selected_sequences:
            for marker in timeline_markers:
                if marker.name in strip.name:
                    strip.frame_start = marker.frame - strip.frame_offset_start
        return {"FINISHED"}
