"""Pure logic for Anim Offset propagation (no bpy)."""

from __future__ import annotations

__all__ = [
    "MaskRegion",
    "mask_weight",
    "compute_propagated_values",
    "compute_propagated_values_full_range",
    "frames_outside_mask",
]

from dataclasses import dataclass

from .utils import EPSILON, clamp, smoothstep


@dataclass
class MaskRegion:
    """Time range defining which frames are affected by Anim Offset propagation.

    Blend_in and blend_out create smooth falloff using smoothstep so offset blending
    looks natural and doesn't create hard pops at the mask boundaries.
    """
    start: float
    end: float
    blend_in: float = 5.0
    blend_out: float = 5.0
    enabled: bool = True


def mask_weight(frame: float, mask: MaskRegion) -> float:
    """Return smoothstep falloff weight for frame within the mask region.

    Returns 1.0 in core region [start, end], smoothly fades to 0.0 during
    blend_in/blend_out to prevent hard transitions. Used to modulate propagated delta.
    """
    if not mask.enabled:
        return 1.0

    outer_left = mask.start - mask.blend_in
    outer_right = mask.end + mask.blend_out

    if frame < outer_left or frame > outer_right:
        return 0.0

    if frame < mask.start and mask.blend_in > EPSILON:
        t = (frame - outer_left) / mask.blend_in
        return smoothstep(clamp(t, 0.0, 1.0))

    if frame > mask.end and mask.blend_out > EPSILON:
        t = (outer_right - frame) / mask.blend_out
        return smoothstep(clamp(t, 0.0, 1.0))

    return 1.0


def compute_propagated_values(
    original_values: dict[float, float],
    delta: float,
    mask: MaskRegion,
    current_frame: float,
) -> dict[float, float]:
    """Apply weighted delta to each frame in the mask region.

    Skips the grabbed frame (current_frame) and uses mask_weight() to modulate
    the delta so surrounding keys are adjusted smoothly without hard breaks.
    """
    result: dict[float, float] = {}
    for frame, orig in original_values.items():
        if abs(frame - current_frame) < EPSILON:
            continue
        w = mask_weight(frame, mask)
        if w > EPSILON:
            result[frame] = orig + delta * w
    return result


def compute_propagated_values_full_range(
    original_values: dict[float, float],
    delta: float,
    current_frame: float,
) -> dict[float, float]:
    """Apply uniform delta to all frames except the grabbed frame.

    Used when mask is disabled, so the offset propagates equally everywhere.
    """
    result: dict[float, float] = {}
    for frame, orig in original_values.items():
        if abs(frame - current_frame) < EPSILON:
            continue
        result[frame] = orig + delta
    return result


def frames_outside_mask(frames: list[float], mask: MaskRegion) -> list[float]:
    """Return frames with zero mask weight (unaffected by offset propagation)."""
    return [f for f in frames if mask_weight(f, mask) < EPSILON]