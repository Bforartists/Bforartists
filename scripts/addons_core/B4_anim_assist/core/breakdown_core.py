# --- BREAKDOWN AND INBETWEEN TOOLS ---
"""Core breakdown math, sampling, and write routines.

All breakdown operators delegate the *what to write* question to this
module. Operators themselves are thin shells that build a
:class:`BreakdownOptions`, resolve the target set, and call
:func:`apply_breakdown`.

Design notes
------------

* Nothing here imports from ``operators`` or ``ui`` so it is safe to use
  from any call site (modal preview, batch, preset apply).
* Every write honours ``scene.library`` / ``override_library`` and
  silently no-ops on linked read-only data.
* Quaternion rotation channels are written as a 4-tuple slerp so we
  never ship a broken half-rotation key.
* Tangent continuity is preserved by matching the new key's handle
  types to whichever neighbor is closer in frame.
"""

from __future__ import annotations

import contextlib
import math
from dataclasses import dataclass, field
from typing import Iterable

import bpy
from mathutils import Quaternion

from .breakdown_masks import BreakdownMask, ExclusionSet, apply_exclusion
from .fcurve_compat import get_fcurves
from .fcurve_utils import (
    get_bone_name_from_fcurve,
)
from .logging import get_logger

_log = get_logger(__name__)

__all__ = [
    "BreakdownOptions",
    "BreakdownResult",
    "nearest_bracket",
    "blend_linear",
    "blend_euler_wrap",
    "blend_quaternion",
    "iter_target_fcurves",
    "apply_breakdown",
    "remember_last",
    "get_last",
    "MODE_REPLACE",
    "MODE_OFFSET",
    "MODE_PUSH_PREV",
    "MODE_PUSH_NEXT",
    "MODE_PULL_PREV",
    "MODE_PULL_NEXT",
    "SPACE_LOCAL",
    "SPACE_WORLD",
]


# ---------------------------------------------------------------------------
# Options
# ---------------------------------------------------------------------------

MODE_REPLACE = "REPLACE"
MODE_OFFSET = "OFFSET"
MODE_PUSH_PREV = "PUSH_PREV"
MODE_PUSH_NEXT = "PUSH_NEXT"
MODE_PULL_PREV = "PULL_PREV"
MODE_PULL_NEXT = "PULL_NEXT"

SPACE_LOCAL = "LOCAL"
SPACE_WORLD = "WORLD"


@dataclass
class BreakdownOptions:
    """Everything an operator needs to pass down to :func:`apply_breakdown`."""

    factor: float = 0.5
    mode: str = MODE_REPLACE
    mask: BreakdownMask = field(default_factory=BreakdownMask)
    exclusion: ExclusionSet | None = None
    space: str = SPACE_LOCAL
    visual_transform: bool = False
    quaternion_aware: bool = True
    euler_wrap_aware: bool = True
    preserve_world_contact: bool = False
    preserve_child_contact: bool = False
    match_tangents: bool = True
    auto_key_missing: bool = False
    target_frame: float | None = None  # None = scene.frame_current_final
    offset_amount: float = 0.0            # used for MODE_OFFSET
    push_strength: float = 1.25           # used for PUSH_*
    pull_strength: float = 0.75           # used for PULL_*


@dataclass
class BreakdownResult:
    """Results summary from a breakdown operation."""

    keys_written: int = 0
    fcurves_touched: int = 0
    skipped_locked: int = 0
    skipped_exclusion: int = 0
    skipped_empty: int = 0
    messages: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Frame / scene helpers
# ---------------------------------------------------------------------------

@contextlib.contextmanager
def _preserve_frame(scene: bpy.types.Scene):
    """Save and restore the scene frame, preserving sub-frame precision."""
    original = float(scene.frame_current_final)
    int_part = int(original)
    sub_part = original - int_part
    try:
        yield
    finally:
        # ``scene.frame_set`` supports a fractional ``subframe`` kwarg so we
        # never truncate the animator's current sub-frame position.
        try:
            scene.frame_set(int_part, subframe=sub_part)
        except TypeError:  # pragma: no cover — very old Blender fallback
            scene.frame_set(int_part)


def _scene_writable(scene: bpy.types.Scene) -> bool:
    return scene.library is None or scene.override_library is not None


# ---------------------------------------------------------------------------
# Neighbor resolution
# ---------------------------------------------------------------------------

def nearest_bracket(
    fcurve: bpy.types.FCurve,
    frame: float,
) -> tuple[tuple[float, float] | None, tuple[float, float] | None]:
    """Return ``(prev_key, next_key)`` bracketing ``frame`` or ``None`` ends.

    Ties (existing key on ``frame``) treat the matching key as the
    *previous* neighbor so a fresh midpoint of a stable pose stays put.
    """
    prev_kp = None
    next_kp = None
    for kp in fcurve.keyframe_points:
        f = float(kp.co[0])
        v = float(kp.co[1])
        if f <= frame:
            if prev_kp is None or f > prev_kp[0]:
                prev_kp = (f, v)
        elif f > frame:
            if next_kp is None or f < next_kp[0]:
                next_kp = (f, v)
    return prev_kp, next_kp


# ---------------------------------------------------------------------------
# Blending primitives
# ---------------------------------------------------------------------------

def _linear_blend(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def blend_linear(
    prev_val: float,
    next_val: float,
    t: float,
    mode: str,
    push_strength: float,
    pull_strength: float,
) -> float:
    """Blend a scalar channel between two keyframe values in the requested mode.

    Handles REPLACE, PUSH_PREV, PUSH_NEXT, PULL_PREV, and PULL_NEXT for
    location, scale, and Euler rotation channels. Returns the scalar value
    to be written to the FCurve.
    """
    if mode == MODE_REPLACE:
        return _linear_blend(prev_val, next_val, t)
    if mode == MODE_PUSH_PREV:
        return prev_val - (next_val - prev_val) * (push_strength - 1.0)
    if mode == MODE_PUSH_NEXT:
        return next_val + (next_val - prev_val) * (push_strength - 1.0)
    if mode == MODE_PULL_PREV:
        return _linear_blend(prev_val, next_val, max(0.0, min(1.0, 1.0 - pull_strength)))
    if mode == MODE_PULL_NEXT:
        return _linear_blend(prev_val, next_val, max(0.0, min(1.0, pull_strength)))
    # OFFSET handled at a higher layer (needs current value).
    return _linear_blend(prev_val, next_val, t)


def blend_euler_wrap(prev_val: float, next_val: float, t: float) -> float:
    """Shortest-path euler blend (picks the <=π arc)."""
    diff = next_val - prev_val
    if diff > math.pi:
        next_val -= 2.0 * math.pi
    elif diff < -math.pi:
        next_val += 2.0 * math.pi
    return _linear_blend(prev_val, next_val, t)


def blend_quaternion(
    prev_q: tuple[float, float, float, float],
    next_q: tuple[float, float, float, float],
    t: float,
) -> tuple[float, float, float, float]:
    """Spherically interpolate two quaternions along the shortest path.

    Ensures rotation blending avoids gimbal flips by using SLERP and
    normalizing both quaternions. Returns (w, x, y, z) ready for writing
    to rotation_quaternion FCurves.
    """
    q1 = Quaternion(prev_q).normalized()
    q2 = Quaternion(next_q).normalized()
    # Ensure shortest path.
    if q1.dot(q2) < 0.0:
        q2 = Quaternion((-q2.w, -q2.x, -q2.y, -q2.z))
    out = q1.slerp(q2, max(0.0, min(1.0, t)))
    return (out.w, out.x, out.y, out.z)


# ---------------------------------------------------------------------------
# Key writing
# ---------------------------------------------------------------------------

def _write_key(
    fcurve: bpy.types.FCurve,
    frame: float,
    value: float,
    *,
    match_tangents: bool,
) -> bpy.types.Keyframe | None:
    # Bracket BEFORE inserting: afterwards the new key is its own nearest
    # neighbour and match_tangents would copy its own default handle type.
    prev_kp, next_kp = nearest_bracket(fcurve, frame) if match_tangents else (None, None)
    # No NEEDED flag: a breakdown key is wanted even when it lands exactly on
    # the evaluated curve (common on LINEAR segments); NEEDED silently skips it.
    kp = fcurve.keyframe_points.insert(frame, value, options={"FAST"})
    # Blender 4.x: insert() with the NEEDED flag returns None when the value
    # matched an existing key and no new key was inserted. Recover the existing
    # keyframe at this frame so callers (and attribute access below) stay safe.
    if kp is None:
        for existing in fcurve.keyframe_points:
            if math.isclose(float(existing.co[0]), float(frame)):
                kp = existing
                break
        if kp is None:
            # Nothing to touch; bail out rather than raise.
            return None
    if match_tangents:
        # Match tangent type to the closer neighbor for continuity.
        ref_handle = "AUTO_CLAMPED"
        if prev_kp is not None and next_kp is not None:
            prev_dist = frame - prev_kp[0]
            next_dist = next_kp[0] - frame
            # Try to copy handle type from whichever existing key is closer.
            ref_kp = None
            for existing in fcurve.keyframe_points:
                ef = float(existing.co[0])
                if math.isclose(ef, prev_kp[0]) and prev_dist <= next_dist:
                    ref_kp = existing
                    break
                if math.isclose(ef, next_kp[0]) and prev_dist > next_dist:
                    ref_kp = existing
                    break
            if ref_kp is not None:
                ref_handle = ref_kp.handle_left_type
        kp.handle_left_type = ref_handle
        kp.handle_right_type = ref_handle
    return kp


# ---------------------------------------------------------------------------
# FCurve enumeration
# ---------------------------------------------------------------------------

def iter_target_fcurves(
    obj: bpy.types.Object,
    bone_names: Iterable[str] | None,
    mask: BreakdownMask,
    exclusion: ExclusionSet | None,
) -> list[bpy.types.FCurve]:
    """Filter an object's FCurves to those matching selected bones and exclusion rules.

    Restricts to bone_names (if supplied), applies the exclusion set, and
    filters by the breakdown mask (channel type and axis). Returns an empty
    list if the object has no action.
    """
    adata = getattr(obj, "animation_data", None)
    if adata is None or adata.action is None:
        return []
    fcurves = get_fcurves(adata.action, anim_data=adata)

    if bone_names is not None:
        bone_set = set(bone_names)
        fcurves = [
            fc for fc in fcurves
            if (get_bone_name_from_fcurve(fc) or "") in bone_set
        ]

    fcurves = apply_exclusion(fcurves, exclusion)
    fcurves = [fc for fc in fcurves if mask.allows_fcurve(fc)]
    return fcurves


# ---------------------------------------------------------------------------
# Quaternion grouping
# ---------------------------------------------------------------------------

def _group_quaternions(
    fcurves: list[bpy.types.FCurve],
) -> dict[str, list[bpy.types.FCurve]]:
    groups: dict[str, list[bpy.types.FCurve]] = {}
    for fc in fcurves:
        if "rotation_quaternion" not in fc.data_path:
            continue
        base = fc.data_path
        groups.setdefault(base, []).append(fc)
    return groups


# ---------------------------------------------------------------------------
# Quaternion processing helper (flattened from deeply nested loop)
# ---------------------------------------------------------------------------

def _process_quaternion_group(
    group: list[bpy.types.FCurve],
    frame: float,
    options: BreakdownOptions,
    touched: set[int],
    result: BreakdownResult,
    visual_samples: dict[int, float],
) -> None:
    """Process a single quaternion rotation group and write blended values.

    Extracted to reduce nesting depth in the main loop.
    """
    if not group:
        return

    # Build prev/next tuples component-wise.
    prev_q = [0.0, 0.0, 0.0, 0.0]
    next_q = [0.0, 0.0, 0.0, 0.0]
    have_any_neighbour = False

    for fc in group:
        idx = int(fc.array_index)
        p, n = nearest_bracket(fc, frame)
        if p is None and n is None:
            try:
                prev_q[idx] = float(fc.evaluate(frame))
                next_q[idx] = prev_q[idx]
            except Exception:
                # Fallback to default quaternion identity if evaluation fails.
                _log.debug(
                    "Failed to evaluate quaternion component %d; using identity",
                    idx,
                    exc_info=True,
                )
                prev_q[idx] = 0.0 if idx != 0 else 1.0
                next_q[idx] = prev_q[idx]
            continue
        have_any_neighbour = True
        if p is None:
            try:
                prev_q[idx] = float(fc.evaluate(frame))
            except Exception:
                # Fall back to next keyframe value if evaluation fails.
                _log.debug(
                    "Failed to evaluate prev quaternion component %d",
                    idx,
                    exc_info=True,
                )
                prev_q[idx] = n[1]
        else:
            prev_q[idx] = p[1]
        if n is None:
            try:
                next_q[idx] = float(fc.evaluate(frame))
            except Exception:
                # Fall back to prev keyframe value if evaluation fails.
                _log.debug("Failed to evaluate next quaternion component %d", idx, exc_info=True)
                next_q[idx] = p[1]
        else:
            next_q[idx] = n[1]

    if not have_any_neighbour and not options.auto_key_missing:
        for fc in group:
            result.skipped_empty += 1
        return

    # Compute blended values by component.
    if options.quaternion_aware:
        blended_tuple = blend_quaternion(
            (prev_q[0], prev_q[1], prev_q[2], prev_q[3]),
            (next_q[0], next_q[1], next_q[2], next_q[3]),
            options.factor,
        )
        # blend_quaternion returns (w, x, y, z) matching array
        # indices 0..3 of rotation_quaternion fcurves.
        blended_by_idx = {
            0: blended_tuple[0],
            1: blended_tuple[1],
            2: blended_tuple[2],
            3: blended_tuple[3],
        }
    else:
        blended_by_idx = {
            idx: blend_linear(
                prev_q[idx], next_q[idx], options.factor,
                options.mode, options.push_strength,
                options.pull_strength,
            )
            for idx in range(4)
        }

    # Write blended values to each fcurve in the group.
    for fc in group:
        idx = int(fc.array_index)
        comp_value = float(blended_by_idx.get(idx, 0.0))
        if options.visual_transform and id(fc) in visual_samples:
            comp_value = visual_samples[id(fc)]
        if options.mode == MODE_OFFSET:
            try:
                current = float(fc.evaluate(frame))
            except Exception:
                # Fall back to computed value if current evaluation fails.
                _log.debug(
                    "Failed to evaluate current value for quaternion OFFSET; "
                    "using computed",
                    exc_info=True,
                )
                current = comp_value
            comp_value = current + options.offset_amount
        if _write_key(
            fc,
            frame,
            comp_value,
            match_tangents=options.match_tangents,
        ) is not None:
            result.keys_written += 1
        touched.add(id(fc))


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def apply_breakdown(
    context: bpy.types.Context,
    obj: bpy.types.Object,
    bone_names: Iterable[str] | None,
    options: BreakdownOptions,
    *,
    frames: Iterable[float] | None = None,
) -> BreakdownResult:
    """Run a breakdown across ``obj`` for one or more frames.

    ``frames`` defaults to ``[options.target_frame or scene frame]``.
    """
    scene = context.scene
    result = BreakdownResult()

    if not _scene_writable(scene):
        result.messages.append("Scene is linked and read-only; skipped.")
        return result

    adata = getattr(obj, "animation_data", None)
    if adata is None or adata.action is None:
        result.messages.append(f"{obj.name}: no action to write to.")
        return result

    target_fcurves = iter_target_fcurves(
        obj, bone_names, options.mask, options.exclusion
    )
    if not target_fcurves:
        result.messages.append("No fcurves matched the current mask.")
        return result

    quat_groups = _group_quaternions(target_fcurves)
    # Quaternion channels are always handled by the quat loop below,
    # regardless of ``quaternion_aware``. When that flag is off we fall
    # back to per-component linear blending instead of a true slerp so
    # rotation channels are never silently dropped.
    scalar_fcurves = [
        fc for fc in target_fcurves
        if "rotation_quaternion" not in fc.data_path
    ]

    if frames is None:
        base_frame = (
            options.target_frame
            if options.target_frame is not None
            else float(scene.frame_current_final)
        )
        frame_list = [base_frame]
    else:
        frame_list = [float(f) for f in frames]

    touched: set[int] = set()

    # ------------------------------------------------------------------
    # Optional visual-transform sampling helper.
    #
    # Instead of calling ``scene.frame_set`` inside the per-fcurve loop
    # (which would trigger one depsgraph re-eval per channel), we build
    # a single dict of evaluated values per target frame by jumping the
    # scene to that frame once, sampling every target fcurve, and then
    # restoring the original frame via the ``_preserve_frame`` context
    # manager (which now keeps sub-frame precision).
    # ------------------------------------------------------------------
    def _sample_visual_values(target_frame: float) -> dict[int, float]:
        samples: dict[int, float] = {}
        with _preserve_frame(scene):
            try:
                scene.frame_set(
                    int(target_frame),
                    subframe=target_frame - int(target_frame),
                )
            except TypeError:  # pragma: no cover
                scene.frame_set(int(round(target_frame)))
            depsgraph = context.evaluated_depsgraph_get()
            obj_eval = obj.evaluated_get(depsgraph) if depsgraph else obj
            eval_adata = getattr(obj_eval, "animation_data", None)
            eval_action = (
                eval_adata.action if eval_adata is not None else None
            )
            if eval_action is None:
                eval_action = adata.action
            # Map by (data_path, array_index) so we can look up originals.
            eval_index: dict[tuple[str, int], bpy.types.FCurve] = {
                (fc.data_path, int(fc.array_index)): fc
                for fc in get_fcurves(eval_action)
            }
            for fc in target_fcurves:
                key = (fc.data_path, int(fc.array_index))
                ev_fc = eval_index.get(key, fc)
                try:
                    samples[id(fc)] = float(ev_fc.evaluate(target_frame))
                except Exception:
                    # Fall back to unevaluated fcurve if evaluated version fails.
                    _log.debug(
                        "Failed to evaluate visual sample for %s",
                        fc.data_path,
                        exc_info=True,
                    )
                    try:
                        samples[id(fc)] = float(fc.evaluate(target_frame))
                    except Exception:
                        # Cannot sample this fcurve; skip it; caller will handle gracefully.
                        _log.debug(
                            "Fallback evaluation also failed for %s",
                            fc.data_path,
                            exc_info=True,
                        )
                        continue
        return samples

    for frame in frame_list:
        visual_samples: dict[int, float] = (
            _sample_visual_values(frame) if options.visual_transform else {}
        )

        # -- Scalar channels -------------------------------------------------
        for fc in scalar_fcurves:
            prev_kp, next_kp = nearest_bracket(fc, frame)
            if prev_kp is None and next_kp is None:
                result.skipped_empty += 1
                if options.auto_key_missing:
                    # Auto-key with the evaluated current value so the
                    # fcurve gains an anchor we can blend off next time.
                    try:
                        eval_val = float(fc.evaluate(frame))
                    except Exception:
                        # Cannot sample; skip this empty fcurve.
                        _log.debug(
                            "Failed to evaluate empty fcurve %s for auto-key",
                            fc.data_path,
                            exc_info=True,
                        )
                        continue
                    if _write_key(
                        fc,
                        frame,
                        eval_val,
                        match_tangents=options.match_tangents,
                    ) is not None:
                        result.keys_written += 1
                    touched.add(id(fc))
                continue

            # Base blended value first.
            if prev_kp is None:
                value = next_kp[1]
            elif next_kp is None:
                value = prev_kp[1]
            else:
                pv, nv = prev_kp[1], next_kp[1]
                is_euler = "rotation_euler" in fc.data_path
                if is_euler and options.euler_wrap_aware:
                    value = blend_euler_wrap(pv, nv, options.factor)
                else:
                    value = blend_linear(
                        pv, nv, options.factor, options.mode,
                        options.push_strength, options.pull_strength,
                    )

            # Visual transform overrides the pure blend with the
            # depsgraph-evaluated value sampled once per frame above.
            if options.visual_transform and id(fc) in visual_samples:
                value = visual_samples[id(fc)]

            # OFFSET mode works regardless of neighbour availability.
            if options.mode == MODE_OFFSET:
                try:
                    current = float(fc.evaluate(frame))
                except Exception:
                    # Fall back to blended value if current evaluation fails.
                    _log.debug(
                        "Failed to evaluate current for scalar OFFSET; "
                        "using blended",
                        exc_info=True,
                    )
                    current = float(value)
                value = current + options.offset_amount

            if _write_key(
                fc, frame, float(value),
                match_tangents=options.match_tangents,
            ) is not None:
                result.keys_written += 1
            touched.add(id(fc))

        # -- Quaternion groups ----------------------------------------------
        # Always iterate quaternion groups so rotation channels are never
        # silently skipped when ``quaternion_aware`` is disabled.
        for _, group in quat_groups.items():
            _process_quaternion_group(
                group,
                frame,
                options,
                touched,
                result,
                visual_samples,
            )

    for fc in target_fcurves:
        try:
            fc.update()
        except Exception:  # pragma: no cover — defensive
            # FCurve.update() can raise on orphaned data; safe to skip.
            _log.debug("FCurve.update() failed; fcurve may be orphaned", exc_info=True)

    result.fcurves_touched = len(touched)
    result.messages.append(
        f"Wrote {result.keys_written} key(s) across "
        f"{result.fcurves_touched} fcurve(s)."
    )
    return result


# ---------------------------------------------------------------------------
# Repeat-last memory (used by Feature 42)
# ---------------------------------------------------------------------------

_LAST_OPTIONS: BreakdownOptions | None = None


def remember_last(options: BreakdownOptions) -> None:
    """Store ``options`` as the most recent breakdown request."""
    global _LAST_OPTIONS
    _LAST_OPTIONS = options


def get_last() -> BreakdownOptions | None:
    """Return the most recent breakdown options, or *None* if none has run."""
    return _LAST_OPTIONS
