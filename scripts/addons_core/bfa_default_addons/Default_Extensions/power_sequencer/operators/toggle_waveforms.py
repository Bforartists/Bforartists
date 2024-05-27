# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from .utils.global_settings import SequenceTypes
from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_toggle_waveforms(bpy.types.Operator):
    """
    *brief* Toggle audio waveforms

    Toggle drawing of waveforms for selected strips or for all audio strips if no selection
    is active.
    """

    doc = {
        "name": doc_name(__qualname__),
        "demo": "https://i.imgur.com/HJ5ryhv.gif",
        "description": doc_description(__doc__),
        "shortcuts": [({"type": "W", "value": "PRESS", "alt": True}, {}, "Toggle Waveforms")],
        "keymap": "Sequencer",
    }
    bl_idname = doc_idname(__qualname__)
    bl_label = doc["name"]
    bl_description = doc_brief(doc["description"])
    bl_options = {"REGISTER", "UNDO"}

    mode: bpy.props.EnumProperty(
        items=[
            ("auto", "Auto", "Automatically toggle the waveform"),
            ("on", "On", "Make the waveforms visible"),
            ("off", "Off", "Make the waveforms invisible"),
        ],
        name="Waveform visibility",
        description="Force the waveforms' visibility with On or Off, \
            or let Blender choose automatically",
        default="auto",
    )

    @classmethod
    def poll(cls, context):
        return context.selected_sequences

    def execute(self, context):
        selection = context.selected_sequences
        if not selection:
            selection = context.sequences

        sequences = [s for s in selection if s.type in SequenceTypes.SOUND]

        if not sequences:
            self.report({"ERROR_INVALID_INPUT"}, "Select at least one sound strip")
            return {"CANCELLED"}

        show_waveform = None
        if self.mode == "auto":
            from operator import attrgetter

            show_waveform = not sorted(sequences, key=attrgetter("frame_final_start"))[
                0
            ].show_waveform
        else:
            show_waveform = True if self.mode == "on" else False

        for s in sequences:
            s.show_waveform = show_waveform
        return {"FINISHED"}
