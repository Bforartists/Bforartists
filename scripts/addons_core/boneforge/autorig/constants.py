"""BoneCraft Phase 3 — Named constants for auto-rigging.

Anatomical proportion ratios for deriving intermediate joint positions.
These defaults are based on standard anatomical proportion references
(Andrew Loomis figure construction, Bammes proportional studies).
Each ratio is a fraction along the respective limb vector measured
from the proximal marker.

All four are exposed as user-overridable FloatProperty fields in
addon preferences with reset-to-default buttons.
"""

# ── Proportion ratios ──────────────────────────────────────────

SHOULDER_RATIO = 0.18  # Neck base -> shoulder as fraction of total arm length
ELBOW_RATIO = 0.48     # Shoulder -> elbow as fraction of total arm length
HIP_RATIO = 0.10       # Pelvis center -> hip joint as fraction of leg length
KNEE_RATIO = 0.52      # Hip -> knee as fraction of leg length
TOE_RATIO = 0.40       # Foot extends forward from ankle; toe tip fraction
HEEL_RATIO = 0.15      # Heel extends backward from ankle; heel fraction


# ── Body marker definitions ────────────────────────────────────

BODY_MARKERS = (
    'HEAD_TOP',
    'NECK_BASE',
    'WRIST_LEFT',
    'WRIST_RIGHT',
    'ANKLE_LEFT',
    'ANKLE_RIGHT',
    'PELVIS',
    # Optional precision markers — placed manually for better accuracy,
    # otherwise auto-derived from the 7 core markers above.
    'SHOULDER_LEFT',
    'SHOULDER_RIGHT',
    'ELBOW_LEFT',
    'ELBOW_RIGHT',
    'HIP_LEFT',
    'HIP_RIGHT',
    'KNEE_LEFT',
    'KNEE_RIGHT',
    'TOE_LEFT',
    'TOE_RIGHT',
    'HEEL_LEFT',
    'HEEL_RIGHT',
)

BODY_MARKER_COUNT = len(BODY_MARKERS)

# The original 7 core markers required for basic rig generation.
# These must be confirmed before proceeding; the rest are optional.
REQUIRED_BODY_MARKERS = (
    'HEAD_TOP',
    'NECK_BASE',
    'WRIST_LEFT',
    'WRIST_RIGHT',
    'ANKLE_LEFT',
    'ANKLE_RIGHT',
    'PELVIS',
)

# Optional precision markers that override derived joint positions.
# Users can skip these; the system will compute them automatically.
OPTIONAL_BODY_MARKERS = (
    'SHOULDER_LEFT',
    'SHOULDER_RIGHT',
    'ELBOW_LEFT',
    'ELBOW_RIGHT',
    'HIP_LEFT',
    'HIP_RIGHT',
    'KNEE_LEFT',
    'KNEE_RIGHT',
    'TOE_LEFT',
    'TOE_RIGHT',
    'HEEL_LEFT',
    'HEEL_RIGHT',
)

# Symmetry pairs: (left_marker, right_marker).  Non-paired markers
# (HEAD_TOP, NECK_BASE, PELVIS) are not in this tuple.
BODY_SYMMETRY_PAIRS = (
    ('WRIST_LEFT', 'WRIST_RIGHT'),
    ('ANKLE_LEFT', 'ANKLE_RIGHT'),
    ('SHOULDER_LEFT', 'SHOULDER_RIGHT'),
    ('ELBOW_LEFT', 'ELBOW_RIGHT'),
    ('HIP_LEFT', 'HIP_RIGHT'),
    ('KNEE_LEFT', 'KNEE_RIGHT'),
    ('TOE_LEFT', 'TOE_RIGHT'),
    ('HEEL_LEFT', 'HEEL_RIGHT'),
)


# ── Facial marker definitions ─────────────────────────────────

FACE_MARKERS = (
    'BROW_LEFT',
    'BROW_RIGHT',
    'EYE_LEFT',
    'EYE_RIGHT',
    'NOSE_TIP',
    'CHEEK_LEFT',
    'CHEEK_RIGHT',
    'UPPER_LIP',
    'LOWER_LIP',
    'CHIN',
    'JAW_LEFT',
    'JAW_RIGHT',
)

FACE_MARKER_COUNT = len(FACE_MARKERS)

FACE_SYMMETRY_PAIRS = (
    ('BROW_LEFT', 'BROW_RIGHT'),
    ('EYE_LEFT', 'EYE_RIGHT'),
    ('CHEEK_LEFT', 'CHEEK_RIGHT'),
    ('JAW_LEFT', 'JAW_RIGHT'),
)


# ── Derived joint names ───────────────────────────────────────

DERIVED_JOINTS = (
    'SHOULDER_LEFT',
    'SHOULDER_RIGHT',
    'ELBOW_LEFT',
    'ELBOW_RIGHT',
    'HIP_LEFT',
    'HIP_RIGHT',
    'KNEE_LEFT',
    'KNEE_RIGHT',
    'TOE_LEFT',
    'TOE_RIGHT',
    'HEEL_LEFT',
    'HEEL_RIGHT',
)


# ── Rig type enum items for EnumProperty ──────────────────────

RIG_TYPE_ITEMS = [
    ('BODY_AND_FACE', "Body + Face", "Generate both body and facial rig"),
    ('BODY_ONLY', "Body Only", "Generate body rig without facial controls"),
    ('FACE_ONLY', "Face Only", "Generate facial rig only (requires existing armature)"),
]


# ── Wizard steps ──────────────────────────────────────────────

STEP_INACTIVE = 0
STEP_SELECT_MESH = 1
STEP_RIG_TYPE = 2
STEP_BODY_MARKERS = 3
STEP_FINGER_MARKERS = 4
STEP_FACE_MARKERS = 5
STEP_REVIEW = 6
STEP_GENERATE = 7
STEP_DONE = 8

STEP_LABELS = {
    STEP_INACTIVE: "Inactive",
    STEP_SELECT_MESH: "Select Mesh",
    STEP_RIG_TYPE: "Rig Type",
    STEP_BODY_MARKERS: "Body Markers",
    STEP_FINGER_MARKERS: "Finger Markers",
    STEP_FACE_MARKERS: "Face Markers",
    STEP_REVIEW: "Review",
    STEP_GENERATE: "Generate",
    STEP_DONE: "Done",
}


# ── Rigify-compatible bone naming ─────────────────────────────
# Used by body_gen.py so Phase 2 rigify_enhance recognises the rig.

BODY_BONE_NAMES = {
    'spine': 'spine',
    'spine_001': 'spine.001',
    'spine_002': 'spine.002',
    'spine_003': 'spine.003',
    'spine_004': 'spine.004',
    'spine_005': 'spine.005',
    'spine_006': 'spine.006',
    'spine_007': 'spine.007',
    'upper_arm_L': 'upper_arm.L',
    'forearm_L': 'forearm.L',
    'hand_L': 'hand.L',
    'hand_ik_L': 'hand_ik.L',
    'upper_arm_R': 'upper_arm.R',
    'forearm_R': 'forearm.R',
    'hand_R': 'hand.R',
    'hand_ik_R': 'hand_ik.R',
    'thigh_L': 'thigh.L',
    'shin_L': 'shin.L',
    'foot_L': 'foot.L',
    'foot_ik_L': 'foot_ik.L',
    'thigh_R': 'thigh.R',
    'shin_R': 'shin.R',
    'foot_R': 'foot.R',
    'foot_ik_R': 'foot_ik.R',
    'toe_L': 'toe.L',
    'toe_R': 'toe.R',
    'heel_L': 'heel.L',
    'heel_R': 'heel.R',
    'head': 'head',
    'neck': 'neck',
    'neck_001': 'neck.001',
    'neck_002': 'neck.002',
    'neck_003': 'neck.003',
}


# ── Facial shape key names ────────────────────────────────────
# Created by face_gen.py and optionally wired by Phase 2 correctives.

FACE_SHAPE_KEY_NAMES = (
    'blink_L',
    'blink_R',
    'brow_raise_L',
    'brow_raise_R',
    'brow_furrow',
    'smile',
    'jaw_open',
    'cheek_puff',
    'squint',
)


# ── Bone collection names ────────────────────────────────────

BODY_IK_COLLECTION = "Body IK"
BODY_FK_COLLECTION = "Body FK"
BODY_DEFORM_COLLECTION = "Body Deform"
FACE_CONTROLS_COLLECTION = "Face Controls"
FACE_DEFORM_COLLECTION = "Face Deform"
FINGER_DEFORM_COLLECTION = "Finger Deform"

BONE_COLLECTION_NAMES = (
    BODY_IK_COLLECTION,
    BODY_FK_COLLECTION,
    BODY_DEFORM_COLLECTION,
    FACE_CONTROLS_COLLECTION,
    FACE_DEFORM_COLLECTION,
    FINGER_DEFORM_COLLECTION,
)


# ── Staging collection for atomic generation ──────────────────

STAGING_COLLECTION_NAME = "_boneforge_staging"


# ── Retarget bone matching: Mixamo name mapping ──────────────

# ── Skinning pipeline constants (Phase 3B) ───────────────────

# Corrective presets for known problem areas in automatic weight painting.
# Each preset targets a specific anatomical joint and applies a correction
# method to improve deformation quality.
CORRECTIVE_PRESETS = {
    'shoulder': {
        'description': (
            "Smooth transition from trapezius to deltoid. "
            "Prevents the common 'candy wrapper' twist artifact."
        ),
        'affected_bones': [
            'upper_arm.L', 'upper_arm.R',
            'shoulder.L', 'shoulder.R',
            # Expanded v3.0.9 — catch armpit bleed into upper spine.
            'spine', 'spine.001',
        ],
        'method': 'gradient_blend',
        'parameters': {'blend_width': 0.15, 'falloff': 'SMOOTH'},
    },
    'elbow': {
        'description': (
            "Sharpen flexor/extensor split at the elbow. "
            "Prevents forearm twisting from bleeding into upper arm."
        ),
        'affected_bones': ['forearm.L', 'forearm.R', 'upper_arm.L', 'upper_arm.R'],
        'method': 'gradient_blend',
        'parameters': {'blend_width': 0.10, 'falloff': 'SHARP'},
    },
    'hip': {
        'description': (
            "Clean inner thigh weight bleeding. Prevents "
            "leg movement from pulling on the opposite leg."
        ),
        # v8.6.7: the whole leg, not just the thigh — envelope/heat weights
        # let inner-shin and foot vertices pick up the other leg too.
        # (Unsided bones such as 'spine' are never clipped.)
        'affected_bones': ['thigh.L', 'thigh.R', 'shin.L', 'shin.R',
                           'foot.L', 'foot.R', 'toe.L', 'toe.R',
                           'heel.L', 'heel.R', 'spine'],
        'method': 'midplane_clip',
        'parameters': {'clip_axis': 'X', 'blend_margin': 0.05},
    },
    'knee': {
        'description': (
            "Refine quad/hamstring boundary at the knee. "
            "Prevents the 'collapsing knee' artifact on flex."
        ),
        'affected_bones': ['shin.L', 'shin.R', 'thigh.L', 'thigh.R'],
        'method': 'gradient_blend',
        'parameters': {'blend_width': 0.10, 'falloff': 'SHARP'},
    },
    # v3.0.9: tight per-segment falloffs keep finger animation crisp
    # without bleed from adjacent fingers on humanoid/VRChat avatars.
    'finger_thumb': {
        'description': (
            "Tight thumb segment boundaries. Prevents thumb weight "
            "from bleeding into index finger on humanoid avatars."
        ),
        'affected_bones': [
            'thumb.01.L', 'thumb.02.L', 'thumb.03.L',
            'thumb.01.R', 'thumb.02.R', 'thumb.03.R',
        ],
        'method': 'gradient_blend',
        'parameters': {'blend_width': 0.03, 'falloff': 'SHARP'},
    },
    'finger_digits': {
        'description': (
            "Tight individual finger boundaries. Keeps index/middle/"
            "ring/pinky from cross-bleeding on clenched fists."
        ),
        'affected_bones': [
            'f_index.01.L', 'f_index.02.L', 'f_index.03.L',
            'f_middle.01.L', 'f_middle.02.L', 'f_middle.03.L',
            'f_ring.01.L', 'f_ring.02.L', 'f_ring.03.L',
            'f_pinky.01.L', 'f_pinky.02.L', 'f_pinky.03.L',
            'f_index.01.R', 'f_index.02.R', 'f_index.03.R',
            'f_middle.01.R', 'f_middle.02.R', 'f_middle.03.R',
            'f_ring.01.R', 'f_ring.02.R', 'f_ring.03.R',
            'f_pinky.01.R', 'f_pinky.02.R', 'f_pinky.03.R',
        ],
        'method': 'gradient_blend',
        'parameters': {'blend_width': 0.03, 'falloff': 'SHARP'},
    },
}

# Quality score thresholds for the skinning quality report.
QUALITY_SCORE_PRODUCTION = 0.85   # Above this: production-ready
QUALITY_SCORE_ACCEPTABLE = 0.65   # Above this: acceptable with touch-up

# Mesh validation: maximum ratio of non-manifold edges before auto-weights
# are expected to fail.  Meshes above 5% non-manifold skip ARMATURE_AUTO.
NON_MANIFOLD_AUTO_WEIGHT_THRESHOLD = 0.05

# Weight discontinuity threshold for quality scoring.  Adjacent vertices
# whose dominant bone weight differs by more than this are flagged.
WEIGHT_DISCONTINUITY_THRESHOLD = 0.3

# Minimum face area below which a face is considered degenerate.
ZERO_AREA_THRESHOLD = 1e-8

# Face region radius multiplier: the face isolation radius is this
# times the maximum distance from face centroid to any face marker.
# Raised from 1.5 → 2.0 so the ear/jaw ring isn't clipped off on
# stock VRoid-style humanoid avatars (red-team v3.0.9).
FACE_RADIUS_MULTIPLIER = 2.0

# Minimum weight value considered non-zero.  Weights below this are
# treated as zero for normalization and scoring.
# Raised from 1e-6 → 1e-4 so genuinely-small-but-real finger and
# eyelid weights aren't crushed to zero after sharpen (red-team v3.0.9).
MIN_WEIGHT_EPSILON = 1e-4


# ── Retarget bone matching: Mixamo name mapping ──────────────

# ── Finger marker definitions ─────────────────────────────────

# Maximum finger markers per hand (all counts use a subset of this list).
# The first 2 are shared by all non-zero counts; the rest are added as
# the finger count increases.
FINGER_MARKERS_ALL = (
    'FINGER_PALM_L',
    'FINGER_THUMB_TIP_L',
    'FINGER_THUMB_BASE_L',
    'FINGER_INDEX_TIP_L',
    'FINGER_INDEX_BASE_L',
    'FINGER_MIDDLE_TIP_L',
    'FINGER_MIDDLE_BASE_L',
    'FINGER_RING_TIP_L',
    'FINGER_RING_BASE_L',
    'FINGER_PINKY_TIP_L',
    'FINGER_PINKY_BASE_L',
)

# Marker sets per finger count (left hand only; right is mirrored).
FINGER_MARKERS_BY_COUNT = {
    0: (),
    1: ('FINGER_PALM_L', 'FINGER_TIP_L'),
    2: ('FINGER_PALM_L', 'FINGER_THUMB_TIP_L',
        'FINGER_THUMB_BASE_L', 'FINGER_INDEX_TIP_L'),
    3: ('FINGER_PALM_L', 'FINGER_THUMB_TIP_L', 'FINGER_THUMB_BASE_L',
        'FINGER_INDEX_TIP_L', 'FINGER_INDEX_BASE_L', 'FINGER_PINKY_TIP_L'),
    5: ('FINGER_PALM_L',
        'FINGER_THUMB_TIP_L', 'FINGER_THUMB_BASE_L',
        'FINGER_INDEX_TIP_L', 'FINGER_INDEX_BASE_L',
        'FINGER_MIDDLE_TIP_L', 'FINGER_MIDDLE_BASE_L',
        'FINGER_RING_TIP_L', 'FINGER_RING_BASE_L',
        'FINGER_PINKY_TIP_L', 'FINGER_PINKY_BASE_L'),
}

# Right-hand equivalents are generated by replacing _L with _R.
FINGER_MARKERS_MAX_COUNT = len(FINGER_MARKERS_ALL)

# Symmetry pairs for finger markers (left, right).
FINGER_SYMMETRY_PAIRS = tuple(
    (name, name.replace('_L', '_R'))
    for name in FINGER_MARKERS_ALL
)

# Display labels for finger markers (user-friendly names).
FINGER_MARKER_LABELS = {
    'FINGER_PALM': "Palm",
    'FINGER_TIP': "Finger Tip",
    'FINGER_THUMB_TIP': "Thumb Tip",
    'FINGER_THUMB_BASE': "Thumb Base",
    'FINGER_INDEX_TIP': "Index Tip",
    'FINGER_INDEX_BASE': "Index Base",
    'FINGER_MIDDLE_TIP': "Middle Tip",
    'FINGER_MIDDLE_BASE': "Middle Base",
    'FINGER_RING_TIP': "Ring Tip",
    'FINGER_RING_BASE': "Ring Base",
    'FINGER_PINKY_TIP': "Pinky Tip",
    'FINGER_PINKY_BASE': "Pinky Base",
}

# Valid finger count choices (matching Mixamo).
# Labels are written from the user's mental model:
#   0 → no finger bones at all; wrist is terminal.
#   1 → single "sock puppet" bone covering the whole hand (one bone
#       that animates as one unit; structurally one bone more than 0).
#   2 → "mitten": thumb + four-finger group (two bones total).
#   3 → "mitten + index": thumb, index, and a group for the remaining
#       three fingers.
#   5 → full individual human hand (3 bones per finger).
FINGER_COUNT_ITEMS = [
    (0, "No Fingers",
     "Wrist is a terminal bone. No finger bones generated"),
    (1, "Sock Puppet",
     "One extra bone covering the entire hand as a single unit"),
    (2, "Mitten",
     "Thumb plus a single bone covering the four remaining fingers"),
    (3, "Mitten + Index",
     "Thumb, index finger, plus a single bone covering the remaining three fingers"),
    (5, "Full Human Hand",
     "Full individual finger set, 3 bones per finger"),
]

# ── Finger bone names (Rigify convention) ────────────────────

FINGER_BONE_NAMES_5 = {
    'thumb': ('thumb.01.{side}', 'thumb.02.{side}', 'thumb.03.{side}'),
    'index': ('f_index.01.{side}', 'f_index.02.{side}', 'f_index.03.{side}'),
    'middle': ('f_middle.01.{side}', 'f_middle.02.{side}', 'f_middle.03.{side}'),
    'ring': ('f_ring.01.{side}', 'f_ring.02.{side}', 'f_ring.03.{side}'),
    'pinky': ('f_pinky.01.{side}', 'f_pinky.02.{side}', 'f_pinky.03.{side}'),
}

# Unity humanoid finger bone name mapping for VRChat.
FINGER_UNITY_MAPPING = {
    'thumb.01.L': 'LeftThumbProximal',
    'thumb.02.L': 'LeftThumbIntermediate',
    'thumb.03.L': 'LeftThumbDistal',
    'f_index.01.L': 'LeftIndexProximal',
    'f_index.02.L': 'LeftIndexIntermediate',
    'f_index.03.L': 'LeftIndexDistal',
    'f_middle.01.L': 'LeftMiddleProximal',
    'f_middle.02.L': 'LeftMiddleIntermediate',
    'f_middle.03.L': 'LeftMiddleDistal',
    'f_ring.01.L': 'LeftRingProximal',
    'f_ring.02.L': 'LeftRingIntermediate',
    'f_ring.03.L': 'LeftRingDistal',
    'f_pinky.01.L': 'LeftLittleProximal',
    'f_pinky.02.L': 'LeftLittleIntermediate',
    'f_pinky.03.L': 'LeftLittleDistal',
    'thumb.01.R': 'RightThumbProximal',
    'thumb.02.R': 'RightThumbIntermediate',
    'thumb.03.R': 'RightThumbDistal',
    'f_index.01.R': 'RightIndexProximal',
    'f_index.02.R': 'RightIndexIntermediate',
    'f_index.03.R': 'RightIndexDistal',
    'f_middle.01.R': 'RightMiddleProximal',
    'f_middle.02.R': 'RightMiddleIntermediate',
    'f_middle.03.R': 'RightMiddleDistal',
    'f_ring.01.R': 'RightRingProximal',
    'f_ring.02.R': 'RightRingIntermediate',
    'f_ring.03.R': 'RightRingDistal',
    'f_pinky.01.R': 'RightLittleProximal',
    'f_pinky.02.R': 'RightLittleIntermediate',
    'f_pinky.03.R': 'RightLittleDistal',
}

# Intermediate knuckle position as fraction of base-to-tip vector.
FINGER_INTERMEDIATE_RATIO = 0.55

# Index-to-tip fraction for deriving base knuckle in 2-finger mode.
FINGER_GROUP_BASE_RATIO = 0.40


MIXAMO_TO_RIGIFY = {
    'mixamorig:Hips': 'spine',
    'mixamorig:Spine': 'spine.001',
    'mixamorig:Spine1': 'spine.002',
    'mixamorig:Spine2': 'spine.003',
    'mixamorig:Neck': 'neck',
    'mixamorig:Head': 'head',
    'mixamorig:LeftShoulder': 'shoulder.L',
    'mixamorig:LeftArm': 'upper_arm.L',
    'mixamorig:LeftForeArm': 'forearm.L',
    'mixamorig:LeftHand': 'hand.L',
    'mixamorig:RightShoulder': 'shoulder.R',
    'mixamorig:RightArm': 'upper_arm.R',
    'mixamorig:RightForeArm': 'forearm.R',
    'mixamorig:RightHand': 'hand.R',
    'mixamorig:LeftUpLeg': 'thigh.L',
    'mixamorig:LeftLeg': 'shin.L',
    'mixamorig:LeftFoot': 'foot.L',
    'mixamorig:LeftToeBase': 'toe.L',
    'mixamorig:RightUpLeg': 'thigh.R',
    'mixamorig:RightLeg': 'shin.R',
    'mixamorig:RightFoot': 'foot.R',
    'mixamorig:RightToeBase': 'toe.R',
}
