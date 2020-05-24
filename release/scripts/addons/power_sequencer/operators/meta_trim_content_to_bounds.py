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


class POWER_SEQUENCER_OT_meta_trim_content_to_bounds(bpy.types.Operator):
    """
    Deletes and trims the strips inside selected meta-strips to the meta strip's bounds
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
        return context.selected_sequences

    def execute(self, context):
        to_delete = []
        meta_strips = [s for s in context.selected_sequences if s.type == "META"]
        for m in meta_strips:
            start, end = m.frame_final_start, m.frame_final_end
            sequences_to_process = (s for s in m.sequences if s.type not in SequenceTypes.EFFECT)
            for s in sequences_to_process:
                if s.frame_final_end < start or s.frame_final_start > m.frame_final_end:
                    to_delete.append(s)
                    continue
                # trim strips on the meta's edges or longer than the meta's extents
                if s.frame_final_start < start:
                    s.frame_final_start = start
                if s.frame_final_end > end:
                    s.frame_final_end = end
        bpy.ops.sequencer.select_all(action="DESELECT")
        for s in to_delete:
            s.select = True
        bpy.ops.sequencer.delete()
        return {"FINISHED"}
