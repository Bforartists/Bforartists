"""Anim Offset operators and modal propagation."""

from __future__ import annotations

import bpy
from bpy.props import FloatProperty
from bpy.types import Operator

from ..core.anim_offset import (
    MaskRegion,
    compute_propagated_values,
    compute_propagated_values_full_range,
    frames_outside_mask,
)
from ..core.fcurve_compat import get_fcurves
from ..core.p6_retime_math import backup_fcurves, restore_fcurves
from ..core.utils import EPSILON


_TIMER_STEP: float = 0.08
_sessions = {}


def offset_session_status(scene, mask_scene=None):
    """Describe the captured target and the mask actually read by propagation."""
    target = _sessions.get(scene.as_pointer())
    if not target or not scene.anim_assist.anim_offset_active:
        return ""
    mask = (mask_scene or scene).anim_assist.mask
    coverage = (f"mask {min(mask.start_frame, mask.end_frame)}–{max(mask.start_frame, mask.end_frame)} "
                f"(blend {mask.blend_left}/{mask.blend_right})" if mask.enabled else "all frames")
    try:
        return f"{target[0].name} / {target[1].name} | {coverage}"
    except ReferenceError:
        return f"Captured target removed | {coverage}"


def _addon_prefs(context: bpy.types.Context):
    from ..prefs import get_prefs
    return get_prefs(context)


def _target_object(context: bpy.types.Context):
    """The object Anim Offset works on. ``context.object`` is empty in the
    Properties editor's Scene tab, where the Anim Assist home lives, so fall
    back to the active object."""
    return context.object or context.active_object


def _object_fcurves(context: bpy.types.Context) -> list:
    obj = _target_object(context)
    if obj and obj.animation_data and obj.animation_data.action:
        return [fc for fc in get_fcurves(obj.animation_data.action, anim_data=obj.animation_data) if not fc.lock and not fc.hide]
    return []


def _snapshot_all(fcurves: list) -> dict[int, dict[float, float]]:
    return {i: {kp.co[0]: kp.co[1] for kp in fc.keyframe_points} for i, fc in enumerate(fcurves)}


def _snapshot_for_cancel(fcurves: list) -> list[dict]:
    """Retain curve geometry and key metadata, including user edits to handles."""
    backups = backup_fcurves(fcurves)
    for fc, backup in zip(fcurves, backups):
        for key, stored in zip(fc.keyframe_points, backup["keys"]):
            stored.update(type=key.type, amplitude=key.amplitude,
                          back=key.back, period=key.period,
                          sel_left=key.select_left_handle,
                          sel_right=key.select_right_handle)
    return backups


def _restore_cancel_snapshot(fcurves: list, backups: list[dict]) -> None:
    restore_fcurves(fcurves, backups)
    for fc, backup in zip(fcurves, backups):
        for key, stored in zip(fc.keyframe_points, backup["keys"]):
            key.type = stored["type"]
            key.amplitude = stored["amplitude"]
            key.back = stored["back"]
            key.period = stored["period"]
            key.select_left_handle = stored["sel_left"]
            key.select_right_handle = stored["sel_right"]


def _key_value_at_frame(fc, frame: float):
    for kp in fc.keyframe_points:
        if abs(kp.co[0] - frame) < EPSILON:
            return kp.co[1]
    return None


def _snapshot_at_frame(fcurves: list, frame: float) -> dict[int, float]:
    values: dict[int, float] = {}
    for i, fc in enumerate(fcurves):
        v = _key_value_at_frame(fc, frame)
        values[i] = fc.evaluate(frame) if v is None else v
    return values


def _has_key_at_frame(fc, frame: float) -> bool:
    for kp in fc.keyframe_points:
        if abs(kp.co[0] - frame) < EPSILON:
            return True
    return False


class ANIMASSIST_OT_anim_offset(Operator):
    bl_idname = "animassist.anim_offset"
    bl_label = "Anim Offset"
    bl_description = "Toggle Anim Offset mode and propagate current-frame edits across keyed animation"
    # UNDO: the modal writes keyframe values and inserts keys directly; without
    # it, Blender pushes no undo step on FINISHED and the session can't be reverted.
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _target_object(context) is not None

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        # ACCESS_GATE_HERE
        try:
            settings = context.scene.anim_assist

            if settings.anim_offset_active:
                settings.anim_offset_active = False
                return {"FINISHED"}

            self._fcurves = _object_fcurves(context)
            if not self._fcurves:
                self.report({"WARNING"}, "Active object has no editable animation curves")
                return {"CANCELLED"}

            self._current_frame = float(context.scene.frame_current)
            self._snap_all = _snapshot_all(self._fcurves)
            self._snap_cancel = _snapshot_for_cancel(self._fcurves)
            self._snap_frame = _snapshot_at_frame(self._fcurves, self._current_frame)
            self._propagating = False
            self._pending_fast_update = False

            settings.anim_offset_active = True
            obj = _target_object(context)
            self._scene = context.scene
            _sessions[self._scene.as_pointer()] = (obj, obj.animation_data.action)
            self._status(context)
            self._timer = context.window_manager.event_timer_add(_TIMER_STEP, window=context.window)
            context.window_manager.modal_handler_add(self)
            self.report({"INFO"}, f"Offset active: {offset_session_status(context.scene)}")
            return {"RUNNING_MODAL"}
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

    def modal(self, context: bpy.types.Context, event: bpy.types.Event):
        settings = context.scene.anim_assist
        prefs = _addon_prefs(context)

        if not settings.anim_offset_active:
            self._cleanup(context)
            self.report({"INFO"}, "Anim Offset deactivated")
            return {"FINISHED"}

        if event.type == "ESC" and event.value == "PRESS":
            self._restore_all()
            self._cleanup(context)
            if context.area:
                context.area.tag_redraw()
            return {"CANCELLED"}

        if event.type == "MOUSEMOVE":
            self._pending_fast_update = True

        if event.type == "LEFTMOUSE" and event.value == "RELEASE":
            self._pending_fast_update = True
            if prefs and prefs.animassist_fast_offset:
                self._propagate(context)

        if event.type == "TIMER":
            self._status(context)
            if prefs and prefs.animassist_fast_offset:
                # fast mode: only apply on mouse release
                pass
            else:
                self._propagate(context)

        return {"PASS_THROUGH"}

    def _status(self, context):
        if context.workspace:
            context.workspace.status_text_set(
                f"Action Offset: {offset_session_status(self._scene, context.scene)} | Toggle: finish | Esc: restore snapshot")

    def _build_mask(self, context: bpy.types.Context) -> MaskRegion:
        m = context.scene.anim_assist.mask
        start = float(min(m.start_frame, m.end_frame))
        end = float(max(m.start_frame, m.end_frame))
        return MaskRegion(
            start=start,
            end=end,
            blend_in=float(max(0, m.blend_left)),
            blend_out=float(max(0, m.blend_right)),
            enabled=bool(m.enabled),
        )

    def _propagate(self, context: bpy.types.Context) -> None:
        if self._propagating:
            return

        self._propagating = True
        try:
            cur = float(context.scene.frame_current)
            prefs = _addon_prefs(context)

            if abs(cur - self._current_frame) > EPSILON:
                self._current_frame = cur
                self._snap_all = _snapshot_all(self._fcurves)
                self._snap_cancel = _snapshot_for_cancel(self._fcurves)
                self._snap_frame = _snapshot_at_frame(self._fcurves, cur)
                self._pending_fast_update = False
                return

            if prefs and prefs.animassist_fast_offset and not self._pending_fast_update:
                return

            self._pending_fast_update = False
            mask = self._build_mask(context)

            any_changed = False
            for i, fc in enumerate(self._fcurves):
                live_val = _key_value_at_frame(fc, cur)
                if live_val is None:
                    live_val = fc.evaluate(cur)

                base_val = self._snap_frame.get(i, live_val)
                delta = live_val - base_val
                if abs(delta) < EPSILON:
                    continue

                orig_keys = self._snap_all.get(i, {})
                if mask.enabled:
                    new_vals = compute_propagated_values(orig_keys, delta, mask, cur)
                else:
                    new_vals = compute_propagated_values_full_range(orig_keys, delta, cur)

                for kp in fc.keyframe_points:
                    frame = kp.co[0]
                    if frame in new_vals:
                        # Carry the handles by the actual incremental change.
                        # The keyed edit may already have moved its own handles.
                        dy = new_vals[frame] - kp.co[1]
                        left_y, right_y = kp.handle_left.y, kp.handle_right.y
                        kp.co[1] = new_vals[frame]
                        kp.handle_left.y = left_y + dy
                        kp.handle_right.y = right_y + dy

                # optional autokey outside mask
                if prefs and prefs.animassist_autokey_outside_margins and mask.enabled:
                    outside = frames_outside_mask(list(orig_keys.keys()), mask)
                    for fr in outside:
                        if not _has_key_at_frame(fc, fr):
                            fc.keyframe_points.insert(fr, fc.evaluate(fr), options={"FAST"})

                fc.update()
                any_changed = True

            if any_changed and context.area:
                context.area.tag_redraw()
        finally:
            self._propagating = False

    def _restore_all(self) -> None:
        _restore_cancel_snapshot(self._fcurves, self._snap_cancel)

    def _cleanup(self, context: bpy.types.Context) -> None:
        context.scene.anim_assist.anim_offset_active = False
        _sessions.pop(self._scene.as_pointer(), None)
        if context.workspace:
            context.workspace.status_text_set(None)
        if hasattr(self, "_timer") and self._timer is not None:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None
        self._fcurves = []
        self._snap_all = {}
        self._snap_cancel = []
        self._snap_frame = {}


class ANIMASSIST_OT_anim_offset_set_range(Operator):
    bl_idname = "animassist.anim_offset_set_range"
    bl_label = "Set Offset Range"
    bl_description = "Set the start and end frames of the Anim Offset mask"
    bl_options = {"REGISTER", "UNDO"}

    start: FloatProperty(name="Start", description="First frame of the offset mask", default=1.0)  # type: ignore[assignment]
    end: FloatProperty(name="End", description="Last frame of the offset mask", default=250.0)  # type: ignore[assignment]

    def execute(self, context: bpy.types.Context):
        # ACCESS_GATE_HERE
        m = context.scene.anim_assist.mask
        m.start_frame = int(self.start)
        m.end_frame = int(self.end)
        return {"FINISHED"}


class ANIMASSIST_OT_anim_offset_range_from_scene(Operator):
    bl_idname = "animassist.anim_offset_range_from_scene"
    bl_label = "Range from Scene"
    bl_description = "Copy the scene frame range into the Anim Offset mask"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context):
        # ACCESS_GATE_HERE
        sc = context.scene
        m = sc.anim_assist.mask
        m.start_frame = sc.frame_start
        m.end_frame = sc.frame_end
        return {"FINISHED"}


class ANIMASSIST_OT_anim_offset_toggle_mask(Operator):
    bl_idname = "animassist.anim_offset_toggle_mask"
    bl_label = "Toggle Mask"
    bl_description = "Enable or disable the Anim Offset frame mask"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context):
        # ACCESS_GATE_HERE
        m = context.scene.anim_assist.mask
        m.enabled = not m.enabled
        return {"FINISHED"}


classes: list[type] = [
    ANIMASSIST_OT_anim_offset,
    ANIMASSIST_OT_anim_offset_set_range,
    ANIMASSIST_OT_anim_offset_range_from_scene,
    ANIMASSIST_OT_anim_offset_toggle_mask,
]
