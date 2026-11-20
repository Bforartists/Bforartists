"""MMD Japanese bone name → Unity humanoid standard rename.

Reads the active armature and renames every bone that matches a known
Japanese MMD bone name to the VRChat / Unity humanoid equivalent.
Non-matching bones are left alone. Stores original names as custom
properties on each renamed bone plus a full receipt on the armature.

Translation receipt keys (stored under ``boneforge_mmd_rename_receipt``):
    converted       — list of [old, new] pairs
    skipped         — bones already carrying a Unity name
    needs_manual    — bones with no known mapping (first 30)
    total           — total bone count before rename
"""

import bpy
from bpy.types import Operator

import logging

logger = logging.getLogger(__name__)

# ── Lookup table ────────────────────────────────────────────────

_MMD_TO_UNITY: dict[str, str] = {
    # Root helpers (non-humanoid but commonly present)
    "全ての親":     "Root",
    "センター":     "Center",
    "グルーブ":     "Groove",
    # Core spine chain
    "腰":           "Hips",
    "上半身":       "Spine",
    "上半身2":      "Chest",
    "上半身3":      "UpperChest",
    "首":           "Neck",
    "頭":           "Head",
    # Eyes / jaw
    "左目":         "LeftEye",
    "右目":         "RightEye",
    "口":           "Jaw",
    # Shoulders & arms
    "左肩":         "LeftShoulder",
    "左腕":         "LeftUpperArm",
    "左ひじ":       "LeftLowerArm",
    "左手首":       "LeftHand",
    "右肩":         "RightShoulder",
    "右腕":         "RightUpperArm",
    "右ひじ":       "RightLowerArm",
    "右手首":       "RightHand",
    # Legs
    "左足":         "LeftUpperLeg",
    "左ひざ":       "LeftLowerLeg",
    "左足首":       "LeftFoot",
    "左つま先":     "LeftToes",
    "右足":         "RightUpperLeg",
    "右ひざ":       "RightLowerLeg",
    "右足首":       "RightFoot",
    "右つま先":     "RightToes",
    # Left hand fingers
    "左親指０":     "LeftThumbProximal",
    "左親指１":     "LeftThumbIntermediate",
    "左親指２":     "LeftThumbDistal",
    "左人指１":     "LeftIndexProximal",
    "左人指２":     "LeftIndexIntermediate",
    "左人指３":     "LeftIndexDistal",
    "左中指１":     "LeftMiddleProximal",
    "左中指２":     "LeftMiddleIntermediate",
    "左中指３":     "LeftMiddleDistal",
    "左薬指１":     "LeftRingProximal",
    "左薬指２":     "LeftRingIntermediate",
    "左薬指３":     "LeftRingDistal",
    "左小指１":     "LeftLittleProximal",
    "左小指２":     "LeftLittleIntermediate",
    "左小指３":     "LeftLittleDistal",
    # Right hand fingers
    "右親指０":     "RightThumbProximal",
    "右親指１":     "RightThumbIntermediate",
    "右親指２":     "RightThumbDistal",
    "右人指１":     "RightIndexProximal",
    "右人指２":     "RightIndexIntermediate",
    "右人指３":     "RightIndexDistal",
    "右中指１":     "RightMiddleProximal",
    "右中指２":     "RightMiddleIntermediate",
    "右中指３":     "RightMiddleDistal",
    "右薬指１":     "RightRingProximal",
    "右薬指２":     "RightRingIntermediate",
    "右薬指３":     "RightRingDistal",
    "右小指１":     "RightLittleProximal",
    "右小指２":     "RightLittleIntermediate",
    "右小指３":     "RightLittleDistal",
    # IK helpers
    "左足IK":       "LeftFootIK",
    "右足IK":       "RightFootIK",
    "左つま先IK":   "LeftToesIK",
    "右つま先IK":   "RightToesIK",
    "左足IK親":     "LeftFootIKParent",
    "右足IK親":     "RightFootIKParent",
    # Twist helpers (common in MMD rigs)
    "左腕捩":       "LeftArmTwist",
    "右腕捩":       "RightArmTwist",
    "左手捩":       "LeftHandTwist",
    "右手捩":       "RightHandTwist",
    "左足捩":       "LeftLegTwist",
    "右足捩":       "RightLegTwist",
}

_UNITY_NAMES = set(_MMD_TO_UNITY.values())


# ── Operator ─────────────────────────────────────────────────────

class BF_OT_MMDConvertBoneNames(Operator):
    """Rename Japanese MMD bone names to Unity humanoid standard."""

    bl_idname  = "boneforge.mmd_convert_bone_names"
    bl_label   = "Convert MMD Bone Names"
    bl_description = (
        "Rename Japanese MMD bone names (センター, 頭, 左腕…) to Unity "
        "humanoid standard (Head, LeftUpperArm…) for VRChat SDK "
        "compatibility. Original names saved as bone custom properties."
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == "ARMATURE"

    def execute(self, context):
        arm_obj = context.active_object
        converted  = []
        skipped    = []
        needs_manual = []

        bones = arm_obj.data.bones
        total = len(bones)

        for bone in bones:
            old = bone.name
            new = _MMD_TO_UNITY.get(old)
            if new is None:
                if old in _UNITY_NAMES:
                    skipped.append(old)
                else:
                    needs_manual.append(old)
                continue
            # Store original name before renaming.
            bone["boneforge_mmd_original_name"] = old
            bone.name = new
            converted.append([old, new])
            logger.debug("[BoneCraft] MMD rename: %s → %s", old, new)

        receipt = {
            "converted":    converted,
            "skipped":      skipped,
            "needs_manual": needs_manual[:30],
            "total":        total,
        }
        from boneforge.core import write_custom_json
        write_custom_json(arm_obj, "boneforge_mmd_rename_receipt", receipt)

        self.report(
            {"INFO"},
            f"MMD bone rename: {len(converted)} converted, "
            f"{len(skipped)} already Unity-named, "
            f"{len(needs_manual)} need manual review — see armature custom props",
        )
        return {"FINISHED"}
