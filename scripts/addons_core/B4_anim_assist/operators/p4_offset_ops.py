# --- OFFSET TOOLS ---
"""Offset operators.

Core pipeline:

1. ``_resolve_options`` — pull defaults from the PropertyGroup
   into a lightweight namespace so the pipeline doesn't need Blender
   RNA access after this point.
2. ``_resolve_frames`` — decide which frames get written based on scope.
3. ``_run_offset`` — for each target, for each frame, compute the
   weighted + rebased delta and write the new T/R/S values to the
   matching fcurves.
4. ``_commit`` — call ``fc.update()``, tag redraws, remember the
   operation for Reapply/Invert Last.

All the axis-filter and push/pull variants share this same pipeline
through a thin wrapper so the logic lives in exactly one place.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import bpy

try:
    from mathutils import Vector, Quaternion, Euler
except Exception:  # pragma: no cover
    Vector = Quaternion = Euler = None  # type: ignore[assignment]

from ..core import p4_offset_math as om
from ..core import p4_falloff as fo
from ..core import p4_mirror as mr
from ..core import p4_presets as pr
from ..core import p4_space as sp
from ..core import p4_targets as tg
from ..core.p4_properties import get_p4


# ---------------------------------------------------------------------------
# Options snapshot
# ---------------------------------------------------------------------------

@dataclass
class _OffsetOptions:
    translate: tuple[float, float, float]
    rotate: tuple[float, float, float]
    scale: tuple[float, float, float]
    channel_mask: str
    scope: str
    selected_channels_only: bool
    keyed_channels_only: bool
    skip_locked: bool
    skip_muted: bool
    auto_key_missing: bool
    range_start: float
    range_end: float
    falloff_shape: str
    space: str
    pivot_mode: str
    preserve_contact_axis: str
    mirror_sign_enabled: bool
    mirror_axis: str
    fine_step: bool
    preset_multiplier: float


def _resolve_options(
    context: bpy.types.Context,
    *,
    channel_mask_override: Optional[str] = None,
    scope_override: Optional[str] = None,
    push_axis: Optional[str] = None,
    push_sign: float = 0.0,
) -> Optional[_OffsetOptions]:
    p4 = get_p4(context)
    if p4 is None:
        return None

    preset = pr.preset_by_id(p4.active_preset)
    preset_mul = preset.multiplier if preset is not None else 1.0

    if push_axis is not None:
        mag = abs(float(p4.push_amount)) * float(push_sign)
        tx = mag if push_axis == "X" else 0.0
        ty = mag if push_axis == "Y" else 0.0
        tz = mag if push_axis == "Z" else 0.0
        translate = (tx, ty, tz)
        rotate = (0.0, 0.0, 0.0)
        scale = (0.0, 0.0, 0.0)
    else:
        translate = tuple(p4.translate_amount)
        rotate = tuple(p4.rotate_amount)
        scale = tuple(p4.scale_amount)

    return _OffsetOptions(
        translate=translate,
        rotate=rotate,
        scale=scale,
        channel_mask=channel_mask_override or p4.channel_mask,
        scope=scope_override or p4.scope,
        selected_channels_only=bool(p4.selected_channels_only),
        keyed_channels_only=bool(p4.keyed_channels_only),
        skip_locked=bool(p4.skip_locked),
        skip_muted=bool(p4.skip_muted),
        auto_key_missing=bool(p4.auto_key_missing),
        range_start=float(p4.range_start),
        range_end=float(p4.range_end),
        falloff_shape=str(p4.falloff_shape),
        space=str(p4.space),
        pivot_mode=str(p4.pivot_mode),
        preserve_contact_axis=str(p4.preserve_contact_axis),
        mirror_sign_enabled=bool(p4.mirror_sign_enabled),
        mirror_axis=str(p4.mirror_axis),
        fine_step=bool(p4.fine_step),
        preset_multiplier=preset_mul,
    )


# ---------------------------------------------------------------------------
# Frame resolution
# ---------------------------------------------------------------------------

def _frames_from_scope(
    context: bpy.types.Context,
    opts: _OffsetOptions,
    targets: list[tg.OffsetTarget],
    action: bpy.types.Action,
) -> list[float]:
    if opts.scope == "CURRENT_FRAME":
        return [float(context.scene.frame_current_final)]

    collected: set[float] = set()
    if opts.scope == "SELECTED_KEYS":
        for target in targets:
            for fc in tg.iter_target_fcurves(
                target,
                action,
                channel_mask=opts.channel_mask,
                skip_locked=opts.skip_locked,
                skip_muted=opts.skip_muted,
                keyed_only=True,
                selected_only=True,
            ):
                for kp in fc.keyframe_points:
                    if kp.select_control_point:
                        collected.add(round(float(kp.co.x), 6))
        return sorted(collected)

    if opts.scope == "FRAME_RANGE":
        start = min(opts.range_start, opts.range_end)
        end = max(opts.range_start, opts.range_end)
        for target in targets:
            for fc in tg.iter_target_fcurves(
                target,
                action,
                channel_mask=opts.channel_mask,
                skip_locked=opts.skip_locked,
                skip_muted=opts.skip_muted,
                keyed_only=True,
                selected_only=False,
            ):
                for kp in fc.keyframe_points:
                    f = float(kp.co.x)
                    if start - 1e-6 <= f <= end + 1e-6:
                        collected.add(round(f, 6))
        return sorted(collected)

    return []


# ---------------------------------------------------------------------------
# Write helpers
# ---------------------------------------------------------------------------

def _sample_base_at(fc: bpy.types.FCurve, frame: float) -> float:
    """Return the fcurve value at ``frame`` without changing scene state."""
    try:
        return float(fc.evaluate(frame))
    except Exception:
        return 0.0


def _insert_or_update(
    fc: bpy.types.FCurve,
    frame: float,
    new_value: float,
    *,
    auto_key_missing: bool,
) -> bool:
    """Write ``new_value`` at ``frame``. Returns True if a key was touched."""
    kps = fc.keyframe_points
    for kp in kps:
        if abs(kp.co.x - frame) < 1e-4:
            # Preserve handle offsets relative to the key value so
            # tangent shapes survive the offset write.  R1 audit fix.
            delta_y = new_value - kp.co.y
            kp.co.y = new_value
            kp.handle_left.y += delta_y
            kp.handle_right.y += delta_y
            return True
    if auto_key_missing:
        kps.insert(frame, new_value, options={"NEEDED", "FAST"})
        return True
    return False


def _apply_scalar_offset(
    fc: bpy.types.FCurve,
    frame: float,
    delta: float,
    *,
    auto_key_missing: bool,
) -> bool:
    base = _sample_base_at(fc, frame)
    return _insert_or_update(
        fc, frame, base + delta,
        auto_key_missing=auto_key_missing,
    )


def _apply_quat_offset(
    fcs_by_index: dict[int, bpy.types.FCurve],
    frame: float,
    q_delta,
    *,
    local_compose: bool,
    auto_key_missing: bool,
) -> int:
    """Apply a quaternion delta to all four components of a quaternion group."""
    if Quaternion is None:
        return 0
    w = _sample_base_at(fcs_by_index.get(0), frame) if 0 in fcs_by_index else 1.0
    x = _sample_base_at(fcs_by_index.get(1), frame) if 1 in fcs_by_index else 0.0
    y = _sample_base_at(fcs_by_index.get(2), frame) if 2 in fcs_by_index else 0.0
    z = _sample_base_at(fcs_by_index.get(3), frame) if 3 in fcs_by_index else 0.0
    q_base = Quaternion((w, x, y, z))
    try:
        q_base.normalize()
    except Exception:
        pass
    if q_delta is None:
        q_new = q_base
    elif local_compose:
        q_new = q_base @ q_delta
    else:
        q_new = q_delta @ q_base
    touched = 0
    comps = (("w", 0, q_new.w), ("x", 1, q_new.x), ("y", 2, q_new.y), ("z", 3, q_new.z))
    for _label, idx, val in comps:
        fc = fcs_by_index.get(idx)
        if fc is None:
            continue
        if _insert_or_update(fc, frame, float(val),
                             auto_key_missing=auto_key_missing):
            touched += 1
    return touched


# ---------------------------------------------------------------------------
# Core offset runner
# ---------------------------------------------------------------------------

def _run_offset(
    context: bpy.types.Context,
    opts: _OffsetOptions,
    targets: list[tg.OffsetTarget],
    action: bpy.types.Action,
    frames: list[float],
) -> tuple[int, int, list[str]]:
    """Run the offset pipeline. Returns (frames_written, channels_written, warnings)."""
    warnings: list[str] = []
    touched_channels = 0
    touched_frames = 0

    if not frames:
        return (0, 0, ["No frames matched the current scope."])

    # Build the master delta once (independent of frame / target).
    master = om.build_delta(
        translation=opts.translate,
        rotation_euler=opts.rotate,
        scale=opts.scale,
        channel_mask=opts.channel_mask,
        fine_step=opts.fine_step,
        multiplier=opts.preset_multiplier,
    )
    master = master.masked_for_axis(opts.preserve_contact_axis)

    if master.is_zero():
        return (0, 0, ["Offset delta is zero — nothing to do."])

    # Resolve per-frame weights once per frame.
    window_start, window_end = fo.window_bounds(
        opts.range_start if opts.scope == "FRAME_RANGE" else None,
        opts.range_end if opts.scope == "FRAME_RANGE" else None,
        frames,
    )

    # Cache a "did we already warn about gimbal fallback" flag.
    gimbal_fallback_warned = False

    scene = context.scene
    original_frame = scene.frame_current_final

    # R6 audit fix: pre-build per-target fcurve buckets ONCE, outside the
    # frame loop.  Previously ``iter_target_fcurves`` was called T×F times
    # (targets × frames); now it is called T times.
    _TargetBucket = tuple[
        "tg.OffsetTarget",
        int,   # mirror sign
        str,   # effective_space
        dict,  # loc_fcs
        dict,  # rot_euler_fcs
        dict,  # rot_quat_fcs
        dict,  # scale_fcs
    ]
    target_buckets: list[_TargetBucket] = []

    for target in targets:
        fcs = list(
            tg.iter_target_fcurves(
                target,
                action,
                channel_mask=opts.channel_mask,
                skip_locked=opts.skip_locked,
                skip_muted=opts.skip_muted,
                keyed_only=opts.keyed_channels_only,
                selected_only=opts.selected_channels_only,
            )
        )
        if not fcs:
            continue

        loc_fcs: dict[int, bpy.types.FCurve] = {}
        rot_euler_fcs: dict[int, bpy.types.FCurve] = {}
        rot_quat_fcs: dict[int, bpy.types.FCurve] = {}
        scale_fcs: dict[int, bpy.types.FCurve] = {}
        for fc in fcs:
            leaf = fc.data_path.rsplit(".", 1)[-1] if "." in fc.data_path else fc.data_path
            idx = fc.array_index
            if leaf == "location":
                loc_fcs[idx] = fc
            elif leaf == "rotation_euler":
                rot_euler_fcs[idx] = fc
            elif leaf == "rotation_quaternion":
                rot_quat_fcs[idx] = fc
            elif leaf == "scale":
                scale_fcs[idx] = fc

        # Mirror sign (frame-independent).
        if opts.mirror_sign_enabled:
            sign = mr.mirror_sign(target.display_name)
        else:
            sign = 1

        # Gimbal fallback for quaternion targets (frame-independent).
        effective_space = opts.space
        if effective_space == "GIMBAL" and target.rotation_mode == "QUATERNION":
            effective_space = "LOCAL"
            if not gimbal_fallback_warned:
                warnings.append(
                    "Gimbal space fell back to Local on quaternion targets."
                )
                gimbal_fallback_warned = True

        target_buckets.append((
            target, sign, effective_space,
            loc_fcs, rot_euler_fcs, rot_quat_fcs, scale_fcs,
        ))

    try:
        for frame in frames:
            weight = fo.falloff_weight(frame, window_start, window_end, opts.falloff_shape)
            if weight <= 0.0:
                continue

            any_write = False
            for (target, sign, effective_space,
                 loc_fcs, rot_euler_fcs, rot_quat_fcs, scale_fcs) in target_buckets:

                # Build per-target delta.
                per_target = master.scaled(weight)
                if sign == -1 and opts.mirror_axis in ("X", "Y", "Z"):
                    ax_idx = {"X": 0, "Y": 1, "Z": 2}[opts.mirror_axis]
                    t = list(per_target.translation)
                    t[ax_idx] = -t[ax_idx]
                    r = list(per_target.rotation_euler)
                    r[ax_idx] = -r[ax_idx]
                    per_target = om.OffsetDelta(
                        translation=(t[0], t[1], t[2]),
                        rotation_euler=(r[0], r[1], r[2]),
                        scale=per_target.scale,
                        channel_mask=per_target.channel_mask,
                    )

                resolved = sp.delta_to_basis(target, per_target, effective_space)

                # Translation
                if "T" in opts.channel_mask and loc_fcs:
                    for axis_idx, delta_component in enumerate(resolved.translation):
                        fc = loc_fcs.get(axis_idx)
                        if fc is None:
                            continue
                        if _apply_scalar_offset(fc, frame, float(delta_component),
                                                auto_key_missing=opts.auto_key_missing):
                            touched_channels += 1
                            any_write = True

                # Rotation
                if "R" in opts.channel_mask:
                    # Euler path — treat each axis as a scalar delta.
                    if rot_euler_fcs:
                        # R4 audit fix: For LOCAL and GIMBAL the delta is
                        # already an euler aligned to the target's rotation
                        # order.  Pass it through directly instead of the
                        # lossy quat→euler round-trip that wraps large
                        # angles.  For WORLD/VISUAL/PARENT we still need the
                        # quat-rebased conversion.
                        if effective_space in ("LOCAL", "GIMBAL"):
                            euler_delta = per_target.rotation_euler
                        else:
                            q = resolved.rotation
                            if q is not None and Euler is not None:
                                try:
                                    e = q.to_euler(target.rotation_order or "XYZ")
                                    euler_delta = (float(e.x), float(e.y), float(e.z))
                                except Exception:
                                    euler_delta = (0.0, 0.0, 0.0)
                            else:
                                euler_delta = (0.0, 0.0, 0.0)
                        for axis_idx, dv in enumerate(euler_delta):
                            fc = rot_euler_fcs.get(axis_idx)
                            if fc is None:
                                continue
                            if _apply_scalar_offset(fc, frame, float(dv),
                                                    auto_key_missing=opts.auto_key_missing):
                                touched_channels += 1
                                any_write = True

                    # Quaternion path — compose as a quaternion.
                    if rot_quat_fcs:
                        local_compose = effective_space == "LOCAL"
                        written = _apply_quat_offset(
                            rot_quat_fcs, frame, resolved.rotation,
                            local_compose=local_compose,
                            auto_key_missing=opts.auto_key_missing,
                        )
                        if written:
                            touched_channels += written
                            any_write = True

                # Scale
                if "S" in opts.channel_mask and scale_fcs:
                    for axis_idx, delta_component in enumerate(resolved.scale):
                        fc = scale_fcs.get(axis_idx)
                        if fc is None:
                            continue
                        if _apply_scalar_offset(fc, frame, float(delta_component),
                                                auto_key_missing=opts.auto_key_missing):
                            touched_channels += 1
                            any_write = True

            # R7 audit fix: touched_frames now increments at the frame
            # level (outside the target loop), not inside it.
            if any_write:
                touched_frames += 1

    finally:
        # Restore the original scene frame in case the caller or a
        # downstream evaluator moved it. frame_current_final is float;
        # use the int form + subframe to preserve precision.
        try:
            int_part = int(original_frame)
            sub_part = float(original_frame) - float(int_part)
            try:
                scene.frame_set(int_part, subframe=sub_part)
            except TypeError:
                scene.frame_set(int_part)
        except Exception:
            pass

    # Flush fcurve updates (catches order / handle recomputation).
    for target in targets:
        for fc in tg.iter_target_fcurves(
            target,
            action,
            channel_mask=opts.channel_mask,
            skip_locked=opts.skip_locked,
            skip_muted=opts.skip_muted,
            keyed_only=False,
            selected_only=False,
        ):
            try:
                fc.update()
            except Exception:
                pass

    try:
        context.view_layer.update()
    except Exception:
        pass
    if context.area is not None:
        context.area.tag_redraw()

    return (touched_frames, touched_channels, warnings)


# ---------------------------------------------------------------------------
# Shared poll
# ---------------------------------------------------------------------------

def _valid_context(context: bpy.types.Context) -> bool:
    obj = getattr(context, "active_object", None)
    if obj is None:
        return False
    adata = getattr(obj, "animation_data", None)
    if adata is None or adata.action is None:
        return False
    return get_p4(context) is not None


# ---------------------------------------------------------------------------
# Operators
# ---------------------------------------------------------------------------

# R3 audit fix: _OffsetBase is a plain mixin, NOT a bpy.types.Operator
# subclass.  This avoids the registration landmine where Blender would
# attempt to register an abstract class without a bl_idname.  Concrete
# subclasses inherit from both this mixin and bpy.types.Operator.
class _OffsetBase:
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _valid_context(context)

    def _run(
        self,
        context: bpy.types.Context,
        *,
        channel_mask_override: Optional[str] = None,
        scope_override: Optional[str] = None,
        push_axis: Optional[str] = None,
        push_sign: float = 0.0,
    ) -> set[str]:
        opts = _resolve_options(
            context,
            channel_mask_override=channel_mask_override,
            scope_override=scope_override,
            push_axis=push_axis,
            push_sign=push_sign,
        )
        if opts is None:
            self.report({"WARNING"}, "Offset properties unavailable.")
            return {"CANCELLED"}

        targets = tg.resolve_targets(context, pivot_mode=opts.pivot_mode)
        if not targets:
            self.report({"INFO"}, "No targets selected.")
            return {"CANCELLED"}

        action = context.active_object.animation_data.action
        frames = _frames_from_scope(context, opts, targets, action)
        if not frames:
            self.report({"INFO"}, "No frames matched the current scope.")
            return {"CANCELLED"}

        written_frames, written_channels, warnings = _run_offset(
            context, opts, targets, action, frames,
        )

        for w in warnings:
            self.report({"WARNING"}, w)

        if written_channels == 0:
            self.report({"INFO"}, "Offset matched no writable channels.")
            return {"CANCELLED"}

        # Record for Reapply / Invert Last.
        delta = om.build_delta(
            translation=opts.translate,
            rotation_euler=opts.rotate,
            scale=opts.scale,
            channel_mask=opts.channel_mask,
            fine_step=opts.fine_step,
            multiplier=opts.preset_multiplier,
        )
        om.remember_last(
            om.LastOffsetRecord(
                delta=delta.masked_for_axis(opts.preserve_contact_axis),
                space=opts.space,
                pivot_mode=opts.pivot_mode,
                scope=opts.scope,
                falloff_shape=opts.falloff_shape,
            )
        )

        self.report(
            {"INFO"},
            f"Offset: {written_channels} channel writes across {written_frames} frames.",
        )
        return {"FINISHED"}


class AA_OT_p4_nudge_current(_OffsetBase, bpy.types.Operator):
    bl_idname = "animassist.p4_nudge_current"
    bl_label = "Nudge Current Frame"
    bl_description = (
        "Apply the current translate/rotate/scale deltas to every selected target at the current frame"
    )

    def execute(self, context):
        return self._run(context, scope_override="CURRENT_FRAME")


class AA_OT_p4_offset_selected(_OffsetBase, bpy.types.Operator):
    bl_idname = "animassist.p4_offset_selected"
    bl_label = "Offset Selected Keys"
    bl_description = (
        "Apply the current offset to every selected keyframe on the target channels"
    )

    def execute(self, context):
        return self._run(context, scope_override="SELECTED_KEYS")


class AA_OT_p4_offset_translate_only(_OffsetBase, bpy.types.Operator):
    bl_idname = "animassist.p4_offset_translate_only"
    bl_label = "Translation Only"
    bl_description = (
        "Applies only the translate delta at the current scope. Ignores rotate "
        "and scale amounts without modifying the scene properties."
    )

    def execute(self, context):
        return self._run(context, channel_mask_override="T")


class AA_OT_p4_offset_rotate_only(_OffsetBase, bpy.types.Operator):
    bl_idname = "animassist.p4_offset_rotate_only"
    bl_label = "Rotation Only"
    bl_description = (
        "Applies only the rotate delta at the current scope. Ignores translate "
        "and scale amounts without modifying the scene properties."
    )

    def execute(self, context):
        return self._run(context, channel_mask_override="R")


class AA_OT_p4_offset_scale_only(_OffsetBase, bpy.types.Operator):
    bl_idname = "animassist.p4_offset_scale_only"
    bl_label = "Scale Only"
    bl_description = (
        "Applies only the scale delta at the current scope. Ignores translate "
        "and rotate amounts without modifying the scene properties."
    )

    def execute(self, context):
        return self._run(context, channel_mask_override="S")


class AA_OT_p4_offset_trs_combined(_OffsetBase, bpy.types.Operator):
    bl_idname = "animassist.p4_offset_trs_combined"
    bl_label = "Combined TRS Offset"
    bl_description = (
        "Applies the translate, rotate, and scale deltas together in one pass. "
        "Writes land as a single undo step."
    )

    def execute(self, context):
        return self._run(context, channel_mask_override="TRS")


# ---------------------------------------------------------------------------
# Reapply / Invert / Preset
# ---------------------------------------------------------------------------

def _run_from_record(
    context: bpy.types.Context,
    record: om.LastOffsetRecord,
) -> tuple[int, int, list[str]]:
    opts = _resolve_options(context)
    if opts is None:
        return (0, 0, ["Offset properties unavailable."])

    # Replace the scene-derived amounts with the recorded delta — the
    # rest of the options (skip locked, channel filter, etc.) come from
    # the current scene state on purpose so the user can retarget.
    opts.translate = record.delta.translation
    opts.rotate = record.delta.rotation_euler
    opts.scale = record.delta.scale
    opts.channel_mask = record.delta.channel_mask
    opts.space = record.space
    opts.pivot_mode = record.pivot_mode
    opts.scope = record.scope
    opts.falloff_shape = record.falloff_shape
    # The delta is already scaled by preset / fine step, so neutralise them.
    opts.preset_multiplier = 1.0
    opts.fine_step = False

    targets = tg.resolve_targets(context, pivot_mode=opts.pivot_mode)
    if not targets:
        return (0, 0, ["No targets selected."])

    action = context.active_object.animation_data.action
    frames = _frames_from_scope(context, opts, targets, action)
    if not frames:
        return (0, 0, ["No frames matched the current scope."])

    return _run_offset(context, opts, targets, action, frames)


class AA_OT_p4_reapply_last(bpy.types.Operator):
    bl_idname = "animassist.p4_reapply_last"
    bl_label = "Reapply Last Offset"
    bl_description = (
        "Re-runs the most recent offset with identical amounts, space, pivot, "
        "scope, and falloff. Cancels if no offset has been run this session."
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _valid_context(context) and om.get_last() is not None

    def execute(self, context):
        record = om.get_last()
        if record is None:
            self.report({"INFO"}, "No previous offset to reapply.")
            return {"CANCELLED"}
        frames, channels, warnings = _run_from_record(context, record)
        for w in warnings:
            self.report({"WARNING"}, w)
        if channels == 0:
            return {"CANCELLED"}
        self.report({"INFO"}, f"Reapplied last offset: {channels} channels, {frames} frames.")
        return {"FINISHED"}


class AA_OT_p4_invert_last(bpy.types.Operator):
    bl_idname = "animassist.p4_invert_last"
    bl_label = "Invert Last Offset"
    bl_description = (
        "Re-run the last offset with every component negated"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _valid_context(context) and om.get_last() is not None

    def execute(self, context):
        record = om.get_last()
        if record is None:
            self.report({"INFO"}, "No previous offset to invert.")
            return {"CANCELLED"}
        inverted = record.as_inverted()
        frames, channels, warnings = _run_from_record(context, inverted)
        for w in warnings:
            self.report({"WARNING"}, w)
        if channels == 0:
            return {"CANCELLED"}
        # Remember the inverted record so a double-invert undoes itself.
        om.remember_last(inverted)
        self.report({"INFO"}, f"Inverted last offset: {channels} channels, {frames} frames.")
        return {"FINISHED"}


class AA_OT_p4_apply_preset(_OffsetBase, bpy.types.Operator):
    bl_idname = "animassist.p4_apply_preset"
    bl_label = "Apply Preset"
    bl_description = (
        "Applies the currently selected transform multiplier preset to the "
        "entered offset amounts and runs Nudge Current Frame."
    )

    def execute(self, context):
        return self._run(context, scope_override="CURRENT_FRAME")


CLASSES: tuple[type, ...] = (
    AA_OT_p4_nudge_current,
    AA_OT_p4_offset_selected,
    AA_OT_p4_offset_translate_only,
    AA_OT_p4_offset_rotate_only,
    AA_OT_p4_offset_scale_only,
    AA_OT_p4_offset_trs_combined,
    AA_OT_p4_reapply_last,
    AA_OT_p4_invert_last,
    AA_OT_p4_apply_preset,
)


# Expose the resolver and runner for the modal operator.
__all__ = [
    "CLASSES",
    "_resolve_options",
    "_frames_from_scope",
    "_run_offset",
    "_valid_context",
    "_OffsetOptions",
]
