"""Selected animation target snapshot utilities."""

from __future__ import annotations

from dataclasses import dataclass, field

import bpy

from .cache import push_selection_entry, remember_active_target
from .fcurve_compat import get_fcurves
from .bone_utils import fcurve_belongs_to_bone, pose_bone_selected, set_pose_bone_selected

__all__ = [
    "TargetSnapshot",
    "get_active_target",
    "resolve_and_remember_active_target",
    "get_selected_target_snapshots",
    "get_selected_targets",
    "get_selected_pose_bone_names",
]


@dataclass
class TargetSnapshot:
    """Bundle of the active animation target: object, optional bone, action, and FCurves.

    Captures "what is the animator working on right now?" so operators know which
    channels to modify. Also tracks if object is linked (read-only) for protection.
    """
    # NOTE: field is named 'obj' (not 'object') to avoid shadowing Python's
    # built-in 'object' type, which can confuse type-checkers and linters.
    obj: bpy.types.Object
    bone_name: str | None = None
    action: bpy.types.Action | None = None
    fcurves: list[bpy.types.FCurve] = field(default_factory=list)
    is_linked: bool = False


def get_active_target(
    context: bpy.types.Context | None = None,
) -> TargetSnapshot | None:
    """Snapshot the active object (and optional active pose bone)."""
    ctx = context or bpy.context
    obj = getattr(ctx, "active_object", None) or getattr(ctx, "object", None)
    if obj is None:
        return None

    is_linked = obj.library is not None and obj.override_library is None

    bone_name: str | None = None
    if obj.type == "ARMATURE" and obj.mode == "POSE":
        active_bone = getattr(ctx, "active_pose_bone", None)
        if active_bone is not None:
            bone_name = active_bone.name

    action: bpy.types.Action | None = None
    fcurves: list[bpy.types.FCurve] = []
    anim_data = getattr(obj, "animation_data", None)
    if anim_data is not None:
        action = anim_data.action
        if action is not None:
            fcurves = get_fcurves(action, anim_data=anim_data)

    return TargetSnapshot(
        obj=obj,
        bone_name=bone_name,
        action=action,
        fcurves=fcurves,
        is_linked=is_linked,
    )


def resolve_and_remember_active_target(
    context: bpy.types.Context | None = None,
) -> TargetSnapshot | None:
    """Snapshot active target and cache it so "re-select last target" works.

    Pushes the selection into the session cache (object name, bone name) so
    animators can quickly jump back to their previous working target.
    """
    target = get_active_target(context)
    if target is not None:
        remember_active_target(target.obj.name, target.bone_name)
        push_selection_entry(target.obj.name, target.bone_name)
    return target


def _get_object_anim_data(
    obj: bpy.types.Object,
) -> tuple[bpy.types.Action | None, list[bpy.types.FCurve]]:
    """Helper to extract action and fcurves from an object."""
    anim_data = getattr(obj, "animation_data", None)
    if anim_data is None:
        return None, []
    action = anim_data.action
    fcurves = get_fcurves(action, anim_data=anim_data) if action is not None else []
    return action, fcurves


def _get_selected_bones_snapshots(
    obj: bpy.types.Object,
    is_linked: bool,
    action: bpy.types.Action | None,
    fcurves: list[bpy.types.FCurve],
) -> list[TargetSnapshot]:
    """Helper to build snapshots for selected pose bones."""
    results: list[TargetSnapshot] = []
    pose = getattr(obj, "pose", None)
    if pose is None:
        return results

    selected_bones = [b for b in pose.bones if pose_bone_selected(b)]
    if not selected_bones:
        return results

    for bone in selected_bones:
        # Transforms AND custom properties keyed on the bone (e.g. an IK/FK
        # switch), so bone-targeted operators keep them in step.
        bone_fcurves = [fc for fc in fcurves if fcurve_belongs_to_bone(fc, bone.name)]
        results.append(
            TargetSnapshot(
                obj=obj,
                bone_name=bone.name,
                action=action,
                fcurves=bone_fcurves,
                is_linked=is_linked,
            )
        )
    return results


def get_selected_target_snapshots(
    context: bpy.types.Context | None = None,
) -> list[TargetSnapshot]:
    """Return per-bone snapshots for selected bones, or object-level snapshots otherwise.

    Handles the complex case of multiple selected bones on an armature by creating
    one snapshot per bone with filtered FCurves, enabling batch bone operations.
    """
    ctx = context or bpy.context
    selected = getattr(ctx, "selected_objects", None) or []
    results: list[TargetSnapshot] = []

    for obj in selected:
        is_linked = obj.library is not None and obj.override_library is None
        action, fcurves = _get_object_anim_data(obj)

        # If this is an armature in pose mode with selected bones, create
        # per-bone snapshots and skip the object-level snapshot.
        if obj.type == "ARMATURE" and obj.mode == "POSE":
            bone_snapshots = _get_selected_bones_snapshots(
                obj, is_linked, action, fcurves
            )
            if bone_snapshots:
                results.extend(bone_snapshots)
                continue

        # Otherwise, create a single object-level snapshot.
        results.append(
            TargetSnapshot(
                obj=obj,
                bone_name=None,
                action=action,
                fcurves=fcurves,
                is_linked=is_linked,
            )
        )

    return results


get_selected_targets = get_selected_target_snapshots


def get_selected_pose_bone_names(
    context: bpy.types.Context | None = None,
) -> list[str]:
    """Return list of selected pose bone names from context."""
    ctx = context or bpy.context
    bones = getattr(ctx, "selected_pose_bones", None) or []
    return [b.name for b in bones]
