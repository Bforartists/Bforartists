"""
viewport_draw.py — GPU draw handlers for ghost visualization in the 3D viewport.

This module registers persistent draw handlers that render:
- Ghost spheres at interpolated positions (color-coded by generation level)
- Motion arcs connecting ghosts and keyframes in sequence
- Spacing tick marks showing frame density along the arc
- Snapshot overlay ghosts in a desaturated style

All drawing uses Blender's gpu module with batched draw calls for performance.
Draw handlers are registered/unregistered cleanly to prevent crashes.
"""

from __future__ import annotations

import math
from typing import Optional

import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector

from .ghost_data import GhostStore, Ghost, MAX_SUBDIVISION_LEVEL
from .session_state import SessionState
from . import fcurve_utils
from .utils import log, warn, debug, tag_viewport_redraw


# ---------------------------------------------------------------------------
# Module-level draw handler references (must be stored for unregistration)
# ---------------------------------------------------------------------------

_draw_handler_3d: Optional[object] = None
_draw_handler_2d: Optional[object] = None

# Cache key for archetype preview recomputation.
# Tuple of (store_version, archetype_name, amplitude, axis).
# When unchanged between draw calls the expensive preview rebuild is skipped.
_archetype_preview_cache_key: tuple = ()


# ---------------------------------------------------------------------------
# GPU Batch Cache — avoids per-frame batch_for_shader rebuilds
# ---------------------------------------------------------------------------

class _BatchCache:
    """Bounded to the most recent viewport's marker batches."""
    def __init__(self):
        self.clear()

    def clear(self):
        self.key = None
        self.batches = ()


_batch_cache = _BatchCache()


# Pre-computed circle index template (reused for every ghost marker)
_CIRCLE_INDICES: list[tuple[int, int]] = []


def _get_circle_indices(segments: int = 16) -> list[tuple[int, int]]:
    """Return cached circle line indices for the given segment count."""
    global _CIRCLE_INDICES
    if len(_CIRCLE_INDICES) != segments:
        _CIRCLE_INDICES = [(i, (i + 1) % segments) for i in range(segments)]
    return _CIRCLE_INDICES


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Default colors per generation level (RGBA)
DEFAULT_LEVEL_COLORS: list[tuple[float, float, float, float]] = [
    (0.2, 0.7, 1.0, 0.85),   # Level 1: bright blue
    (0.3, 1.0, 0.5, 0.80),   # Level 2: green
    (1.0, 0.8, 0.2, 0.75),   # Level 3: gold
    (1.0, 0.4, 0.2, 0.70),   # Level 4: orange
    (0.9, 0.2, 0.8, 0.65),   # Level 5: magenta
]

KEYFRAME_MARKER_COLOR: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 0.95)
SELECTED_HIGHLIGHT_COLOR: tuple[float, float, float, float] = (1.0, 1.0, 0.0, 1.0)
PINNED_RING_COLOR: tuple[float, float, float, float] = (1.0, 0.3, 0.3, 0.9)
ARC_COLOR: tuple[float, float, float, float] = (0.5, 0.5, 0.5, 0.6)

SPHERE_SEGMENTS: int = 16
"""Number of line segments used to approximate a circle for ghost markers."""

CIRCLE_SEGMENTS: int = 16
"""Number of segments for billboard circles."""

PINNED_RING_SEGMENTS: int = 8
"""Number of segments for pinned ghost ring markers."""

SELECTED_RING_SCALE: float = 1.4
"""Radius multiplier for selected ghost highlight ring."""

PINNED_RING_SCALE: float = 1.2
"""Radius multiplier for pinned ghost indicator ring."""

DEFAULT_GHOST_RADIUS: float = 0.05
"""Default world-space radius for ghost markers."""

DEFAULT_ARC_WIDTH: float = 2.0
"""Default line width for the motion arc."""

DEFAULT_FPS: float = 24.0
"""Default frames per second for ballistic calculations."""

SPACING_TICK_LENGTH: float = 0.03
"""World-space length of spacing tick marks shown along motion arcs."""

ACCEL_COLOR: tuple[float, float, float, float] = (0.2, 0.9, 0.3, 0.8)
"""Color for acceleration markers (green = speeding up)."""

DECEL_COLOR: tuple[float, float, float, float] = (0.9, 0.2, 0.2, 0.8)
"""Color for deceleration markers (red = slowing down)."""

ACCEL_TICK_LENGTH: float = 0.04
"""World-space length of acceleration tick marks (slightly larger than spacing ticks)."""

ACCEL_THRESHOLD: float = 0.001
"""Minimum acceleration magnitude to display a marker. Below this, acceleration
is considered negligible and no marker is drawn. Adjust for scene scale."""

HOVER_RING_SCALE: float = 1.3
"""Radius multiplier for hover highlight ring."""

HOVER_RING_COLOR: tuple[float, float, float, float] = (0.8, 0.9, 1.0, 0.9)
"""Default color for hover highlight ring (overridden by settings)."""

KEYFRAME_MARKER_SCALE: float = 1.5
"""Radius multiplier for keyframe markers (larger than ghost circles)."""

KEYFRAME_MARKER_SEGMENTS: int = 4
"""Number of segments for keyframe diamond shape (4 = diamond)."""

DEFAULT_KEYFRAME_MARKER_COLOR: tuple[float, float, float, float] = (1.0, 0.85, 0.0, 0.90)
"""Default color for keyframe position markers on the trail."""

FRAME_LABEL_FONT_SIZE: int = 14
"""Font size for frame number labels shown on hover."""

FRAME_LABEL_OFFSET_PX: tuple[int, int] = (12, 12)
"""Pixel offset from ghost screen position for frame label placement."""

BALLISTIC_PREVIEW_SCALE: float = 0.01
"""Scale factor converting scene-unit gravity displacement to visual preview size."""

# HUD constants — Mode Label and Progress Ring
MODE_LABEL_FONT_SIZE: int = 13
"""Font size for the persistent mode label HUD."""

MODE_LABEL_MARGIN_PX: tuple[int, int] = (14, 14)
"""Pixel margin from the top-left corner for the mode label HUD."""

PROGRESS_RING_RADIUS_PX: float = 18.0
"""Screen-space radius (pixels) of the bake progress ring."""

PROGRESS_RING_SEGMENTS: int = 32
"""Number of line segments in the progress ring circle."""

PROGRESS_RING_COLOR: tuple[float, float, float, float] = (0.3, 0.85, 1.0, 0.9)
"""Color for the bake progress ring."""

PROGRESS_RING_BG_COLOR: tuple[float, float, float, float] = (0.15, 0.15, 0.15, 0.5)
"""Background circle color for the bake progress ring."""

PROGRESS_RING_MARGIN_PX: tuple[int, int] = (14, 50)
"""Pixel margin from the top-left corner for the progress ring center."""


# ---------------------------------------------------------------------------
# Geometry generation helpers
# ---------------------------------------------------------------------------

def _build_circle_line_indices(segments: int) -> list[tuple[int, int]]:
    """Build edge indices for a circle outline.

    Args:
        segments: Number of segments in the circle.

    Returns:
        list[tuple[int, int]]: Pairs of vertex indices forming line segments.
    """
    indices = []
    for i in range(segments):
        indices.append((i, (i + 1) % segments))
    return indices


def _extract_billboard_axes(view_matrix) -> tuple[Vector, Vector]:
    """Extract the right and up vectors from a view matrix.

    Computing ``view_matrix.inverted()`` is non-trivial.  This function
    should be called **once per draw frame** and the results passed to
    all geometry builders.

    Args:
        view_matrix: The region's view matrix (rv3d.view_matrix).

    Returns:
        tuple[Vector, Vector]: (right, up) unit vectors in world space.
    """
    inv_view = view_matrix.inverted()
    right = Vector((inv_view[0][0], inv_view[0][1], inv_view[0][2])).normalized()
    up = Vector((inv_view[1][0], inv_view[1][1], inv_view[1][2])).normalized()
    return right, up


def _build_3d_diamond_verts(
    center: Vector,
    radius: float,
    bb_right: Vector,
    bb_up: Vector,
) -> list[Vector]:
    """Generate a view-facing diamond (4-point rotated square) in 3D space.

    Used for keyframe markers to visually distinguish them from ghost circles.

    Args:
        center: World-space center of the diamond.
        radius: Radius (distance from center to each vertex).
        bb_right: Pre-computed billboard right vector (from ``_extract_billboard_axes``).
        bb_up: Pre-computed billboard up vector.

    Returns:
        list[Vector]: 4 world-space vertices forming the diamond outline.
    """
    return [
        center + bb_up * radius,            # top
        center + bb_right * radius,          # right
        center - bb_up * radius,             # bottom
        center - bb_right * radius,          # left
    ]


def _build_3d_circle_verts(
    center: Vector,
    radius: float,
    bb_right: Vector,
    bb_up: Vector,
    segments: int = SPHERE_SEGMENTS,
) -> list[Vector]:
    """Generate a view-facing (billboard) circle in 3D space.

    The circle is oriented perpendicular to the view direction so it
    always faces the camera, like a billboard.

    Args:
        center: World-space center of the circle.
        radius: Radius in world-space units.
        bb_right: Pre-computed billboard right vector (from ``_extract_billboard_axes``).
        bb_up: Pre-computed billboard up vector.
        segments: Number of segments.

    Returns:
        list[Vector]: World-space vertices for the circle outline.
    """
    verts = []
    for i in range(segments):
        angle = 2.0 * math.pi * i / segments
        offset = bb_right * (radius * math.cos(angle)) + bb_up * (radius * math.sin(angle))
        verts.append(center + offset)
    return verts


# ---------------------------------------------------------------------------
# Color utilities
# ---------------------------------------------------------------------------

def _get_level_color(level: int) -> tuple[float, float, float, float]:
    """Get the display color for a ghost generation level.

    Reads from addon preferences if available, otherwise uses defaults.

    Args:
        level: Generation level (1-based).

    Returns:
        tuple: RGBA color.
    """
    # Try to read from addon preferences
    try:
        prefs = bpy.context.preferences.addons.get("ghost_tool")
        if prefs and hasattr(prefs.preferences, f"level_{level}_color"):
            color = getattr(prefs.preferences, f"level_{level}_color", (1.0, 1.0, 1.0, 1.0))
            return (color[0], color[1], color[2], 0.85)
    except Exception as exc:
        warn(f"Error getting level color: {exc}")

    # Fall back to defaults
    idx = max(0, min(level - 1, len(DEFAULT_LEVEL_COLORS) - 1))
    return DEFAULT_LEVEL_COLORS[idx]


def _desaturate_color(
    color: tuple[float, float, float, float],
    factor: float = 0.5,
) -> tuple[float, float, float, float]:
    """Desaturate an RGBA color for snapshot overlay display.

    Args:
        color: Input RGBA color.
        factor: Desaturation amount (0 = no change, 1 = full grayscale).

    Returns:
        tuple: Desaturated RGBA color.
    """
    gray = 0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2]
    red = color[0] + (gray - color[0]) * factor
    green = color[1] + (gray - color[1]) * factor
    blue = color[2] + (gray - color[2]) * factor
    return (red, green, blue, color[3] * 0.5)


def _lerp_color_rgba(
    slow_speed_color: tuple[float, float, float, float],
    fast_speed_color: tuple[float, float, float, float],
    interpolation_factor: float,
) -> tuple[float, float, float, float]:
    """Linearly interpolate between two RGBA colors.

    Args:
        slow_speed_color: Color for slow motion (dense spacing).
        fast_speed_color: Color for fast motion (sparse spacing).
        interpolation_factor: Interpolation factor (0.0 = slow_speed_color, 1.0 = fast_speed_color).

    Returns:
        tuple: Interpolated RGBA color.
    """
    interpolation_factor = max(0.0, min(1.0, interpolation_factor))
    return (
        slow_speed_color[0] + (fast_speed_color[0] - slow_speed_color[0]) * interpolation_factor,
        slow_speed_color[1] + (fast_speed_color[1] - slow_speed_color[1]) * interpolation_factor,
        slow_speed_color[2] + (fast_speed_color[2] - slow_speed_color[2]) * interpolation_factor,
        slow_speed_color[3] + (fast_speed_color[3] - slow_speed_color[3]) * interpolation_factor,
    )


# ---------------------------------------------------------------------------
# GPU Drawing Helpers
# ---------------------------------------------------------------------------

def _draw_batch(shader, batch, color):
    """Bind shader, set color uniform, and draw the batch.

    Args:
        shader: GPU shader instance.
        batch: GPU batch to draw.
        color: RGBA color tuple (r, g, b, a) each in 0–1 range.
    """
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)


# ---------------------------------------------------------------------------
# Main 3D Draw Handler
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Ghost coloring helpers
# ---------------------------------------------------------------------------

# Time-based colors: past = blue, future = orange
# These are fallback defaults; user-configurable colors are in scene settings.
PAST_GHOST_COLOR: tuple[float, float, float, float] = (0.25, 0.55, 1.0, 0.85)
"""Color for ghosts before the current frame (past, historical positions)."""
FUTURE_GHOST_COLOR: tuple[float, float, float, float] = (1.0, 0.55, 0.15, 0.85)
"""Color for ghosts after the current frame (future, predictive positions)."""
CURRENT_GHOST_COLOR: tuple[float, float, float, float] = (0.2, 1.0, 0.4, 0.95)
"""Color for the ghost at the current frame."""

# Key/Inbetween default colors (overridden by scene settings)
KEY_GHOST_COLOR: tuple[float, float, float, float] = (1.0, 0.85, 0.0, 0.90)
"""Color for keyframe ghosts (generation level 0)."""
INBETWEEN_GHOST_COLOR: tuple[float, float, float, float] = (0.4, 0.75, 1.0, 0.80)
"""Color for interpolated/inbetween ghosts (generation level > 0)."""

# Ballistic preview colors
BALLISTIC_ARC_COLOR: tuple[float, float, float, float] = (0.8, 0.3, 1.0, 0.5)
"""Color for ballistic trajectory preview arc lines (magenta, semi-transparent)."""
BALLISTIC_MARKER_COLOR: tuple[float, float, float, float] = (0.8, 0.3, 1.0, 0.35)
"""Color for ballistic prediction markers along the arc (magenta, more transparent)."""

# Arc style speed-coloring: slow motion (dense spacing) to fast motion (sparse spacing)
SLOW_SPEED_COLOR: tuple[float, float, float, float] = (0.2, 0.4, 1.0, 0.8)
"""Color for slow motion on speed-colored arcs and ticks (blue)."""
FAST_SPEED_COLOR: tuple[float, float, float, float] = (1.0, 0.3, 0.1, 0.8)
"""Color for fast motion on speed-colored arcs and ticks (red-orange)."""

# Rainbow palette (12 stops) for rainbow color mode spanning red → magenta → red
# Ghosts are colored based on their temporal position across the timeline.
RAINBOW_PALETTE: list[tuple[float, float, float, float]] = [
    (1.0, 0.0, 0.0, 0.85),    # Red
    (1.0, 0.5, 0.0, 0.85),    # Orange
    (1.0, 1.0, 0.0, 0.85),    # Yellow
    (0.5, 1.0, 0.0, 0.85),    # Lime
    (0.0, 1.0, 0.0, 0.85),    # Green
    (0.0, 1.0, 0.5, 0.85),    # Spring
    (0.0, 1.0, 1.0, 0.85),    # Cyan
    (0.0, 0.5, 1.0, 0.85),    # Azure
    (0.0, 0.0, 1.0, 0.85),    # Blue
    (0.5, 0.0, 1.0, 0.85),    # Violet
    (1.0, 0.0, 1.0, 0.85),    # Magenta
    (1.0, 0.0, 0.5, 0.85),    # Rose
]


def _apply_falloff(t: float, curve_type: str) -> float:
    """Apply a falloff curve to a normalised distance value.

    Args:
        t: Normalised distance (0 = at cursor, 1 = farthest).
        curve_type: One of "LINEAR", "SMOOTH", "EXPONENTIAL", "CONSTANT".
                    CONSTANT returns 0.0 (no distance-based fade applied).

    Returns:
        float: Adjusted distance factor (0–1), where 0 = no fade (ghosts full opacity),
               1 = maximum fade (ghosts fully transparent).
    """
    t = max(0.0, min(t, 1.0))
    if curve_type == "CONSTANT":
        return 0.0
    elif curve_type == "SMOOTH":
        # Smooth-step: 3t² - 2t³
        return t * t * (3.0 - 2.0 * t)
    elif curve_type == "EXPONENTIAL":
        # Quick initial fade, slow tail
        return 1.0 - math.pow(1.0 - t, 3.0)
    else:
        # LINEAR (default)
        return t


def _get_ghost_color(
    ghost: Ghost,
    current_frame: float,
    frame_range: tuple[float, float],
    color_mode: str,
    fade_factor: float,
    settings=None,
) -> tuple[float, float, float, float]:
    """Compute the color for a ghost based on the active coloring mode.

    Args:
        ghost: The ghost to color.
        current_frame: The scene's current frame.
        frame_range: (min_frame, max_frame) of all ghosts for normalizing.
        color_mode: One of "LEVEL", "TIME", "FADE", "RAINBOW", "KEY_INBETWEEN".
        fade_factor: How aggressively alpha fades with distance (0-1).
        settings: Optional GhostToolSceneSettings for user colors and falloff.

    Returns:
        RGBA color tuple.
    """
    if color_mode == "LEVEL":
        return _get_level_color(ghost.generation_level)

    # Read user-configurable values from settings
    min_alpha = settings.ghost_min_alpha
    falloff_curve = settings.ghost_falloff_curve

    delta = ghost.frame - current_frame
    range_width = max(frame_range[1] - frame_range[0], 1.0)
    normalized_distance = min(abs(delta) / range_width, 1.0)  # 0 = at cursor, 1 = farthest
    falloff_distance = _apply_falloff(normalized_distance, falloff_curve)

    if color_mode == "TIME":
        # User-configurable past/future colors
        past_rgb = tuple(settings.ghost_past_color)
        future_rgb = tuple(settings.ghost_future_color)
        base = (*past_rgb, 0.85) if delta < 0 else (*future_rgb, 0.85)
        alpha = base[3] * (1.0 - falloff_distance * fade_factor)
        return (base[0], base[1], base[2], max(alpha, min_alpha))

    elif color_mode == "FADE":
        # White/bright near cursor, fading to dim with distance
        brightness = 1.0 - falloff_distance * fade_factor * 0.7
        alpha = 0.9 * (1.0 - falloff_distance * fade_factor)
        return (brightness, brightness, brightness, max(alpha, min_alpha))

    elif color_mode == "RAINBOW":
        # Position on rainbow based on normalized time position
        time_normalized = (ghost.frame - frame_range[0]) / range_width
        palette_idx_float = time_normalized * (len(RAINBOW_PALETTE) - 1)
        palette_idx = int(palette_idx_float)
        palette_fraction = palette_idx_float - palette_idx
        palette_idx = max(0, min(palette_idx, len(RAINBOW_PALETTE) - 2))
        color_1 = RAINBOW_PALETTE[palette_idx]
        color_2 = RAINBOW_PALETTE[palette_idx + 1]
        red = color_1[0] + (color_2[0] - color_1[0]) * palette_fraction
        green = color_1[1] + (color_2[1] - color_1[1]) * palette_fraction
        blue = color_1[2] + (color_2[2] - color_1[2]) * palette_fraction
        alpha = 0.85 * (1.0 - falloff_distance * fade_factor * 0.3)
        return (red, green, blue, max(alpha, min_alpha))

    elif color_mode == "KEY_INBETWEEN":
        # Keyframe ghosts (level 0) get key_color, all others get inbetween_color
        is_key = (ghost.generation_level == 0)
        if is_key:
            rgb = tuple(settings.ghost_key_color)
        else:
            rgb = tuple(settings.ghost_inbetween_color)
        base_alpha = 0.90 if is_key else 0.80
        alpha = base_alpha * (1.0 - falloff_distance * fade_factor)
        return (rgb[0], rgb[1], rgb[2], max(alpha, min_alpha))

    # Fallback
    return _get_level_color(ghost.generation_level)


def _build_marker_batches(shader, store, all_ghost_list, settings, ghost_radius,
                          bb_right, bb_up, current_frame, frame_range):
    batches = []
    color_mode = settings.ghost_color_mode
    fade_factor = settings.ghost_fade_factor
    # --- Draw ghost markers ---
    # Preserve level grouping and rounded color buckets.
    if color_mode == "LEVEL":
        # Original level-based batching
        # Levels: 0 = keyframe ghosts, 1-5 = subdivision levels
        for level in range(0, MAX_SUBDIVISION_LEVEL + 2):
            if level > 0 and not settings.is_level_visible(level):
                continue

            ghosts_at_level = store.filter_by_level(level) if level > 0 else [
                ghost for ghost in all_ghost_list if ghost.generation_level == 0
            ]
            if not ghosts_at_level:
                continue

            level_color = _get_level_color(max(level, 1))

            all_verts: list[Vector] = []
            all_indices: list[tuple[int, int]] = []

            for ghost in ghosts_at_level:
                vertex_offset = len(all_verts)
                circle_verts = _build_3d_circle_verts(
                    ghost.world_position, ghost_radius, bb_right, bb_up
                )
                all_verts.extend(circle_verts)
                for a, b in _get_circle_indices(SPHERE_SEGMENTS):
                    all_indices.append((vertex_offset + a, vertex_offset + b))

            if all_verts:
                batch = batch_for_shader(
                    shader, 'LINES',
                    {"pos": [tuple(vertex) for vertex in all_verts]},
                    indices=all_indices,
                )
                batches.append((batch, level_color))

    else:
        # Per-ghost coloring (TIME, FADE, RAINBOW, KEY_INBETWEEN)
        # Batching strategy: group ghosts by color bucket (rounded to 2 decimals)
        # to reduce GPU draw calls to the number of color buckets.
        color_buckets: dict[tuple, tuple[list, list]] = {}

        for ghost in all_ghost_list:
            color = _get_ghost_color(
                ghost, current_frame, frame_range, color_mode, fade_factor,
                settings=settings,
            )

            # Adjust radius: ghosts closer to playhead are slightly larger
            range_width = max(frame_range[1] - frame_range[0], 1.0)
            normalized_distance = min(abs(ghost.frame - current_frame) / range_width, 1.0)
            adjusted_radius = ghost_radius * (1.0 + 0.5 * (1.0 - normalized_distance))

            color_key = (round(color[0], 2), round(color[1], 2), round(color[2], 2), round(color[3], 2))
            if color_key not in color_buckets:
                color_buckets[color_key] = ([], [])

            verts, indices = color_buckets[color_key]
            vertex_offset = len(verts)
            circle_verts = _build_3d_circle_verts(
                ghost.world_position, adjusted_radius, bb_right, bb_up
            )
            verts.extend(tuple(v) for v in circle_verts)
            for a, b in _get_circle_indices(SPHERE_SEGMENTS):
                indices.append((vertex_offset + a, vertex_offset + b))

        # One draw call per unique color bucket
        for color_key, (verts, indices) in color_buckets.items():
            if verts:
                batch = batch_for_shader(
                    shader, 'LINES',
                    {"pos": verts},
                    indices=indices,
                )
                batches.append((batch, color_key))
    return tuple(batches)


def _get_marker_batches(shader, store, ghosts, settings, radius, right, up,
                        current_frame, frame_range, context_key=None):
    # Ghost fields can change in place during drag/API edits without a store
    # version bump. Compare actual render inputs, never just the version.
    key = (
        context_key,
        tuple((tuple(g.world_position), g.frame, g.generation_level) for g in ghosts),
        tuple(right), tuple(up), radius, current_frame, frame_range,
        settings.ghost_color_mode, settings.ghost_fade_factor,
        settings.ghost_min_alpha, settings.ghost_falloff_curve,
        tuple(settings.ghost_past_color), tuple(settings.ghost_future_color),
        tuple(settings.ghost_key_color), tuple(settings.ghost_inbetween_color),
        tuple(settings.is_level_visible(i) for i in range(1, MAX_SUBDIVISION_LEVEL + 2)),
        tuple(_get_level_color(i) for i in range(1, MAX_SUBDIVISION_LEVEL + 2)),
    )
    if key != _batch_cache.key:
        batches = _build_marker_batches(shader, store, ghosts, settings, radius,
                                        right, up, current_frame, frame_range)
        _batch_cache.key, _batch_cache.batches = key, batches
    return _batch_cache.batches


def draw_ghosts_3d(context: bpy.types.Context) -> None:
    """Main 3D viewport draw callback for all ghost visualization.

    Supports multiple coloring modes (level, time, fade, rainbow),
    proximity-based alpha falloff, full-timeline arc lines, and
    speed-colored trajectory trails.

    When live mode is enabled, this function also triggers the pipeline
    to regenerate ghosts before drawing (throttled to avoid perf issues).

    Args:
        context: The current Blender context.
    """
    from . import ghost_data

    scene = getattr(context, 'scene', None)

    # Check if ghost display is active
    if not hasattr(scene, 'ghost_tool') or not scene.ghost_tool.is_active:
        debug("Ghost overlay inactive — skipping draw")
        return

    settings = scene.ghost_tool

    # Set flag to indicate we're in a draw handler
    ghost_data._IN_DRAW_HANDLER = True
    try:
        _draw_ghosts_3d_impl(context, settings, scene)
    finally:
        # Clear flag when exiting draw handler
        ghost_data._IN_DRAW_HANDLER = False


def _draw_ghosts_3d_impl(context: bpy.types.Context, settings, scene: bpy.types.Scene) -> None:
    """Internal implementation of draw_ghosts_3d, called with draw handler flag set.

    Args:
        context: The current Blender context.
        settings: The GhostToolSceneSettings.
        scene: The Blender scene.
    """
    # NOTE: Live update generation is now handled by bpy.app.timers
    # (scheduled from frame_change_post handler), NOT from the draw handler.
    # Calling scene.frame_set() from a draw handler is illegal in Blender
    # and was the root cause of live updates silently failing.

    # Check for a staging store from an in-progress bake (Preview Skeleton feature).
    # When _BAKE_IN_PROGRESS is True and _staging_store is populated, render from
    # the staging store so the animator sees partial results while the bake runs.
    try:
        from . import ghost_pipeline as _gp
        if _gp._BAKE_IN_PROGRESS and _gp._staging_store is not None and len(_gp._staging_store) > 0:
            store = _gp._staging_store
        else:
            store = GhostStore.get(scene)
    except Exception:
        store = GhostStore.get(scene)

    if len(store) == 0:
        return

    # We need the 3D region's view data for billboard calculations
    region = context.region
    region_3d = context.region_data
    if not region_3d:
        return

    # Get the shader for 3D uniform color drawing
    try:
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    except Exception as exc:
        warn(f"Failed to load GPU shader: {exc}")
        return

    gpu.state.blend_set('ALPHA')
    gpu.state.depth_test_set('LESS_EQUAL')
    gpu.state.line_width_set(2.0)
    try:
        ghost_radius = DEFAULT_GHOST_RADIUS
        try:
            prefs = bpy.context.preferences.addons.get("ghost_tool")
            if prefs and hasattr(prefs.preferences, "ghost_radius"):
                ghost_radius = prefs.preferences.ghost_radius
        except Exception as exc:
            debug(f"Failed to read ghost radius preference: {exc}")

        view_matrix = region_3d.view_matrix
        bb_right, bb_up = _extract_billboard_axes(view_matrix)
        current_frame = scene.frame_current
        color_mode = settings.ghost_color_mode
        fade_factor = settings.ghost_fade_factor

        # Use cached frame range from store (avoids O(n) min/max every frame)
        all_ghost_list = list(store)
        frame_range = store.frame_range

        show_markers = settings.show_cached_markers
        if show_markers:
            for batch, color in _get_marker_batches(
                shader, store, all_ghost_list, settings, ghost_radius, bb_right, bb_up,
                current_frame, frame_range,
                (context.window.as_pointer(), region.as_pointer()),
            ):
                _draw_batch(shader, batch, color)

        # --- Draw selected ghost highlights (SessionState is the single source of truth) ---
        session = SessionState.get(scene)
        all_selected = {g.uid: g for g in all_ghost_list if session.is_selected(g.uid)}

        if show_markers and all_selected:
            all_verts = []
            all_indices = []
            for ghost in all_selected.values():
                vertex_offset = len(all_verts)
                circle_verts = _build_3d_circle_verts(
                    ghost.world_position, ghost_radius * SELECTED_RING_SCALE, bb_right, bb_up
                )
                all_verts.extend(circle_verts)
                for a, b in _get_circle_indices(SPHERE_SEGMENTS):
                    all_indices.append((vertex_offset + a, vertex_offset + b))

            if all_verts:
                batch = batch_for_shader(
                    shader, 'LINES',
                    {"pos": [tuple(vertex) for vertex in all_verts]},
                    indices=all_indices,
                )
                _draw_batch(shader, batch, SELECTED_HIGHLIGHT_COLOR)

        # --- Draw hover highlight ring ---
        if show_markers and session.hovered_ghost_uid:
            hovered_ghost = store.get_by_uid(session.hovered_ghost_uid)
            if hovered_ghost:
                hc = settings.hover_highlight_color
                hover_color = tuple(hc) if len(hc) == 4 else HOVER_RING_COLOR

                hover_verts = _build_3d_circle_verts(
                    hovered_ghost.world_position, ghost_radius * HOVER_RING_SCALE,
                    bb_right, bb_up,
                )
                hover_indices = _get_circle_indices(SPHERE_SEGMENTS)
                batch = batch_for_shader(
                    shader, 'LINES',
                    {"pos": [tuple(v) for v in hover_verts]},
                    indices=hover_indices,
                )
                _draw_batch(shader, batch, hover_color)

        # --- Draw keyframe markers (diamonds) ---
        show_kf_markers = settings.show_keyframe_markers
        if show_markers and show_kf_markers:
            kmc = settings.keyframe_marker_color
            kf_marker_color = tuple(kmc) if len(kmc) == 4 else DEFAULT_KEYFRAME_MARKER_COLOR

            kf_verts: list[tuple] = []
            kf_indices: list[tuple[int, int]] = []

            # Find ghosts that coincide with keyframes (generation_level == 0
            # or frame matches a keyframe on the fcurve within snap threshold)
            for ghost in all_ghost_list:
                is_keyframe_ghost = (ghost.generation_level == 0)
                if not is_keyframe_ghost:
                    # Quick check: is the ghost's parent_frame_a == parent_frame_b?
                    # That indicates a keyframe-only ghost.
                    if abs(ghost.parent_frame_a - ghost.parent_frame_b) < 0.01:
                        is_keyframe_ghost = True

                if is_keyframe_ghost:
                    vertex_offset = len(kf_verts)
                    diamond_verts = _build_3d_diamond_verts(
                        ghost.world_position,
                        ghost_radius * KEYFRAME_MARKER_SCALE,
                        bb_right, bb_up,
                    )
                    for v in diamond_verts:
                        kf_verts.append(tuple(v))
                    # Diamond edges: top→right, right→bottom, bottom→left, left→top
                    kf_indices.append((vertex_offset + 0, vertex_offset + 1))
                    kf_indices.append((vertex_offset + 1, vertex_offset + 2))
                    kf_indices.append((vertex_offset + 2, vertex_offset + 3))
                    kf_indices.append((vertex_offset + 3, vertex_offset + 0))

            if kf_verts:
                gpu.state.line_width_set(2.5)
                batch = batch_for_shader(
                    shader, 'LINES',
                    {"pos": kf_verts},
                    indices=kf_indices,
                )
                _draw_batch(shader, batch, kf_marker_color)
                gpu.state.line_width_set(2.0)

        # --- Draw key bookend markers (prev/next keyframes outside ghost range) ---
        # IMPORTANT: Bookend positions are estimated from the nearest ghost's
        # world position, NOT from scene.frame_set() — draw handlers must never
        # call frame_set() as it triggers depsgraph re-evaluation during draw.
        show_bookends = settings.show_key_bookends
        if show_markers and show_bookends and all_ghost_list:
            bookend_color = tuple(settings.key_bookend_color)
            if len(bookend_color) != 4:
                bookend_color = (0.8, 0.8, 0.8, 0.5)

            # Find the frame range covered by existing ghosts
            ghost_frame_min = min(g.frame for g in all_ghost_list)
            ghost_frame_max = max(g.frame for g in all_ghost_list)

            # Collect bookend keyframe positions from f-curves
            bookend_verts: list[tuple] = []
            bookend_indices: list[tuple[int, int]] = []

            # Get unique object/bone/channel combos from existing ghosts
            seen_combos: set[tuple[str, str, str]] = set()
            for ghost in all_ghost_list:
                combo = (ghost.object_name, ghost.bone_name, ghost.channel)
                if combo in seen_combos:
                    continue
                seen_combos.add(combo)

                obj = bpy.data.objects.get(ghost.object_name)
                if obj is None:
                    continue

                fcurve = fcurve_utils.resolve_fcurve(obj, ghost.bone_name, ghost.channel)
                if fcurve is None:
                    continue

                # Find keyframe immediately before ghost_frame_min
                prev_kf_frame = None
                next_kf_frame = None
                for kp in sorted(fcurve.keyframe_points, key=lambda k: k.co.x):
                    if kp.co.x < ghost_frame_min - 0.5:
                        prev_kf_frame = kp.co.x
                    elif kp.co.x > ghost_frame_max + 0.5 and next_kf_frame is None:
                        next_kf_frame = kp.co.x

                # Draw bookend diamonds at prev/next keyframe positions.
                # Use the nearest ghost's world position as an approximation
                # rather than calling scene.frame_set() inside the draw handler.
                chain_ghosts = [g for g in all_ghost_list if g.object_name == ghost.object_name
                               and g.bone_name == ghost.bone_name and g.channel == ghost.channel]
                chain_ghosts.sort(key=lambda g: g.frame)

                for kf_frame in (prev_kf_frame, next_kf_frame):
                    if kf_frame is None:
                        continue

                    # Estimate bookend position: evaluate the f-curve value at this
                    # frame and offset from the nearest ghost's position proportionally.
                    # This avoids calling scene.frame_set() inside the draw handler.
                    if kf_frame < ghost_frame_min:
                        nearest = chain_ghosts[0]
                    else:
                        nearest = chain_ghosts[-1]

                    # Read the f-curve values at the bookend frame and the nearest ghost frame
                    bookend_value = fcurve.evaluate(kf_frame)
                    nearest_value = fcurve.evaluate(nearest.frame)
                    value_delta = bookend_value - nearest_value

                    # Estimate world position by shifting the nearest ghost's position
                    # along the appropriate axis based on the f-curve value delta
                    world_pos = nearest.world_position.copy()
                    channel_lower = ghost.channel.lower()
                    if channel_lower.endswith(".x"):
                        world_pos.x += value_delta
                    elif channel_lower.endswith(".y"):
                        world_pos.y += value_delta
                    elif channel_lower.endswith(".z"):
                        world_pos.z += value_delta

                    vertex_offset = len(bookend_verts)
                    diamond_verts = _build_3d_diamond_verts(
                        world_pos,
                        ghost_radius * KEYFRAME_MARKER_SCALE * 0.8,
                        bb_right, bb_up,
                    )
                    for v in diamond_verts:
                        bookend_verts.append(tuple(v))
                    bookend_indices.append((vertex_offset + 0, vertex_offset + 1))
                    bookend_indices.append((vertex_offset + 1, vertex_offset + 2))
                    bookend_indices.append((vertex_offset + 2, vertex_offset + 3))
                    bookend_indices.append((vertex_offset + 3, vertex_offset + 0))

            if bookend_verts:
                gpu.state.line_width_set(2.0)
                batch = batch_for_shader(
                    shader, 'LINES',
                    {"pos": bookend_verts},
                    indices=bookend_indices,
                )
                _draw_batch(shader, batch, bookend_color)
                gpu.state.line_width_set(1.0)

        # --- Draw pinned ghost indicators ---
        pinned_ghosts = store.get_pinned()
        if show_markers and pinned_ghosts:
            all_verts = []
            all_indices = []
            for ghost in pinned_ghosts:
                vertex_offset = len(all_verts)
                circle_verts = _build_3d_circle_verts(
                    ghost.world_position, ghost_radius * PINNED_RING_SCALE, bb_right, bb_up,
                    segments=PINNED_RING_SEGMENTS,
                )
                all_verts.extend(circle_verts)
                for i in range(PINNED_RING_SEGMENTS):
                    all_indices.append((vertex_offset + i, vertex_offset + (i + 1) % PINNED_RING_SEGMENTS))

            if all_verts:
                batch = batch_for_shader(
                    shader, 'LINES',
                    {"pos": [tuple(vertex) for vertex in all_verts]},
                    indices=all_indices,
                )
                _draw_batch(shader, batch, PINNED_RING_COLOR)

        # --- Draw arc lines (trajectory trails) ---
        show_arcs = settings.show_arc_lines or settings.show_motion_arc
        if show_arcs:
            arc_style = settings.arc_line_style
            _draw_arc_lines(
                store, shader, settings, current_frame, frame_range, arc_style, fade_factor
            )

        # --- Draw spacing ticks ---
        if settings.show_spacing_ticks:
            _draw_spacing_ticks_impl(store, shader, bb_up, settings)

        # --- Draw acceleration markers ---
        if settings.show_acceleration_markers:
            _draw_acceleration_markers(store, shader, bb_up, bb_right, settings)

        # --- Draw snapshot overlays ---
        _draw_snapshot_overlays(context, shader, bb_right, bb_up, ghost_radius)

        # --- Draw ballistic preview ---
        if settings.show_ballistic_preview:
            _draw_ballistic_preview(
                store, shader, bb_right, bb_up, ghost_radius, settings, current_frame
            )

        # --- Draw physics suggestion preview markers ---
        # Shared preview state is written by either GHOST_OT_physics_suggest
        # (parabolic arc correction) or GHOST_OT_archetype_bake (when
        # show_archetype_preview is active).  The draw handler is agnostic
        # to the source — it reads one list and draws diamonds.
        try:
            from .physics_suggest import get_physics_preview
            preview_data = get_physics_preview()
            if preview_data:
                # Green tint for physics suggest; cyan tint for archetype preview.
                # Distinguish the two sources so the animator knows which is active.
                archetype_preview_on = getattr(settings, "show_archetype_preview", False)
                preview_color = (
                    (0.2, 0.9, 1.0, 0.65)   # cyan  — archetype preview
                    if archetype_preview_on
                    else (0.3, 1.0, 0.3, 0.6)  # green — physics suggest
                )
                pv_verts: list[tuple] = []
                pv_indices: list[tuple[int, int]] = []

                for entry in preview_data:
                    suggested_pos = entry.get("suggested_position")
                    if suggested_pos is None:
                        continue

                    vertex_offset = len(pv_verts)
                    diamond_verts = _build_3d_diamond_verts(
                        suggested_pos,
                        ghost_radius * 0.7,
                        bb_right, bb_up,
                    )
                    for v in diamond_verts:
                        pv_verts.append(tuple(v))
                    pv_indices.append((vertex_offset, vertex_offset + 1))
                    pv_indices.append((vertex_offset + 1, vertex_offset + 2))
                    pv_indices.append((vertex_offset + 2, vertex_offset + 3))
                    pv_indices.append((vertex_offset + 3, vertex_offset))

                if pv_verts:
                    gpu.state.line_width_set(1.5)
                    batch = batch_for_shader(
                        shader, 'LINES',
                        {"pos": pv_verts},
                        indices=pv_indices,
                    )
                    _draw_batch(shader, batch, preview_color)
                    gpu.state.line_width_set(2.0)

        except ImportError:
            debug("Preview shader module not available for this feature")

        # --- Populate archetype preview when the toggle is on ---
        # Evaluated here (inside the draw callback's finally-guarded block) so
        # the overlay appears immediately when the toggle is enabled, without
        # requiring a separate operator invocation.
        # NOTE: draw handlers must not call scene.frame_set() — archetype
        # preview displaces existing ghost positions, never seeks new frames.
        #
        # Performance: recomputation is skipped when nothing has changed since
        # the last draw (same store version + same archetype settings).
        if getattr(settings, "show_archetype_preview", False):
            global _archetype_preview_cache_key
            try:
                archetype_name = getattr(settings, "archetype_active", "BOUNCE")
                amplitude = getattr(settings, "archetype_amplitude", 1.0)
                axis = getattr(settings, "archetype_axis", "Z").lower()
                cache_key = (
                    id(store), getattr(store, "version", 0),
                    tuple((g.frame, tuple(g.world_position)) for g in all_ghost_list),
                    archetype_name,
                    amplitude,
                    axis,
                )

                if cache_key != _archetype_preview_cache_key:
                    from .physics_suggest import _clear_physics_preview, _set_physics_preview
                    from .physics_archetypes import ARCHETYPES

                    archetype_fn = ARCHETYPES.get(archetype_name)
                    axis_idx = {"x": 0, "y": 1, "z": 2}.get(axis, 2)

                    if archetype_fn is not None and all_ghost_list:
                        sorted_preview_ghosts = sorted(all_ghost_list, key=lambda g: g.frame)
                        first_frame = sorted_preview_ghosts[0].frame
                        last_frame = sorted_preview_ghosts[-1].frame
                        total_frames = max(last_frame - first_frame, 1.0)

                        archetype_entries: list[dict] = []
                        for ghost in sorted_preview_ghosts:
                            t = (ghost.frame - first_frame) / total_frames
                            displacement = archetype_fn(t) * amplitude
                            preview_pos = ghost.world_position.copy()
                            preview_pos[axis_idx] += displacement
                            archetype_entries.append({"suggested_position": preview_pos})

                        # Mutual exclusion: clear before writing (contract in physics_suggest.py).
                        _clear_physics_preview()
                        _set_physics_preview(archetype_entries)
                        _archetype_preview_cache_key = cache_key

            except Exception as exc:
                debug(f"Archetype preview update error: {exc}")

        # --- Draw Visual Diff overlay ---
        if getattr(settings, "show_diff_overlay", False):
            try:
                from .diff_mode import draw_diff_overlay
                draw_diff_overlay(
                    context, store, shader, bb_right, bb_up, ghost_radius
                )
            except Exception as exc:
                debug(f"Diff overlay draw error: {exc}")

    finally:
        # Restore GPU state
        gpu.state.blend_set('NONE')
        gpu.state.depth_test_set('NONE')
        gpu.state.line_width_set(1.0)


# ---------------------------------------------------------------------------
# Motion Arc Drawing
# ---------------------------------------------------------------------------

def _draw_motion_arcs(
    store: GhostStore,
    shader,
    settings,
) -> None:
    """Legacy motion arc drawing — delegates to trajectory arcs."""
    _draw_arc_lines(
        store, shader, settings,
        bpy.context.scene.frame_current,
        (0.0, 1.0), 'SOLID', 0.7,
    )


def _draw_arc_lines(
    store: GhostStore,
    shader,
    settings,
    current_frame: float,
    frame_range: tuple[float, float],
    arc_style: str,
    fade_factor: float,
) -> None:
    """Draw trajectory arc lines through ghost chains.

    Supports three styles:
      - SOLID:  Single color line
      - SPEED:  Segments colored by velocity (blue=slow, red=fast)
      - FADE:   Line fades with distance from the current frame

    Args:
        store: The GhostStore with active ghosts.
        shader: GPU shader.
        settings: Scene settings.
        current_frame: The playhead position.
        frame_range: Min/max frame of all ghosts.
        arc_style: "SOLID", "SPEED", or "FADE".
        fade_factor: Alpha falloff strength.
    """
    # ── Skeleton View filter ────────────────────────────────────────────
    # When skeleton_view is enabled, only include root/spine bones.
    # This collapses the arc display to a clean spinal column trail.
    skeleton_view_active = getattr(settings, "show_skeleton_view", False)
    skeleton_bone_names: Optional[set[str]] = None
    if skeleton_view_active:
        custom_filter = getattr(settings, "skeleton_view_bone_filter", "").strip()
        if custom_filter:
            # User-specified comma-separated bone name substrings
            skeleton_bone_names = {s.strip().lower() for s in custom_filter.split(",") if s.strip()}
        else:
            # Built-in heuristic: bones whose names contain root/spine/pelvis/hip/chest keywords
            skeleton_bone_names = {"root", "spine", "pelvis", "hip", "chest", "torso", "cog", "center"}

    # Collect unique chains (object, bone combinations — merge channels for location)
    # Group by object+bone so we get one arc per bone, combining x/y/z
    bone_chains: dict[tuple[str, str], list[Ghost]] = {}

    for ghost in store:
        bone_lower = ghost.bone_name.lower()
        # Skeleton View: skip bones that don't match the filter set
        if skeleton_view_active and skeleton_bone_names is not None:
            if not any(kw in bone_lower for kw in skeleton_bone_names):
                continue
        key = (ghost.object_name, ghost.bone_name)
        if key not in bone_chains:
            bone_chains[key] = []
        bone_chains[key].append(ghost)

    arc_width = DEFAULT_ARC_WIDTH
    try:
        prefs = bpy.context.preferences.addons.get("ghost_tool")
        if prefs and hasattr(prefs.preferences, "arc_line_width"):
            arc_width = prefs.preferences.arc_line_width
    except Exception as exc:
        debug(f"Failed to read arc line width preference: {exc}")

    gpu.state.line_width_set(arc_width)

    range_width = max(frame_range[1] - frame_range[0], 1.0)

    for chain_key, ghosts in bone_chains.items():
        # Deduplicate by frame (multiple channels at same frame = same world pos)
        frame_to_pos: dict[float, Vector] = {}
        for g in ghosts:
            if g.frame not in frame_to_pos:
                frame_to_pos[g.frame] = g.world_position

        sorted_frames = sorted(frame_to_pos.keys())
        if len(sorted_frames) < 2:
            continue

        positions = [frame_to_pos[f] for f in sorted_frames]

        if arc_style == "SOLID":
            # Single color, one batch
            verts = [tuple(p) for p in positions]
            indices = [(i, i + 1) for i in range(len(verts) - 1)]
            batch = batch_for_shader(
                shader, 'LINES', {"pos": verts}, indices=indices,
            )
            _draw_batch(shader, batch, ARC_COLOR)

        elif arc_style == "SPEED":
            # Each segment colored by velocity: blue=slow, red=fast
            distances = []
            for i in range(len(positions) - 1):
                distance = (positions[i + 1] - positions[i]).length
                distances.append(distance)

            max_distance = max(distances) if distances else 1.0
            min_distance = min(distances) if distances else 0.0

            # Batch segments by color bucket to minimize draw calls
            speed_buckets: dict[tuple, tuple[list, list]] = {}
            for i in range(len(positions) - 1):
                distance = distances[i]
                interpolation_factor = (distance - min_distance) / (max_distance - min_distance) if max_distance > min_distance else 0.5
                color = _lerp_color_rgba(SLOW_SPEED_COLOR, FAST_SPEED_COLOR, interpolation_factor)
                color_key = (round(color[0], 2), round(color[1], 2), round(color[2], 2), round(color[3], 2))

                if color_key not in speed_buckets:
                    speed_buckets[color_key] = ([], [])
                verts, indices = speed_buckets[color_key]
                offset = len(verts)
                verts.append(tuple(positions[i]))
                verts.append(tuple(positions[i + 1]))
                indices.append((offset, offset + 1))

            for color_key, (verts, indices) in speed_buckets.items():
                if verts:
                    batch = batch_for_shader(
                        shader, 'LINES', {"pos": verts}, indices=indices,
                    )
                    _draw_batch(shader, batch, color_key)

        elif arc_style == "FADE":
            # Segments fade with distance from cursor
            # Batch segments by color bucket
            fade_buckets: dict[tuple, tuple[list, list]] = {}
            for i in range(len(sorted_frames) - 1):
                mid_frame = (sorted_frames[i] + sorted_frames[i + 1]) / 2.0
                normalized_distance = min(abs(mid_frame - current_frame) / range_width, 1.0)
                alpha = 0.8 * (1.0 - normalized_distance * fade_factor)
                color = (0.7, 0.7, 0.7, max(alpha, 0.05))
                color_key = (round(color[0], 2), round(color[1], 2), round(color[2], 2), round(color[3], 2))

                if color_key not in fade_buckets:
                    fade_buckets[color_key] = ([], [])
                verts, indices = fade_buckets[color_key]
                offset = len(verts)
                verts.append(tuple(positions[i]))
                verts.append(tuple(positions[i + 1]))
                indices.append((offset, offset + 1))

            for color_key, (verts, indices) in fade_buckets.items():
                if verts:
                    batch = batch_for_shader(
                        shader, 'LINES', {"pos": verts}, indices=indices,
                    )
                    _draw_batch(shader, batch, color_key)

    gpu.state.line_width_set(2.0)


# ---------------------------------------------------------------------------
# Spacing Tick Drawing
# ---------------------------------------------------------------------------

def _draw_spacing_ticks_impl(
    store: GhostStore,
    shader,
    bb_up: Vector,
    settings,
) -> None:
    """Draw tick marks along the motion arc showing frame spacing.

    Ticks are colored from slow motion (dense/blue) to fast motion (sparse/red-orange).
    Tick density visually represents acceleration: dense = slow, sparse = fast.

    Args:
        store: The GhostStore containing all active ghosts.
        shader: The GPU shader to use.
        bb_up: Billboard up axis (from _extract_billboard_axes).
        settings: The GhostToolSceneSettings property group.
    """

    # Collect chains by object, bone, and channel
    chains: dict[tuple[str, str, str], list[Ghost]] = {}
    for ghost in store:
        key = (ghost.object_name, ghost.bone_name, ghost.channel)
        if key not in chains:
            chains[key] = []
        chains[key].append(ghost)

    up_vector = bb_up

    for chain_key, ghosts in chains.items():
        ghosts.sort(key=lambda ghost: ghost.frame)
        if len(ghosts) < 2:
            continue

        # Compute spatial distances between consecutive ghosts
        distances = []
        for i in range(len(ghosts) - 1):
            distance = (ghosts[i + 1].world_position - ghosts[i].world_position).length
            distances.append(distance)

        if not distances:
            continue

        _max_d = max(distances)
        max_distance = _max_d if _max_d > 0 else 1.0
        min_distance = min(distances)

        # Accumulate ticks into color buckets for efficient batching
        tick_buckets: dict[tuple, tuple[list, list]] = {}

        for i, ghost in enumerate(ghosts):
            # Determine speed factor: use average of adjacent distances
            if i == 0:
                speed = distances[0] if distances else 0
            elif i >= len(distances):
                speed = distances[-1] if distances else 0
            else:
                speed = (distances[i - 1] + distances[i]) / 2.0

            # Normalize to [0, 1] range for color mapping
            if max_distance > min_distance:
                interpolation_factor = (speed - min_distance) / (max_distance - min_distance)
            else:
                interpolation_factor = 0.5

            color = _lerp_color_rgba(SLOW_SPEED_COLOR, FAST_SPEED_COLOR, interpolation_factor)
            color_key = (round(color[0], 2), round(color[1], 2), round(color[2], 2), round(color[3], 2))

            if color_key not in tick_buckets:
                tick_buckets[color_key] = ([], [])
            verts, indices = tick_buckets[color_key]
            offset = len(verts)

            ghost_position = ghost.world_position
            tick_top = ghost_position + up_vector * SPACING_TICK_LENGTH
            tick_bottom = ghost_position - up_vector * SPACING_TICK_LENGTH

            verts.append(tuple(tick_top))
            verts.append(tuple(tick_bottom))
            indices.append((offset, offset + 1))

        # Draw one batch per color bucket
        for color_key, (verts, indices) in tick_buckets.items():
            if verts:
                batch = batch_for_shader(
                    shader, 'LINES', {"pos": verts}, indices=indices,
                )
                _draw_batch(shader, batch, color_key)


def _draw_acceleration_markers(
    store: GhostStore,
    shader,
    bb_up: Vector,
    bb_right: Vector,
    settings,
) -> None:
    """Draw acceleration/deceleration markers along the motion arc.

    Computes velocity between consecutive ghost pairs, then acceleration
    as the change in velocity. Draws upward green ticks for acceleration
    and downward red ticks for deceleration.

    Args:
        store: The GhostStore containing all active ghosts.
        shader: The GPU shader to use.
        bb_up: Billboard up axis.
        bb_right: Billboard right axis.
        settings: The GhostToolSceneSettings property group.
    """
    # Collect chains by object and bone (ignore channel for position)
    bone_chains: dict[tuple[str, str], list[Ghost]] = {}
    for ghost in store:
        key = (ghost.object_name, ghost.bone_name)
        if key not in bone_chains:
            bone_chains[key] = []
        bone_chains[key].append(ghost)

    accel_verts: list[tuple] = []
    accel_indices: list[tuple[int, int]] = []
    decel_verts: list[tuple] = []
    decel_indices: list[tuple[int, int]] = []

    for chain_key, ghosts in bone_chains.items():
        # Deduplicate by frame
        frame_to_pos: dict[float, Vector] = {}
        for g in ghosts:
            if g.frame not in frame_to_pos:
                frame_to_pos[g.frame] = g.world_position

        sorted_frames = sorted(frame_to_pos.keys())
        if len(sorted_frames) < 3:
            continue

        positions = [frame_to_pos[f] for f in sorted_frames]

        # Compute velocities (distance between consecutive positions)
        velocities = []
        for i in range(len(positions) - 1):
            dt = sorted_frames[i + 1] - sorted_frames[i]
            if dt > 0:
                vel = (positions[i + 1] - positions[i]).length / dt
            else:
                vel = 0.0
            velocities.append(vel)

        # Compute accelerations (change in velocity)
        # acceleration[i] corresponds to the ghost at sorted_frames[i+1]
        for i in range(len(velocities) - 1):
            accel = velocities[i + 1] - velocities[i]

            # Skip negligible accelerations
            if abs(accel) < ACCEL_THRESHOLD:
                continue

            # The marker goes at the ghost between the two velocity samples
            ghost_pos = positions[i + 1]

            if accel > 0:
                # Accelerating — draw upward green tick
                offset = len(accel_verts)
                tick_top = ghost_pos + bb_up * ACCEL_TICK_LENGTH
                tick_bottom = ghost_pos
                accel_verts.append(tuple(tick_top))
                accel_verts.append(tuple(tick_bottom))
                accel_indices.append((offset, offset + 1))
                # Small arrowhead
                arrow_left = ghost_pos + bb_up * ACCEL_TICK_LENGTH * 0.7 - bb_right * ACCEL_TICK_LENGTH * 0.3
                arrow_right = ghost_pos + bb_up * ACCEL_TICK_LENGTH * 0.7 + bb_right * ACCEL_TICK_LENGTH * 0.3
                offset2 = len(accel_verts)
                accel_verts.append(tuple(tick_top))
                accel_verts.append(tuple(arrow_left))
                accel_indices.append((offset2, offset2 + 1))
                offset3 = len(accel_verts)
                accel_verts.append(tuple(tick_top))
                accel_verts.append(tuple(arrow_right))
                accel_indices.append((offset3, offset3 + 1))
            else:
                # Decelerating — draw downward red tick
                offset = len(decel_verts)
                tick_top = ghost_pos
                tick_bottom = ghost_pos - bb_up * ACCEL_TICK_LENGTH
                decel_verts.append(tuple(tick_top))
                decel_verts.append(tuple(tick_bottom))
                decel_indices.append((offset, offset + 1))
                # Small arrowhead pointing down
                arrow_left = ghost_pos - bb_up * ACCEL_TICK_LENGTH * 0.7 - bb_right * ACCEL_TICK_LENGTH * 0.3
                arrow_right = ghost_pos - bb_up * ACCEL_TICK_LENGTH * 0.7 + bb_right * ACCEL_TICK_LENGTH * 0.3
                offset2 = len(decel_verts)
                decel_verts.append(tuple(tick_bottom))
                decel_verts.append(tuple(arrow_left))
                decel_indices.append((offset2, offset2 + 1))
                offset3 = len(decel_verts)
                decel_verts.append(tuple(tick_bottom))
                decel_verts.append(tuple(arrow_right))
                decel_indices.append((offset3, offset3 + 1))

    # Draw batched acceleration markers
    gpu.state.line_width_set(2.0)
    if accel_verts:
        batch = batch_for_shader(
            shader, 'LINES', {"pos": accel_verts}, indices=accel_indices,
        )
        _draw_batch(shader, batch, ACCEL_COLOR)

    if decel_verts:
        batch = batch_for_shader(
            shader, 'LINES', {"pos": decel_verts}, indices=decel_indices,
        )
        _draw_batch(shader, batch, DECEL_COLOR)

    gpu.state.line_width_set(1.0)


# ---------------------------------------------------------------------------
# Snapshot Overlay Drawing
# ---------------------------------------------------------------------------

def _draw_snapshot_overlays(
    context: bpy.types.Context,
    shader,
    bb_right: Vector,
    bb_up: Vector,
    ghost_radius: float,
) -> None:
    """Draw desaturated ghost markers for visible snapshots.

    Snapshot ghosts are non-interactive and drawn with reduced opacity.

    Args:
        context: The current Blender context.
        shader: The GPU shader to use.
        bb_right: Billboard right axis (from _extract_billboard_axes).
        bb_up: Billboard up axis (from _extract_billboard_axes).
        ghost_radius: Base radius for ghost markers.
    """
    # Import here to avoid circular dependency
    try:
        from .snapshot import SnapshotStore
    except ImportError:
        return

    scene = context.scene
    snap_store = SnapshotStore.get(scene)
    if snap_store is None:
        return

    for snapshot in snap_store.get_visible():
        for ghost_data in snapshot.ghost_data:
            world_position = Vector(ghost_data.get("world_position", (0, 0, 0)))
            generation_level = ghost_data.get("generation_level", 1)

            base_color = _get_level_color(generation_level)
            desaturated_color = _desaturate_color(base_color, factor=0.6)

            all_verts: list[tuple] = []
            all_indices: list[tuple[int, int]] = []

            circle_verts = _build_3d_circle_verts(
                world_position, ghost_radius * 0.8, bb_right, bb_up
            )
            for vertex in circle_verts:
                all_verts.append(tuple(vertex))
            all_indices.extend(_get_circle_indices(SPHERE_SEGMENTS))

            if all_verts:
                batch = batch_for_shader(
                    shader, 'LINES',
                    {"pos": all_verts},
                    indices=all_indices,
                )
                _draw_batch(shader, batch, desaturated_color)


# ---------------------------------------------------------------------------
# Public draw functions (referenced in the spec for clarity)
# ---------------------------------------------------------------------------

def draw_ghosts(context: bpy.types.Context) -> None:
    """Draw ghost markers in the viewport.

    Wrapper that delegates to draw_ghosts_3d.  Kept as a named function
    matching the spec for documentation purposes.

    Args:
        context: The current Blender context.
    """
    draw_ghosts_3d(context)


def draw_motion_arc(context: bpy.types.Context) -> None:
    """Draw motion arcs in the viewport.

    Note: Arc drawing is integrated into draw_ghosts_3d for batching
    efficiency.  This function is a no-op and exists for API compatibility.

    Args:
        context: The current Blender context.
    """
    # Integrated into draw_ghosts_3d
    pass


def draw_spacing_ticks(context: bpy.types.Context) -> None:
    """Draw spacing ticks in the viewport.

    Note: Tick drawing is integrated into draw_ghosts_3d for batching
    efficiency.  This function is a no-op and exists for API compatibility.

    Args:
        context: The current Blender context.
    """
    # Integrated into draw_ghosts_3d
    pass


def draw_snapshot_overlay(context: bpy.types.Context) -> None:
    """Draw snapshot overlays in the viewport.

    Note: Snapshot drawing is integrated into draw_ghosts_3d for batching
    efficiency.  This function is a no-op and exists for API compatibility.

    Args:
        context: The current Blender context.
    """
    # Integrated into draw_ghosts_3d
    pass


# ---------------------------------------------------------------------------
# Ballistic Preview Drawing
# ---------------------------------------------------------------------------

def _draw_ballistic_preview(
    store: GhostStore,
    shader,
    bb_right: Vector,
    bb_up: Vector,
    ghost_radius: float,
    settings,
    current_frame: float,
) -> None:
    """Draw a ballistic arc preview showing physics-influenced ghost trajectories.

    Renders a dashed arc and translucent markers at predicted positions
    assuming constant gravitational acceleration.

    Args:
        store: The GhostStore with current ghosts.
        shader: The GPU shader to draw with.
        bb_right: Billboard right axis (from _extract_billboard_axes).
        bb_up: Billboard up axis (from _extract_billboard_axes).
        ghost_radius: Base radius for ghost markers.
        settings: GhostToolSceneSettings with ballistic parameters.
        current_frame: The scene's current playhead frame.
    """
    all_ghosts = list(store)
    if len(all_ghosts) < 2:
        return

    gravity_strength = settings.ballistic_gravity
    gravity_axis = settings.ballistic_gravity_axis
    offset = Vector(settings.ballistic_offset)

    # Map gravity axis name to vector component index (0=X, 1=Y, 2=Z)
    axis_idx = {"X": 0, "Y": 1, "Z": 2}.get(gravity_axis.upper(), 2)
    fps = (bpy.context.scene.render.fps / bpy.context.scene.render.fps_base) if bpy.context.scene else DEFAULT_FPS

    # Collect ghost positions sorted by frame
    sorted_ghosts = sorted(all_ghosts, key=lambda ghost: ghost.frame)

    if len(sorted_ghosts) < 2:
        return

    first_frame = sorted_ghosts[0].frame
    last_frame = sorted_ghosts[-1].frame
    total_frames = last_frame - first_frame
    if total_frames <= 0:
        return

    total_time = total_frames / fps

    # Compute ballistic preview positions for each ghost
    # Using parabolic trajectory: displacement = 0.5 * g * t * (T - t)
    # This peaks at the midpoint and falls off symmetrically
    preview_positions: list[Vector] = []
    for ghost in sorted_ghosts:
        time_frames = ghost.frame - first_frame
        time_seconds = time_frames / fps

        # Parabolic displacement formula (peaks at T/2, zeros at T=0 and T=T)
        displacement = 0.5 * gravity_strength * time_seconds * (total_time - time_seconds)

        preview_position = ghost.world_position.copy()
        # Apply displacement along gravity axis, scaled down for visual clarity
        preview_position[axis_idx] -= displacement * BALLISTIC_PREVIEW_SCALE
        preview_position += offset
        preview_positions.append(preview_position)

    if not preview_positions:
        return

    # Draw the ballistic arc line with dashed effect (every other segment drawn)
    arc_verts: list[tuple] = []
    arc_indices: list[tuple[int, int]] = []
    for i in range(len(preview_positions) - 1):
        # Skip every other segment for visual dashed appearance
        if i % 2 == 0:
            vertex_offset = len(arc_verts)
            arc_verts.append(tuple(preview_positions[i]))
            arc_verts.append(tuple(preview_positions[i + 1]))
            arc_indices.append((vertex_offset, vertex_offset + 1))

    if arc_verts:
        gpu.state.line_width_set(2.0)
        batch = batch_for_shader(
            shader, 'LINES',
            {"pos": arc_verts},
            indices=arc_indices,
        )
        _draw_batch(shader, batch, BALLISTIC_ARC_COLOR)

    # Draw translucent markers at ballistic preview positions
    marker_radius = ghost_radius * 0.7
    for preview_position in preview_positions:
        circle_verts = _build_3d_circle_verts(preview_position, marker_radius, bb_right, bb_up)
        vertex_indices = _get_circle_indices(SPHERE_SEGMENTS)

        batch = batch_for_shader(
            shader, 'LINES',
            {"pos": [tuple(vertex) for vertex in circle_verts]},
            indices=vertex_indices,
        )
        _draw_batch(shader, batch, BALLISTIC_MARKER_COLOR)


# ---------------------------------------------------------------------------
# 2D Draw Handler — Frame labels on hover (POST_PIXEL)
# ---------------------------------------------------------------------------

def _draw_mode_label_hud(
    context: bpy.types.Context,
    settings,
    blf_module,
) -> None:
    """Render the persistent Mode Label HUD in the top-left of the viewport.

    Shows the current ghost display mode (Live, Snapshot, Diff, or
    BAKE IN PROGRESS) as a small text label.  A dark shadow is drawn
    first for readability against any background.

    Args:
        context: Current Blender context.
        settings: GhostToolSceneSettings.
        blf_module: Already-imported blf module.
    """
    # Lazy module imports — both are cached after first call, no per-frame cost.
    try:
        from . import ghost_pipeline as _gp
        bake_active = _gp._BAKE_IN_PROGRESS
    except AttributeError:
        bake_active = False

    try:
        from .ghost_data import DiffReference, AnchorState
        _diff_available = True
    except ImportError:
        _diff_available = False

    # Determine the label text and color based on active mode
    if bake_active:
        label = "BAKING..."
        label_color = (1.0, 0.8, 0.2, 0.95)
    elif _diff_available and getattr(settings, "show_diff_overlay", False):
        scene = context.scene
        diff_ref = DiffReference.get(scene)
        if diff_ref and diff_ref.state == AnchorState.STALE:
            label = "DIFF  [STALE]"
            label_color = (1.0, 0.4, 0.1, 0.95)
        elif diff_ref:
            label = f"DIFF  f{diff_ref.anchor_frame}"
            label_color = (0.4, 0.9, 1.0, 0.95)
        else:
            label = "DIFF  (no anchor)"
            label_color = (0.6, 0.6, 0.6, 0.85)
    elif not getattr(settings, "live_point_ghosts", True):
        label = "SNAPSHOT"
        label_color = (0.8, 0.8, 0.8, 0.85)
    elif getattr(settings, "show_skeleton_view", False):
        label = "SKELETON VIEW"
        label_color = (0.5, 1.0, 0.6, 0.90)
    else:
        label = "LIVE"
        label_color = (0.3, 0.9, 0.4, 0.85)

    region = context.region
    if region is None:
        return

    margin_x, margin_y = MODE_LABEL_MARGIN_PX
    x = margin_x
    y = region.height - margin_y - MODE_LABEL_FONT_SIZE

    font_id = 0
    blf_module.size(font_id, MODE_LABEL_FONT_SIZE)

    # Shadow pass
    blf_module.color(font_id, 0.0, 0.0, 0.0, 0.7)
    blf_module.position(font_id, x + 1, y - 1, 0)
    blf_module.draw(font_id, label)

    # Main label
    blf_module.color(font_id, *label_color)
    blf_module.position(font_id, x, y, 0)
    blf_module.draw(font_id, label)


def _draw_progress_ring(
    context: bpy.types.Context,
    blf_module,
) -> None:
    """Render a 2D progress ring while a bake is in progress.

    Draws a screen-space circle using ``gpu`` module 2D immediate drawing,
    positioned near the top-left of the viewport alongside the mode label.
    The ring is a simple static circle; animated appearance comes from the
    label text cycling (the ring itself is always fully drawn).

    Args:
        context: Current Blender context.
        blf_module: Already-imported blf module (unused here, kept for API consistency).
    """
    region = context.region
    if region is None:
        return

    try:
        import gpu as _gpu
        from gpu_extras.batch import batch_for_shader as _bfs
    except ImportError:
        return

    margin_x, margin_y = PROGRESS_RING_MARGIN_PX
    cx = float(margin_x + PROGRESS_RING_RADIUS_PX)
    cy = float(region.height - margin_y - PROGRESS_RING_RADIUS_PX)
    r = PROGRESS_RING_RADIUS_PX

    # Build circle verts
    segs = PROGRESS_RING_SEGMENTS
    verts_bg = []
    verts_ring = []
    indices = []

    for i in range(segs):
        angle = 2.0 * math.pi * i / segs
        verts_bg.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        verts_ring.append((cx + (r - 2) * math.cos(angle), cy + (r - 2) * math.sin(angle)))
        indices.append((i, (i + 1) % segs))

    try:
        shader_2d = _gpu.shader.from_builtin('UNIFORM_COLOR')
        shader_2d.bind()

        _gpu.state.blend_set('ALPHA')
        _gpu.state.line_width_set(3.0)

        # Background ring (dim)
        shader_2d.uniform_float("color", PROGRESS_RING_BG_COLOR)
        batch_bg = _bfs(shader_2d, 'LINES', {"pos": verts_bg}, indices=indices)
        batch_bg.draw(shader_2d)

        # Bright foreground ring
        shader_2d.uniform_float("color", PROGRESS_RING_COLOR)
        batch_fg = _bfs(shader_2d, 'LINES', {"pos": verts_ring}, indices=indices)
        batch_fg.draw(shader_2d)

        _gpu.state.line_width_set(1.0)
        _gpu.state.blend_set('NONE')
    except Exception as exc:
        debug(f"Progress ring draw error: {exc}")


def draw_ghosts_2d(context: bpy.types.Context) -> None:
    """2D overlay draw callback for frame labels, mode HUD, and progress ring.

    Renders:
    - A persistent Mode Label HUD (top-left) showing the active ghost mode.
    - A warm-up Progress Ring while a bake is in progress.
    - A frame-number label on the currently hovered ghost.

    Uses ``blf`` for bitmap font rendering in the POST_PIXEL drawing stage.

    Args:
        context: The current Blender context.
    """
    try:
        scene = getattr(context, 'scene', None)

        if not hasattr(scene, 'ghost_tool') or not scene.ghost_tool.is_active:
            return

        settings = scene.ghost_tool

        try:
            import blf
        except ImportError:
            return

        # --- Mode Label HUD ---
        if getattr(settings, "show_mode_label", True):
            _draw_mode_label_hud(context, settings, blf)

        # --- Progress Ring ---
        try:
            from . import ghost_pipeline as _gp
            if _gp._BAKE_IN_PROGRESS:
                _draw_progress_ring(context, blf)
        except Exception as exc:
            debug(f"Progress ring check error: {exc}")

        # --- Hover frame label ---
        if not settings.show_cached_markers or not settings.show_hover_frame_label:
            return

        session = SessionState.get(scene)
        if not session.hovered_ghost_uid:
            return

        store = GhostStore.get(scene)
        hovered_ghost = store.get_by_uid(session.hovered_ghost_uid)
        if not hovered_ghost:
            return

        # Project the ghost's world position to 2D screen coordinates
        region = context.region
        region_3d = context.region_data
        if not region or not region_3d:
            return

        try:
            from bpy_extras.view3d_utils import location_3d_to_region_2d
        except ImportError:
            return

        screen_pos = location_3d_to_region_2d(region, region_3d, hovered_ghost.world_position)
        if screen_pos is None:
            return

        # Build label text — integer frame for whole frames, one decimal otherwise
        # Include offset from current frame
        frame_val = hovered_ghost.frame
        current_frame = scene.frame_current
        offset = int(hovered_ghost.frame - current_frame)
        offset_str = f" (+{offset})" if offset > 0 else f" ({offset})" if offset < 0 else ""

        if abs(frame_val - round(frame_val)) < 0.01:
            label_text = f"f{int(round(frame_val))}{offset_str}"
        else:
            label_text = f"f{frame_val:.1f}{offset_str}"

        font_id = 0
        font_size = FRAME_LABEL_FONT_SIZE
        offset_x, offset_y = FRAME_LABEL_OFFSET_PX

        blf.size(font_id, font_size)

        # Draw a dark shadow first for readability
        shadow_offset = 1
        blf.color(font_id, 0.0, 0.0, 0.0, 0.7)
        blf.position(font_id,
                     screen_pos[0] + offset_x + shadow_offset,
                     screen_pos[1] + offset_y - shadow_offset,
                     0)
        blf.draw(font_id, label_text)

        # Draw the bright label on top
        blf.color(font_id, 1.0, 1.0, 1.0, 0.95)
        blf.position(font_id,
                     screen_pos[0] + offset_x,
                     screen_pos[1] + offset_y,
                     0)
        blf.draw(font_id, label_text)
    except Exception as exc:
        warn(f"Error in 2D ghost overlay draw: {exc}")
        return


# ---------------------------------------------------------------------------
# Registration / Unregistration
# ---------------------------------------------------------------------------

def register() -> None:
    """Register 3D and 2D viewport draw handlers.

    Adds a POST_VIEW draw handler for 3D geometry (ghosts, arcs, ticks)
    and a POST_PIXEL handler for 2D overlays (frame labels on hover).
    Handler references are stored at module level for clean removal.
    """
    global _draw_handler_3d, _draw_handler_2d

    if _draw_handler_3d is not None:
        # Already registered — prevent duplicates
        return

    _draw_handler_3d = bpy.types.SpaceView3D.draw_handler_add(
        draw_ghosts_3d,
        (bpy.context,),
        'WINDOW',
        'POST_VIEW',
    )

    _draw_handler_2d = bpy.types.SpaceView3D.draw_handler_add(
        draw_ghosts_2d,
        (bpy.context,),
        'WINDOW',
        'POST_PIXEL',
    )
    log("Viewport draw handlers registered (3D + 2D).")


def unregister() -> None:
    """Remove all viewport draw handlers.

    Must be called during addon unregistration to prevent Blender crashes
    from stale draw callbacks referencing unloaded code.
    """
    global _draw_handler_3d, _draw_handler_2d

    if _draw_handler_3d is not None:
        try:
            bpy.types.SpaceView3D.draw_handler_remove(_draw_handler_3d, 'WINDOW')
        except Exception as exc:
            warn(f"Failed to remove 3D draw handler: {exc}")
        _draw_handler_3d = None

    if _draw_handler_2d is not None:
        try:
            bpy.types.SpaceView3D.draw_handler_remove(_draw_handler_2d, 'WINDOW')
        except Exception as exc:
            warn(f"Failed to remove 2D draw handler: {exc}")
        _draw_handler_2d = None

    global _archetype_preview_cache_key
    _archetype_preview_cache_key = ()
    _batch_cache.clear()
    log("Viewport draw handlers unregistered.")


# ---------------------------------------------------------------------------
# Test notes
# ---------------------------------------------------------------------------
#
# Test 1: Draw handler registration
# >>> from ghost_tool import viewport_draw
# >>> viewport_draw.register()
# >>> # Verify no errors in the console
# >>> viewport_draw.unregister()
#
# Test 2: Ghost display after generation
# >>> # 1. Generate ghosts on an object with keyframes
# >>> # 2. Set scene.ghost_tool.is_active = True
# >>> # 3. Verify colored circles appear at ghost positions in viewport
# >>> # 4. Toggle show_level_1 off — level 1 ghosts should disappear
#
# Test 3: Motion arc visibility
# >>> # With ghosts generated, scene.ghost_tool.show_motion_arc = True
# >>> # A gray line should connect ghosts in sequence
#
# Test 4: Spacing ticks color gradient
# >>> # scene.ghost_tool.show_spacing_ticks = True
# >>> # Dense areas (slow motion) should be blue, sparse = red
