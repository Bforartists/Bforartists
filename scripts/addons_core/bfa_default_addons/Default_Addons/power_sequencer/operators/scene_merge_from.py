# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_merge_from_scene_strip(bpy.types.Operator):
    """
    *brief* Copies all sequences and markers from a SceneStrip's scene into
    the active scene. Optionally delete the source scene and the strip

    WARNING: Currently the operator doesn't recreate any animation data,
    be careful by choosing to delete the scene after the merge
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

    delete_scene: bpy.props.BoolProperty(
        name="Delete Strip's scene",
        description="Delete the SceneStrip's scene after the merging",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        return context.scene.sequence_editor.active_strip

    def invoke(self, context, event):
        window_manager = context.window_manager
        return window_manager.invoke_props_dialog(self)

    def execute(self, context):
        strip = context.scene.sequence_editor.active_strip
        if strip.type != "SCENE":
            return {"FINISHED"}
        strip_scene = strip.scene
        start_scene = context.window.scene

        self.merge_markers(context, strip_scene, start_scene)
        self.merge_strips(context, strip_scene, start_scene)

        if not self.delete_scene:
            return {"FINISHED"}

        bpy.ops.sequencer.select_all(action="DESELECT")
        strip.select = True
        bpy.ops.sequencer.delete()
        context.window.scene = strip_scene
        bpy.ops.scene.delete()
        context.window.scene = start_scene
        self.report(type={"WARNING"}, message="Merged scenes lose all their animation data.")

        return {"FINISHED"}

    def merge_strips(self, context, source_scene, target_scene):
        context.window.scene = source_scene
        current_frame = context.scene.frame_current
        context.scene.frame_current = context.scene.frame_start
        bpy.ops.sequencer.select_all(action="SELECT")
        bpy.ops.sequencer.copy()
        context.scene.frame_current = current_frame

        context.window.scene = target_scene
        current_frame = context.scene.frame_current
        active = context.scene.sequence_editor.active_strip
        context.scene.frame_current = active.frame_start
        bpy.ops.sequencer.select_all(action="DESELECT")
        bpy.ops.sequencer.paste()

        context.scene.frame_current = current_frame

    def merge_markers(self, context, source_scene, target_scene):
        if len(source_scene.timeline_markers) == 0:
            return

        if len(target_scene.timeline_markers) > 0:
            bpy.ops.marker.select_all(action="DESELECT")

        bpy.context.window.scene = source_scene
        bpy.ops.marker.select_all(action="SELECT")
        bpy.ops.marker.make_links_scene(scene=target_scene.name)

        bpy.context.window.scene = target_scene
        active = bpy.context.window.scene.sequence_editor.active_strip

        # Offset to account for source scenes starting on any frame.
        time_offset = active.frame_start - source_scene.frame_start
        bpy.ops.marker.move(frames=time_offset)
        bpy.ops.marker.select_all(action="DESELECT")
