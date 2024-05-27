# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from operator import attrgetter

from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_scene_create_from_selection(bpy.types.Operator):
    """
    *brief* Convert selected strips into a scene strip


    Create a scene from the selected sequences, copying the current scene's settings, and
    replace the selection with the newly created scene as a strip
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

    move_to_first_frame: bpy.props.BoolProperty(
        name="Move to First Frame",
        description="The strips will start at frame 1 on the new scene",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        return context.selected_sequences

    def execute(self, context):
        start_scene_name = context.scene.name

        if len(context.selected_sequences) != 0:
            selection = context.selected_sequences[:]
            selection_start_frame = min(
                selection, key=attrgetter("frame_final_start")
            ).frame_final_start
            selection_start_channel = min(selection, key=attrgetter("channel")).channel

            # Create new scene for the scene strip
            bpy.ops.scene.new(type="FULL_COPY")

            context.window.scene.name = context.selected_sequences[0].name
            new_scene_name = context.window.scene.name

            ###after full copy also unselected strips are in the sequencer... Delete those strips
            bpy.ops.sequencer.select_all(action="INVERT")
            bpy.ops.power_sequencer.delete_direct()
            frame_offset = selection_start_frame - 1
            for s in context.sequences:
                try:
                    s.frame_start -= frame_offset
                except Exception:
                    continue
            bpy.ops.sequencer.select_all()
            bpy.ops.power_sequencer.preview_to_selection()

            # Back to start scene
            bpy.context.window.scene = bpy.data.scenes[start_scene_name]

            bpy.ops.power_sequencer.delete_direct()
            bpy.ops.sequencer.scene_strip_add(
                frame_start=selection_start_frame,
                channel=selection_start_channel,
                scene=new_scene_name,
            )
            scene_strip = context.selected_sequences[0]
        # scene_strip.use_sequence = True
        return {"FINISHED"}
