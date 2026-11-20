# --- MIRROR TRANSFORM MATH ---
"""Mirrored transform computations for character animation.

Provides mathematical operations for mirroring bone transforms across
a specified axis (typically X for bilateral symmetry), supporting both
local direct transforms and constrained rig evaluation.

Key concepts
------------

*Mirror axis*
    The axis across which to mirror: X, Y, or Z. Typically X for
    left/right symmetric character rigs.

*Mirror transform*
    Negate the component on the mirror axis for location; negate
    perpendicular rotation components while keeping the axis rotation.

*Visual mirror*
    For constrained rigs: use depsgraph-evaluated matrices and
    compute_match to find local values that yield the mirrored result.

*Swap*
    Exchange mirrored transforms between two bones (e.g., arm.L <-> arm.R).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .logging import get_logger
from . import p8_match_math as mm

if TYPE_CHECKING:
    pass

__all__ = [
    "MirrorAxis",
    "MirrorResult",
    "mirror_location",
    "mirror_rotation_euler",
    "mirror_scale",
    "mirror_transform",
    "compute_mirror_matrix",
    "mirror_bone_pose",
    "swap_bone_poses",
    "mirror_bone_visual",
    "key_mirror_result",
]

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Mirror Axis Definition
# ---------------------------------------------------------------------------

class MirrorAxis:
    """Mirror axis constants."""
    X = "X"
    Y = "Y"
    Z = "Z"


# ---------------------------------------------------------------------------
# Basic Mirror Operations
# ---------------------------------------------------------------------------

def mirror_location(
    loc: tuple[float, float, float],
    axis: str = "X",
) -> tuple[float, float, float]:
    """Mirror a location across the given axis.

    Negates the component on the mirror axis.

    Parameters
    ----------
    loc : tuple[float, float, float]
        The location (x, y, z).
    axis : str
        The mirror axis: "X", "Y", or "Z".

    Returns
    -------
    tuple[float, float, float]
        The mirrored location.
    """
    x, y, z = loc
    if axis == "X":
        return (-x, y, z)
    elif axis == "Y":
        return (x, -y, z)
    elif axis == "Z":
        return (x, y, -z)
    else:
        logger.warning(f"Unknown mirror axis: {axis}, returning unchanged")
        return loc


def mirror_rotation_euler(
    rot: tuple[float, float, float],
    axis: str = "X",
) -> tuple[float, float, float]:
    """Mirror Euler rotation across the given axis.

    For X axis: keep X rotation, negate Y and Z.
    For Y axis: negate X and Z, keep Y.
    For Z axis: negate X and Y, keep Z.

    Parameters
    ----------
    rot : tuple[float, float, float]
        The Euler angles (x, y, z) in radians.
    axis : str
        The mirror axis: "X", "Y", or "Z".

    Returns
    -------
    tuple[float, float, float]
        The mirrored rotation.
    """
    x, y, z = rot
    if axis == "X":
        return (x, -y, -z)
    elif axis == "Y":
        return (-x, y, -z)
    elif axis == "Z":
        return (-x, -y, z)
    else:
        logger.warning(f"Unknown mirror axis: {axis}, returning unchanged")
        return rot


def mirror_rotation_quaternion(
    quat: tuple[float, float, float, float],
    axis: str = "X",
) -> tuple[float, float, float, float]:
    """Mirror a (w, x, y, z) quaternion across the given axis.

    Reflecting a rotation across the plane normal to *axis* keeps the
    rotation's component along that axis and negates the other two - the
    exact counterpart of :func:`mirror_rotation_euler`'s convention.
    """
    w, x, y, z = quat
    if axis == "X":
        return (w, x, -y, -z)
    elif axis == "Y":
        return (w, -x, y, -z)
    elif axis == "Z":
        return (w, -x, -y, z)
    logger.warning(f"Unknown mirror axis: {axis}, returning unchanged")
    return quat


def mirror_rotation_axis_angle(
    aa: tuple[float, float, float, float],
    axis: str = "X",
) -> tuple[float, float, float, float]:
    """Mirror an (angle, x, y, z) axis-angle rotation across the given axis."""
    angle, x, y, z = aa
    if axis == "X":
        return (angle, x, -y, -z)
    elif axis == "Y":
        return (angle, -x, y, -z)
    elif axis == "Z":
        return (angle, -x, -y, z)
    logger.warning(f"Unknown mirror axis: {axis}, returning unchanged")
    return aa


# ---------------------------------------------------------------------------
# Rotation-mode aware bone rotation I/O
# ---------------------------------------------------------------------------

_EULER_MODES = ("XYZ", "XZY", "YXZ", "YZX", "ZXY", "ZYX")


def rotation_data_path(bone) -> str:  # type: ignore[no-untyped-def]
    """Property that carries *bone*'s rotation for its ``rotation_mode``."""
    return mm.rotation_data_path(getattr(bone, "rotation_mode", "XYZ"))


def _rotation_values(bone):  # type: ignore[no-untyped-def]
    """Return ``(mode, values)`` for *bone* in its own rotation mode."""
    mode = getattr(bone, "rotation_mode", "XYZ")
    return mode, tuple(getattr(bone, mm.rotation_data_path(mode)))


def _mirror_rotation_values(values, mode: str, axis: str):  # type: ignore[no-untyped-def]
    if mode == "QUATERNION":
        return mirror_rotation_quaternion(values, axis)
    if mode == "AXIS_ANGLE":
        return mirror_rotation_axis_angle(values, axis)
    return mirror_rotation_euler(values, axis)


def _convert_rotation(values, from_mode: str, to_mode: str):  # type: ignore[no-untyped-def]
    """Re-express a rotation from one ``rotation_mode`` in another."""
    if from_mode == to_mode:
        return tuple(values)
    from mathutils import Euler, Quaternion

    if from_mode == "QUATERNION":
        q = Quaternion(values)
    elif from_mode == "AXIS_ANGLE":
        q = Quaternion(values[1:], values[0])
    else:
        q = Euler(values, from_mode if from_mode in _EULER_MODES else "XYZ").to_quaternion()

    if to_mode == "QUATERNION":
        return tuple(q)
    if to_mode == "AXIS_ANGLE":
        ax, ang = q.to_axis_angle()
        return (ang, ax.x, ax.y, ax.z)
    return tuple(q.to_euler(to_mode if to_mode in _EULER_MODES else "XYZ"))


def _write_rotation_values(
    dst_bone, mode: str, values, axis_mask, respect_locks: bool, respect_drivers: bool,
) -> list[str]:  # type: ignore[no-untyped-def]
    """Write rotation *values* (already in *mode*) to *dst_bone*.

    Euler is written per component under the axis mask.  Quaternion and
    axis-angle are written whole: a partial quaternion has no meaning, so
    the mask is read as "any rotation requested" and any lock on a requested
    axis (or the W lock) skips the write entirely.
    """
    written: list[str] = []
    path = mm.rotation_data_path(mode)
    if mode in ("QUATERNION", "AXIS_ANGLE"):
        if not axis_mask.any():
            return written
        if respect_locks and (
            getattr(dst_bone, "lock_rotation_w", False)
            or any(f and dst_bone.lock_rotation[i] for i, f in enumerate(axis_mask.as_tuple()))
        ):
            return written
        if respect_drivers and mm.is_channel_driven(dst_bone, path):
            return written
        setattr(dst_bone, path, values)
        written.append(path)
        return written
    for i, axis_name in enumerate(("x", "y", "z")):
        if not axis_mask.as_tuple()[i]:
            continue
        if respect_locks and dst_bone.lock_rotation[i]:
            continue
        if respect_drivers and mm.is_channel_driven(dst_bone, "rotation_euler", i):
            continue
        dst_bone.rotation_euler[i] = values[i]
        written.append(f"rotation_euler.{axis_name}")
    return written


def mirror_scale(
    sca: tuple[float, float, float],
    axis: str = "X",
) -> tuple[float, float, float]:
    """Mirror scale across the given axis.

    Scale is typically copied as-is (no negation needed for mirroring).

    Parameters
    ----------
    sca : tuple[float, float, float]
        The scale (x, y, z).
    axis : str
        The mirror axis: "X", "Y", or "Z".

    Returns
    -------
    tuple[float, float, float]
        The mirrored scale (unchanged).
    """
    return sca


# ---------------------------------------------------------------------------
# Composite Mirror Transform
# ---------------------------------------------------------------------------

def mirror_transform(
    loc: tuple[float, float, float],
    rot: tuple[float, float, float],
    sca: tuple[float, float, float],
    axis: str = "X",
    channel_filter: mm.ChannelFilter | None = None,
) -> tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]:
    """Apply mirror transformation to location, rotation, and scale.

    Respects channel_filter to skip filtered-out channels.

    Parameters
    ----------
    loc : tuple[float, float, float]
        The location.
    rot : tuple[float, float, float]
        The rotation (Euler, in radians).
    sca : tuple[float, float, float]
        The scale.
    axis : str
        The mirror axis: "X", "Y", or "Z".
    channel_filter : ChannelFilter, optional
        Which channels to apply mirroring to.

    Returns
    -------
    tuple of three tuples
        (mirrored_loc, mirrored_rot, mirrored_sca)
    """
    if channel_filter is None:
        channel_filter = mm.ChannelFilter.all()

    mirrored_loc = loc
    mirrored_rot = rot
    mirrored_sca = sca

    if channel_filter.location.any():
        mirrored_loc = mirror_location(loc, axis)

    if channel_filter.rotation.any():
        mirrored_rot = mirror_rotation_euler(rot, axis)

    if channel_filter.scale.any():
        mirrored_sca = mirror_scale(sca, axis)

    return mirrored_loc, mirrored_rot, mirrored_sca


# ---------------------------------------------------------------------------
# Matrix Mirroring
# ---------------------------------------------------------------------------

def compute_mirror_matrix(matrix, axis: str = "X"):
    """Mirror a 4x4 matrix across the given axis.

    Uses a reflection matrix to negate components on the mirror axis.

    Parameters
    ----------
    matrix : Matrix
        A 4x4 transformation matrix.
    axis : str
        The mirror axis: "X", "Y", or "Z".

    Returns
    -------
    Matrix
        The mirrored matrix.
    """
    from mathutils import Matrix

    # Create a reflection/scale matrix that negates the mirror axis.
    if axis == "X":
        mirror_scale = Matrix.Scale(-1, 4, (1, 0, 0))
    elif axis == "Y":
        mirror_scale = Matrix.Scale(-1, 4, (0, 1, 0))
    elif axis == "Z":
        mirror_scale = Matrix.Scale(-1, 4, (0, 0, 1))
    else:
        logger.warning(f"Unknown mirror axis: {axis}, returning unchanged")
        return matrix.copy()

    # Apply: mirror the matrix by negating the axis, then negate again
    # to keep the result in the same space.
    # result = mirror_scale @ matrix @ mirror_scale
    return mirror_scale @ matrix @ mirror_scale


# ---------------------------------------------------------------------------
# Bone-level Mirror Operations
# ---------------------------------------------------------------------------

@dataclass
class MirrorResult:
    """Result of a mirror operation on a bone."""
    bone_name: str
    opposite_name: str
    channels_written: list[str] = field(default_factory=list)
    success: bool = True
    error: str = ""


def mirror_bone_pose(
    src_bone,
    dst_bone,
    axis: str = "X",
    channel_filter: mm.ChannelFilter | None = None,
    respect_locks: bool = True,
    respect_drivers: bool = True,
) -> list[str]:
    """Mirror transforms from src_bone to dst_bone (local space).

    Reads src_bone's local transform, computes mirrored values,
    and writes to dst_bone respecting locks and drivers.

    Parameters
    ----------
    src_bone : bpy.types.PoseBone
        Source bone to read from.
    dst_bone : bpy.types.PoseBone
        Destination bone to write to.
    axis : str
        The mirror axis: "X", "Y", or "Z".
    channel_filter : ChannelFilter, optional
        Which channels to mirror.
    respect_locks : bool
        Skip locked channels.
    respect_drivers : bool
        Skip driven channels.

    Returns
    -------
    list[str]
        List of channels written (e.g., ["location", "rotation_euler"]).
    """
    if channel_filter is None:
        channel_filter = mm.ChannelFilter.all()

    channels_written = []

    try:
        # Extract source transforms.
        src_loc = tuple(src_bone.location)
        src_rot = tuple(src_bone.rotation_euler)
        src_sca = tuple(src_bone.scale)

        # Compute mirrored transforms.
        mir_loc, mir_rot, mir_sca = mirror_transform(
            src_loc, src_rot, src_sca,
            axis=axis,
            channel_filter=channel_filter,
        )

        # --- Location ---
        if channel_filter.location.any():
            for i, axis_name in enumerate(("x", "y", "z")):
                if not channel_filter.location.as_tuple()[i]:
                    continue
                if respect_locks and dst_bone.lock_location[i]:
                    continue
                if respect_drivers and mm.is_channel_driven(dst_bone, "location", i):
                    continue
                dst_bone.location[i] = mir_loc[i]
                channels_written.append(f"location.{axis_name}")

        # --- Rotation (in the bones' own rotation modes) ---
        if channel_filter.rotation.any():
            src_mode, src_vals = _rotation_values(src_bone)
            mir_vals = _mirror_rotation_values(src_vals, src_mode, axis)
            dst_mode = getattr(dst_bone, "rotation_mode", "XYZ")
            mir_vals = _convert_rotation(mir_vals, src_mode, dst_mode)
            channels_written += _write_rotation_values(
                dst_bone, dst_mode, mir_vals, channel_filter.rotation,
                respect_locks, respect_drivers,
            )

        # --- Scale ---
        if channel_filter.scale.any():
            for i, axis_name in enumerate(("x", "y", "z")):
                if not channel_filter.scale.as_tuple()[i]:
                    continue
                if respect_locks and dst_bone.lock_scale[i]:
                    continue
                if respect_drivers and mm.is_channel_driven(dst_bone, "scale", i):
                    continue
                dst_bone.scale[i] = mir_sca[i]
                channels_written.append(f"scale.{axis_name}")

    except Exception as e:
        logger.error(f"Error mirroring {src_bone.name} to {dst_bone.name}: {e}")

    return channels_written


def swap_bone_poses(bone_a, bone_b) -> tuple[list[str], list[str]]:
    """Swap mirrored transforms between two bones (for L/R swap).

    Records both bones' transforms, mirrors and exchanges them.

    Parameters
    ----------
    bone_a : bpy.types.PoseBone
        First bone.
    bone_b : bpy.types.PoseBone
        Second bone.

    Returns
    -------
    tuple[list[str], list[str]]
        (channels_written_to_a, channels_written_to_b)
    """
    try:
        # Record current transforms.
        a_loc = tuple(bone_a.location)
        a_rot = tuple(bone_a.rotation_euler)
        a_sca = tuple(bone_a.scale)
        a_mode, a_rot_vals = _rotation_values(bone_a)

        b_loc = tuple(bone_b.location)
        b_rot = tuple(bone_b.rotation_euler)
        b_sca = tuple(bone_b.scale)
        b_mode, b_rot_vals = _rotation_values(bone_b)
        full_rot = mm.ChannelFilter.all().rotation

        # Mirror and cross-assign.
        mir_a_loc, mir_a_rot, mir_a_sca = mirror_transform(a_loc, a_rot, a_sca)
        mir_b_loc, mir_b_rot, mir_b_sca = mirror_transform(b_loc, b_rot, b_sca)

        channels_a = []
        channels_b = []

        # Assign to opposite bones.
        try:
            bone_b.location = mir_a_loc
            channels_a.append("location")
        except Exception as e:
            logger.debug(f"Could not write location to {bone_b.name}: {e}")

        try:
            vals = _convert_rotation(_mirror_rotation_values(a_rot_vals, a_mode, "X"), a_mode, b_mode)
            channels_a += _write_rotation_values(bone_b, b_mode, vals, full_rot, False, False)
        except Exception as e:
            logger.debug(f"Could not write rotation to {bone_b.name}: {e}")

        try:
            bone_b.scale = mir_a_sca
            channels_a.append("scale")
        except Exception as e:
            logger.debug(f"Could not write scale to {bone_b.name}: {e}")

        try:
            bone_a.location = mir_b_loc
            channels_b.append("location")
        except Exception as e:
            logger.debug(f"Could not write location to {bone_a.name}: {e}")

        try:
            vals = _convert_rotation(_mirror_rotation_values(b_rot_vals, b_mode, "X"), b_mode, a_mode)
            channels_b += _write_rotation_values(bone_a, a_mode, vals, full_rot, False, False)
        except Exception as e:
            logger.debug(f"Could not write rotation to {bone_a.name}: {e}")

        try:
            bone_a.scale = mir_b_sca
            channels_b.append("scale")
        except Exception as e:
            logger.debug(f"Could not write scale to {bone_a.name}: {e}")

        return channels_a, channels_b

    except Exception as e:
        logger.error(f"Error swapping poses between {bone_a.name} and {bone_b.name}: {e}")
        return [], []


def mirror_bone_visual(
    src_bone,
    dst_bone,
    armature_obj,
    axis: str = "X",
    channel_filter: mm.ChannelFilter | None = None,
    source_world=None,
) -> list[str]:
    """Mirror bone transforms using evaluated (visual) matrices.

    For constrained rigs: uses depsgraph-evaluated matrices and
    compute_match to find local values that yield the mirrored result.

    Parameters
    ----------
    src_bone : bpy.types.PoseBone
        Source bone to read from (will be evaluated).
    dst_bone : bpy.types.PoseBone
        Destination bone to write to.
    armature_obj : bpy.types.Object
        The armature object (needed for depsgraph).
    axis : str
        The mirror axis: "X", "Y", or "Z".
    channel_filter : ChannelFilter, optional
        Which channels to mirror.

    Returns
    -------
    list[str]
        List of channels written.
    """
    if channel_filter is None:
        channel_filter = mm.ChannelFilter.all()

    channels_written = []

    try:
        # Get source bone's evaluated world matrix.
        src_world = source_world if source_world is not None else mm.visual_world_matrix(src_bone)

        # Mirror the world matrix.
        mir_world = compute_mirror_matrix(src_world, axis=axis)

        # Compute what local transform makes dst_bone match the mirrored world.
        match_result = mm.compute_match(
            source_world=mir_world,
            target_obj=dst_bone,
            channel_filter=channel_filter,
            maintain_offset=False,
            respect_locks=True,
            respect_drivers=True,
            use_visual=True,
        )

        # Apply the match result.
        mm.apply_match_result(dst_bone, match_result)
        channels_written = match_result.channels_written

    except Exception as e:
        logger.error(
            f"Error visually mirroring {src_bone.name} to {dst_bone.name}: {e}"
        )

    return channels_written


def copy_bone_pose(
    src_bone,
    dst_bone,
    channel_filter: mm.ChannelFilter | None = None,
    respect_locks: bool = True,
    respect_drivers: bool = True,
) -> list[str]:
    """Copy transforms from src_bone to dst_bone **without** mirroring.

    This is what "match" means: make *dst_bone* take *src_bone*'s local
    pose.  Rotation is converted between rotation modes when they differ.

    Returns
    -------
    list[str]
        Channels written (e.g. ["location.x", "rotation_quaternion"]).
    """
    if channel_filter is None:
        channel_filter = mm.ChannelFilter.all()

    channels_written: list[str] = []
    try:
        if channel_filter.location.any():
            for i, axis_name in enumerate(("x", "y", "z")):
                if not channel_filter.location.as_tuple()[i]:
                    continue
                if respect_locks and dst_bone.lock_location[i]:
                    continue
                if respect_drivers and mm.is_channel_driven(dst_bone, "location", i):
                    continue
                dst_bone.location[i] = src_bone.location[i]
                channels_written.append(f"location.{axis_name}")

        if channel_filter.rotation.any():
            src_mode, src_vals = _rotation_values(src_bone)
            dst_mode = getattr(dst_bone, "rotation_mode", "XYZ")
            vals = _convert_rotation(src_vals, src_mode, dst_mode)
            channels_written += _write_rotation_values(
                dst_bone, dst_mode, vals, channel_filter.rotation,
                respect_locks, respect_drivers,
            )

        if channel_filter.scale.any():
            for i, axis_name in enumerate(("x", "y", "z")):
                if not channel_filter.scale.as_tuple()[i]:
                    continue
                if respect_locks and dst_bone.lock_scale[i]:
                    continue
                if respect_drivers and mm.is_channel_driven(dst_bone, "scale", i):
                    continue
                dst_bone.scale[i] = src_bone.scale[i]
                channels_written.append(f"scale.{axis_name}")
    except Exception as e:
        logger.error(f"Error copying pose {src_bone.name} -> {dst_bone.name}: {e}")

    return channels_written


# ---------------------------------------------------------------------------
# Keyframing
# ---------------------------------------------------------------------------

def key_mirror_result(bone, channels_written: list[str], frame: int) -> int:
    """Insert keyframes for channels that were written during mirror.

    Parameters
    ----------
    bone : bpy.types.PoseBone
        The bone to keyframe.
    channels_written : list[str]
        List of channel names (e.g., ["location", "rotation_euler"]).
    frame : int
        The frame to insert keys at.

    Returns
    -------
    int
        Number of keyframes inserted.
    """
    try:

        keyed = 0

        # Check for location channels.
        if any(c.startswith("location") for c in channels_written):
            bone.keyframe_insert(data_path="location", frame=frame)
            keyed += 1

        # Check for rotation channels.
        if any(c.startswith("rotation") for c in channels_written):
            bone.keyframe_insert(data_path=rotation_data_path(bone), frame=frame)
            keyed += 1

        # Check for scale channels.
        if any(c.startswith("scale") for c in channels_written):
            bone.keyframe_insert(data_path="scale", frame=frame)
            keyed += 1

        return keyed

    except Exception as e:
        logger.error(f"Error inserting keyframes for {bone.name}: {e}")
        return 0
