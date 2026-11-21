"""Constraint inspection helpers."""

from __future__ import annotations

import bpy

__all__ = [
    "get_bone_constraints",
    "get_object_constraints",
    "get_active_constraints",
    "has_ik_constraint",
    "get_constraint_targets",
]


def get_bone_constraints(
    obj: bpy.types.Object | None,
    bone_name: str,
) -> list[bpy.types.Constraint]:
    """Safely retrieve all constraints applied to a pose bone.

    Returns empty list if object is not an armature or bone does not exist,
    preventing None reference errors when inspecting constraint types and targets.
    """
    if obj is None or obj.type != "ARMATURE":
        return []
    pose = getattr(obj, "pose", None)
    if pose is None:
        return []
    bone = pose.bones.get(bone_name)
    if bone is None:
        return []
    return list(bone.constraints)


def get_object_constraints(
    obj: bpy.types.Object | None,
) -> list[bpy.types.Constraint]:
    """Safely retrieve all constraints applied to an object.

    Returns empty list if object is None, preventing None reference errors.
    """
    if obj is None:
        return []
    return list(obj.constraints)


def get_active_constraints(
    obj: bpy.types.Object | None,
    bone_name: str | None = None,
) -> list[bpy.types.Constraint]:
    """Return enabled constraints with non-zero influence."""
    if bone_name is not None:
        constraints = get_bone_constraints(obj, bone_name)
    else:
        constraints = get_object_constraints(obj)
    return [c for c in constraints if not c.mute and c.influence > 0.0]


def has_ik_constraint(
    obj: bpy.types.Object | None,
    bone_name: str,
) -> bool:
    """Check if a pose bone has an active (unmuted) IK constraint.

    Used by matching and space switching (IK/FK switching) to detect IK chains and validate rig structure.
    """
    constraints = get_bone_constraints(obj, bone_name)
    return any(c.type == "IK" and not c.mute for c in constraints)


def get_constraint_targets(
    constraint: bpy.types.Constraint,
) -> list[bpy.types.Object]:
    """Return all target objects referenced by a constraint (e.g., IK pole target, Copy Transforms).

    Handles both single-target (target) and multi-target (targets) constraint types.
    Used by proxy (proxy baking) to identify control objects and constraint dependencies.
    """
    targets: list[bpy.types.Object] = []
    target = getattr(constraint, "target", None)
    if target is not None:
        targets.append(target)
    target_list = getattr(constraint, "targets", None)
    if target_list is not None:
        for entry in target_list:
            tgt = getattr(entry, "target", None)
            if tgt is not None:
                targets.append(tgt)
    return targets