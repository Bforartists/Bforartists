"""BoneCraft core armature introspection utilities.

Stable public functions for querying armatures, bone collections,
and visibility states. All phase modules import from here — never
from each other's internals.
"""

import bpy
import json
from typing import Optional


# ── Armature queries ────────────────────────────────────────────

def _scene_target_armature(context: bpy.types.Context) -> Optional[bpy.types.Object]:
    scene = getattr(context, "scene", None)
    target_name = getattr(scene, "boneforge_cats_target_armature_name", "") if scene else ""
    obj = bpy.data.objects.get(target_name) if target_name else None
    if obj is not None and obj.type == 'ARMATURE' and scene.objects.get(obj.name) == obj:
        return obj

    obj = getattr(scene, "boneforge_cats_target_armature", None) if scene else None
    if obj is not None and obj.type == 'ARMATURE' and scene.objects.get(obj.name) == obj:
        return obj
    return None


def active_armature(context: bpy.types.Context) -> Optional[bpy.types.Object]:
    """Return the active armature object, or None."""
    target = _scene_target_armature(context)
    if target is not None:
        return target

    obj = context.active_object
    if obj is not None and obj.type == 'ARMATURE':
        return obj
    return None


def armature_data(context: bpy.types.Context) -> Optional[bpy.types.Armature]:
    """Return the Armature datablock of the active object, or None."""
    obj = active_armature(context)
    if obj is not None:
        return obj.data
    return None


# ── Bone collection helpers ─────────────────────────────────────

def bone_collections(arm_data: bpy.types.Armature) -> list:
    """Return all bone collections as a list.

    Works with Blender 4.0+ BoneCollection API.
    """
    return list(arm_data.collections)


def collection_by_name(arm_data: bpy.types.Armature,
                       name: str) -> Optional[object]:
    """Find a bone collection by name. Returns None if missing."""
    return arm_data.collections.get(name)


def collection_bone_names(arm_data: bpy.types.Armature,
                          collection_name: str) -> list[str]:
    """Return sorted bone names belonging to *collection_name*."""
    coll = collection_by_name(arm_data, collection_name)
    if coll is None:
        return []
    return sorted(bone.name for bone in coll.bones)


def set_collection_visibility(arm_data: bpy.types.Armature,
                              collection_name: str,
                              visible: bool) -> bool:
    """Set visibility of a single collection. Returns True on success."""
    coll = collection_by_name(arm_data, collection_name)
    if coll is None:
        return False
    coll.is_visible = visible
    return True


def snapshot_visibility(arm_data: bpy.types.Armature) -> dict[str, bool]:
    """Capture current visibility of every collection as {name: bool}."""
    return {c.name: c.is_visible for c in bone_collections(arm_data)}


def restore_visibility(arm_data: bpy.types.Armature,
                       state: dict[str, bool]) -> list[str]:
    """Restore visibility from a snapshot dict.

    Collections present in *state* but missing from the armature are
    silently skipped. Collections on the armature but absent from
    *state* are left untouched.

    Returns a list of collection names that were in *state* but not
    found on the armature (for error reporting).
    """
    missing = []
    for name, visible in state.items():
        if not set_collection_visibility(arm_data, name, visible):
            missing.append(name)
    return missing


# ── Custom property JSON helpers ────────────────────────────────

def read_custom_json(obj: bpy.types.Object,
                     key: str,
                     default=None):
    """Read a JSON-serialized custom property from *obj*.

    Returns *default* if the key is missing or the JSON is invalid.
    Never raises.
    """
    raw = obj.get(key)
    if raw is None:
        return default
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return default


def write_custom_json(obj: bpy.types.Object,
                      key: str,
                      value) -> None:
    """Write *value* as a JSON string into a custom property on *obj*."""
    obj[key] = json.dumps(value, ensure_ascii=False)


# ── Bone selection ──────────────────────────────────────────────

def select_bones_in_collection(context: bpy.types.Context,
                               arm_obj: bpy.types.Object,
                               collection_name: str,
                               extend: bool = False) -> int:
    """Select all bones belonging to *collection_name*.

    Works in both Pose and Edit mode by selecting the appropriate
    bone type. Returns the number of bones selected.

    If *extend* is False, the current selection is cleared first.
    """
    arm_data = arm_obj.data
    coll = collection_by_name(arm_data, collection_name)
    if coll is None:
        return 0

    target_names = {b.name for b in coll.bones}

    # Determine the bone source and selection accessor based on mode.
    # In Pose mode, selection lives on bone.select (via pose_bone.bone).
    # In Edit mode, selection lives directly on edit_bone.select.
    is_pose = context.mode == 'POSE'
    if is_pose:
        bone_items = arm_obj.pose.bones
    elif context.mode == 'EDIT_ARMATURE':
        bone_items = arm_data.edit_bones
    else:
        # Object mode — caller must switch to Pose/Edit first
        return 0

    def _selection_target(bone_item):
        """Return the data-block whose selection state controls the bone.

        In Pose mode the selection state lives on the underlying Bone
        (``pose_bone.bone``); in Edit mode it lives directly on the
        EditBone.
        """
        return bone_item.bone if is_pose else bone_item

    def _set_selected(bone_item, selected: bool) -> None:
        """Set selection state, defensive against API drift.

        Blender 5.x / Bforartists 5.2 removed ``Bone.select`` as a
        direct attribute; selection now goes through ``select_set``
        and ``select_get`` methods. Older Blender (4.0–4.4) still has
        the attribute. Try the modern method first, fall back to the
        attribute, and silently skip if neither path exists so a
        single broken bone can't crash the whole pick operation.
        """
        target = _selection_target(bone_item)
        if hasattr(target, "select_set"):
            try:
                target.select_set(selected)
                return
            except (RuntimeError, TypeError):
                pass
        try:
            target.select = selected
        except AttributeError:
            pass

    if not extend:
        for bone_item in bone_items:
            _set_selected(bone_item, False)

    count = 0
    for bone_item in bone_items:
        if bone_item.name in target_names:
            _set_selected(bone_item, True)
            count += 1

    return count


# ── Rigify detection ────────────────────────────────────────────

def is_rigify_human(arm_obj: bpy.types.Object) -> bool:
    """Heuristic: does this armature look like a Rigify human rig?

    Checks for characteristic bone names present in every default
    Rigify human meta-rig generation.
    """
    if arm_obj is None or arm_obj.type != 'ARMATURE':
        return False
    bone_names = {b.name for b in arm_obj.data.bones}
    rigify_markers = {
        'spine', 'spine.001', 'spine.002', 'spine.003',
        'upper_arm.L', 'upper_arm.R',
        'thigh.L', 'thigh.R',
        'head',
    }
    return rigify_markers.issubset(bone_names)


# ── Vertex weight helpers (v3.1.6 M-1) ──────────────────────────

def vertex_weights_by_group_index(vert) -> dict:
    """Return {vertex_group_index: weight} for groups assigned to *vert*.

    Replaces the legacy pattern of looping every ``obj.vertex_groups`` and
    calling ``vg.weight(vert.index)`` inside ``try/except RuntimeError``.
    The legacy pattern raised once per (vertex, unassigned-group) pair —
    Python exception machinery dominated weight-pipeline runtimes on
    production-scale meshes.
    """
    return {vge.group: vge.weight for vge in vert.groups}


def vertex_weights_by_group_name(obj, vert) -> dict:
    """Return {vertex_group_name: weight} for groups assigned to *vert*.

    Convenience over :func:`vertex_weights_by_group_index` for callers
    that need names rather than indices.
    """
    groups = obj.vertex_groups
    return {groups[vge.group].name: vge.weight for vge in vert.groups}

# ── Avatar-context resolution (v3.3.5) ──────────────────────────

def find_avatar_armature(context) -> "Optional[bpy.types.Object]":
    """Return the armature relevant to the current avatar context.

    Walks the active object's relationships to locate the armature it
    belongs to, so the BoneCraft sidebar's Task Board / Rig Notes /
    Overview hub stay visible while the user is working on any part
    of an avatar — not just when they've explicitly selected the
    armature itself.

    Returns the armature object when:
    * Active object IS an armature → that armature.
    * Active object is a mesh parented to an armature → the parent.
    * Active object is a mesh with an Armature modifier → the modifier's
      target object (covers VRChat / VRoid avatars where meshes are
      armature-modifier-bound but not necessarily parented).

    Returns ``None`` when there is no avatar context — non-avatar
    meshes, empties, lights, cameras, or no active object at all.
    The callers can then hide their panel via ``poll()`` and the
    sidebar's empty state shows only Setup → Auto-Rig Wizard.
    """
    obj = context.active_object
    if obj is None:
        return None
    if obj.type == "ARMATURE":
        return obj
    if obj.type != "MESH":
        return None
    parent = obj.parent
    if parent is not None and parent.type == "ARMATURE":
        return parent
    for mod in obj.modifiers:
        if mod.type == "ARMATURE":
            target = getattr(mod, "object", None)
            if target is not None and target.type == "ARMATURE":
                return target
    return None
