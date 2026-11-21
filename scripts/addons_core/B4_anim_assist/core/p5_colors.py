# --- TRAJECTORY VISUALIZATION ---
"""Colour palettes and per-segment colouring functions for trajectory overlays.

All colours are ``(R, G, B, A)`` float tuples in 0–1 range, ready for
GPU shader uniforms.  No bpy dependency — pure Python + basic math.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "TrajectoryPalette",
    "PALETTE_DEFAULT",
    "PALETTE_CONTRAST",
    "PALETTE_PASTEL",
    "PALETTES",
    "palette_by_id",
    "PALETTE_ENUM_ITEMS",
    "palette_enum_items_callback",
    "spacing_color",
    "deviation_heatmap_color",
]


# ---------------------------------------------------------------------------
# Base palette
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TrajectoryPalette:
    """Named colour preset for the trajectory overlay."""

    id: str
    label: str
    path: tuple[float, float, float, float]
    keyframe_tick: tuple[float, float, float, float]
    frame_tick: tuple[float, float, float, float]
    velocity: tuple[float, float, float, float]
    tangent: tuple[float, float, float, float]
    ghost: tuple[float, float, float, float]
    stop_marker: tuple[float, float, float, float]
    contact_marker: tuple[float, float, float, float]
    apex_marker: tuple[float, float, float, float]
    reversal_marker: tuple[float, float, float, float]
    issue_hi: tuple[float, float, float, float]
    issue_lo: tuple[float, float, float, float]
    comparison_a: tuple[float, float, float, float]
    comparison_b: tuple[float, float, float, float]
    label_color: tuple[float, float, float, float]


PALETTE_DEFAULT = TrajectoryPalette(
    id="DEFAULT",
    label="Default",
    path=(0.9, 0.65, 0.15, 0.85),
    keyframe_tick=(1.0, 1.0, 0.2, 1.0),
    frame_tick=(0.7, 0.7, 0.7, 0.5),
    velocity=(0.3, 0.9, 0.3, 0.7),
    tangent=(0.3, 0.6, 1.0, 0.5),
    ghost=(0.8, 0.8, 0.8, 0.3),
    stop_marker=(1.0, 0.2, 0.2, 1.0),
    contact_marker=(0.2, 0.8, 0.2, 1.0),
    apex_marker=(0.2, 0.5, 1.0, 1.0),
    reversal_marker=(1.0, 0.5, 0.0, 1.0),
    issue_hi=(1.0, 0.15, 0.15, 0.9),
    issue_lo=(0.3, 0.3, 1.0, 0.7),
    comparison_a=(0.9, 0.5, 0.1, 0.8),
    comparison_b=(0.1, 0.5, 0.9, 0.8),
    label_color=(1.0, 1.0, 1.0, 0.9),
)

PALETTE_CONTRAST = TrajectoryPalette(
    id="CONTRAST",
    label="High Contrast",
    path=(1.0, 1.0, 0.0, 1.0),
    keyframe_tick=(1.0, 0.0, 1.0, 1.0),
    frame_tick=(0.9, 0.9, 0.9, 0.7),
    velocity=(0.0, 1.0, 0.0, 0.9),
    tangent=(0.0, 0.7, 1.0, 0.7),
    ghost=(1.0, 1.0, 1.0, 0.4),
    stop_marker=(1.0, 0.0, 0.0, 1.0),
    contact_marker=(0.0, 1.0, 0.0, 1.0),
    apex_marker=(0.0, 0.4, 1.0, 1.0),
    reversal_marker=(1.0, 0.6, 0.0, 1.0),
    issue_hi=(1.0, 0.0, 0.0, 1.0),
    issue_lo=(0.4, 0.4, 1.0, 0.9),
    comparison_a=(1.0, 0.6, 0.0, 1.0),
    comparison_b=(0.0, 0.6, 1.0, 1.0),
    label_color=(1.0, 1.0, 1.0, 1.0),
)

PALETTE_PASTEL = TrajectoryPalette(
    id="PASTEL",
    label="Pastel",
    path=(0.85, 0.75, 0.55, 0.7),
    keyframe_tick=(0.95, 0.85, 0.5, 0.9),
    frame_tick=(0.7, 0.7, 0.7, 0.4),
    velocity=(0.5, 0.85, 0.5, 0.6),
    tangent=(0.55, 0.7, 0.9, 0.5),
    ghost=(0.75, 0.75, 0.75, 0.25),
    stop_marker=(0.9, 0.45, 0.45, 0.9),
    contact_marker=(0.45, 0.8, 0.45, 0.9),
    apex_marker=(0.45, 0.6, 0.9, 0.9),
    reversal_marker=(0.9, 0.65, 0.35, 0.9),
    issue_hi=(0.9, 0.35, 0.35, 0.8),
    issue_lo=(0.5, 0.5, 0.85, 0.6),
    comparison_a=(0.85, 0.65, 0.4, 0.7),
    comparison_b=(0.4, 0.65, 0.85, 0.7),
    label_color=(0.95, 0.95, 0.95, 0.85),
)

PALETTES: dict[str, TrajectoryPalette] = {
    p.id: p for p in (PALETTE_DEFAULT, PALETTE_CONTRAST, PALETTE_PASTEL)
}


def palette_by_id(pid: str) -> TrajectoryPalette:
    """Resolve a preset name (id) to its color list so UI and draw callback agree on colors."""
    return PALETTES.get(pid, PALETTE_DEFAULT)


# Module-level enum items for EnumProperty (Blender string retention safety).
PALETTE_ENUM_ITEMS: tuple[tuple[str, str, str], ...] = tuple(
    (p.id, p.label, f"Use the {p.label} colour scheme for trajectory overlays.")
    for p in (PALETTE_DEFAULT, PALETTE_CONTRAST, PALETTE_PASTEL)
)


def palette_enum_items_callback(self, context) -> tuple[tuple[str, str, str], ...]:  # noqa: ARG001
    """Return palette enum items for EnumProperty."""
    return PALETTE_ENUM_ITEMS


# ---------------------------------------------------------------------------
# Spacing-based segment coloring
# ---------------------------------------------------------------------------

def spacing_color(
    segment_len: float,
    median_len: float,
    *,
    hi_ratio: float = 1.8,
    lo_ratio: float = 0.4,
    base_color: tuple[float, float, float, float] = (0.9, 0.65, 0.15, 0.85),
    hi_color: tuple[float, float, float, float] = (1.0, 0.15, 0.15, 0.9),
    lo_color: tuple[float, float, float, float] = (0.3, 0.3, 1.0, 0.7),
) -> tuple[float, float, float, float]:
    """Return an RGBA colour for a segment based on its length relative to median.

    Overspaced (> hi_ratio * median) → ``hi_color``.
    Underspaced (< lo_ratio * median) → ``lo_color``.
    Normal → ``base_color``.
    In-between values are linearly interpolated.
    """
    if median_len <= 0.0:
        return base_color

    ratio = segment_len / median_len

    if ratio >= hi_ratio:
        return hi_color
    if ratio <= lo_ratio:
        return lo_color

    # Interpolate in the transition zones.
    if ratio > 1.0:
        t = (ratio - 1.0) / max(hi_ratio - 1.0, 1e-6)
        t = min(max(t, 0.0), 1.0)
        return _lerp4(base_color, hi_color, t)
    else:
        t = (1.0 - ratio) / max(1.0 - lo_ratio, 1e-6)
        t = min(max(t, 0.0), 1.0)
        return _lerp4(base_color, lo_color, t)


def deviation_heatmap_color(
    deviation: float,
    max_deviation: float,
    *,
    cold_color: tuple[float, float, float, float] = (0.2, 0.6, 1.0, 0.7),
    hot_color: tuple[float, float, float, float] = (1.0, 0.15, 0.15, 0.9),
) -> tuple[float, float, float, float]:
    """Heatmap blue→red based on arc deviation magnitude."""
    if max_deviation <= 0.0:
        return cold_color
    t = min(max(deviation / max_deviation, 0.0), 1.0)
    return _lerp4(cold_color, hot_color, t)


def _lerp4(
    a: tuple[float, float, float, float],
    b: tuple[float, float, float, float],
    t: float,
) -> tuple[float, float, float, float]:
    return (
        a[0] + (b[0] - a[0]) * t,
        a[1] + (b[1] - a[1]) * t,
        a[2] + (b[2] - a[2]) * t,
        a[3] + (b[3] - a[3]) * t,
    )
