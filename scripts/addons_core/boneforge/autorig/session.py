"""BoneCraft Phase 3 — AutoRig Session PropertyGroup and Serialization.

Defines the scene-level wizard state container, crash-recovery JSON
serialization, derived joint calculation, and scene change-log for
cancellation rollback.

The session PropertyGroup is the live Blender-persistent state.  The
JSON custom property on the scene is the crash-recovery backup, written
on every wizard step transition.
"""

import json

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatProperty,
    FloatVectorProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
from mathutils import Vector

from boneforge.core import addon_prefs
from boneforge.autorig.constants import (
    BODY_MARKERS,
    DERIVED_JOINTS,
    FACE_MARKERS,
    FINGER_MARKERS_ALL,
    FINGER_MARKERS_MAX_COUNT,
    RIG_TYPE_ITEMS,
    SHOULDER_RATIO,
    ELBOW_RATIO,
    HIP_RATIO,
    KNEE_RATIO,
    TOE_RATIO,
    HEEL_RATIO,
    STEP_INACTIVE,
)

import logging

logger = logging.getLogger(__name__)


# ── JSON schema version ───────────────────────────────────────

_SCHEMA_VERSION = 2
_JSON_KEY = "boneforge_autorig_session_json"

# Minimum distance threshold for considering a position as "placed".
# Positions at or near the origin (below this threshold) are treated
# as unplaced markers.
MIN_POSITION_THRESHOLD = 0.001


# ── PropertyGroups ────────────────────────────────────────────

class BF_BodyMarker(bpy.types.PropertyGroup):
    """Per-body-marker data: position, confidence, confirmed, symmetry lock."""

    position: FloatVectorProperty(
        name="Position",
        description="3D world-space coordinate of this body marker",
        size=3,
        default=(0.0, 0.0, 0.0),
    )
    confidence: FloatProperty(
        name="Confidence",
        description="Detection confidence score (0.0 = unknown, 1.0 = certain)",
        default=0.0,
        min=0.0,
        max=1.0,
    )
    confirmed: BoolProperty(
        name="Confirmed",
        description="Whether the user has confirmed this marker position",
        default=False,
    )
    symmetry_locked: BoolProperty(
        name="Symmetry Locked",
        description="Whether this marker is mirrored from its symmetry pair",
        default=True,
    )


class BF_FaceMarker(bpy.types.PropertyGroup):
    """Per-facial-marker data: position, confidence, confirmed, symmetry lock."""

    position: FloatVectorProperty(
        name="Position",
        description="3D world-space coordinate of this facial marker",
        size=3,
        default=(0.0, 0.0, 0.0),
    )
    confidence: FloatProperty(
        name="Confidence",
        description="Detection confidence score",
        default=0.0,
        min=0.0,
        max=1.0,
    )
    confirmed: BoolProperty(
        name="Confirmed",
        description="Whether the user has confirmed this marker position",
        default=False,
    )
    symmetry_locked: BoolProperty(
        name="Symmetry Locked",
        description="Whether this marker is mirrored from its symmetry pair",
        default=True,
    )


class BF_FingerMarker(bpy.types.PropertyGroup):
    """Per-finger-marker data: position, confidence, confirmed, symmetry lock."""

    position: FloatVectorProperty(
        name="Position",
        description="3D world-space coordinate of this finger marker",
        size=3,
        default=(0.0, 0.0, 0.0),
    )
    confidence: FloatProperty(
        name="Confidence",
        description="Detection confidence score",
        default=0.0,
        min=0.0,
        max=1.0,
    )
    confirmed: BoolProperty(
        name="Confirmed",
        description="Whether the user has confirmed this marker position",
        default=False,
    )
    symmetry_locked: BoolProperty(
        name="Symmetry Locked",
        description="Whether this marker is mirrored from its symmetry pair",
        default=True,
    )


class BF_SkinningSettings(bpy.types.PropertyGroup):
    """Per-session skinning pipeline configuration.

    Controls how the production skinning pipeline (skin_gen.py)
    processes vertex weights after rig generation.  Exposed in
    the editor's Review step so the user can tune before clicking
    Generate.
    """

    max_influences: IntProperty(
        name="Max Influences",
        description=(
            "Maximum number of bone influences per vertex. "
            "4 is standard for game engines; 8 for film"
        ),
        default=4,
        min=1,
        max=16,
    )

    smooth_iterations: IntProperty(
        name="Smooth Iterations",
        description=(
            "Number of Laplacian smoothing passes on weights. "
            "Higher values produce softer transitions but may "
            "lose detail at joints"
        ),
        # Lowered v3.0.9 default 2 → 1 for humanoid avatar creation —
        # combined with sharpen=1.5 this preserves finger/face detail.
        default=1,
        min=0,
        max=10,
    )

    face_isolation: BoolProperty(
        name="Isolate Face Weights",
        description=(
            "Prevent body bones from influencing face vertices "
            "and vice versa. Recommended for characters with "
            "separate face and body rigs"
        ),
        default=True,
    )

    preserve_volume: BoolProperty(
        name="Preserve Volume",
        description=(
            "Dual-quaternion skinning: bent elbows and knees keep their "
            "volume instead of collapsing (can bulge at bent joints). Joint "
            "Correctives replace it: with both on, correctives are used"
        ),
        default=False,
    )

    joint_correctives: BoolProperty(
        name="Joint Correctives",
        description=(
            "When the control rig is built, add corrective shape keys: elbows "
            "and knees keep their shape when bent, deep bends and lowered arms "
            "flatten skin against skin instead of passing through"
        ),
        default=False,
    )

    corrective_presets: BoolProperty(
        name="Apply Corrective Presets",
        description=(
            "Apply known-good weight adjustments for common "
            "problem areas (shoulders, elbows, hips, knees)"
        ),
        default=True,
    )

    quality_target: EnumProperty(
        name="Quality Target",
        description="Skinning quality / performance trade-off",
        items=[
            ('GAME', "Game Ready",
             "4 influences max, aggressive smoothing, optimized for real-time"),
            ('FILM', "Film Quality",
             "8 influences max, gentle smoothing, maximum deformation fidelity"),
            ('DRAFT', "Draft",
             "Fast auto-weights only, no post-processing"),
        ],
        default='GAME',
    )


class BF_RetargetBoneMapping(bpy.types.PropertyGroup):
    """Single source-to-target bone mapping entry for retargeting."""

    source_name: StringProperty(
        name="Source Bone",
        description="Bone name in the source animation",
        default="",
    )
    target_name: StringProperty(
        name="Target Bone",
        description="Bone name in the target armature",
        default="",
    )
    match_type: EnumProperty(
        name="Match Type",
        description="How this mapping was established",
        items=[
            ('EXACT', "Exact", "Names matched exactly"),
            ('RIGIFY', "Rigify", "Matched via Rigify naming convention"),
            ('MIXAMO', "Mixamo", "Matched via Mixamo-to-Rigify mapping"),
            ('PRESET', "Preset", "Matched via a bone-map preset (control rig FK)"),
            ('MANUAL', "Manual", "User-assigned mapping"),
            ('EXCLUDED', "Excluded", "Explicitly excluded from retargeting"),
        ],
        default='EXACT',
    )
    is_matched: BoolProperty(
        name="Is Matched",
        description="Whether a target bone has been assigned",
        default=False,
    )


class BF_AutoRigSession(bpy.types.PropertyGroup):
    """Root session container for the auto-rig wizard.

    Holds all wizard state, marker positions, derived joints, and the
    scene change-log for cancellation rollback.  Registered as a
    ``PointerProperty`` on ``bpy.types.Scene``.
    """

    # ── Wizard state ───────────────────────────────────────────

    is_active: BoolProperty(
        name="Wizard Active",
        description="Whether the auto-rig wizard is currently running",
        default=False,
    )
    wizard_step: IntProperty(
        name="Current Step",
        description="Current wizard step number (0 = inactive)",
        default=0,
        min=0,
        max=8,
    )

    # ── Mesh and rig type ──────────────────────────────────────

    mesh_object_name: StringProperty(
        name="Mesh Object",
        description="Name of the target mesh object for rigging",
        default="",
    )
    rig_type: EnumProperty(
        name="Rig Type",
        description="What to generate: body, face, or both",
        items=RIG_TYPE_ITEMS,
        default='BODY_AND_FACE',
    )

    # ── Body markers (7 markers as a CollectionProperty) ──────

    body_markers: CollectionProperty(
        name="Body Markers",
        description="Body landmark positions for auto-rigging",
        type=BF_BodyMarker,
    )

    # ── Facial markers (12 markers) ───────────────────────────

    face_markers: CollectionProperty(
        name="Face Markers",
        description="Facial landmark positions for facial rig generation",
        type=BF_FaceMarker,
    )

    # ── Finger markers ───────────────────────────────────────
    finger_markers: CollectionProperty(
        name="Finger Markers",
        description="Finger landmark positions for finger rig generation",
        type=BF_FingerMarker,
    )
    finger_count: IntProperty(
        name="Finger Count",
        description="Number of fingers to generate per hand (0, 1, 2, 3, or 5)",
        default=5, min=0, max=5,
    )
    finger_symmetry: BoolProperty(
        name="Mirror Fingers",
        description="Mirror left hand finger markers to right hand",
        default=True,
    )
    body_symmetry_enabled: BoolProperty(
        name="Mirror Body Markers",
        description=(
            "When enabled, moving a left or right marker automatically "
            "mirrors it to the opposite side. Disable for asymmetric rigs."
        ),
        default=True,
    )
    face_symmetry_enabled: BoolProperty(
        name="Mirror Face Markers",
        description=(
            "When enabled, moving a left or right facial marker automatically "
            "mirrors it to the opposite side. Disable for asymmetric face rigs."
        ),
        default=True,
    )
    finger_active_hand: EnumProperty(
        name="Active Hand",
        description="Which hand to place finger markers on",
        items=[
            ('LEFT', "Left", "Place markers on left hand"),
            ('RIGHT', "Right", "Place markers on right hand"),
        ],
        default='LEFT',
    )
    finger_right_overrides: StringProperty(
        name="Right Hand Overrides",
        description="JSON-encoded set of right-hand marker names with broken mirror links",
        default="[]",
    )

    # ── Derived joint positions (8 joints) ────────────────────

    derived_shoulder_left: FloatVectorProperty(size=3, default=(0, 0, 0))
    derived_shoulder_right: FloatVectorProperty(size=3, default=(0, 0, 0))
    derived_elbow_left: FloatVectorProperty(size=3, default=(0, 0, 0))
    derived_elbow_right: FloatVectorProperty(size=3, default=(0, 0, 0))
    derived_hip_left: FloatVectorProperty(size=3, default=(0, 0, 0))
    derived_hip_right: FloatVectorProperty(size=3, default=(0, 0, 0))
    derived_knee_left: FloatVectorProperty(size=3, default=(0, 0, 0))
    derived_knee_right: FloatVectorProperty(size=3, default=(0, 0, 0))
    derived_toe_left: FloatVectorProperty(size=3, default=(0, 0, 0))
    derived_toe_right: FloatVectorProperty(size=3, default=(0, 0, 0))
    derived_heel_left: FloatVectorProperty(size=3, default=(0, 0, 0))
    derived_heel_right: FloatVectorProperty(size=3, default=(0, 0, 0))

    # ── Retarget mapping table ────────────────────────────────

    retarget_mappings: CollectionProperty(
        name="Retarget Mappings",
        description="Source-to-target bone mapping for retargeting",
        type=BF_RetargetBoneMapping,
    )

    # ── Generated armature references ─────────────────────────

    generated_body_armature: StringProperty(
        name="Generated Body Armature",
        description="Name of the generated body armature object",
        default="",
    )
    generated_face_armature: StringProperty(
        name="Generated Face Armature",
        description="Name of the generated face armature object",
        default="",
    )
    generated_final_armature: StringProperty(
        name="Final Armature",
        description="Name of the merged final armature object",
        default="",
    )

    # ── Scene change log for cancellation rollback ────────────

    snapshot_blend_data: StringProperty(
        name="Scene Snapshot",
        description="JSON change-log of wizard-created scene modifications",
        default="{}",
    )

    # ── Skinning settings ─────────────────────────────────────

    skinning_settings: PointerProperty(
        name="Skinning Settings",
        description="Configuration for the production skinning pipeline",
        type=BF_SkinningSettings,
    )

    skinning_quality_score: FloatProperty(
        name="Skinning Quality Score",
        description="Overall quality score from the skinning pipeline (0.0–1.0)",
        default=0.0,
        min=0.0,
        max=1.0,
    )

    skinning_method: StringProperty(
        name="Skinning Method",
        description="Which base weight method was used: AUTO, ENVELOPE, or FALLBACK",
        default="",
    )

    skinning_warnings: StringProperty(
        name="Skinning Warnings",
        description="JSON-encoded list of warnings from the skinning pipeline",
        default="[]",
    )

    skinning_unweighted_verts: IntProperty(
        name="Unweighted Vertices",
        description="Number of vertices with zero weight after skinning",
        default=0,
    )

    skinning_discontinuities: IntProperty(
        name="Weight Discontinuities",
        description="Number of weight discontinuities detected",
        default=0,
    )

    skinning_face_isolated: BoolProperty(
        name="Face Isolation Applied",
        description="Whether face/body weight isolation was applied",
        default=False,
    )

    skinning_correctives_applied: BoolProperty(
        name="Correctives Applied",
        description="Whether corrective presets were applied",
        default=False,
    )

    # ── Generation progress tracking ──────────────────────────

    generation_stage: IntProperty(
        name="Generation Stage",
        description="Current generation stage index for progress display",
        default=0,
        min=0,
    )

    generation_stage_label: StringProperty(
        name="Stage Label",
        description="Human-readable label of the current generation stage",
        default="",
    )

    # ── Rig generation options ───────────────────────────────

    rig_mode: EnumProperty(
        name="IK/FK Mode",
        description="Which kinematic chains to generate",
        items=[
            ('IK_FK', "IK + FK",
             "Generate both inverse and forward kinematics chains"),
            ('IK_ONLY', "IK Only",
             "Generate inverse kinematics chains only"),
            ('FK_ONLY', "FK Only",
             "Generate forward kinematics chains only"),
        ],
        default='IK_FK',
    )

    generate_controllers: BoolProperty(
        name="Generate Controllers",
        description=(
            "Create custom shape widgets for pose bones "
            "(circles, cubes, etc.) for easier viewport selection"
        ),
        default=True,
    )

    # ── Controller density per body section ─────────────────

    spine_segments: IntProperty(
        name="Spine Segments",
        description=(
            "Number of bones in the spine chain. More segments "
            "allow smoother spinal bending and twist distribution"
        ),
        default=3,
        min=2,
        max=8,
    )

    neck_segments: IntProperty(
        name="Neck Segments",
        description=(
            "Number of bones in the neck chain. "
            "2+ segments allow serpentine neck motion"
        ),
        default=1,
        min=1,
        max=4,
    )

    finger_controls: BoolProperty(
        name="Finger Controls",
        description=(
            "Generate individual finger bones with FK controls. "
            "Requires a hand mesh with enough geometry"
        ),
        default=False,
    )
    # Deprecated: Use finger_count and finger_symmetry instead for v2+

    twist_bones: BoolProperty(
        name="Twist Bones",
        description=(
            "Add twist/roll bones to upper arms and thighs for "
            "smoother deformation during rotation"
        ),
        default=False,
    )

    skirt_bones: BoolProperty(
        name="Skirt Bones",
        description=(
            "When the control rig is built and the mesh has a skirt or dress "
            "(skin hanging below the hips all the way around), add a ring of "
            "skirt bones that swing with the legs"
        ),
        default=True,
    )

    face_controls: BoolProperty(
        name="Face Controls",
        description=(
            "When the control rig is built, add eye aim, blinking lids and "
            "lip follow to the wizard's face bones"
        ),
        default=True,
    )

    twist_segments: IntProperty(
        name="Twist Segments",
        description=(
            "Number of twist subdivisions per limb segment. "
            "Higher values give smoother twist distribution"
        ),
        default=2,
        min=1,
        max=4,
    )

    # ── Marker placement axis constraint ─────────────────────

    placement_axis_x: BoolProperty(
        name="X", description="Allow marker placement along the X axis",
        default=True,
    )
    placement_axis_y: BoolProperty(
        name="Y", description="Allow marker placement along the Y axis",
        default=True,
    )
    placement_axis_z: BoolProperty(
        name="Z", description="Allow marker placement along the Z axis",
        default=True,
    )

    # ── Viewport helper expand state ─────────────────────────
    viewport_tools_expanded: BoolProperty(
        name="Viewport Display",
        description="Show simplified viewport display toggles for rigging",
        default=False,
    )

    # ── Decimated collision proxy ─────────────────────────────

    proxy_mesh_name: StringProperty(
        name="Proxy Mesh",
        description="Name of the decimated collision proxy mesh",
        default="",
    )


# ── Marker index lookup ──────────────────────────────────────

def _marker_index(marker_name, marker_list):
    """Return the index of *marker_name* within *marker_list*, or -1.

    This is an intentional fallback — returning -1 signals "not found"
    to callers, which guard against it before indexing.
    """
    try:
        return marker_list.index(marker_name)
    except ValueError:
        return -1


def _ensure_marker_slots(session):
    """Ensure the session's marker collections have the right number of entries.

    Called after session creation or JSON restore to pad missing slots.
    """
    while len(session.body_markers) < len(BODY_MARKERS):
        session.body_markers.add()
    while len(session.face_markers) < len(FACE_MARKERS):
        session.face_markers.add()
    # Finger markers: allocate max slots (6 left + 6 right = 12)
    finger_total = FINGER_MARKERS_MAX_COUNT * 2  # left + right
    while len(session.finger_markers) < finger_total:
        session.finger_markers.add()


def get_body_marker(session, marker_name):
    """Return the BF_BodyMarker for *marker_name*, or None."""
    index = _marker_index(marker_name, BODY_MARKERS)
    if index < 0 or index >= len(session.body_markers):
        return None
    return session.body_markers[index]


def get_face_marker(session, marker_name):
    """Return the BF_FaceMarker for *marker_name*, or None."""
    index = _marker_index(marker_name, FACE_MARKERS)
    if index < 0 or index >= len(session.face_markers):
        return None
    return session.face_markers[index]


def get_finger_marker(session, marker_name):
    """Return the BF_FingerMarker for *marker_name*, or None.

    Finger markers use a flat index: left markers at indices 0..N-1,
    right markers at N..2N-1, where N is FINGER_MARKERS_MAX_COUNT.
    """
    # Try left markers first
    if marker_name in FINGER_MARKERS_ALL:
        index = FINGER_MARKERS_ALL.index(marker_name)
        if index >= 0 and index < len(session.finger_markers):
            return session.finger_markers[index]
    # Try right markers
    right_name = marker_name
    left_equiv = marker_name.replace('_R', '_L')
    if left_equiv in FINGER_MARKERS_ALL and left_equiv != marker_name:
        index = FINGER_MARKERS_ALL.index(left_equiv) + FINGER_MARKERS_MAX_COUNT
        if index < len(session.finger_markers):
            return session.finger_markers[index]
    return None


def is_position_placed(position):
    """Return True if a marker position is meaningfully placed (not at origin)."""
    return Vector(position).length > MIN_POSITION_THRESHOLD


# ── Serialization helpers ─────────────────────────────────────

def _serialize_markers(marker_collection, marker_names):
    """Serialize a marker collection to a list of dicts.

    Used by both body and face marker serialization to avoid
    code duplication.

    Args:
        marker_collection: The ``CollectionProperty`` of markers.
        marker_names: Tuple of marker name strings.

    Returns:
        List of dicts with name, position, confidence, confirmed,
        and symmetry_locked fields.
    """
    result = []
    for index, name in enumerate(marker_names):
        marker = marker_collection[index]
        result.append({
            'name': name,
            'position': list(marker.position),
            'confidence': marker.confidence,
            'confirmed': marker.confirmed,
            'symmetry_locked': marker.symmetry_locked,
        })
    return result


def _deserialize_markers(marker_collection, marker_data_list, marker_names):
    """Restore marker data from a list of dicts into a collection.

    Args:
        marker_collection: The ``CollectionProperty`` to populate.
        marker_data_list: List of dicts from ``_serialize_markers()``.
        marker_names: Tuple of valid marker names (for bounds checking).
    """
    for index, marker_data in enumerate(marker_data_list):
        if index >= len(marker_names):
            break
        marker = marker_collection[index]
        position = marker_data.get('position', [0, 0, 0])
        marker.position = (position[0], position[1], position[2])
        marker.confidence = marker_data.get('confidence', 0.0)
        marker.confirmed = marker_data.get('confirmed', False)
        marker.symmetry_locked = marker_data.get('symmetry_locked', True)


def _derived_joint_attr_name(joint_name):
    """Convert a derived joint name like 'SHOULDER_LEFT' to its attribute name.

    The naming convention maps UPPER_SNAKE (constant) to lower_snake
    (PropertyGroup attribute): 'SHOULDER_LEFT' -> 'derived_shoulder_left'.
    """
    return f"derived_{joint_name.lower()}"


# ── Serialization ─────────────────────────────────────────────

def session_to_json(session):
    """Serialize the entire session PropertyGroup to a JSON string.

    Returns:
        A JSON string suitable for storing as a scene custom property.
    """
    _ensure_marker_slots(session)

    body = _serialize_markers(session.body_markers, BODY_MARKERS)
    face = _serialize_markers(session.face_markers, FACE_MARKERS)
    finger_names = tuple(FINGER_MARKERS_ALL) + tuple(n.replace('_L', '_R') for n in FINGER_MARKERS_ALL)
    fingers = _serialize_markers(session.finger_markers, finger_names)

    derived = {}
    for joint_name in DERIVED_JOINTS:
        attr_name = _derived_joint_attr_name(joint_name)
        derived[joint_name] = list(getattr(session, attr_name, (0, 0, 0)))

    data = {
        'schema_version': _SCHEMA_VERSION,
        'is_active': session.is_active,
        'wizard_step': session.wizard_step,
        'mesh_object_name': session.mesh_object_name,
        'rig_type': session.rig_type,
        'body_markers': body,
        'face_markers': face,
        'finger_markers': fingers,
        'finger_count': session.finger_count,
        'finger_symmetry': session.finger_symmetry,
        'finger_active_hand': session.finger_active_hand,
        'finger_right_overrides': session.finger_right_overrides,
        'derived_joints': derived,
        'generated_body_armature': session.generated_body_armature,
        'generated_face_armature': session.generated_face_armature,
        'generated_final_armature': session.generated_final_armature,
        'snapshot_blend_data': session.snapshot_blend_data,
        'proxy_mesh_name': session.proxy_mesh_name,
        'rig_mode': session.rig_mode,
        'generate_controllers': session.generate_controllers,
        'controller_density': {
            'spine_segments': session.spine_segments,
            'neck_segments': session.neck_segments,
            'finger_controls': session.finger_controls,
            'twist_bones': session.twist_bones,
            'twist_segments': session.twist_segments,
            'face_controls': session.face_controls,
            'skirt_bones': session.skirt_bones,
        },
        'placement_axis': [
            session.placement_axis_x,
            session.placement_axis_y,
            session.placement_axis_z,
        ],
        # MIN-11 fix: persist skinning settings so they survive crash/restore
        'skinning_settings': {
            'max_influences': session.skinning_settings.max_influences,
            'smooth_iterations': session.skinning_settings.smooth_iterations,
            'face_isolation': session.skinning_settings.face_isolation,
            'corrective_presets': session.skinning_settings.corrective_presets,
            'quality_target': session.skinning_settings.quality_target,
        },
    }

    return json.dumps(data, indent=2)


def json_to_session(json_str, session):
    """Deserialize a JSON string into the session PropertyGroup.

    Args:
        json_str: JSON string previously produced by ``session_to_json()``.
        session: The ``BF_AutoRigSession`` PropertyGroup to populate.

    Returns:
        True if deserialization succeeded, False if the JSON was corrupt
        or schema-mismatched.
    """
    try:
        data = json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return False

    if not isinstance(data, dict):
        return False

    # M-02: Schema versioning with migration support
    version = data.get('schema_version', 0)
    if version < _SCHEMA_VERSION:
        logger.info(f"[BoneCraft] Migrating session data from v{version} to v{_SCHEMA_VERSION}")
        # v1 -> v2: Remap wizard steps for finger markers
        if version < 2:
            # Remap wizard steps: old 4->5, 5->6, 6->7, 7->8
            old_step = data.get('wizard_step', 0)
            step_remap = {4: 5, 5: 6, 6: 7, 7: 8}
            data['wizard_step'] = step_remap.get(old_step, old_step)
    if version > _SCHEMA_VERSION:
        return False  # Cannot load data from a newer schema version

    session.is_active = data.get('is_active', False)
    session.wizard_step = data.get('wizard_step', STEP_INACTIVE)
    session.mesh_object_name = data.get('mesh_object_name', "")
    session.rig_type = data.get('rig_type', 'BODY_AND_FACE')

    # Restore markers using shared helper
    _ensure_marker_slots(session)
    _deserialize_markers(
        session.body_markers, data.get('body_markers', []), BODY_MARKERS,
    )
    _deserialize_markers(
        session.face_markers, data.get('face_markers', []), FACE_MARKERS,
    )

    # Restore finger markers
    finger_names = tuple(FINGER_MARKERS_ALL) + tuple(
        n.replace('_L', '_R') for n in FINGER_MARKERS_ALL
    )
    _deserialize_markers(
        session.finger_markers, data.get('finger_markers', []), finger_names,
    )
    session.finger_count = data.get('finger_count', 5)
    session.finger_symmetry = data.get('finger_symmetry', True)
    session.finger_active_hand = data.get('finger_active_hand', 'LEFT')
    session.finger_right_overrides = data.get('finger_right_overrides', '[]')

    # Restore derived joints
    derived = data.get('derived_joints', {})
    for joint_name in DERIVED_JOINTS:
        attr_name = _derived_joint_attr_name(joint_name)
        position = derived.get(joint_name, [0, 0, 0])
        setattr(session, attr_name, (position[0], position[1], position[2]))

    # Restore generated armature names
    session.generated_body_armature = data.get('generated_body_armature', "")
    session.generated_face_armature = data.get('generated_face_armature', "")
    session.generated_final_armature = data.get('generated_final_armature', "")

    # Restore scene snapshot and proxy
    session.snapshot_blend_data = data.get('snapshot_blend_data', "{}")
    session.proxy_mesh_name = data.get('proxy_mesh_name', "")

    # Restore rig generation options
    session.rig_mode = data.get('rig_mode', 'IK_FK')
    session.generate_controllers = data.get('generate_controllers', True)
    cd = data.get('controller_density', {})
    if cd:
        session.spine_segments = cd.get('spine_segments', 3)
        session.neck_segments = cd.get('neck_segments', 1)
        session.finger_controls = cd.get('finger_controls', False)
        session.twist_bones = cd.get('twist_bones', False)
        session.twist_segments = cd.get('twist_segments', 2)
        session.face_controls = cd.get('face_controls', True)
        session.skirt_bones = cd.get('skirt_bones', True)
    axis = data.get('placement_axis', [True, True, True])
    if len(axis) >= 3:
        session.placement_axis_x = axis[0]
        session.placement_axis_y = axis[1]
        session.placement_axis_z = axis[2]

    # MIN-11 fix: restore skinning settings
    skin_data = data.get('skinning_settings', {})
    if skin_data:
        ss = session.skinning_settings
        ss.max_influences = skin_data.get('max_influences', 4)
        ss.smooth_iterations = skin_data.get('smooth_iterations', 1)
        ss.face_isolation = skin_data.get('face_isolation', True)
        ss.corrective_presets = skin_data.get('corrective_presets', True)
        ss.quality_target = skin_data.get('quality_target', 'GAME')

    return True


def save_session_backup(scene):
    """Write the current session state to the scene's JSON custom property.

    Called on every wizard step transition for crash recovery.
    """
    session = scene.boneforge_autorig_session
    scene[_JSON_KEY] = session_to_json(session)


def restore_session_backup(scene):
    """Attempt to restore the session from the scene's JSON custom property.

    Returns:
        True if a valid backup was found and restored, False otherwise.
    """
    json_str = scene.get(_JSON_KEY, "")
    if not json_str:
        return False
    session = scene.boneforge_autorig_session
    if not json_to_session(json_str, session):
        return False

    # S-07 fix: Validate that referenced objects still exist in the current
    # file.  After file append / crash recovery the mesh or armature may be
    # gone.  If so, reset the session to prevent a broken wizard state.
    if session.is_active:
        # MIN-9 fix: removed redundant 'import bpy' (already at module level)
        mesh_name = session.mesh_object_name
        if mesh_name and bpy.data.objects.get(mesh_name) is None:
            session.is_active = False
            session.wizard_step = STEP_INACTIVE
            return False

        for attr in ('generated_body_armature',
                     'generated_face_armature',
                     'generated_final_armature'):
            arm_name = getattr(session, attr, "")
            if arm_name:
                obj = bpy.data.objects.get(arm_name)
                # SIG-1 fix: also verify the object is actually an armature,
                # not a replacement object with the same name
                if obj is None or obj.type != 'ARMATURE':
                    # Clear the stale reference but don't abort — the wizard
                    # may still be in an earlier step that hasn't generated
                    # this armature yet.
                    setattr(session, attr, "")

    return True


# ── Derived joint calculation ─────────────────────────────────

def _read_marker_position(session, marker_name):
    """Read a body marker's position as a Vector.

    Centralises the pattern of looking up a marker by name and
    converting its position tuple to a mathutils Vector.
    """
    marker_index = _marker_index(marker_name, BODY_MARKERS)
    if marker_index < 0:
        raise ValueError(
            f"Unknown body marker '{marker_name}'. "
            f"Valid markers: {', '.join(BODY_MARKERS)}"
        )
    return Vector(session.body_markers[marker_index].position)


def _read_optional_marker_position(session, marker_name):
    """Read an optional body marker's position, returning None if unplaced.

    Unlike ``_read_marker_position()`` which raises on unknown names,
    this returns ``None`` for markers that haven't been manually placed.
    """
    marker = get_body_marker(session, marker_name)
    if marker is None:
        return None
    pos = Vector(marker.position)
    if not is_position_placed(pos):
        return None
    if not marker.confirmed:
        return None
    return pos


def recalculate_derived_joints(session, context=None):
    """Recalculate the 8 derived joint positions from body markers.

    For each derived joint, a manually placed optional marker takes
    priority.  If the user has placed and confirmed e.g. SHOULDER_LEFT,
    that position is used directly instead of being computed via lerp.

    Uses proportion ratios from addon preferences (which default to the
    named constants in ``constants.py``).

    Args:
        session: The ``BF_AutoRigSession`` PropertyGroup.
        context: Optional Blender context for reading addon preferences.
                 If None, uses the constant defaults directly.
    """
    _ensure_marker_slots(session)

    # Read proportion ratios from preferences or fall back to defaults
    shoulder_ratio = SHOULDER_RATIO
    elbow_ratio = ELBOW_RATIO
    hip_ratio = HIP_RATIO
    knee_ratio = KNEE_RATIO
    toe_ratio = TOE_RATIO
    heel_ratio = HEEL_RATIO

    if context is not None:
        try:
            prefs = addon_prefs(context)
            shoulder_ratio = getattr(prefs, 'proportion_shoulder', SHOULDER_RATIO)
            elbow_ratio = getattr(prefs, 'proportion_elbow', ELBOW_RATIO)
            hip_ratio = getattr(prefs, 'proportion_hip', HIP_RATIO)
            knee_ratio = getattr(prefs, 'proportion_knee', KNEE_RATIO)
            toe_ratio = getattr(prefs, 'proportion_toe', TOE_RATIO)
            heel_ratio = getattr(prefs, 'proportion_heel', HEEL_RATIO)
        except KeyError:
            # Addon not yet registered — use constant defaults
            pass

    # Read body marker positions
    neck_position = _read_marker_position(session, 'NECK_BASE')
    pelvis_position = _read_marker_position(session, 'PELVIS')
    wrist_left_position = _read_marker_position(session, 'WRIST_LEFT')
    wrist_right_position = _read_marker_position(session, 'WRIST_RIGHT')
    ankle_left_position = _read_marker_position(session, 'ANKLE_LEFT')
    ankle_right_position = _read_marker_position(session, 'ANKLE_RIGHT')

    # Check for manually placed optional markers — these take priority
    manual_shoulder_left = _read_optional_marker_position(session, 'SHOULDER_LEFT')
    manual_shoulder_right = _read_optional_marker_position(session, 'SHOULDER_RIGHT')
    manual_elbow_left = _read_optional_marker_position(session, 'ELBOW_LEFT')
    manual_elbow_right = _read_optional_marker_position(session, 'ELBOW_RIGHT')
    manual_hip_left = _read_optional_marker_position(session, 'HIP_LEFT')
    manual_hip_right = _read_optional_marker_position(session, 'HIP_RIGHT')
    manual_knee_left = _read_optional_marker_position(session, 'KNEE_LEFT')
    manual_knee_right = _read_optional_marker_position(session, 'KNEE_RIGHT')
    manual_toe_left = _read_optional_marker_position(session, 'TOE_LEFT')
    manual_toe_right = _read_optional_marker_position(session, 'TOE_RIGHT')
    manual_heel_left = _read_optional_marker_position(session, 'HEEL_LEFT')
    manual_heel_right = _read_optional_marker_position(session, 'HEEL_RIGHT')

    # Derive shoulder positions: manual placement or neck -> wrist lerp
    shoulder_left = manual_shoulder_left or neck_position.lerp(wrist_left_position, shoulder_ratio)
    shoulder_right = manual_shoulder_right or neck_position.lerp(wrist_right_position, shoulder_ratio)

    # Derive elbow positions: manual placement or shoulder -> wrist lerp
    elbow_left = manual_elbow_left or shoulder_left.lerp(wrist_left_position, elbow_ratio)
    elbow_right = manual_elbow_right or shoulder_right.lerp(wrist_right_position, elbow_ratio)

    # Derive hip positions: manual placement or pelvis -> ankle lerp
    hip_left = manual_hip_left or pelvis_position.lerp(ankle_left_position, hip_ratio)
    hip_right = manual_hip_right or pelvis_position.lerp(ankle_right_position, hip_ratio)

    # Derive knee positions: manual placement or hip -> ankle lerp
    knee_left = manual_knee_left or hip_left.lerp(ankle_left_position, knee_ratio)
    knee_right = manual_knee_right or hip_right.lerp(ankle_right_position, knee_ratio)

    # Derive toe positions: manual placement or project forward from ankle
    # Toes extend forward (negative Y in Blender convention) from the ankle
    foot_forward = Vector((0.0, -1.0, 0.0))
    shin_length_left = (ankle_left_position - knee_left).length
    shin_length_right = (ankle_right_position - knee_right).length
    toe_left = manual_toe_left or (ankle_left_position + foot_forward * shin_length_left * toe_ratio)
    toe_right = manual_toe_right or (ankle_right_position + foot_forward * shin_length_right * toe_ratio)

    # Derive heel positions: manual placement or project backward from ankle
    # Heels extend behind and slightly below the ankle
    heel_offset = Vector((0.0, 1.0, -0.3)).normalized()
    heel_left = manual_heel_left or (ankle_left_position + heel_offset * shin_length_left * heel_ratio)
    heel_right = manual_heel_right or (ankle_right_position + heel_offset * shin_length_right * heel_ratio)

    # Write back to session
    session.derived_shoulder_left = tuple(shoulder_left)
    session.derived_shoulder_right = tuple(shoulder_right)
    session.derived_elbow_left = tuple(elbow_left)
    session.derived_elbow_right = tuple(elbow_right)
    session.derived_hip_left = tuple(hip_left)
    session.derived_hip_right = tuple(hip_right)
    session.derived_knee_left = tuple(knee_left)
    session.derived_knee_right = tuple(knee_right)
    session.derived_toe_left = tuple(toe_left)
    session.derived_toe_right = tuple(toe_right)
    session.derived_heel_left = tuple(heel_left)
    session.derived_heel_right = tuple(heel_right)


# ── Scene change-log ──────────────────────────────────────────

def _load_change_log(session):
    """Parse the scene change-log JSON from the session.

    Returns a dict.  If the JSON is corrupt, returns an empty dict
    and prints a warning so the corruption is visible.
    """
    try:
        return json.loads(session.snapshot_blend_data)
    except (json.JSONDecodeError, TypeError):
        logger.warning("[BoneCraft] Warning: scene change-log JSON was corrupt — starting fresh")
        return {}


def log_scene_change(session, category, data):
    """Append a change entry to the session's scene snapshot log.

    Args:
        session: The ``BF_AutoRigSession`` PropertyGroup.
        category: One of ``'objects_created'``, ``'modifiers_added'``,
                  ``'properties_set'``.
        data: The data to log.  For ``objects_created``, a string (object
              name).  For ``modifiers_added``, a dict
              ``{'object': name, 'modifier': name}``.  For
              ``properties_set``, a dict ``{'object': name, 'prop': name,
              'old_value': value}``.
    """
    log = _load_change_log(session)

    if category not in log:
        log[category] = []

    log[category].append(data)
    session.snapshot_blend_data = json.dumps(log)


def _rollback_created_objects(object_names):
    """Delete objects created by the wizard, in reverse order.

    Returns the number of objects successfully removed.
    """
    reverted = 0
    for object_name in reversed(object_names):
        obj = bpy.data.objects.get(object_name)
        if obj is not None:
            bpy.data.objects.remove(obj, do_unlink=True)
            reverted += 1
    return reverted


def _rollback_added_modifiers(modifier_entries):
    """Remove modifiers added by the wizard.

    Returns the number of modifiers successfully removed.
    """
    reverted = 0
    for entry in reversed(modifier_entries):
        object_name = entry.get('object', '')
        modifier_name = entry.get('modifier', '')
        obj = bpy.data.objects.get(object_name)
        if obj is None:
            continue
        modifier = obj.modifiers.get(modifier_name)
        if modifier is not None:
            obj.modifiers.remove(modifier)
            reverted += 1
    return reverted


def _rollback_set_properties(property_entries):
    """Restore properties that the wizard changed to their original values.

    Returns the number of properties successfully restored.
    """
    reverted = 0
    for entry in reversed(property_entries):
        object_name = entry.get('object', '')
        property_name = entry.get('prop', '')
        old_value = entry.get('old_value')
        obj = bpy.data.objects.get(object_name)
        if obj is None:
            continue
        if not property_name or old_value is None:
            continue
        try:
            setattr(obj, property_name, old_value)
            reverted += 1
        except (AttributeError, TypeError) as error:
            logger.error(f"[BoneCraft] Failed to restore {object_name}.{property_name}: {error}")
    return reverted


def rollback_scene_changes(session):
    """Revert all wizard-created scene modifications using the change log.

    Delegates to specialised rollback helpers for each change category.

    Args:
        session: The ``BF_AutoRigSession`` PropertyGroup.

    Returns:
        The number of changes successfully reverted.
    """
    log = _load_change_log(session)
    reverted = 0

    reverted += _rollback_created_objects(log.get('objects_created', []))
    reverted += _rollback_added_modifiers(log.get('modifiers_added', []))
    reverted += _rollback_set_properties(log.get('properties_set', []))

    # Clear the log
    session.snapshot_blend_data = "{}"
    return reverted


# ── Session reset ─────────────────────────────────────────────

def reset_session(session):
    """Reset all session fields to their default state.

    Called on wizard cancel or completion.
    """
    session.is_active = False
    session.wizard_step = STEP_INACTIVE
    session.mesh_object_name = ""
    session.rig_type = 'BODY_AND_FACE'

    # Clear marker collections
    session.body_markers.clear()
    session.face_markers.clear()
    session.finger_markers.clear()

    # Clear derived joints
    for joint_name in DERIVED_JOINTS:
        attr_name = _derived_joint_attr_name(joint_name)
        setattr(session, attr_name, (0.0, 0.0, 0.0))

    # Clear retarget mappings
    session.retarget_mappings.clear()

    # Clear generated armature references
    session.generated_body_armature = ""
    session.generated_face_armature = ""
    session.generated_final_armature = ""

    # Clear skinning results
    session.skinning_quality_score = 0.0
    session.skinning_method = ""
    session.skinning_warnings = "[]"
    session.skinning_unweighted_verts = 0
    session.skinning_discontinuities = 0
    session.skinning_face_isolated = False
    session.skinning_correctives_applied = False
    session.generation_stage = 0
    session.generation_stage_label = ""

    # Reset rig generation options
    session.rig_mode = 'IK_FK'
    session.generate_controllers = True
    session.spine_segments = 3
    session.neck_segments = 1
    session.finger_controls = False
    session.twist_bones = False
    session.twist_segments = 2
    session.placement_axis_x = True
    session.placement_axis_y = True
    session.placement_axis_z = True

    # Reset finger fields
    session.finger_count = 5
    session.finger_symmetry = True
    session.body_symmetry_enabled = True
    session.face_symmetry_enabled = True
    session.finger_active_hand = 'LEFT'
    session.finger_right_overrides = '[]'

    # Clear change log and proxy
    session.snapshot_blend_data = "{}"
    session.proxy_mesh_name = ""


# ── Registration ──────────────────────────────────────────────

classes = (
    BF_BodyMarker,
    BF_FaceMarker,
    BF_FingerMarker,
    BF_SkinningSettings,
    BF_RetargetBoneMapping,
    BF_AutoRigSession,
)


def register():
    """Register session PropertyGroups and scene pointer.

    Individual class registrations are wrapped in try/except so that a
    'already registered' RuntimeError on add-on reload does not abort
    the function before the PointerProperty is attached to the Scene.
    """
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except RuntimeError:
            pass  # Already registered from a previous load.

    # Always (re-)assign; harmless if already present.
    bpy.types.Scene.boneforge_autorig_session = PointerProperty(
        type=BF_AutoRigSession,
    )


def unregister():
    """Unregister session PropertyGroups and scene pointer."""
    if hasattr(bpy.types.Scene, 'boneforge_autorig_session'):
        del bpy.types.Scene.boneforge_autorig_session

    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
