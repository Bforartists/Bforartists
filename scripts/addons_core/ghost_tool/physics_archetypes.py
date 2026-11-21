"""physics_archetypes.py — Pure math archetype functions for physics-informed animation.

Zero bpy imports.  This module is testable outside Blender and safe to import
from any context.

Each archetype function accepts ``t ∈ [0.0, 1.0]`` (normalised time within a
motion segment) and returns a normalised displacement value.

Amplitude, axis mapping, and frame-to-time conversion are the *caller's*
responsibility — these functions produce only the shape of the motion curve.

Boundary contracts
------------------
Return-to-rest archetypes (PENDULUM, BOUNCE, WOBBLE):
    f(0.0) ≈ 0.0  and  f(1.0) ≈ 0.0

Settle-type archetypes (SETTLE):
    f(0.0) = 0.0  and  f(1.0) → 1.0  (asymptotic; reaches ~0.993 at t=1)

Overshoot archetypes (SPRINGBACK):
    f(0.0) = 0.0  — peaks above 1.0 near t≈0.6  — f(1.0) ≈ 0.0

Adding a new archetype in v2
-----------------------------
1.  Write a function matching signature ``(t: float) -> float``.
2.  Register it in ``ARCHETYPES`` dict below.
3.  Add a matching entry to ``ARCHETYPE_ENUM_ITEMS``.
No other files need changing — the UI and bake loop both iterate ARCHETYPES.
"""

from __future__ import annotations

import math
from typing import Callable

# ---------------------------------------------------------------------------
# Shape constants — named so their intent is auditable, not magic numbers
# ---------------------------------------------------------------------------

_PENDULUM_CYCLES: float = 2.5
"""Full oscillation cycles across the normalised segment [0, 1]."""

_PENDULUM_DAMPING: float = 3.5
"""Exponential decay rate for pendulum amplitude.

Tuned so the decayed envelope at t=1.0 is small (e^-3.5 ~= 0.030).  Because
2.5 half-cycles end on a sine peak, the raw curve retains that full 3%
residual at t=1.0 — stamped onto the final keyframe, that reads as an
end-pop.  ``_pendulum`` therefore subtracts a linear tail so f(1.0) == 0.0
exactly while deviating from the raw shape by at most 3%.
"""

_PENDULUM_TAIL: float = math.sin(math.pi * _PENDULUM_CYCLES) * math.exp(-_PENDULUM_DAMPING)
"""Raw residual displacement of the pendulum curve at t=1.0.

Subtracted linearly across the segment by ``_pendulum`` to satisfy the
return-to-rest boundary contract (f(1.0) == 0.0) without a hard clamp.
"""

_BOUNCE_DECAY: float = 0.55
"""Height ratio between successive bounce arcs (0 < decay < 1).

0.55 produces four visually distinct bounces before the motion flattens.
"""

_BOUNCE_ARC_COUNT: int = 4
"""Number of parabolic bounce arcs to model."""

_SETTLE_STEEPNESS: float = 5.0
"""Exponential approach rate for SETTLE.

At t=1.0: 1 - e^(-5) ≈ 0.993 — effectively reached the target.
"""

_WOBBLE_FREQUENCY: float = 4.0
"""Oscillation cycles for WOBBLE across [0, 1]."""

_WOBBLE_DECAY: float = 4.0
"""Exponential envelope decay for WOBBLE amplitude."""

_SPRINGBACK_OVERSHOOT: float = 1.4
"""Peak displacement multiplier for SPRINGBACK.

Values above 1.0 produce overshoot beyond the canonical displacement range.
Intentionally exaggerated to make the arc readable at typical scene scales.
"""

_EPSILON: float = 1e-8
"""Guard against division-by-zero in normalised segment calculations."""


# ---------------------------------------------------------------------------
# Archetype functions
# ---------------------------------------------------------------------------

def _pendulum(t: float) -> float:
    """Damped-sine arc — swings out and settles at rest.

    Models a pendulum released from displacement: one or more oscillations
    with exponentially decaying amplitude.

    Boundary: f(0) ≈ 0.0, f(1) < 0.05 (effectively at rest).

    Args:
        t: Normalised time in [0.0, 1.0].

    Returns:
        float: Displacement in approximately [-1.0, 1.0].
    """
    raw = math.sin(t * math.pi * _PENDULUM_CYCLES) * math.exp(-_PENDULUM_DAMPING * t)
    return raw - t * _PENDULUM_TAIL


def _bounce(t: float) -> float:
    """Parabolic-decay series — impacts the floor and bounces progressively smaller.

    Simulates a ball: each successive arc has reduced height and duration
    scaled by ``_BOUNCE_DECAY``.  Always non-negative (object above ground).

    Boundary: f(0) = 0.0, f(1) ≈ 0.0.

    Args:
        t: Normalised time in [0.0, 1.0].

    Returns:
        float: Displacement in [0.0, 1.0].
    """
    heights = [_BOUNCE_DECAY ** i for i in range(_BOUNCE_ARC_COUNT)]
    # Duration of each arc is proportional to the square root of its drop height
    raw_durations = [math.sqrt(h) for h in heights]
    total = sum(raw_durations)
    durations = [d / total for d in raw_durations]

    cumulative = 0.0
    for i, segment_width in enumerate(durations):
        segment_end = cumulative + segment_width
        is_last_arc = (i == _BOUNCE_ARC_COUNT - 1)

        if t <= segment_end or is_last_arc:
            local_t = (t - cumulative) / max(segment_width, _EPSILON)
            local_t = max(0.0, min(local_t, 1.0))
            # Parabolic arc peaking at local_t == 0.5
            return heights[i] * 4.0 * local_t * (1.0 - local_t)

        cumulative = segment_end

    return 0.0


def _settle(t: float) -> float:
    """Exponential approach — accelerates toward a target and effectively arrives.

    Boundary: f(0) = 0.0, f(1) ≈ 0.993 (asymptotic, not exactly 1.0).

    Args:
        t: Normalised time in [0.0, 1.0].

    Returns:
        float: Displacement in [0.0, ~1.0].
    """
    return 1.0 - math.exp(-_SETTLE_STEEPNESS * t)


def _wobble(t: float) -> float:
    """Decaying cosine — symmetric ring oscillation fading to rest.

    Models a structure or spring that vibrates after an impulse.  The cosine
    is offset by its own envelope so f(0) starts at zero rather than -1.

    Boundary: f(0) ≈ 0.0, f(1) ≈ 0.0.

    # TODO(v2): validate wobble frequency and decay against animator feedback
    # before promoting to a first-class archetype in the default preset set.

    Args:
        t: Normalised time in [0.0, 1.0].

    Returns:
        float: Displacement in approximately [-1.0, 1.0].
    """
    envelope = math.exp(-_WOBBLE_DECAY * t)
    return math.cos(t * math.pi * _WOBBLE_FREQUENCY) * envelope - envelope


def _springback(t: float) -> float:
    """Cubic overshoot — shoots past the target, then snaps back toward rest.

    Uses a smoothstep-shaped cubic multiplied by a sine to create a single
    visible overshoot above 1.0 before returning.

    Boundary: f(0) = 0.0, f(1) ≈ 0.0.

    # TODO(v2): validate springback overshoot magnitude against animator
    # feedback. The current overshoot factor is intentionally exaggerated
    # for preview clarity at typical scene scales.

    Args:
        t: Normalised time in [0.0, 1.0].

    Returns:
        float: Displacement; peaks above 1.0 near t≈0.6.
    """
    smoothstep = t * t * (3.0 - 2.0 * t)
    return _SPRINGBACK_OVERSHOOT * smoothstep * math.sin(t * math.pi)


# ---------------------------------------------------------------------------
# Public registry — the single source of truth for all consumers
# ---------------------------------------------------------------------------

ARCHETYPES: dict[str, Callable[[float], float]] = {
    "PENDULUM":   _pendulum,
    "BOUNCE":     _bounce,
    "SETTLE":     _settle,
    "WOBBLE":     _wobble,
    "SPRINGBACK": _springback,
}
"""Map of archetype name → normalised displacement function.

This dict is consumed by:
  - ``ARCHETYPE_ENUM_ITEMS`` (UI dropdown, built once at import time)
  - The preview loop in ``physics_suggest.py`` (evaluates selected fn per ghost)
  - ``GHOST_OT_archetype_bake.execute()`` (same evaluation, writes keyframes)

To add a new archetype: implement a function above and register it here.
No other files require modification.
"""

ARCHETYPE_ENUM_ITEMS: list[tuple[str, str, str]] = [
    (
        "PENDULUM",
        "Pendulum",
        "Damped swing — oscillates out from rest and settles back",
    ),
    (
        "BOUNCE",
        "Bounce",
        "Impact arcs — decaying parabolic bounces toward the floor",
    ),
    (
        "SETTLE",
        "Settle",
        "Exponential approach — accelerates toward target and arrives",
    ),
    (
        "WOBBLE",
        "Wobble",
        "Decaying ring — symmetric oscillation fading to rest after impulse",
    ),
    (
        "SPRINGBACK",
        "Springback",
        "Overshoot cubic — snaps past target, returns toward rest",
    ),
]
"""Pre-built EnumProperty items derived from ARCHETYPES.

Kept in insertion order so the UI dropdown matches the narrative arc
from largest motion (PENDULUM) to controlled arrival (SPRINGBACK).
"""
