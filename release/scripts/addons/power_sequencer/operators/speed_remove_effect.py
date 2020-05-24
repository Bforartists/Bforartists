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


class POWER_SEQUENCER_OT_speed_remove_effect(bpy.types.Operator):
    """
    *brief* Removes speed from META, un-groups META


    This is the opposite of power_sequencer's "Add Speed" operator.  It seeks out and removes
    the speed modifier inside a meta and ungroups all the remaining strips within.
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
        return context.scene.sequence_editor.active_strip.type == "META"

    def execute(self, context):
        active = context.scene.sequence_editor.active_strip
        sub_strips = []
        for s in active.sequences:
            if s.type == "SPEED":
                speed_strip = s
            else:
                sub_strips.append(s)

        bpy.ops.sequencer.meta_separate()
        bpy.ops.sequencer.select_all(action="DESELECT")

        speed_strip.select = True
        bpy.ops.sequencer.delete()

        for s in sub_strips:
            s.select = True
        return {"FINISHED"}
