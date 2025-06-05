# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_scene_rename_with_strip(bpy.types.Operator):
    """
    Rename a Scene Strip and its source scene
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

    new_name: bpy.props.StringProperty(
        name="Strip New Name",
        description="The name both the SceneStrip and its source Scene will take",
        default="",
    )

    @classmethod
    def poll(cls, context):
        return context.selected_sequences

    def invoke(self, context, event):
        window_manager = context.window_manager
        return window_manager.invoke_props_dialog(self)

    def execute(self, context):
        scene_strips = [s for s in context.selected_sequences if s.type == "SCENE"]
        for strip in scene_strips:
            strip.name = self.new_name
            strip.scene.name = strip.name
        return {"FINISHED"}
