# --- RIGGING AND CONTROL SETUP ---
"""Bake operators (Features 31-35).

All bake operators use manual frame-by-frame evaluation to avoid
``bpy.ops.nla.bake()`` context-override issues. Transform values are
sampled via ``scene.frame_set()`` + ``obj.matrix_world`` and written
back as keyframes.

Operators:

* **Smart Bake**           — bake + key reduction
* **Reduce Keys**          — simplify existing keys in-place
* **Bake Range**           — bake within configured range only
* **Bake Preview Range**   — bake preview/playback range only
* **Bake Selected Channels** — bake only selected channels
* **Bake Preserve Timing** — bake only at existing keyframe positions
* **Bake Selected**        — bake all selected objects
* **Bake with Step**       — bake every Nth frame
"""

from __future__ import annotations

import math

import bpy

from ..core.logging import get_logger
from ..core.p7_properties import get_p7
from ..core.p7_proxy_math import (
    resolve_bake_range,
    reduce_keys,
    KeySample,
    channels_for_mode,
)
from ..core.fcurve_compat import get_fcurves

_log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Internal bake helpers
# ---------------------------------------------------------------------------

def _get_bake_range(context, p7):
    """Resolve the bake frame range from current settings.

    Handles SCENE, ACTION, CUSTOM, SELECTION, and PREVIEW modes.
    For SELECTION mode, gathers selected keyframe frames from the
    active object's FCurves.
    """
    scene = context.scene
    obj = context.active_object

    action_start = action_end = None
    if obj is not None:
        ad = getattr(obj, "animation_data", None)
        action = getattr(ad, "action", None) if ad else None
        if action is not None:
            action_start, action_end = action.frame_range

    selected_frames = None
    if p7.bake_range_mode == "SELECTION" and obj is not None:
        # Gather all frames where keyframes exist on the active object's FCurves
        frames = set()
        ad = getattr(obj, "animation_data", None)
        action = getattr(ad, "action", None) if ad else None
        if action is not None:
            for fc in get_fcurves(action, anim_data=ad):
                for kp in fc.keyframe_points:
                    if kp.select_control_point:
                        frames.add(float(kp.co.x))
        selected_frames = sorted(frames) if frames else None

    # For PREVIEW mode, pass preview range parameters
    preview_start = preview_end = None
    if p7.bake_range_mode == "PREVIEW" and scene.use_preview_range:
        preview_start = scene.frame_preview_start
        preview_end = scene.frame_preview_end

    return resolve_bake_range(
        mode=p7.bake_range_mode,
        scene_start=scene.frame_start,
        scene_end=scene.frame_end,
        action_start=action_start,
        action_end=action_end,
        custom_start=p7.bake_range_start,
        custom_end=p7.bake_range_end,
        selected_frames=selected_frames,
        preview_start=preview_start,
        preview_end=preview_end,
    )


def _restore_frame(scene, frame: float) -> None:
    """Restore a possibly fractional frame without truncating the subframe."""
    base = math.floor(frame)
    try:
        scene.frame_set(base, subframe=float(frame) - base)
    except TypeError:  # pragma: no cover - very old Blender
        scene.frame_set(base)


def _bake_object_transform(context, obj, frame_start, frame_end, step=1,
                           channel_mode="ALL"):
    """Sample evaluated transforms and insert keyframes.

    Returns the number of keyframes inserted.
    """
    scene = context.scene
    original_frame = float(scene.frame_current_final)
    channels = channels_for_mode(channel_mode)
    inserted = 0

    # Ensure the object has animation data.
    if obj.animation_data is None:
        obj.animation_data_create()
    if obj.animation_data.action is None:
        obj.animation_data.action = bpy.data.actions.new(
            name=f"{obj.name}_P7Bake"
        )

    for frame in range(frame_start, frame_end + 1, step):
        scene.frame_set(frame)
        mat = obj.matrix_world

        if "location" in channels:
            obj.location = mat.to_translation()
            obj.keyframe_insert(data_path="location", frame=frame)
            inserted += 3

        if "rotation_euler" in channels:
            obj.rotation_euler = mat.to_euler()
            obj.keyframe_insert(data_path="rotation_euler", frame=frame)
            inserted += 3

        if "rotation_quaternion" in channels:
            obj.rotation_quaternion = mat.to_quaternion()
            obj.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            inserted += 4

        if "scale" in channels:
            obj.scale = mat.to_scale()
            obj.keyframe_insert(data_path="scale", frame=frame)
            inserted += 3

    # Restore frame.
    _restore_frame(scene, original_frame)

    # Update all FCurves.
    if obj.animation_data and obj.animation_data.action:
        for fc in get_fcurves(obj.animation_data.action, anim_data=obj.animation_data):
            fc.update()

    return inserted


def _reduce_fcurves(obj, tolerance):
    """Apply key reduction to all FCurves on *obj*. Returns keys removed."""
    if obj.animation_data is None or obj.animation_data.action is None:
        return 0

    removed = 0
    for fc in get_fcurves(obj.animation_data.action, anim_data=obj.animation_data):
        kps = fc.keyframe_points
        if len(kps) <= 2:
            continue

        samples = [KeySample(frame=kp.co.x, value=kp.co.y) for kp in kps]
        reduced = reduce_keys(samples, tolerance)
        keep_frames = {s.frame for s in reduced}

        to_remove = [i for i, kp in enumerate(kps) if kp.co.x not in keep_frames]
        for idx in reversed(to_remove):
            kps.remove(kps[idx])
            removed += 1

        fc.update()

    return removed


def _bake_at_existing_keys(context, obj, channel_mode="ALL"):
    """Bake only at frames where keyframes already exist.

    Samples evaluated transforms and updates values at existing keyframe
    positions without inserting new keyframes. Returns the number of
    keyframes updated.
    """
    scene = context.scene
    original_frame = float(scene.frame_current_final)
    channels = channels_for_mode(channel_mode)
    updated = 0

    # Gather all existing keyframe frames
    ad = getattr(obj, "animation_data", None)
    action = getattr(ad, "action", None) if ad else None
    if action is None:
        return 0

    frames = set()
    for fc in get_fcurves(action, anim_data=ad):
        for kp in fc.keyframe_points:
            frames.add(float(kp.co.x))

    if not frames:
        return 0

    for frame in sorted(frames):
        base = math.floor(frame)
        scene.frame_set(base, subframe=frame - base)
        mat = obj.matrix_world

        if "location" in channels:
            obj.location = mat.to_translation()
            obj.keyframe_insert(data_path="location", frame=frame)
            updated += 3

        if "rotation_euler" in channels:
            obj.rotation_euler = mat.to_euler()
            obj.keyframe_insert(data_path="rotation_euler", frame=frame)
            updated += 3

        if "rotation_quaternion" in channels:
            obj.rotation_quaternion = mat.to_quaternion()
            obj.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            updated += 4

        if "scale" in channels:
            obj.scale = mat.to_scale()
            obj.keyframe_insert(data_path="scale", frame=frame)
            updated += 3

    # Restore frame.
    _restore_frame(scene, original_frame)

    # Update all FCurves.
    if action:
        for fc in get_fcurves(action, anim_data=ad):
            fc.update()

    return updated


# ---------------------------------------------------------------------------
# Feature 31 — Bake Selected Range Only
# ---------------------------------------------------------------------------

class AA_OT_p7_bake_range(bpy.types.Operator):
    """Bake only within the configured frame range."""

    bl_idname = "animassist.p7_bake_range"
    bl_label = "Bake Range"
    bl_description = (
        "Bake the active object's evaluated transform within the "
        "configured bake range (SCENE, ACTION, CUSTOM, SELECTION, or PREVIEW mode)"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and get_p7(context) is not None

    def execute(self, context):
        p7 = get_p7(context)
        obj = context.active_object
        frame_start, frame_end = _get_bake_range(context, p7)

        inserted = _bake_object_transform(
            context, obj, frame_start, frame_end,
            step=p7.bake_step, channel_mode=p7.bake_channels,
        )
        self.report({"INFO"},
                    f"Baked range [{frame_start}–{frame_end}]: {inserted} keys")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Feature 32 — Bake Preview Range
# ---------------------------------------------------------------------------

class AA_OT_p7_bake_preview(bpy.types.Operator):
    """Bake only the preview/playback range."""

    bl_idname = "animassist.p7_bake_preview"
    bl_label = "Bake Preview Range"
    bl_description = (
        "Bake the active object's evaluated transform within the "
        "preview/playback range only"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        scene = context.scene
        return (context.active_object is not None and
                get_p7(context) is not None and
                scene.use_preview_range)

    def execute(self, context):
        p7 = get_p7(context)
        obj = context.active_object
        scene = context.scene

        if not scene.use_preview_range:
            self.report({"WARNING"}, "Preview range is not enabled")
            return {"CANCELLED"}

        frame_start = scene.frame_preview_start
        frame_end = scene.frame_preview_end

        inserted = _bake_object_transform(
            context, obj, frame_start, frame_end,
            step=p7.bake_step, channel_mode=p7.bake_channels,
        )
        self.report({"INFO"},
                    f"Baked preview range [{frame_start}–{frame_end}]: {inserted} keys")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Feature 33 — Bake Selected Channels Only
# ---------------------------------------------------------------------------

class AA_OT_p7_bake_selected_channels(bpy.types.Operator):
    """Bake only selected channels."""

    bl_idname = "animassist.p7_bake_selected_channels"
    bl_label = "Bake Selected Channels"
    bl_description = (
        "Bake the active object's evaluated transform using "
        "the SELECTED channel mode (existing keyframe channels)"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and get_p7(context) is not None

    def execute(self, context):
        p7 = get_p7(context)
        obj = context.active_object
        frame_start, frame_end = _get_bake_range(context, p7)

        # For SELECTED mode, we need to determine which channels have existing keys
        # The channels_for_mode returns () for SELECTED, so we need to gather them
        ad = getattr(obj, "animation_data", None)
        action = getattr(ad, "action", None) if ad else None
        selected_channels = set()

        if action is not None:
            for fc in get_fcurves(action, anim_data=ad):
                # Extract channel group from data_path (e.g., "location", "rotation_euler")
                data_path = fc.data_path
                if data_path.startswith("location"):
                    selected_channels.add("location")
                elif data_path.startswith("rotation_euler"):
                    selected_channels.add("rotation_euler")
                elif data_path.startswith("rotation_quaternion"):
                    selected_channels.add("rotation_quaternion")
                elif data_path.startswith("scale"):
                    selected_channels.add("scale")

        if not selected_channels:
            self.report({"WARNING"}, "No existing animation channels found")
            return {"CANCELLED"}

        # Manually bake only the selected channels
        scene = context.scene
        original_frame = float(scene.frame_current_final)
        inserted = 0

        for frame in range(frame_start, frame_end + 1, p7.bake_step):
            scene.frame_set(frame)
            mat = obj.matrix_world

            if "location" in selected_channels:
                obj.location = mat.to_translation()
                obj.keyframe_insert(data_path="location", frame=frame)
                inserted += 3

            if "rotation_euler" in selected_channels:
                obj.rotation_euler = mat.to_euler()
                obj.keyframe_insert(data_path="rotation_euler", frame=frame)
                inserted += 3

            if "rotation_quaternion" in selected_channels:
                obj.rotation_quaternion = mat.to_quaternion()
                obj.keyframe_insert(data_path="rotation_quaternion", frame=frame)
                inserted += 4

            if "scale" in selected_channels:
                obj.scale = mat.to_scale()
                obj.keyframe_insert(data_path="scale", frame=frame)
                inserted += 3

        _restore_frame(scene, original_frame)

        if action:
            for fc in get_fcurves(action, anim_data=ad):
                fc.update()

        self.report({"INFO"},
                    f"Baked {len(selected_channels)} channel(s): {inserted} keys")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Feature 34 — Smart Bake with Key Reduction Safety
# ---------------------------------------------------------------------------

class AA_OT_p7_smart_bake(bpy.types.Operator):
    """Bake with automatic key reduction to minimize keyframe count."""

    bl_idname = "animassist.p7_smart_bake"
    bl_label = "Smart Bake"
    bl_description = (
        "Bake the active object's evaluated transform, then apply "
        "key reduction to remove redundant keyframes"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and get_p7(context) is not None

    def execute(self, context):
        p7 = get_p7(context)
        obj = context.active_object
        frame_start, frame_end = _get_bake_range(context, p7)

        inserted = _bake_object_transform(
            context, obj, frame_start, frame_end,
            step=1, channel_mode=p7.bake_channels,
        )
        removed = _reduce_fcurves(obj, p7.smart_bake_tolerance)

        self.report({"INFO"},
                    f"Smart bake: {inserted} keys baked, "
                    f"{removed} redundant key(s) removed")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Feature 34 utility — Reduce Keys
# ---------------------------------------------------------------------------

class AA_OT_p7_reduce_keys(bpy.types.Operator):
    """Remove redundant keys from existing animation curves."""

    bl_idname = "animassist.p7_reduce_keys"
    bl_label = "Reduce Keys"
    bl_description = (
        "Simplify the active object's existing animation by removing "
        "keyframes whose deletion causes less than the tolerance deviation"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if obj is None:
            return False
        ad = getattr(obj, "animation_data", None)
        return ad is not None and getattr(ad, "action", None) is not None

    def execute(self, context):
        p7 = get_p7(context)
        tolerance = p7.smart_bake_tolerance if p7 else 0.01
        removed = _reduce_fcurves(context.active_object, tolerance)
        self.report({"INFO"}, f"Removed {removed} redundant key(s)")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Feature 35 — Preserve Existing Timing on Bake
# ---------------------------------------------------------------------------

class AA_OT_p7_bake_preserve_timing(bpy.types.Operator):
    """Bake but only update values at existing keyframe positions."""

    bl_idname = "animassist.p7_bake_preserve_timing"
    bl_label = "Bake Preserve Timing"
    bl_description = (
        "Bake the active object's evaluated transform while preserving "
        "existing keyframe timing (updates values at existing key positions only)"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if obj is None:
            return False
        ad = getattr(obj, "animation_data", None)
        action = getattr(ad, "action", None) if ad else None
        return action is not None

    def execute(self, context):
        p7 = get_p7(context)
        obj = context.active_object

        updated = _bake_at_existing_keys(
            context, obj, channel_mode=p7.bake_channels
        )

        self.report({"INFO"}, f"Preserved timing: {updated} keys updated")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Utility — Bake All Selected
# ---------------------------------------------------------------------------

class AA_OT_p7_bake_selected(bpy.types.Operator):
    """Bake all selected objects."""

    bl_idname = "animassist.p7_bake_selected"
    bl_label = "Bake Selected"
    bl_description = (
        "Bake the evaluated transform of every selected object "
        "within the configured bake range"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return bool(context.selected_objects) and get_p7(context) is not None

    def execute(self, context):
        p7 = get_p7(context)
        frame_start, frame_end = _get_bake_range(context, p7)
        total = 0
        for obj in context.selected_objects:
            n = _bake_object_transform(
                context, obj, frame_start, frame_end,
                step=p7.bake_step, channel_mode=p7.bake_channels,
            )
            total += n
        self.report({"INFO"},
                    f"Baked {len(context.selected_objects)} object(s), {total} keys")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Utility — Bake with Step
# ---------------------------------------------------------------------------

class AA_OT_p7_bake_step(bpy.types.Operator):
    """Bake every Nth frame."""

    bl_idname = "animassist.p7_bake_step"
    bl_label = "Bake with Step"
    bl_description = (
        "Bake the active object's evaluated transform at every Nth frame "
        "(controlled by the Frame Step setting)"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and get_p7(context) is not None

    def execute(self, context):
        p7 = get_p7(context)
        obj = context.active_object
        frame_start, frame_end = _get_bake_range(context, p7)

        inserted = _bake_object_transform(
            context, obj, frame_start, frame_end,
            step=max(1, p7.bake_step), channel_mode=p7.bake_channels,
        )
        self.report({"INFO"},
                    f"Baked every {p7.bake_step} frame(s): {inserted} keys")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Class list
# ---------------------------------------------------------------------------

CLASSES: tuple[type, ...] = (
    AA_OT_p7_bake_range,
    AA_OT_p7_bake_preview,
    AA_OT_p7_bake_selected_channels,
    AA_OT_p7_smart_bake,
    AA_OT_p7_reduce_keys,
    AA_OT_p7_bake_preserve_timing,
    AA_OT_p7_bake_selected,
    AA_OT_p7_bake_step,
)
