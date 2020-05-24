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

from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_markers_create_from_selected_strips(bpy.types.Operator):
    """
    *brief* Create one marker at the start on each selected strip, based on its name

    Use it to copy markers as timecodes.
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

    @classmethod
    def poll(cls, context):
        return context.selected_sequences

    def execute(self, context):
        cursor_frame_start = context.scene.frame_current

        for m in context.scene.timeline_markers:
            m.select = False

        for s in context.selected_sequences:
            bpy.ops.marker.add()
            new_marker = context.scene.timeline_markers[-1]

            new_marker.select = True
            bpy.ops.marker.rename(name=s.name)
            gap = s.frame_final_start - cursor_frame_start
            bpy.ops.marker.move(frames=gap)
            new_marker.select = False
        return {"FINISHED"}
