"""path_fast_sampler.py — motion path positions straight from the curves, without frame_set (design §8 dec. 13).

Only for targets where it provably matches frame stepping: an object or a bone head/tail whose motion is
its own location/rotation/scale curves and its parents' (a bone chain under an armature). Anything Blender
evaluates that these few lines do not model — constraints, drivers, NLA, an animated or bone parent, delta
rotation/scale, bones that do not inherit rotation/scale normally — makes the target ineligible, and the
caller keeps stepping frames for it. A wrong path looks exactly like a right one, so eligibility is strict.
"""

from __future__ import annotations

from typing import Optional

import bpy
from mathutils import Euler, Matrix, Quaternion, Vector

from .utils import get_fcurves_from_action

EULER_ORDERS = {'XYZ', 'XZY', 'YXZ', 'YZX', 'ZXY', 'ZYX'}


def _animation_is_plain(id_block) -> bool:
    """No drivers, no NLA, and the active action at full influence in Replace or Combine mode. Blender 5
    creates actions in Combine; with no NLA underneath it layers onto the defaults (location + 0,
    rotation x identity, scale x 1), which equals Replace. Add and Multiply do not, so they step."""
    ad = getattr(id_block, "animation_data", None)
    if ad is None:
        return True
    if len(ad.drivers) or len(ad.nla_tracks):
        return False
    if getattr(ad, "action_influence", 1.0) != 1.0:
        return False
    if getattr(ad, "action_blend_type", 'REPLACE') not in {'REPLACE', 'COMBINE'}:
        return False
    return True


def _static(obj) -> bool:
    """An object whose world matrix does not change over time: no animation, constraints or moving parent."""
    ad = obj.animation_data
    if ad is not None and (ad.action is not None or len(ad.drivers) or len(ad.nla_tracks)):
        return False
    if len(obj.constraints):
        return False
    return obj.parent is None or (obj.parent_type == 'OBJECT' and _static(obj.parent))


def _keyed_paths(obj) -> set[str]:
    ad = obj.animation_data
    action = ad.action if ad else None
    return {fc.data_path for fc in get_fcurves_from_action(action, obj)} if action else set()


def _deltas_neutral(obj) -> bool:
    """Delta rotation and scale are not modelled: they must be neutral and not keyed (a keyed delta changes
    over time even when its current value is neutral). Delta location is modelled, keyed or not."""
    if _keyed_paths(obj) & {"delta_scale", "delta_rotation_euler", "delta_rotation_quaternion"}:
        return False
    if tuple(obj.delta_scale) != (1.0, 1.0, 1.0):
        return False
    if obj.rotation_mode == 'QUATERNION':
        return tuple(obj.delta_rotation_quaternion) == (1.0, 0.0, 0.0, 0.0)
    return tuple(obj.delta_rotation_euler) == (0.0, 0.0, 0.0)


def _bone_chain_plain(pose_bone) -> bool:
    pb = pose_bone
    while pb is not None:
        bone = pb.bone
        if len(pb.constraints) or not bone.use_inherit_rotation or bone.inherit_scale != 'FULL':
            return False
        if not bone.use_local_location or bone.use_relative_parent:
            return False
        if pb.rotation_mode not in EULER_ORDERS | {'QUATERNION', 'AXIS_ANGLE'}:
            return False
        pb = pb.parent
    return True


def time_is_plain(scene) -> bool:
    """Curves are evaluated at the scene frame only without Time Remapping (frame_map_old == frame_map_new)."""
    return scene is None or scene.render.frame_map_old == scene.render.frame_map_new


def fast_eligible(obj, bone_name: str = "", vertex_index: int = -1, scene=None) -> bool:
    """True only when sample_fast provably equals stepping the frames for this target (in ``scene``)."""
    if obj is None or vertex_index >= 0 or not time_is_plain(scene):
        return False
    if len(obj.constraints) or not _animation_is_plain(obj) or not _deltas_neutral(obj):
        return False
    if obj.rotation_mode not in EULER_ORDERS | {'QUATERNION', 'AXIS_ANGLE'}:
        return False
    if obj.parent is not None and (obj.parent_type != 'OBJECT' or not _static(obj.parent)):
        return False
    if bone_name:
        if obj.type != 'ARMATURE' or bone_name not in obj.pose.bones:
            return False
        return _bone_chain_plain(obj.pose.bones[bone_name])
    return True


class _Curves:
    """The object's action curves by (data path, index), read once per batch of frames."""

    def __init__(self, obj):
        ad = obj.animation_data
        action = ad.action if ad else None
        self.by_path = {}
        for fc in get_fcurves_from_action(action, obj) if action else ():
            self.by_path[(fc.data_path, fc.array_index)] = fc

    def value(self, data_path: str, index: int, frame: float, current: float) -> float:
        fc = self.by_path.get((data_path, index))
        return fc.evaluate(frame) if fc is not None else current


def _rotation(curves: _Curves, prefix: str, holder, frame: float) -> Matrix:
    mode = holder.rotation_mode
    if mode == 'QUATERNION':
        q = Quaternion([curves.value(prefix + "rotation_quaternion", i, frame, holder.rotation_quaternion[i])
                        for i in range(4)])
        return q.normalized().to_matrix().to_4x4() if q.magnitude > 1e-12 else Matrix.Identity(4)
    if mode == 'AXIS_ANGLE':
        w = [curves.value(prefix + "rotation_axis_angle", i, frame, holder.rotation_axis_angle[i]) for i in range(4)]
        axis = Vector(w[1:])
        return Matrix.Rotation(w[0], 4, axis.normalized()) if axis.length > 1e-12 else Matrix.Identity(4)
    e = [curves.value(prefix + "rotation_euler", i, frame, holder.rotation_euler[i]) for i in range(3)]
    return Euler(e, mode).to_matrix().to_4x4()


def _basis(curves: _Curves, prefix: str, holder, frame: float, location_offset=None, use_location=True) -> Matrix:
    loc = Vector([curves.value(prefix + "location", i, frame, holder.location[i]) for i in range(3)])
    if location_offset is not None:
        loc += location_offset
    scale = [curves.value(prefix + "scale", i, frame, holder.scale[i]) for i in range(3)]
    translation = Matrix.Translation(loc) if use_location else Matrix.Identity(4)
    return translation @ _rotation(curves, prefix, holder, frame) @ Matrix.Diagonal((*scale, 1.0))


def _object_world(obj, curves: _Curves, frame: float) -> Matrix:
    # Delta location may be keyed: evaluate it at the frame like location (review 52c23eca).
    delta = Vector([curves.value("delta_location", i, frame, obj.delta_location[i]) for i in range(3)])
    basis = _basis(curves, "", obj, frame, location_offset=delta)
    if obj.parent is None:
        return basis
    return obj.parent.matrix_world @ obj.matrix_parent_inverse @ basis   # the parent is static (eligibility)


def _bone_pose(obj, curves: _Curves, pose_bone, frame: float, memo: dict) -> Matrix:
    """Armature-space pose matrix of ``pose_bone`` at ``frame``: channel matrix @ basis, up the chain."""
    if pose_bone.name in memo:
        return memo[pose_bone.name]
    bone = pose_bone.bone
    prefix = f'pose.bones["{bpy.utils.escape_identifier(pose_bone.name)}"].'
    # A connected bone ignores its location channels.
    basis = _basis(curves, prefix, pose_bone, frame, use_location=not bone.use_connect)
    if pose_bone.parent is None:
        channel = bone.matrix_local
    else:
        parent_pose = _bone_pose(obj, curves, pose_bone.parent, frame, memo)
        channel = parent_pose @ pose_bone.parent.bone.matrix_local.inverted() @ bone.matrix_local
    memo[pose_bone.name] = channel @ basis
    return memo[pose_bone.name]


def sample_fast(obj, bone_name: str, anchor: str, frames) -> list[Vector]:
    """World positions of an eligible target (object origin, or a bone's head or tail) at each frame."""
    curves = _Curves(obj)
    out = []
    for frame in frames:
        world = _object_world(obj, curves, frame)
        if not bone_name:
            out.append(world.translation.copy())
            continue
        pose_bone = obj.pose.bones[bone_name]
        pose = _bone_pose(obj, curves, pose_bone, frame, {})
        local = pose @ Vector((0.0, pose_bone.bone.length, 0.0)) if anchor == 'TAIL' else pose.translation
        out.append(world @ local)
    return out


def first_ineligibility(obj, bone_name: str = "") -> Optional[str]:
    """A short reason the target is not fast-eligible, for debug logs and tests; None when eligible."""
    checks = [
        (lambda: len(obj.constraints) == 0, "object constraints"),
        (lambda: _animation_is_plain(obj), "drivers, NLA or a blended action"),
        (lambda: _deltas_neutral(obj), "delta rotation or scale"),
        (lambda: obj.parent is None or (obj.parent_type == 'OBJECT' and _static(obj.parent)),
         "an animated, constrained or bone parent"),
    ]
    for ok, reason in checks:
        if not ok():
            return reason
    if bone_name and not _bone_chain_plain(obj.pose.bones[bone_name]):
        return "a bone in the chain has constraints or non-default inheritance"
    return None
