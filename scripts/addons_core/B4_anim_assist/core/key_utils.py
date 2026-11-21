"""Key utility/clipboard helpers (key selection and channel)."""

from __future__ import annotations

import bpy

from .context_utils import iter_visible_fcurves, iter_selected_keys

__all__ = [
    "copy_selected_keys",
    "paste_keys",
    "clipboard_size",
    "offset_selected",
    "snap_selected_to_integer_frames",
    "mirror_selected",
]


# ---------------------------------------------------------------------------
# Session-transient clipboard
# ---------------------------------------------------------------------------

# (action.name, data_path, array_index) -> list of serialised keyframe dicts
_clipboard: dict[tuple, list[dict]] = {}


def copy_selected_keys(context: bpy.types.Context) -> int:
    """Copy selected keys (with handle data) into the module clipboard.

    Replaces any previously copied data.
    """
    _clipboard.clear()
    count = 0
    for obj, action, fc in iter_visible_fcurves(context):
        items: list[dict] = []
        for kp in fc.keyframe_points:
            if not kp.select_control_point:
                continue
            items.append({
                "frame": float(kp.co.x),
                "value": float(kp.co.y),
                "interpolation": kp.interpolation,
                "type": kp.type,
                "hl": (float(kp.handle_left.x), float(kp.handle_left.y)),
                "hr": (float(kp.handle_right.x), float(kp.handle_right.y)),
                "hlt": kp.handle_left_type,
                "hrt": kp.handle_right_type,
            })
        if items:
            _clipboard[(action.name, fc.data_path, fc.array_index)] = items
            count += len(items)
    return count


def paste_keys(context: bpy.types.Context, frame_offset: float = 0.0) -> int:
    """Paste clipboard keys onto matching FCurves, shifted by *frame_offset*."""
    count = 0
    for _o, action, fc in iter_visible_fcurves(context):
        items = _clipboard.get((action.name, fc.data_path, fc.array_index))
        if not items:
            continue
        for it in items:
            kp = fc.keyframe_points.insert(
                it["frame"] + frame_offset, it["value"], options={"FAST"}
            )
            # Defensive: Blender 4.x has returned None from insert() in edge
            # cases (NEEDED flag, duplicate frames). Skip the row instead of
            # crashing so the remaining paste rows still land.
            if kp is None:
                continue
            kp.interpolation = it["interpolation"]
            kp.type = it["type"]
            kp.handle_left_type = it["hlt"]
            kp.handle_right_type = it["hrt"]
            kp.handle_left.x = it["hl"][0] + frame_offset
            kp.handle_left.y = it["hl"][1]
            kp.handle_right.x = it["hr"][0] + frame_offset
            kp.handle_right.y = it["hr"][1]
            count += 1
        fc.update()
    return count


def clipboard_size() -> int:
    """Return the number of keyframes currently in the module clipboard.

    This clipboard preserves handle types and interpolation, unlike Blender's
    native clipboard which strips that data.
    """
    return sum(len(v) for v in _clipboard.values())


# ---------------------------------------------------------------------------
# In-place key mutations
# ---------------------------------------------------------------------------

class _FCurveTracker:
    """Helper to track and batch-update touched FCurves."""

    def __init__(self) -> None:
        self._ids: set[int] = set()
        self._curves: list[bpy.types.FCurve] = []
        self.count: int = 0

    def touch(self, fc: bpy.types.FCurve) -> None:
        """Mark an FCurve as touched. Deduplicates by object ID."""
        if id(fc) not in self._ids:
            self._ids.add(id(fc))
            self._curves.append(fc)
        self.count += 1

    def update_all(self) -> None:
        """Call update() on all touched FCurves."""
        for fc in self._curves:
            fc.update()


def offset_selected(context: bpy.types.Context, dx: float = 0.0, dy: float = 0.0) -> int:
    """Shift selected keys by *dx* frames and *dy* value units.

    Only FCurves that actually contain selected keys are updated.
    """
    tracker = _FCurveTracker()
    for _o, _a, fc, _i, kp in iter_selected_keys(context):
        kp.co.x += dx
        kp.co.y += dy
        kp.handle_left.x += dx
        kp.handle_left.y += dy
        kp.handle_right.x += dx
        kp.handle_right.y += dy
        tracker.touch(fc)
    tracker.update_all()
    return tracker.count


def snap_selected_to_integer_frames(context: bpy.types.Context) -> int:
    """Round selected keys' frame positions to the nearest integer."""
    tracker = _FCurveTracker()
    for _o, _a, fc, _i, kp in iter_selected_keys(context):
        kp.co.x = round(kp.co.x)
        tracker.touch(fc)
    tracker.update_all()
    return tracker.count


def mirror_selected(context: bpy.types.Context, pivot: float) -> int:
    """Mirror selected keys horizontally around *pivot* (frame number).

    Both the key's X position and its bezier handles are mirrored correctly:
    the left and right handles swap sides, with both X and Y exchanged so
    tangent curvature is preserved after the flip.
    """
    tracker = _FCurveTracker()
    for _o, _a, fc, _i, kp in iter_selected_keys(context):
        # Mirror the control point.
        kp.co.x = 2.0 * pivot - kp.co.x

        # Capture both handles before mutating either.
        old_hl_x = float(kp.handle_left.x)
        old_hl_y = float(kp.handle_left.y)
        old_hr_x = float(kp.handle_right.x)
        old_hr_y = float(kp.handle_right.y)

        # After mirroring, the old right handle becomes the new left handle and
        # vice-versa.  Mirror the X and swap the Y values between sides.
        kp.handle_left.x = 2.0 * pivot - old_hr_x
        kp.handle_left.y = old_hr_y
        kp.handle_right.x = 2.0 * pivot - old_hl_x
        kp.handle_right.y = old_hl_y

        tracker.touch(fc)
    tracker.update_all()
    return tracker.count
