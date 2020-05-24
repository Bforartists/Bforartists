#
# Copyright (C) 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# This file is part of Power Sequencer.
#
# Power Sequencer is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Power Sequencer is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with Power Sequencer. If
# not, see <https://www.gnu.org/licenses/>.
#
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
