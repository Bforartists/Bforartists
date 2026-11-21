"""BoneCraft Phase 3 — Body Armature Generator.

Constructs a body armature from the seven body markers and eight derived
joints stored in the AutoRigSession.  Bones follow Rigify naming
conventions so Phase 2 rigify_enhance recognises the rig automatically.

The generation uses a staging collection for atomic undo: everything is
built hidden, then revealed on success or deleted entirely on failure.
"""

import bpy
from dataclasses import dataclass, field
from mathutils import Vector

from boneforge.autorig.constants import (
    BODY_IK_COLLECTION,
    BODY_FK_COLLECTION,
    BODY_DEFORM_COLLECTION,
    REQUIRED_BODY_MARKERS,
)
from boneforge.autorig.session import (
    get_body_marker,
    log_scene_change,
)

import logging

logger = logging.getLogger(__name__)

# Non-deforming IK target controls that belong to the IK collection.
# Deforming limb bones remain in the FK/Deform collections.
BODY_IK_BONE_NAMES = {'hand_ik.L', 'hand_ik.R', 'foot_ik.L', 'foot_ik.R'}


# ── Result dataclass ──────────────────────────────────────────

@dataclass
class BodyRigResult:
    """Result of body rig generation."""

    success: bool = False
    message: str = ""
    armature_object_name: str = ""
    bone_count: int = 0
    collection_names: list = field(default_factory=list)


# ── Internal helpers ──────────────────────────────────────────

def _create_bone_chain(edit_bones, chain_name, positions, parent_bone=None):
    """Create a chain of connected bones from a list of positions.

    Each bone spans from ``positions[i]`` to ``positions[i+1]``.
    The first bone in the chain is parented to *parent_bone* if given.

    Args:
        edit_bones: ``armature.edit_bones`` in edit mode.
        chain_name: Base name for the chain (bones get ``.001`` suffixes).
        positions: List of ``Vector`` head/tail positions (minimum 2).
        parent_bone: Optional ``EditBone`` to parent the first bone to.

    Returns:
        List of created ``EditBone`` objects.
    """
    created = []
    segment_count = len(positions) - 1

    for segment_index in range(segment_count):
        if segment_index == 0:
            bone_name = chain_name
        else:
            bone_name = f"{chain_name}.{segment_index:03d}"

        bone = edit_bones.new(bone_name)
        bone.head = positions[segment_index]
        bone.tail = positions[segment_index + 1]

        if segment_index == 0 and parent_bone is not None:
            bone.parent = parent_bone
            bone.use_connect = True
        elif created:
            bone.parent = created[-1]
            bone.use_connect = True

        created.append(bone)

    return created


def _create_body_bone_collections(armature_data, rig_mode='IK_FK'):
    """Create body bone collections based on the chosen IK/FK mode.

    Args:
        armature_data: The armature data block.
        rig_mode: One of ``'IK_FK'``, ``'IK_ONLY'``, ``'FK_ONLY'``.

    Returns:
        Dict mapping collection name to the ``BoneCollection`` object.
    """
    collections = {}
    if rig_mode in ('IK_FK', 'IK_ONLY'):
        collections[BODY_IK_COLLECTION] = armature_data.collections.new(BODY_IK_COLLECTION)
    if rig_mode in ('IK_FK', 'FK_ONLY'):
        collections[BODY_FK_COLLECTION] = armature_data.collections.new(BODY_FK_COLLECTION)
    collections[BODY_DEFORM_COLLECTION] = armature_data.collections.new(BODY_DEFORM_COLLECTION)
    return collections


def _apply_automatic_weights(context, mesh_obj, armature_obj):
    """Apply automatic weights from *armature_obj* to *mesh_obj*.

    Uses Blender's built-in "Armature Deform With Automatic Weights"
    operator.

    Returns:
        True if weighting succeeded, False otherwise.
    """
    bpy.ops.object.select_all(action='DESELECT')
    mesh_obj.select_set(True)
    armature_obj.select_set(True)
    context.view_layer.objects.active = armature_obj

    try:
        bpy.ops.object.parent_set(type='ARMATURE_AUTO')
        return True
    except RuntimeError as error:
        logger.warning(f"[BoneCraft] Automatic weight painting failed: {error}")
        return False


def _setup_ik_constraints(armature_obj, bone_map):
    """Add IK constraints to the appropriate limb bones.

    Args:
        armature_obj: Armature object that owns the pose bones.
        bone_map: Dict mapping logical bone name to actual bone name.
    """
    pose_bones = armature_obj.pose.bones

    # Each entry: (bone receiving IK, IK subtarget bone, chain length)
    ik_definitions = [
        ('forearm.L', 'hand_ik.L', 2),
        ('forearm.R', 'hand_ik.R', 2),
        ('shin.L', 'foot_ik.L', 2),
        ('shin.R', 'foot_ik.R', 2),
    ]

    for bone_name, target_name, chain_length in ik_definitions:
        actual_bone_name = bone_map.get(bone_name, bone_name)
        actual_target_name = bone_map.get(target_name, target_name)

        pose_bone = pose_bones.get(actual_bone_name)
        if pose_bone is None or pose_bones.get(actual_target_name) is None:
            continue

        constraint = pose_bone.constraints.new('IK')
        constraint.name = "BoneCraft IK"
        constraint.target = armature_obj
        constraint.chain_count = chain_length
        constraint.subtarget = actual_target_name


def _create_limb_chain(edit_bones, bone_names, positions, parent_bone):
    """Create a two-bone limb chain (upper + lower) with correct naming.

    Used for both arms and legs to avoid duplicating the same
    pattern four times.

    Args:
        edit_bones: Armature edit bones.
        bone_names: Tuple of (upper_name, lower_name) like ('upper_arm.L', 'forearm.L').
        positions: List of 3 Vectors: [proximal, mid_joint, distal].
        parent_bone: Parent EditBone for the first bone.

    Returns:
        Tuple of (upper_bone, lower_bone, bone_map_entries).
    """
    upper_name, lower_name = bone_names
    bone_map_entries = {}

    upper_bone = edit_bones.new(upper_name)
    upper_bone.head = positions[0]
    upper_bone.tail = positions[1]
    upper_bone.parent = parent_bone
    upper_bone.use_connect = False  # Limb roots are not connected to spine
    bone_map_entries[upper_name] = upper_bone.name

    lower_bone = edit_bones.new(lower_name)
    lower_bone.head = positions[1]
    lower_bone.tail = positions[2]
    lower_bone.parent = upper_bone
    lower_bone.use_connect = True
    bone_map_entries[lower_name] = lower_bone.name

    return upper_bone, lower_bone, bone_map_entries


def _create_terminal_bone(edit_bones, bone_name, head_position, direction, length_fraction, parent_bone):
    """Create a terminal bone (hand or foot) at the end of a limb.

    Args:
        edit_bones: Armature edit bones.
        bone_name: Name for the bone (e.g. 'hand.L').
        head_position: Vector for the bone head.
        direction: Normalized direction vector for the bone tail.
        length_fraction: How long the terminal bone should be
                         relative to the reference length.
        parent_bone: Parent EditBone.

    Returns:
        The created EditBone.
    """
    bone = edit_bones.new(bone_name)
    bone.head = head_position
    bone.tail = head_position + direction * length_fraction
    bone.parent = parent_bone
    bone.use_connect = True
    return bone


def _create_ik_target_bone(edit_bones, bone_name, head_position, tail_position):
    """Create a non-deforming IK target control bone.

    The target must not be connected inside the deform chain; otherwise the
    IK constraint points at a child that is moved by the same chain.
    """
    bone = edit_bones.new(bone_name)
    bone.head = head_position
    bone.tail = tail_position
    bone.use_deform = False
    bone.use_connect = False
    return bone


def _assign_bones_to_collections(edit_bones, collections):
    """Assign all bones to the appropriate bone collections.

    IK endpoint bones go to the IK collection (if it exists),
    everything else to FK (if it exists).  All bones are assigned
    to Deform regardless.
    """
    for bone in edit_bones:
        if bone.name in BODY_IK_BONE_NAMES:
            if BODY_IK_COLLECTION in collections:
                collections[BODY_IK_COLLECTION].assign(bone)
            elif BODY_FK_COLLECTION in collections:
                # FK-only mode: IK bones still need a collection
                collections[BODY_FK_COLLECTION].assign(bone)
        else:
            if BODY_FK_COLLECTION in collections:
                collections[BODY_FK_COLLECTION].assign(bone)
            elif BODY_IK_COLLECTION in collections:
                collections[BODY_IK_COLLECTION].assign(bone)

        if getattr(bone, 'use_deform', True):
            collections[BODY_DEFORM_COLLECTION].assign(bone)


def _build_body_picker_zones(session):
    """Build picker zone dicts for Phase 1 integration.

    Returns:
        List of dicts in the format expected by ``picker._dict_to_layout()``.
    """
    spine_count = max(2, int(getattr(session, 'spine_segments', 3) or 3))
    neck_count = max(1, int(getattr(session, 'neck_segments', 1) or 1))
    spine_bone_names = [
        'spine' if segment_index == 0 else f'spine.{segment_index:03d}'
        for segment_index in range(spine_count)
    ]
    neck_bone_names = [
        'neck' if segment_index == 0 else f'neck.{segment_index:03d}'
        for segment_index in range(neck_count)
    ]

    zone_definitions = [
        {"name": "Spine", "bones": spine_bone_names,
         "color": (0.4, 0.6, 0.8), "position": (0.5, 0.5)},
        {"name": "Left Arm", "bones": ["upper_arm.L", "forearm.L", "hand.L", "hand_ik.L"],
         "color": (0.8, 0.4, 0.4), "position": (0.2, 0.6)},
        {"name": "Right Arm", "bones": ["upper_arm.R", "forearm.R", "hand.R", "hand_ik.R"],
         "color": (0.8, 0.4, 0.4), "position": (0.8, 0.6)},
        {"name": "Left Leg", "bones": ["thigh.L", "shin.L", "foot.L", "foot_ik.L", "toe.L", "heel.L"],
         "color": (0.4, 0.8, 0.4), "position": (0.35, 0.2)},
        {"name": "Right Leg", "bones": ["thigh.R", "shin.R", "foot.R", "foot_ik.R", "toe.R", "heel.R"],
         "color": (0.4, 0.8, 0.4), "position": (0.65, 0.2)},
        {"name": "Head", "bones": neck_bone_names + ["head"],
         "color": (0.8, 0.7, 0.3), "position": (0.5, 0.85)},
    ]

    return [
        {
            'name': zone['name'],
            'bones': zone['bones'],
            'color': list(zone['color']),
            'position': list(zone['position']),
        }
        for zone in zone_definitions
    ]


# ── Region builders (composition helpers for generate_body_rig) ──

# Fraction of (wrist - elbow) length used for the terminal hand bone.
_HAND_LENGTH_FRACTION = 0.3
# Fraction of (toe - ankle) length used for the extended toe tip.
_TOE_TIP_LENGTH_FRACTION = 0.5


def _build_spine_neck_head(
    edit_bones,
    pelvis,
    neck_base,
    head_top,
    bone_map,
    spine_segment_count=3,
    neck_segment_count=1,
):
    """Build the spine chain plus the neck and head bones.

    Side effects: creates the requested spine and neck chains plus head on
    ``edit_bones`` and writes their generated names into ``bone_map``.

    Returns:
        List of spine ``EditBone`` objects (empty list if spine creation failed).
    """
    spine_segment_count = max(2, int(spine_segment_count or 3))
    neck_segment_count = max(1, int(neck_segment_count or 1))

    spine_positions = [
        pelvis.lerp(neck_base, segment_index / spine_segment_count)
        for segment_index in range(spine_segment_count + 1)
    ]
    spine_bones = _create_bone_chain(
        edit_bones,
        'spine',
        spine_positions,
    )
    for segment_index, spine_bone in enumerate(spine_bones):
        logical_name = 'spine' if segment_index == 0 else f'spine.{segment_index:03d}'
        bone_map[logical_name] = spine_bone.name

    head_base = neck_base.lerp(head_top, 0.5)
    neck_positions = [
        neck_base.lerp(head_base, segment_index / neck_segment_count)
        for segment_index in range(neck_segment_count + 1)
    ]

    neck_bones = _create_bone_chain(
        edit_bones,
        'neck',
        neck_positions,
        parent_bone=spine_bones[-1] if spine_bones else None,
    )
    for segment_index, neck_bone in enumerate(neck_bones):
        logical_name = 'neck' if segment_index == 0 else f'neck.{segment_index:03d}'
        bone_map[logical_name] = neck_bone.name

    head_bone = edit_bones.new('head')
    head_bone.head = head_base
    head_bone.tail = head_top
    if neck_bones:
        head_bone.parent = neck_bones[-1]
        head_bone.use_connect = True
    bone_map['head'] = head_bone.name

    return spine_bones


def _build_arm_with_hand(edit_bones, shoulder, elbow, wrist, side, parent_bone, bone_map):
    """Build upper_arm, forearm, and hand for one side (``'L'`` or ``'R'``)."""
    _, forearm_bone, arm_map = _create_limb_chain(
        edit_bones,
        bone_names=(f'upper_arm.{side}', f'forearm.{side}'),
        positions=[shoulder, elbow, wrist],
        parent_bone=parent_bone,
    )
    bone_map.update(arm_map)

    hand_direction = (wrist - elbow).normalized()
    hand_length = (wrist - elbow).length * _HAND_LENGTH_FRACTION
    hand_bone = _create_terminal_bone(
        edit_bones, f'hand.{side}', wrist,
        hand_direction, hand_length, forearm_bone,
    )
    bone_map[f'hand.{side}'] = hand_bone.name

    ik_target = _create_ik_target_bone(
        edit_bones,
        f'hand_ik.{side}',
        wrist,
        wrist + hand_direction * max(hand_length, 0.05),
    )
    bone_map[f'hand_ik.{side}'] = ik_target.name


def _build_leg_with_foot(edit_bones, hip, knee, ankle, toe, heel, side, parent_bone, bone_map):
    """Build thigh, shin, foot, toe, and heel for one side (``'L'`` or ``'R'``)."""
    _, shin_bone, leg_map = _create_limb_chain(
        edit_bones,
        bone_names=(f'thigh.{side}', f'shin.{side}'),
        positions=[hip, knee, ankle],
        parent_bone=parent_bone,
    )
    bone_map.update(leg_map)

    # Foot bone: ankle -> toe (uses derived or manually placed toe position)
    foot_bone = edit_bones.new(f'foot.{side}')
    foot_bone.head = ankle
    foot_bone.tail = toe
    foot_bone.parent = shin_bone
    foot_bone.use_connect = True
    bone_map[f'foot.{side}'] = foot_bone.name

    foot_ik = _create_ik_target_bone(
        edit_bones,
        f'foot_ik.{side}',
        ankle,
        toe,
    )
    bone_map[f'foot_ik.{side}'] = foot_ik.name

    # Toe bone: toe -> extended tip
    toe_direction = (toe - ankle).normalized()
    toe_tip = toe + toe_direction * (toe - ankle).length * _TOE_TIP_LENGTH_FRACTION
    toe_bone = edit_bones.new(f'toe.{side}')
    toe_bone.head = toe
    toe_bone.tail = toe_tip
    toe_bone.parent = foot_bone
    toe_bone.use_connect = True
    bone_map[f'toe.{side}'] = toe_bone.name

    # Heel bone: ankle -> heel (non-connected, used for IK foot roll)
    heel_bone = edit_bones.new(f'heel.{side}')
    heel_bone.head = ankle
    heel_bone.tail = heel
    heel_bone.parent = shin_bone
    heel_bone.use_connect = False
    bone_map[f'heel.{side}'] = heel_bone.name


# ── Main generation function ──────────────────────────────────

def generate_body_rig(context, session):
    """Generate a body armature from the session's marker and derived joint data.

    Creates an armature with Rigify-compatible bone names, organized into
    three bone collections (IK, FK, Deform).

    Side effects:
        Creates armature and bone-shape objects in the staging collection.
        Changes Blender's active object and mode during execution.

    Args:
        context: Blender context.
        session: ``BF_AutoRigSession`` PropertyGroup with confirmed markers.

    Returns:
        ``BodyRigResult`` with generation outcome.
    """
    mesh_obj = bpy.data.objects.get(session.mesh_object_name)
    if mesh_obj is None:
        return BodyRigResult(
            success=False,
            message=f"Mesh object '{session.mesh_object_name}' not found",
        )

    # Read marker positions — each get_body_marker() call can return None
    # if the session markers are incomplete, so guard explicitly.
    # Only the 7 core markers are strictly required.
    _required_markers = {name: None for name in REQUIRED_BODY_MARKERS}
    for marker_name in _required_markers:
        marker = get_body_marker(session, marker_name)
        if marker is None:
            return BodyRigResult(
                success=False,
                message=f"Body marker '{marker_name}' not found in session",
            )
        if not marker.confirmed:
            return BodyRigResult(
                success=False,
                message=f"Required body marker '{marker_name}' not confirmed",
            )
        _required_markers[marker_name] = Vector(marker.position)

    head_top = _required_markers['HEAD_TOP']
    neck_base = _required_markers['NECK_BASE']
    wrist_left = _required_markers['WRIST_LEFT']
    wrist_right = _required_markers['WRIST_RIGHT']
    ankle_left = _required_markers['ANKLE_LEFT']
    ankle_right = _required_markers['ANKLE_RIGHT']
    pelvis = _required_markers['PELVIS']

    # Read derived joints (includes manual overrides if user placed them)
    shoulder_left = Vector(session.derived_shoulder_left)
    shoulder_right = Vector(session.derived_shoulder_right)
    elbow_left = Vector(session.derived_elbow_left)
    elbow_right = Vector(session.derived_elbow_right)
    hip_left = Vector(session.derived_hip_left)
    hip_right = Vector(session.derived_hip_right)
    knee_left = Vector(session.derived_knee_left)
    knee_right = Vector(session.derived_knee_right)
    toe_left = Vector(session.derived_toe_left)
    toe_right = Vector(session.derived_toe_right)
    heel_left = Vector(session.derived_heel_left)
    heel_right = Vector(session.derived_heel_right)

    # Create the armature data and object
    armature_data = bpy.data.armatures.new("BoneForge_Body")
    armature_data.display_type = 'OCTAHEDRAL'
    armature_obj = bpy.data.objects.new("BoneForge_Body", armature_data)

    # Link directly to the scene's root collection so the armature
    # is guaranteed visible in the active view layer.  Do NOT link to
    # the staging collection here — it is excluded from all view layers
    # and can prevent parent_set / mode_set from finding the object.
    context.scene.collection.objects.link(armature_obj)
    # Force Blender to refresh the view layer's object list.
    context.view_layer.update()

    log_scene_change(session, 'objects_created', armature_obj.name)

    # Enter edit mode to create bones
    context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode='EDIT')
    edit_bones = armature_data.edit_bones

    bone_map = {}

    # ── Spine chain + neck + head ─────────────────────────────
    spine_bones = _build_spine_neck_head(
        edit_bones,
        pelvis,
        neck_base,
        head_top,
        bone_map,
        spine_segment_count=getattr(session, 'spine_segments', 3),
        neck_segment_count=getattr(session, 'neck_segments', 1),
    )
    spine_tip = spine_bones[-1] if spine_bones else None
    spine_root = spine_bones[0] if spine_bones else None

    # ── Arms (shoulder -> elbow -> wrist -> hand) ─────────────
    _build_arm_with_hand(
        edit_bones, shoulder_left, elbow_left, wrist_left,
        side='L', parent_bone=spine_tip, bone_map=bone_map,
    )
    _build_arm_with_hand(
        edit_bones, shoulder_right, elbow_right, wrist_right,
        side='R', parent_bone=spine_tip, bone_map=bone_map,
    )

    # ── Legs (hip -> knee -> ankle -> foot/toe/heel) ──────────
    _build_leg_with_foot(
        edit_bones, hip_left, knee_left, ankle_left,
        toe_left, heel_left,
        side='L', parent_bone=spine_root, bone_map=bone_map,
    )
    _build_leg_with_foot(
        edit_bones, hip_right, knee_right, ankle_right,
        toe_right, heel_right,
        side='R', parent_bone=spine_root, bone_map=bone_map,
    )

    bone_count = len(edit_bones)

    # ── Assign bones to collections ───────────────────────────
    rig_mode = getattr(session, 'rig_mode', 'IK_FK')
    collections = _create_body_bone_collections(armature_data, rig_mode)
    _assign_bones_to_collections(edit_bones, collections)

    # Exit edit mode
    bpy.ops.object.mode_set(mode='OBJECT')

    # ── Set up IK constraints in pose mode (skip for FK-only) ─
    if rig_mode in ('IK_FK', 'IK_ONLY'):
        bpy.ops.object.mode_set(mode='POSE')
        _setup_ik_constraints(armature_obj, bone_map)
        bpy.ops.object.mode_set(mode='OBJECT')

    # Store result on session
    session.generated_body_armature = armature_obj.name

    active_collections = list(collections.keys())
    mode_label = {'IK_FK': 'IK+FK', 'IK_ONLY': 'IK', 'FK_ONLY': 'FK'}
    return BodyRigResult(
        success=True,
        message=(f"Body rig generated: {bone_count} bones "
                 f"({mode_label.get(rig_mode, rig_mode)})"),
        armature_object_name=armature_obj.name,
        bone_count=bone_count,
        collection_names=active_collections,
    )


# ── Operator (called internally by WizardGenerate) ────────────

class BF_OT_GenerateBodyRig(bpy.types.Operator):
    """Generate body armature from placed markers (internal)"""

    bl_idname = "boneforge.autorig_generate_body"
    bl_label = "Generate Body Rig"
    bl_description = "Build the body bones from the markers placed in the Auto-Rig Wizard"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        """Require an active session with a mesh target."""
        session = context.scene.boneforge_autorig_session
        return session.is_active and session.mesh_object_name != ""

    def execute(self, context):
        """Run body rig generation from current session state."""
        session = context.scene.boneforge_autorig_session
        result = generate_body_rig(context, session)

        if result.success:
            self.report({'INFO'}, result.message)
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, result.message)
            return {'CANCELLED'}


# ── Registration ──────────────────────────────────────────────

classes = (BF_OT_GenerateBodyRig,)


def register():
    """Register body generation operator."""
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    """Unregister body generation operator."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
