# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
import bpy
from math import ceil

from .utils.global_settings import SequenceTypes
from .utils.functions import slice_selection
from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_speed_up_movie_strip(bpy.types.Operator):
    """
    *brief* Adds a speed effect to the  2x speed, set frame end, wrap both into META

    Add 2x speed to strip and set its frame end accordingly. Wraps both the strip and the speed
    modifier into a META strip.
    """

    doc = {
        "name": doc_name(__qualname__),
        "demo": "https://i.imgur.com/ZyEd0jD.gif",
        "description": doc_description(__doc__),
        "shortcuts": [
            (
                {"type": "TWO", "value": "PRESS", "alt": True},
                {"speed_factor": 2},
                "Speed x2",
            ),
            (
                {"type": "THREE", "value": "PRESS", "alt": True},
                {"speed_factor": 3},
                "Speed x3",
            ),
            (
                {"type": "FOUR", "value": "PRESS", "alt": True},
                {"speed_factor": 4},
                "Speed x4",
            ),
        ],
        "keymap": "Sequencer",
    }
    bl_idname = doc_idname(__qualname__)
    bl_label = doc["name"]
    bl_description = doc_brief(doc["description"])
    bl_options = {"REGISTER", "UNDO"}

    speed_factor: bpy.props.IntProperty(
        name="Speed factor", description="How many times the footage gets sped up", default=2, min=0
    )
    individual_sequences: bpy.props.BoolProperty(
        name="Affect individual strips",
        description="Speed up every VIDEO strip individually",
        default=False,
    )

    @classmethod
    def poll(cls, context):
        return context.selected_sequences

    def execute(self, context):
        sequences = [s for s in context.selected_sequences if s.type in SequenceTypes.VIDEO]

        if not sequences:
            self.report(
                {"ERROR_INVALID_INPUT"},
                "No Movie meta_strip or Metastrips selected. Operation cancelled",
            )
            return {"FINISHED"}

        selection_blocks = []
        if self.individual_sequences:
            selection_blocks = [[s] for s in sequences]
        else:
            selection_blocks = slice_selection(context, sequences)

        for sequences in selection_blocks:
            self.speed_effect_add(context, sequences)

        self.report(
            {"INFO"}, "Successfully processed " + str(len(selection_blocks)) + " selection blocks"
        )
        return {"FINISHED"}

    def speed_effect_add(self, context, sequences):
        if not sequences:
            return

        sequence_editor = context.scene.sequence_editor
        sequencer = bpy.ops.sequencer

        sequencer.select_all(action="DESELECT")
        for s in sequences:
            s.select = True
        sequencer.meta_make()
        meta_strip = sequence_editor.active_strip

        sequencer.effect_strip_add(type="SPEED")
        speed_effect = sequence_editor.active_strip
        speed_effect.use_default_fade = False
        speed_effect.speed_factor = self.speed_factor

        duration = ceil(meta_strip.frame_final_duration / speed_effect.speed_factor)
        meta_strip.frame_final_end = meta_strip.frame_final_start + duration

        sequence_editor.active_strip = meta_strip
        speed_effect.select = True
        meta_strip.select = True
        sequencer.meta_make()
        sequence_editor.active_strip.name = (
            meta_strip.sequences[0].name + " " + str(self.speed_factor) + "x"
        )
