# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_marker_delete_direct(bpy.types.Operator):
    """
    Delete selected markers instantly skipping the default confirmation prompt
    """

    doc = {
        "name": doc_name(__qualname__),
        "demo": "",
        "description": doc_description(__doc__),
        "shortcuts": [({"type": "X", "value": "PRESS"}, {}, "Delete Markers Instantly")],
        "keymap": "Markers",
    }
    bl_idname = doc_idname(__qualname__)
    bl_label = doc["name"]
    bl_description = doc_brief(doc["description"])
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.scene.timeline_markers

    def execute(self, context):
        markers = context.scene.timeline_markers

        selected_markers = [m for m in markers if m.select]
        for m in selected_markers:
            markers.remove(m)
        self.report({"INFO"}, "Deleted %s markers." % len(selected_markers))
        return {"FINISHED"}
