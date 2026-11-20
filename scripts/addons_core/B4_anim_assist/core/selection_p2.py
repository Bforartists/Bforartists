"""Advanced key selection helpers (key selection and channel)."""

from __future__ import annotations

from typing import Callable

import bpy

from .context_utils import iter_visible_fcurves, iter_selected_keys

__all__ = [
    "select_all_visible",
    "invert_visible",
    "select_where",
    "selected_frames",
    "selection_bounds",
    "select_frame_range",
    "select_every_nth",
    "select_neighbors",
]


def _set_selected(kp: bpy.types.Keyframe, state: bool, handles: bool = True) -> None:
    kp.select_control_point = state
    if handles:
        kp.select_left_handle = state
        kp.select_right_handle = state


def select_all_visible(context: bpy.types.Context, state: bool = True) -> int:
    """Select or deselect all keyframes in visible FCurves. Return count modified."""
    n = 0
    for _o, _a, fc in iter_visible_fcurves(context):
        for kp in fc.keyframe_points:
            _set_selected(kp, state)
            n += 1
    return n


def invert_visible(context: bpy.types.Context) -> int:
    """Toggle selection state of all keyframes in visible FCurves. Return count modified."""
    n = 0
    for _o, _a, fc in iter_visible_fcurves(context):
        for kp in fc.keyframe_points:
            _set_selected(kp, not kp.select_control_point)
            n += 1
    return n


def select_where(
    context: bpy.types.Context,
    predicate: Callable[[bpy.types.FCurve, int, bpy.types.Keyframe], bool],
    additive: bool = False,
    deselect: bool = False,
) -> int:
    """Select keys matching a predicate function, powering "select by tag", "select dense keys", etc.

    Additive=True keeps existing selection; deselect=True inverts the selection logic.
    Return count of keys modified.
    """
    n = 0
    target_state = not deselect
    for _o, _a, fc in iter_visible_fcurves(context):
        for i, kp in enumerate(fc.keyframe_points):
            hit = predicate(fc, i, kp)
            if hit:
                _set_selected(kp, target_state)
                n += 1
            elif not additive and not deselect:
                _set_selected(kp, False)
    return n


def selected_frames(context: bpy.types.Context) -> set[float]:
    """Return the set of frame numbers with selected keys."""
    return {round(float(kp.co.x), 4) for *_x, kp in iter_selected_keys(context)}


def selection_bounds(context: bpy.types.Context) -> tuple[float, float] | None:
    """Return (min_frame, max_frame) of selected keys, or None if empty.

    Used by offset and retime operations to determine the working frame range.
    """
    frames = selected_frames(context)
    if not frames:
        return None
    return min(frames), max(frames)


def select_frame_range(
    context: bpy.types.Context, start: float, end: float, deselect: bool = False
) -> int:
    """Select all keys in [start, end] frame range. Return count modified."""
    lo, hi = min(start, end), max(start, end)
    return select_where(
        context,
        lambda _fc, _i, kp: lo <= kp.co.x <= hi,
        additive=False,
        deselect=deselect,
    )


def select_every_nth(context: bpy.types.Context, n: int, offset: int = 0) -> int:
    """Select every nth key (essential for cleaning up motion capture decimation).

    Select key at indices where (i - offset) % n == 0. Return count modified.
    """
    n = max(1, int(n))
    count = 0
    for _o, _a, fc in iter_visible_fcurves(context):
        for i, kp in enumerate(fc.keyframe_points):
            if (i - offset) % n == 0 and (i - offset) >= 0:
                _set_selected(kp, True)
                count += 1
            else:
                _set_selected(kp, False)
    return count


def select_neighbors(context: bpy.types.Context, direction: str = "BOTH") -> int:
    """Extend selection to neighbouring key(s) of each currently selected key."""
    count = 0
    for _o, _a, fc in iter_visible_fcurves(context):
        selected_idx = [i for i, kp in enumerate(fc.keyframe_points) if kp.select_control_point]
        if not selected_idx:
            continue
        to_add: set[int] = set()
        last = len(fc.keyframe_points) - 1
        for i in selected_idx:
            if direction in ("LEFT", "BOTH") and i > 0:
                to_add.add(i - 1)
            if direction in ("RIGHT", "BOTH") and i < last:
                to_add.add(i + 1)
        for j in to_add:
            _set_selected(fc.keyframe_points[j], True)
            count += 1
    return count
