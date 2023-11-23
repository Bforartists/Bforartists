# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2023, The SPA Studios. All rights reserved.

import functools
from typing import Optional
import traceback

import bpy

from spa_sequencer.render.tasks import (
    BaseRenderTask,
    BaseTask,
    CopySoundStripsTask,
    FitResolutionToContentTask,
    SequenceRenderTask,
    StripRenderTask,
    TaskStatus,
    ValueOverrides,
)

from spa_sequencer.sync.core import get_sync_settings
from spa_sequencer.utils import register_classes, unregister_classes


class RenderCancelled(RuntimeError):
    """Exception indicating a render task was cancelled by the user"""

    pass


def close_window(window: bpy.types.Window):
    """Helper function to close the window `win`."""
    bpy.ops.wm.window_close({"window": window}, "INVOKE_DEFAULT")


class SEQUENCER_OT_batch_render(bpy.types.Operator):
    bl_idname = "sequencer.batch_render"
    bl_label = "Sequencer Batch Render"
    bl_description = "Batch render several scene strips from a sequencer"
    bl_options = {"BLOCKING"}

    RENDER_WINDOW_WIDTH = 1080

    def __init__(self):
        self.tasks: list[BaseTask] = []
        self.active_task: Optional[BaseTask] = None

        self.output_channel_offset: int = 0
        self.output_sound_strips: list[bpy.types.SoundSequence] = []

        self.cancelled: bool = False

        # The temporary render view window
        self.render_window: Optional[bpy.types.Window] = None
        # An event timer used to trigger automatic updates when rendering
        self.render_event_timer: Optional[bpy.types.Timer] = None

        # Global overrides made for rendering
        self.global_overrides: ValueOverrides = ValueOverrides()
        # Area used for viewport rendering
        self.render_viewport_area: Optional[bpy.types.Area] = None
        # Window containing the area used for viewport rendering
        self.render_viewport_window: Optional[bpy.types.Window] = None
        # Overrides made to the render viewport space
        self.space_overrides: ValueOverrides = ValueOverrides()

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return (
            context.scene.sequence_editor
            and context.window_manager.batch_render.status != "RUNNING"
        )

    def setup_tasks(self, scene: bpy.types.Scene):
        """
        Setup tasks and internals to batch render scene sequences in `scene` based on
        its options.

        :param scene: The Scene to setup for.
        """
        self.scene = scene
        self.render_options = self.scene.batch_render_options
        render_op_invoke = self.options.is_invoke

        # Select scene sequence strips to render
        seqs = [
            seq
            for seq in self.scene.sequence_editor.sequences
            if isinstance(seq, bpy.types.SceneSequence)
            and (seq.select or not self.render_options.selection_only)
        ]

        # Create render tasks
        for seq in sorted(seqs, key=lambda x: x.frame_final_start):
            self.tasks.append(StripRenderTask(strip=seq, is_modal=render_op_invoke))

        # Early return if output scene is not set.
        if not (output_scene := self.render_options.output_scene):
            return

        # List sound strips if they need to be copied over output scene.
        if self.render_options.output_copy_sound_strips:
            sound_strips = [
                seq
                for seq in self.scene.sequence_editor.sequences
                if isinstance(seq, bpy.types.SoundSequence)
                and (seq.select or not self.render_options.selection_only)
            ]
            self.output_sound_strips = sorted(
                sound_strips, key=lambda x: x.frame_final_start
            )
            if self.output_sound_strips:
                self.tasks.append(
                    CopySoundStripsTask(
                        src_scene=self.scene,
                        dst_scene=output_scene,
                        sound_strips=self.output_sound_strips,
                    )
                )

        # Output scene setup.
        if sed := output_scene.sequence_editor:
            # Deselect all strips in output scene's sequencer in order to keep
            # only the new strips as selected.
            bpy.ops.sequencer.select_all({"scene": output_scene}, action="DESELECT")

            # Compute channel offset in output scene based on existing content
            if self.render_options.output_auto_offset_channels and sed.sequences:
                self.output_channel_offset = max([s.channel for s in sed.sequences])
        else:
            # Ensure sequence editor is created in output scene.
            output_scene.sequence_editor_create()

        if self.tasks:
            if self.render_options.output_scene:
                self.tasks.append(FitResolutionToContentTask(scene=output_scene))
            if self.render_options.render_output_scene:
                self.tasks.append(
                    SequenceRenderTask(scene=output_scene, is_modal=render_op_invoke)
                )

    def render_view_update(self):
        """Ensure render view displays the entire image."""
        # Render window only has one Image Editor area.
        area = self.render_window.screen.areas[0]
        # Get window region.
        region = next(region for region in area.regions if region.type == "WINDOW")
        # Ensure the entire rendered image is visible in the render window.
        bpy.ops.image.view_all(
            {
                "window": self.render_window,
                "area": self.render_window.screen.areas[0],
                "region": region,
            }
        )

    def cancel(self, context):
        """Called when the operator is cancelled, e.g when the user closes the
        render window manually."""
        self.cleanup()
        self.render_props.status = "CANCELLED"

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        if not self.setup(context):
            return {"CANCELLED"}

        self.render_props.status = "RUNNING"
        # Start the modal loop.
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def setup(self, context):
        self.setup_tasks(context.scene)
        self.render_props = context.window_manager.batch_render

        if not self.tasks:
            self.report({"WARNING"}, f"Nothing to render in {context.scene.name}")
            self.render_props.status = "CANCELLED"
            return False

        # Disable synchronization while rendering to avoid issues with
        # conflicting frame change callbacks behaviors.
        self.global_overrides.set(get_sync_settings(), "enabled", False)

        if any(
            isinstance(task, (SequenceRenderTask, StripRenderTask))
            for task in self.tasks
        ):
            # Setting up render window can be skipped in non-modal mode.
            if self.options.is_invoke:
                self.setup_render_window(context)

            # Update render tasks.
            for task in (t for t in self.tasks if isinstance(t, StripRenderTask)):
                task.viewport_area = self.render_viewport_area
                task.viewport_window = self.render_viewport_window
                task.output_channel_offset = self.output_channel_offset

        self.render_props.task_count = len(self.tasks)
        return True

    def setup_render_window(self, context: bpy.types.Context):
        """
        Setup render window and any required change in the UI for this operator to run.
        When returning from the function, the temporarty render view window is made
        active in the current`context`.
        """
        self.space_overrides = ValueOverrides()

        # Viewport rendering: find and setup a 3D view
        if self.render_options.renderer == "VIEWPORT":
            # Setup and use first available 3D view for viewport rendering
            self.render_viewport_area = next(
                (a for a in context.screen.areas if a.type == "VIEW_3D"), None
            )

            if not self.render_viewport_area:
                raise RuntimeError("Viewport rendering requires a 3D view")

            self.render_viewport_window = context.window

            space = self.render_viewport_area.spaces.active
            self.space_overrides.set(space, "show_gizmo", False)
            self.space_overrides.set(space.overlay, "show_overlays", False)
            self.space_overrides.set(space.shading, "type", "RENDERED")
            self.space_overrides.set(space.shading, "use_scene_world_render", True)
            self.space_overrides.set(space.shading, "use_scene_lights_render", True)
            self.space_overrides.set(space.region_3d, "view_perspective", "CAMERA")

        # Temporarily change resolution for render view to have a fixed, pre-defined
        # size.
        render = context.scene.render
        resolution_overrides = ValueOverrides()
        r_ratio = render.resolution_y / render.resolution_x
        win_height = int(self.RENDER_WINDOW_WIDTH * r_ratio)
        resolution_overrides.set(render, "resolution_x", self.RENDER_WINDOW_WIDTH)
        resolution_overrides.set(render, "resolution_y", win_height)
        resolution_overrides.set(render, "resolution_percentage", 100)

        # Show the render window ourselves to identify it.
        main_window = context.window
        ctx = context.copy()
        bpy.ops.render.view_show("INVOKE_DEFAULT")

        # If render view is not active at this point, it means that it was already open.
        # This operator needs to run with this view active: try and close the existing
        # render view.
        if context.window == main_window:
            for win in context.window_manager.windows:
                # Filter out windows that are not temporary.
                if "temp" not in win.screen.name:
                    continue
                try:
                    # This operator will only succeed if the window and area
                    # match a render view setup.
                    bpy.ops.render.view_cancel(
                        {"window": win, "area": win.screen.areas[0]}
                    )
                    # Re-open the render view
                    bpy.ops.render.view_show(ctx, "INVOKE_DEFAULT")
                    break
                except RuntimeError:
                    pass
            if context.window == main_window:
                resolution_overrides.revert()
                raise RuntimeError("Failed to create a render window")

        # Restore resolution settings now that the render view is open.
        resolution_overrides.revert()

        self.render_window = context.window

        # Add a periodical timer event to ensure modal operator is evaluated
        # without any user events.
        # The chosen interval of 0.5 seconds is a good trade-off to get feedback without
        # perceiving waiting time in between 2 tasks or at the end of the process.
        self.render_event_timer = context.window_manager.event_timer_add(
            0.5, window=self.render_window
        )

    def close_render_window(self, context: bpy.types.Context):
        """Close the render view and restore any UI changes made for rendering."""
        if not self.render_window:
            return

        # Restore changes mades to the area
        self.space_overrides.revert()

        # Remove event timer
        context.window_manager.event_timer_remove(self.render_event_timer)
        self.render_event_timer = None

        # Delay closing of render window to the next event loop (using a small interval of .1)
        # for report message to be displayed and operator to finish correctly.
        bpy.app.timers.register(
            functools.partial(close_window, self.render_window),
            first_interval=0.1,
        )

    def modal(self, context: bpy.types.Context, event: bpy.types.Event):
        status = "FINISHED"
        message = "Batch render done."
        report_level = "INFO"

        try:
            # Consume task and evalute its status.
            self.consume_task_async(context)
            if self.active_task:
                # Task has been cancelled, cancel batch render.
                if self.active_task.status == TaskStatus.CANCELLED:
                    raise RenderCancelled()
                # Task has finished, clear it.
                if self.active_task.status == TaskStatus.FINISHED:
                    self.clear_active_task()
                # Otherwise, keep running modally.
                return {"RUNNING_MODAL"}
        except RenderCancelled:
            message = "Batch render cancelled by user."
            report_level = "WARNING"
            status = "CANCELLED"
        except Exception:
            message = f"Batch Render failed. \n{traceback.format_exc()}"
            report_level = "ERROR"
            status = "CANCELLED"

        # Batch rendering has finished, cleanup remaining tasks if any.
        self.cleanup()

        # Report operator result based on status
        self.report({report_level}, message)
        # Close render window
        self.close_render_window(context)

        # Update global status.
        self.render_props.status = status

        return {status}

    def consume_task_async(self, context: bpy.types.Context):
        """Asynchronously consume next task in queue."""

        # Start a new task if none is running.
        if not self.active_task:
            self.setup_next_task(context)
            # No task left to do, return.
            if not self.active_task:
                return

        # An active task is setup but has not been started yet.
        if self.active_task.status == TaskStatus.PENDING:
            # NOTE: It might take several tries to actually start a task.
            self.start_active_task(context)

        # Active task is still running.
        elif self.active_task.status == TaskStatus.RUNNING:
            if isinstance(self.active_task, BaseRenderTask):
                # Ensure the entire rendered image is visible in the render window.
                self.render_view_update()

        # Active task has finished, perform post run logic.
        # NOTE: A task without having asynchronous logic would have finished immediatly
        #       after `start_active_task`. Test this status with an if statement
        #       (not an elif).
        if self.active_task.status == TaskStatus.FINISHED:
            self.active_task.post_run(context, self.render_options)

    def consume_task_sync(self, context: bpy.types.Context):
        """Synchronously consume the next task in queue."""
        # Setup and make next task in queue active.
        self.setup_next_task(context)
        # Run the task.
        self.start_active_task(context)
        # Trigger task's post-run process.
        self.active_task.post_run(context, self.render_options)
        # Clear active task.
        self.clear_active_task()

    def execute(self, context: bpy.types.Context):
        # If operator has been invoked, it should have ran modally.
        if self.options.is_invoke:
            return {"FINISHED"}

        if context.scene.batch_render_options.renderer == "VIEWPORT":
            self.report(
                {"ERROR"}, "Blocking render incompatible with viewport rendering."
            )
            return {"CANCELLED"}

        # Otherwise, run synchronously.
        if not self.setup(context):
            return {"CANCELLED"}

        self.render_props.status = "RUNNING"

        while self.tasks:
            try:
                self.consume_task_sync(context)
            except Exception as e:
                self.report(
                    {"ERROR"}, f"Batch Render failed. \n{traceback.format_exc()}"
                )
                self.cancel(context)
                return {"CANCELLED"}

        self.cleanup()
        self.render_props.status = "FINISHED"
        self.report({"INFO"}, "Batch render done!")
        return {"FINISHED"}

    def setup_next_task(self, context):
        """
        Setup the context for the next task in the tasks list.
        After this call:
          - this task won't be in the tasks list anymore.
          - `self.active_task` will be set to this task.
        """
        if self.active_task or not self.tasks:
            return

        self.active_task = self.tasks.pop(0)

        self.active_task.setup(context, self.render_options)

    def start_active_task(self, context):
        """Start the active task."""
        if not self.active_task or self.active_task.status != TaskStatus.PENDING:
            return
        self.active_task.run(context, self.render_options)

    def clear_tasks(self):
        """Remove all the registered tasks."""
        self.clear_active_task()
        self.tasks.clear()
        # Reset global task count.
        self.render_props.task_count = 0

    def clear_active_task(self):
        """Unassign and clear active task by restoring overriden values."""
        if not self.active_task:
            return
        self.active_task.teardown()
        # Unassign active task
        self.active_task = None
        # Decrease global task count.
        self.render_props.task_count -= 1

    def cleanup(self):
        """Clear all tasks, unregister app handlers and reset any override applied
        to the scene."""
        self.clear_tasks()
        # Revert global overrides
        self.global_overrides.revert()


classes = (SEQUENCER_OT_batch_render,)


def register():
    register_classes(classes)


def unregister():
    unregister_classes(classes)
