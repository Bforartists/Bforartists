# --- TRANSFORM OFFSET CONTROLS ---
"""Per-frame falloff shapes for offset offset distribution.

The helpers in this module produce a *scalar weight in [0, 1]* for a
given frame inside an ``[start, end]`` window. The weight is then used
to scale a single, already-computed transform delta when it is applied
to each frame in the window.

Important: these helpers DO NOT modify fcurve tangents, handles,
interpolation modes, or key values directly. They only return a
distribution weight. This boundary is what keeps offset's
"ease-in / ease-out distribution helpers" out of the excluded Animaide
user-facing ease-tangent category.

Shape semantics (normalised across the window):

* ``NONE``      — always returns ``1.0``.
* ``LINEAR``    — triangular peak at the window midpoint, 0 at edges.
* ``EASE_IN``   — starts at 0, accelerates toward 1 at the end.
* ``EASE_OUT``  — starts at 1, decelerates toward 0 at the end.
* ``BELL``      — smooth cosine 0 at edges, 1 at midpoint.

All shapes clamp to ``[0, 1]``.

Pure Python. No ``bpy`` imports — safe to unit-test without Blender.
"""

from __future__ import annotations

import math

EPSILON = 1e-9

FALLOFF_SHAPES: tuple[str, ...] = (
    "NONE",
    "LINEAR",
    "EASE_IN",
    "EASE_OUT",
    "BELL",
)


def _normalise(frame: float, start: float, end: float) -> float | None:
    """Return normalised position [0, 1] or None if outside window."""
    """Return the normalised position ``t ∈ [0, 1]`` inside the window.

    Returns ``None`` when the frame lies strictly outside the window, so
    callers can skip writes instead of applying a zero weight.
    """
    if end < start:
        start, end = end, start
    span = end - start
    if span <= EPSILON:
        # Zero-width window degenerates to full weight at the start frame
        # and no weight elsewhere.
        return 1.0 if abs(frame - start) <= EPSILON else None
    if frame < start - EPSILON or frame > end + EPSILON:
        return None
    t = (frame - start) / span
    if t < 0.0:
        t = 0.0
    elif t > 1.0:
        t = 1.0
    return t


def falloff_weight(
    frame: float,
    start: float,
    end: float,
    shape: str,
) -> float:
    """Return the falloff weight for ``frame`` inside ``[start, end]``.

    Frames outside the window return ``0.0``. Unknown shapes degrade to
    ``NONE``.
    """
    if shape == "NONE":
        # NONE is global: every frame in the window gets full weight.
        # For frames outside the window we still return 0 so the caller
        # can safely skip them, matching the other shapes.
        t = _normalise(frame, start, end)
        return 0.0 if t is None else 1.0

    t = _normalise(frame, start, end)
    if t is None:
        return 0.0

    if shape == "LINEAR":
        # Triangle: 0 at edges, 1 at midpoint.
        return 1.0 - abs(2.0 * t - 1.0)

    if shape == "EASE_IN":
        # Quadratic ease-in: 0 → 1, slow start.
        return t * t

    if shape == "EASE_OUT":
        # Quadratic ease-out: 1 → 0, slow end. This is an ease-out of the
        # amount being distributed: the first frame gets the full delta
        # and later frames get progressively less.
        inv = 1.0 - t
        return inv * inv

    if shape == "BELL":
        # Smooth cosine bell centred on the midpoint.
        return 0.5 - 0.5 * math.cos(2.0 * math.pi * t)

    # Unknown shape → fall back to NONE behaviour.
    return 1.0


def window_bounds(
    explicit_start: float | None,
    explicit_end: float | None,
    frames: list[float],
) -> tuple[float, float]:
    """Resolve the active falloff window.

    If the caller supplied explicit ``start`` / ``end`` values they are
    used verbatim (swapped if inverted). Otherwise the window spans the
    ``(min, max)`` of the provided frames, or ``(0, 0)`` if the frame
    list is empty.
    """
    if explicit_start is not None and explicit_end is not None:
        if explicit_end < explicit_start:
            return (explicit_end, explicit_start)
        return (explicit_start, explicit_end)
    if not frames:
        return (0.0, 0.0)
    return (min(frames), max(frames))


__all__ = [
    "FALLOFF_SHAPES",
    "falloff_weight",
    "window_bounds",
]
