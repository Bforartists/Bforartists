"""
fcurve_utils.py — F-curve sampling, handle recalculation, and overshoot prevention.

This module provides all f-curve manipulation functions used by Ghost Tool.
It handles reading curve values, finding adjacent keyframes, recalculating
bezier handles when a ghost is moved, and applying easing presets.

All f-curve writes are designed to be non-destructive: handles are adjusted
but keyframes are never added or removed unless explicitly requested.
"""

from __future__ import annotations

import bisect
import math
from typing import Optional

import bpy
from mathutils import Vector

from .utils import sampling_operation, log, warn, debug


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HANDLE_CLAMP_FACTOR: float = 0.4
"""Maximum fraction of the segment width that a handle can extend.

This prevents overshooting oscillation when handles are adjusted to pass
through a new ghost position.  0.4 means a handle can extend at most 40%
of the frame distance to the adjacent keyframe.
"""

HANDLE_MIN_LENGTH: float = 0.01
"""Minimum handle length to prevent degenerate zero-length handles."""

CONVERGENCE_THRESHOLD: float = 0.001
"""Tolerance for convergence in handle recalculation iterations."""

MAX_CONVERGENCE_ITERATIONS: int = 5
"""Maximum number of iterations for convergence in free mode."""

LOCKED_SCALE_DAMPING: float = 0.3
"""Dampens per-iteration handle scaling in locked mode."""

SMOOTH_CORRECTION_DAMPING: float = 0.4
"""Dampens per-iteration handle correction in smooth mode."""

HANDLE_SCALE_MIN: float = 0.1
"""Minimum handle scale to prevent collapse."""

FRAME_MATCH_EPSILON: float = 0.001
"""Tolerance for matching keyframes by frame number during fcurve restoration.

When restoring an fcurve snapshot, keyframes are matched to snapshot entries
based on nearest frame number. A keyframe matches if it's within this epsilon.
"""

HANDLE_SCALE_MAX: float = 3.0
"""Maximum handle scale to prevent explosion."""

KEYFRAME_FRAME_TOLERANCE: float = 0.01
"""Tolerance for matching existing keyframes (in frames)."""

INITIAL_HANDLE_DAMPING: float = 0.75
"""Damping factor for first handle correction pass.

Reduces the initial handle offset to ~75% of the computed delta,
preventing overshoot before iterative refinement begins.
"""

ITERATIVE_HANDLE_DAMPING: float = 0.5
"""Damping factor for subsequent convergence iterations.

Each iteration corrects by half the remaining residual, providing
stable convergence without oscillation.
"""


# ---------------------------------------------------------------------------
# F-curve Sampling
# ---------------------------------------------------------------------------

def sample_fcurve(fcurve: bpy.types.FCurve, frame: float) -> float:
    """Return the f-curve's interpolated value at the given frame.

    Args:
        fcurve: The f-curve to sample. May be None.
        frame: The frame number to evaluate at.

    Returns:
        float: The curve value at the frame, or 0.0 if the fcurve is None.
    """
    if fcurve is None:
        warn("sample_fcurve called with None fcurve, returning 0.0")
        return 0.0
    try:
        return fcurve.evaluate(frame)
    except (RuntimeError, ValueError, TypeError) as exc:
        warn(f"Failed to evaluate fcurve at frame {frame}: {exc}")
        return 0.0


# ---------------------------------------------------------------------------
# Sorted Keyframe Cache — avoids re-sorting every call
# ---------------------------------------------------------------------------

# Cache only the permutation, never persistent Keyframe RNA references: keys
# can be deleted/replaced or reordered without changing their count.
_sorted_kf_cache: dict[int, tuple[tuple[float, ...], tuple[int, ...]]] = {}


def _get_sorted_keyframes(fcurve: bpy.types.FCurve) -> list[bpy.types.Keyframe]:
    points = list(fcurve.keyframe_points)
    frames = tuple(point.co.x for point in points)
    key = fcurve.as_pointer()  # Distinguishes channels in different action slots.
    cached = _sorted_kf_cache.get(key)
    if cached is None or cached[0] != frames:
        order = tuple(sorted(range(len(frames)), key=frames.__getitem__))
        if len(_sorted_kf_cache) >= 512:
            _sorted_kf_cache.clear()
        _sorted_kf_cache[key] = (frames, order)
    else:
        order = cached[1]
    return [points[index] for index in order]


def invalidate_keyframe_cache() -> None:
    """Clear the sorted keyframe cache.

    Should be called on undo/redo, keyframe edits, or generation cycles
    to ensure stale data doesn't persist.
    """
    _sorted_kf_cache.clear()


# ---------------------------------------------------------------------------
# Keyframe Lookup
# ---------------------------------------------------------------------------

def get_adjacent_keyframes(
    fcurve: bpy.types.FCurve,
    frame: float,
) -> tuple[Optional[bpy.types.Keyframe], Optional[bpy.types.Keyframe]]:
    """Return the keyframes immediately before and after the given frame.

    Uses a cached sorted keyframe list and bisect for O(log n) lookup
    instead of sorting + linear scan on every call.

    Args:
        fcurve: The f-curve to search.
        frame: The frame number to look around.

    Returns:
        tuple: (left_keyframe, right_keyframe).  Either may be None if
               the frame is before the first or after the last keyframe.
    """
    if fcurve is None:
        return (None, None)

    keyframes = _get_sorted_keyframes(fcurve)
    if not keyframes:
        return (None, None)

    # Extract frame values for bisect
    frames = [kp.co.x for kp in keyframes]
    idx = bisect.bisect_left(frames, frame)

    left: Optional[bpy.types.Keyframe] = None
    right: Optional[bpy.types.Keyframe] = None

    # Left: the keyframe just before 'frame'
    if idx > 0 and frames[idx - 1] < frame:
        left = keyframes[idx - 1]
    elif idx > 0 and frames[idx - 1] == frame and idx > 1:
        # Exact match — left is one further back
        left = keyframes[idx - 2]

    # Right: the keyframe just after 'frame'
    if idx < len(keyframes) and frames[idx] > frame:
        right = keyframes[idx]
    elif idx < len(keyframes) and frames[idx] == frame and idx + 1 < len(keyframes):
        right = keyframes[idx + 1]

    return (left, right)


def get_keyframe_at_frame(
    fcurve: bpy.types.FCurve,
    frame: float,
    tolerance: float = 0.01,
) -> Optional[bpy.types.Keyframe]:
    """Find a keyframe at or very near the given frame.

    Args:
        fcurve: The f-curve to search.
        frame: Target frame number.
        tolerance: Maximum frame distance to consider a match.

    Returns:
        Keyframe or None: The matching keyframe point, if found.
    """
    if fcurve is None:
        return None
    for keypoint in fcurve.keyframe_points:
        if abs(keypoint.co.x - frame) <= tolerance:
            return keypoint
    return None


# ---------------------------------------------------------------------------
# Handle Recalculation
# ---------------------------------------------------------------------------

def recalculate_handles(
    fcurve: bpy.types.FCurve,
    frame: float,
    new_value: float,
    mode: str = "free",
) -> bool:
    """Modify an f-curve so it passes through new_value at the given frame.

    This is the core function called when a ghost is dragged to a new
    position.  It adjusts the bezier handles of the surrounding keyframes
    to reshape the curve segment without adding or removing keyframes.

    Three modes are supported:
        - "free": Handles adjust both angle and length to hit the target.
        - "locked": Handle angles are preserved; only lengths change.
        - "smooth": Handle influence is redistributed evenly across the segment.

    Args:
        fcurve: The f-curve to modify.
        frame: The frame where the new value should appear.
        new_value: The desired f-curve value at this frame.
        mode: One of "free", "locked", "smooth".

    Returns:
        bool: True if the recalculation succeeded, False otherwise.
    """
    if fcurve is None:
        warn("recalculate_handles called with None fcurve")
        return False

    left_kp, right_kp = get_adjacent_keyframes(fcurve, frame)
    if left_kp is None or right_kp is None:
        warn(f"Cannot recalculate handles at frame {frame} — missing adjacent keyframes.")
        return False
    if left_kp.interpolation != 'BEZIER':
        # Handles only shape BEZIER segments. On LINEAR/CONSTANT the loop
        # below would push handle offsets forever with no effect, then
        # corrupt the curve the moment the user switches to Bezier.
        warn(f"Cannot reshape a {left_kp.interpolation} segment at frame {frame}; handles have no effect there.")
        return False

    try:
        if mode == "free":
            if not _recalc_free(fcurve, left_kp, right_kp, frame, new_value):
                return False
        elif mode == "locked":
            _recalc_locked(fcurve, left_kp, right_kp, frame, new_value)
        elif mode == "smooth":
            _recalc_smooth(fcurve, left_kp, right_kp, frame, new_value)
        else:
            warn(f"Unknown curve mode '{mode}', using 'free'")
            if not _recalc_free(fcurve, left_kp, right_kp, frame, new_value):
                return False

        # Clamp handles to prevent overshoot
        _clamp_handles(left_kp, right_kp)

        fcurve.update()
        return True

    except Exception as exc:
        warn(f"Error during handle recalculation: {exc}")
        return False


def _recalc_free(
    fcurve: bpy.types.FCurve,
    left_kp: bpy.types.Keyframe,
    right_kp: bpy.types.Keyframe,
    frame: float,
    new_value: float,
) -> bool:
    """Free mode: adjust handle angles and lengths to pass through the target.

    This uses a simple proportional offset approach.  The current
    midpoint value is compared to the desired value, and the handle
    offsets are adjusted proportionally.

    Args:
        fcurve: The f-curve being modified.
        left_kp: The keyframe to the left of the target frame.
        right_kp: The keyframe to the right of the target frame.
        frame: The target frame.
        new_value: The desired value at the target frame.
    """
    # Snapshot so a non-converging solve can be rolled back instead of
    # leaving partially pushed handles behind.
    orig_lr = tuple(left_kp.handle_right)
    orig_rl = tuple(right_kp.handle_left)
    orig_lrt = left_kp.handle_right_type
    orig_rlt = right_kp.handle_left_type

    # Set handles to FREE type so we can manipulate them directly
    left_kp.handle_right_type = 'FREE'
    right_kp.handle_left_type = 'FREE'

    # Current value at the target frame
    current_value = fcurve.evaluate(frame)
    delta = new_value - current_value

    if abs(delta) < 1e-7:
        return True

    # Parametric position of the frame within the segment [0..1]
    segment_width = right_kp.co.x - left_kp.co.x
    if segment_width < 0.001:
        return True
    parametric_position = (frame - left_kp.co.x) / segment_width

    # Distribute the correction to both handles based on parametric position.
    # The closer handle gets more influence (complement weighting).
    # Higher influence on the nearer keyframe's handle.
    left_influence = 1.0 - parametric_position
    right_influence = parametric_position

    # Adjust left keyframe's right handle (controls the exit from left KP)
    # INITIAL_HANDLE_DAMPING factor dampens handle movement to achieve gradual convergence
    left_kp.handle_right[1] += delta * left_influence * INITIAL_HANDLE_DAMPING
    # Adjust right keyframe's left handle (controls the entry to right KP)
    right_kp.handle_left[1] += delta * right_influence * INITIAL_HANDLE_DAMPING

    # Iterate to converge on the target value, since bezier
    # handle adjustments don't map linearly to midpoint values.
    # ITERATIVE_HANDLE_DAMPING factor reduces step size on iteration to avoid overshooting.
    # 5 iterations: free mode converges faster since both handles move independently
    residual = 0.0
    for iteration_num in range(MAX_CONVERGENCE_ITERATIONS):
        fcurve.update()
        current_value = fcurve.evaluate(frame)
        residual = new_value - current_value

        if abs(residual) < CONVERGENCE_THRESHOLD:
            break

        left_kp.handle_right[1] += residual * left_influence * ITERATIVE_HANDLE_DAMPING
        right_kp.handle_left[1] += residual * right_influence * ITERATIVE_HANDLE_DAMPING
    else:
        # Loop completed without converging: roll back and report failure so
        # callers stop claiming success on an unchanged (or damaged) curve.
        warn(f"Handle recalculation did not converge after {MAX_CONVERGENCE_ITERATIONS} iterations (residual: {residual:.6f})")
        left_kp.handle_right = orig_lr
        right_kp.handle_left = orig_rl
        left_kp.handle_right_type = orig_lrt
        right_kp.handle_left_type = orig_rlt
        fcurve.update()
        return False
    return True


def _recalc_locked(
    fcurve: bpy.types.FCurve,
    left_kp: bpy.types.Keyframe,
    right_kp: bpy.types.Keyframe,
    frame: float,
    new_value: float,
) -> None:
    """Locked mode: preserve handle angles, only adjust handle lengths.

    The direction from each keyframe to its handle is preserved, but the
    handle is extended or shortened to make the curve pass through the
    target value.

    Args:
        fcurve: The f-curve being modified.
        left_kp: The keyframe to the left of the target frame.
        right_kp: The keyframe to the right of the target frame.
        frame: The target frame.
        new_value: The desired value at the target frame.
    """
    left_kp.handle_right_type = 'FREE'
    right_kp.handle_left_type = 'FREE'

    current_value = fcurve.evaluate(frame)
    delta = new_value - current_value

    if abs(delta) < 1e-7:
        return

    segment_width = right_kp.co.x - left_kp.co.x
    if segment_width < 0.001:
        return
    parametric_position = (frame - left_kp.co.x) / segment_width

    # Compute handle direction vectors (from keyframe to handle tip)
    left_handle_dir = Vector((
        left_kp.handle_right[0] - left_kp.co.x,
        left_kp.handle_right[1] - left_kp.co.y,
    ))
    right_handle_dir = Vector((
        right_kp.handle_left[0] - right_kp.co.x,
        right_kp.handle_left[1] - right_kp.co.y,
    ))

    left_len = left_handle_dir.length
    right_len = right_handle_dir.length

    # Check for degenerate handles before attempting normalization
    if left_len < HANDLE_MIN_LENGTH or right_len < HANDLE_MIN_LENGTH:
        # Fall back to free mode if handles are degenerate
        _recalc_free(fcurve, left_kp, right_kp, frame, new_value)
        return

    # Normalize directions
    left_dir_norm = left_handle_dir / left_len
    right_dir_norm = right_handle_dir / right_len

    # Scale handles proportionally to close the gap
    # 8 iterations: locked mode needs more passes because handle directions are constrained
    residual = 0.0
    for iteration_num in range(8):
        fcurve.update()
        current_value = fcurve.evaluate(frame)
        residual = new_value - current_value
        if abs(residual) < CONVERGENCE_THRESHOLD:
            break

        # Scale factor: how much to stretch handles to achieve the residual
        # LOCKED_SCALE_DAMPING factor dampens scaling adjustments per iteration
        # max(abs(...), 0.1) prevents division by near-zero
        scale_left = 1.0 + (residual * (1.0 - parametric_position) * LOCKED_SCALE_DAMPING) / max(abs(left_len), 0.1)
        scale_right = 1.0 + (residual * parametric_position * LOCKED_SCALE_DAMPING) / max(abs(right_len), 0.1)

        # Clamp scale to prevent extreme handle lengths [HANDLE_SCALE_MIN to HANDLE_SCALE_MAX]
        # This prevents handles from growing unbounded or shrinking to zero
        scale_left = max(HANDLE_SCALE_MIN, min(scale_left, HANDLE_SCALE_MAX))
        scale_right = max(HANDLE_SCALE_MIN, min(scale_right, HANDLE_SCALE_MAX))

        new_left_handle = left_dir_norm * (left_len * scale_left)
        new_right_handle = right_dir_norm * (right_len * scale_right)

        left_kp.handle_right[0] = left_kp.co.x + new_left_handle.x
        left_kp.handle_right[1] = left_kp.co.y + new_left_handle.y
        right_kp.handle_left[0] = right_kp.co.x + new_right_handle.x
        right_kp.handle_left[1] = right_kp.co.y + new_right_handle.y

        left_len = new_left_handle.length
        right_len = new_right_handle.length
    else:
        # Loop completed without converging
        warn(f"Handle recalculation did not converge after 8 iterations (residual: {residual:.6f})")


def _recalc_smooth(
    fcurve: bpy.types.FCurve,
    left_kp: bpy.types.Keyframe,
    right_kp: bpy.types.Keyframe,
    frame: float,
    new_value: float,
) -> None:
    """Smooth mode: redistribute handle influence evenly across the segment.

    Both handles are reset to a balanced configuration first, then
    adjusted symmetrically to hit the target value.

    Args:
        fcurve: The f-curve being modified.
        left_kp: The keyframe to the left of the target frame.
        right_kp: The keyframe to the right of the target frame.
        frame: The target frame.
        new_value: The desired value at the target frame.
    """
    left_kp.handle_right_type = 'FREE'
    right_kp.handle_left_type = 'FREE'

    segment_width = right_kp.co.x - left_kp.co.x
    if segment_width < 0.001:
        return

    # Reset handles to a smooth balanced state (1/3 of segment width)
    one_third = segment_width / 3.0
    value_diff = right_kp.co.y - left_kp.co.y
    slope = value_diff / segment_width

    left_kp.handle_right[0] = left_kp.co.x + one_third
    left_kp.handle_right[1] = left_kp.co.y + slope * one_third

    right_kp.handle_left[0] = right_kp.co.x - one_third
    right_kp.handle_left[1] = right_kp.co.y - slope * one_third

    # Now iteratively adjust to hit the target
    # 8 iterations: smooth mode uses symmetric corrections requiring more passes
    residual = 0.0
    for iteration_num in range(8):
        fcurve.update()
        current_value = fcurve.evaluate(frame)
        residual = new_value - current_value
        if abs(residual) < CONVERGENCE_THRESHOLD:
            break

        # Apply correction symmetrically to both handles
        # SMOOTH_CORRECTION_DAMPING factor dampens step size to achieve smooth convergence
        correction = residual * SMOOTH_CORRECTION_DAMPING
        left_kp.handle_right[1] += correction
        right_kp.handle_left[1] += correction
    else:
        # Loop completed without converging
        warn(f"Handle recalculation did not converge after 8 iterations (residual: {residual:.6f})")


def _clamp_handles(
    left_kp: bpy.types.Keyframe,
    right_kp: bpy.types.Keyframe,
) -> None:
    """Clamp handle lengths to prevent overshoot and oscillation.

    Ensures that handles don't extend beyond a fraction of the segment
    width, which would cause the curve to overshoot the keyframe values.

    Args:
        left_kp: The left keyframe of the segment.
        right_kp: The right keyframe of the segment.
    """
    segment_width = right_kp.co.x - left_kp.co.x
    max_extend = segment_width * HANDLE_CLAMP_FACTOR

    if max_extend < HANDLE_MIN_LENGTH:
        return

    # Clamp left keyframe's right handle (shouldn't extend past the midpoint)
    # This handle controls the curve as it exits the left keyframe
    handle_dx = left_kp.handle_right[0] - left_kp.co.x
    if handle_dx > max_extend:
        # Handle exceeds max distance; scale it back and preserve Y angle
        scale = max_extend / handle_dx
        left_kp.handle_right[0] = left_kp.co.x + max_extend
        handle_dy = left_kp.handle_right[1] - left_kp.co.y
        left_kp.handle_right[1] = left_kp.co.y + handle_dy * scale
    elif handle_dx < 0:
        # Handle pointing backward (negative x direction) is invalid;
        # force it forward with minimum length
        left_kp.handle_right[0] = left_kp.co.x + HANDLE_MIN_LENGTH

    # Clamp right keyframe's left handle (shouldn't extend past the midpoint)
    # This handle controls the curve as it enters the right keyframe
    handle_dx = right_kp.handle_left[0] - right_kp.co.x
    if handle_dx < -max_extend:
        # Handle exceeds max distance (negative direction); scale it back
        # and preserve Y angle
        scale = max_extend / abs(handle_dx)
        right_kp.handle_left[0] = right_kp.co.x - max_extend
        handle_dy = right_kp.handle_left[1] - right_kp.co.y
        right_kp.handle_left[1] = right_kp.co.y + handle_dy * scale
    elif handle_dx > 0:
        # Handle pointing forward (positive x direction) is invalid;
        # force it backward with minimum length
        right_kp.handle_left[0] = right_kp.co.x - HANDLE_MIN_LENGTH


# ---------------------------------------------------------------------------
# World Position Evaluation
# ---------------------------------------------------------------------------

# World-position evaluation cache: avoids redundant scene.frame_set() calls.
# Structure: { frame_int: { (obj_name, bone_name, rounded_frame): Vector } }
# Entries are FIFO-evicted when size exceeds _FRAME_CACHE_MAX_SIZE.
_FRAME_CACHE_MAX_SIZE = 500
_frame_cache: dict[int, dict[str, Vector]] = {}


def clear_frame_cache() -> None:
    """Clear the world position evaluation cache.

    Should be called at the start of each ghost generation or drag update
    cycle to prevent stale data.
    """
    _frame_cache.clear()


def _evict_frame_cache_if_needed() -> None:
    """Evict oldest entries if cache exceeds max size.

    This prevents unbounded memory growth during long animation timelines
    by maintaining at most _FRAME_CACHE_MAX_SIZE entries. Oldest entries
    (first inserted) are removed when the limit is exceeded.
    """
    if len(_frame_cache) > _FRAME_CACHE_MAX_SIZE:
        # Remove oldest entries (first inserted)
        excess = len(_frame_cache) - _FRAME_CACHE_MAX_SIZE
        keys_to_remove = list(_frame_cache.keys())[:excess]
        for key in keys_to_remove:
            del _frame_cache[key]


@sampling_operation
def get_world_position_at_frame(
    obj: bpy.types.Object,
    bone_name: str,
    channel: str,
    frame: float,
) -> Vector:
    """Get the world-space position of an object or bone at a given frame.

    Temporarily sets the scene frame, evaluates the pose, and returns
    the world position.  Results are cached per frame to minimize the
    cost of repeated scene.frame_set() calls.

    Args:
        obj: The Blender object (armature or mesh).
        bone_name: The pose bone name, or empty string for object origin.
        channel: The channel identifier (used only for cache keying).
        frame: The frame to evaluate at.

    Returns:
        Vector: World-space position of the bone head or object origin.
    """
    scene = bpy.context.scene

    # Build a cache key
    int_frame = math.floor(frame)
    subframe = frame - int_frame
    cache_key = (scene.as_pointer(), obj.as_pointer(), bone_name, frame)

    if int_frame in _frame_cache and cache_key in _frame_cache[int_frame]:
        return _frame_cache[int_frame][cache_key].copy()

    # Save current frame
    original_frame = scene.frame_current
    original_subframe = scene.frame_subframe if hasattr(scene, 'frame_subframe') else 0.0

    try:
        scene.frame_set(int_frame, subframe=subframe)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        depsgraph.update()

        if bone_name and obj.type == 'ARMATURE':
            pose_bone = obj.pose.bones.get(bone_name)
            if pose_bone:
                world_pos = obj.matrix_world @ pose_bone.head.copy()
            else:
                warn(f"Bone '{bone_name}' not found on '{obj.name}'")
                world_pos = obj.matrix_world.translation.copy()
        else:
            world_pos = obj.matrix_world.translation.copy()

        # Cache the result
        if int_frame not in _frame_cache:
            _frame_cache[int_frame] = {}
        _frame_cache[int_frame][cache_key] = world_pos.copy()

        # Evict oldest entries if cache is growing too large
        _evict_frame_cache_if_needed()

        return world_pos.copy()

    except (AttributeError, TypeError, RuntimeError, ValueError) as exc:
        warn(f"Error evaluating world position at frame {frame}: {exc}")
        return Vector((0.0, 0.0, 0.0))

    finally:
        # Always restore the original frame including subframe
        scene.frame_set(original_frame, subframe=original_subframe)


# ---------------------------------------------------------------------------
# F-curve Snapshot for Undo Support
# ---------------------------------------------------------------------------

def set_handle_values(fcurve: bpy.types.FCurve, frame: float, side: str, value: float,
                      aligned: bool = False) -> bool:
    """Set the value of one handle of the key at ``frame``; its time stays, and so does the key.

    FREE: the other handle keeps its position; if it was Aligned it becomes Free too, so the pair is
    unlinked (Free after Aligned). ALIGNED: both handles become Aligned and the other one turns to stay
    collinear through the key, its time unchanged too. Returns False when there is no key at ``frame``.
    Handle types are set before the values, and the curve is not recalculated afterwards, because an
    Aligned recalculation keeps the other handle's length and would move its time."""
    if side not in ('LEFT', 'RIGHT'):
        raise ValueError("side must be 'LEFT' or 'RIGHT'")
    key = next((k for k in fcurve.keyframe_points if abs(k.co.x - frame) < 1e-4), None)
    if key is None:
        return False
    if aligned:
        key.handle_left_type = key.handle_right_type = 'ALIGNED'
    else:
        if side == 'LEFT':
            key.handle_left_type = 'FREE'
            if key.handle_right_type == 'ALIGNED':
                key.handle_right_type = 'FREE'
        else:
            key.handle_right_type = 'FREE'
            if key.handle_left_type == 'ALIGNED':
                key.handle_left_type = 'FREE'
    handle_x = (key.handle_left if side == 'LEFT' else key.handle_right).x
    other = key.handle_right if side == 'LEFT' else key.handle_left
    other_value = other.y
    if aligned and abs(handle_x - key.co.x) > 1e-9:
        slope = (value - key.co.y) / (handle_x - key.co.x)
        other_value = key.co.y + slope * (other.x - key.co.x)
    if side == 'LEFT':
        key.handle_left = (handle_x, value)
        key.handle_right = (other.x, other_value)
    else:
        key.handle_right = (handle_x, value)
        key.handle_left = (other.x, other_value)
    invalidate_keyframe_cache()
    return True


def snapshot_fcurve(fcurve: bpy.types.FCurve) -> list[dict]:
    """Capture the current state of an f-curve's keyframes and handles.

    Used before a ghost drag to enable cancellation / undo.

    Args:
        fcurve: The f-curve to snapshot.

    Returns:
        list[dict]: A list of dicts, one per keyframe, containing all
                    editable properties (co, handles, types, interpolation).
    """
    if fcurve is None:
        return []

    snapshot = []
    for keypoint in fcurve.keyframe_points:
        snapshot.append({
            "co": (keypoint.co.x, keypoint.co.y),
            "type": keypoint.type,
            "amplitude": keypoint.amplitude,
            "back": keypoint.back,
            "period": keypoint.period,
            "handle_left": (keypoint.handle_left[0], keypoint.handle_left[1]),
            "handle_right": (keypoint.handle_right[0], keypoint.handle_right[1]),
            "handle_left_type": keypoint.handle_left_type,
            "handle_right_type": keypoint.handle_right_type,
            "interpolation": keypoint.interpolation,
            "easing": keypoint.easing if hasattr(keypoint, 'easing') else 'AUTO',
        })
    return snapshot


def validate_curve_snapshot(snapshot):
    """Validate serialized keyframes completely before touching an f-curve."""
    if not isinstance(snapshot, list):
        raise ValueError("Curve keys must be a list")
    frames = set()
    for entry in snapshot:
        if not isinstance(entry, dict):
            raise ValueError("Keyframe must be an object")
        for field in ('co', 'handle_left', 'handle_right'):
            pair = entry.get(field)
            if not isinstance(pair, (list, tuple)) or len(pair) != 2 or any(
                    isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in pair):
                raise ValueError("Invalid keyframe coordinates")
        if entry['co'][0] in frames:
            raise ValueError("Duplicate keyframe times")
        frames.add(entry['co'][0])
        for field in ('handle_left_type', 'handle_right_type', 'interpolation', 'easing', 'type'):
            value = entry.get(field)
            if value is None and field in ('easing', 'type'):
                continue
            if value not in bpy.types.Keyframe.bl_rna.properties[field].enum_items.keys():
                raise ValueError(f"Invalid keyframe {field}")
        for field in ('amplitude', 'back', 'period'):
            if field in entry and (not isinstance(entry[field], (int, float)) or not math.isfinite(entry[field])):
                raise ValueError(f"Invalid keyframe {field}")


def restore_fcurve(fcurve: bpy.types.FCurve, snapshot: list[dict]) -> bool:
    """Restore an f-curve to a previously captured snapshot state.

    Validates and reconstructs keyframes, including original times, handles,
    interpolation, and easing. Keys added since capture are removed.

    Args:
        fcurve: The f-curve to restore.
        snapshot: The snapshot data from snapshot_fcurve().

    Returns:
        bool: True if restoration succeeded, False otherwise.
    """
    if fcurve is None or not isinstance(snapshot, list):
        return False
    try:
        validate_curve_snapshot(snapshot)
        entries = sorted(snapshot, key=lambda entry: entry['co'][0])
        fcurve.keyframe_points.clear()
        fcurve.keyframe_points.add(len(entries))
        for point, entry in zip(fcurve.keyframe_points, entries):
            point.co = entry['co']
            point.handle_left_type = entry['handle_left_type']
            point.handle_right_type = entry['handle_right_type']
            point.interpolation = entry['interpolation']
            point.easing = entry.get('easing', 'AUTO')
            for field in ('amplitude', 'back', 'period', 'type'):
                if field in entry:
                    setattr(point, field, entry[field])
            point.handle_left = entry['handle_left']
            point.handle_right = entry['handle_right']
        fcurve.update()
        # Keep explicitly captured handles, including manually adjusted AUTO ones.
        for point, entry in zip(fcurve.keyframe_points, entries):
            point.handle_left = entry['handle_left']
            point.handle_right = entry['handle_right']
        invalidate_keyframe_cache()
        clear_frame_cache()
        return True
    except (KeyError, TypeError, ValueError, RuntimeError, ReferenceError) as exc:
        warn(f"Error restoring fcurve snapshot: {exc}")
        return False


# ---------------------------------------------------------------------------
# F-curve Channel Resolution
# ---------------------------------------------------------------------------

def resolve_fcurve(
    obj: bpy.types.Object,
    bone_name: str,
    channel: str,
) -> Optional[bpy.types.FCurve]:
    """Resolve a bone/channel pair to an actual FCurve on the object's action.

    Compatible with both legacy (Blender < 4.4) and slotted (5.x+) Actions.

    Args:
        obj: The Blender object (must have animation data with an action).
        bone_name: Pose bone name, or empty string for object channels.
        channel: Channel identifier like "location.x" or "rotation_euler.z".

    Returns:
        FCurve or None: The resolved f-curve, or None if not found.
    """
    from .utils import find_fcurve_in_action

    if not obj or not obj.animation_data or not obj.animation_data.action:
        return None

    action = obj.animation_data.action
    axis_map = {"x": 0, "y": 1, "z": 2, "w": 3}

    parts = channel.rsplit(".", 1)
    if len(parts) == 2:
        prop_name = parts[0]
        axis = parts[1].lower()
        if prop_name == "rotation_quaternion":
            axis_map = {"w": 0, "x": 1, "y": 2, "z": 3}
        array_index = axis_map.get(axis, 0)
    else:
        prop_name = channel
        array_index = 0

    if bone_name:
        data_path = f'pose.bones["{bpy.utils.escape_identifier(bone_name)}"].{prop_name}'
    else:
        data_path = prop_name

    # Use the compatibility helper that handles both legacy and slotted APIs
    return find_fcurve_in_action(action, data_path, array_index, obj=obj)


# ---------------------------------------------------------------------------
# Easing Preset Application (delegates to easing_presets module)
# ---------------------------------------------------------------------------

def insert_keyframe_from_ghost(
    fcurve: bpy.types.FCurve,
    frame: float,
    value: float,
    handle_type: str = "AUTO_CLAMPED",
) -> bool:
    """Insert a real keyframe at a ghost's position (Model A editing).

    This is the core function for "ghost becomes key" — when the user
    confirms a drag with INSERT_KEY editing mode, this function creates
    a new keyframe on the f-curve at the ghost's frame with the ghost's
    current value.

    After insertion, the new keyframe's handles are set to the specified
    type.  The f-curve is updated to reflect the topology change.

    Args:
        fcurve: The f-curve to insert the keyframe on.
        frame: The frame number for the new keyframe.
        value: The f-curve value at this frame.
        handle_type: Blender handle type for the new keyframe.
            One of 'FREE', 'ALIGNED', 'VECTOR', 'AUTO', 'AUTO_CLAMPED'.
            Defaults to 'AUTO_CLAMPED' for predictable curve shapes.

    Returns:
        bool: True if insertion succeeded, False otherwise.
    """
    if fcurve is None:
        warn("insert_keyframe_from_ghost called with None fcurve")
        return False

    try:
        # Check if a keyframe already exists at this frame (within tolerance).
        # Use tight tolerance to avoid silently overwriting adjacent keys —
        # subdivision ghosts sit at fractional frames like 10.25, 10.5, etc.
        existing = get_keyframe_at_frame(fcurve, frame, tolerance=KEYFRAME_FRAME_TOLERANCE)
        if existing is not None:
            # Update the existing keyframe's value instead of inserting a duplicate
            existing.co.y = value
            existing.handle_left_type = handle_type
            existing.handle_right_type = handle_type
            fcurve.update()
            log(f"Updated existing keyframe at frame {frame:.1f} to value {value:.4f}")
            return True

        # Insert a new keyframe using the FAST option to avoid automatic
        # handle recalculation (we set handles explicitly below).
        keyframe = fcurve.keyframe_points.insert(
            frame, value, options={'FAST'}
        )

        # Set handle types on the new keyframe
        keyframe.handle_left_type = handle_type
        keyframe.handle_right_type = handle_type
        keyframe.interpolation = 'BEZIER'

        # Update the f-curve to recalculate all handles
        fcurve.update()

        log(f"Inserted keyframe at frame {frame:.1f} with value {value:.4f}")
        return True

    except Exception as exc:
        warn(f"Error inserting keyframe at frame {frame}: {exc}")
        return False


def apply_easing_preset(
    fcurve: bpy.types.FCurve,
    frame_a: float,
    frame_b: float,
    preset_name: str,
) -> bool:
    """Apply a named easing preset to the f-curve handles between two keyframes.

    This function delegates to easing_presets.apply_preset_to_range() but
    provides a stable interface for use by other Ghost Tool modules.

    Args:
        fcurve: The f-curve to modify.
        frame_a: Frame of the left keyframe.
        frame_b: Frame of the right keyframe.
        preset_name: Identifier of the preset (e.g. "EASE_IN", "BOUNCE").

    Returns:
        bool: True if the preset was applied successfully, False otherwise.
    """
    # Lazy import to avoid circular dependency at module load time
    try:
        from . import easing_presets
        return easing_presets.apply_preset_to_range(fcurve, frame_a, frame_b, preset_name)
    except ImportError:
        warn("easing_presets module not available")
        return False
    except Exception as exc:
        warn(f"Error applying easing preset '{preset_name}': {exc}")
        return False


# ---------------------------------------------------------------------------
# Test notes
# ---------------------------------------------------------------------------
#
# Test 1: sample_fcurve handles None gracefully
# >>> val = sample_fcurve(None, 10.0)
# >>> assert val == 0.0
#
# Test 2: get_adjacent_keyframes finds correct neighbors
# >>> # Setup: object with keyframes at frames 1, 10, 20
# >>> left, right = get_adjacent_keyframes(fcurve, 15.0)
# >>> assert left.co.x == 10.0 and right.co.x == 20.0
#
# Test 3: recalculate_handles adjusts curve to hit target value
# >>> original = fcurve.evaluate(5.0)
# >>> recalculate_handles(fcurve, 5.0, original + 2.0, mode="free")
# >>> new_val = fcurve.evaluate(5.0)
# >>> assert abs(new_val - (original + 2.0)) < 0.1
#
# Test 4: snapshot_fcurve / restore_fcurve round-trips correctly
# >>> snap = snapshot_fcurve(fcurve)
# >>> recalculate_handles(fcurve, 5.0, 999.0)
# >>> restore_fcurve(fcurve, snap)
# >>> assert abs(fcurve.evaluate(5.0) - original) < 0.01
