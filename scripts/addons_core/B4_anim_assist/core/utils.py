"""Shared data structures and utility functions (pure Python)."""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = [
    "EPSILON",
    "KeyData",
    "FCurveSnapshot",
    "lerp",
    "clamp",
    "smoothstep",
    "inverse_lerp",
    "remap",
    "get_selected_indices",
    "find_neighbors",
]

EPSILON: float = 1e-6


@dataclass
class KeyData:
    """Bpy-free representation of a keyframe, enabling unit-testable FCurve math.

    Stores frame, value, selection state, and handle positions for pure Python
    computation in Curve Tools and Breakdown operations without Blender dependencies.
    """
    frame: float
    value: float
    selected: bool = False
    handle_left: tuple[float, float] = (0.0, 0.0)
    handle_right: tuple[float, float] = (0.0, 0.0)


@dataclass
class FCurveSnapshot:
    """Snapshot of a single FCurve's keys at a moment in time.

    Captures data_path, array_index, and all KeyData for a channel so Curve Tools
    can operate on the curve's state independently of the bpy object.
    """
    data_path: str = ""
    array_index: int = 0
    keys: list[KeyData] = field(default_factory=list)


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation: blend from a to b by factor t (0=a, 1=b)."""
    return a + (b - a) * t


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Constrain value to [min_val, max_val] range."""
    return max(min_val, min(max_val, value))


def smoothstep(t: float) -> float:
    """Hermite ease-in/ease-out interpolation: smooth acceleration and deceleration."""
    t = clamp(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def inverse_lerp(a: float, b: float, value: float) -> float:
    """Return the blend factor t such that lerp(a, b, t) == value."""
    denom = b - a
    if abs(denom) < EPSILON:
        return 0.0
    return (value - a) / denom


def remap(value: float, from_min: float, from_max: float, to_min: float, to_max: float) -> float:
    """Map value from [from_min, from_max] to [to_min, to_max] range."""
    t = inverse_lerp(from_min, from_max, value)
    return lerp(to_min, to_max, t)


def get_selected_indices(keys: list[KeyData]) -> list[int]:
    """Return indices of all selected keys in order."""
    return [i for i, k in enumerate(keys) if k.selected]


def find_neighbors(
    all_keys: list[KeyData],
    selected_indices: list[int],
) -> tuple[KeyData | None, KeyData | None]:
    """Find the nearest unselected keys bracketing the selection.

    Return (left_neighbor, right_neighbor) so Blend-to-Neighbor and Blend Offset
    know their interpolation targets. Both None if selection is empty or at curve edges.
    """
    if not selected_indices:
        return None, None

    sel_set = set(selected_indices)
    min_idx = min(selected_indices)
    max_idx = max(selected_indices)

    left: KeyData | None = None
    for i in range(min_idx - 1, -1, -1):
        if i not in sel_set:
            left = all_keys[i]
            break

    right: KeyData | None = None
    for i in range(max_idx + 1, len(all_keys)):
        if i not in sel_set:
            right = all_keys[i]
            break

    return left, right