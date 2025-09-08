# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from .utils.functions import get_frame_range
from .utils.functions import set_preview_range
from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_preview_to_selection(bpy.types.Operator):
    """
    *brief* Sets the timeline preview range to match the selection

    Sets the scene frame start to the earliest frame start of selected strips and the scene
    frame end to the last frame of selected strips.
    Uses all strips in the current context if no strips are selected.
    """

    doc = {
        "name": doc_name(__qualname__),
        "demo": "https://i.imgur.com/EV1sUrn.gif",
        "description": doc_description(__doc__),
        "shortcuts": [
            ({"type": "P", "value": "PRESS", "ctrl": True, "alt": True}, {}, "Preview To Selection")
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
            if len(context.selected_strips) >= 1
            else context.strips
        )
        frame_start, frame_end = get_frame_range(strips)
        set_preview_range(context, frame_start, frame_end - 1)
        return {"FINISHED"}
