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


class POWER_SEQUENCER_OT_set_timeline_range(bpy.types.Operator):
    """
    Set the timeline start and end frame using the time cursor
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

    adjust: bpy.props.EnumProperty(
        items=[("start", "start", "start"), ("end", "end", "end")],
        name="Adjust",
        description="Change the start or the end frame of the timeline",
        default="start",
    )

    @classmethod
    def poll(cls, context):
        return context.scene.sequence_editor

    def execute(self, context):
        scene = context.scene
        if self.adjust == "start":
            scene.frame_start = scene.frame_current
        elif self.adjust == "end":
            scene.frame_end = scene.frame_current - 1
        return {"FINISHED"}
