"""BoneCraft VRChat — Naming Convention Detector.

Scans the top 12 structurally significant bones of an armature
and scores them against all known naming conventions. Reports the
detected convention, ambiguity, and detection confidence.

Category: VRChat Naming.
"""

import bpy
from bpy.types import Operator, Panel

from boneforge.core import active_armature, write_custom_json, read_custom_json
from boneforge.i18n import T


# ── Convention Database ──────────────────────────────────────────

KNOWN_CONVENTIONS = {
    "MMD": {
        "hips": ["センター", "Center"],
        "spine": ["上半身", "Upper Body"],
        "chest": ["上半身2", "Upper Body 2"],
        "neck": ["首", "Neck"],
        "head": ["頭", "Head"],
        "left_upper_arm": ["左腕", "Left Arm"],
        "right_upper_arm": ["右腕", "Right Arm"],
        "left_upper_leg": ["左足", "Left Leg"],
        "right_upper_leg": ["右足", "Right Leg"],
        "left_hand": ["左手首", "Left Wrist"],
        "right_hand": ["右手首", "Right Wrist"],
    },
    "Mixamo": {
        "hips": ["mixamorig:Hips"],
        "spine": ["mixamorig:Spine"],
        "chest": ["mixamorig:Spine1", "mixamorig:Spine2"],
        "neck": ["mixamorig:Neck"],
        "head": ["mixamorig:Head"],
        "left_upper_arm": ["mixamorig:LeftShoulder", "mixamorig:LeftArm"],
        "right_upper_arm": ["mixamorig:RightShoulder", "mixamorig:RightArm"],
        "left_upper_leg": ["mixamorig:LeftUpLeg"],
        "right_upper_leg": ["mixamorig:RightUpLeg"],
        "left_hand": ["mixamorig:LeftHand"],
        "right_hand": ["mixamorig:RightHand"],
    },
    "Rigify": {
        "hips": ["DEF-spine", "DEF-hips"],
        "spine": ["DEF-spine.001"],
        "chest": ["DEF-spine.002", "DEF-chest"],
        "neck": ["DEF-spine.003", "DEF-neck"],
        "head": ["DEF-head"],
        "left_upper_arm": ["DEF-upper_arm.L"],
        "right_upper_arm": ["DEF-upper_arm.R"],
        "left_upper_leg": ["DEF-upper_leg.L"],
        "right_upper_leg": ["DEF-upper_leg.R"],
        "left_hand": ["DEF-hand.L"],
        "right_hand": ["DEF-hand.R"],
    },
    "VRoid": {
        "hips": ["J_Bip_C_Hips"],
        "spine": ["J_Bip_C_Spine"],
        "chest": ["J_Bip_C_Chest"],
        "neck": ["J_Bip_C_Neck"],
        "head": ["J_Bip_C_Head"],
        "left_upper_arm": ["J_Bip_L_UpperArm"],
        "right_upper_arm": ["J_Bip_R_UpperArm"],
        "left_upper_leg": ["J_Bip_L_UpperLeg"],
        "right_upper_leg": ["J_Bip_R_UpperLeg"],
        "left_hand": ["J_Bip_L_Hand"],
        "right_hand": ["J_Bip_R_Hand"],
    },
    "Unity Humanoid": {
        "hips": ["Hips"],
        "spine": ["Spine"],
        "chest": ["Chest"],
        "neck": ["Neck"],
        "head": ["Head"],
        "left_upper_arm": ["LeftUpperArm"],
        "right_upper_arm": ["RightUpperArm"],
        "left_upper_leg": ["LeftUpperLeg"],
        "right_upper_leg": ["RightUpperLeg"],
        "left_hand": ["LeftHand"],
        "right_hand": ["RightHand"],
    },
}

# ── Cache Key ────────────────────────────────────────────────────

_CACHE_KEY = "boneforge_vrchat_naming_convention"

# Minimum score required to consider a convention detected (out of 24 max)
DETECTION_SCORE_THRESHOLD = 8

# Maximum score difference to flag ambiguity between top candidates
AMBIGUITY_SCORE_MARGIN = 2


# ── Detection Functions ──────────────────────────────────────────

def _get_12_significant_bones(armature_data):
    """
    Get the top 12 structurally significant bones from an armature.

    B-09: Instead of searching bone collections (which most armatures
    don't use), directly iterate all bones and match them against all
    known convention names. Returns a dict mapping slot names to bone
    names found in the armature.
    """
    all_bone_names = [bone.name for bone in armature_data.bones]
    if not all_bone_names:
        return {}

    # Build a reverse lookup: for each bone name, check which slot it
    # could fill across ALL conventions
    slot_candidates = {}

    for conv_name, conv_slots in KNOWN_CONVENTIONS.items():
        for slot, expected_names in conv_slots.items():
            for bone_name in all_bone_names:
                if bone_name in expected_names:
                    # Exact match — strongest signal
                    if slot not in slot_candidates:
                        slot_candidates[slot] = bone_name
                else:
                    # Partial / case-insensitive check
                    for expected in expected_names:
                        if (expected.lower() in bone_name.lower() or
                                bone_name.lower() in expected.lower()):
                            if slot not in slot_candidates:
                                slot_candidates[slot] = bone_name
                            break

    return slot_candidates


def _score_convention(bone_names_dict, convention_name: str) -> int:
    """
    Score an armature against a single convention.
    Max score = 24 (12 slots × 2 points for exact match).
    Exact match = 2 points.
    Partial match (contains key term) = 1 point.
    No match = 0.
    """
    convention = KNOWN_CONVENTIONS.get(convention_name, {})
    score = 0

    for slot, bone_name in bone_names_dict.items():
        if bone_name is None:
            continue

        expected_names = convention.get(slot, [])
        if not expected_names:
            continue

        # Check for exact match
        if bone_name in expected_names:
            score += 2
        else:
            # Check for partial match (contains any key term)
            for expected in expected_names:
                if expected.lower() in bone_name.lower() or bone_name.lower() in expected.lower():
                    score += 1
                    break

    return score


def detect_convention(armature, force_rescan=False, write_cache=True):
    """
    Detect the naming convention used in an armature.

    Returns:
        tuple: (convention_name, score, ambiguous_list)
        - convention_name: str or None
        - score: int (highest score)
        - ambiguous_list: list of (name, score) tuples for close scores
    """
    # Check cache if not forced
    if not force_rescan:
        cached = read_custom_json(armature, _CACHE_KEY)
        if cached is not None:
            return tuple(cached)

    # Get the 12 significant bones
    bone_names = _get_12_significant_bones(armature.data)

    # Score against all conventions
    scores = {}
    for conv_name in KNOWN_CONVENTIONS.keys():
        scores[conv_name] = _score_convention(bone_names, conv_name)

    # Find best score
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    if not sorted_scores or sorted_scores[0][1] < DETECTION_SCORE_THRESHOLD:
        # Below threshold
        result = [None, 0, []]
    else:
        best_name, best_score = sorted_scores[0]

        # Check for ambiguity (within margin)
        ambiguous = []
        for name, score in sorted_scores[1:]:
            if best_score - score <= AMBIGUITY_SCORE_MARGIN and score > 0:
                ambiguous.append([name, score])
            else:
                break

        result = [best_name, best_score, ambiguous]

    # Cache result — skip during draw context (Blender forbids writing
    # to ID datablocks while a Panel.draw is running).
    if write_cache:
        try:
            write_custom_json(armature, _CACHE_KEY, result)
        except AttributeError:
            # "Writing to ID classes in this context is not allowed" —
            # we're being called from a draw path; silently skip caching.
            pass

    return tuple(result)


# ── Operator ─────────────────────────────────────────────────────

class BF_OT_VRC_DetectConvention(Operator):
    """Detect the bone naming convention used in the active armature"""
    bl_idname = "boneforge.vrc_detect_convention"
    bl_label = "Detect Naming Convention"
    bl_options = {"REGISTER", "UNDO"}

    force_rescan: bpy.props.BoolProperty(
        name="Force Rescan",
        description="Clear cache and re-scan all bones",
        default=False,
    )

    def execute(self, context):
        arm = active_armature(context)
        if arm is None:
            self.report({'WARNING'}, "No active armature")
            return {'CANCELLED'}

        # M-06: Clear stale cache before re-detecting
        if _CACHE_KEY in arm:
            del arm[_CACHE_KEY]

        convention, score, ambiguous = detect_convention(arm, force_rescan=self.force_rescan)

        if convention is None:
            self.report({'INFO'},
                       f"Unrecognized convention (score {score} < 8 threshold)")
        else:
            msg = f"Detected: {convention} (score {score}/24)"
            if ambiguous:
                alt = ", ".join([f"{n} ({s})" for n, s in ambiguous])
                msg += f" — ambiguous with: {alt}"
            self.report({'INFO'}, msg)

        return {'FINISHED'}


class BONEFORGE_PT_vrc_naming_status(Panel):
    """Naming convention detection status panel."""

    bl_label = " "
    bl_idname = "BONEFORGE_PT_vrc_naming_status"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_parent_id = "BONEFORGE_PT_vrc_main"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        self.layout.label(text=T("Naming Convention"))

    @classmethod
    def poll(cls, context):
        return active_armature(context) is not None

    def draw(self, context):
        layout = self.layout
        arm = active_armature(context)
        if not arm:
            return

        # Show cached detection result if available
        cached = arm.get(_CACHE_KEY, None)
        if cached:
            layout.label(text=f"Detected: {cached}", icon="CHECKMARK")
        else:
            layout.label(text=T("Not yet detected"), icon="QUESTION")

        layout.operator("boneforge.vrc_detect_convention", text=T("Detect Convention"))


# ── Panel ────────────────────────────────────────────────────────

class BONEFORGE_PT_vrc_naming_detect(Panel):
    """Convention detection panel"""
    bl_label = " "
    bl_idname = "BONEFORGE_PT_vrc_naming_detect"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BoneCraft"

    def draw_header(self, context):
        self.layout.label(text=T("Convention Detection"))

    @classmethod
    def poll(cls, context):
        # Suppressed from Tool tab — displayed via BoneForge tab VRChat hub.
        return False

    def draw(self, context):
        layout = self.layout
        arm = active_armature(context)
        if arm is None:
            layout.label(text=T("No active armature"))
            return

        # Show last detection result — read-only (no cache write in draw)
        convention, score, ambiguous = detect_convention(arm, write_cache=False)

        col = layout.column(align=True)
        if convention is None:
            col.label(text=T("Status: Unrecognized"), icon='INFO')
            col.label(text=f"Score: {score}/24 (threshold: 8)")
        else:
            col.label(text=f"Convention: {convention}", icon='CHECKMARK')
            col.label(text=f"Confidence: {score}/24")

            if ambiguous:
                col.separator()
                col.label(text=T("Ambiguous with:"), icon='WARNING')
                for name, alt_score in ambiguous:
                    col.label(text=f"  {name} ({alt_score})", icon='NONE')

        col.separator()
        col.operator("boneforge.vrc_detect_convention", text=T("Detect"),
                    icon='VIEWZOOM').force_rescan = False
        col.operator("boneforge.vrc_detect_convention", text=T("Force Rescan"),
                    icon='FILE_REFRESH').force_rescan = True


# ── Registration ─────────────────────────────────────────────────

_classes = [
    BF_OT_VRC_DetectConvention,
    BONEFORGE_PT_vrc_naming_status,
    BONEFORGE_PT_vrc_naming_detect,
]


def register():
    """Register detector module."""
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    """Unregister detector module."""
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
