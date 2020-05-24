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


class POWER_SEQUENCER_OT_scene_cycle(bpy.types.Operator):
    """
    Cycle through scenes
    """

    doc = {
        "name": doc_name(__qualname__),
        "demo": "https://i.imgur.com/7zhq8Tg.gif",
        "description": doc_description(__doc__),
        "shortcuts": [({"type": "TAB", "value": "PRESS", "shift": True}, {}, "Cycle Scenes")],
        "keymap": "Sequencer",
    }
    bl_idname = doc_idname(__qualname__)
    bl_label = doc["name"]
    bl_description = doc_brief(doc["description"])
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return bpy.data.scenes

    def execute(self, context):
        scenes = bpy.data.scenes

        scene_count = len(scenes)

        if context.screen.is_animation_playing:
            bpy.ops.screen.animation_cancel(restore_frame=False)
        for index in range(scene_count):
            if context.scene == scenes[index]:
                context.window.scene = scenes[(index + 1) % scene_count]
                break
        return {"FINISHED"}
