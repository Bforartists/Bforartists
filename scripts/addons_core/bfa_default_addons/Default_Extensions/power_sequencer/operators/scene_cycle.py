# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later


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
