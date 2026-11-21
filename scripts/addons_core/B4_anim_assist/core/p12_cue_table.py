"""Typed wrapper around the cue list stored on AA_P12_LipsyncLayerLink.

A cue table is a sequence of (time_seconds, viseme_name) pairs - the output
of audio analysis. Used by:
  - Driver expressions in PREVIEW mode (live evaluation per frame)
  - Bake operator in SHIPPED mode (write fcurves once)

Both modes read from the SAME table, so a re-analysis updates both.

Kept bpy-light: the dataclass + helpers work on any duck-typed link object
that exposes a `cue_table` collection with `time_seconds` and `viseme_name`
fields. Tests use a dict-of-lists stub.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .logging import get_logger

__all__ = [
    "Cue",
    "write_cues_to_link",
    "read_cues_from_link",
    "find_active_cue",
    "ease_smoothstep",
    "viseme_value_at_time",
]

_log = get_logger(__name__)


@dataclass
class Cue:
    """A single phoneme/viseme cue."""
    time_seconds: float
    viseme_name: str


def write_cues_to_link(link, cues: Iterable[Cue]) -> int:
    """Replace the link's cue collection with sorted *cues*. Returns count written."""
    if not hasattr(link, "cue_table"):
        return 0
    link.cue_table.clear()
    sorted_cues = sorted(cues, key=lambda c: c.time_seconds)
    for cue in sorted_cues:
        row = link.cue_table.add()
        row.time_seconds = float(cue.time_seconds)
        row.viseme_name = str(cue.viseme_name)
    return len(sorted_cues)


def read_cues_from_link(link) -> list[Cue]:
    """Materialise the link's cue collection as a typed list."""
    out: list[Cue] = []
    if not hasattr(link, "cue_table"):
        return out
    for row in link.cue_table:
        out.append(Cue(
            time_seconds=float(row.time_seconds),
            viseme_name=str(row.viseme_name),
        ))
    return out


def find_active_cue(
    cues: list[Cue],
    time_seconds: float,
) -> tuple[Cue | None, Cue | None, float]:
    """Return (prev, next, t) where t in [0,1] is the blend between prev and next.

    Edge cases:
    - Empty cue list -> (None, None, 0.0)
    - Time before first cue -> (cues[0], cues[0], 0.0)  (clamp left)
    - Time at/after last cue -> (cues[-1], cues[-1], 0.0)  (clamp right)
    """
    if not cues:
        return None, None, 0.0
    if time_seconds <= cues[0].time_seconds:
        return cues[0], cues[0], 0.0
    if time_seconds >= cues[-1].time_seconds:
        return cues[-1], cues[-1], 0.0
    for i in range(len(cues) - 1):
        a, b = cues[i], cues[i + 1]
        if a.time_seconds <= time_seconds < b.time_seconds:
            span = b.time_seconds - a.time_seconds
            t = 0.0 if span <= 0 else (time_seconds - a.time_seconds) / span
            return a, b, max(0.0, min(1.0, t))
    return cues[-1], cues[-1], 0.0


def ease_smoothstep(t: float) -> float:
    """Smoothstep easing - 3t^2 - 2t^3. Smooth in/out around midpoint."""
    if t <= 0.0:
        return 0.0
    if t >= 1.0:
        return 1.0
    return t * t * (3.0 - 2.0 * t)


def viseme_value_at_time(
    cues: list[Cue],
    time_seconds: float,
    viseme_name: str,
) -> float:
    """Return the blended 0..1 value for *viseme_name* at *time_seconds*.

    Used by the PREVIEW driver expression. If neither the prev nor next cue
    matches *viseme_name*, the value is 0 (mouth at rest for this viseme).
    If only one matches, the value crossfades against rest.
    """
    prev, nxt, t = find_active_cue(cues, time_seconds)
    if prev is None:
        return 0.0
    eased = ease_smoothstep(t)
    prev_val = 1.0 if prev.viseme_name == viseme_name else 0.0
    nxt_val = 1.0 if nxt.viseme_name == viseme_name else 0.0
    return prev_val * (1.0 - eased) + nxt_val * eased
