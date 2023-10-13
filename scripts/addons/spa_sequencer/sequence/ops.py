# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2023, The SPA Studios. All rights reserved.

import bpy

from spa_sequencer.utils import register_classes, unregister_classes
from spa_sequencer.sync.core import (
    get_sync_master_strip,
    get_sync_settings,
    remap_frame_value,
    sync_system_update,
)


class DOPESHEET_OT_sequence_navigate(bpy.types.Operator):
    bl_idname = "dopesheet.sequence_navigate"
    bl_label = "Navigate Sequence"
    bl_description = "Navigate master sequence"
    bl_options = {"UNDO", "BLOCKING", "INTERNAL"}

    frame: bpy.props.IntProperty(
        name="Frame",
        description="Frame value",
        default=-1,
        options={"SKIP_SAVE"},
    )

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return get_sync_settings().master_scene is not None

    def modal(self, context: bpy.types.Context, event: bpy.types.Event):
        frame_value = int(
            context.region.view2d.region_to_view(event.mouse_region_x, 0)[0]
        )
        if frame_value != self.frame:
            self.frame = frame_value
            self.execute(context)

        # Validate
        if event.type in {"LEFTMOUSE"} and event.value in {"RELEASE"}:
            return {"FINISHED"}

        return {"RUNNING_MODAL"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context: bpy.types.Context):
        master_scene = get_sync_settings().master_scene
        master_strip, _ = get_sync_master_strip()

        # Find a strip that matches the timing
        strips = [
            s
            for s in master_scene.sequence_editor.sequences
            if isinstance(s, bpy.types.SceneSequence) and s.scene == bpy.context.scene
        ]

        candidates = [
            s
            for s in strips
            if (
                remap_frame_value(s.frame_final_start, s)
                <= self.frame
                <= remap_frame_value(s.frame_final_end, s)
            )
        ]

        strip = next(
            (s for s in candidates if s == master_strip), next(iter(candidates), None)
        )

        # Update master scene current frame to enter target strip.
        if strip and strip != master_strip:
            master_scene.frame_set(strip.frame_final_start)

        # Set frame_current directly for context's active scene.
        # This proves to be enough and reacts better than frame_set which
        # might discard the change when playback is running.
        context.scene.frame_current = self.frame

        return {"FINISHED"}


class SEQUENCE_OT_active_shot_camera_set(bpy.types.Operator):
    bl_idname = "sequence.active_shot_camera_set"
    bl_label = "Set Active Shot Camera"
    bl_description = "Set active shot camera"
    bl_options = {"UNDO"}

    camera: bpy.props.StringProperty(
        name="Camera",
        description="Scene to set on active shot",
        options={"SKIP_SAVE"},
    )

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return get_sync_master_strip(use_cache=True)[0] is not None

    def execute(self, context: bpy.types.Context):
        strip = get_sync_master_strip(use_cache=True)[0]
        cam = bpy.data.objects.get(self.camera, None)
        # Update strip's camera.
        strip.scene_camera = cam
        # Set this camera active in underlying scene.
        strip.scene.camera = cam
        return {"FINISHED"}


class SEQUENCE_OT_active_shot_scene_set(bpy.types.Operator):
    bl_idname = "sequence.active_shot_scene_set"
    bl_label = "Set Active Shot Scene"
    bl_description = "Set active shot scene"
    bl_options = {"UNDO"}

    scene: bpy.props.StringProperty(
        name="Scene",
        description="Scene to set on active shot",
        options={"SKIP_SAVE"},
    )

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return get_sync_master_strip(use_cache=True)[0] is not None

    def execute(self, context: bpy.types.Context):
        strip = get_sync_master_strip(use_cache=True)[0]
        scene = bpy.data.scenes.get(self.scene, None)

        strip.scene = scene

        # Update strip's camera to use target scene's active camera.
        if not strip.scene_camera or (
            strip.scene_camera.name not in scene.collection.all_objects
        ):
            strip.scene_camera = scene.camera

        # Force sync system to update to account for this change.
        sync_system_update(context, force=True)
        return {"FINISHED"}


class SEQUENCE_OT_check_obj_users_scene(bpy.types.Operator):
    bl_idname = "sequence.check_obj_users_scene"
    bl_label = "Report Object use by Sequencer"
    bl_description = (
        "From the active object, report all sequencer strips using "
        "this object in their strip scenes"
    )

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.active_object and get_sync_master_strip(use_cache=True)[0]

    def build_obj_user_scene_report(self, obj):
        info_msg = ""
        master_scene = get_sync_settings().master_scene
        strips = [
            strip
            for strip in master_scene.sequence_editor.sequences_all
            if strip.type == "SCENE"
        ]

        for strip in sorted(strips, key=lambda f: f.frame_final_start):
            scene_msg = f" - Scene '{strip.scene.name}' from strips:\n"
            if scene_msg not in info_msg:
                info_msg += scene_msg
            info_msg += (
                f"   - {strip.name} "
                f"[{strip.frame_final_start}, {strip.frame_final_end}]\n"
            )

        report = f"Object '{obj.name}' is used in '{master_scene.name}' by:\n{info_msg}"
        return report

    def invoke(self, context, event):
        self.setup_name = context.scene.name
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        report = self.build_obj_user_scene_report(context.active_object)
        report_lines = report.split("\n")
        col = self.layout.column()
        for line in report_lines:
            col = self.layout.column()
            col.label(text=line)

    def execute(self, context: bpy.types.Context):
        report = self.build_obj_user_scene_report(context.active_object)
        self.report({"INFO"}, report)
        return {"FINISHED"}


class SEQUENCE_OT_child_scene_setup_create(bpy.types.Operator):
    bl_idname = "sequence.child_scene_setup_create"
    bl_label = "Create Child Scene Setup"
    bl_description = "From the current scene, make a new scene and add a new collection"
    bl_property = "setup_name"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return get_sync_master_strip(use_cache=True)[0]

    setup_name: bpy.props.StringProperty(name="Name")

    def invoke(self, context, event):
        self.setup_name = context.scene.name
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "setup_name")

    def execute(self, context: bpy.types.Context):
        # Cancel if user provides a scene name that is already used
        if self.setup_name in bpy.data.scenes:
            self.report({"ERROR"}, "Name already in use")
            return {"CANCELLED"}
        # Get current strip it's scene as a reference
        strip = get_sync_master_strip(use_cache=True)[0]
        ref_scene = strip.scene
        # Create new Scene and set name
        with context.temp_override(scene=ref_scene):
            bpy.ops.scene.new(type="LINK_COPY")
        new_scene = context.scene
        new_scene.name = self.setup_name
        # create pointer back to old scene
        new_scene.parent_scene = ref_scene

        # Create new collection with the same name
        new_setup_collection = bpy.data.collections.new(name=self.setup_name)
        new_scene.collection.children.link(new_setup_collection)

        # Assign new scene to current strip
        strip.scene = new_scene

        # Report to user new scene creation and assignment
        self.report(
            {"INFO"},
            f"New scene setup '{self.setup_name}' created on strip '{strip.name}'",
        )
        return {"FINISHED"}


classes = (
    SEQUENCE_OT_check_obj_users_scene,
    DOPESHEET_OT_sequence_navigate,
    SEQUENCE_OT_active_shot_camera_set,
    SEQUENCE_OT_active_shot_scene_set,
    SEQUENCE_OT_child_scene_setup_create,
)


def register():
    register_classes(classes)


def unregister():
    unregister_classes(classes)
