"""
motion_channels.py — Which channels ghost markers follow, and how a dragged
marker maps back onto them.

Location channels move a bone's head, so their markers sit on the head and a
drag converts straight into a location offset.  Rotation channels never move
a bone's own head (the head is the pivot), so their markers sit on the bone's
tail, and a drag re-aims the bone at the cursor: the swing that carries the
old tail direction onto the new one is applied around the head and converted
back into the bone's rotation channels.

All functions here are pure math over captured matrices, so they can be
tested without a viewport or a modal operator.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import bpy
from mathutils import Euler, Matrix, Quaternion, Vector

LOCATION_CHANNELS: list[str] = ["location.x", "location.y", "location.z"]
ROTATION_EULER_CHANNELS: list[str] = ["rotation_euler.x", "rotation_euler.y", "rotation_euler.z"]
ROTATION_QUAT_CHANNELS: list[str] = [
    "rotation_quaternion.w", "rotation_quaternion.x",
    "rotation_quaternion.y", "rotation_quaternion.z",
]

#: Channels Generate looks for. Missing f-curves are skipped, so a bone only
#: gets markers for what is actually animated.
MOTION_CHANNELS: list[str] = LOCATION_CHANNELS + ROTATION_EULER_CHANNELS + ROTATION_QUAT_CHANNELS

_AXIS_INDEX = {"x": 0, "y": 1, "z": 2}
_QUAT_INDEX = {"w": 0, "x": 1, "y": 2, "z": 3}


def channel_family(channel: str) -> str:
    """"location", "rotation_euler", "rotation_quaternion", or the prefix as-is."""
    return channel.rsplit(".", 1)[0]


def is_rotation_channel(channel: str) -> bool:
    return channel_family(channel) in ("rotation_euler", "rotation_quaternion")


def channel_component(channel: str) -> int:
    family, _, axis = channel.rpartition(".")
    table = _QUAT_INDEX if family == "rotation_quaternion" else _AXIS_INDEX
    return table.get(axis.lower(), 0)


def rest_channel_matrix(pose_bone: bpy.types.PoseBone, parent_pose_matrix: Optional[Matrix]) -> Matrix:
    """Armature-space matrix the bone's local channels are expressed in.

    ``pose_bone.matrix = channel_matrix @ matrix_basis`` for a bone that
    inherits rotation and scale (the common case).
    """
    bone = pose_bone.bone
    if pose_bone.parent is not None and parent_pose_matrix is not None:
        return parent_pose_matrix @ pose_bone.parent.bone.matrix_local.inverted() @ bone.matrix_local
    return bone.matrix_local.copy()


@dataclass
class RotationDragFrame:
    """The bone's state at the dragged marker's frame, captured once per drag."""

    world: Matrix              # armature object's matrix_world at the frame
    pose: Matrix               # pose_bone.matrix (armature space) at the frame
    channel_matrix: Matrix     # rest_channel_matrix at the frame
    rotation_mode: str
    euler: Euler               # basis rotation at the frame (for compatible solutions)
    quaternion: Quaternion
    length: float              # rest length; the pose matrix carries any scale

    @property
    def head_world(self) -> Vector:
        return self.world @ self.pose.translation

    @property
    def tail_world(self) -> Vector:
        return self.world @ (self.pose @ Vector((0.0, self.length, 0.0)))


def capture_rotation_frame(scene: bpy.types.Scene, obj: bpy.types.Object, bone_name: str,
                           frame: float) -> Optional[RotationDragFrame]:
    """Evaluate ``bone_name`` at ``frame`` and return what a rotation drag needs.

    Moves the scene to ``frame`` and back; call it once when a drag starts,
    never from a draw handler.
    """
    pose_bone = obj.pose.bones.get(bone_name) if obj.type == "ARMATURE" else None
    if pose_bone is None:
        return None
    original = scene.frame_current_final
    try:
        whole = int(frame // 1)
        scene.frame_set(whole, subframe=frame - whole)
        parent_matrix = pose_bone.parent.matrix.copy() if pose_bone.parent else None
        captured = RotationDragFrame(
            world=obj.matrix_world.copy(),
            pose=pose_bone.matrix.copy(),
            channel_matrix=rest_channel_matrix(pose_bone, parent_matrix),
            rotation_mode=pose_bone.rotation_mode,
            euler=pose_bone.rotation_euler.copy(),
            quaternion=pose_bone.rotation_quaternion.copy(),
            length=pose_bone.length,
        )
        return captured
    finally:
        whole = int(original // 1)
        scene.frame_set(whole, subframe=original - whole)


def solve_rotation_drag(captured: RotationDragFrame, target_world: Vector) -> dict[str, float]:
    """Channel values that swing the bone so its tail points at ``target_world``.

    Returns every rotation channel of the bone's rotation mode, e.g.
    ``{"rotation_euler.x": ..., "rotation_euler.y": ..., "rotation_euler.z": ...}``.
    Values stay continuous with the captured rotation (no 360-degree flips,
    no quaternion sign flips).
    """
    head = captured.head_world
    old_dir = captured.tail_world - head
    new_dir = target_world - head
    if old_dir.length < 1e-9 or new_dir.length < 1e-9:
        return {}

    world_rot = captured.world.to_3x3().normalized()
    swing_world = old_dir.rotation_difference(new_dir).to_matrix()
    swing_armature = world_rot.inverted() @ swing_world @ world_rot

    pose_rot = captured.pose.to_3x3()
    new_pose_rot = swing_armature @ pose_rot
    basis_rot = (captured.channel_matrix.to_3x3().inverted() @ new_pose_rot).normalized()

    if captured.rotation_mode == "QUATERNION":
        quat = basis_rot.to_quaternion()
        if quat.dot(captured.quaternion) < 0.0:
            quat.negate()
        return {f"rotation_quaternion.{axis}": quat[index] for axis, index in _QUAT_INDEX.items()}
    if captured.rotation_mode == "AXIS_ANGLE":
        return {}
    euler = basis_rot.to_euler(captured.rotation_mode, captured.euler)
    return {f"rotation_euler.{axis}": euler[index] for axis, index in _AXIS_INDEX.items()}


def bone_tail_world(obj: bpy.types.Object, pose_bone: bpy.types.PoseBone) -> Vector:
    return obj.matrix_world @ pose_bone.tail


__all__ = [
    "LOCATION_CHANNELS",
    "MOTION_CHANNELS",
    "ROTATION_EULER_CHANNELS",
    "ROTATION_QUAT_CHANNELS",
    "RotationDragFrame",
    "bone_tail_world",
    "capture_rotation_frame",
    "channel_component",
    "channel_family",
    "is_rotation_channel",
    "rest_channel_matrix",
    "solve_rotation_drag",
]
