"""Bone path resolver and per-bone metadata accessor."""

from __future__ import annotations

import json

import bpy

from .. import constants
from .fcurve_compat import get_fcurves
from .logging import get_logger

__all__ = [
    "bone_path_prefixes",
    "fcurve_belongs_to_bone",
    "pose_bone_selected",
    "set_pose_bone_selected",
    "get_bone_data_path",
    "get_bone_transform_paths",
    "get_bone_fcurves",
    "get_bone_metadata",
    "set_bone_metadata",
    "resolve_bone_from_context",
]

_log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Data-path helpers
# ---------------------------------------------------------------------------

def get_bone_data_path(bone_name: str, property_name: str) -> str:
    """Build a Blender data path string for a pose bone property (e.g., location, rotation).

    Encapsulates bone name quoting rules so operators don't hardcode bracket syntax.
    Names are escaped: a bone called ``Arm"L`` or one containing a backslash
    would otherwise produce a path Blender cannot resolve (and that never
    matches the ``data_path`` Blender itself stores on the FCurve).
    """
    return f'pose.bones["{bpy.utils.escape_identifier(bone_name)}"].{property_name}'


def get_bone_transform_paths(bone_name: str) -> dict[str, str]:
    """Return data paths for all transform channels (location, rotation, scale) of a pose bone.

    Used by offset, retime, and constraint-binding operators to enumerate all animatable
    transform properties without hardcoding data path strings.
    """
    return {
        "location": get_bone_data_path(bone_name, "location"),
        "rotation_euler": get_bone_data_path(bone_name, "rotation_euler"),
        "rotation_quaternion": get_bone_data_path(
            bone_name, "rotation_quaternion"
        ),
        "scale": get_bone_data_path(bone_name, "scale"),
    }


def bone_path_prefixes(bone_name: str) -> tuple[str, str]:
    """Both data-path prefixes a pose bone's channels can carry.

    Transform channels look like ``pose.bones["x"].location``; custom
    properties keyed on the bone look like ``pose.bones["x"]["ik_fk"]``.
    A prefix ending in a dot silently drops the second kind.
    """
    base = f'pose.bones["{bpy.utils.escape_identifier(bone_name)}"]'
    return (base + ".", base + "[")


def fcurve_belongs_to_bone(fcurve: bpy.types.FCurve, bone_name: str) -> bool:
    """True for any FCurve driving *bone_name* - transforms or custom properties."""
    return fcurve.data_path.startswith(bone_path_prefixes(bone_name))


def get_bone_fcurves(
    action: bpy.types.Action, bone_name: str
) -> list[bpy.types.FCurve]:
    """Return all FCurves (animation channels) belonging to a specific pose bone in an action.

    Includes custom-property channels keyed on the bone, not only transforms.
    """
    return [fc for fc in get_fcurves(action) if fcurve_belongs_to_bone(fc, bone_name)]


# ---------------------------------------------------------------------------
# Per-bone metadata (stored in scene property group)
# ---------------------------------------------------------------------------

def get_bone_metadata(
    scene: bpy.types.Scene,
    object_name: str,
    bone_name: str,
) -> dict:
    """Retrieve stored metadata dict for a pose bone (tags, notes, constraint bindings, etc.).

    Returns empty dict if no metadata exists. Stored in scene-level CollectionProperty
    because Blender does not allow custom properties on PoseBones.
    """
    props = getattr(scene, constants.SCENE_PROP_ATTR, None)
    if props is None:
        return {}

    for item in props.bone_metadata:
        if item.object_name == object_name and item.bone_name == bone_name:
            try:
                return json.loads(item.metadata_json)
            except (json.JSONDecodeError, TypeError):
                return {}
    return {}


def set_bone_metadata(
    scene: bpy.types.Scene,
    object_name: str,
    bone_name: str,
    data: dict,
) -> bool:
    """Store or update metadata dict for a pose bone.

    Updates existing entry or creates new CollectionProperty item. Respects library
    write restrictions. Return False on validation error or library protection.
    """
    if not isinstance(data, dict):
        _log.warning("Bone metadata must be a dict, got %s", type(data).__name__)
        return False

    # Guard against linked scene / library write restrictions.
    if scene.library is not None and scene.override_library is None:
        _log.debug("Skipping bone metadata write for linked scene '%s'", scene.name)
        return False

    props = getattr(scene, constants.SCENE_PROP_ATTR, None)
    if props is None:
        return False

    # Serialise BEFORE touching the collection: a non-JSON value (Vector,
    # bpy struct, set) used to raise after add(), leaving a stub entry with
    # metadata_json == "{}" behind and breaking the "return False" contract.
    try:
        payload = json.dumps(data, ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        _log.warning("Bone metadata for %s/%s is not JSON-serialisable: %s",
                     object_name, bone_name, exc)
        return False

    for item in props.bone_metadata:
        if item.object_name == object_name and item.bone_name == bone_name:
            item.metadata_json = payload
            return True

    item = props.bone_metadata.add()
    item.object_name = object_name
    item.bone_name = bone_name
    item.metadata_json = payload
    return True


# ---------------------------------------------------------------------------
# Context helper
# ---------------------------------------------------------------------------

def resolve_bone_from_context(
    context: bpy.types.Context | None = None,
) -> tuple[bpy.types.Object, str] | None:
    """Return ``(armature_object, bone_name)`` if in pose mode, else *None*."""
    ctx = context or bpy.context
    obj = getattr(ctx, "active_object", None)
    if obj is None or obj.type != "ARMATURE" or obj.mode != "POSE":
        return None

    active_bone = getattr(ctx, "active_pose_bone", None)
    if active_bone is None:
        return None

    return (obj, active_bone.name)


def pose_bone_selected(pose_bone) -> bool:  # type: ignore[no-untyped-def]
    """Selection state of a pose bone across Blender versions.

    Blender 5.x removed ``Bone.select``; selection now lives on ``PoseBone``.
    4.x exposes it only on ``Bone``.  Read whichever this build provides.
    """
    sel = getattr(pose_bone, "select", None)
    if sel is not None:
        return bool(sel)
    return bool(pose_bone.bone.select)


def set_pose_bone_selected(pose_bone, value: bool) -> None:  # type: ignore[no-untyped-def]
    """Set pose-bone selection on whichever attribute this Blender build exposes."""
    if hasattr(pose_bone, "select"):
        pose_bone.select = value
    else:
        pose_bone.bone.select = value
