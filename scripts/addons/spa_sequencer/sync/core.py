# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2023, The SPA Studios. All rights reserved.

from contextlib import contextmanager
from typing import Any, Callable, Optional, Union, Type

import bpy

from spa_sequencer.utils import register_classes, unregister_classes


SequenceType = Type[bpy.types.Sequence]


class TimelineSyncSettings(bpy.types.PropertyGroup):
    """Timeline Synchronization Settings."""

    enabled: bpy.props.BoolProperty(
        name="Enabled",
        description="Status of Timeline Synchronization system",
        default=False,
    )

    master_scene: bpy.props.PointerProperty(
        type=bpy.types.Scene,
        name="Master Scene",
        description="The Scene that drives the Timeline Synchronization",
    )

    bidirectional: bpy.props.BoolProperty(
        name="Bidirectional",
        description=(
            "Whether changing the active Scene's time should update "
            "the Master Scene's current frame"
        ),
        default=True,
    )

    sync_all_windows: bpy.props.BoolProperty(
        name="Synchronize all Windows",
        description="Whether the Timeline Synchronization impacts all Main Windows",
        default=False,
    )

    keep_gpencil_tool_settings: bpy.props.BoolProperty(
        name="Keep Grease Pencil Settings",
        description="Keep active Grease Pencil tool settings while navigating Shots",
        default=True,
    )

    def use_preview_range_update_callback(self, context):
        # Update master strip preview range when the option is changed
        if (
            strip := get_sync_master_strip(use_cache=True)[0]
        ) and self.use_preview_range:
            update_preview_range(strip)

    use_preview_range: bpy.props.BoolProperty(
        name="Use Preview Range",
        description=(
            "Update the preview range of current strip's scene to match the useful "
            "range of this strip"
        ),
        default=True,
        update=use_preview_range_update_callback,
    )

    # Cached values from last update
    # See sync_system_update function for details

    last_master_frame: bpy.props.IntProperty(
        description="Last frame value that triggered an update in master Scene",
        default=-1,
        options={"HIDDEN"},
    )

    last_master_strip: bpy.props.StringProperty(
        description="Name of the Scene Strip used during the last Synchronization update",
        default="",
        options={"HIDDEN"},
    )

    last_master_strip_idx: bpy.props.IntProperty(
        description="Index of the Scene Strip used during the last Synchronization update",
        default=-1,
        options={"HIDDEN"},
    )

    last_strip_scene_frame: bpy.props.IntProperty(
        description="Last frame value that triggered an update in master strip's Scene",
        default=-1,
        options={"HIDDEN"},
    )

    last_strip_scene_frame_out_of_range: bpy.props.BoolProperty(
        description="Whether frame value in master strip's Scene is out of strip range",
        default=True,
        options={"HIDDEN"},
    )

    last_gp_mode: bpy.props.StringProperty(
        description="Last grease pencil interaction mode",
        default="",
        options={"HIDDEN"},
    )

    active_follows_playhead: bpy.props.BoolProperty(
        name="Active Follows Playhead",
        description=("Update the active strip while scrubbing the sequencer"),
        default=False,
        update=use_preview_range_update_callback,
    )


def get_sync_settings() -> TimelineSyncSettings:
    """Return the TimelineSyncSettings instance."""
    return bpy.context.window_manager.timeline_sync_settings


# Main scene frame set function that will use the optimized or fallback to default
# implementation.
scene_frame_set: Optional[
    Callable[[bpy.types.Context, bpy.types.Scene, int], None]
] = None


def _scene_frame_set_default(
    context: bpy.types.Context, scene: bpy.types.Scene, frame: int
):
    """Default implementation of scene.frame_set."""
    scene.frame_set(frame)


def _scene_frame_set_optimized(
    context: bpy.types.Context, scene: bpy.types.Scene, frame: int
):
    """Set `scene` frame with improved performance when playback is active.

    :param context: The active context.
    :param scene: The scene to set current frame on.
    :param frame: The frame value.
    """
    # This relies on a custom extension of the `frame_set` API.
    try:
        # Performance: only trigger notifiers when playback is not active
        scene.frame_set(frame, notify=not context.screen.is_animation_playing)
    except TypeError:
        # If notify is not available, re-assign `scene_frame_set` to use default
        # frame_set for the next calls.
        # This avoids going into exception catching everytime, which could impact
        # performance.
        global scene_frame_set
        scene_frame_set = _scene_frame_set_default
        scene_frame_set(context, scene, frame)


# Default to optimized implementation of frame_set.
scene_frame_set = _scene_frame_set_optimized


def remap_frame_value(frame: int, scene_strip: bpy.types.SceneSequence) -> int:
    """Remap `frame` in `scene_strip`'s underlying scene reference.

    :param frame: The frame to remap
    :param scene_strip: The scene strip to remap to.
    :returns: The remapped frame value
    """
    return int(frame - scene_strip.frame_start + scene_strip.scene.frame_start)


def get_strips_at_frame(
    frame: int,
    strips: list[bpy.types.Sequence],
    type_filter: Union[SequenceType, tuple[SequenceType, ...]] = None,
    skip_muted: bool = True,
) -> list[bpy.types.Sequence]:
    """
    Get all strips containing the given `frame` within their final range.

    :param frame: The frame value
    :param strips: The strips to consider
    :param type_filter: Only consider strips that are instances of the given type(s)
    :param skip_muted: Whether to skip muted strips
    :returns: The subset of strips matching the given parameters
    """
    return [
        s
        for s in strips
        if (
            (not type_filter or isinstance(s, type_filter))
            and (not skip_muted or not s.mute)
            and (frame >= s.frame_final_start and frame < s.frame_final_end)
        )
    ]


def get_scene_strip_at_frame(
    frame: int,
    sequence_editor: bpy.types.SequenceEditor,
    skip_muted: bool = True,
) -> tuple[Union[bpy.types.SceneSequence, None], int]:
    """
    Get the scene strip at `frame` in `sequence_editor`'s strips with the highest
    channel number.

    :param frame: The frame value
    :param sequence_editor: Sequence editor containing the strips
    :param skip_muted: Exclude muted strips
    :returns: The scene strip (or None) and the frame in underlying scene's reference
    """

    strips = sequence_editor.sequences
    channels = sequence_editor.channels

    if skip_muted:
        # Exclude strips from muted channels
        muted_channels = [idx for idx, channel in enumerate(channels) if channel.mute]
        strips = [strip for strip in strips if not strip.channel in muted_channels]

    strips = get_strips_at_frame(frame, strips, bpy.types.SceneSequence, skip_muted)

    if not strips:
        return None, frame
    # Sort strips by channel
    strip = sorted(strips, key=lambda x: x.channel)[-1]

    # Help type checking: strip can only be a SceneSequence here
    assert isinstance(strip, bpy.types.SceneSequence)

    # Only consider scene strips with a valid scene
    if not strip.scene:
        return None, frame

    # Compute frame in underlying scene's reference
    return strip, remap_frame_value(frame, strip)


@contextmanager
def scene_change_manager(context: bpy.types.Context):
    """
    A context manager for saving/restoring states when changing a window's active Scene.

    :param context: The current context
    """
    sync_settings = get_sync_settings()
    tool_settings = context.window.scene.tool_settings

    def get_attrs(obj: object, names: list[str]) -> dict[str, Any]:
        """Get several named attributes from an object as a {name: value} dict."""
        return {name: getattr(obj, name) for name in names} if obj else {}

    def set_attrs(obj: object, attrs: dict[str, Any]):
        """Set several named attributes on an object."""
        if not obj:
            return
        for key, value in attrs.items():
            if getattr(obj, key, None) != value:
                setattr(obj, key, value)

    # Store settings
    if sync_settings.keep_gpencil_tool_settings:
        paint_settings = get_attrs(
            tool_settings.gpencil_paint, ("brush", "color_mode", "palette")
        )
        sculpt_settings = get_attrs(tool_settings.gpencil_sculpt_paint, ("brush",))
        edit_settings = get_attrs(tool_settings, ("gpencil_selectmode_edit",))

        # Safely get GP paint option set by SPA 2D animation addon.
        if hasattr(context.window.scene, "gp_paint_color"):
            scene_settings = get_attrs(
                context.window.scene.gp_paint_color, ("mode", "vertex_color_style")
            )

        # Store the active GP material and mode if any
        gp_material = None

        if context.active_object and isinstance(
            context.active_object.data, bpy.types.GreasePencil
        ):
            gp_material = context.active_object.active_material
            sync_settings.last_gp_mode = context.active_object.mode

    yield

    # Apply settings
    if sync_settings.keep_gpencil_tool_settings:
        tool_settings = context.window.scene.tool_settings
        set_attrs(tool_settings.gpencil_paint, paint_settings)
        set_attrs(tool_settings.gpencil_sculpt_paint, sculpt_settings)
        set_attrs(tool_settings, edit_settings)
        if hasattr(context.window.scene, "gp_paint_color"):
            set_attrs(context.window.scene.gp_paint_color, scene_settings)

        # If the new active object is a GP, restore the previously stored material
        # as active if also assigned.
        if (gpencil := context.active_object) and isinstance(
            gpencil.data, bpy.types.GreasePencil
        ):
            if gp_material:
                material_idx = gpencil.data.materials.find(gp_material.name)
                if material_idx >= 0:
                    gpencil.active_material_index = material_idx

            gp_mode = sync_settings.last_gp_mode
            if gp_mode and gpencil.mode != gp_mode:
                set_gpencil_mode_safe(context, gpencil, gp_mode)


def set_gpencil_mode_safe(
    context: bpy.types.Context, gpencil: bpy.types.Object, mode: str
):
    """
    Safely set the interaction `mode` on `gpencil` by handling inconsistencies
    between object mode and internal gpencil data flags that could lead to errors.

    :param context: The current context
    :param gpencil: The grease pencil object to set the mode of
    :param mode: The mode to activate
    """
    # Override context: "object.mode_set" uses view_layer's active object
    with context.temp_override(
        scene=context.window.scene,
        view_layer=context.window.scene.view_layers[0],
        active_object=gpencil,
    ):
        # There might be inconsistencies between the object interaction mode and
        # the mode flag on the gp data itself (is_stroke_{modename}_mode).
        # When that happens, switching to the mode fails.
        # If data flag for this mode is already activated, switch to the safe
        # 'EDIT_GPENCIL' mode first as a workaround to sync back the flags.
        if mode not in ("OBJECT", "EDIT_GPENCIL"):
            # Get short name for this mode to build data flag
            # e.g: PAINT_GPENCIL => paint
            mode_short = mode.split("_")[0].lower()
            # Switch to edit mode first if data flags is activated
            if getattr(gpencil.data, f"is_stroke_{mode_short}_mode", False):
                bpy.ops.object.mode_set(mode="EDIT_GPENCIL")
        # Switch the object interaction mode
        bpy.ops.object.mode_set(mode=mode)


def get_sync_master_strip(
    use_cache: bool = False,
) -> tuple[Union[bpy.types.SceneSequence, None], int]:
    """
    Return the scene strip currently used by the Timeline Synchronization.

    :param use_cache: If True, return last cached value. Compute from current master time otherwise.
    """
    settings = get_sync_settings()
    master_scene = settings.master_scene
    if not settings.enabled or not master_scene or not master_scene.sequence_editor:
        return None, -1

    if use_cache:
        return (
            master_scene.sequence_editor.sequences.get(settings.last_master_strip),
            settings.last_strip_scene_frame,
        )

    return get_scene_strip_at_frame(
        master_scene.frame_current,
        master_scene.sequence_editor,
    )


def update_preview_range(scene_strip: bpy.types.SceneSequence):
    """Update `scene_strip`'s scene preview range to match `scene_strip`'s range.

    :param scene_strip: The scene strip to update.
    """
    # Discard scene strip without scene
    if not scene_strip.scene:
        return

    # Ensure strip's scene is using preview range.
    # NOTE: This has to be done only if it's not the case, otherwise playback
    #       performance are degraded due to UI updates caused by this action.
    if not scene_strip.scene.use_preview_range:
        scene_strip.scene.use_preview_range = True

    # Compute and update preview range if necessary
    start = remap_frame_value(scene_strip.frame_final_start, scene_strip)
    end = remap_frame_value(scene_strip.frame_final_end, scene_strip) - 1
    if start != scene_strip.scene.frame_preview_start:
        scene_strip.scene.frame_preview_start = start
    if end != scene_strip.scene.frame_preview_end:
        scene_strip.scene.frame_preview_end = end


def sync_system_update(context: bpy.types.Context, force: bool = False):
    """Perform the synchronization system update.

    :param context: The active context.
    :param force: Whether to force the update, even if time did not change.
    """

    # Discard windows without scene (may happen during render)
    if not context.window:
        return

    sync_settings = get_sync_settings()
    master_scene = sync_settings.master_scene
    win_scene = context.window.scene

    # Discard update if disabled or not properly configured
    if (
        not sync_settings.enabled
        or not master_scene
        or not master_scene.sequence_editor
    ):
        return

    # In order to evaluate if the master scene's current frame has changed,
    # we current have to rely on a system that stores the last frame values
    # that triggered a change.
    # This is a temporary solution that will be replaced when the
    # frame_change_post callback recieve the correct Scene.
    master_time_changed = sync_settings.last_master_frame != master_scene.frame_current
    scene_time_changed = sync_settings.last_strip_scene_frame != win_scene.frame_current

    # Take `force` update into account.
    master_time_changed |= force

    # Discard update if master scene's current frame is similar to cached frame value
    if not sync_settings.bidirectional and not master_time_changed:
        return

    if sync_settings.bidirectional and not master_time_changed:
        # Return if time has not changed in active scene
        if not scene_time_changed:
            return

        # Get sync master strip.
        # NOTE: use cached value as a convenient shortcut to avoid computing it again.
        strip = master_scene.sequence_editor.sequences.get(
            sync_settings.last_master_strip
        )

        # Return if the master strip does not match currently active scene.
        if not strip or strip.scene != win_scene:
            return

        # Compute offset between scene's previous and current frame values
        offset = win_scene.frame_current - sync_settings.last_strip_scene_frame

        # Evaluate strip in master scene when applying this offset
        new_strip, _ = get_scene_strip_at_frame(
            master_scene.frame_current + offset,
            master_scene.sequence_editor,
        )

        # No strip is available: stop here.
        if not new_strip:
            return

        # Strip at target time is valid but differs from current master strip:
        if new_strip != strip:

            # Discard changes coming from outside the strip range.
            if sync_settings.last_strip_scene_frame_out_of_range:
                return

            # Compute strip range in scene's referential
            frame_start = remap_frame_value(strip.frame_final_start, strip)
            frame_end = remap_frame_value(strip.frame_final_end - 1, strip)

            # Compute new strip range in current strip referential
            new_strip_start = remap_frame_value(new_strip.frame_final_start, strip)
            new_strip_end = remap_frame_value(new_strip.frame_final_end - 1, strip)

            # If current frame is not consecutive to current strip boundary
            # or equal to one of the new strip's boundary,
            # identify as out of range and discard update.
            if win_scene.frame_current not in (
                frame_start - 1,
                frame_end + 1,
                new_strip_start,
                new_strip_end,
            ):
                sync_settings.last_strip_scene_frame_out_of_range = True
                return

            # Only tolerate offset values of 1 to jump between strips.
            if abs(offset) != 1:
                return

            # Don't update master time if user is scrubbing through the timeline
            # or if the animation is playing to avoid unwanted scene switching.
            if context.screen.is_scrubbing or context.screen.is_animation_playing:
                return

        # Apply the offset to master scene, and return.
        # The master scene and cache update will happen in the next frame_change_post
        # handler call.
        scene_frame_set(context, master_scene, master_scene.frame_current + offset)
        return

    # Update cached frame cache value
    sync_settings.last_master_frame = master_scene.frame_current

    # Get scene strip at current frame
    strip, inner_frame = get_scene_strip_at_frame(
        master_scene.frame_current,
        master_scene.sequence_editor,
    )
    # Discard update if no such strip exists
    if not strip:
        sync_settings.last_master_strip = ""
        sync_settings.last_master_strip_idx = -1
        sync_settings.last_strip_scene_frame = -1
        return

    # Update cached values
    sync_settings.last_master_strip = strip.name
    sync_settings.last_master_strip_idx = master_scene.sequence_editor.sequences.find(
        strip.name
    )
    sync_settings.last_strip_scene_frame = inner_frame
    sync_settings.last_strip_scene_frame_out_of_range = False

    # Update strip's underlying scene frame before making it active in context's window
    # to avoid unwanted updates in case bidirectional sync is enabled.
    if strip.scene.frame_current != inner_frame:
        scene_frame_set(context, strip.scene, inner_frame)

    if sync_settings.use_preview_range:
        # Update scene's preview range.
        update_preview_range(strip)

    # Synchronize target windows
    for window in (
        context.window_manager.windows
        if sync_settings.sync_all_windows
        else [context.window]
    ):
        # If window's scene is explicitly set to master scene, don't update it.
        if not bpy.app.background and window.scene == master_scene:
            continue
        # Open strip's scene in window at the remapped frame
        if window.scene != strip.scene:
            # Use scene_change_manager to optionnaly keep tool settings between scenes
            with scene_change_manager(context):
                window.scene = strip.scene
        # Use strip camera if specified
        if strip.scene_camera and window.scene.camera != strip.scene_camera:
            window.scene.camera = strip.scene_camera

    if sync_settings.active_follows_playhead:
        if master_scene.sequence_editor.active_strip != strip:
            master_scene.sequence_editor.active_strip = strip


@bpy.app.handlers.persistent
def on_frame_changed(scene: bpy.types.Scene, depsgraph: bpy.types.Depsgraph):
    # Early return when context is still a restricted context
    if not isinstance(bpy.context, bpy.types.Context):
        return

    # Update Timeline Synchronization system
    sync_system_update(bpy.context)


def update_sync_cache_from_current_state():
    """
    Update Timeline Synchronization cached values based on file's current state.
    """
    sync_settings = get_sync_settings()
    sync_settings.last_master_frame = sync_settings.master_scene.frame_current
    strip, frame = get_sync_master_strip()
    sync_settings.last_master_strip = strip.name if strip else ""
    sync_settings.last_master_strip_idx = (
        sync_settings.master_scene.sequence_editor.sequences.find(strip.name)
        if strip
        else -1
    )
    sync_settings.last_strip_scene_frame = frame
    sync_settings.last_strip_scene_frame_out_of_range = not strip


@bpy.app.handlers.persistent
def on_load_pre(*args):
    sync_settings = get_sync_settings()
    # Reset Timeline Synchronization settings
    sync_settings.enabled = False
    sync_settings.master_scene = None
    sync_settings.last_master_frame = -1
    sync_settings.last_master_strip = ""
    sync_settings.last_master_strip_idx = -1
    sync_settings.last_strip_scene_frame = -1
    sync_settings.last_strip_scene_frame_out_of_range = True
    sync_settings.last_gp_mode = ""


@bpy.app.handlers.persistent
def on_load_post(*args):
    sync_settings = get_sync_settings()
    # Auto-setup the system for the new file if the active screen contains
    # a Sequence Editor area defining a scene override with at least 1 scene strip.
    for area in bpy.context.screen.areas:
        space = area.spaces.active
        if isinstance(space, bpy.types.SpaceSequenceEditor) and getattr(
            space, "scene_override", False
        ):
            seq_editor = area.spaces.active.scene_override.sequence_editor
            if seq_editor and any(
                isinstance(s, bpy.types.SceneSequence) for s in seq_editor.sequences
            ):
                sync_settings.master_scene = area.spaces.active.scene_override
                sync_settings.enabled = True
                update_sync_cache_from_current_state()
                break


@bpy.app.handlers.persistent
def on_undo_redo(scene, _):
    """Undo/Redo post handler callback."""
    sync_settings = get_sync_settings()
    if not sync_settings.enabled:
        return

    # Explicitly update cached values on undo/redo events since
    # they don't re-trigger frame change events.
    # Two update cases:
    # 1. Event comes from master scene and master time has changed
    # 2. (Bidirectional ON) Event comes from window's scene and scene time has changed
    if (
        scene == sync_settings.master_scene
        and sync_settings.master_scene.frame_current != sync_settings.last_master_frame
    ) or (
        sync_settings.bidirectional
        and scene == bpy.context.window.scene
        and scene.frame_current != sync_settings.last_strip_scene_frame
    ):
        update_sync_cache_from_current_state()


classes = (TimelineSyncSettings,)


def register():
    register_classes(classes)

    # Store Synchronization settings on the WindowManager type
    # NOTE: this is not saved in the Blender file
    bpy.types.WindowManager.timeline_sync_settings = bpy.props.PointerProperty(
        type=TimelineSyncSettings,
        name="Timeline Synchronization Settings",
    )

    # React to scenes current frame changes
    bpy.app.handlers.frame_change_post.append(on_frame_changed)
    # React to file opening
    bpy.app.handlers.load_pre.append(on_load_pre)
    bpy.app.handlers.load_post.append(on_load_post)

    bpy.app.handlers.undo_post.append(on_undo_redo)
    bpy.app.handlers.redo_post.append(on_undo_redo)


def unregister():
    unregister_classes(classes)

    del bpy.types.WindowManager.timeline_sync_settings
    bpy.app.handlers.frame_change_post.remove(on_frame_changed)
    bpy.app.handlers.load_pre.remove(on_load_pre)
    bpy.app.handlers.load_post.remove(on_load_post)

    bpy.app.handlers.undo_post.remove(on_undo_redo)
    bpy.app.handlers.redo_post.remove(on_undo_redo)
