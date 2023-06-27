# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from .utils.functions import find_sequences_after
from .utils.functions import convert_duration_to_frames
from .utils.global_settings import SequenceTypes
from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_crossfade_add(bpy.types.Operator):
    """
    *brief* Adds cross fade between selected sequence and the closest sequence to its right

    Based on the active strip, finds the closest next sequence of a similar type, moves it
    so it overlaps the active strip, and adds a gamma cross effect between them. Works with
    MOVIE, IMAGE and META strips
    """

    doc = {
        "name": doc_name(__qualname__),
        "demo": "https://i.imgur.com/ZyEd0jD.gif",
        "description": doc_description(__doc__),
        "shortcuts": [
            ({"type": "C", "value": "PRESS", "ctrl": True, "alt": True}, {}, "Add Crossfade")
        ],
        "keymap": "Sequencer",
    }
    bl_idname = doc_idname(__qualname__)
    bl_label = doc["name"]
    bl_description = doc_brief(doc["description"])
    bl_options = {"REGISTER", "UNDO"}

    crossfade_duration: bpy.props.FloatProperty(
        name="Crossfade Duration", description="The duration of the crossfade", default=0.5, min=0
    )
    auto_move_strip: bpy.props.BoolProperty(
        name="Auto Move Strip",
        description=(
            "When true, moves the second strip so the crossfade"
            " is of the length set in 'Crossfade Length'"
        ),
        default=True,
    )

    @classmethod
    def poll(cls, context):
        return context.selected_sequences

    def execute(self, context):
        sorted_selection = sorted(context.selected_sequences, key=lambda s: s.frame_final_start)
        for s in sorted_selection:
            s_next = self.get_next_sequence_after(context, s)
            s_to_offset = s_next.input_1 if hasattr(s_next, "input_1") else s_next

            if self.auto_move_strip:
                offset = s_to_offset.frame_final_start - s.frame_final_end
                s_to_offset.frame_start -= offset

            if s_to_offset.frame_final_start == s.frame_final_end:
                self.offset_sequence_handles(context, s, s_to_offset)

            self.apply_crossfade(context, s, s_next)
        return {"FINISHED"}

    def get_next_sequence_after(self, context, sequence):
        """
        Returns the first sequence after `sequence` by frame_final_start
        """
        next_sequence = None
        next_in_channel = [
            s for s in find_sequences_after(context, sequence) if s.channel == sequence.channel
        ]
        next_transitionable = (s for s in next_in_channel if s.type in SequenceTypes.TRANSITIONABLE)
        try:
            next_sequence = min(next_transitionable, key=lambda s: s.frame_final_start)
        except ValueError:
            pass
        return next_sequence

    def apply_crossfade(self, context, strip_from, strip_to):
        for s in bpy.context.selected_sequences:
            s.select = False
        strip_from.select = True
        strip_to.select = True
        context.scene.sequence_editor.active_strip = strip_to
        bpy.ops.sequencer.effect_strip_add(type="GAMMA_CROSS")

    def offset_sequence_handles(self, context, sequence_1, sequence_2):
        """
        Moves the handles of the two sequences before adding the crossfade
        """
        fade_duration = convert_duration_to_frames(context, self.crossfade_duration)
        fade_offset = int(fade_duration / 2)

        if hasattr(sequence_1, "input_1"):
            sequence_1.input_1.frame_final_end -= fade_offset
        else:
            sequence_1.frame_final_end -= fade_offset

        if hasattr(sequence_2, "input_1"):
            sequence_2.input_1.frame_final_start += fade_offset
        else:
            sequence_2.frame_final_start += fade_offset
