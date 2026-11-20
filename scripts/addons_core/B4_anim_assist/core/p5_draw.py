# --- TRAJECTORY VISUALIZATION ---
"""GPU draw callbacks for trajectory overlays.

Two callbacks are registered through ``draw_registry``:

1. ``draw_paths_3d`` — ``POST_VIEW`` in VIEW_3D.  Draws 3D trajectory
   lines, tick marks, velocity vectors, tangent lines, and ghost points
   using the ``gpu`` module.

2. ``draw_labels_2d`` — ``POST_PIXEL`` in VIEW_3D.  Draws frame-number
   labels, marker text, and the arc-quality score badge using ``blf``.

Both callbacks are wrapped in ``try/except``.  On any exception they
log the error, unregister themselves via ``draw_registry``, and clear
``RuntimeState.overlay_enabled`` to prevent repeated failures.
"""

from __future__ import annotations

import math

try:
    import bpy
    import gpu
    from gpu_extras.batch import batch_for_shader
    import blf
    from mathutils import Vector
except Exception:  # pragma: no cover
    bpy = None  # type: ignore[assignment]
    gpu = None  # type: ignore[assignment]
    blf = None  # type: ignore[assignment]
    Vector = None  # type: ignore[assignment]

from .logging import get_logger

_log = get_logger(__name__)

__all__ = [
    "set_draw_data",
    "clear_draw_data",
    "get_issues",
    "build_draw_data",
    "draw_paths_3d",
    "draw_labels_2d",
    "get_handler_ids",
    "set_handler_ids",
    "clear_handler_ids",
]

# ---------------------------------------------------------------------------
# Draw state namespace
# ---------------------------------------------------------------------------

class _DrawState:
    """Namespace for module-level draw state."""

    def __init__(self) -> None:
        self.handler_3d: int = -1
        self.handler_2d: int = -1
        self.paths: list["_PathDrawData"] = []
        self.issues: list = []
        self.score: float = -1.0
        self.generation: int = -1


_state = _DrawState()


def get_handler_ids() -> tuple[int, int]:
    """Return the current draw handler IDs (3D and 2D) so callers can manage them."""
    return (_state.handler_3d, _state.handler_2d)


def set_handler_ids(h3d: int, h2d: int) -> None:
    """Store the draw handler IDs from draw_handler_add() so they can be unregistered later."""
    _state.handler_3d = h3d
    _state.handler_2d = h2d


def clear_handler_ids() -> None:
    """Reset handler IDs to -1 after unregistration or on file load to prevent stale handler crashes."""
    _state.handler_3d = -1
    _state.handler_2d = -1


class _PathDrawData:
    """Pre-computed draw data for one target."""

    __slots__ = (
        "label", "coords", "colors", "key_coords", "key_frames",
        "frame_coords", "ghost_coords", "velocity_lines",
        "tangent_lines", "marker_points", "marker_labels",
        "path_width", "show_frame_numbers",
    )

    def __init__(self) -> None:
        self.label: str = ""
        self.coords: list[tuple[float, float, float]] = []
        self.colors: list[tuple[float, float, float, float]] = []
        self.key_coords: list[tuple[float, float, float]] = []
        self.key_frames: list[int] = []
        self.frame_coords: list[tuple[float, float, float]] = []
        self.ghost_coords: list[tuple[float, float, float]] = []
        self.velocity_lines: list[tuple[float, float, float]] = []
        self.tangent_lines: list[tuple[float, float, float]] = []
        self.marker_points: list[tuple[float, float, float]] = []
        self.marker_labels: list[tuple[tuple[float, float, float], str, tuple[float, float, float, float]]] = []
        self.path_width: float = 2.0
        self.show_frame_numbers: bool = False


def set_draw_data(
    paths: list["_PathDrawData"],
    issues: list,
    score: float,
    generation: int,
) -> None:
    """Replace the draw data atomically (called by the refresh operator)."""
    _state.paths = paths
    _state.issues = issues
    _state.score = score
    _state.generation = generation


def clear_draw_data() -> None:
    """Wipe cached trajectory geometry when the animation changes to avoid stale path rendering."""
    _state.paths = []
    _state.issues = []
    _state.score = -1.0
    _state.generation = -1


def get_issues() -> list:
    """Public accessor for the current issue list (used by nav operators)."""
    return _state.issues


# ---------------------------------------------------------------------------
# Build draw data from cache/samples
# ---------------------------------------------------------------------------

def build_draw_data(
    samples: list,
    issues: list,
    *,
    palette,
    label: str = "",
    show_frame_ticks: bool = True,
    show_keyframe_ticks: bool = True,
    show_velocity: bool = False,
    show_tangent: bool = False,
    show_ghost_points: bool = True,
    show_frame_numbers: bool = False,
    show_spacing_color: bool = False,
    show_deviation_heatmap: bool = False,
    current_frame: float = 0.0,
    ghost_radius: int = 2,
    path_width: float = 2.0,
) -> _PathDrawData:
    """Build a ``_PathDrawData`` from samples and issues."""
    from .p5_sampling import segment_lengths, derive_velocity
    from .p5_colors import spacing_color, deviation_heatmap_color
    from .p5_issues import detect_arc_drift

    dd = _PathDrawData()
    dd.label = label
    dd.path_width = path_width
    dd.show_frame_numbers = show_frame_numbers

    if not samples:
        return dd

    # Base path coords.
    for s in samples:
        dd.coords.append(s.world_pos)

    # Segment colouring.
    seg_lens = segment_lengths(samples)
    median_len = sorted(seg_lens)[len(seg_lens) // 2] if seg_lens else 0.0

    if show_deviation_heatmap:
        drift_issues = detect_arc_drift(samples)
        dev_map: dict[int, float] = {}
        max_dev = 0.0
        for iss in drift_issues:
            if iss.sample_index >= 0:
                dev_map[iss.sample_index] = iss.severity
                max_dev = max(max_dev, iss.severity)
        for i in range(len(samples)):
            dev = dev_map.get(i, 0.0)
            dd.colors.append(deviation_heatmap_color(dev, max(max_dev, 0.01)))
    elif show_spacing_color and seg_lens:
        dd.colors.append(palette.path)  # First vertex has no segment.
        for sl in seg_lens:
            dd.colors.append(spacing_color(
                sl, median_len,
                base_color=palette.path,
                hi_color=palette.issue_hi,
                lo_color=palette.issue_lo,
            ))
    else:
        dd.colors = [palette.path] * len(samples)

    # Keyframe ticks.
    if show_keyframe_ticks:
        for s in samples:
            if s.is_keyframe:
                dd.key_coords.append(s.world_pos)
                # Only populate frame numbers when the user has enabled
                # the label — draw_labels_2d skips the blf loop when
                # key_frames is empty.
                if show_frame_numbers:
                    dd.key_frames.append(int(round(s.frame)))

    # Frame ticks.
    if show_frame_ticks:
        for s in samples:
            dd.frame_coords.append(s.world_pos)

    # Ghost points (neighborhood around current frame).
    if show_ghost_points:
        for s in samples:
            dist = abs(s.frame - current_frame)
            if 0 < dist <= ghost_radius:
                dd.ghost_coords.append(s.world_pos)

    # Velocity vectors.
    if show_velocity:
        vels = derive_velocity(samples)
        scale = 0.05
        for v in vels:
            dd.velocity_lines.append(v.world_pos)
            end = (
                v.world_pos[0] + v.velocity[0] * scale,
                v.world_pos[1] + v.velocity[1] * scale,
                v.world_pos[2] + v.velocity[2] * scale,
            )
            dd.velocity_lines.append(end)

    # Tangent lines at keyframes.
    if show_tangent:
        vels = derive_velocity(samples) if not show_velocity else []
        if not vels:
            vels = derive_velocity(samples)
        vel_by_frame: dict[float, tuple] = {}
        for v in vels:
            vel_by_frame[round(v.frame, 4)] = v.velocity
        scale = 0.1
        for s in samples:
            if s.is_keyframe and round(s.frame, 4) in vel_by_frame:
                vel = vel_by_frame[round(s.frame, 4)]
                vlen = math.sqrt(vel[0] ** 2 + vel[1] ** 2 + vel[2] ** 2)
                if vlen > 1e-8:
                    nv = (vel[0] / vlen, vel[1] / vlen, vel[2] / vlen)
                    dd.tangent_lines.append((
                        s.world_pos[0] - nv[0] * scale,
                        s.world_pos[1] - nv[1] * scale,
                        s.world_pos[2] - nv[2] * scale,
                    ))
                    dd.tangent_lines.append((
                        s.world_pos[0] + nv[0] * scale,
                        s.world_pos[1] + nv[1] * scale,
                        s.world_pos[2] + nv[2] * scale,
                    ))

    # Issue markers.
    for iss in issues:
        dd.marker_points.append(iss.world_pos)
        dd.marker_labels.append((iss.world_pos, iss.issue_type, palette.issue_hi))

    return dd


# ---------------------------------------------------------------------------
# 3D draw callback
# ---------------------------------------------------------------------------

def draw_paths_3d() -> None:
    """POST_VIEW callback — draws 3D trajectory geometry."""
    if gpu is None:
        return


    try:
        if not _state.paths:
            return

        shader = gpu.shader.from_builtin('SMOOTH_COLOR')

        for dd in _state.paths:
            if len(dd.coords) < 2:
                continue

            # Main path line.
            shader.bind()
            batch = batch_for_shader(shader, 'LINE_STRIP', {
                "pos": dd.coords,
                "color": dd.colors[:len(dd.coords)],
            })
            gpu.state.line_width_set(dd.path_width)
            gpu.state.blend_set('ALPHA')
            batch.draw(shader)

            # Frame tick points.
            if dd.frame_coords:
                pt_shader = gpu.shader.from_builtin('FLAT_COLOR')
                pt_shader.bind()
                pt_batch = batch_for_shader(pt_shader, 'POINTS', {
                    "pos": dd.frame_coords,
                    "color": [(0.7, 0.7, 0.7, 0.4)] * len(dd.frame_coords),
                })
                gpu.state.point_size_set(3.0)
                pt_batch.draw(pt_shader)

            # Keyframe tick points.
            if dd.key_coords:
                pt_shader = gpu.shader.from_builtin('FLAT_COLOR')
                pt_shader.bind()
                pt_batch = batch_for_shader(pt_shader, 'POINTS', {
                    "pos": dd.key_coords,
                    "color": [(1.0, 1.0, 0.2, 1.0)] * len(dd.key_coords),
                })
                gpu.state.point_size_set(6.0)
                pt_batch.draw(pt_shader)

            # Ghost points.
            if dd.ghost_coords:
                pt_shader = gpu.shader.from_builtin('FLAT_COLOR')
                pt_shader.bind()
                pt_batch = batch_for_shader(pt_shader, 'POINTS', {
                    "pos": dd.ghost_coords,
                    "color": [(0.8, 0.8, 0.8, 0.3)] * len(dd.ghost_coords),
                })
                gpu.state.point_size_set(5.0)
                pt_batch.draw(pt_shader)

            # Velocity vectors.
            if dd.velocity_lines:
                line_shader = gpu.shader.from_builtin('FLAT_COLOR')
                line_shader.bind()
                n = len(dd.velocity_lines)
                line_batch = batch_for_shader(line_shader, 'LINES', {
                    "pos": dd.velocity_lines,
                    "color": [(0.3, 0.9, 0.3, 0.6)] * n,
                })
                gpu.state.line_width_set(1.0)
                line_batch.draw(line_shader)

            # Tangent lines.
            if dd.tangent_lines:
                line_shader = gpu.shader.from_builtin('FLAT_COLOR')
                line_shader.bind()
                n = len(dd.tangent_lines)
                line_batch = batch_for_shader(line_shader, 'LINES', {
                    "pos": dd.tangent_lines,
                    "color": [(0.3, 0.6, 1.0, 0.5)] * n,
                })
                gpu.state.line_width_set(1.0)
                line_batch.draw(line_shader)

            # Issue marker points.
            if dd.marker_points:
                pt_shader = gpu.shader.from_builtin('FLAT_COLOR')
                pt_shader.bind()
                pt_batch = batch_for_shader(pt_shader, 'POINTS', {
                    "pos": dd.marker_points,
                    "color": [(1.0, 0.2, 0.2, 0.9)] * len(dd.marker_points),
                })
                gpu.state.point_size_set(8.0)
                pt_batch.draw(pt_shader)

        gpu.state.blend_set('NONE')
        gpu.state.line_width_set(1.0)
        gpu.state.point_size_set(1.0)

    except Exception:
        _log.exception("trajectory draw_paths_3d failed; disabling overlay")
        _emergency_disable()


# ---------------------------------------------------------------------------
# 2D label draw callback
# ---------------------------------------------------------------------------

def draw_labels_2d() -> None:
    """POST_PIXEL callback — draws frame numbers, markers, and arc score."""
    if blf is None or bpy is None:
        return


    try:
        context = bpy.context
        region = getattr(context, "region", None)
        rv3d = getattr(context, "region_data", None)
        if region is None or rv3d is None:
            return

        font_id = 0
        blf.size(font_id, 11)

        for dd in _state.paths:
            # Frame number labels at keyframe positions.
            for coord, frame_num in zip(dd.key_coords, dd.key_frames):
                screen = _project_3d_to_2d(region, rv3d, coord)
                if screen is None:
                    continue
                blf.color(font_id, 1.0, 1.0, 1.0, 0.8)
                blf.position(font_id, screen[0] + 8, screen[1] + 4, 0)
                blf.draw(font_id, str(frame_num))

            # Issue marker labels.
            for pos3d, label_text, color in dd.marker_labels:
                screen = _project_3d_to_2d(region, rv3d, pos3d)
                if screen is None:
                    continue
                blf.color(font_id, color[0], color[1], color[2], color[3])
                blf.position(font_id, screen[0] + 10, screen[1] - 4, 0)
                blf.draw(font_id, label_text)

        # Arc quality score badge (top-left of viewport).
        if _state.score >= 0.0:
            blf.size(font_id, 14)
            if _state.score >= 80:
                blf.color(font_id, 0.3, 0.9, 0.3, 0.9)
            elif _state.score >= 50:
                blf.color(font_id, 0.9, 0.8, 0.2, 0.9)
            else:
                blf.color(font_id, 0.9, 0.3, 0.3, 0.9)
            blf.position(font_id, 20, region.height - 30, 0)
            blf.draw(font_id, f"Arc Score: {_state.score:.0f}")

    except Exception:
        _log.exception("trajectory draw_labels_2d failed; disabling overlay")
        _emergency_disable()


# ---------------------------------------------------------------------------
# 3D → 2D projection helper
# ---------------------------------------------------------------------------

def _project_3d_to_2d(region, rv3d, coord):
    """Project a world-space coordinate to 2D screen space."""
    try:
        from bpy_extras.view3d_utils import location_3d_to_region_2d
        if Vector is not None:
            v = Vector(coord) if not isinstance(coord, Vector) else coord
            return location_3d_to_region_2d(region, rv3d, v)
    except Exception:
        # Projection can fail for off-screen points; skip gracefully.
        _log.debug("3D to 2D projection failed", exc_info=True)
    return None


# ---------------------------------------------------------------------------
# Emergency disable
# ---------------------------------------------------------------------------

def _emergency_disable() -> None:
    """Disable the overlay and unregister draw handlers after an error."""
    from . import draw_registry as dreg
    from . import runtime as rts_mod

    try:
        state = rts_mod.get_state()
        state.overlay_enabled = False
        state.active_overlay_tags.discard("p5_trajectory")
    except Exception:
        # Runtime state unavailable; cannot disable gracefully but cleanup will proceed.
        _log.debug("Failed to disable runtime state", exc_info=True)

    for hid in (_state.handler_3d, _state.handler_2d):
        if hid >= 0:
            try:
                dreg.unregister_handler(hid)
            except Exception:
                # Handler already removed by another path; harmless.
                _log.debug("Failed to unregister draw handler %d", hid, exc_info=True)
    clear_handler_ids()
    clear_draw_data()
