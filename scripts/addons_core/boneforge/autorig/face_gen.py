"""BoneCraft Phase 3 — Facial Rig Generator.

Constructs a facial armature and shape keys from the twelve facial
landmarks stored in the AutoRigSession.  Custom bone shapes are
created for intuitive viewport controls.

The generation uses the same staging collection as body_gen for
atomic undo behaviour.
"""


import bpy
from dataclasses import dataclass, field
from mathutils import Vector

from boneforge.autorig.constants import (
    FACE_MARKERS,
    FACE_CONTROLS_COLLECTION,
    FACE_DEFORM_COLLECTION,
    FACE_SHAPE_KEY_NAMES,
)
from boneforge.autorig.session import (
    get_face_marker,
    is_position_placed,
    log_scene_change,
    MIN_POSITION_THRESHOLD,
)
from boneforge.weights.shapes import generate_circle, generate_diamond

import logging

logger = logging.getLogger(__name__)

# Default bone tail direction when face center cannot be determined.
DEFAULT_BONE_DIRECTION = Vector((0, -1, 0))

# Bone length as a fraction of minimum marker spacing.
BONE_LENGTH_RATIO = 0.3

# Fallback bone length when marker spacing is degenerate.
FALLBACK_BONE_LENGTH = 0.02

# Number of vertices in custom bone shape circles.
BONE_SHAPE_SEGMENTS = 12


# ── Result dataclass ──────────────────────────────────────────

@dataclass
class FaceRigResult:
    """Result of facial rig generation."""

    success: bool = False
    message: str = ""
    armature_object_name: str = ""
    bone_count: int = 0
    shape_key_names: list = field(default_factory=list)


# ── Internal helpers ──────────────────────────────────────────

def _gather_face_marker_positions(session):
    """Collect all facial marker positions into a dict.

    Returns:
        Dict mapping marker name to Vector.  Markers at the origin
        are still included but flagged by having near-zero length.
    """
    markers = {}
    for name in FACE_MARKERS:
        marker = get_face_marker(session, name)
        if marker is not None:
            markers[name] = Vector(marker.position)
        else:
            markers[name] = Vector((0, 0, 0))
    return markers


def _compute_face_center(marker_positions):
    """Compute the centroid of all placed markers.

    Only includes markers that are meaningfully placed (not at origin).
    """
    placed_positions = [
        position for position in marker_positions.values()
        if is_position_placed(position)
    ]
    if not placed_positions:
        return Vector((0, 0, 0))

    center = Vector((0, 0, 0))
    for position in placed_positions:
        center += position
    center /= len(placed_positions)
    return center


def _compute_minimum_marker_spacing(marker_positions):
    """Find the smallest distance between any two placed markers.

    Used to scale bone shapes proportionally to the character's
    facial proportions.

    Returns:
        The minimum spacing, or FALLBACK_BONE_LENGTH if fewer than
        two markers are placed.
    """
    placed = [
        position for position in marker_positions.values()
        if is_position_placed(position)
    ]
    if len(placed) < 2:
        return FALLBACK_BONE_LENGTH

    minimum_spacing = float('inf')
    for i in range(len(placed)):
        for j in range(i + 1, len(placed)):
            distance = (placed[i] - placed[j]).length
            if distance > MIN_POSITION_THRESHOLD:
                minimum_spacing = min(minimum_spacing, distance)

    if minimum_spacing == float('inf'):
        return FALLBACK_BONE_LENGTH
    return minimum_spacing


def _derive_face_bones(session):
    """Compute all facial bone head/tail positions from the 12 landmarks.

    Each control bone sits at a landmark position with a short tail
    pointing outward from the face center.

    Returns:
        Dict mapping bone name to ``(head_position, tail_position)``
        as Vectors.
    """
    marker_positions = _gather_face_marker_positions(session)
    face_center = _compute_face_center(marker_positions)
    minimum_spacing = _compute_minimum_marker_spacing(marker_positions)
    bone_length = minimum_spacing * BONE_LENGTH_RATIO

    # Mapping from Blender bone names to marker names
    bone_to_marker = {
        'brow.L': 'BROW_LEFT',
        'brow.R': 'BROW_RIGHT',
        'eye.L': 'EYE_LEFT',
        'eye.R': 'EYE_RIGHT',
        'nose_tip': 'NOSE_TIP',
        'cheek.L': 'CHEEK_LEFT',
        'cheek.R': 'CHEEK_RIGHT',
        'lip_upper': 'UPPER_LIP',
        'lip_lower': 'LOWER_LIP',
        'chin': 'CHIN',
        'jaw.L': 'JAW_LEFT',
        'jaw.R': 'JAW_RIGHT',
    }

    bones = {}
    for bone_name, marker_name in bone_to_marker.items():
        head_position = marker_positions[marker_name]
        if not is_position_placed(head_position):
            continue

        # Tail points outward from face center
        outward_direction = head_position - face_center
        if outward_direction.length > MIN_POSITION_THRESHOLD:
            outward_direction = outward_direction.normalized()
        else:
            outward_direction = DEFAULT_BONE_DIRECTION

        tail_position = head_position + outward_direction * bone_length
        bones[bone_name] = (head_position, tail_position)

    # Derived jaw root: midpoint between left and right jaw markers
    jaw_left = marker_positions.get('JAW_LEFT', Vector((0, 0, 0)))
    jaw_right = marker_positions.get('JAW_RIGHT', Vector((0, 0, 0)))
    if is_position_placed(jaw_left) and is_position_placed(jaw_right):
        jaw_root_position = jaw_left.lerp(jaw_right, 0.5)
        jaw_root_tail = jaw_root_position + Vector((0, 0, -bone_length))
        bones['jaw_root'] = (jaw_root_position, jaw_root_tail)

    return bones


def _create_shape_object(name, verts, edges):
    """Create a hidden wireframe mesh object for use as a custom bone shape.

    Uses vertex/edge data from ``boneforge.weights.shapes`` generators.

    Returns:
        The created mesh ``Object``.
    """
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, edges, [])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    # hide_viewport, not hide_set: hide_set needs the object in a view layer,
    # and it is not linked yet (the RuntimeError dropped every face shape)
    obj.hide_viewport = True
    obj.hide_render = True
    return obj


def _create_face_bone_shapes():
    """Create custom shape meshes for facial control bones.

    Delegates geometry generation to ``boneforge.weights.shapes`` while
    keeping the face-specific sizes.

    Returns:
        Dict mapping shape name to mesh ``Object``.
        Returns an empty dict if creation fails.
    """
    shapes = {}

    # circle_small: radius 0.005, same segment count as weights default (16)
    verts, edges = generate_circle(radius=0.005, segments=BONE_SHAPE_SEGMENTS)
    shapes['circle_small'] = _create_shape_object("BF_Shape_circle_small", verts, edges)

    # circle_medium: radius 0.01
    verts, edges = generate_circle(radius=0.01, segments=BONE_SHAPE_SEGMENTS)
    shapes['circle_medium'] = _create_shape_object("BF_Shape_circle_medium", verts, edges)

    # diamond: size 0.008
    verts, edges = generate_diamond(size=0.008)
    shapes['diamond'] = _create_shape_object("BF_Shape_diamond", verts, edges)

    return shapes


def _shape_key_exists(mesh_obj, key_name):
    """Check whether a shape key with *key_name* already exists on *mesh_obj*."""
    if mesh_obj.data.shape_keys is None:
        return False
    return mesh_obj.data.shape_keys.key_blocks.get(key_name) is not None


def _create_face_shape_keys(mesh_obj, face_bones):
    """Create named shape keys on the mesh for facial expressions.

    Creates a basis shape key if none exists, then adds each expression
    shape key with default zero influence.  Skips keys that already exist.

    Args:
        mesh_obj: The mesh object to receive shape keys.
        face_bones: Dict of bone positions (used for region identification).

    Returns:
        List of successfully created shape key names.
    """
    created_names = []

    # Ensure basis shape key exists
    if mesh_obj.data.shape_keys is None:
        mesh_obj.shape_key_add(name="Basis", from_mix=False)
    else:
        # Verify vertex count matches existing basis
        basis = mesh_obj.data.shape_keys.reference_key
        if basis and len(basis.data) != len(mesh_obj.data.vertices):
            logger.info("[BoneCraft] Shape keys skipped: existing basis has "
                  "incompatible vertex count")
            return created_names

    for key_name in FACE_SHAPE_KEY_NAMES:
        if _shape_key_exists(mesh_obj, key_name):
            continue  # Do not overwrite existing user data

        try:
            shape_key = mesh_obj.shape_key_add(name=key_name, from_mix=False)
            shape_key.value = 0.0
            created_names.append(key_name)
        except RuntimeError as error:
            logger.error(f"[BoneCraft] Shape key '{key_name}' creation failed: {error}")

    return created_names


def _compute_face_root_position(face_bones):
    """Determine the position for the face hierarchy root bone.

    Uses jaw_root if available, otherwise the centroid of all
    facial bone head positions.
    """
    if 'jaw_root' in face_bones:
        return face_bones['jaw_root']

    all_heads = [head for head, _tail in face_bones.values()]
    center = Vector((0, 0, 0))
    for head_position in all_heads:
        center += head_position
    center /= len(all_heads)
    return (center, center + Vector((0, 0, 0.02)))


def _build_face_picker_zones(session):
    """Build picker zone dicts for Phase 1 integration.

    Returns:
        List of dicts in the format expected by ``picker._dict_to_layout()``.
    """
    return [
        {
            'name': "Eyes",
            'bones': ['eye.L', 'eye.R', 'brow.L', 'brow.R'],
            'color': [0.3, 0.6, 0.9],
            'position': [0.5, 0.75],
        },
        {
            'name': "Nose",
            'bones': ['nose_tip'],
            'color': [0.9, 0.7, 0.3],
            'position': [0.5, 0.55],
        },
        {
            'name': "Mouth",
            'bones': ['lip_upper', 'lip_lower', 'jaw_root'],
            'color': [0.9, 0.4, 0.4],
            'position': [0.5, 0.35],
        },
        {
            'name': "Jaw",
            'bones': ['jaw.L', 'jaw.R', 'chin'],
            'color': [0.6, 0.4, 0.7],
            'position': [0.5, 0.2],
        },
        {
            'name': "Cheeks",
            'bones': ['cheek.L', 'cheek.R'],
            'color': [0.9, 0.6, 0.6],
            'position': [0.5, 0.5],
        },
    ]


# ── Main generation function ──────────────────────────────────

def generate_face_rig(context, session):
    """Generate a facial armature from the session's facial marker data.

    Creates facial control bones, custom bone shapes, and named shape
    keys on the target mesh.

    Side effects:
        Creates armature and bone-shape objects in the staging collection.
        Changes Blender's active object and mode during execution.

    Args:
        context: Blender context.
        session: ``BF_AutoRigSession`` PropertyGroup with confirmed markers.

    Returns:
        ``FaceRigResult`` with generation outcome.
    """
    # Check for at least one placed facial marker
    has_placed_markers = any(
        is_position_placed(session.face_markers[i].position)
        for i in range(len(session.face_markers))
    )
    if not has_placed_markers:
        return FaceRigResult(
            success=False,
            message="No facial markers placed",
        )

    mesh_obj = bpy.data.objects.get(session.mesh_object_name)
    if mesh_obj is None:
        return FaceRigResult(
            success=False,
            message=f"Mesh object '{session.mesh_object_name}' not found",
        )

    # Derive bone positions from landmarks
    face_bones = _derive_face_bones(session)
    if not face_bones:
        return FaceRigResult(
            success=False,
            message="Could not derive bone positions from facial markers",
        )

    # Create armature
    armature_data = bpy.data.armatures.new("BoneForge_Face")
    armature_data.display_type = 'WIRE'
    armature_obj = bpy.data.objects.new("BoneForge_Face", armature_data)

    # Link directly to the scene's root collection — NOT the staging
    # collection, which is excluded from view layers.
    context.scene.collection.objects.link(armature_obj)
    context.view_layer.update()
    log_scene_change(session, 'objects_created', armature_obj.name)

    # Create custom bone shapes
    try:
        bone_shapes = _create_face_bone_shapes()
        for shape_name, shape_obj in bone_shapes.items():
            context.scene.collection.objects.link(shape_obj)
            log_scene_change(session, 'objects_created', shape_obj.name)
    except RuntimeError as error:
        logger.warning(f"[BoneCraft] Custom bone shapes could not be created: {error}")
        bone_shapes = {}  # Fall back to default octahedral display

    # Enter edit mode to create bones
    context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode='EDIT')
    edit_bones = armature_data.edit_bones

    # Create face hierarchy root bone
    root_head, root_tail = _compute_face_root_position(face_bones)
    face_root = edit_bones.new('face_root')
    face_root.head = root_head
    face_root.tail = root_tail

    # Create all facial control bones, parented to face_root
    for bone_name, (head_position, tail_position) in face_bones.items():
        bone = edit_bones.new(bone_name)
        bone.head = head_position
        bone.tail = tail_position
        bone.parent = face_root
    # Jaw hinge: the chin and lower lip ride on jaw_root, so rotating it
    # opens the mouth (it used to be a loose sibling that moved nothing).
    jaw = edit_bones.get('jaw_root')
    if jaw is not None:
        for child in ('chin', 'lip_lower'):
            eb = edit_bones.get(child)
            if eb is not None:
                eb.parent = jaw

    bone_count = len(edit_bones)

    # Create bone collections
    # All facial bones serve dual control/deform role
    controls_collection = armature_data.collections.new(FACE_CONTROLS_COLLECTION)
    deform_collection = armature_data.collections.new(FACE_DEFORM_COLLECTION)
    for bone in edit_bones:
        controls_collection.assign(bone)
        deform_collection.assign(bone)

    bpy.ops.object.mode_set(mode='OBJECT')

    # Assign custom bone shapes in object mode (if enabled)
    generate_controllers = getattr(session, 'generate_controllers', True)
    if generate_controllers:
        circle_shape = bone_shapes.get('circle_small')
        if circle_shape is not None:
            for pose_bone in armature_obj.pose.bones:
                pose_bone.custom_shape = circle_shape

    # Create shape keys on the mesh
    shape_key_names = _create_face_shape_keys(mesh_obj, face_bones)

    # Store result
    session.generated_face_armature = armature_obj.name

    return FaceRigResult(
        success=True,
        message=f"Face rig generated: {bone_count} bones, "
                f"{len(shape_key_names)} shape keys",
        armature_object_name=armature_obj.name,
        bone_count=bone_count,
        shape_key_names=shape_key_names,
    )


# ── Operator (called internally by WizardGenerate) ────────────

class BF_OT_GenerateFaceRig(bpy.types.Operator):
    """Generate facial armature from placed markers (internal)"""

    bl_idname = "boneforge.autorig_generate_face"
    bl_label = "Generate Face Rig"
    bl_description = "Build the face bones from the markers placed in the Auto-Rig Wizard"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        """Require an active session with a mesh target."""
        session = context.scene.boneforge_autorig_session
        return session.is_active and session.mesh_object_name != ""

    def execute(self, context):
        """Run face rig generation from current session state."""
        session = context.scene.boneforge_autorig_session
        result = generate_face_rig(context, session)

        if result.success:
            self.report({'INFO'}, result.message)
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, result.message)
            return {'CANCELLED'}


# ── Registration ──────────────────────────────────────────────

classes = (BF_OT_GenerateFaceRig,)


def register():
    """Register face generation operator."""
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    """Unregister face generation operator."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
