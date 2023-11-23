# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2023, The SPA Studios. All rights reserved.

import re

import bpy


from spa_sequencer.shot.naming import ShotNaming, ShotPrefix
from spa_sequencer.shot.core import slip_shot_content
from spa_sequencer.utils import register_classes, unregister_classes

from spa_sequencer.editorial.core import gather_strips_groups_by_regex
from spa_sequencer.render.tasks import (
    STRIP_PROP_SOURCE_SCENE,
    STRIP_PROP_SOURCE_CAMERA,
    STRIP_PROP_SOURCE_FRAME_START,
    STRIP_PROP_SOURCE_FRAME_END,
)

from spa_sequencer.sync.core import remap_frame_value


def get_shot_prefix_enum(self, ctx):
    return [(item.value, item.value, item.name) for item in ShotPrefix]


class SEQUENCER_OT_edit_conform_shots_from_panels(bpy.types.Operator):
    bl_idname = "sequencer.edit_conform_shots_from_panels"
    bl_label = "Generate Shots From Panels"
    bl_description = "Generate a scene strip track based on a media track with panels"
    bl_options = {"UNDO", "REGISTER"}

    ref_channel: bpy.props.IntProperty(
        name="Reference Channel",
        description="Channel that contains the panels",
        default=1,
    )

    shot_id_regex: bpy.props.StringProperty(
        name="Shot ID Regex",
        description="Single capture group regex to extract shot id from panel names",
        default=r"\w*_s(\d*)_?\w*",
    )

    shot_prefix: bpy.props.EnumProperty(
        name="Shot Prefix",
        description="Shot prefix",
        items=get_shot_prefix_enum,
    )

    def get_scenes(self, context):
        """
        Get all scenes that can be used by scene strips, i.e:
        - are not the current one
        - have a camera
        """
        # Store this on the class to keep a valid Python reference to string props.
        scenes = [
            (s.name, s.name, "")
            for s in bpy.data.scenes
            if s != context.scene and s.camera
        ]
        if not scenes:
            scenes = [("NONE", "No Valid Shot Scene", "No valid shot scene found")]
        SEQUENCER_OT_edit_conform_shots_from_panels._scenes = scenes
        return SEQUENCER_OT_edit_conform_shots_from_panels._scenes

    shot_scene: bpy.props.EnumProperty(
        name="Shot Scene",
        description="The scene the generated shot scene strips should use",
        items=get_scenes,
    )

    target_channel: bpy.props.IntProperty(
        name="Target Channel",
        description="Channel to create the shot scene strips on",
        default=2,
    )

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.scene.sequence_editor is not None

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context: bpy.types.Context):
        if self.shot_scene == "NONE":
            self.report({"ERROR"}, "No valid shot Scene")
            return {"CANCELLED"}

        seq_editor = context.scene.sequence_editor

        # Get list of strips from reference channel.
        ref_strips = sorted(
            [s for s in seq_editor.sequences if s.channel == self.ref_channel],
            key=lambda x: x.frame_final_start,
        )

        # Build strip groups based on shot regex.
        strips_groups = gather_strips_groups_by_regex(ref_strips, self.shot_id_regex)

        shot_naming = ShotNaming()

        # Build shot scene strips based on reference strip groups.
        shot_scene = bpy.data.scenes[self.shot_scene]
        for number, group in enumerate(strips_groups):
            shot_name = shot_naming.build_shot_name((number + 1) * 10, self.shot_prefix)

            # Create a new scene strip at frame start of the first ref strip in this group.
            shot_strip = seq_editor.sequences.new_scene(
                shot_name,
                shot_scene,
                self.target_channel,
                group.frame_start,
            )
            # Match the duration of the whole group.
            shot_strip.frame_final_duration = group.frame_duration
            # Adjust internal offset to target the correct range within the strip's scene.
            slip_shot_content(shot_strip, shot_strip.frame_final_start)
            # Assign active camera of the scene.
            shot_strip.scene_camera = shot_scene.camera

        # Trigger a sequencer update.
        bpy.ops.sequencer.reload()

        self.report(
            {"INFO"},
            f"Created {len(strips_groups)} shots from {len(ref_strips)} panels",
        )
        return {"FINISHED"}


class SEQUENCER_OT_edit_conform_shots_from_editorial(bpy.types.Operator):
    bl_idname = "sequencer.edit_conform_shots_from_editorial"
    bl_label = "Conform Shots From Editorial"
    bl_description = (
        "Generate a scene strip track based on a media track with movie strips"
    )
    bl_options = {"UNDO"}

    ref_channel: bpy.props.IntProperty(
        name="Reference Channel",
        description="Channel that contains the movie strips (0 for all)",
        default=0,
    )

    target_channel: bpy.props.IntProperty(
        name="Target Channel",
        description="Channel to create the edit on",
        default=2,
    )

    shot_prefix: bpy.props.EnumProperty(
        name="Shot Prefix",
        description="Shot prefix",
        items=get_shot_prefix_enum,
    )

    shot_id_regex: bpy.props.StringProperty(
        name="Shot ID Regex",
        description="Single capture group regex to extract shot id from panel names",
        default=r"\w*_PSH(\d*)\.\w*",
    )

    freeze_frame_handles: bpy.props.IntVectorProperty(
        name="Freeze Frame Handles",
        description="Freeze frame handles (left/right)",
        size=2,
        min=0,
        soft_max=240,
        default=[100, 100],
    )

    freeze_frame_handles_applied: bpy.props.BoolProperty(
        name="Freeze Frames Handles Applied",
        description=(
            "Whether freeze frame handlers are applied to metadata values"
            " or need to be taken into account"
        ),
        default=True,
    )

    freeze_frame_handles_warning: bpy.props.BoolProperty(
        name="Freeze Frame Handles Warning",
        description="Color strips that exceed original source range (using freeze frame handles)",
        default=True,
    )

    def draw(self, context: bpy.types.Context):
        self.layout.use_property_split = True
        self.layout.prop(self, "ref_channel")
        self.layout.prop(self, "target_channel")
        self.layout.prop(self, "shot_prefix")
        self.layout.prop(self, "shot_id_regex")
        box = self.layout.box()
        box.prop(self, "freeze_frame_handles", expand=True)
        box.prop(self, "freeze_frame_handles_applied", text="Applied to Metadata")
        box.prop(self, "freeze_frame_handles_warning", text="Warn Usage")

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context: bpy.types.Context):

        seq_editor = context.scene.sequence_editor
        regex = re.compile(self.shot_id_regex)

        shot_naming = ShotNaming()

        for strip in seq_editor.sequences:

            if self.ref_channel != 0 and strip.channel != self.ref_channel:
                continue

            # We expect to find specific keys on movie strips to reconstruct scene strips
            scene = bpy.data.scenes.get(strip.get(STRIP_PROP_SOURCE_SCENE, ""))

            if not scene:
                continue

            # Extract additional metadata from strip
            camera = bpy.data.objects.get(strip.get(STRIP_PROP_SOURCE_CAMERA, ""))
            frame_start = int(strip.get(STRIP_PROP_SOURCE_FRAME_START, 0))
            frame_end = int(
                strip.get(
                    STRIP_PROP_SOURCE_FRAME_END,
                    (frame_start + strip.frame_duration - 1),
                )
            )

            # Compute source frame start without freeze frame handles
            source_frame_start = frame_start
            source_frame_end = frame_end

            if not self.freeze_frame_handles_applied:
                # Extend strip's internal range by handles.
                frame_start -= self.freeze_frame_handles[0]
                frame_end += self.freeze_frame_handles[1]
            else:
                # Compute original strip range by removing handles.
                source_frame_start += self.freeze_frame_handles[0]
                source_frame_end -= self.freeze_frame_handles[1]

            # Try to extract shot name from strip name.
            res = regex.search(strip.name)
            if res:
                shot_number = int(res.group(1))
                shot_name = shot_naming.build_shot_name(shot_number)
            else:
                shot_name = shot_naming.next_shot_name_from_sequences(seq_editor)

            # Create a new scene strip using extracted information.
            shot_strip = seq_editor.sequences.new_scene(
                shot_name, scene, self.target_channel, strip.frame_final_start
            )
            shot_strip.scene_camera = camera
            # Adjust timing.
            shot_strip.frame_final_duration = strip.frame_final_duration
            shot_strip.frame_final_start = strip.frame_final_start
            start_offset = frame_start + strip.frame_offset_start - 1
            slip_shot_content(shot_strip, start_offset)

            # Detect if shot is exceeding initial rendering range.
            if self.freeze_frame_handles_warning:
                frame_start = remap_frame_value(
                    shot_strip.frame_final_start, shot_strip
                )
                frame_end = remap_frame_value(shot_strip.frame_final_end, shot_strip)
                if frame_start < source_frame_start or frame_end > source_frame_end:
                    shot_strip.color_tag = "COLOR_02"

        return {"FINISHED"}


classes = (
    SEQUENCER_OT_edit_conform_shots_from_panels,
    SEQUENCER_OT_edit_conform_shots_from_editorial,
)


def register():
    register_classes(classes)


def unregister():
    unregister_classes(classes)
