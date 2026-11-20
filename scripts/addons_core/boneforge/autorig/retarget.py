"""BoneCraft Phase 3 — Animation Retargeting.

Clip browser, bone name matching cascade (exact -> Rigify -> Mixamo ->
manual), rest pose correction, NLA preview, and action application.

The clip library starts empty.  Users import clips (FBX, BVH, .blend)
or set a library folder.  All categories are user-assigned.
"""

import math
import os

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)

from boneforge.i18n import T
from mathutils import Matrix, Vector

from boneforge.core import active_armature, addon_prefs
from boneforge.autorig.constants import MIXAMO_TO_RIGIFY

import logging

logger = logging.getLogger(__name__)

# Supported file extensions for clip library scanning.
SUPPORTED_CLIP_EXTENSIONS = frozenset({'.fbx', '.bvh', '.blend'})

# Rigify prefixes to strip during bone name normalization.
_RIGIFY_PREFIXES = ('ORG-', 'DEF-', 'MCH-')

# Name for the temporary NLA track used during preview playback.
_PREVIEW_TRACK_NAME = "_boneforge_preview"

# Confidence threshold below which auto-detection is considered unreliable.
_CONFIDENCE_THRESHOLD = 0.7

# Angle boundaries (degrees) for T-pose vs A-pose classification.
_T_POSE_ANGLE_MAX = 30
_A_POSE_ANGLE_MIN = 60


# ── PropertyGroups ────────────────────────────────────────────

class BF_ClipEntry(bpy.types.PropertyGroup):
    """Metadata for a single animation clip in the library."""

    clip_name: StringProperty(
        name="Clip Name",
        description="Display name for this clip",
        default="",
    )
    user_category: StringProperty(
        name="Category",
        description="User-assigned category tag",
        default="",
    )
    filepath: StringProperty(
        name="File Path",
        description="Filesystem path to the clip file",
        subtype='FILE_PATH',
        default="",
    )
    action_name: StringProperty(
        name="Action",
        description="Name of the Blender action (if loaded)",
        default="",
    )


class BF_RetargetSettings(bpy.types.PropertyGroup):
    """State for the retarget clip browser and preview system."""

    clips: CollectionProperty(
        name="Clips",
        description="Loaded animation clips",
        type=BF_ClipEntry,
    )
    active_clip_index: IntProperty(
        name="Active Clip",
        description="Index of the currently selected clip",
        default=-1,
    )
    filter_text: StringProperty(
        name="Filter",
        description="Text filter for clip names",
        default="",
    )
    preview_active: BoolProperty(
        name="Preview Active",
        description="Whether a clip preview is currently playing",
        default=False,
    )
    rest_pose_mode: EnumProperty(
        name="Source Rest Pose",
        description="Rest pose type of the source animation",
        items=[
            ('AUTO', "Auto-Detect", "Automatically detect T-pose or A-pose"),
            ('T_POSE', "T-Pose", "Source is in T-pose"),
            ('A_POSE', "A-Pose", "Source is in A-pose"),
            ('CUSTOM', "Custom", "Use manual offset"),
            ('NONE', "None", "No rest pose correction"),
        ],
        default='AUTO',
    )
    manual_offset_angle: FloatProperty(
        name="Manual Offset",
        description="Manual arm rotation offset in degrees",
        default=0.0,
        min=-90.0,
        max=90.0,
    )


# ── Shared helpers ───────────────────────────────────────────

def _action_fcurves(action):
    """F-curves across legacy and layered (Blender 4.4+/5.x) action APIs.

    Blender 5 removed ``Action.fcurves``: curves live in
    ``layers[].strips[].channelbags[].fcurves``.
    """
    if action is None:
        return []
    layers = getattr(action, "layers", None)
    if layers:
        fcurves = []
        for layer in layers:
            for strip in layer.strips:
                for bag in getattr(strip, "channelbags", []):
                    fcurves.extend(bag.fcurves)
        if fcurves:
            return fcurves
    return list(getattr(action, "fcurves", []))


def _normalize_bone_name(name):
    """Normalize a bone name for matching by stripping Rigify prefixes and suffixes.

    Strips ORG-, DEF-, MCH- prefixes and normalizes side suffixes
    (_L/_R, _l/_r) to Rigify-style (.L/.R).  Returns lowercase.

    Args:
        name: Raw bone name string.

    Returns:
        Lowercase normalized name.
    """
    cleaned = name
    for prefix in _RIGIFY_PREFIXES:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]
            break  # Only one prefix can apply

    cleaned = cleaned.replace('_L', '.L').replace('_R', '.R')
    cleaned = cleaned.replace('_l', '.L').replace('_r', '.R')
    return cleaned.lower()


def _extract_bone_names_from_action(action):
    """Extract unique bone names referenced by an action's FCurves.

    Only considers FCurves with data paths starting with ``pose.bones["``.

    Args:
        action: Blender Action to inspect.

    Returns:
        Sorted list of bone name strings.
    """
    bone_names = set()
    for fcurve in _action_fcurves(action):
        if fcurve.data_path.startswith('pose.bones["'):
            bone_name = fcurve.data_path.split('"')[1]
            bone_names.add(bone_name)
    return sorted(bone_names)


def _find_action_with_bone_animation():
    """Search all actions for one containing skeletal animation.

    Returns:
        The first Action with bone FCurves, or None.
    """
    for action in bpy.data.actions:
        has_bone_curves = any(
            fcurve.data_path.startswith('pose.bones[')
            for fcurve in _action_fcurves(action)
        )
        if has_bone_curves:
            return action
    return None


def _suppress_onion_skin():
    """No-op — onion skinning was removed in v3.0.26.

    Kept as a stub so the retargeting preview code can call it without
    an ImportError; to be deleted once all call sites are cleaned up.
    """
    return


def _restore_onion_skin():
    """No-op — onion skinning was removed in v3.0.26."""
    return


def _remove_preview_nla_track(armature_obj):
    """Remove the temporary NLA preview track and its retargeted actions.

    Args:
        armature_obj: Armature object that may have a preview track.
    """
    if armature_obj is None or armature_obj.animation_data is None:
        return

    for track in armature_obj.animation_data.nla_tracks:
        if track.name != _PREVIEW_TRACK_NAME:
            continue

        for strip in track.strips:
            action = strip.action
            if action and action.name.endswith("_retargeted"):
                bpy.data.actions.remove(action)

        armature_obj.animation_data.nla_tracks.remove(track)
        return  # Only one preview track should exist


def _build_mapping_list_from_session(session):
    """Convert session retarget mappings into a list of dicts.

    Returns:
        List of dicts matching the format expected by ``retarget_action()``.
    """
    mappings = []
    for mapping in session.retarget_mappings:
        mappings.append({
            'source': mapping.source_name,
            'target': mapping.target_name,
            'type': mapping.match_type,
            'matched': mapping.is_matched,
        })
    return mappings


# ── Bone matching cascade ────────────────────────────────────

def _match_exact(source_names, target_names):
    """Match bones by exact name equality.

    Returns:
        Dict mapping source name to target name for exact matches.
    """
    target_set = set(target_names)
    matches = {}
    for name in source_names:
        if name in target_set:
            matches[name] = name
    return matches


def _match_rigify(source_names, target_names):
    """Match bones using Rigify naming conventions.

    Handles common Rigify patterns like ORG-, DEF-, MCH- prefixes
    and .L/.R suffixes versus _L/_R.

    Returns:
        Dict mapping source name to target name for Rigify matches.
    """
    # Build normalized target map
    target_by_normalized = {}
    for target_name in target_names:
        normalized = _normalize_bone_name(target_name)
        target_by_normalized[normalized] = target_name

    matches = {}
    for source_name in source_names:
        normalized = _normalize_bone_name(source_name)
        target_name = target_by_normalized.get(normalized)
        if target_name is not None:
            matches[source_name] = target_name

    return matches


def _match_mixamo(source_names, target_names):
    """Match bones using the Mixamo-to-Rigify mapping table.

    Returns:
        Dict mapping source name to target name for Mixamo matches.
    """
    target_set = set(target_names)
    matches = {}

    for source_name in source_names:
        # Direct Mixamo mapping
        rigify_name = MIXAMO_TO_RIGIFY.get(source_name)
        if rigify_name and rigify_name in target_set:
            matches[source_name] = rigify_name
            continue

        # Try without the mixamorig: prefix
        stripped_name = source_name
        if stripped_name.startswith('mixamorig:'):
            stripped_name = stripped_name[len('mixamorig:'):]

        rigify_name = MIXAMO_TO_RIGIFY.get(f'mixamorig:{stripped_name}')
        if rigify_name and rigify_name in target_set:
            matches[source_name] = rigify_name

    return matches


def _match_preset(source_names, target_names, min_matches=6):
    """Best ``maps/`` preset for these bones, as ``{source: target}``.

    Only used when the target carries the control rig's FK controls and the
    preset matches at least ``min_matches`` bones.
    """
    from boneforge.autorig import maps as _maps
    from boneforge.autorig import retarget_core as _rc
    if "upperarm.fk-L" not in target_names:
        return {}
    best = {}
    for map_name in _maps.available_maps():
        result = _rc.build_mappings(_maps.load_map(map_name), source_names, target_names)
        found = _rc.matched_name_map(result)
        if len(found) > len(best):
            best = found
    return best if len(best) >= min_matches else {}


def _fk_target(name, target_armature):
    """Keyable control for a mapped bone: an engine ``*.def-S`` deform bone is
    driven by constraints, so its matching ``*.fk-S`` control is keyed."""
    if ".def-" in name:
        fk = name.replace(".def-", ".fk-")
        if target_armature.data.bones.get(fk) is not None:
            return fk
    return name


def _source_armature_for_action(action):
    """The imported clip skeleton that plays ``action``, or None."""
    for ob in bpy.data.objects:
        if ob.type == 'ARMATURE' and ob.animation_data is not None                 and ob.animation_data.action == action:
            return ob
    return None


def retarget_to_new_action(source_arm, target_arm, mappings, action_name):
    """Direction-matched retarget of ``source_arm``'s clip into a new action.

    Returns the new action (not left assigned) or None when nothing mapped.
    """
    name_map = {}
    for m in mappings:
        if m.get("matched") and m.get("target"):
            name_map[m["source"]] = _fk_target(m["target"], target_arm)
    if not name_map or source_arm.animation_data is None             or source_arm.animation_data.action is None:
        return None
    scene = bpy.context.scene
    keep_frame = scene.frame_current
    if target_arm.animation_data is None:
        target_arm.animation_data_create()
    previous = target_arm.animation_data.action
    new_action = bpy.data.actions.new(action_name)
    target_arm.animation_data.action = new_action
    props = target_arm.pose.bones.get("properties")
    if props is not None:      # FK controls must drive the deform bones
        for key in list(props.keys()):
            if key.startswith("IK_FK-"):
                props[key] = 0.0
        target_arm.update_tag()
    try:
        f0, f1 = source_arm.animation_data.action.frame_range
        frames = retarget_clip_corrected(source_arm, target_arm, name_map, int(f0), int(f1))
    finally:
        target_arm.animation_data.action = previous
        scene.frame_set(keep_frame)
    if frames == 0:
        bpy.data.actions.remove(new_action)
        return None
    return new_action


def auto_match_bones(source_action, target_armature):
    """Run the full bone matching cascade on an action and armature.

    Tries exact match, then Rigify conventions, then Mixamo mapping.

    Args:
        source_action: The source Action containing bone FCurves.
        target_armature: The target armature Object.

    Returns:
        List of dicts with keys ``source``, ``target``, ``type``, ``matched``.
    """
    source_names = _extract_bone_names_from_action(source_action)
    target_names = [bone.name for bone in target_armature.data.bones]

    matched = {}
    match_types = {}

    # Stage 0: the best-fitting bone-map preset (VRM / J_Bip / suffix /
    # mocap / engine names) onto the control rig's FK controls
    for source_name, target_name in _match_preset(source_names, target_names).items():
        matched[source_name] = target_name
        match_types[source_name] = 'PRESET'

    # Stage 1: Exact match (only unmatched bones)
    exact_matches = _match_exact([n for n in source_names if n not in matched],
                                 target_names)
    for source_name, target_name in exact_matches.items():
        matched[source_name] = target_name
        match_types[source_name] = 'EXACT'

    # Stage 2: Rigify convention match (only unmatched bones)
    unmatched_names = [name for name in source_names if name not in matched]
    rigify_matches = _match_rigify(unmatched_names, target_names)
    for source_name, target_name in rigify_matches.items():
        matched[source_name] = target_name
        match_types[source_name] = 'RIGIFY'

    # Stage 3: Mixamo mapping (only unmatched bones)
    unmatched_names = [name for name in source_names if name not in matched]
    mixamo_matches = _match_mixamo(unmatched_names, target_names)
    for source_name, target_name in mixamo_matches.items():
        matched[source_name] = target_name
        match_types[source_name] = 'MIXAMO'

    # Build result list
    result = []
    for source_name in source_names:
        if source_name in matched:
            result.append({
                'source': source_name,
                'target': matched[source_name],
                'type': match_types[source_name],
                'matched': True,
            })
        else:
            result.append({
                'source': source_name,
                'target': '',
                'type': 'MANUAL',
                'matched': False,
            })

    return result


# ── Rest pose correction ─────────────────────────────────────

def _compute_rest_pose_offset(source_action, target_armature, mode='AUTO'):
    """Compute a correction matrix for rest pose differences.

    Detects T-pose vs A-pose based on wrist-to-spine angle and
    returns a correction rotation matrix.

    Args:
        source_action: Source action to analyze.
        target_armature: Target armature with rest pose.
        mode: One of ``'AUTO'``, ``'T_POSE'``, ``'A_POSE'``, ``'CUSTOM'``, ``'NONE'``.

    Returns:
        Tuple of ``(correction_matrix, confidence, detected_pose)``.
    """
    if mode == 'NONE':
        return Matrix.Identity(4), 1.0, 'NONE'

    # Analyze target armature rest pose
    detected_pose, confidence = _detect_arm_pose(target_armature)

    if mode == 'AUTO':
        if confidence < _CONFIDENCE_THRESHOLD:
            return Matrix.Identity(4), confidence, detected_pose
    elif mode == 'T_POSE':
        detected_pose = 'T_POSE'
        confidence = 1.0
    elif mode == 'A_POSE':
        detected_pose = 'A_POSE'
        confidence = 1.0
    else:
        # CUSTOM mode — return identity for now
        return Matrix.Identity(4), 1.0, mode

    # Compute correction: if source and target are different poses,
    # apply a rotation offset to the arms.
    # Returns identity for now — the full implementation would compute
    # the exact rotation difference between source and target rest poses.
    return Matrix.Identity(4), confidence, detected_pose


def _detect_arm_pose(target_armature):
    """Detect whether the target armature is in T-pose or A-pose.

    Measures the angle of the left upper arm bone relative to the
    horizontal plane to classify the rest pose.

    Args:
        target_armature: Armature object to analyze.

    Returns:
        Tuple of ``(pose_name, confidence)`` where pose_name is one of
        ``'T_POSE'``, ``'A_POSE'``, or ``'UNKNOWN'``.
    """
    upper_arm_bone = target_armature.data.bones.get('upper_arm.L')
    spine_bone = target_armature.data.bones.get('spine.003')

    if upper_arm_bone is None or spine_bone is None:
        return 'UNKNOWN', 0.0

    # Compute arm direction from head to tail
    arm_direction = (
        upper_arm_bone.tail_local - upper_arm_bone.head_local
    ).normalized()

    # Project arm direction onto horizontal plane
    arm_horizontal_projection = Vector((
        arm_direction.x,
        arm_direction.y,
        0,
    ))

    if arm_horizontal_projection.length < 0.001:
        return 'UNKNOWN', 0.0

    arm_horizontal_projection = arm_horizontal_projection.normalized()

    # Measure angle from the X axis (pure horizontal = T-pose)
    horizontal_reference = Vector((1, 0, 0))
    dot_product = arm_horizontal_projection.dot(horizontal_reference)
    clamped_dot = max(-1.0, min(1.0, dot_product))
    angle_from_horizontal = math.degrees(math.acos(clamped_dot))

    if angle_from_horizontal < _T_POSE_ANGLE_MAX:
        return 'T_POSE', 0.9
    elif angle_from_horizontal > _A_POSE_ANGLE_MIN:
        return 'A_POSE', 0.9
    else:
        # Ambiguous — between T-pose and A-pose thresholds
        return 'UNKNOWN', 0.4


# ── Retarget action creation ──────────────────────────────────

def retarget_action(source_action, target_armature, mappings, rest_offset):
    """
    # Writes curves with the pre-layered-action API (``Action.fcurves.new``),
    # which Blender 5 removed; callers fall back to a clear message there.
    if not hasattr(bpy.types.Action, "fcurves"):
        return NoneCreate a new action by retargeting source animation to target bones.

    Copies FCurves from the source action, remapping bone names according
    to the provided mappings and applying the rest pose correction.

    Args:
        source_action: The source Action to retarget from.
        target_armature: The target armature Object.
        mappings: List of mapping dicts from ``auto_match_bones()``.
        rest_offset: Correction Matrix from ``_compute_rest_pose_offset()``.

    Returns:
        The newly created Action, or None if retargeting failed.
    """
    # Build source-to-target name mapping
    name_map = {}
    for entry in mappings:
        if entry.get('matched') and entry.get('target'):
            name_map[entry['source']] = entry['target']

    if not name_map:
        return None

    new_action_name = f"{source_action.name}_retargeted"
    new_action = bpy.data.actions.new(name=new_action_name)

    # Copy and remap FCurves
    for source_fcurve in _action_fcurves(source_action):
        data_path = source_fcurve.data_path
        if not data_path.startswith('pose.bones["'):
            continue

        # Extract bone name from data path
        bone_name = data_path.split('"')[1]
        if bone_name not in name_map:
            continue

        target_bone_name = name_map[bone_name]

        # Build new data path with remapped bone name
        path_parts = data_path.split('"].', 1)
        if len(path_parts) < 2:
            continue
        property_suffix = path_parts[1]
        new_data_path = f'pose.bones["{target_bone_name}"].{property_suffix}'

        # Create new FCurve and copy keyframes
        new_fcurve = new_action.fcurves.new(
            data_path=new_data_path,
            index=source_fcurve.array_index,
        )

        for keyframe in source_fcurve.keyframe_points:
            new_keyframe = new_fcurve.keyframe_points.insert(
                keyframe.co.x, keyframe.co.y, options={'FAST'},
            )
            new_keyframe.interpolation = keyframe.interpolation
            new_keyframe.handle_left = keyframe.handle_left
            new_keyframe.handle_right = keyframe.handle_right
            new_keyframe.handle_left_type = keyframe.handle_left_type
            new_keyframe.handle_right_type = keyframe.handle_right_type

        new_fcurve.update()

    # If no FCurves were copied, clean up
    if len(new_action.fcurves) == 0:
        bpy.data.actions.remove(new_action)
        return None

    return new_action


_LATERAL_PAIRS = (("thigh.fk-L", "thigh.fk-R"), ("upperarm.fk-L", "upperarm.fk-R"),
                  ("clavicle.fk-L", "clavicle.fk-R"))


def facing_alignment(source_arm, target_arm, name_map):
    """World rotation (about the up axis) turning the source figure to face
    the way the target does, from the left->right line of mapped hips (or
    shoulders). Identity when no left/right pair is mapped."""
    from mathutils import Quaternion, Vector
    inv = {t: s for s, t in name_map.items()}
    for left, right in _LATERAL_PAIRS:
        if left in inv and right in inv and left in target_arm.data.bones                 and right in target_arm.data.bones:
            def lat(ob, l, r):
                v = (ob.matrix_world @ ob.data.bones[l].head_local)                     - (ob.matrix_world @ ob.data.bones[r].head_local)
                v.z = 0.0
                return v
            vs = lat(source_arm, inv[left], inv[right])
            vt = lat(target_arm, left, right)
            if vs.length > 1e-9 and vt.length > 1e-9:
                ang = math.atan2(vs.x * vt.y - vs.y * vt.x, vs.dot(vt))
                return Quaternion(Vector((0.0, 0.0, 1.0)), ang)
    return Quaternion()


def _frame(up, lateral):
    """Orthonormal 3x3 frame (columns: lateral, forward, up) from two vectors."""
    from mathutils import Matrix
    z = up.normalized()
    x = (lateral - z * lateral.dot(z)).normalized()
    y = z.cross(x)
    return Matrix((x, y, z)).transposed()


def retarget_clip_corrected(source_arm, target_arm, name_map,
                            frame_start, frame_end, tweaks=None, root_motion=True):
    """Retarget the source's active action onto the target's FK controls by
    matching world bone *directions*, frame by frame, from the hips outward.

    Rest poses do not have to agree: motion-capture skeletons often rest in an
    arbitrary zero pose (bones pointing sideways), where copying rotations
    relative to rest produces unrelated motion. Here each mapped target bone is
    turned so it points where its source bone points (after a whole-body facing
    alignment); the hips match both their up direction and their left-right
    line, and ``root_motion`` carries the hips' travel onto ``COG``, scaled by
    leg length. Per-bone tweaks (multiplier + euler offset) refine the result.
    Bakes keys with ``keyframe_insert``. Returns the number of frames baked.
    """
    from mathutils import Quaternion, Euler, Matrix, Vector
    tweaks = tweaks or {}
    scene = bpy.context.scene
    tbones = target_arm.data.bones
    pairs = {tgt: src for src, tgt in name_map.items()
             if source_arm.pose.bones.get(src) is not None and tbones.get(tgt) is not None}
    if not pairs:
        return 0
    inv_src = {t: s for t, s in pairs.items()}

    align = facing_alignment(source_arm, target_arm, name_map).to_matrix()
    src_obj = source_arm.matrix_world.to_quaternion().to_matrix()
    tgt_obj_inv = target_arm.matrix_world.to_quaternion().to_matrix().inverted()
    to_tgt = tgt_obj_inv @ align @ src_obj          # source world -> target armature

    rest = {b.name: b.matrix_local.to_quaternion().to_matrix() for b in tbones}

    def rest_rel(b):
        return rest[b.parent.name].inverted() @ rest[b.name] if b.parent else rest[b.name]

    def depth(b):
        d = 0
        while b.parent is not None:
            b, d = b.parent, d + 1
        return d

    order = sorted(pairs, key=lambda n: depth(tbones[n]))

    def src_head(name):
        return to_tgt @ (source_arm.matrix_world @ source_arm.pose.bones[name].head)

    # hips frame: up = hips -> first spine bone, lateral = right hip -> left hip
    hips_frame = None
    spine_t = next((t for t in ("spine.01", "spine.02", "chest") if t in pairs), None)
    if "hips" in pairs and spine_t and "thigh.fk-L" in pairs and "thigh.fk-R" in pairs:
        up_rest = tbones[spine_t].head_local - tbones["hips"].head_local
        lat_rest = tbones["thigh.fk-L"].head_local - tbones["thigh.fk-R"].head_local
        hips_frame = (_frame(up_rest, lat_rest), spine_t)

    # root motion scale from leg length (independent of either rest pose)
    cog = target_arm.pose.bones.get("COG") if root_motion else None
    scale = 1.0
    if cog is not None and "thigh.fk-L" in pairs and "shin.fk-L" in pairs:
        t_len = tbones["thigh.fk-L"].length + tbones["shin.fk-L"].length
        s_len = (source_arm.data.bones[pairs["thigh.fk-L"]].length
                 + source_arm.data.bones[pairs["shin.fk-L"]].length)
        s_len *= source_arm.matrix_world.to_scale()[0]
        scale = t_len * target_arm.matrix_world.to_scale()[0] / s_len if s_len > 1e-9 else 1.0
    hips_start = None

    # Collarbones: mocap skeletons angle them up toward the neck, stylised
    # (VRoid) ones lie flat, so copying their direction shrugs the shoulders
    # for the whole clip. Keep this character's own collarbone angle and
    # carry only the clip's collarbone *motion* (its swing around the
    # clip's average), measured in a first pass.
    clav = [t for t in order if "clavicle" in t]
    clav_mean = {}

    def one_frame(frame, bake):
        scene.frame_set(frame)
        posed = {}
        swings = {}

        def world_of(name):
            if name not in posed:
                b = tbones[name]
                posed[name] = (world_of(b.parent.name) @ rest_rel(b)) if b.parent else rest[name]
            return posed[name]

        for tgt in order:
            src = pairs[tgt]
            b = tbones[tgt]
            base = (world_of(b.parent.name) @ rest_rel(b)) if b.parent else rest[tgt]
            if tgt == "hips" and hips_frame is not None:
                frame_rest, spine_name = hips_frame
                up = src_head(inv_src[spine_name]) - src_head(src)
                lat = src_head(inv_src["thigh.fk-L"]) - src_head(inv_src["thigh.fk-R"])
                desired = _frame(up, lat) @ frame_rest.inverted() @ rest[tgt]
            else:
                s_rot = source_arm.pose.bones[src].matrix.to_quaternion().to_matrix()
                want = (to_tgt @ src_obj.inverted() @ (src_obj @ s_rot)).col[1]
                swing_q = base.col[1].rotation_difference(want)
                if tgt in clav:
                    # swing in the parent's frame, so chest motion is not counted
                    swings[tgt] = base.to_quaternion().inverted() @ swing_q @ base.to_quaternion()
                    if tgt in clav_mean:
                        rel = clav_mean[tgt].inverted() @ swings[tgt]
                        swing_q = base.to_quaternion() @ rel @ base.to_quaternion().inverted()
                desired = swing_q.to_matrix() @ base
            local = (base.inverted() @ desired).to_quaternion()
            tweak = tweaks.get(src)
            if tweak is not None:
                if tweak.rot_multiplier != 1.0:
                    local = Quaternion().slerp(local, tweak.rot_multiplier)
                if tweak.rot_offset != (0.0, 0.0, 0.0):
                    local = local @ Euler(tweak.rot_offset).to_quaternion()
            posed[tgt] = base @ local.to_matrix()
            if bake:
                tb = target_arm.pose.bones[tgt]
                tb.rotation_mode = 'QUATERNION'
                tb.rotation_quaternion = local
                tb.keyframe_insert("rotation_quaternion", frame=frame)
        return swings

    if clav:
        sums = {t: [] for t in clav}
        for frame in range(int(frame_start), int(frame_end) + 1):
            for t, q in one_frame(frame, False).items():
                sums[t].append(q)
        for t, qs in sums.items():
            if qs:
                acc = qs[0].copy()
                for k, q in enumerate(qs[1:], start=2):
                    if acc.dot(q) < 0.0:
                        q = -q
                    acc = acc.slerp(q, 1.0 / k)        # running quaternion mean
                clav_mean[t] = acc

    n = 0
    for frame in range(int(frame_start), int(frame_end) + 1):
        one_frame(frame, True)

        if cog is not None and "hips" in pairs:
            hips_now = src_head(pairs["hips"])
            if hips_start is None:
                hips_start = hips_now.copy()
            travel = (hips_now - hips_start) * scale
            cog.location = rest["COG"].inverted() @ travel
            cog.keyframe_insert("location", frame=frame)
        n += 1
    return n


# ── Clip library scanning ────────────────────────────────────

def _scan_clip_library(library_path):
    """Scan a directory for animation clip files.

    Supports .fbx, .bvh, and .blend files.

    Args:
        library_path: Filesystem path to the clip library directory.

    Returns:
        List of dicts with keys ``name``, ``filepath``, ``extension``.
    """
    clips = []

    if not library_path or not os.path.isdir(library_path):
        return clips

    for filename in sorted(os.listdir(library_path)):
        stem, extension = os.path.splitext(filename)
        extension_lower = extension.lower()
        if extension_lower in SUPPORTED_CLIP_EXTENSIONS:
            clips.append({
                'name': stem,
                'filepath': os.path.join(library_path, filename),
                'extension': extension_lower,
            })

    return clips


# ── Operators ─────────────────────────────────────────────────

class BF_OT_RetargetBrowseClips(bpy.types.Operator):
    """Scan the clip library folder for animation files."""

    bl_idname = "boneforge.retarget_browse_clips"
    bl_label = "Browse Clips"
    bl_options = {'REGISTER'}

    def execute(self, context):
        """Scan the configured clip library folder and populate the clip list."""
        prefs = addon_prefs(context)
        library_path = getattr(prefs, 'clip_library_path', "")

        if not library_path:
            self.report({'WARNING'},
                        "No clip library folder set — "
                        "configure in addon preferences")
            return {'CANCELLED'}

        settings = context.scene.boneforge_retarget_settings
        settings.clips.clear()

        found_clips = _scan_clip_library(library_path)
        for clip_data in found_clips:
            clip = settings.clips.add()
            clip.clip_name = clip_data['name']
            clip.filepath = clip_data['filepath']

        self.report({'INFO'}, f"Found {len(found_clips)} clips")
        if context.area is not None:
            context.area.tag_redraw()
        return {'FINISHED'}


class BF_OT_RetargetImportClip(bpy.types.Operator):
    """Import an animation clip file (FBX, BVH, or .blend)."""

    bl_idname = "boneforge.retarget_import_clip"
    bl_label = "Import Clip"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(
        subtype='FILE_PATH',
    )

    filter_glob: StringProperty(
        default="*.fbx;*.bvh;*.blend",
        options={'HIDDEN'},
    )

    def invoke(self, context, event):
        """Open the file browser for clip selection."""
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        """Import the selected clip file and add it to the clip list."""
        if not self.filepath:
            self.report({'WARNING'}, "No file selected")
            return {'CANCELLED'}

        _, extension = os.path.splitext(self.filepath)
        extension = extension.lower()

        try:
            if extension == '.fbx':
                bpy.ops.import_scene.fbx(filepath=self.filepath)
            elif extension == '.bvh':
                bpy.ops.import_anim.bvh(filepath=self.filepath)
            elif extension == '.blend':
                with bpy.data.libraries.load(self.filepath) as (
                    data_from, data_to,
                ):
                    data_to.actions = data_from.actions
            else:
                self.report({'WARNING'}, f"Unsupported format: {extension}")
                return {'CANCELLED'}
        except RuntimeError as import_error:
            self.report({'ERROR'}, f"Import failed: {import_error}")
            return {'CANCELLED'}

        # Add to clip list
        settings = context.scene.boneforge_retarget_settings
        clip = settings.clips.add()
        clip_basename = os.path.basename(self.filepath)
        clip.clip_name = os.path.splitext(clip_basename)[0]
        clip.filepath = self.filepath

        # Associate with the most recently added action
        if bpy.data.actions:
            clip.action_name = bpy.data.actions[-1].name

        self.report({'INFO'}, f"Imported: {clip.clip_name}")
        if context.area is not None:
            context.area.tag_redraw()
        return {'FINISHED'}


class BF_OT_RetargetSelectClip(bpy.types.Operator):
    """Select a clip from the clip list by index."""

    bl_idname = "boneforge.retarget_select_clip"
    bl_label = "Select Clip"
    bl_options = {'REGISTER'}

    clip_index: IntProperty(
        name="Clip Index",
        description="Index of the clip to select",
        default=0,
    )

    def execute(self, context):
        """Set the active clip index to the specified clip."""
        settings = context.scene.boneforge_retarget_settings
        if not (0 <= self.clip_index < len(settings.clips)):
            self.report({'WARNING'}, "Clip index out of range")
            return {'CANCELLED'}
        settings.active_clip_index = self.clip_index
        if context.area:
            context.area.tag_redraw()
        return {'FINISHED'}


class BF_OT_RetargetAutoMatch(bpy.types.Operator):
    """Auto-match source bones to target armature."""

    bl_idname = "boneforge.retarget_auto_match"
    bl_label = "Auto-Match Bones"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        """Require an active armature and a selected clip."""
        armature_obj = active_armature(context)
        if armature_obj is None:
            return False
        settings = context.scene.boneforge_retarget_settings
        clip_index = settings.active_clip_index
        return 0 <= clip_index < len(settings.clips)

    def execute(self, context):
        """Run the bone matching cascade and populate session mappings."""
        armature_obj = active_armature(context)
        settings = context.scene.boneforge_retarget_settings
        session = context.scene.boneforge_autorig_session

        clip_index = settings.active_clip_index
        if not (0 <= clip_index < len(settings.clips)):
            self.report({'WARNING'}, "No clip selected")
            return {'CANCELLED'}
        clip = settings.clips[clip_index]
        action = bpy.data.actions.get(clip.action_name)

        if action is None:
            action = _find_action_with_bone_animation()
            if action is not None:
                clip.action_name = action.name

        if action is None:
            self.report({'WARNING'},
                        "No bone animation found in this file. "
                        "Ensure the file contains skeletal animation data.")
            return {'CANCELLED'}

        mappings = auto_match_bones(action, armature_obj)

        # Populate session retarget mappings
        session.retarget_mappings.clear()
        matched_count = 0
        for entry in mappings:
            mapping = session.retarget_mappings.add()
            mapping.source_name = entry['source']
            mapping.target_name = entry['target']
            mapping.match_type = entry['type']
            mapping.is_matched = entry['matched']
            if entry['matched']:
                matched_count += 1

        total_count = len(mappings)
        if matched_count == 0:
            self.report({'WARNING'},
                        "No automatic bone matches found. "
                        "Please map bones manually using the table below.")
        else:
            # SIG-7 fix: report match type breakdown for quality assessment
            match_type_counts = {}
            for entry in mappings:
                if entry['matched']:
                    mtype = entry['type']
                    match_type_counts[mtype] = match_type_counts.get(mtype, 0) + 1
            type_detail = ", ".join(
                f"{count} {mtype}" for mtype, count in sorted(match_type_counts.items())
            )
            self.report({'INFO'},
                        f"Matched {matched_count}/{total_count} bones "
                        f"({type_detail})")

        # CRIT-2 fix: guard context.area before tag_redraw
        if context.area is not None:
            context.area.tag_redraw()
        return {'FINISHED'}


class BF_OT_RetargetPreview(bpy.types.Operator):
    """Preview the retargeted animation with a temporary NLA strip."""

    bl_idname = "boneforge.retarget_preview"
    bl_label = "Preview Clip"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        """Require an active armature and no preview already running."""
        armature_obj = active_armature(context)
        if armature_obj is None:
            return False
        settings = context.scene.boneforge_retarget_settings
        return not settings.preview_active

    def execute(self, context):
        """Create a temporary retargeted action and start NLA preview."""
        settings = context.scene.boneforge_retarget_settings
        session = context.scene.boneforge_autorig_session
        armature_obj = active_armature(context)

        if not session.retarget_mappings:
            self.report({'WARNING'}, "Run auto-match first")
            return {'CANCELLED'}

        clip_index = settings.active_clip_index
        if not (0 <= clip_index < len(settings.clips)):
            self.report({'WARNING'}, "No clip selected")
            return {'CANCELLED'}

        clip = settings.clips[clip_index]
        source_action = bpy.data.actions.get(clip.action_name)
        if source_action is None:
            self.report({'WARNING'}, "Clip action not found")
            return {'CANCELLED'}

        # Compute rest pose offset
        rest_offset, confidence, detected_pose = _compute_rest_pose_offset(
            source_action, armature_obj, settings.rest_pose_mode,
        )

        mappings = _build_mapping_list_from_session(session)

        # Direction-matched retarget when the clip's skeleton is in the scene
        # (FBX/BVH imports keep it): exact on any rest pose. An actions-only
        # clip (.blend) falls back to the older rest-pose method.
        source_arm = _source_armature_for_action(source_action)
        if source_arm is not None:
            retargeted_action = retarget_to_new_action(
                source_arm, armature_obj, mappings,
                source_action.name + "_retarget")
        else:
            self.report({'WARNING'}, "Clip has no skeleton in the scene; "
                        "using the older rest-pose retarget (not available on "
                        "Blender 5+: import the clip as FBX or BVH instead)")
            retargeted_action = retarget_action(
                source_action, armature_obj, mappings, rest_offset,
            )
        if retargeted_action is None:
            self.report({'WARNING'}, "Retargeting produced no valid FCurves")
            return {'CANCELLED'}

        _suppress_onion_skin()

        # Create temp NLA strip for preview
        if armature_obj.animation_data is None:
            armature_obj.animation_data_create()

        track = armature_obj.animation_data.nla_tracks.new()
        track.name = _PREVIEW_TRACK_NAME
        track.strips.new(
            retargeted_action.name, 0, retargeted_action,
        )

        settings.preview_active = True

        # Start playback from the action's first frame
        first_frame = int(source_action.frame_range[0])
        context.scene.frame_set(first_frame)
        bpy.ops.screen.animation_play()

        self.report({'INFO'}, "Preview playing — click Stop to end")
        if context.area is not None:
            context.area.tag_redraw()
        return {'FINISHED'}


class BF_OT_RetargetStopPreview(bpy.types.Operator):
    """Stop the retarget preview and clean up temporary data."""

    bl_idname = "boneforge.retarget_stop_preview"
    bl_label = "Stop Preview"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        """Only available when a preview is active."""
        settings = context.scene.boneforge_retarget_settings
        return settings.preview_active

    def execute(self, context):
        """Stop playback, remove temporary NLA track, and restore state."""
        settings = context.scene.boneforge_retarget_settings
        armature_obj = active_armature(context)

        bpy.ops.screen.animation_cancel(restore_frame=True)
        _remove_preview_nla_track(armature_obj)
        _restore_onion_skin()

        settings.preview_active = False
        if context.area is not None:
            context.area.tag_redraw()

        self.report({'INFO'}, "Preview stopped")
        return {'FINISHED'}


class BF_OT_RetargetApply(bpy.types.Operator):
    """Apply the retargeted animation as a new action."""

    bl_idname = "boneforge.retarget_apply"
    bl_label = "Apply Retarget"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        """Require an active armature with mappings and no preview running."""
        armature_obj = active_armature(context)
        if armature_obj is None:
            return False
        session = context.scene.boneforge_autorig_session
        settings = context.scene.boneforge_retarget_settings
        has_mappings = len(session.retarget_mappings) > 0
        return has_mappings and not settings.preview_active

    def execute(self, context):
        """Create and assign the retargeted action to the armature."""
        armature_obj = active_armature(context)
        session = context.scene.boneforge_autorig_session
        settings = context.scene.boneforge_retarget_settings

        clip_index = settings.active_clip_index
        if not (0 <= clip_index < len(settings.clips)):
            self.report({'ERROR'}, "No clip selected")
            return {'CANCELLED'}

        clip = settings.clips[clip_index]
        source_action = bpy.data.actions.get(clip.action_name)
        if source_action is None:
            self.report({'ERROR'}, "Source action not found")
            return {'CANCELLED'}

        # Compute rest pose offset
        rest_offset, confidence, detected_pose = _compute_rest_pose_offset(
            source_action, armature_obj, settings.rest_pose_mode,
        )
        if confidence < _CONFIDENCE_THRESHOLD and settings.rest_pose_mode == 'AUTO':
            self.report({'WARNING'},
                        "Rest pose could not be reliably detected. "
                        "Use the manual offset if the animation looks wrong.")

        mappings = _build_mapping_list_from_session(session)

        # Direction-matched retarget when the clip's skeleton is in the scene
        # (FBX/BVH imports keep it): exact on any rest pose. An actions-only
        # clip (.blend) falls back to the older rest-pose method.
        source_arm = _source_armature_for_action(source_action)
        if source_arm is not None:
            retargeted_action = retarget_to_new_action(
                source_arm, armature_obj, mappings,
                source_action.name + "_retarget")
        else:
            self.report({'WARNING'}, "Clip has no skeleton in the scene; "
                        "using the older rest-pose retarget (not available on "
                        "Blender 5+: import the clip as FBX or BVH instead)")
            retargeted_action = retarget_action(
                source_action, armature_obj, mappings, rest_offset,
            )
        if retargeted_action is None:
            self.report({'ERROR'}, "Retargeting produced no valid data")
            return {'CANCELLED'}

        # Assign to armature
        if armature_obj.animation_data is None:
            armature_obj.animation_data_create()
        armature_obj.animation_data.action = retargeted_action

        self.report({'INFO'},
                    f"Applied retargeted animation: {retargeted_action.name}")
        if context.area is not None:
            context.area.tag_redraw()
        return {'FINISHED'}


# ── Panels ────────────────────────────────────────────────────

class BF_PT_RetargetPanel(bpy.types.Panel):
    """Retargeting clip browser and controls."""

    bl_idname = "BONEFORGE_PT_retarget"
    bl_label = " "
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BoneCraft"
    bl_order = 55

    def draw_header(self, context):
        self.layout.label(text=T("Retarget"))

    def draw(self, context):
        """Draw the clip browser, controls, and active clip options."""
        layout = self.layout
        settings = context.scene.boneforge_retarget_settings

        # Show a hint when no armature is active — operators need one
        if active_armature(context) is None:
            layout.label(
                text=T("Select an armature to enable retargeting"),
                icon='INFO',
            )
            layout.separator()

        # Import / browse
        row = layout.row(align=True)
        row.operator("boneforge.retarget_import_clip",
                     text=T("Import Clip"), icon='IMPORT')
        row.operator("boneforge.retarget_browse_clips",
                     text=T("Browse Library"), icon='FILE_FOLDER')

        # Filter
        if len(settings.clips) > 0:
            layout.prop(settings, "filter_text", text="", icon='VIEWZOOM')

        # Clip list
        if len(settings.clips) > 0:
            self._draw_clip_list(layout, settings)
        else:
            layout.label(text=T("No clips loaded"), icon='INFO')
            layout.label(text=T("Import a clip or set a library folder"))

    def _draw_clip_list(self, layout, settings):
        """Draw the scrollable list of clips with selection."""
        box = layout.box()

        for clip_index, clip in enumerate(settings.clips):
            # Apply text filter
            if settings.filter_text:
                filter_lower = settings.filter_text.lower()
                if filter_lower not in clip.clip_name.lower():
                    continue

            row = box.row(align=True)
            is_active = clip_index == settings.active_clip_index
            icon = 'PLAY' if is_active else 'ACTION'

            # Select clip on click
            select_op = row.operator(
                "boneforge.retarget_select_clip",
                text=clip.clip_name, icon=icon,
                emboss=is_active,
            )
            select_op.clip_index = clip_index

            if not is_active:
                auto_match_op = row.operator(
                    "boneforge.retarget_auto_match",
                    text="", icon='AUTO',
                )
            else:
                row.operator(
                    "boneforge.retarget_auto_match",
                    text="", icon='AUTO',
                )

        # Active clip controls
        clip_index = settings.active_clip_index
        if 0 <= clip_index < len(settings.clips):
            layout.separator()
            layout.label(text=T("Rest Pose Correction:"))
            layout.prop(settings, "rest_pose_mode", text="")

            if settings.rest_pose_mode == 'CUSTOM':
                layout.prop(settings, "manual_offset_angle")

            layout.separator()
            row = layout.row(align=True)
            if settings.preview_active:
                row.operator("boneforge.retarget_stop_preview",
                             text=T("Stop Preview"), icon='PAUSE')
            else:
                row.operator("boneforge.retarget_preview",
                             text=T("Preview"), icon='PLAY')
                row.operator("boneforge.retarget_apply",
                             text=T("Apply"), icon='ACTION')


class BF_PT_RetargetMappingSubPanel(bpy.types.Panel):
    """Bone mapping table sub-panel."""

    bl_idname = "BONEFORGE_PT_retarget_mapping"
    bl_label = " "
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BoneCraft"
    bl_parent_id = "BF_PT_sb_retarget"  # v3.3.2: re-parented from BONEFORGE_PT_retarget to hub delegate
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text=T("Bone Mapping"))

    @classmethod
    def poll(cls, context):
        """Only show when retarget mappings exist."""
        session = context.scene.boneforge_autorig_session
        return len(session.retarget_mappings) > 0

    def draw(self, context):
        """Draw the bone mapping table with match status."""
        layout = self.layout
        session = context.scene.boneforge_autorig_session

        matched_count = sum(
            1 for mapping in session.retarget_mappings if mapping.is_matched
        )
        total_count = len(session.retarget_mappings)
        layout.label(text=f"Matched: {matched_count}/{total_count}")

        # Mapping table header
        box = layout.box()
        header_row = box.row()
        header_row.label(text=T("Source"))
        header_row.label(text=T("Target"))
        header_row.label(text=T("Type"))

        # Mapping rows
        for mapping in session.retarget_mappings:
            row = box.row(align=True)
            row.label(text=mapping.source_name)

            if mapping.is_matched:
                row.label(text=mapping.target_name)
                row.label(text=mapping.match_type, icon='CHECKMARK')
            else:
                row.prop(mapping, "target_name", text="")
                row.label(text="", icon='ERROR')


def _preset_items(self, context):
    from boneforge.autorig import maps
    return [(n, n, "") for n in maps.available_maps()]


class BF_OT_RetargetPreset(bpy.types.Operator):
    """Retarget a selected source armature's action onto the active rig using
    a source-skeleton mapping preset (with namespace + rest correction)."""

    bl_idname = "boneforge.retarget_preset"
    bl_label = "Retarget From Preset"
    bl_options = {'REGISTER', 'UNDO'}

    preset: EnumProperty(description='The skeleton the animation comes from', name="Source Skeleton", items=_preset_items)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        arms = [o for o in context.selected_objects if o.type == 'ARMATURE']
        return obj is not None and obj.type == 'ARMATURE' and len(arms) >= 2

    def execute(self, context):
        from boneforge import bfa_guard
        bfa_guard.require_bforartists("retarget")
        from boneforge.autorig import maps
        from boneforge.autorig import retarget_core as rc

        target = context.active_object
        source = next((o for o in context.selected_objects
                       if o.type == 'ARMATURE' and o is not target), None)
        if source is None:
            self.report({'ERROR'}, "Select a source and a target armature")
            return {'CANCELLED'}

        preset = maps.load_map(self.preset)
        result = rc.build_mappings(
            preset,
            [b.name for b in source.data.bones],
            {b.name for b in target.data.bones},
        )
        name_map = rc.matched_name_map(result)
        if not name_map:
            self.report({'WARNING'},
                        "No bones matched (missing: %s)"
                        % ", ".join(result["missing_source"][:4]))
            return {'CANCELLED'}

        scene = context.scene
        target.animation_data_create()
        target.animation_data.action = bpy.data.actions.new(
            "%s_retargeted" % source.name)
        n = retarget_clip_corrected(source, target, name_map,
                                    scene.frame_start, scene.frame_end)
        miss = len(result["missing_source"])
        self.report(
            {'INFO'},
            "Retargeted %d bones over %d frames (%d source bone(s) unmatched)"
            % (len(name_map), n, miss))
        return {'FINISHED'}


# ── Registration ──────────────────────────────────────────────

classes = (
    BF_ClipEntry,
    BF_RetargetSettings,
    BF_OT_RetargetBrowseClips,
    BF_OT_RetargetSelectClip,
    BF_OT_RetargetPreview,
    BF_OT_RetargetStopPreview,
    BF_OT_RetargetApply,
    BF_OT_RetargetImportClip,
    BF_OT_RetargetAutoMatch,
    BF_OT_RetargetPreset,
    BF_PT_RetargetMappingSubPanel,
)


def register():
    """Register retarget PropertyGroups, operators, and panels."""
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.boneforge_retarget_settings = PointerProperty(
        type=BF_RetargetSettings,
    )


def unregister():
    """Unregister retarget PropertyGroups, operators, and panels."""
    if hasattr(bpy.types.Scene, 'boneforge_retarget_settings'):
        del bpy.types.Scene.boneforge_retarget_settings

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
