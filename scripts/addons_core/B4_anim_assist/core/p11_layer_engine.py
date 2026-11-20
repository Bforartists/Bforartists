# --- ANIMATION LAYER ENGINE ---
"""Animation layer evaluation engine.

Evaluates the full layer stack for a given bone at a given frame,
accumulating transforms from the base layer upward through each active
layer, applying blend modes and weights.  Also provides utilities for
Action-based layer data I/O and layer stack manipulation.

Design notes
------------
Each animation layer is backed by a separate Blender Action.  The base
layer uses the object's current Action (``obj.animation_data.action``).
Override layers store their keyed values in secondary Actions that are
never directly assigned to the object — they are read by this engine
during evaluation.

The evaluation pipeline:
    1. Read base-layer transform from the object's active Action.
    2. For each layer above the base (bottom-to-top):
       a. Skip if muted or weight == 0.
       b. If any layer is solo, skip non-solo layers.
       c. Read the layer's Action values at the current frame.
       d. Apply blend_transforms with the layer's mode and weight.
    3. Write the final accumulated transform back to the bone.

Caching strategy:
    A ``_generation`` counter is stored on the scene PropertyGroup.
    When the layer stack changes (add, remove, reorder, weight change),
    the generation is bumped to invalidate cached evaluations.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .logging import get_logger
from . import p11_blend_math as bm
from .fcurve_compat import get_fcurves, find_fcurve, new_fcurve


def _escape_bone_name(name: str) -> str:
    """``bpy.utils.escape_identifier`` via a runtime-only import.

    This module does not bind ``bpy`` at module level, so a direct reference
    would NameError at call time.
    """
    import bpy
    return bpy.utils.escape_identifier(name)

if TYPE_CHECKING:
    from bpy.types import Action, Object, PoseBone, PropertyGroup

__all__ = [
    "BoneSnapshot",
    "LayerEvalResult",
    "read_bone_from_action",
    "write_bone_to_action",
    "get_layer_action",
    "is_bone_on_layer",
    "get_channel_weights",
    "has_solo_layer",
    "evaluate_layer_stack",
    "apply_eval_result",
]

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Layer snapshot — bone-level transform data read from an Action
# ---------------------------------------------------------------------------

@dataclass
class BoneSnapshot:
    """Transform values for a single bone read from an Action at a frame."""
    bone_name: str
    location: tuple[float, float, float] = bm.REST_LOCATION
    rotation: tuple[float, float, float] = bm.REST_ROTATION
    scale: tuple[float, float, float] = bm.REST_SCALE
    has_keys: bool = False


@dataclass
class LayerEvalResult:
    """Result of evaluating the full layer stack for one bone."""
    bone_name: str
    final_location: tuple[float, float, float] = bm.REST_LOCATION
    final_rotation: tuple[float, float, float] = bm.REST_ROTATION
    final_scale: tuple[float, float, float] = bm.REST_SCALE
    layers_applied: list[str] = field(default_factory=list)
    channels_written: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Action reading utilities
# ---------------------------------------------------------------------------

_EULER_MODES = ("XYZ", "XZY", "YXZ", "YZX", "ZXY", "ZYX")


def _rotation_path_for_mode(mode: str) -> str:
    if mode == "QUATERNION":
        return "rotation_quaternion"
    if mode == "AXIS_ANGLE":
        return "rotation_axis_angle"
    return "rotation_euler"


def _euler_to_mode(rot, mode: str):  # type: ignore[no-untyped-def]
    """Express an (x, y, z) euler triple in *mode* (4-tuple for quat/axis-angle)."""
    if mode not in ("QUATERNION", "AXIS_ANGLE"):
        return tuple(rot)
    from mathutils import Euler
    q = Euler(rot, "XYZ").to_quaternion()
    if mode == "QUATERNION":
        return tuple(q)
    ax, ang = q.to_axis_angle()
    return (ang, ax.x, ax.y, ax.z)


def _mode_to_euler(values, mode: str):  # type: ignore[no-untyped-def]
    """Bring a rotation stored in *mode* back to the engine's euler triple."""
    if mode not in ("QUATERNION", "AXIS_ANGLE"):
        return tuple(values)
    from mathutils import Quaternion
    if mode == "QUATERNION":
        q = Quaternion(values)
    else:
        q = Quaternion(values[1:], values[0])
    return tuple(q.to_euler("XYZ"))


def _infer_rotation_mode(action, prefix: str) -> str:  # type: ignore[no-untyped-def]
    """Rotation mode implied by the curves already keyed under *prefix*."""
    found = set()
    for fc in get_fcurves(action):
        if fc.data_path.startswith(prefix):
            found.add(fc.data_path[len(prefix):])
    if "rotation_quaternion" in found:
        return "QUATERNION"
    if "rotation_axis_angle" in found:
        return "AXIS_ANGLE"
    if "rotation_euler" in found:
        return "XYZ"
    # Nothing keyed yet (fresh layer action): ask the rig itself.  Only
    # trust an unambiguous answer - exactly one armature owning that bone.
    try:
        import bpy
        end = prefix.find('"]')
        bone_name = prefix[len('pose.bones["'):end] if end > 0 else ""
        owners = [o for o in bpy.data.objects
                  if o.type == "ARMATURE" and o.pose and o.pose.bones.get(bone_name)]
        if len(owners) == 1:
            return owners[0].pose.bones[bone_name].rotation_mode
    except Exception:  # noqa: BLE001 - outside Blender or no data
        pass
    return "XYZ"


def bone_rotation_mode(armature_obj, bone_name: str) -> str:  # type: ignore[no-untyped-def]
    """``rotation_mode`` of a pose bone, or XYZ when it cannot be resolved."""
    pose = getattr(armature_obj, "pose", None)
    pb = pose.bones.get(bone_name) if pose is not None else None
    return getattr(pb, "rotation_mode", "XYZ") if pb is not None else "XYZ"


def read_bone_from_action(
    action: Action | None,
    bone_name: str,
    frame: float,
    rotation_mode: str = "XYZ",
) -> BoneSnapshot:
    """Read a bone's transform from an Action at a specific frame.

    Evaluates the Action's fcurves for the given bone and frame,
    returning a BoneSnapshot with the sampled values.

    Parameters
    ----------
    action : bpy.types.Action
        The Blender Action to read from.
    bone_name : str
        The name of the pose bone.
    frame : float
        The frame number to sample at.

    Returns
    -------
    BoneSnapshot
        The sampled transform values.
    """
    snap = BoneSnapshot(bone_name=bone_name)
    if action is None:
        return snap

    prefix = f'pose.bones["{_escape_bone_name(bone_name)}"].'

    loc = list(bm.REST_LOCATION)
    rot = list(bm.REST_ROTATION)
    sca = list(bm.REST_SCALE)
    found = False
    quat = [1.0, 0.0, 0.0, 0.0]
    aa = [0.0, 0.0, 1.0, 0.0]
    quat_found = aa_found = False

    for fc in get_fcurves(action):
        if not fc.data_path.startswith(prefix):
            continue
        channel = fc.data_path[len(prefix):]
        idx = fc.array_index

        val = fc.evaluate(frame)
        found = True

        if channel == "location" and 0 <= idx <= 2:
            loc[idx] = val
        elif channel == "rotation_euler" and 0 <= idx <= 2:
            rot[idx] = val
        elif channel == "rotation_quaternion" and 0 <= idx <= 3:
            quat[idx] = val
            quat_found = True
        elif channel == "rotation_axis_angle" and 0 <= idx <= 3:
            aa[idx] = val
            aa_found = True
        elif channel == "scale" and 0 <= idx <= 2:
            sca[idx] = val

    # The engine blends euler triples; bring quaternion / axis-angle curves to
    # that form.  Prefer the curves matching the bone's own rotation mode.
    if rotation_mode == "QUATERNION" and quat_found:
        rot = list(_mode_to_euler(quat, "QUATERNION"))
    elif rotation_mode == "AXIS_ANGLE" and aa_found:
        rot = list(_mode_to_euler(aa, "AXIS_ANGLE"))
    elif quat_found and rot == list(bm.REST_ROTATION):
        rot = list(_mode_to_euler(quat, "QUATERNION"))
    elif aa_found and rot == list(bm.REST_ROTATION):
        rot = list(_mode_to_euler(aa, "AXIS_ANGLE"))

    snap.location = tuple(loc)
    snap.rotation = tuple(rot)
    snap.scale = tuple(sca)
    snap.has_keys = found
    return snap


def write_bone_to_action(
    action: Action | None,
    bone_name: str,
    frame: float,
    location: tuple[float, float, float] | None = None,
    rotation: tuple[float, float, float] | None = None,
    scale: tuple[float, float, float] | None = None,
    rotation_mode: str | None = None,
) -> int:
    """Write a bone's transform into an Action at a specific frame.

    Creates fcurves as needed and inserts keyframes.

    Parameters
    ----------
    action : bpy.types.Action
        The Blender Action to write to.
    bone_name : str
        The name of the pose bone.
    frame : float
        The frame number to key at.
    location, rotation, scale : 3-tuples, optional
        Values to key.  ``None`` means skip that channel.

    Returns
    -------
    int
        Number of keyframes inserted.
    """
    if action is None:
        return 0

    prefix = f'pose.bones["{_escape_bone_name(bone_name)}"].'
    keyed = 0

    channel_map = []
    if location is not None:
        channel_map.append(("location", location))
    if rotation is not None:
        # Key the property the bone actually reads; a quaternion bone keyed on
        # rotation_euler never moves and collects dead curves.  When the
        # caller does not say which mode the bone uses, follow whatever
        # rotation curves already exist for this bone on the action.
        if rotation_mode is None:
            rotation_mode = _infer_rotation_mode(action, prefix)
        channel_map.append((_rotation_path_for_mode(rotation_mode),
                            _euler_to_mode(rotation, rotation_mode)))
    if scale is not None:
        channel_map.append(("scale", scale))

    touched = []
    for channel_name, values in channel_map:
        data_path = prefix + channel_name
        for idx in range(len(values)):
            fc = find_fcurve(action, data_path, idx)
            if fc is None:
                fc = new_fcurve(action, data_path, idx)
            fc.keyframe_points.insert(frame, values[idx], options={'FAST'})
            touched.append(fc)
            keyed += 1

    # FAST skips handle recalculation; flush once per curve or handles stay stale.
    for fc in touched:
        fc.update()

    return keyed


# ---------------------------------------------------------------------------
# Layer-level helpers
# ---------------------------------------------------------------------------

def get_layer_action(layer: PropertyGroup, create: bool = False) -> Action | None:
    """Return the Blender Action for a layer, optionally creating it.

    Parameters
    ----------
    layer : AA_P11_AnimLayer
        The layer PropertyGroup.
    create : bool
        If True and the action doesn't exist, create a new one.

    Returns
    -------
    bpy.types.Action or None
    """
    import bpy

    name = layer.action_name
    if name and name in bpy.data.actions:
        return bpy.data.actions[name]

    if create:
        action = bpy.data.actions.new(name=f"AA_Layer_{layer.name}")
        action.use_fake_user = True
        layer.action_name = action.name
        return action

    return None


def is_bone_on_layer(layer: PropertyGroup, bone_name: str) -> bool:
    """Check if a bone is assigned to a layer.

    If the layer has no assignments, it affects ALL bones (whole-body).
    """
    if len(layer.assigned_bones) == 0:
        return True
    return any(b.bone_name == bone_name for b in layer.assigned_bones)


def get_channel_weights(layer: PropertyGroup, bone_name: str) -> tuple[float, float, float]:
    """Get per-channel weight overrides for a bone on a layer.

    Returns (loc_weight, rot_weight, sca_weight).  If no override
    exists, returns (1.0, 1.0, 1.0).
    """
    for ovr in layer.channel_overrides:
        if ovr.bone_name == bone_name:
            return (ovr.location_weight, ovr.rotation_weight, ovr.scale_weight)
    return (1.0, 1.0, 1.0)


def has_solo_layer(p11: PropertyGroup) -> bool:
    """Return True if any layer in the stack has solo enabled."""
    return any(layer.solo for layer in p11.layers)


# ---------------------------------------------------------------------------
# Full stack evaluation
# ---------------------------------------------------------------------------

def evaluate_layer_stack(
    p11: PropertyGroup,
    bone_name: str,
    frame: float,
    armature_obj: Object | None = None,
) -> LayerEvalResult:
    """Evaluate the full layer stack for a single bone at a frame.

    Accumulates transforms from the base layer upward, applying each
    active layer's blend mode and weight.

    Parameters
    ----------
    p11 : AA_P11_Properties
        The animation layer scene PropertyGroup.
    bone_name : str
        Name of the bone to evaluate.
    frame : float
        Frame number to sample at.
    armature_obj : bpy.types.Object, optional
        The armature object (for base action access).

    Returns
    -------
    LayerEvalResult
        The final accumulated transforms.
    """
    result = LayerEvalResult(bone_name=bone_name)

    if not p11.layers_enabled or len(p11.layers) == 0:
        return result

    solo_active = has_solo_layer(p11)

    # Start with rest pose as the base accumulator.
    acc_loc = bm.REST_LOCATION
    acc_rot = bm.REST_ROTATION
    acc_sca = bm.REST_SCALE

    for layer in p11.layers:
        # --- Skip conditions ---
        if layer.mute:
            continue
        if layer.weight <= 0.0:
            continue
        if solo_active and not layer.solo and not layer.is_base_layer:
            continue
        if not is_bone_on_layer(layer, bone_name):
            continue

        # --- Scope filter ---
        scope = layer.layer_scope
        loc_active = scope in ("ALL", "LOCATION", "CUSTOM")
        rot_active = scope in ("ALL", "ROTATION", "CUSTOM")
        sca_active = scope in ("ALL", "SCALE", "CUSTOM")

        if scope == "CUSTOM" and layer.custom_filter:
            filters = [f.strip() for f in layer.custom_filter.split(",")]
            loc_active = any("location" in f for f in filters)
            rot_active = any("rotation" in f for f in filters)
            sca_active = any("scale" in f for f in filters)

        # --- Read layer action ---
        action = get_layer_action(layer)
        if action is None and layer.is_base_layer and armature_obj is not None:
            # Base layer uses the object's active action.
            anim_data = getattr(armature_obj, "animation_data", None)
            if anim_data is not None:
                action = anim_data.action

        snap = read_bone_from_action(
            action, bone_name, frame,
            rotation_mode=bone_rotation_mode(armature_obj, bone_name),
        )

        if not snap.has_keys and not layer.is_base_layer:
            continue

        # --- Get per-channel weights ---
        lw, rw, sw = get_channel_weights(layer, bone_name)
        if not loc_active:
            lw = 0.0
        if not rot_active:
            rw = 0.0
        if not sca_active:
            sw = 0.0

        # --- Blend ---
        mode = layer.blend_mode if not layer.is_base_layer else "OVERRIDE"
        blend_result = bm.blend_transforms(
            blend_mode=mode,
            base_loc=acc_loc,
            base_rot=acc_rot,
            base_sca=acc_sca,
            layer_loc=snap.location,
            layer_rot=snap.rotation,
            layer_sca=snap.scale,
            weight=layer.weight,
            loc_weight=lw,
            rot_weight=rw,
            sca_weight=sw,
        )

        acc_loc = blend_result.location
        acc_rot = blend_result.rotation
        acc_sca = blend_result.scale
        result.layers_applied.append(layer.name)
        result.channels_written.extend(blend_result.channels_blended)

    result.final_location = acc_loc
    result.final_rotation = acc_rot
    result.final_scale = acc_sca
    return result


def apply_eval_result(
    bone: PoseBone,
    eval_result: LayerEvalResult,
    respect_locks: bool = True,
) -> list[str]:
    """Write a LayerEvalResult to a pose bone.

    Parameters
    ----------
    bone : bpy.types.PoseBone
        The bone to write to.
    eval_result : LayerEvalResult
        The evaluated transforms.
    respect_locks : bool
        Skip locked channels.

    Returns
    -------
    list[str]
        List of channels written.
    """
    channels = []

    if "location" in eval_result.channels_written:
        for i in range(3):
            if respect_locks and bone.lock_location[i]:
                continue
            bone.location[i] = eval_result.final_location[i]
        channels.append("location")

    if "rotation" in eval_result.channels_written:
        mode = getattr(bone, "rotation_mode", "XYZ")
        if mode in ("QUATERNION", "AXIS_ANGLE"):
            # Written whole; any rotation lock skips it (a partial quaternion
            # has no meaning).
            locked = respect_locks and (
                any(bone.lock_rotation) or getattr(bone, "lock_rotation_w", False)
            )
            if not locked:
                path = _rotation_path_for_mode(mode)
                setattr(bone, path, _euler_to_mode(eval_result.final_rotation, mode))
                channels.append(path)
        else:
            for i in range(3):
                if respect_locks and bone.lock_rotation[i]:
                    continue
                bone.rotation_euler[i] = eval_result.final_rotation[i]
            channels.append("rotation_euler")

    if "scale" in eval_result.channels_written:
        for i in range(3):
            if respect_locks and bone.lock_scale[i]:
                continue
            bone.scale[i] = eval_result.final_scale[i]
        channels.append("scale")

    return channels


# ---------------------------------------------------------------------------
# Layer stack manipulation
# ---------------------------------------------------------------------------

def ensure_base_layer(p11) -> None:
    """Ensure the layer stack has a base layer at index 0.

    The layer stack requires at least one base layer for evaluation. If no layers exist
    (e.g., after a file load or undo that cleared the stack), this creates a default
    OVERRIDE layer so blend operations never encounter an empty stack.
    """
    if len(p11.layers) == 0 or not p11.layers[0].is_base_layer:
        layer = p11.layers.add()
        layer.name = "Base Layer"
        layer.is_base_layer = True
        layer.weight = 1.0
        layer.blend_mode = "OVERRIDE"
        layer.protected = True
        # Move to index 0.
        if len(p11.layers) > 1:
            p11.layers.move(len(p11.layers) - 1, 0)
        p11.eval_generation += 1


def add_layer(
    p11,
    name: str = "New Layer",
    blend_mode: str = "OVERRIDE",
    weight: float = 1.0,
) -> int:
    """Add a new animation layer to the top of the stack.

    Returns the index of the new layer.
    """
    ensure_base_layer(p11)
    layer = p11.layers.add()
    layer.name = name
    layer.blend_mode = blend_mode
    layer.weight = weight
    layer.is_base_layer = False
    p11.active_layer_index = len(p11.layers) - 1
    p11.eval_generation += 1
    return len(p11.layers) - 1


def remove_layer(p11, index: int) -> bool:
    """Remove a layer by index.  Cannot remove the base layer.

    Returns True if removed, False if refused.
    """
    if index < 0 or index >= len(p11.layers):
        return False
    layer = p11.layers[index]
    if layer.is_base_layer:
        logger.warning("Cannot remove the base layer")
        return False
    if layer.protected:
        logger.warning("Cannot remove a protected layer")
        return False

    p11.layers.remove(index)
    if p11.active_layer_index >= len(p11.layers):
        p11.active_layer_index = max(0, len(p11.layers) - 1)
    p11.eval_generation += 1
    return True


def move_layer(p11, from_index: int, to_index: int) -> bool:
    """Move a layer within the stack.  Cannot move the base layer.

    Returns True if moved, False if refused.
    """
    n = len(p11.layers)
    if from_index < 0 or from_index >= n:
        return False
    if to_index < 0 or to_index >= n:
        return False
    if from_index == to_index:
        return False
    layer = p11.layers[from_index]
    if layer.is_base_layer:
        logger.warning("Cannot reorder the base layer")
        return False
    # Don't allow moving below the base layer.
    if to_index == 0 and p11.layers[0].is_base_layer:
        to_index = 1

    p11.layers.move(from_index, to_index)
    p11.active_layer_index = to_index
    p11.eval_generation += 1
    return True


def duplicate_layer(p11, index: int) -> int:
    """Duplicate a layer (excluding the base).  Returns new index or -1."""
    if index < 0 or index >= len(p11.layers):
        return -1
    src = p11.layers[index]
    if src.is_base_layer:
        logger.warning("Cannot duplicate the base layer")
        return -1

    new_idx = add_layer(p11, name=f"{src.name} Copy",
                        blend_mode=src.blend_mode,
                        weight=src.weight)
    dst = p11.layers[new_idx]
    dst.layer_scope = src.layer_scope
    dst.custom_filter = src.custom_filter
    dst.layer_color = src.layer_color

    # Copy bone assignments.
    for bone_assign in src.assigned_bones:
        new_assign = dst.assigned_bones.add()
        new_assign.bone_name = bone_assign.bone_name

    # Copy channel overrides.
    for ovr in src.channel_overrides:
        new_ovr = dst.channel_overrides.add()
        new_ovr.bone_name = ovr.bone_name
        new_ovr.location_weight = ovr.location_weight
        new_ovr.rotation_weight = ovr.rotation_weight
        new_ovr.scale_weight = ovr.scale_weight

    # Copy Action data if it exists.
    src_action = get_layer_action(src)
    if src_action is not None:
        new_action = src_action.copy()
        new_action.name = f"AA_Layer_{dst.name}"
        new_action.use_fake_user = True
        dst.action_name = new_action.name

    return new_idx


# ---------------------------------------------------------------------------
# Merge / Flatten
# ---------------------------------------------------------------------------

def merge_layer_down(p11, index: int, armature_obj=None) -> bool:
    """Merge a layer into the one below it.

    Evaluates the active layer and the one below it frame-by-frame across the bake range,
    blends them using the active layer's blend mode and weight, then writes the combined
    result into the lower layer's action and removes the active layer.

    Parameters
    ----------
    p11 : AA_P11_Properties
    index : int
        Index of the layer to merge down.
    armature_obj : bpy.types.Object, optional
        The armature for base action access.

    Returns
    -------
    bool
        True if merged, False if refused.
    """

    if index <= 0 or index >= len(p11.layers):
        return False
    upper = p11.layers[index]
    lower = p11.layers[index - 1]

    if upper.is_base_layer or upper.protected:
        return False

    upper_action = get_layer_action(upper)
    lower_action = get_layer_action(lower, create=True)

    if upper_action is None:
        # Nothing to merge.
        remove_layer(p11, index)
        return True

    # Collect all keyed frames from the upper layer.
    keyed_frames = set()
    for fc in get_fcurves(upper_action):
        for kp in fc.keyframe_points:
            keyed_frames.add(kp.co[0])

    # Collect bone names from the upper layer.
    if len(upper.assigned_bones) > 0:
        bone_names = [b.bone_name for b in upper.assigned_bones]
    else:
        # All bones — collect from action fcurves.
        bone_names = set()
        for fc in get_fcurves(upper_action):
            if fc.data_path.startswith('pose.bones["'):
                end = fc.data_path.index('"]')
                name = fc.data_path[len('pose.bones["'):end]
                bone_names.add(name)
        bone_names = list(bone_names)

    for frame in sorted(keyed_frames):
        for bone_name in bone_names:
            # Read both layers.
            mode = bone_rotation_mode(armature_obj, bone_name)
            lower_snap = read_bone_from_action(lower_action, bone_name, frame, rotation_mode=mode)
            upper_snap = read_bone_from_action(upper_action, bone_name, frame, rotation_mode=mode)

            if not upper_snap.has_keys:
                continue

            # Blend.
            lw, rw, sw = get_channel_weights(upper, bone_name)
            blend_result = bm.blend_transforms(
                blend_mode=upper.blend_mode,
                base_loc=lower_snap.location,
                base_rot=lower_snap.rotation,
                base_sca=lower_snap.scale,
                layer_loc=upper_snap.location,
                layer_rot=upper_snap.rotation,
                layer_sca=upper_snap.scale,
                weight=upper.weight,
                loc_weight=lw,
                rot_weight=rw,
                sca_weight=sw,
            )

            # Write merged result to lower action.
            write_bone_to_action(
                lower_action, bone_name, frame,
                location=blend_result.location,
                rotation=blend_result.rotation,
                scale=blend_result.scale,
                rotation_mode=mode,
            )

    # Remove upper layer.
    remove_layer(p11, index)
    return True


def flatten_all(p11, armature_obj=None) -> bool:
    """Flatten all layers into the base layer.

    Repeatedly merges the topmost layer down until only the base remains.
    """
    while len(p11.layers) > 1:
        top_idx = len(p11.layers) - 1
        if not merge_layer_down(p11, top_idx, armature_obj):
            return False
    return True


# ---------------------------------------------------------------------------
# Preset serialization
# ---------------------------------------------------------------------------

def serialize_layer_stack(p11) -> str:
    """Serialize the layer stack configuration to JSON (no Action data).

    Useful for saving layer setups as presets.
    """
    data = {
        "layers": [],
        "edit_active_only": p11.edit_active_only,
        "auto_assign_on_key": p11.auto_assign_on_key,
    }
    for layer in p11.layers:
        layer_data = {
            "name": layer.name,
            "blend_mode": layer.blend_mode,
            "weight": layer.weight,
            "mute": layer.mute,
            "solo": layer.solo,
            "locked": layer.locked,
            "protected": layer.protected,
            "layer_scope": layer.layer_scope,
            "custom_filter": layer.custom_filter,
            "layer_color": layer.layer_color,
            "is_base_layer": layer.is_base_layer,
            "assigned_bones": [b.bone_name for b in layer.assigned_bones],
            "channel_overrides": [
                {
                    "bone_name": ovr.bone_name,
                    "location_weight": ovr.location_weight,
                    "rotation_weight": ovr.rotation_weight,
                    "scale_weight": ovr.scale_weight,
                }
                for ovr in layer.channel_overrides
            ],
        }
        data["layers"].append(layer_data)
    return json.dumps(data, indent=2)


def deserialize_layer_stack(p11, json_str: str) -> bool:
    """Restore a layer stack configuration from JSON.

    Clears the existing stack and rebuilds it.
    Does NOT restore Action data — only the layer structure.
    """
    try:
        data = json.loads(json_str)
    except (json.JSONDecodeError, ValueError) as e:
        logger.error("Failed to deserialize layer stack: %s", e)
        return False

    # Clear existing layers.
    p11.layers.clear()

    for layer_data in data.get("layers", []):
        layer = p11.layers.add()
        layer.name = layer_data.get("name", "Layer")
        layer.blend_mode = layer_data.get("blend_mode", "OVERRIDE")
        layer.weight = layer_data.get("weight", 1.0)
        layer.mute = layer_data.get("mute", False)
        layer.solo = layer_data.get("solo", False)
        layer.locked = layer_data.get("locked", False)
        layer.protected = layer_data.get("protected", False)
        layer.layer_scope = layer_data.get("layer_scope", "ALL")
        layer.custom_filter = layer_data.get("custom_filter", "")
        layer.layer_color = layer_data.get("layer_color", "DEFAULT")
        layer.is_base_layer = layer_data.get("is_base_layer", False)

        for bone_name in layer_data.get("assigned_bones", []):
            ba = layer.assigned_bones.add()
            ba.bone_name = bone_name

        for ovr_data in layer_data.get("channel_overrides", []):
            ovr = layer.channel_overrides.add()
            ovr.bone_name = ovr_data.get("bone_name", "")
            ovr.location_weight = ovr_data.get("location_weight", 1.0)
            ovr.rotation_weight = ovr_data.get("rotation_weight", 1.0)
            ovr.scale_weight = ovr_data.get("scale_weight", 1.0)

    p11.edit_active_only = data.get("edit_active_only", True)
    p11.auto_assign_on_key = data.get("auto_assign_on_key", False)
    p11.eval_generation += 1
    return True
