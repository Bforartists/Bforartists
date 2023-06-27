# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from .utils.functions import find_neighboring_markers
from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_set_preview_between_markers(bpy.types.Operator):
    """
    Set the timeline's preview range using the 2 markers closest to the time cursor
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
        return context.scene.sequence_editor

    def invoke(self, context, event):
        if not context.scene.timeline_markers:
            self.report({"ERROR_INVALID_INPUT"}, "There are no markers. Operation cancelled.")
            return {"CANCELLED"}

        frame = context.scene.frame_current
        previous_marker, next_marker = find_neighboring_markers(context, frame)

        if not (previous_marker and next_marker):
            self.report({"ERROR_INVALID_INPUT"}, "There are no markers. Operation cancelled.")
            return {"CANCELLED"}

        frame_start = previous_marker.frame if previous_marker else 0
        if next_marker:
            frame_end = next_marker.frame
        else:
            from operator import attrgetter

            frame_end = max(
                context.scene.sequence_editor.sequences, key=attrgetter("frame_final_end")
            ).frame_final_end

        from .utils.functions import set_preview_range

        set_preview_range(context, frame_start, frame_end)
        return {"FINISHED"}
