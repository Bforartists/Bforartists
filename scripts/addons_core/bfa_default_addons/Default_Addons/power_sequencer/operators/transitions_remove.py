# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from operator import attrgetter

from .utils.global_settings import SequenceTypes
from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_transitions_remove(bpy.types.Operator):
    """
    Delete a crossfade strip and moves the handles of the input strips to form a cut again
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

    sequences_override = []

    @classmethod
    def poll(cls, context):
        return context.selected_sequences

    def execute(self, context):
        to_process = (
            self.sequences_override if self.sequences_override else context.selected_sequences
        )

        transitions = [s for s in to_process if s.type in SequenceTypes.TRANSITION]
        if not transitions:
            return {"FINISHED"}

        saved_selection = [
            s for s in context.selected_sequences if s.type not in SequenceTypes.TRANSITION
        ]
        bpy.ops.sequencer.select_all(action="DESELECT")
        for transition in transitions:
            effect_middle_frame = round(
                (transition.frame_final_start + transition.frame_final_end) / 2
            )

            inputs = [transition.input_1, transition.input_2]
            strips_to_edit = []
            for input in inputs:
                if input.type in SequenceTypes.EFFECT and hasattr(input, "input_1"):
                    strips_to_edit.append(input.input_1)
                else:
                    strips_to_edit.append(input)

            strip_1 = min(strips_to_edit, key=attrgetter("frame_final_end"))
            strip_2 = max(strips_to_edit, key=attrgetter("frame_final_end"))

            strip_1.frame_final_end = effect_middle_frame
            strip_2.frame_final_start = effect_middle_frame

            transition.select = True
            bpy.ops.sequencer.delete()

        for s in saved_selection:
            s.select = True
        return {"FINISHED"}
