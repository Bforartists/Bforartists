# --- BREAKDOWN AND INBETWEEN TOOLS ---
"""Pose snapshot + compare state used by the breakdown pose-compare tools.

A snapshot is an in-memory dict keyed by ``(data_path, array_index)``
containing the fcurve-evaluated value at a specific frame. Two slots
("previous" and "next") are tracked at module scope so an animator can
Copy Prev / Copy Next and then run a breakdown toward either reference.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import bpy

from .fcurve_compat import get_fcurves
from .logging import get_logger

__all__ = [
    "PoseSnapshot",
    "PoseCompareState",
    "get_state",
    "snapshot_object",
    "set_prev",
    "set_next",
    "set_reference",
    "clear",
    "compare_snapshots",
]

_log = get_logger(__name__)


PoseKey = tuple[str, int]


@dataclass
class PoseSnapshot:
    """Snapshot of all FCurve values at a given frame for a pose object.

    Keyed by (data_path, array_index), enabling the animator to set Previous
    and Next reference poses and interpolate breakdown keys between them.
    """
    frame: float
    label: str
    values: dict[PoseKey, float] = field(default_factory=dict)

    def get(self, data_path: str, array_index: int) -> float | None:
        """Look up the captured value for a specific FCurve channel in this snapshot."""
        return self.values.get((data_path, int(array_index)))


@dataclass
class PoseCompareState:
    """Session state tracking previous, next, and reference pose snapshots.

    Allows animators to set Prev/Next, then scrub the breakdown slider to place
    the inbetween pose. Compare reports show which channels differ between poses.
    """
    prev_snapshot: PoseSnapshot | None = None
    next_snapshot: PoseSnapshot | None = None
    reference_snapshot: PoseSnapshot | None = None
    last_report: list[str] = field(default_factory=list)


_STATE = PoseCompareState()


def get_state() -> PoseCompareState:
    """Return the module-level pose compare state singleton."""
    return _STATE


def snapshot_object(
    obj: bpy.types.Object,
    frame: float,
    label: str,
) -> PoseSnapshot:
    """Capture all FCurve values for obj at frame into a PoseSnapshot.

    Evaluate each FCurve at the given frame and store in a dict keyed by
    (data_path, array_index) for later pose comparison.
    """
    snap = PoseSnapshot(frame=frame, label=label)
    adata = getattr(obj, "animation_data", None)
    if adata is None or adata.action is None:
        return snap
    for fc in get_fcurves(adata.action, anim_data=adata):
        try:
            value = float(fc.evaluate(frame))
        except Exception:  # pragma: no cover — defensive against RNA edge cases
            continue
        snap.values[(fc.data_path, int(fc.array_index))] = value
    return snap


def set_prev(obj: bpy.types.Object, frame: float) -> PoseSnapshot:
    """Snapshot obj at frame and store as the previous reference pose."""
    _STATE.prev_snapshot = snapshot_object(obj, frame, "Previous Pose")
    return _STATE.prev_snapshot


def set_next(obj: bpy.types.Object, frame: float) -> PoseSnapshot:
    """Snapshot obj at frame and store as the next reference pose."""
    _STATE.next_snapshot = snapshot_object(obj, frame, "Next Pose")
    return _STATE.next_snapshot


def set_reference(obj: bpy.types.Object, frame: float) -> PoseSnapshot:
    """Snapshot obj at frame and store as an additional reference pose."""
    _STATE.reference_snapshot = snapshot_object(obj, frame, "Reference Pose")
    return _STATE.reference_snapshot


def clear() -> None:
    """Reset all pose snapshots and comparison reports."""
    _STATE.prev_snapshot = None
    _STATE.next_snapshot = None
    _STATE.reference_snapshot = None
    _STATE.last_report.clear()


def compare_snapshots(
    a: PoseSnapshot | None,
    b: PoseSnapshot | None,
    *,
    tolerance: float = 1e-5,
) -> list[str]:
    """Return a human-readable list of differing channels."""
    if a is None or b is None:
        return ["Both snapshots required for compare."]
    diffs: list[str] = []
    keys = set(a.values.keys()) | set(b.values.keys())
    for key in sorted(keys):
        va = a.values.get(key)
        vb = b.values.get(key)
        if va is None:
            diffs.append(f"+ {key[0]}[{key[1]}]  (only in {b.label})")
            continue
        if vb is None:
            diffs.append(f"- {key[0]}[{key[1]}]  (only in {a.label})")
            continue
        if abs(va - vb) > tolerance:
            diffs.append(
                f"~ {key[0]}[{key[1]}]  {va:.4f} → {vb:.4f}"
            )
    return diffs
