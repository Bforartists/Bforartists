"""BoneCraft Phase 3 — Finger Armature Generator.

Constructs finger bones from placed finger markers and adds them to an
existing body armature. Unlike body_gen, finger_gen does NOT create a new
armature; it extends one created by body_gen with finger chains parented
to the hand bones.

The generation follows the same staging/collection pattern as body_gen
but operates entirely in edit mode on the provided armature.
"""

import bpy
from dataclasses import dataclass, field
from mathutils import Vector

from boneforge.autorig.constants import (
    FINGER_BONE_NAMES_5,
    FINGER_DEFORM_COLLECTION,
    FINGER_INTERMEDIATE_RATIO,
    FINGER_GROUP_BASE_RATIO,
    FINGER_MARKERS_BY_COUNT,
)
from boneforge.autorig.session import (
    get_finger_marker,
    is_position_placed,
    log_scene_change,
)


# ── Result dataclass ──────────────────────────────────────────

@dataclass
class FingerRigResult:
    """Result of finger rig generation."""

    success: bool = False
    message: str = ""
    bone_count: int = 0
    collection_names: list = field(default_factory=list)


# ── Internal helpers ──────────────────────────────────────────

def _mirror_position(position, center_x):
    """Mirror a 3D position across a plane perpendicular to the X-axis.

    Used to mirror left-hand finger markers to the right side when
    finger_symmetry is enabled.

    Args:
        position: Vector or tuple to mirror.
        center_x: X-coordinate of the mirror plane (typically the armature center).

    Returns:
        New Vector with mirrored coordinates.
    """
    mirrored = Vector(position)
    mirrored.x = 2.0 * center_x - mirrored.x
    return mirrored


def _get_marker_position(session, marker_name, side):
    """Retrieve a finger marker position from the session, applying side suffix.

    Args:
        session: AutoRigSession PropertyGroup.
        marker_name: Base marker name (e.g. 'FINGER_PALM').
        side: 'L' or 'R' to build the full marker name.

    Returns:
        Vector position if found and placed, None otherwise.
    """
    full_name = f"{marker_name}_{side}"

    # Use the session's index-based lookup (FINGER_MARKERS_ALL is the
    # source of truth for slot ordering). Name-based iteration does not
    # work because slot .name is never assigned.
    marker = get_finger_marker(session, full_name)
    if marker is None:
        return None
    if not is_position_placed(marker.position):
        return None
    return Vector(marker.position)


def _derive_finger_positions(markers_dict, finger_count, wrist_pos):
    """Derive all finger bone positions from marker positions.

    Computes intermediate joint positions based on marker placements
    and finger count. Each finger returns a list of positions for
    the bone chain.

    Args:
        markers_dict: Dict of marker_name → Vector position.
        finger_count: Number of fingers (0, 1, 2, 3, or 5).
        wrist_pos: Vector position of the wrist (hand parent).

    Returns:
        Dict mapping finger name (thumb, index, middle, ring, pinky)
        to a list of Vectors representing bone head/tail positions.
    """
    result = {}

    if finger_count == 0:
        return result

    if finger_count == 1:
        # Single "sock puppet" bone: palm to tip
        palm = markers_dict.get('FINGER_PALM')
        tip = markers_dict.get('FINGER_TIP')

        if palm is None or tip is None:
            return result

        knuckle = palm.lerp(tip, 0.5)
        result['index'] = [palm, knuckle, tip]
        return result

    if finger_count == 2:
        # Thumb (2 bones) + index group (2 bones)
        palm = markers_dict.get('FINGER_PALM')
        thumb_tip = markers_dict.get('FINGER_THUMB_TIP')
        thumb_base = markers_dict.get('FINGER_THUMB_BASE')
        index_tip = markers_dict.get('FINGER_INDEX_TIP')

        if any(v is None for v in [palm, thumb_tip, thumb_base, index_tip]):
            return result

        # Thumb: palm -> base -> tip (2 bones)
        result['thumb'] = [palm, thumb_base, thumb_tip]

        # Index group: palm -> base -> mid -> tip (2 bones)
        index_base = palm.lerp(index_tip, FINGER_GROUP_BASE_RATIO)
        index_mid = index_base.lerp(index_tip, FINGER_INTERMEDIATE_RATIO)
        result['index'] = [palm, index_base, index_mid, index_tip]

        return result

    if finger_count == 3:
        # Thumb (2 bones) + index (2 bones) + middle group (2 bones)
        palm = markers_dict.get('FINGER_PALM')
        thumb_tip = markers_dict.get('FINGER_THUMB_TIP')
        thumb_base = markers_dict.get('FINGER_THUMB_BASE')
        index_tip = markers_dict.get('FINGER_INDEX_TIP')
        index_base = markers_dict.get('FINGER_INDEX_BASE')
        pinky_tip = markers_dict.get('FINGER_PINKY_TIP')

        if any(v is None for v in [palm, thumb_tip, thumb_base, index_tip,
                                   index_base, pinky_tip]):
            return result

        # Thumb: palm -> base -> tip
        result['thumb'] = [palm, thumb_base, thumb_tip]

        # Index: palm -> base -> mid -> tip
        index_mid = index_base.lerp(index_tip, FINGER_INTERMEDIATE_RATIO)
        result['index'] = [palm, index_base, index_mid, index_tip]

        # Middle/remaining group: palm -> group_base -> mid -> group_tip
        # Base position weighted toward pinky (0.6 along index->pinky)
        group_base = index_base.lerp(pinky_tip, 0.6)
        group_tip = pinky_tip
        group_mid = group_base.lerp(group_tip, FINGER_INTERMEDIATE_RATIO)
        result['middle'] = [palm, group_base, group_mid, group_tip]

        return result

    if finger_count == 5:
        # All five fingers: each finger gets its own base+tip marker pair
        # so the user places every knuckle individually.
        palm = markers_dict.get('FINGER_PALM')
        thumb_tip = markers_dict.get('FINGER_THUMB_TIP')
        thumb_base = markers_dict.get('FINGER_THUMB_BASE')
        index_tip = markers_dict.get('FINGER_INDEX_TIP')
        index_base = markers_dict.get('FINGER_INDEX_BASE')
        middle_tip = markers_dict.get('FINGER_MIDDLE_TIP')
        middle_base = markers_dict.get('FINGER_MIDDLE_BASE')
        ring_tip = markers_dict.get('FINGER_RING_TIP')
        ring_base = markers_dict.get('FINGER_RING_BASE')
        pinky_tip = markers_dict.get('FINGER_PINKY_TIP')
        pinky_base = markers_dict.get('FINGER_PINKY_BASE')

        required = [palm, thumb_tip, thumb_base, index_tip, index_base,
                    middle_tip, middle_base, ring_tip, ring_base,
                    pinky_tip, pinky_base]
        if any(v is None for v in required):
            return result

        # Thumb: palm -> base -> tip (2 bones)
        result['thumb'] = [palm, thumb_base, thumb_tip]

        # Each finger: palm -> base -> mid -> tip (3 bones)
        index_mid = index_base.lerp(index_tip, FINGER_INTERMEDIATE_RATIO)
        result['index'] = [palm, index_base, index_mid, index_tip]

        middle_mid = middle_base.lerp(middle_tip, FINGER_INTERMEDIATE_RATIO)
        result['middle'] = [palm, middle_base, middle_mid, middle_tip]

        ring_mid = ring_base.lerp(ring_tip, FINGER_INTERMEDIATE_RATIO)
        result['ring'] = [palm, ring_base, ring_mid, ring_tip]

        pinky_mid = pinky_base.lerp(pinky_tip, FINGER_INTERMEDIATE_RATIO)
        result['pinky'] = [palm, pinky_base, pinky_mid, pinky_tip]

        return result

    return result


def _create_finger_bones(edit_bones, finger_positions, parent_bone, side):
    """Create finger bones from position chains.

    For each finger in finger_positions, creates a chain of connected bones
    parented to the hand (parent_bone). Bone names follow Rigify convention.

    Args:
        edit_bones: ``armature.edit_bones`` in edit mode.
        finger_positions: Dict of finger_name → list of Vectors.
        parent_bone: The hand EditBone to parent all fingers to.
        side: 'L' or 'R' for bone naming.

    Returns:
        List of all created EditBone objects.
    """
    created = []

    for finger_name in ['thumb', 'index', 'middle', 'ring', 'pinky']:
        if finger_name not in finger_positions:
            continue

        positions = finger_positions[finger_name]
        if len(positions) < 2:
            continue

        # Look up bone names for this finger and side
        if finger_name not in FINGER_BONE_NAMES_5:
            continue

        bone_name_templates = FINGER_BONE_NAMES_5[finger_name]

        # Create bones for each segment in the chain
        segment_count = len(positions) - 1
        finger_bones = []

        for segment_idx in range(segment_count):
            # Format the bone name with the side
            template = bone_name_templates[segment_idx]
            bone_name = template.format(side=side)

            bone = edit_bones.new(bone_name)
            bone.head = positions[segment_idx]
            bone.tail = positions[segment_idx + 1]

            # Parent the first bone to the hand
            if segment_idx == 0:
                bone.parent = parent_bone
                bone.use_connect = False
            else:
                # Connect subsequent bones in the chain
                bone.parent = finger_bones[-1]
                bone.use_connect = True

            finger_bones.append(bone)
            created.append(bone)

    return created


def _assign_finger_bones_to_collection(edit_bones, collection):
    """Assign all finger bones to the Finger Deform collection.

    Args:
        edit_bones: All bones in the armature.
        collection: The Finger Deform BoneCollection object.
    """
    # Check if a bone is a finger bone by looking for known prefixes
    finger_prefixes = (
        'thumb',
        'f_index',
        'f_middle',
        'f_ring',
        'f_pinky',
    )

    for bone in edit_bones:
        if any(bone.name.startswith(prefix) for prefix in finger_prefixes):
            collection.assign(bone)


def _get_finger_bone_names(finger_count, side):
    """Return all finger bone names for the given count and side.

    Used by picker zone building.

    Args:
        finger_count: Number of fingers (0, 1, 2, 3, or 5).
        side: 'L' or 'R'.

    Returns:
        List of bone name strings.
    """
    names = []

    if finger_count == 0:
        return names

    if finger_count == 1:
        # Single index group
        for template in FINGER_BONE_NAMES_5['index']:
            names.append(template.format(side=side))

    elif finger_count == 2:
        # Thumb + index
        for template in FINGER_BONE_NAMES_5['thumb']:
            names.append(template.format(side=side))
        for template in FINGER_BONE_NAMES_5['index']:
            names.append(template.format(side=side))

    elif finger_count == 3:
        # Thumb + index + middle
        for template in FINGER_BONE_NAMES_5['thumb']:
            names.append(template.format(side=side))
        for template in FINGER_BONE_NAMES_5['index']:
            names.append(template.format(side=side))
        for template in FINGER_BONE_NAMES_5['middle']:
            names.append(template.format(side=side))

    elif finger_count == 5:
        # All five fingers
        for finger_name in ['thumb', 'index', 'middle', 'ring', 'pinky']:
            for template in FINGER_BONE_NAMES_5[finger_name]:
                names.append(template.format(side=side))

    return names


def _build_finger_picker_zones(session):
    """Build picker zone dicts for Phase 1 integration.

    Returns:
        List of dicts in the format expected by ``picker._dict_to_layout()``.
    """
    zones = []

    if session.finger_count > 0:
        zones.append({
            'name': "Left Fingers",
            'bones': _get_finger_bone_names(session.finger_count, 'L'),
            'color': [0.9, 0.5, 0.4],
            'position': [0.12, 0.55],
        })
        zones.append({
            'name': "Right Fingers",
            'bones': _get_finger_bone_names(session.finger_count, 'R'),
            'color': [0.9, 0.5, 0.4],
            'position': [0.88, 0.55],
        })

    return zones


# ── Main generation function ──────────────────────────────────

def generate_finger_rig(context, session, armature_obj, hand_bones):
    """Generate finger bones and add them to an existing armature.

    Unlike generate_body_rig, this function receives an existing armature
    and hand bone references, then adds finger chains to it. The function
    operates entirely in edit mode and does not create a new armature.

    Args:
        context: Blender context.
        session: ``BF_AutoRigSession`` PropertyGroup with finger markers.
        armature_obj: The existing armature object to extend.
        hand_bones: Dict mapping hand logical names ('hand.L', 'hand.R')
                   to actual bone names. Typically {'hand.L': 'hand.L', 'hand.R': 'hand.R'}.

    Returns:
        ``FingerRigResult`` with generation outcome.
    """
    # Early exit if no fingers requested
    if session.finger_count == 0:
        return FingerRigResult(
            success=True,
            message="No fingers generated (finger_count=0)",
            bone_count=0,
            collection_names=[],
        )

    # Verify armature exists
    if armature_obj is None or armature_obj.type != 'ARMATURE':
        return FingerRigResult(
            success=False,
            message="Invalid or missing armature object",
        )

    armature_data = armature_obj.data

    # Verify hand bones exist in the armature
    hand_bone_names = {}
    for logical_name, actual_name in hand_bones.items():
        if actual_name not in armature_data.bones:
            return FingerRigResult(
                success=False,
                message=f"Hand bone '{actual_name}' not found in armature",
            )
        hand_bone_names[logical_name] = actual_name

    # Determine mirror center (armature center X)
    center_x = armature_obj.location.x

    # Enter edit mode
    context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode='EDIT')
    edit_bones = armature_data.edit_bones

    all_created_bones = []
    bone_count = 0

    try:
        # Process left and right hands
        for side, logical_hand_name in [('L', 'hand.L'), ('R', 'hand.R')]:
            actual_hand_name = hand_bone_names.get(logical_hand_name)
            if actual_hand_name is None:
                continue

            hand_bone = edit_bones.get(actual_hand_name)
            if hand_bone is None:
                continue

            # Collect marker positions for this side
            markers_dict = {}

            # Derive marker names from the authoritative marker set for this
            # finger count (single source of truth: FINGER_MARKERS_BY_COUNT).
            # Strip the trailing "_L" side suffix — the side loop adds it back.
            marker_names = [
                name[:-2] for name in
                FINGER_MARKERS_BY_COUNT.get(session.finger_count, ())
            ]

            # Load marker positions
            for marker_name in marker_names:
                pos = _get_marker_position(session, marker_name, side)
                if pos is not None:
                    markers_dict[marker_name] = pos
                else:
                    # If this is the right side and symmetry is on, mirror left markers
                    if side == 'R' and session.finger_symmetry:
                        left_pos = _get_marker_position(session, marker_name, 'L')
                        if left_pos is not None:
                            markers_dict[marker_name] = _mirror_position(left_pos, center_x)

            # Verify we have at least the required markers
            if 'FINGER_PALM' not in markers_dict:
                continue

            # Derive finger bone positions
            finger_positions = _derive_finger_positions(
                markers_dict,
                session.finger_count,
                hand_bone.head
            )

            if not finger_positions:
                continue

            # Create the finger bones
            created = _create_finger_bones(
                edit_bones,
                finger_positions,
                hand_bone,
                side
            )

            all_created_bones.extend(created)

        bone_count = len(all_created_bones)

        # Create or get the Finger Deform collection
        finger_collection = armature_data.collections.get(FINGER_DEFORM_COLLECTION)
        if finger_collection is None:
            finger_collection = armature_data.collections.new(FINGER_DEFORM_COLLECTION)

        # Assign all created bones to the collection
        _assign_finger_bones_to_collection(edit_bones, finger_collection)

        # Exit edit mode
        bpy.ops.object.mode_set(mode='OBJECT')

        # Store result on session
        session.generated_finger_count = session.finger_count

        log_scene_change(session, 'finger_bones_created', bone_count)

        return FingerRigResult(
            success=True,
            message=f"Finger rig generated: {bone_count} bones",
            bone_count=bone_count,
            collection_names=[FINGER_DEFORM_COLLECTION],
        )

    except RuntimeError as error:
        # Exit edit mode on error
        bpy.ops.object.mode_set(mode='OBJECT')
        return FingerRigResult(
            success=False,
            message=f"Finger rig generation failed: {error}",
        )


# ── Operator (called internally by WizardGenerate) ────────────

class BF_OT_GenerateFingerRig(bpy.types.Operator):
    """Generate finger bones and add to body armature (internal)"""

    bl_idname = "boneforge.autorig_generate_finger"
    bl_label = "Generate Finger Rig"
    bl_description = "Build the finger bones from the placed markers and add them to the body rig"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        """Require an active session with generated body rig."""
        session = context.scene.boneforge_autorig_session
        return (session.is_active and
                session.finger_count > 0 and
                session.generated_body_armature != "")

    def execute(self, context):
        """Run finger rig generation from current session state."""
        session = context.scene.boneforge_autorig_session

        # Retrieve the body armature object
        armature_obj = bpy.data.objects.get(session.generated_body_armature)
        if armature_obj is None:
            self.report({'ERROR'}, "Body armature not found")
            return {'CANCELLED'}

        # Hand bone mapping (standard naming)
        hand_bones = {
            'hand.L': 'hand.L',
            'hand.R': 'hand.R',
        }

        result = generate_finger_rig(context, session, armature_obj, hand_bones)

        if result.success:
            self.report({'INFO'}, result.message)
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, result.message)
            return {'CANCELLED'}


# ── Registration ──────────────────────────────────────────────

classes = (BF_OT_GenerateFingerRig,)


def register():
    """Register finger generation operator."""
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    """Unregister finger generation operator."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
