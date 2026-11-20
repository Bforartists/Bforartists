# --- TRANSFORM OFFSET CONTROLS ---
"""Unified target resolver for offset offset operators.

Produces a stream of :class:`OffsetTarget` records that abstract over
object and pose-bone selection so every offset operator can share a
single code path.

Each ``OffsetTarget`` carries everything needed by
``p4_space.delta_to_basis`` and the frame-write loop in
``operators/p4_offset_ops``:

* Owning object (always the armature in Pose Mode).
* Optional ``PoseBone`` handle.
* Rotation order / mode.
* Data-path prefix for fcurve lookup (``location`` / ``rotation_euler``
  / ``rotation_quaternion`` / ``scale`` or their ``pose.bones[...]``
  counterparts).
* Parent-to-world / parent-to-rest matrices used by the space
  converter.
* A per-target pivot point.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator

try:
    import bpy
    from mathutils import Matrix, Vector
except Exception:  # pragma: no cover
    bpy = None  # type: ignore[assignment]
    Matrix = Vector = None  # type: ignore[assignment]

from .logging import get_logger
from .fcurve_compat import get_fcurves

_log = get_logger(__name__)


# ---------------------------------------------------------------------------
# OffsetTarget record
# ---------------------------------------------------------------------------

@dataclass
class OffsetTarget:
    """Uniform descriptor for a single offset destination."""

    object: object  # bpy.types.Object
    pose_bone: object | None = None  # bpy.types.PoseBone
    display_name: str = ""
    data_path_prefix: str = ""
    rotation_order: str = "XYZ"
    rotation_mode: str = "XYZ"   # object.rotation_mode / pose_bone.rotation_mode
    is_pose_bone: bool = False
    pivot_world: object = None   # mathutils.Vector in practice
    # R5 audit fix: store depsgraph at resolve time so methods never
    # reach into bpy.context.
    depsgraph: object = field(default=None, repr=False)
    # Cached matrices. Populated lazily by the space converter.
    _world_to_basis: object = field(default=None, repr=False)
    _parent_to_basis: object = field(default=None, repr=False)

    # ------------------------------------------------------------------
    # Data-path builders
    # ------------------------------------------------------------------

    def data_path(self, component: str) -> str:
        """Return the fcurve ``data_path`` for a transform component.

        ``component`` is one of ``"location"``, ``"rotation_euler"``,
        ``"rotation_quaternion"``, ``"scale"``.
        """
        if self.is_pose_bone:
            return f'{self.data_path_prefix}.{component}'
        return component

    # ------------------------------------------------------------------
    # Matrix helpers
    # ------------------------------------------------------------------

    def world_to_basis_matrix(self, *, visual: bool = False):
        """Return the matrix that transforms world-space vectors into basis.

        For pose bones this is
        ``(armature_world @ bone.parent_matrix_local).inverted()``.
        For objects it is ``parent_world.inverted()`` (identity if no
        parent).

        When ``visual=True`` the depsgraph-evaluated world matrix is used
        as the basis reference so constraints and drivers contribute.
        """
        if Matrix is None:  # pragma: no cover
            return None

        if self.is_pose_bone:
            arm = self.object
            if visual:
                # R5 audit fix: use stored depsgraph instead of
                # bpy.context.evaluated_depsgraph_get().
                try:
                    dg = self.depsgraph
                    if dg is None:
                        dg = bpy.context.evaluated_depsgraph_get()
                    arm_eval = arm.evaluated_get(dg)
                    arm_world = arm_eval.matrix_world
                except Exception:
                    _log.debug(
                        "Failed to get evaluated armature matrix; using local",
                        exc_info=True,
                    )
                    arm_world = arm.matrix_world
            else:
                arm_world = arm.matrix_world
            bone = self.pose_bone.bone  # Bone (armature) not PoseBone.
            parent_mat = arm_world @ bone.matrix_local
            try:
                return parent_mat.inverted()
            except Exception:
                _log.debug("Failed to invert parent matrix for pose bone", exc_info=True)
                return None

        # Plain object.
        obj = self.object
        parent = getattr(obj, "parent", None)
        if parent is None:
            if visual:
                try:
                    dg = self.depsgraph
                    if dg is None:
                        dg = bpy.context.evaluated_depsgraph_get()
                    return obj.evaluated_get(dg).matrix_world.inverted()
                except Exception:
                    _log.debug("Failed to get evaluated object matrix; using local", exc_info=True)
            try:
                return obj.matrix_world.inverted()
            except Exception:
                _log.debug("Failed to invert object matrix; returning identity", exc_info=True)
                return Matrix.Identity(4)
        try:
            return parent.matrix_world.inverted()
        except Exception:
            _log.debug("Failed to invert parent matrix; returning identity", exc_info=True)
            return Matrix.Identity(4)

    def parent_to_basis_matrix(self):
        """Return the matrix converting parent-space vectors to basis."""
        if Matrix is None:  # pragma: no cover
            return None
        if self.is_pose_bone:
            bone = self.pose_bone.bone
            try:
                return bone.matrix_local.inverted()
            except Exception:
                _log.debug("Failed to invert bone local matrix", exc_info=True)
                return None
        # For objects parent-space == the parent's local space; since
        # basis for a plain object is its own local space, the conversion
        # is identity when no parent exists, otherwise identity again
        # because Blender's object.location already lives in parent-local
        # space.
        return Matrix.Identity(4)


# ---------------------------------------------------------------------------
# Resolver
# ---------------------------------------------------------------------------

def _compute_pivot_for_bone(pose_bone, arm_object, mode: str):
    """Return a world-space pivot vector for a pose bone."""
    if Vector is None or Matrix is None:  # pragma: no cover
        return None
    arm_world = arm_object.matrix_world
    bone = pose_bone.bone
    if mode == "BONE_HEAD":
        return arm_world @ bone.head_local.copy()
    if mode == "BONE_TAIL":
        return arm_world @ bone.tail_local.copy()
    if mode == "ACTIVE":
        # Same as INDIVIDUAL for the pose bone itself.
        # R9 audit fix: parenthesise to avoid operator precedence issue
        # (``@`` binds tighter than ``*``).
        return arm_world @ ((bone.head_local + bone.tail_local) * 0.5)
    # INDIVIDUAL / AVERAGE: midpoint of the bone head/tail.
    return arm_world @ ((bone.head_local + bone.tail_local) * 0.5)


def _compute_pivot_for_object(obj, mode: str):
    if Vector is None:  # pragma: no cover
        return None
    if mode in ("BONE_HEAD", "BONE_TAIL"):
        # Nonsensical on a plain object; fall back to origin.
        return obj.matrix_world.translation.copy()
    return obj.matrix_world.translation.copy()


def resolve_targets(
    context,
    *,
    pivot_mode: str = "INDIVIDUAL",
) -> list[OffsetTarget]:
    """Return the list of targets matching the current selection.

    Pose Mode on an armature: one target per selected pose bone on the
    active armature. Object Mode: one target per selected object. Any
    other context returns an empty list.
    """
    if bpy is None:  # pragma: no cover
        return []

    obj = getattr(context, "active_object", None)
    if obj is None:
        return []

    # R5 audit fix: capture depsgraph once from the operator context.
    try:
        _depsgraph = context.evaluated_depsgraph_get()
    except Exception:
        _log.debug("Failed to get evaluated depsgraph from context", exc_info=True)
        _depsgraph = None

    targets: list[OffsetTarget] = []

    mode = getattr(obj, "mode", None)
    if mode == "POSE" and obj.type == "ARMATURE":
        selected = getattr(context, "selected_pose_bones_from_active_object", None) or []
        for pb in selected:
            rot_mode = getattr(pb, "rotation_mode", "XYZ")
            valid_modes = ("XYZ", "XZY", "YXZ", "YZX", "ZXY", "ZYX")
            rot_order = rot_mode if rot_mode in valid_modes else "XYZ"
            try:
                escaped = pb.name.replace('"', r"\"")
            except Exception:
                _log.debug("Failed to escape pose bone name", exc_info=True)
                escaped = pb.name
            prefix = f'pose.bones["{escaped}"]'
            targets.append(
                OffsetTarget(
                    object=obj,
                    pose_bone=pb,
                    display_name=pb.name,
                    data_path_prefix=prefix,
                    rotation_order=rot_order,
                    rotation_mode=rot_mode,
                    is_pose_bone=True,
                    pivot_world=_compute_pivot_for_bone(pb, obj, pivot_mode),
                    depsgraph=_depsgraph,
                )
            )
        return targets

    if mode == "OBJECT":
        selected = getattr(context, "selected_objects", None) or []
        # Ensure the active object is considered first when present.
        ordered = [o for o in selected if o is not None]
        if obj in ordered:
            ordered.remove(obj)
            ordered.insert(0, obj)
        for ob in ordered:
            rot_mode = getattr(ob, "rotation_mode", "XYZ")
            valid_modes = ("XYZ", "XZY", "YXZ", "YZX", "ZXY", "ZYX")
            rot_order = rot_mode if rot_mode in valid_modes else "XYZ"
            targets.append(
                OffsetTarget(
                    object=ob,
                    pose_bone=None,
                    display_name=ob.name,
                    data_path_prefix="",
                    rotation_order=rot_order,
                    rotation_mode=rot_mode,
                    is_pose_bone=False,
                    pivot_world=_compute_pivot_for_object(ob, pivot_mode),
                    depsgraph=_depsgraph,
                )
            )
        return targets

    return []


# ---------------------------------------------------------------------------
# Channel filtering
# ---------------------------------------------------------------------------

def iter_target_fcurves(
    target: OffsetTarget,
    action,
    *,
    channel_mask: str,
    skip_locked: bool,
    skip_muted: bool,
    keyed_only: bool,
    selected_only: bool,
) -> Iterator[object]:
    """Yield the fcurves on ``action`` that belong to ``target``.

    The filter respects:

    * ``channel_mask`` — "T" / "R" / "S" / "TRS".
    * ``skip_locked`` — drop fcurves with ``fcurve.lock``.
    * ``skip_muted`` — drop fcurves with ``fcurve.mute``.
    * ``keyed_only`` — only fcurves that already have at least one key.
    * ``selected_only`` — only fcurves that have at least one selected
      keyframe point.
    """
    if action is None:
        return

    prefix = target.data_path_prefix
    want_loc = "T" in channel_mask or channel_mask == "TRS"
    want_rot = "R" in channel_mask or channel_mask == "TRS"
    want_scale = "S" in channel_mask or channel_mask == "TRS"

    for fc in get_fcurves(action):
        dp = fc.data_path or ""
        if target.is_pose_bone:
            if not dp.startswith(prefix + "."):
                continue
            leaf = dp[len(prefix) + 1:]
        else:
            if "." in dp:
                # Plain-object channels have no dots in their data_path.
                continue
            leaf = dp

        if leaf == "location":
            if not want_loc:
                continue
        elif (
            leaf == "rotation_euler"
            or leaf == "rotation_quaternion"
            or leaf == "rotation_axis_angle"
        ):
            if not want_rot:
                continue
        elif leaf == "scale":
            if not want_scale:
                continue
        else:
            continue

        if skip_locked and getattr(fc, "lock", False):
            continue
        if skip_muted and getattr(fc, "mute", False):
            continue

        kps = getattr(fc, "keyframe_points", None)
        if keyed_only and (kps is None or len(kps) == 0):
            continue
        if selected_only:
            if kps is None or not any(kp.select_control_point for kp in kps):
                continue

        yield fc


__all__ = [
    "OffsetTarget",
    "resolve_targets",
    "iter_target_fcurves",
]
