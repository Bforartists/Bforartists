# --- RETIMING AND TIMING DIAGNOSTICS ---
"""Pure-Python retiming math — no bpy side-effects.

All functions operate on standard Python types (floats, lists, dicts) so they
can be unit-tested in isolation and called safely from modal operators without
triggering spurious undo pushes.

Anchor-mode constants intentionally mirror the ``p6_properties`` enum identifiers
so operators can pass ``p6.anchor_mode`` directly to :func:`resolve_pivot`.
"""

from __future__ import annotations

from .fcurve_compat import get_fcurves

__all__ = [
    "ANCHOR_FIRST",
    "ANCHOR_LAST",
    "ANCHOR_CURRENT",
    "ANCHOR_ACTIVE",
    "ANCHOR_CUSTOM",
    "resolve_pivot",
    "scale_frame",
    "offset_frame",
    "collect_key_frames",
    "backup_fcurves",
    "restore_fcurves",
    "apply_scale",
    "apply_offset",
    "apply_ripple",
    "reverse_keys_in_range",
    "distribute_keys",
    "snap_keys_to_frames",
    "remove_duplicate_frames",
    "bake_to_integer_frames",
    "resolve_active_range",
]


# ---------------------------------------------------------------------------
# Anchor mode string constants
# ---------------------------------------------------------------------------

ANCHOR_FIRST = "FIRST"
ANCHOR_LAST = "LAST"
ANCHOR_CURRENT = "CURRENT_FRAME"
ANCHOR_ACTIVE = "ACTIVE"
ANCHOR_CUSTOM = "CUSTOM"


# ---------------------------------------------------------------------------
# Pivot resolution
# ---------------------------------------------------------------------------

def resolve_pivot(
    anchor_mode: str,
    all_frames: list[float],
    current_frame: float,
    custom_frame: float = 0.0,
) -> float:
    """Return the pivot frame for a scale operation.

    Args:
        anchor_mode: One of the ANCHOR_* constants.
        all_frames: Sorted list of keyframe x values (may be empty).
        current_frame: The scene's current frame (playhead).
        custom_frame: User-specified pivot (used with ANCHOR_CUSTOM).

    Returns:
        Float pivot frame, falling back to *current_frame* when the list is
        empty or the mode is unrecognised.
    """
    if not all_frames:
        return current_frame

    if anchor_mode == ANCHOR_FIRST:
        return float(min(all_frames))
    if anchor_mode == ANCHOR_LAST:
        return float(max(all_frames))
    if anchor_mode == ANCHOR_ACTIVE:
        # "Active" key is resolved by the caller; we fall back to playhead.
        return current_frame
    if anchor_mode == ANCHOR_CUSTOM:
        return custom_frame

    # Default: CURRENT_FRAME
    return current_frame


# ---------------------------------------------------------------------------
# Per-frame math
# ---------------------------------------------------------------------------

def scale_frame(x: float, pivot: float, factor: float) -> float:
    """Scale a single frame around *pivot*.

    new_x = pivot + (old_x - pivot) * factor
    """
    return pivot + (x - pivot) * factor


def offset_frame(x: float, delta: float) -> float:
    """Shift a single frame by *delta*."""
    return x + delta


# ---------------------------------------------------------------------------
# FCurve helpers
# ---------------------------------------------------------------------------

def collect_key_frames(fcurves) -> list[float]:
    """Return sorted unique keyframe x values from all FCurves."""
    frames: set[float] = set()
    for fc in fcurves:
        for kp in fc.keyframe_points:
            frames.add(kp.co.x)
    return sorted(frames)


# ---------------------------------------------------------------------------
# Backup / restore (for modal undo support)
# ---------------------------------------------------------------------------

def backup_fcurves(fcurves) -> list[dict]:  # type: ignore[type-arg]
    """Snapshot all keyframe data for later restoration.

    Returns a list of per-FCurve dicts containing co, handle positions,
    handle types, interpolation, easing, and selection state.
    """
    result: list[dict] = []
    for fc in fcurves:
        keys: list[dict] = []
        for kp in fc.keyframe_points:
            keys.append({
                "co":      (kp.co.x, kp.co.y),
                "hl":      (kp.handle_left.x, kp.handle_left.y),
                "hr":      (kp.handle_right.x, kp.handle_right.y),
                "hl_type": kp.handle_left_type,
                "hr_type": kp.handle_right_type,
                "interp":  kp.interpolation,
                "easing":  kp.easing,
                "sel":     kp.select_control_point,
            })
        result.append({
            "data_path":   fc.data_path,
            "array_index": fc.array_index,
            "keys":        keys,
        })
    return result


def restore_fcurves(fcurves, backups: list[dict]) -> None:  # type: ignore[type-arg]
    """Restore FCurves from a snapshot produced by :func:`backup_fcurves`.

    The ``fcurves`` list must be in the same order as ``backups``.
    """
    for fc, backup in zip(fcurves, backups, strict=False):
        kps = fc.keyframe_points
        stored = backup["keys"]

        # Trim extra points.
        while len(kps) > len(stored):
            kps.remove(kps[-1])

        # Add missing points.
        while len(kps) < len(stored):
            entry = stored[len(kps)]
            kps.insert(entry["co"][0], entry["co"][1])

        # Apply stored state.
        for kp, sk in zip(kps, stored, strict=False):
            kp.co.x              = sk["co"][0]
            kp.co.y              = sk["co"][1]
            kp.handle_left.x     = sk["hl"][0]
            kp.handle_left.y     = sk["hl"][1]
            kp.handle_right.x    = sk["hr"][0]
            kp.handle_right.y    = sk["hr"][1]
            kp.handle_left_type  = sk["hl_type"]
            kp.handle_right_type = sk["hr_type"]
            kp.interpolation     = sk["interp"]
            kp.easing            = sk["easing"]
            kp.select_control_point = sk["sel"]

        fc.update()


# ---------------------------------------------------------------------------
# Bulk operations (mutate FCurves in-place)
# ---------------------------------------------------------------------------

def apply_scale(
    fcurves,
    pivot: float,
    factor: float,
    frame_range: tuple[float, float] | None = None,
    snap: bool = False,
) -> None:
    """Scale all keyframe times around *pivot* by *factor*.

    Args:
        fcurves: Iterable of ``bpy.types.FCurve``.
        pivot: Pivot frame.
        factor: Scale multiplier.
        frame_range: Optional ``(lo, hi)``; only keys within range are scaled.
        snap: If True, round resulting x values to integer frames.
    """
    for fc in fcurves:
        for kp in fc.keyframe_points:
            x = kp.co.x
            if frame_range is not None:
                lo, hi = frame_range
                if x < lo or x > hi:
                    continue
            new_x = scale_frame(x, pivot, factor)
            if snap:
                new_x = float(round(new_x))
            dx = new_x - x
            kp.co.x            = new_x
            kp.handle_left.x  += dx
            kp.handle_right.x += dx
        fc.update()


def apply_offset(
    fcurves,
    delta: float,
    frame_range: tuple[float, float] | None = None,
    snap: bool = False,
) -> None:
    """Shift all keyframe times by *delta* frames.

    Args:
        fcurves: Iterable of ``bpy.types.FCurve``.
        delta: Frame offset (positive = later, negative = earlier).
        frame_range: Optional ``(lo, hi)``; only keys within range are moved.
        snap: If True, round resulting x values to integer frames.
    """
    for fc in fcurves:
        for kp in fc.keyframe_points:
            x = kp.co.x
            if frame_range is not None:
                lo, hi = frame_range
                if x < lo or x > hi:
                    continue
            new_x = offset_frame(x, delta)
            if snap:
                new_x = float(round(new_x))
            dx = new_x - x
            kp.co.x            = new_x
            kp.handle_left.x  += dx
            kp.handle_right.x += dx
        fc.update()


def apply_ripple(
    fcurves,
    threshold_frame: float,
    delta: float,
    direction: str = "FORWARD",
    inclusive: bool = False,
    snap: bool = False,
) -> None:
    """Shift all keys on one side of *threshold_frame* by *delta*.

    direction:
        ``"FORWARD"``  — shift keys with x > threshold_frame.
        ``"BACKWARD"`` — shift keys with x < threshold_frame.

    inclusive:
        When True a key sitting exactly on *threshold_frame* is shifted too.
    """
    for fc in fcurves:
        for kp in fc.keyframe_points:
            x = kp.co.x
            if direction == "FORWARD"  and (x < threshold_frame if inclusive else x <= threshold_frame):
                continue
            if direction == "BACKWARD" and (x > threshold_frame if inclusive else x >= threshold_frame):
                continue
            new_x = x + delta
            if snap:
                new_x = float(round(new_x))
            dx = new_x - x
            kp.co.x            = new_x
            kp.handle_left.x  += dx
            kp.handle_right.x += dx
        fc.update()


def reverse_keys_in_range(
    fcurves,
    range_start: float,
    range_end: float,
) -> None:
    """Mirror keyframe timing within [range_start, range_end].

    New x = (range_start + range_end) - old_x.
    Values are untouched; only timing is mirrored.
    """
    total = range_start + range_end
    for fc in fcurves:
        for kp in fc.keyframe_points:
            x = kp.co.x
            if x < range_start or x > range_end:
                continue
            new_x = total - x
            dx = new_x - x
            kp.co.x            = new_x
            kp.handle_left.x  += dx
            kp.handle_right.x += dx
        fc.update()


def distribute_keys(
    fcurves,
    range_start: float,
    range_end: float,
    snap: bool = False,
) -> int:
    """Evenly distribute all keys within [range_start, range_end].

    Boundary keys are fixed; inner keys are re-spaced uniformly.
    Returns the number of keys repositioned.
    """
    # Unique sorted frames within range.
    frames_in_range = sorted({
        round(kp.co.x, 6)
        for fc in fcurves
        for kp in fc.keyframe_points
        if range_start <= kp.co.x <= range_end
    })
    n = len(frames_in_range)
    if n < 3:
        return 0  # Nothing to redistribute.

    span = range_end - range_start
    step = span / (n - 1)
    new_frames = {
        old: range_start + i * step
        for i, old in enumerate(frames_in_range)
    }
    if snap:
        new_frames = {k: float(round(v)) for k, v in new_frames.items()}

    moved = 0
    for fc in fcurves:
        for kp in fc.keyframe_points:
            x = round(kp.co.x, 6)
            if x not in new_frames:
                continue
            new_x = new_frames[x]
            dx = new_x - kp.co.x
            if abs(dx) > 1e-9:
                kp.co.x            = new_x
                kp.handle_left.x  += dx
                kp.handle_right.x += dx
                moved += 1
        fc.update()
    return moved


def snap_keys_to_frames(fcurves) -> int:
    """Round all keyframe x values to the nearest integer frame.

    Returns the count of keyframes that were moved.
    """
    moved = 0
    for fc in fcurves:
        for kp in fc.keyframe_points:
            ix = float(round(kp.co.x))
            if kp.co.x != ix:
                dx = ix - kp.co.x
                kp.co.x            = ix
                kp.handle_left.x  += dx
                kp.handle_right.x += dx
                moved += 1
        fc.update()
    return moved


def remove_duplicate_frames(fcurves, tolerance: float = 0.5) -> int:
    """Remove keyframes that share an integer-rounded x value.

    Keeps the *first* key encountered at each rounded frame; removes later
    duplicates. Returns the count of keys removed.
    """
    removed = 0
    for fc in fcurves:
        seen: set[int] = set()
        to_remove = []
        for kp in fc.keyframe_points:
            frame_key = round(kp.co.x)
            if frame_key in seen:
                to_remove.append(kp)
                removed += 1
            else:
                seen.add(frame_key)
        for kp in reversed(to_remove):
            fc.keyframe_points.remove(kp)
        if to_remove:
            fc.update()
    return removed


def bake_to_integer_frames(fcurves, snap: bool = True) -> int:
    """Alias for :func:`snap_keys_to_frames` used by the bake operator."""
    return snap_keys_to_frames(fcurves)


# ---------------------------------------------------------------------------
# Range resolution
# ---------------------------------------------------------------------------

def resolve_active_range(p6_props, context) -> tuple[float, float]:
    """Return ``(start, end)`` according to the ``p6_props.range_mode`` setting.

    Imports bpy here to keep this module importable without bpy in test runs.
    """
    mode = getattr(p6_props, "range_mode", "SCENE")
    if mode == "CUSTOM":
        return float(p6_props.range_start), float(p6_props.range_end)

    scene = getattr(context, "scene", None)
    if scene is None:
        return 1.0, 100.0

    if mode == "SELECTION":
        # Gather frames from selected keypoints in the active action.
        obj = getattr(context, "active_object", None)
        adata = getattr(obj, "animation_data", None) if obj else None
        action = getattr(adata, "action", None) if adata else None
        if action is not None:
            sel_frames = [
                kp.co.x
                for fc in get_fcurves(action)
                for kp in fc.keyframe_points
                if kp.select_control_point
            ]
            if sel_frames:
                return float(min(sel_frames)), float(max(sel_frames))

    # SCENE or fallback.
    return float(scene.frame_start), float(scene.frame_end)
