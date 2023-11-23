# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2023, The SPA Studios. All rights reserved.

from typing import Callable

import bpy

from spa_sequencer.utils import register_classes, unregister_classes


MEDIA_TYPES_FORMATS = {
    "IMAGES": ("JPEG", "jpg"),
    "MOVIE": ("QUICKTIME", "mov"),
}


class BatchRenderOptions(bpy.types.PropertyGroup):
    """Options for batch rendering stored at scene level (saved in file)."""

    # Python API for executing callbacks on tasks execution.
    tasks_callbacks: dict[str, Callable] = {}

    media_type: bpy.props.EnumProperty(
        name="Media Type",
        description="The type of media to generate",
        items=(
            ("IMAGES", "Images", ""),
            ("MOVIE", "Movie", ""),
        ),
        default="MOVIE",
        options=set(),
    )

    renderer: bpy.props.EnumProperty(
        name="Renderer",
        description="The renderer to use",
        items=(
            ("INTERNAL", "Internal", "Use Internal rendering"),
            ("VIEWPORT", "Viewport", "Use Viewport rendering"),
        ),
        default="INTERNAL",
        options=set(),
    )

    render_engine: bpy.props.EnumProperty(
        name="Engine",
        description="The render engine to use",
        items=(
            ("BLENDER_EEVEE", "Eevee", "Eevee"),
            ("BLENDER_WORKBENCH", "Workbench", "Workbench"),
        ),
        default="BLENDER_EEVEE",
        options=set(),
    )

    resolution: bpy.props.EnumProperty(
        name="Resolution",
        description="Resolution scale factor",
        items=(
            ("100", "Original", "100%"),
            ("50", "1/2", "50%"),
            ("25", "1/4", "25%"),
            ("12", "1/8", "12%"),
        ),
        default="100",
        options=set(),
    )

    frames_handles: bpy.props.IntProperty(
        name="Frames Handles",
        description=(
            "Extra frames to render before and after each strip's original range"
        ),
        default=0,
        min=0,
        soft_max=200,
        options=set(),
    )

    output_scene: bpy.props.PointerProperty(
        name="Output Scene",
        description="The scene in which media strips from render should be created",
        type=bpy.types.Scene,
    )

    output_auto_offset_channels: bpy.props.BoolProperty(
        name="Auto Offset Channels",
        description=(
            "Offset strips channels in output scene to start on the first one "
            "without content"
        ),
        default=False,
        options=set(),
    )

    output_copy_sound_strips: bpy.props.BoolProperty(
        name="Copy Sound Strips",
        description="Copy sound strips from this sequencer to output scene",
        default=False,
        options=set(),
    )

    filepath_pattern: bpy.props.StringProperty(
        name="Filepath Pattern",
        description=(
            "The filepath pattern to name media files.\n"
            "Uses Python string formatting syntax. Available variables:\n"
            " - filename: the base name of the Blender file without extension\n"
            " - strip: the name of the strip\n"
            " - scene: the name of the strip's scene\n"
        ),
        default="//render/{filename}/{strip}",
        options=set(),
    )

    render_output_scene: bpy.props.BoolProperty(
        name="Render Output Scene",
        description="Whether to render the output scene as a single media",
        default=False,
        options=set(),
    )

    output_render_filepath_pattern: bpy.props.StringProperty(
        name="Filepath Pattern",
        description="The filepath pattern to name the output scene render",
        default="//render/{filename}/{filename}",
        options=set(),
    )

    selection_only: bpy.props.BoolProperty(
        name="Selection Only",
        description="Only render selected scene strips",
        default=False,
        options=set(),
    )

    def register_callback(self, task_name: str, callback: Callable):
        """Register a post run callback for given task (task class name)."""
        # TODO: improve logic to ensure task exists
        self.tasks_callbacks[task_name] = callback

    def clear_callback(self, task_name: str):
        """Un-register callback on given task."""
        if task_name in self.tasks_callbacks:
            del self.tasks_callbacks[task_name]


class BatchRenderRuntimeProps(bpy.types.PropertyGroup):
    """Batch Render runtime properties."""

    status: bpy.props.EnumProperty(
        name="Status",
        description="Status of the batch render",
        items=(
            ("NONE", "None", "Batch render was not started yet"),
            ("RUNNING", "Running", "Batch render is currently running"),
            ("FINISHED", "Finished", "Batch render finished properly"),
            (
                "CANCELLED",
                "Cancelled",
                "Batch render was interrupted (by the user or an error)",
            ),
        ),
        default="NONE",
    )

    task_count: bpy.props.IntProperty(
        name="Task Count",
        description="Total number of render tasks",
        default=0,
    )


classes = (
    BatchRenderOptions,
    BatchRenderRuntimeProps,
)


def register():
    register_classes(classes)

    bpy.types.Scene.batch_render_options = bpy.props.PointerProperty(
        type=BatchRenderOptions
    )

    bpy.types.WindowManager.batch_render = bpy.props.PointerProperty(
        name="Batch Render",
        type=BatchRenderRuntimeProps,
    )


def unregister():
    unregister_classes(classes)
    del bpy.types.Scene.batch_render_options
    del bpy.types.WindowManager.batch_render
