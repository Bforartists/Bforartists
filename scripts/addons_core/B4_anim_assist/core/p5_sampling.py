# --- TRAJECTORY VISUALIZATION ---
"""Path sampler for trajectory overlays.

Two sampling modes:

1. **Fast (fcurve-only)** — evaluates location fcurves directly via
   ``fc.evaluate(frame)`` and computes world position from the rest-pose
   armature matrix.  No ``scene.frame_set()`` calls, no depsgraph
   evaluation.  Suitable for most workflows.

2. **Constraint-evaluated** — walks the timeline with
   ``scene.frame_set(f)`` + ``depsgraph.update()`` and reads the
   evaluated ``matrix_world``.  Accurate for IK/constraints but
   orders of magnitude slower.  Opt-in via ``use_constraints=True``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

try:
    import bpy
    from mathutils import Matrix, Vector
except Exception:  # pragma: no cover
    bpy = None  # type: ignore[assignment]
    Matrix = Vector = None  # type: ignore[assignment,misc]

from .fcurve_compat import get_fcurves

__all__ = [
    "SamplePoint",
    "VelocityInfo",
    "sample_path_fast",
    "sample_path_constraints",
    "derive_velocity",
    "segment_lengths",
]


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class SamplePoint:
    """One sampled position on the trajectory."""

    frame: float
    world_pos: tuple[float, float, float]
    local_pos: tuple[float, float, float]
    is_keyframe: bool = False


@dataclass
class VelocityInfo:
    """Derived velocity/acceleration data between consecutive samples."""

    frame: float
    world_pos: tuple[float, float, float]
    velocity: tuple[float, float, float]
    speed: float
    acceleration: tuple[float, float, float]
    accel_magnitude: float


# ---------------------------------------------------------------------------
# Fast fcurve-only sampler
# ---------------------------------------------------------------------------

def _find_location_fcurves(action, data_path_prefix: str):
    """Return a dict {array_index: FCurve} for location channels."""
    if action is None:
        return {}
    target_path = f"{data_path_prefix}.location" if data_path_prefix else "location"
    result = {}
    for fc in get_fcurves(action):
        if fc.data_path == target_path:
            result[fc.array_index] = fc
    return result


def _keyframe_set(action, data_path_prefix: str) -> set[float]:
    """Return the set of keyed frames on any location channel."""
    loc_fcs = _find_location_fcurves(action, data_path_prefix)
    frames: set[float] = set()
    for fc in loc_fcs.values():
        for kp in fc.keyframe_points:
            frames.add(round(float(kp.co.x), 4))
    return frames


def sample_path_fast(
    obj,
    bone_name: str | None,
    action,
    frame_start: float,
    frame_end: float,
    step: float = 1.0,
    *,
    max_samples: int = 500,
) -> list[SamplePoint]:
    """Sample a trajectory using fcurve evaluation only (no depsgraph).

    Returns an empty list if no location fcurves exist for the target.
    """
    if bpy is None or obj is None or action is None or Vector is None:
        return []

    if bone_name:
        escaped = bone_name.replace('"', r'\"')
        prefix = f'pose.bones["{escaped}"]'
    else:
        prefix = ""

    loc_fcs = _find_location_fcurves(action, prefix)
    if not loc_fcs:
        return []

    keyed_frames = _keyframe_set(action, prefix)

    # Compute the rest-pose world matrix for the bone / object.
    arm_world = obj.matrix_world if obj else Matrix.Identity(4)
    bone_rest = Matrix.Identity(4)
    if bone_name and obj and obj.type == "ARMATURE":
        arm_data = obj.data
        if arm_data and bone_name in arm_data.bones:
            bone_rest = arm_data.bones[bone_name].matrix_local

    # Object location is already in parent coordinates. Its current world
    # matrix includes that animated translation (and its own rotation/scale);
    # applying it to sampled location would add the current pose twice.
    rest_world = (arm_world @ bone_rest if bone_name else
                  arm_world @ obj.matrix_basis.inverted_safe())
    fallback = tuple(obj.pose.bones[bone_name].location) if bone_name else tuple(obj.location)

    samples: list[SamplePoint] = []
    f = float(frame_start)
    end = float(frame_end)
    step = max(step, 0.01)
    count = 0

    while f <= end + 1e-4 and count < max_samples:
        lx = float(loc_fcs[0].evaluate(f)) if 0 in loc_fcs else fallback[0]
        ly = float(loc_fcs[1].evaluate(f)) if 1 in loc_fcs else fallback[1]
        lz = float(loc_fcs[2].evaluate(f)) if 2 in loc_fcs else fallback[2]

        local = (lx, ly, lz)
        world_v = rest_world @ Vector((lx, ly, lz, 1.0))
        world = (float(world_v.x), float(world_v.y), float(world_v.z))

        is_key = round(f, 4) in keyed_frames

        samples.append(SamplePoint(
            frame=round(f, 4),
            world_pos=world,
            local_pos=local,
            is_keyframe=is_key,
        ))
        f += step
        count += 1

    return samples


# ---------------------------------------------------------------------------
# Constraint-evaluated sampler
# ---------------------------------------------------------------------------

def sample_path_constraints(
    context,
    obj,
    bone_name: str | None,
    frame_start: float,
    frame_end: float,
    step: float = 1.0,
    *,
    max_samples: int = 200,
) -> list[SamplePoint]:
    """Sample a trajectory using depsgraph evaluation (constraint-accurate).

    **Expensive** — calls ``scene.frame_set()`` for every sample.
    """
    if bpy is None or context is None or Vector is None:
        return []

    scene = context.scene
    depsgraph = context.evaluated_depsgraph_get()
    action = None
    adata = getattr(obj, "animation_data", None)
    if adata:
        action = adata.action

    prefix = ""
    if bone_name:
        escaped = bone_name.replace('"', r'\"')
        prefix = f'pose.bones["{escaped}"]'

    keyed_frames = _keyframe_set(action, prefix) if action else set()

    original_frame = scene.frame_current
    original_sub = getattr(scene, "frame_subframe", 0.0)

    samples: list[SamplePoint] = []
    f = float(frame_start)
    end = float(frame_end)
    step = max(step, 0.01)
    count = 0

    try:
        while f <= end + 1e-4 and count < max_samples:
            int_f = int(f)
            sub_f = f - int_f
            try:
                scene.frame_set(int_f, subframe=sub_f)
            except TypeError:
                scene.frame_set(int_f)
            depsgraph.update()

            obj_eval = obj.evaluated_get(depsgraph)
            if bone_name and obj.type == "ARMATURE":
                pb = obj_eval.pose.bones.get(bone_name)
                if pb is not None:
                    world_mat = obj_eval.matrix_world @ pb.matrix
                    world = (
                        float(world_mat[0][3]),
                        float(world_mat[1][3]),
                        float(world_mat[2][3]),
                    )
                    local_v = pb.location
                    local = (float(local_v.x), float(local_v.y), float(local_v.z))
                else:
                    world = (0.0, 0.0, 0.0)
                    local = (0.0, 0.0, 0.0)
            else:
                world_mat = obj_eval.matrix_world
                world = (
                    float(world_mat[0][3]),
                    float(world_mat[1][3]),
                    float(world_mat[2][3]),
                )
                local = (
                    float(obj_eval.location.x),
                    float(obj_eval.location.y),
                    float(obj_eval.location.z),
                )

            is_key = round(f, 4) in keyed_frames
            samples.append(SamplePoint(
                frame=round(f, 4),
                world_pos=world,
                local_pos=local,
                is_keyframe=is_key,
            ))
            f += step
            count += 1
    finally:
        try:
            scene.frame_set(original_frame, subframe=original_sub)
        except TypeError:
            scene.frame_set(original_frame)

    return samples


# ---------------------------------------------------------------------------
# Velocity / acceleration derivation
# ---------------------------------------------------------------------------

def derive_velocity(samples: list[SamplePoint]) -> list[VelocityInfo]:
    """Compute per-sample velocity and acceleration from position samples.

    Returns one fewer entry than ``samples`` (no velocity at sample 0).
    """
    if len(samples) < 2:
        return []

    velocities: list[VelocityInfo] = []
    prev = samples[0]
    for cur in samples[1:]:
        dt = cur.frame - prev.frame
        if dt <= 0.0:
            prev = cur
            continue
        vx = (cur.world_pos[0] - prev.world_pos[0]) / dt
        vy = (cur.world_pos[1] - prev.world_pos[1]) / dt
        vz = (cur.world_pos[2] - prev.world_pos[2]) / dt
        speed = math.sqrt(vx * vx + vy * vy + vz * vz)
        velocities.append(VelocityInfo(
            frame=cur.frame,
            world_pos=cur.world_pos,
            velocity=(vx, vy, vz),
            speed=speed,
            acceleration=(0.0, 0.0, 0.0),
            accel_magnitude=0.0,
        ))
        prev = cur

    # Compute acceleration (derivative of velocity).
    for i in range(1, len(velocities)):
        v_prev = velocities[i - 1]
        v_cur = velocities[i]
        dt = v_cur.frame - v_prev.frame
        if dt <= 0.0:
            continue
        ax = (v_cur.velocity[0] - v_prev.velocity[0]) / dt
        ay = (v_cur.velocity[1] - v_prev.velocity[1]) / dt
        az = (v_cur.velocity[2] - v_prev.velocity[2]) / dt
        v_cur.acceleration = (ax, ay, az)
        v_cur.accel_magnitude = math.sqrt(ax * ax + ay * ay + az * az)

    return velocities


# ---------------------------------------------------------------------------
# Segment lengths
# ---------------------------------------------------------------------------

def segment_lengths(samples: list[SamplePoint]) -> list[float]:
    """Return distances between consecutive samples."""
    lengths: list[float] = []
    for i in range(1, len(samples)):
        dx = samples[i].world_pos[0] - samples[i - 1].world_pos[0]
        dy = samples[i].world_pos[1] - samples[i - 1].world_pos[1]
        dz = samples[i].world_pos[2] - samples[i - 1].world_pos[2]
        lengths.append(math.sqrt(dx * dx + dy * dy + dz * dz))
    return lengths
