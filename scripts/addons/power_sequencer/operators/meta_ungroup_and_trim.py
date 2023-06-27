# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_meta_ungroup_and_trim(bpy.types.Operator):
    """
    UnMeta all selected meta strips and trim their content
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

    trim_content: bpy.props.BoolProperty(
        name="Trim Content",
        description="Trim the content of the Meta Strips to their extents",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        return context.selected_sequences

    def execute(self, context):
        meta_strips = [s for s in context.selected_sequences if s.type == "META"]
        if self.trim_content:
            bpy.ops.power_sequencer.meta_trim_content_to_bounds()
        self.separate(context, meta_strips)
        return {"FINISHED"}

    def separate(self, context, meta_strips):
        bpy.ops.sequencer.select_all(action="DESELECT")
        for m in meta_strips:
            context.scene.sequence_editor.active_strip = m
            bpy.ops.sequencer.meta_separate()
