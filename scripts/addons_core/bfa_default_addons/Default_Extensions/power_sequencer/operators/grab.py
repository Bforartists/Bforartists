# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from .utils.functions import get_mouse_frame_and_channel
from .utils.global_settings import SequenceTypes
from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_grab(bpy.types.Operator):
    """
    *brief* Grab and move sequences. Extends Blender's built-in grab tool


    Grab and move sequences. If you have no strips selected, it automatically
    finds the strip closest to the mouse and selects it. If you only select
    one or multiple crossfades, selects the handles on either side of the
    crossfades before moving sequences, using POWER_SEQUENCER_OT_crossfade_edit
    """

    doc = {
        "name": doc_name(__qualname__),
        "demo": "",
        "description": doc_description(__doc__),
        "shortcuts": [({"type": "G", "value": "PRESS"}, {}, "")],
        "keymap": "Sequencer",
    }
    bl_idname = doc_idname(__qualname__)
    bl_label = doc["name"]
    bl_description = doc_brief(doc["description"])
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.selected_sequences

    def invoke(self, context, event):
        frame, channel = get_mouse_frame_and_channel(context, event)
        if not context.selected_sequences:
            bpy.ops.power_sequencer.select_closest_to_mouse(frame=frame, channel=channel)
        return self.execute(context)

    def execute(self, context):
        if len(context.selected_sequences) == 0:
            return {"FINISHED"}

        strip = context.selected_sequences[0]
        if len(context.selected_sequences) == 1 and strip.type in SequenceTypes.TRANSITION:
            context.scene.sequence_editor.active_strip = strip
            return bpy.ops.power_sequencer.crossfade_edit()
        else:
            return bpy.ops.transform.seq_slide("INVOKE_DEFAULT")
