# --- MATCHING TRANSFORM MATH ---
"""Pure-ish transform matching and space-switch compensation math.

Provides the mathematical backbone for every matching and space switching matching and
compensation operator.  Functions that need ``bpy`` import it lazily
so unit tests can exercise the pure-math helpers without Blender.

Key concepts
------------

*Visual matrix*
    ``obj.matrix_world`` after depsgraph evaluation — the transform the
    user actually *sees* in the viewport.

*Local matrix*
    ``obj.matrix_local`` — the transform relative to the parent.  This
    is what we can *write* (via ``obj.location`` / ``rotation_euler`` /
    ``scale``) and have Blender propagate to world space.

*Match*
    Set an object's local transform so its visual (world) transform
    equals a target world matrix, optionally filtering by channel or
    axis.

*Compensate*
    Record the visual matrix, change an external property (space
    switch), force a depsgraph update, then compute the new local
    transform that recovers the original visual result.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass  # Forward refs only.

__all__ = [
    "AxisMask",
    "MATCH_ALL",
    "MATCH_NONE",
    "ChannelFilter",
    "decompose_matrix",
    "compose_matrix",
    "visual_world_matrix",
    "parent_world_matrix",
    "compute_local_from_world",
    "is_channel_locked",
    "is_channel_driven",
    "MatchResult",
    "compute_match",
    "apply_match_result",
    "key_match_result",
    "record_visual_state",
    "compensate_after_switch",
    "mirror_name",
]


# ---------------------------------------------------------------------------
# Channel / axis mask helpers
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AxisMask:
    """Per-axis toggle for loc, rot, scale."""

    x: bool = True
    y: bool = True
    z: bool = True

    def any(self) -> bool:
        """Return True if at least one axis is enabled."""
        return self.x or self.y or self.z

    def as_tuple(self) -> tuple[bool, bool, bool]:
        """Return axes as a tuple (x, y, z)."""
        return (self.x, self.y, self.z)


MATCH_ALL = AxisMask(True, True, True)
MATCH_NONE = AxisMask(False, False, False)


@dataclass(frozen=True)
class ChannelFilter:
    """Which transform channels to include in a match operation."""

    location: AxisMask = field(default_factory=lambda: MATCH_ALL)
    rotation: AxisMask = field(default_factory=lambda: MATCH_ALL)
    scale: AxisMask = field(default_factory=lambda: MATCH_ALL)

    # Convenience constructors -------------------------------------------------

    @classmethod
    def all(cls) -> ChannelFilter:
        """Match all channels (location, rotation, scale)."""
        return cls()

    @classmethod
    def loc_only(cls) -> ChannelFilter:
        """Match only location channels, skip rotation and scale."""
        return cls(rotation=MATCH_NONE, scale=MATCH_NONE)

    @classmethod
    def rot_only(cls) -> ChannelFilter:
        """Match only rotation channels, skip location and scale."""
        return cls(location=MATCH_NONE, scale=MATCH_NONE)

    @classmethod
    def scale_only(cls) -> ChannelFilter:
        """Match only scale channels, skip location and rotation."""
        return cls(location=MATCH_NONE, rotation=MATCH_NONE)

    @classmethod
    def loc_rot(cls) -> ChannelFilter:
        """Match location and rotation, skip scale.

        Most common for IK/FK switching on limbs (arms, legs) where scale
        is rarely keyed. Avoids overwriting unintended scale values.
        """
        return cls(scale=MATCH_NONE)


# ---------------------------------------------------------------------------
# Pure math — Matrix → TRS decomposition (uses mathutils via bpy)
# ---------------------------------------------------------------------------

def decompose_matrix(matrix):  # type: ignore[no-untyped-def]
    """Decompose a 4×4 matrix into (location, rotation_euler, scale).

    Returns mathutils types: ``(Vector, Euler, Vector)``.
    """
    loc = matrix.to_translation()
    rot = matrix.to_euler()
    sca = matrix.to_scale()
    return loc, rot, sca


def compose_matrix(loc, rot, sca):  # type: ignore[no-untyped-def]
    """Build a 4×4 matrix from loc/euler/scale components.

    *rot* may be an ``Euler`` or a ``Quaternion``.
    """
    from mathutils import Matrix, Vector

    mat_loc = Matrix.Translation(loc)
    if hasattr(rot, "to_matrix"):
        mat_rot = rot.to_matrix().to_4x4()
    else:
        mat_rot = Matrix.Identity(4)
    mat_sca = Matrix.Diagonal(Vector((*sca, 1.0)))
    return mat_loc @ mat_rot @ mat_sca


# ---------------------------------------------------------------------------
# Object-level queries (need bpy lazily)
# ---------------------------------------------------------------------------

def is_pose_bone(obj) -> bool:  # type: ignore[no-untyped-def]
    """True when *obj* is a ``PoseBone`` rather than an ``Object``."""
    import bpy
    return isinstance(obj, bpy.types.PoseBone)


def _armature_of(pose_bone):  # type: ignore[no-untyped-def]
    return pose_bone.id_data


def visual_world_matrix(obj):  # type: ignore[no-untyped-def]
    """Return the depsgraph-evaluated world matrix of *obj*.

    Accepts an ``Object`` or a ``PoseBone``.  For a pose bone the result is
    ``armature.matrix_world @ pose_bone.matrix`` on the evaluated armature,
    i.e. the bone's final world placement after constraints and drivers.
    Falls back to un-evaluated matrices if no depsgraph is available.
    """
    import bpy
    if is_pose_bone(obj):
        arm = _armature_of(obj)
        try:
            dg = bpy.context.evaluated_depsgraph_get()
            arm_eval = arm.evaluated_get(dg)
            pb_eval = arm_eval.pose.bones.get(obj.name)
            if pb_eval is not None:
                return (arm_eval.matrix_world @ pb_eval.matrix).copy()
        except Exception:  # noqa: BLE001
            pass
        return (arm.matrix_world @ obj.matrix).copy()
    try:
        dg = bpy.context.evaluated_depsgraph_get()
        eval_obj = obj.evaluated_get(dg)
        return eval_obj.matrix_world.copy()
    except Exception:  # noqa: BLE001
        return obj.matrix_world.copy()


def _pose_bone_channel_world(pb):  # type: ignore[no-untyped-def]
    """World matrix of the space a pose bone's loc/rot/scale channels live in.

    ``pb.matrix_basis`` is expressed relative to the bone's rest matrix,
    re-parented under the parent's *posed* matrix.  Used only as a fallback
    when ``Bone.convert_local_to_pose`` is unavailable.
    """
    arm = _armature_of(pb)
    bone = pb.bone
    if pb.parent is not None:
        channel = (pb.parent.matrix
                   @ pb.parent.bone.matrix_local.inverted_safe()
                   @ bone.matrix_local)
    else:
        channel = bone.matrix_local.copy()
    return arm.matrix_world @ channel


def parent_world_matrix(obj):  # type: ignore[no-untyped-def]
    """Return the parent's evaluated world matrix, or Identity if none.

    For a ``PoseBone`` this is the world matrix of its channel space.
    """
    from mathutils import Matrix

    if is_pose_bone(obj):
        return _pose_bone_channel_world(obj)
    if obj.parent is None:
        return Matrix.Identity(4)
    return visual_world_matrix(obj.parent)


def world_to_local(target, desired_world, use_visual: bool = True):  # type: ignore[no-untyped-def]
    """Local (channel-space) matrix that places *target* at *desired_world*.

    Objects: ``(parent_world @ matrix_parent_inverse)^-1 @ desired_world``.
    Pose bones: ``Bone.convert_local_to_pose(..., invert=True)`` so Inherit
    Rotation / Inherit Scale are honoured; falls back to the channel-space
    matrix when that API is missing.
    """
    from mathutils import Matrix

    if is_pose_bone(target):
        arm = _armature_of(target)
        desired_pose = arm.matrix_world.inverted_safe() @ desired_world
        bone = target.bone
        conv = getattr(bone, "convert_local_to_pose", None)
        if conv is not None:
            try:
                if target.parent is not None:
                    return conv(
                        desired_pose, bone.matrix_local,
                        parent_matrix=target.parent.matrix,
                        parent_matrix_local=target.parent.bone.matrix_local,
                        invert=True,
                    )
                return conv(desired_pose, bone.matrix_local, invert=True)
            except (TypeError, RuntimeError):
                pass
        return _pose_bone_channel_world(target).inverted_safe() @ desired_world

    if use_visual:
        p_world = parent_world_matrix(target)
    elif target.parent:
        p_world = target.parent.matrix_world.copy()
    else:
        p_world = Matrix.Identity(4)
    effective_parent = p_world @ target.matrix_parent_inverse
    return effective_parent.inverted_safe() @ desired_world


def compute_local_from_world(desired_world, parent_world):  # type: ignore[no-untyped-def]
    """Compute the local matrix that, when combined with *parent_world*,
    yields *desired_world*.

    ``local = parent_world.inverted() @ desired_world``
    """
    return parent_world.inverted_safe() @ desired_world


# ---------------------------------------------------------------------------
# Channel lock / driver queries
# ---------------------------------------------------------------------------

_LOC_PATHS = ("location",)
_ROT_PATHS = ("rotation_euler", "rotation_quaternion", "rotation_axis_angle")
_SCA_PATHS = ("scale",)


def is_channel_locked(obj, channel: str, axis: int) -> bool:
    """Check whether *obj*'s transform channel is locked.

    *channel*: one of ``"location"``, ``"rotation_euler"``, ``"scale"``.
    *axis*: 0/1/2 for x/y/z.
    """
    if channel == "location":
        return obj.lock_location[axis]
    if channel in ("rotation_euler", "rotation_quaternion", "rotation_axis_angle"):
        if axis == 3:  # W component of quaternion / angle of axis-angle
            return bool(getattr(obj, "lock_rotation_w", False))
        return obj.lock_rotation[axis]
    if channel == "scale":
        return obj.lock_scale[axis]
    return False


def is_channel_driven(obj, data_path: str, index: int = -1) -> bool:
    """Return True if a driver controls *data_path* (optionally at *index*)."""
    adata = getattr(obj, "animation_data", None)
    if adata is None:
        return False
    for drv in adata.drivers:
        if drv.data_path == data_path:
            if index < 0 or drv.array_index == index:
                return True
    return False


# ---------------------------------------------------------------------------
# High-level match: compute target local TRS to match a source world matrix
# ---------------------------------------------------------------------------

@dataclass
class MatchResult:
    """Result of a match computation — what to write to the target."""

    location: tuple[float, float, float] | None = None
    rotation_euler: tuple[float, float, float] | None = None
    rotation_quaternion: tuple[float, float, float, float] | None = None
    rotation_axis_angle: tuple[float, float, float, float] | None = None
    rotation_mode: str = "XYZ"
    scale: tuple[float, float, float] | None = None
    channels_written: list[str] = field(default_factory=list)


_EULER_MODES = ("XYZ", "XZY", "YXZ", "YZX", "ZXY", "ZYX")


def rotation_data_path(mode: str) -> str:
    """Property name that holds rotation for a given ``rotation_mode``."""
    if mode == "QUATERNION":
        return "rotation_quaternion"
    if mode == "AXIS_ANGLE":
        return "rotation_axis_angle"
    return "rotation_euler"


def compute_match(
    source_world,
    target_obj,
    channel_filter: ChannelFilter | None = None,
    maintain_offset: bool = False,
    respect_locks: bool = True,
    respect_drivers: bool = True,
    use_visual: bool = True,
) -> MatchResult:
    """Compute the local TRS that makes *target_obj* visually match *source_world*.

    Parameters
    ----------
    source_world : Matrix
        The desired world-space matrix to match.
    target_obj : bpy.types.Object
        The object whose transform will be set.
    channel_filter : ChannelFilter, optional
        Which channels/axes to include.  Defaults to all.
    maintain_offset : bool
        If True, preserve the existing offset between source and target.
    respect_locks : bool
        Skip locked channels.
    respect_drivers : bool
        Skip driven channels.
    use_visual : bool
        Use evaluated world matrices for parent hierarchy.

    Returns
    -------
    MatchResult
        The computed channel values and list of what was written.
    """

    if channel_filter is None:
        channel_filter = ChannelFilter.all()

    result = MatchResult()

    desired_world = source_world
    if maintain_offset:
        # Compute current offset in world space and re-apply after match.
        if use_visual or is_pose_bone(target_obj):
            current_world = visual_world_matrix(target_obj)
        else:
            current_world = target_obj.matrix_world.copy()
        offset = source_world.inverted_safe() @ current_world
        desired_world = source_world @ offset

    # Works for Objects (parent + matrix_parent_inverse) and PoseBones
    # (rest matrix under the posed parent, honouring inherit flags).
    desired_local = world_to_local(target_obj, desired_world, use_visual)

    d_loc = desired_local.to_translation()
    d_sca = desired_local.to_scale()
    mode = getattr(target_obj, "rotation_mode", "XYZ")
    result.rotation_mode = mode

    # --- Location ---
    _apply_channel_match(
        result, d_loc, target_obj, channel_filter.location,
        "location", respect_locks, respect_drivers
    )

    # --- Rotation (dispatch on the target's rotation mode) ---
    if mode == "QUATERNION":
        _apply_rotation_match_4(
            result, tuple(desired_local.to_quaternion()), target_obj,
            channel_filter.rotation, "rotation_quaternion", respect_locks, respect_drivers,
        )
    elif mode == "AXIS_ANGLE":
        axis, angle = desired_local.to_quaternion().to_axis_angle()
        _apply_rotation_match_4(
            result, (angle, axis.x, axis.y, axis.z), target_obj,
            channel_filter.rotation, "rotation_axis_angle", respect_locks, respect_drivers,
        )
    else:
        order = mode if mode in _EULER_MODES else "XYZ"
        _apply_channel_match(
            result, desired_local.to_euler(order), target_obj, channel_filter.rotation,
            "rotation_euler", respect_locks, respect_drivers
        )

    # --- Scale ---
    _apply_channel_match(
        result, d_sca, target_obj, channel_filter.scale,
        "scale", respect_locks, respect_drivers
    )

    return result


def _apply_channel_match(
    result: MatchResult,
    desired_values,  # type: ignore[no-untyped-def]
    target_obj,  # type: ignore[no-untyped-def]
    axis_mask: AxisMask,
    channel_name: str,
    respect_locks: bool,
    respect_drivers: bool,
) -> None:
    """Helper: apply a single channel match (loc/rot/scale)."""
    if not axis_mask.any():
        return

    if channel_name == "location":
        cur_val = target_obj.location.copy()
    elif channel_name == "rotation_euler":
        cur_val = target_obj.rotation_euler.copy()
    else:  # scale
        cur_val = target_obj.scale.copy()

    new_val = list(cur_val)
    for i, (flag, axis_name) in enumerate(
        zip(axis_mask.as_tuple(), ("x", "y", "z"), strict=False)
    ):
        if not flag:
            continue
        if respect_locks and is_channel_locked(target_obj, channel_name, i):
            continue
        if respect_drivers and is_channel_driven(target_obj, channel_name, i):
            continue
        new_val[i] = desired_values[i]
        result.channels_written.append(f"{channel_name}.{axis_name}")

    # Store result
    if channel_name == "location":
        result.location = tuple(new_val)
    elif channel_name == "rotation_euler":
        result.rotation_euler = tuple(new_val)
    else:  # scale
        result.scale = tuple(new_val)


def _apply_rotation_match_4(
    result: MatchResult,
    desired_values,  # type: ignore[no-untyped-def]
    target_obj,  # type: ignore[no-untyped-def]
    axis_mask: AxisMask,
    channel_name: str,
    respect_locks: bool,
    respect_drivers: bool,
) -> None:
    """Quaternion / axis-angle match: written whole or not at all.

    A partial quaternion has no geometric meaning, so the per-axis filter
    is treated as "any rotation requested".  Any lock on a requested axis
    (or the W lock) or a driver on the property skips the write.
    """
    if not axis_mask.any():
        return
    if respect_locks:
        if is_channel_locked(target_obj, channel_name, 3):
            return
        if any(f and is_channel_locked(target_obj, channel_name, i)
               for i, f in enumerate(axis_mask.as_tuple())):
            return
    if respect_drivers and is_channel_driven(target_obj, channel_name):
        return
    values = tuple(float(v) for v in desired_values)
    if channel_name == "rotation_quaternion":
        result.rotation_quaternion = values
    else:
        result.rotation_axis_angle = values
    result.channels_written.append(channel_name)


def apply_match_result(target_obj, match: MatchResult) -> None:  # type: ignore[no-untyped-def]
    """Write a MatchResult to the target's transform channels (Object or PoseBone)."""
    from mathutils import Vector, Euler, Quaternion

    if match.location is not None:
        target_obj.location = Vector(match.location)
    if match.rotation_quaternion is not None:
        target_obj.rotation_quaternion = Quaternion(match.rotation_quaternion)
    elif match.rotation_axis_angle is not None:
        target_obj.rotation_axis_angle = match.rotation_axis_angle
    elif match.rotation_euler is not None:
        order = match.rotation_mode if match.rotation_mode in _EULER_MODES else "XYZ"
        target_obj.rotation_euler = Euler(match.rotation_euler, order)
    if match.scale is not None:
        target_obj.scale = Vector(match.scale)


def key_match_result(
    target_obj, match: MatchResult, frame: int
) -> int:  # type: ignore[no-untyped-def]
    """Insert keyframes for all channels in *match*.  Returns key count."""
    id_owner = target_obj.id_data if is_pose_bone(target_obj) else target_obj
    if id_owner.animation_data is None:
        id_owner.animation_data_create()

    keyed = 0
    if match.location is not None and any(
        c.startswith("location") for c in match.channels_written
    ):
        target_obj.keyframe_insert(data_path="location", frame=frame)
        keyed += 1
    if any(c.startswith("rotation") for c in match.channels_written):
        target_obj.keyframe_insert(data_path=rotation_data_path(match.rotation_mode), frame=frame)
        keyed += 1
    if match.scale is not None and any(
        c.startswith("scale") for c in match.channels_written
    ):
        target_obj.keyframe_insert(data_path="scale", frame=frame)
        keyed += 1
    return keyed


# ---------------------------------------------------------------------------
# Space-switch compensation helpers
# ---------------------------------------------------------------------------

def record_visual_state(obj) -> dict:  # type: ignore[no-untyped-def, type-arg]
    """Snapshot visual world matrix plus TRS for later restoration."""
    mat = visual_world_matrix(obj)
    loc, rot, sca = decompose_matrix(mat)
    return {
        "matrix_world": mat,
        "location": tuple(loc),
        "rotation_euler": tuple(rot),
        "scale": tuple(sca),
    }


def compensate_after_switch(
    obj,
    recorded_state: dict,  # type: ignore[type-arg]
    channel_filter: ChannelFilter | None = None,
    respect_locks: bool = True,
    respect_drivers: bool = True,
) -> MatchResult:
    """After a property change + depsgraph update, compute the local TRS
    that recovers the object's previously recorded visual transform.

    Call ``record_visual_state()`` *before* the property change, change
    the property, call ``context.view_layer.update()``, then call this.
    """
    return compute_match(
        source_world=recorded_state["matrix_world"],
        target_obj=obj,
        channel_filter=channel_filter,
        maintain_offset=False,
        respect_locks=respect_locks,
        respect_drivers=respect_drivers,
        use_visual=True,
    )


# ---------------------------------------------------------------------------
# Mirror naming (re-implements for matching and space switching independence)
# ---------------------------------------------------------------------------

import re as _re

_MIRROR_PATTERNS: tuple[tuple[_re.Pattern[str], str], ...] = (
    (_re.compile(r"\.L(\b|$)"), ".R"),
    (_re.compile(r"\.R(\b|$)"), ".L"),
    (_re.compile(r"_L(\b|$)"), "_R"),
    (_re.compile(r"_R(\b|$)"), "_L"),
    (_re.compile(r"(?<![a-zA-Z])Left(?![a-zA-Z])"), "Right"),
    (_re.compile(r"(?<![a-zA-Z])Right(?![a-zA-Z])"), "Left"),
    (_re.compile(r"(?<![a-zA-Z])left(?![a-zA-Z])"), "right"),
    (_re.compile(r"(?<![a-zA-Z])right(?![a-zA-Z])"), "left"),
)


def mirror_name(name: str) -> str:
    """Return the opposite-side name, or the original if no pattern matches."""
    for pat, repl in _MIRROR_PATTERNS:
        result = pat.sub(repl, name)
        if result != name:
            return result
    return name
