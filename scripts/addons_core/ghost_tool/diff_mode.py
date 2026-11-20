"""
diff_mode.py — Visual Diff Mode for the Ghost Tool addon.

Provides a per-bone warm/cool difference overlay that compares the current
pose against a pinned reference frame.  The overlay is purely cosmetic —
it does NOT modify any f-curves or insert keyframes.

Architecture
------------
- ``DiffReference`` and ``AnchorState`` live in ``ghost_data.py`` so they
  are available to the rest of the addon without importing this module.
- This module owns the operators (Pin, Unpin) and the draw function that
  is called from ``viewport_draw.draw_ghosts_3d()``.
- Color interpolation uses ``lerp_color()`` from ``utils.py`` to avoid
  importing ``viewport_draw.py`` (prevents a circular dependency).
- The Staleness Guard recomputes ``compute_anchor_hash()`` on each draw
  tick and flips the anchor to ``AnchorState.STALE`` when the hash
  diverges from the stored value, then desaturates the overlay and shows
  a warning via the Mode Label HUD.

All diff logic uses Euclidean distance, linear interpolation and hash comparison.
"""

from __future__ import annotations

import math
from typing import Optional

import bpy
from mathutils import Vector

from .ghost_data import (
    Ghost,
    GhostStore,
    AnchorState,
    DiffReference,
    compute_anchor_hash,
)
from .utils import (
    clamp,
    lerp_color,
    debug,
    tag_viewport_redraw,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Number of line segments used to draw the per-bone diff magnitude circles.
DIFF_CIRCLE_SEGMENTS: int = 12

# Scale factor applied to the diff circle relative to the ghost radius.
# A value of 1.6 makes the diff ring visibly larger than the ghost sphere.
DIFF_RING_SCALE: float = 1.6

# Default cool and warm colors used when settings properties are absent.
_DEFAULT_COOL: tuple[float, float, float, float] = (0.2, 0.4, 1.0, 0.75)
_DEFAULT_WARM: tuple[float, float, float, float] = (1.0, 0.25, 0.05, 0.75)

# Staleness desaturation factor for the overlay rings.
_STALE_DESAT_FACTOR: float = 0.85


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _desaturate_color(
    color: tuple[float, float, float, float],
    factor: float = 0.5,
) -> tuple[float, float, float, float]:
    """Desaturate an RGBA color for stale overlay rendering.

    Isolated copy so diff_mode.py does not need to import viewport_draw.

    Args:
        color: Input RGBA tuple.
        factor: Desaturation factor (0 = unchanged, 1 = full grayscale).

    Returns:
        tuple: Desaturated RGBA color with halved alpha.
    """
    gray = 0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2]
    r = color[0] + (gray - color[0]) * factor
    g = color[1] + (gray - color[1]) * factor
    b = color[2] + (gray - color[2]) * factor
    return (r, g, b, color[3] * 0.5)


def _build_circle_verts(
    center: Vector,
    radius: float,
    bb_right: Vector,
    bb_up: Vector,
    segments: int = DIFF_CIRCLE_SEGMENTS,
) -> list[tuple[float, float, float]]:
    """Build billboard circle vertices for GPU batch rendering.

    Args:
        center: World-space center.
        radius: World-space radius.
        bb_right: Pre-computed billboard right vector.
        bb_up: Pre-computed billboard up vector.
        segments: Number of line segments in the circle.

    Returns:
        list of (x, y, z) tuples.
    """
    verts = []
    for i in range(segments):
        angle = 2.0 * math.pi * i / segments
        offset = bb_right * (radius * math.cos(angle)) + bb_up * (radius * math.sin(angle))
        v = center + offset
        verts.append((v.x, v.y, v.z))
    return verts


def _collect_current_bone_positions(
    scene: bpy.types.Scene,
) -> dict[tuple[str, str], Vector]:
    """Sample the world-space position of every visible pose bone at the current frame.

    Reads directly from the evaluated depsgraph (no frame_set calls needed)
    so this is safe to call from a draw handler.

    Args:
        scene: The Blender scene.

    Returns:
        dict mapping bone_name → world-space Vector.
    """
    positions: dict[tuple[str, str], Vector] = {}
    try:
        dg = bpy.context.evaluated_depsgraph_get()
    except (AttributeError, RuntimeError) as exc:
        # bpy.context may be None outside an operator or during shutdown
        debug(f"diff_mode: cannot get depsgraph: {exc}")
        return positions

    for obj in scene.objects:
        if obj.type != 'ARMATURE':
            continue
        try:
            obj_eval = obj.evaluated_get(dg)
            if not obj_eval.pose:
                continue
            for bone in obj_eval.pose.bones:
                mat = obj_eval.matrix_world @ bone.matrix
                positions[(obj.name, bone.name)] = mat.translation.copy()
        except (AttributeError, RuntimeError) as exc:
            debug(f"diff_mode: error reading bone positions for {obj.name!r}: {exc}")

    return positions


# ---------------------------------------------------------------------------
# Staleness Guard
# ---------------------------------------------------------------------------

def _check_staleness(
    scene: bpy.types.Scene,
    diff_ref: DiffReference,
) -> None:
    """Compare the anchor hash against current keyframe data and update state.

    Called once per draw tick.  If the hash has diverged (i.e. keyframes at
    the anchor frame were edited after pinning) the anchor's state is set to
    ``AnchorState.STALE``.  This is idempotent — calling it when already STALE
    is safe and cheap.

    Args:
        scene: The current scene.
        diff_ref: The active DiffReference to check.
    """
    if diff_ref.state == AnchorState.STALE:
        # Already flagged — no need to re-hash every tick
        return

    # Staleness is a warning, not animated geometry: cap expensive key hashing
    # at 10 Hz even when the viewport redraws much faster.
    import time
    now = time.monotonic()
    if now - getattr(diff_ref, '_last_hash_check', 0.0) < 0.1:
        return
    diff_ref._last_hash_check = now
    current_hash = _scene_anchor_hash(scene, diff_ref.anchor_frame)
    if current_hash != diff_ref.anchor_hash:
        diff_ref.state = AnchorState.STALE


def _scene_anchor_hash(scene, frame):
    import hashlib
    parts = [(obj.name, compute_anchor_hash(obj, frame)) for obj in scene.objects if obj.type == 'ARMATURE']
    return hashlib.sha256(repr(sorted(parts)).encode()).hexdigest()[:16]


def _find_anchor_object(scene: bpy.types.Scene) -> Optional[bpy.types.Object]:
    """Find the active or first armature in the scene to use for hashing.

    Args:
        scene: The Blender scene.

    Returns:
        bpy.types.Object or None: An armature object, or None if none found.
    """
    # Prefer the context active object if it is an armature.
    # AttributeError is the only realistic failure here (context is None outside an operator).
    try:
        ctx_obj = bpy.context.active_object
        if ctx_obj and ctx_obj.type == 'ARMATURE':
            return ctx_obj
    except AttributeError:
        pass

    # Fall back to the first armature in the scene
    for obj in scene.objects:
        if obj.type == 'ARMATURE':
            return obj
    return None


# ---------------------------------------------------------------------------
# Diff Overlay Draw
# ---------------------------------------------------------------------------

def draw_diff_overlay(
    context: bpy.types.Context,
    store: GhostStore,
    shader,
    bb_right: Vector,
    bb_up: Vector,
    ghost_radius: float,
) -> None:
    """Render the per-bone diff overlay rings in the 3D viewport.

    Called from ``viewport_draw.draw_ghosts_3d()`` when
    ``settings.show_diff_overlay`` is True and a ``DiffReference`` exists.

    Each visible ghost's bone is compared against its pinned position.
    The ring color is lerped from cool (small difference) to warm
    (large difference) based on the normalized Euclidean distance.

    When the anchor is STALE, all rings are desaturated and drawn at
    reduced alpha.

    Args:
        context: The current Blender context.
        store: The active GhostStore.
        shader: The GPU UNIFORM_COLOR shader (already bound by the caller).
        bb_right: Billboard right vector.
        bb_up: Billboard up vector.
        ghost_radius: World-space radius used for ghost spheres.
    """
    try:
        import gpu as _gpu
        from gpu_extras.batch import batch_for_shader as _bfs
    except ImportError:
        return

    scene = context.scene
    settings = scene.ghost_tool
    diff_ref = DiffReference.get(scene)

    if diff_ref is None:
        return

    # Run staleness guard on each draw tick
    _check_staleness(scene, diff_ref)

    is_stale = diff_ref.state == AnchorState.STALE

    # Read colors from settings with fallback
    try:
        cool_rgba = tuple(settings.diff_cool_color)
        warm_rgba = tuple(settings.diff_warm_color)
        max_dist = max(settings.diff_max_distance, 0.001)
    except Exception:
        cool_rgba = _DEFAULT_COOL
        warm_rgba = _DEFAULT_WARM
        max_dist = 0.5

    ring_radius = ghost_radius * DIFF_RING_SCALE
    indices = [(i, (i + 1) % DIFF_CIRCLE_SEGMENTS) for i in range(DIFF_CIRCLE_SEGMENTS)]

    # Collect per-bone anchor positions from the pinned reference
    anchor_positions = diff_ref.ghost_positions

    # Collect current bone positions (from depsgraph — no frame_set)
    current_positions = _collect_current_bone_positions(scene)

    # Group ghosts by bone so we only draw one ring per bone per frame
    bone_to_ghosts: dict[tuple[str, str], list[Ghost]] = {}
    for ghost in store:
        if not ghost.bone_name:
            continue
        key = (ghost.object_name, ghost.bone_name)
        if key not in bone_to_ghosts:
            bone_to_ghosts[key] = []
        bone_to_ghosts[key].append(ghost)

    _gpu.state.blend_set('ALPHA')
    _gpu.state.line_width_set(2.0)

    try:
        # Accumulate verts per color bucket to minimize GPU draw calls,
        # consistent with the rest of viewport_draw.py's batching strategy.
        # key = rounded RGBA tuple, value = (verts_list, indices_list)
        color_buckets: dict[tuple, tuple[list, list]] = {}

        for bone_name, ghosts in bone_to_ghosts.items():
            anchor_pos = anchor_positions.get(bone_name)
            current_pos = current_positions.get(bone_name)

            if anchor_pos is None or current_pos is None:
                continue

            # Euclidean distance between pinned and current bone position
            distance = (current_pos - anchor_pos).length
            t = clamp(distance / max_dist, 0.0, 1.0)

            # Lerp cool → warm by normalized distance
            base_color = lerp_color(
                (cool_rgba[0], cool_rgba[1], cool_rgba[2], cool_rgba[3]),
                (warm_rgba[0], warm_rgba[1], warm_rgba[2], warm_rgba[3]),
                t,
            )

            if is_stale:
                base_color = _desaturate_color(base_color, _STALE_DESAT_FACTOR)

            color_key = (
                round(base_color[0], 2),
                round(base_color[1], 2),
                round(base_color[2], 2),
                round(base_color[3], 2),
            )

            if color_key not in color_buckets:
                color_buckets[color_key] = ([], [])

            bucket_verts, bucket_indices = color_buckets[color_key]

            # Accumulate ring verts for every ghost position belonging to this bone
            for ghost in ghosts:
                ring_verts = _build_circle_verts(
                    ghost.world_position, ring_radius, bb_right, bb_up
                )
                offset = len(bucket_verts)
                bucket_verts.extend(ring_verts)
                bucket_indices.extend(
                    (offset + i, offset + (i + 1) % DIFF_CIRCLE_SEGMENTS)
                    for i in range(DIFF_CIRCLE_SEGMENTS)
                )

        # One draw call per unique color — O(unique_colors) not O(N_ghosts)
        for color_key, (bucket_verts, bucket_indices) in color_buckets.items():
            if bucket_verts:
                batch = _bfs(shader, 'LINES', {"pos": bucket_verts}, indices=bucket_indices)
                shader.uniform_float("color", color_key)
                batch.draw(shader)

    finally:
        # Always restore GPU state even if an exception occurs mid-draw
        _gpu.state.line_width_set(1.0)
        _gpu.state.blend_set('NONE')


# ---------------------------------------------------------------------------
# Operators
# ---------------------------------------------------------------------------

class GHOST_OT_pin_diff_reference(bpy.types.Operator):
    """Pin the current frame as the Visual Diff reference pose.

    Captures world-space bone positions at the current frame and stores a
    SHA-256 hash of the underlying keyframe data so the Staleness Guard can
    detect post-pin edits.
    """

    bl_idname = "ghost_tool.pin_diff_reference"
    bl_label = "Pin Diff Reference"
    bl_description = (
        "Pin the current frame as the Visual Diff reference. "
        "Bones will be colored warm/cool by their distance from this pose"
    )
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context: bpy.types.Context):
        scene = context.scene
        settings = scene.ghost_tool
        anchor_frame = scene.frame_current

        # Capture current bone world positions from the evaluated depsgraph
        positions = _collect_current_bone_positions(scene)
        if not positions:
            self.report({'WARNING'}, "No armature bones found — cannot pin Diff Reference")
            return {'CANCELLED'}

        # Compute anchor hash for Staleness Guard
        anchor_hash = _scene_anchor_hash(scene, anchor_frame)

        diff_ref = DiffReference(
            anchor_frame=anchor_frame,
            anchor_hash=anchor_hash,
            ghost_positions=positions,
            state=AnchorState.LIVE,
        )
        DiffReference.set(scene, diff_ref)

        # Store the frame on the settings PropertyGroup for UI display
        settings.diff_anchor_frame = anchor_frame
        settings.show_diff_overlay = True

        tag_viewport_redraw(context)
        self.report({'INFO'}, f"Diff Reference pinned at frame {anchor_frame}")
        return {'FINISHED'}


class GHOST_OT_unpin_diff_reference(bpy.types.Operator):
    """Clear the Visual Diff reference and disable the overlay."""

    bl_idname = "ghost_tool.unpin_diff_reference"
    bl_label = "Unpin Diff Reference"
    bl_description = "Clear the pinned Diff Reference and hide the diff overlay"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context: bpy.types.Context):
        scene = context.scene
        DiffReference.set(scene, None)
        scene.ghost_tool.show_diff_overlay = False
        tag_viewport_redraw(context)
        self.report({'INFO'}, "Diff Reference cleared")
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

CLASSES: tuple[type, ...] = (
    GHOST_OT_pin_diff_reference,
    GHOST_OT_unpin_diff_reference,
)


def register() -> None:
    """Register diff mode operators."""
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    """Unregister diff mode operators and clear all references."""
    DiffReference.clear_all()
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)


# ---------------------------------------------------------------------------
# Test notes
# ---------------------------------------------------------------------------
#
# Test 1: Pin and verify reference
# >>> bpy.ops.ghost_tool.pin_diff_reference()
# >>> from ghost_tool.diff_mode import DiffReference
# >>> ref = DiffReference.get(bpy.context.scene)
# >>> assert ref is not None
# >>> assert ref.state.value == "LIVE"
#
# Test 2: Staleness detection
# >>> # With a reference pinned, edit a keyframe at the anchor frame
# >>> # On next draw tick, ref.state should be AnchorState.STALE
#
# Test 3: Unpin clears the overlay
# >>> bpy.ops.ghost_tool.unpin_diff_reference()
# >>> assert DiffReference.get(bpy.context.scene) is None
# >>> assert not bpy.context.scene.ghost_tool.show_diff_overlay
