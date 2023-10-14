# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2023, The SPA Studios. All rights reserved.

from dataclasses import dataclass, field
from enum import Enum, auto
import math
import os
from typing import Any, Callable, Optional
import bpy
from spa_sequencer.render.props import MEDIA_TYPES_FORMATS, BatchRenderOptions

from spa_sequencer.sync.core import remap_frame_value


STRIP_PROP_SOURCE_BLENDER_FILE = "source_blender_file"
STRIP_PROP_SOURCE_SEQUENCER = "source_sequencer"
STRIP_PROP_SOURCE_STRIP = "source_strip"
STRIP_PROP_SOURCE_SCENE = "source_scene"
STRIP_PROP_SOURCE_CAMERA = "source_camera"
STRIP_PROP_SOURCE_FRAME_START = "source_frame_start"
STRIP_PROP_SOURCE_FRAME_END = "source_frame_end"


class ValueOverrides:
    """Helper class to store attribute value changes and revert them easily."""

    def __init__(self):
        self._overrides: dict[object, list[tuple["str", Any]]] = {}

    def set(self, obj: object, attr, value):
        """Override attribute `attr` on `obj` with `value`."""
        current_value = getattr(obj, attr)
        if current_value == value:
            return
        # Store this change as an override
        if obj not in self._overrides:
            self._overrides[obj] = []
        self._overrides[obj].append((attr, current_value))
        setattr(obj, attr, value)

    def revert(self):
        """Revert all registered overrides."""
        for obj, attrs in self._overrides.items():
            for key, value in attrs:
                setattr(obj, key, value)
        self._overrides.clear()


class TaskStatus(Enum):
    PENDING = auto()
    RUNNING = auto()
    FINISHED = auto()
    CANCELLED = auto()


@dataclass
class BaseTask:
    """Base class for a task."""

    # Task status.
    status: TaskStatus = TaskStatus.PENDING

    # Value overrides associated to this task.
    overrides: ValueOverrides = field(default_factory=ValueOverrides)

    def setup(self, context: bpy.types.Context, render_options: BatchRenderOptions):
        """Setup the task."""
        pass

    def run(self, context: bpy.types.Context, render_options: BatchRenderOptions):
        """Start the task and update its status."""
        pass

    def post_run(self, context: bpy.types.Context, render_options: BatchRenderOptions):
        """Called after run completed successfully."""
        pass

    def teardown(self):
        """Called when task has been consumed, whether it failed or succeeded."""
        self.overrides.revert()


@dataclass
class BaseRenderTask(BaseTask):

    is_modal: bool = True
    handlers_registered: bool = False

    def setup(self, context, options):
        self.register_render_handlers()

    def teardown(self):
        super().teardown()
        self.unregister_app_handlers()

    def on_render_completed(self, *args):
        """Callback for `render_complete` handler."""
        self.status = TaskStatus.FINISHED

    def on_render_cancelled(self, *args):
        """Callback for `render_cancel` handler."""
        self.status = TaskStatus.CANCELLED

    def register_render_handlers(self):
        """Register render handlers callbacks."""
        bpy.app.handlers.render_cancel.append(self.on_render_cancelled)
        bpy.app.handlers.render_complete.append(self.on_render_completed)
        self.handlers_registered = True

    def unregister_app_handlers(self):
        """Unregister render handlers callbacks."""
        if not self.handlers_registered:
            return

        bpy.app.handlers.render_cancel.remove(self.on_render_cancelled)
        bpy.app.handlers.render_complete.remove(self.on_render_completed)
        self.handlers_registered = False

    @staticmethod
    def conform_render_path(filepath: str) -> str:
        # If blender file is not saved, move relative path to temp folder.
        if not bpy.context.blend_data.filepath and filepath.startswith("//"):
            return os.path.join(bpy.app.tempdir, bpy.path.abspath(filepath))
        return filepath

    @property
    def render_op_exec_context(self) -> str:
        """Get operator execution context based on app mode (background/interactive)."""
        return "INVOKE_DEFAULT" if self.is_modal else "EXEC_DEFAULT"


"""
StripRenderTask callback:
 - arguments:
    - source scene strip
    - rendered media filepath
 - returns:
    - path to the new media filepath
"""
StripRenderTaskCallback = Callable[[bpy.types.SceneSequence, str], str]


@dataclass
class StripRenderTask(BaseRenderTask):
    """Strip render task."""

    # The strip to render.
    strip: Optional[bpy.types.SceneSequence] = None
    # Viewport area.
    viewport_area: Optional[bpy.types.Area] = None
    # Window containing the viewport area.
    viewport_window: Optional[bpy.types.Window] = None
    # Output channel offset in output scene.
    output_channel_offset: int = 0

    @property
    def scene(self) -> bpy.types.Scene:
        """Get the internal strip's scene."""
        return self.strip.scene

    def setup(self, context: bpy.types.Context, render_options: BatchRenderOptions):
        super().setup(context, render_options)

        strip = self.strip
        scene = self.scene

        # Override scene's internal range to match strip's range.
        frame_start = remap_frame_value(strip.frame_final_start, strip)
        frame_end = frame_start + strip.frame_final_duration - 1
        # Apply frame handles to range.
        if render_options.media_type == "MOVIE":
            frame_start -= render_options.frames_handles
            frame_end += render_options.frames_handles

        # Set render engine.
        self.overrides.set(scene.render, "engine", render_options.render_engine)

        # Update both range (internal render) and preview range (viewport render)
        self.overrides.set(scene, "frame_start", frame_start)
        self.overrides.set(scene, "frame_end", frame_end)
        self.overrides.set(scene, "frame_preview_start", frame_start)
        self.overrides.set(scene, "frame_preview_end", frame_end)

        # Setup resolution values based on resolution scale setting.
        # NOTE: Blender cannot render movies with odd width/height.
        #       Therefore, instead of using this as the resolution percentage directly,
        #       we compute resolution width and height to round up to the next even
        #       numbers.

        def round_up_to_even(value: float) -> int:
            """Round `value` to next even number."""
            return int(math.ceil(value / 2.0) * 2)

        resolution_scale = int(render_options.resolution) / 100.0
        r_width = round_up_to_even(scene.render.resolution_x * resolution_scale)
        r_height = round_up_to_even(scene.render.resolution_y * resolution_scale)

        self.overrides.set(scene.render, "resolution_x", r_width)
        self.overrides.set(scene.render, "resolution_y", r_height)
        self.overrides.set(scene.render, "resolution_percentage", 100)
        self.overrides.set(scene.render, "use_sequencer", False)

        if strip.scene_camera:
            self.overrides.set(scene, "camera", strip.scene_camera)

        # Resolve output media filepath based on configured pattern
        variables = {
            "strip": strip.name,
            "scene": scene.name,
            "filename": bpy.path.display_name_from_filepath(bpy.data.filepath),
        }
        filepath = render_options.filepath_pattern.format(**variables)
        filepath = self.conform_render_path(filepath)

        # Override render settings based on media type
        file_format, file_ext = MEDIA_TYPES_FORMATS[render_options.media_type]
        render = scene.render
        if render_options.media_type == "IMAGES":
            # Filepath: add separator between resolved name and auto frame number suffix
            filepath += "."
            # Setup render settings
            self.overrides.set(render.image_settings, "file_format", file_format)
            self.overrides.set(render.image_settings, "quality", 100)
            self.overrides.set(render.image_settings, "color_mode", "RGB")
        else:
            # Filepath: add extension to avoid auto frame range suffix
            filepath += f".{file_ext}"
            # Setup render settings
            self.overrides.set(render.image_settings, "file_format", "FFMPEG")
            self.overrides.set(render.ffmpeg, "format", file_format)
            self.overrides.set(render.ffmpeg, "constant_rate_factor", "PERC_LOSSLESS")
        # Setup final filepath
        self.overrides.set(scene.render, "filepath", filepath)

    def run(self, context: bpy.types.Context, render_options: BatchRenderOptions):
        overrides = {"scene": self.scene}
        if self.viewport_area:
            overrides["area"] = self.viewport_area
            overrides["window"] = self.viewport_window
            # We need to make the screen active in the window, overriding it
            # does not work.
            screen = self.viewport_area.id_data
            self.viewport_window.screen = screen
            # Make task's scene active in the window holding the viewport for rendering
            # to happen correctly - context overriding is not enough in this case.
            self.viewport_window.scene = self.scene

        # Determine render operator based on render  options.
        if render_options.renderer == "VIEWPORT":
            render_op = bpy.ops.render.opengl
        else:
            render_op = bpy.ops.render.render

        # Start rendering the target scene. Use a context override for this to
        # work both in interactive and background mode.
        with context.temp_override(**overrides):
            res = render_op(self.render_op_exec_context, animation=True)

        # Calling a render operator right after the previous task finishes may fail due
        # to the ordering of events and how they are dealt with in Blender core.
        # Therefore, we only consider the task as started if operator call returned the
        # proper status (RUNNING_MODAL).
        # See `modal` function to see how this function is used.

        if res == {"RUNNING_MODAL"}:
            self.status = TaskStatus.RUNNING

    def post_run(self, context: bpy.types.Context, render_options: BatchRenderOptions):
        if callback := render_options.tasks_callbacks.get(self.__class__.__name__, []):
            # TODO: check callback compatibility
            new_filepath = callback(self.strip, self.scene.render.filepath)
            self.overrides.set(self.strip.scene.render, "filepath", new_filepath)

        if render_options.output_scene:
            self.create_output_media_strip(
                self.strip,
                render_options.output_scene,
                render_options.media_type,
                render_options.frames_handles,
                self.output_channel_offset,
                render_options,
            )

    def create_output_media_strip(
        self,
        scene_strip: bpy.types.SceneSequence,
        scene: bpy.types.Scene,
        media_type: str,
        frames_handles: int,
        channel_offset: int,
        render_options: BatchRenderOptions,
    ):
        """Create media strip(s) in output scene for the given scene strip.

        :param scene_strip: The source scene sequence strip.
        """
        sed = scene.sequence_editor

        # List created strips and corresponding source frame start/end in scene
        strips: list[tuple[bpy.types.SceneSequence, int, int]] = []

        if media_type == "IMAGES":
            for idx in range(scene_strip.frame_final_duration):
                frame_number = scene_strip.scene.frame_start + idx
                img_path = scene_strip.scene.render.frame_path(frame=frame_number)
                strip = sed.sequences.new_image(
                    name=os.path.basename(bpy.path.abspath(img_path)),
                    filepath=img_path,
                    channel=scene_strip.channel + channel_offset,
                    frame_start=scene_strip.frame_final_start + idx,
                )
                strips.append((strip, frame_number, frame_number))

        elif media_type == "MOVIE":
            filepath = scene_strip.scene.render.filepath
            strip = sed.sequences.new_movie(
                name=os.path.basename(bpy.path.abspath(filepath)),
                filepath=filepath,
                channel=scene_strip.channel + channel_offset,
                frame_start=scene_strip.frame_final_start,
            )

            start_handle = frames_handles
            if frames_handles > 0 and render_options.renderer == "INTERNAL":
                # Internal render does not support negative frame rendering.
                # We therefore need to compute the real start handle duration.
                # This is done by getting the difference between:
                #  the rendered clip duration
                #  and the scene strip's duration + end frame handle's duration.
                start_handle = strip.frame_duration - (
                    scene_strip.frame_final_duration + frames_handles
                )

            strip.frame_offset_start = start_handle
            strip.frame_offset_end = frames_handles
            strip.frame_start -= start_handle
            strips.append(
                (strip, scene_strip.scene.frame_start, scene_strip.scene.frame_end)
            )

        for strip, frame_start, frame_end in strips:
            # Re-assign the strip channel to force Blender to evalute overlaps
            strip.channel = strip.channel
            # Store render source metadata as custom properties on the strip.
            original_edit_scene_name = self.strip.id_data.name
            strip[STRIP_PROP_SOURCE_BLENDER_FILE] = bpy.data.filepath
            strip[STRIP_PROP_SOURCE_SEQUENCER] = original_edit_scene_name
            strip[STRIP_PROP_SOURCE_STRIP] = scene_strip.name
            strip[STRIP_PROP_SOURCE_SCENE] = scene_strip.scene.name
            strip[STRIP_PROP_SOURCE_CAMERA] = scene_strip.scene.camera.name
            strip[STRIP_PROP_SOURCE_FRAME_START] = frame_start
            strip[STRIP_PROP_SOURCE_FRAME_END] = frame_end


@dataclass
class CopySoundStripsTask(BaseTask):
    src_scene: Optional[bpy.types.Scene] = None
    dst_scene: Optional[bpy.types.Scene] = None
    sound_strips: list[bpy.types.SoundSequence] = field(default_factory=list)

    def run(self, context: bpy.types.Context, render_options: BatchRenderOptions):
        self.status = TaskStatus.FINISHED

    def post_run(self, context, render_options):
        if not self.src_scene or not self.dst_scene or not self.sound_strips:
            return

        sed_src = self.src_scene.sequence_editor
        sed_dst = self.dst_scene.sequence_editor

        # Store original selection from source and dest scenes.
        original_selection = [
            seq for seq in sed_src.sequences[:] + sed_dst.sequences[:] if seq.select
        ]

        # Select only sound strips in source scene.
        with context.temp_override(scene=self.src_scene):
            bpy.ops.sequencer.select_all(action="DESELECT")

        for seq in self.sound_strips:
            seq.select = True

        # Copy strips from source.
        # Build context with scene and selected sequences (must match actual selection).
        with context.temp_override(
            scene=self.src_scene, selected_sequences=self.sound_strips
        ):
            bpy.ops.sequencer.copy()

        paste_op_ctx_override = {"scene": self.dst_scene}
        # Paste strips to dest.
        # Override area type to be a sequence editor for paste operator to work.
        if not (area := context.area):
            # Context does not have an area in background mode.
            # In that case, just use the first available area and make it active
            # using context override.
            window = context.window_manager.windows[0]
            screen = window.screen
            area = screen.areas[0]
            paste_op_ctx_override.update(
                {
                    "window": window,
                    "screen": screen,
                }
            )
            # CBB: This should not be necessary, but for some reason this is needed
            #      for sequencer.paste to work with the correct scene...
            self.overrides.set(window, "scene", self.dst_scene)

        paste_op_ctx_override["area"] = area

        self.overrides.set(area, "type", "SEQUENCE_EDITOR")
        # Use sequencer editor's "WINDOW" region for operators to work properly.
        paste_op_ctx_override["region"] = next(
            r for r in area.regions if r.type == "WINDOW"
        )
        # Paster operator does not play well with sounds starting before frame 0.
        # To handle pasting such strips, make the copy happen at frame 0, and slide them
        # from the proper offset afterwards.
        self.overrides.set(self.dst_scene, "frame_current", 0)
        frame_offset = self.sound_strips[0].frame_final_start

        try:
            # Call paste operator with scene context override.
            with context.temp_override(**paste_op_ctx_override):
                bpy.ops.sequencer.paste()
                bpy.ops.transform.seq_slide(value=(frame_offset, 0))
        finally:
            self.overrides.revert()

        # Restore original selection.
        with context.temp_override(scene=self.src_scene):
            bpy.ops.sequencer.select_all(action="DESELECT")
        for seq in original_selection:
            seq.select = True


@dataclass
class FitResolutionToContentTask(BaseTask):

    scene: Optional[bpy.types.Scene] = None

    def run(self, context: bpy.types.Context, render_options: BatchRenderOptions):
        self.status = TaskStatus.FINISHED

    def post_run(self, context: bpy.types.Context, render_options: BatchRenderOptions):
        """Fit output scene resolution to visual content."""

        if not self.scene:
            return

        img_seqs = [
            s
            for s in self.scene.sequence_editor.sequences
            if isinstance(s, (bpy.types.MovieSequence, bpy.types.ImageSequence))
        ]

        if not img_seqs:
            return

        # Get maximum width and height of visual strips.
        width = max(seq.elements[0].orig_width for seq in img_seqs)
        height = max(seq.elements[0].orig_height for seq in img_seqs)

        self.scene.render.resolution_x = width
        self.scene.render.resolution_y = height
        self.scene.render.resolution_percentage = 100


@dataclass
class SequenceRenderTask(BaseRenderTask):
    scene: Optional[bpy.types.Scene] = None

    def setup(self, context: bpy.types.Context, render_options: BatchRenderOptions):
        if not self.scene:
            return

        super().setup(context, render_options)

        # Resolve filename and fallback to default naming if current file is not saved.
        filename = bpy.path.display_name_from_filepath(bpy.data.filepath) or "out"
        # Resolve output media filepath based on configured pattern
        variables = {
            "scene": self.scene.name,
            "filename": filename,
        }
        filepath = render_options.output_render_filepath_pattern.format(**variables)
        filepath = self.conform_render_path(filepath)

        # Override render settings based on media type
        file_format, file_ext = MEDIA_TYPES_FORMATS["MOVIE"]

        # Only consider range of video media types.
        sequences = [
            s
            for s in self.scene.sequence_editor.sequences
            if isinstance(s, (bpy.types.MovieSequence, bpy.types.ImageSequence))
        ]

        self.scene.frame_start = min(s.frame_final_start for s in sequences)
        self.scene.frame_end = max(s.frame_final_end for s in sequences) - 1

        # Filepath: add extension to avoid auto frame range suffix
        filepath += f".{file_ext}"
        # Setup render settings
        render = self.scene.render
        self.overrides.set(render.image_settings, "file_format", "FFMPEG")
        self.overrides.set(render.ffmpeg, "format", file_format)
        self.overrides.set(render.ffmpeg, "constant_rate_factor", "PERC_LOSSLESS")
        self.overrides.set(render.ffmpeg, "audio_codec", "AAC")
        self.overrides.set(render, "filepath", filepath)

    def run(self, context, options):
        with context.temp_override(scene=self.scene):
            res = bpy.ops.render.render(self.render_op_exec_context, animation=True)
            if res == {"RUNNING_MODAL"}:
                self.status = TaskStatus.RUNNING
