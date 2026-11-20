"""BoneCraft — Bone Merge Workspace.

Three-stage pipeline for merging two armatures with full skin weight preservation.

Stage 1 — Scope   : pick armatures, review bone diff, acknowledge complexity to proceed.
Stage 2 — Rename  : normalize both to a naming standard, resolve mismatches, mark uniques.
Stage 3 — Execute : dry-run preview → auto-backup → merge.

Unanimous modifications applied:
  [Borda-Unanimous] Non-destructive dry-run preview before any data is modified
  [Unanimous]       Auto-backup collection (timestamped) created before merge
  [Unanimous]       Atomic bone-rename + vertex-group propagation (one undo step)
  [Unanimous]       Complexity indicator in Stage 1
  [Unanimous]       Symmetric prefix strip — normalize applies to BOTH armatures simultaneously
"""

import re
import logging
from datetime import datetime

import bpy
from bpy.types import Operator, Panel, PropertyGroup, UIList
from bpy.props import (
    BoolProperty, CollectionProperty, EnumProperty,
    IntProperty, PointerProperty, StringProperty,
)

from boneforge.i18n import T

logger = logging.getLogger(__name__)


# ── Mixamo reference data ────────────────────────────────────────────

_MIXAMO_SHORT_TO_FULL: dict = {
    "Pelvis": "mixamorig:Hips",
    "Spine.Lower": "mixamorig:Spine",
    "Spine.Middle": "mixamorig:Spine1",
    "Spine.Upper": "mixamorig:Spine2",
    "Neck": "mixamorig:Neck",
    "Head": "mixamorig:Head",
    "Shoulder.L": "mixamorig:LeftShoulder",
    "UpperArm.L": "mixamorig:LeftArm",
    "Forearm.L": "mixamorig:LeftForeArm",
    "Hand.L": "mixamorig:LeftHand",
    "Shoulder.R": "mixamorig:RightShoulder",
    "UpperArm.R": "mixamorig:RightArm",
    "Forearm.R": "mixamorig:RightForeArm",
    "Hand.R": "mixamorig:RightHand",
    "Thigh.L": "mixamorig:LeftUpLeg",
    "Shin.L": "mixamorig:LeftLeg",
    "Foot.L": "mixamorig:LeftFoot",
    "Thigh.R": "mixamorig:RightUpLeg",
    "Shin.R": "mixamorig:RightLeg",
    "Foot.R": "mixamorig:RightFoot",
    "Thumb1.L": "mixamorig:LeftHandThumb1",
    "Thumb2.L": "mixamorig:LeftHandThumb2",
    "Thumb3.L": "mixamorig:LeftHandThumb3",
    "Index1.L": "mixamorig:LeftHandIndex1",
    "Index2.L": "mixamorig:LeftHandIndex2",
    "Index3.L": "mixamorig:LeftHandIndex3",
    "Middle1.L": "mixamorig:LeftHandMiddle1",
    "Middle2.L": "mixamorig:LeftHandMiddle2",
    "Middle3.L": "mixamorig:LeftHandMiddle3",
    "Ring1.L": "mixamorig:LeftHandRing1",
    "Ring2.L": "mixamorig:LeftHandRing2",
    "Ring3.L": "mixamorig:LeftHandRing3",
    "Pinky1.L": "mixamorig:LeftHandPinky1",
    "Pinky2.L": "mixamorig:LeftHandPinky2",
    "Pinky3.L": "mixamorig:LeftHandPinky3",
    "Thumb1.R": "mixamorig:RightHandThumb1",
    "Thumb2.R": "mixamorig:RightHandThumb2",
    "Thumb3.R": "mixamorig:RightHandThumb3",
    "Index1.R": "mixamorig:RightHandIndex1",
    "Index2.R": "mixamorig:RightHandIndex2",
    "Index3.R": "mixamorig:RightHandIndex3",
    "Middle1.R": "mixamorig:RightHandMiddle1",
    "Middle2.R": "mixamorig:RightHandMiddle2",
    "Middle3.R": "mixamorig:RightHandMiddle3",
    "Ring1.R": "mixamorig:RightHandRing1",
    "Ring2.R": "mixamorig:RightHandRing2",
    "Ring3.R": "mixamorig:RightHandRing3",
    "Pinky1.R": "mixamorig:RightHandPinky1",
    "Pinky2.R": "mixamorig:RightHandPinky2",
    "Pinky3.R": "mixamorig:RightHandPinky3",
    "Toe.L": "mixamorig:LeftToeBase",
    "Toe.R": "mixamorig:RightToeBase",
    "J_Bip_C_Hips": "mixamorig:Hips",
    "J_Bip_C_Spine": "mixamorig:Spine",
    "J_Bip_C_Chest": "mixamorig:Spine1",
    "J_Bip_C_UpperChest": "mixamorig:Spine2",
    "J_Bip_C_Neck": "mixamorig:Neck",
    "J_Bip_C_Head": "mixamorig:Head",
    "J_Bip_L_Shoulder": "mixamorig:LeftShoulder",
    "J_Bip_L_UpperArm": "mixamorig:LeftArm",
    "J_Bip_L_LowerArm": "mixamorig:LeftForeArm",
    "J_Bip_L_Hand": "mixamorig:LeftHand",
    "J_Bip_L_UpperLeg": "mixamorig:LeftUpLeg",
    "J_Bip_L_LowerLeg": "mixamorig:LeftLeg",
    "J_Bip_L_Foot": "mixamorig:LeftFoot",
    "J_Bip_L_ToeBase": "mixamorig:LeftToeBase",
    "J_Bip_R_Shoulder": "mixamorig:RightShoulder",
    "J_Bip_R_UpperArm": "mixamorig:RightArm",
    "J_Bip_R_LowerArm": "mixamorig:RightForeArm",
    "J_Bip_R_Hand": "mixamorig:RightHand",
    "J_Bip_R_UpperLeg": "mixamorig:RightUpLeg",
    "J_Bip_R_LowerLeg": "mixamorig:RightLeg",
    "J_Bip_R_Foot": "mixamorig:RightFoot",
    "J_Bip_R_ToeBase": "mixamorig:RightToeBase",
}


_COMMON_ALIAS_TO_FULL: dict = {
    # Generic, Unity Humanoid, VRM, HumanIK-style names.
    "Hip": "mixamorig:Hips",
    "Hips": "mixamorig:Hips",
    "Waist": "mixamorig:Hips",
    "Lower Body": "mixamorig:Hips",
    "Spine0": "mixamorig:Spine",
    "Spine1": "mixamorig:Spine1",
    "Spine2": "mixamorig:Spine2",
    "Spine01": "mixamorig:Spine",
    "Spine02": "mixamorig:Spine1",
    "Spine03": "mixamorig:Spine2",
    "Chest": "mixamorig:Spine1",
    "Upper Chest": "mixamorig:Spine2",
    "UpperBody": "mixamorig:Spine",
    "UpperBody2": "mixamorig:Spine1",
    "Neck1": "mixamorig:Neck",
    "Head1": "mixamorig:Head",

    # Blender Rigify generated deformation names.
    "DEF-hips": "mixamorig:Hips",
    "DEF-spine": "mixamorig:Spine",
    "DEF-spine.001": "mixamorig:Spine1",
    "DEF-spine.002": "mixamorig:Spine2",
    "DEF-neck": "mixamorig:Neck",
    "DEF-head": "mixamorig:Head",
    "DEF-shoulder.L": "mixamorig:LeftShoulder",
    "DEF-upper_arm.L": "mixamorig:LeftArm",
    "DEF-forearm.L": "mixamorig:LeftForeArm",
    "DEF-hand.L": "mixamorig:LeftHand",
    "DEF-thigh.L": "mixamorig:LeftUpLeg",
    "DEF-shin.L": "mixamorig:LeftLeg",
    "DEF-foot.L": "mixamorig:LeftFoot",
    "DEF-toe.L": "mixamorig:LeftToeBase",
    "DEF-shoulder.R": "mixamorig:RightShoulder",
    "DEF-upper_arm.R": "mixamorig:RightArm",
    "DEF-forearm.R": "mixamorig:RightForeArm",
    "DEF-hand.R": "mixamorig:RightHand",
    "DEF-thigh.R": "mixamorig:RightUpLeg",
    "DEF-shin.R": "mixamorig:RightLeg",
    "DEF-foot.R": "mixamorig:RightFoot",
    "DEF-toe.R": "mixamorig:RightToeBase",

    # Unreal / game-engine FBX style names.
    "pelvis": "mixamorig:Hips",
    "spine_01": "mixamorig:Spine",
    "spine_02": "mixamorig:Spine1",
    "spine_03": "mixamorig:Spine2",
    "neck_01": "mixamorig:Neck",
    "head": "mixamorig:Head",
    "clavicle_l": "mixamorig:LeftShoulder",
    "upperarm_l": "mixamorig:LeftArm",
    "lowerarm_l": "mixamorig:LeftForeArm",
    "hand_l": "mixamorig:LeftHand",
    "thigh_l": "mixamorig:LeftUpLeg",
    "calf_l": "mixamorig:LeftLeg",
    "foot_l": "mixamorig:LeftFoot",
    "ball_l": "mixamorig:LeftToeBase",
    "clavicle_r": "mixamorig:RightShoulder",
    "upperarm_r": "mixamorig:RightArm",
    "lowerarm_r": "mixamorig:RightForeArm",
    "hand_r": "mixamorig:RightHand",
    "thigh_r": "mixamorig:RightUpLeg",
    "calf_r": "mixamorig:RightLeg",
    "foot_r": "mixamorig:RightFoot",
    "ball_r": "mixamorig:RightToeBase",

    # Daz / Poser / Reallusion CC / 3ds Max Biped / Source-style names.
    "abdomenLower": "mixamorig:Spine",
    "abdomenUpper": "mixamorig:Spine1",
    "chestLower": "mixamorig:Spine1",
    "chestUpper": "mixamorig:Spine2",
    "lCollar": "mixamorig:LeftShoulder",
    "lShldr": "mixamorig:LeftArm",
    "lForeArm": "mixamorig:LeftForeArm",
    "lHand": "mixamorig:LeftHand",
    "lThigh": "mixamorig:LeftUpLeg",
    "lShin": "mixamorig:LeftLeg",
    "lFoot": "mixamorig:LeftFoot",
    "lToe": "mixamorig:LeftToeBase",
    "rCollar": "mixamorig:RightShoulder",
    "rShldr": "mixamorig:RightArm",
    "rForeArm": "mixamorig:RightForeArm",
    "rHand": "mixamorig:RightHand",
    "rThigh": "mixamorig:RightUpLeg",
    "rShin": "mixamorig:RightLeg",
    "rFoot": "mixamorig:RightFoot",
    "rToe": "mixamorig:RightToeBase",
    "CC_Base_Hip": "mixamorig:Hips",
    "CC_Base_Waist": "mixamorig:Spine",
    "CC_Base_Spine01": "mixamorig:Spine1",
    "CC_Base_Spine02": "mixamorig:Spine2",
    "CC_Base_NeckTwist01": "mixamorig:Neck",
    "CC_Base_Head": "mixamorig:Head",
    "CC_Base_L_Clavicle": "mixamorig:LeftShoulder",
    "CC_Base_L_Upperarm": "mixamorig:LeftArm",
    "CC_Base_L_Forearm": "mixamorig:LeftForeArm",
    "CC_Base_L_Hand": "mixamorig:LeftHand",
    "CC_Base_L_Thigh": "mixamorig:LeftUpLeg",
    "CC_Base_L_Calf": "mixamorig:LeftLeg",
    "CC_Base_L_Foot": "mixamorig:LeftFoot",
    "CC_Base_L_ToeBase": "mixamorig:LeftToeBase",
    "CC_Base_R_Clavicle": "mixamorig:RightShoulder",
    "CC_Base_R_Upperarm": "mixamorig:RightArm",
    "CC_Base_R_Forearm": "mixamorig:RightForeArm",
    "CC_Base_R_Hand": "mixamorig:RightHand",
    "CC_Base_R_Thigh": "mixamorig:RightUpLeg",
    "CC_Base_R_Calf": "mixamorig:RightLeg",
    "CC_Base_R_Foot": "mixamorig:RightFoot",
    "CC_Base_R_ToeBase": "mixamorig:RightToeBase",
    "Bip01 Pelvis": "mixamorig:Hips",
    "Bip01 Spine": "mixamorig:Spine",
    "Bip01 Spine1": "mixamorig:Spine1",
    "Bip01 Spine2": "mixamorig:Spine2",
    "Bip01 Neck": "mixamorig:Neck",
    "Bip01 Head": "mixamorig:Head",
    "Bip01 L Clavicle": "mixamorig:LeftShoulder",
    "Bip01 L UpperArm": "mixamorig:LeftArm",
    "Bip01 L Forearm": "mixamorig:LeftForeArm",
    "Bip01 L Hand": "mixamorig:LeftHand",
    "Bip01 L Thigh": "mixamorig:LeftUpLeg",
    "Bip01 L Calf": "mixamorig:LeftLeg",
    "Bip01 L Foot": "mixamorig:LeftFoot",
    "Bip01 L Toe0": "mixamorig:LeftToeBase",
    "Bip01 R Clavicle": "mixamorig:RightShoulder",
    "Bip01 R UpperArm": "mixamorig:RightArm",
    "Bip01 R Forearm": "mixamorig:RightForeArm",
    "Bip01 R Hand": "mixamorig:RightHand",
    "Bip01 R Thigh": "mixamorig:RightUpLeg",
    "Bip01 R Calf": "mixamorig:RightLeg",
    "Bip01 R Foot": "mixamorig:RightFoot",
    "Bip01 R Toe0": "mixamorig:RightToeBase",
    "ValveBiped.Bip01_Pelvis": "mixamorig:Hips",
    "ValveBiped.Bip01_Spine": "mixamorig:Spine",
    "ValveBiped.Bip01_Spine1": "mixamorig:Spine1",
    "ValveBiped.Bip01_Spine2": "mixamorig:Spine2",
    "ValveBiped.Bip01_Spine4": "mixamorig:Spine2",
    "ValveBiped.Bip01_Neck1": "mixamorig:Neck",
    "ValveBiped.Bip01_Head1": "mixamorig:Head",
    "ValveBiped.Bip01_L_Clavicle": "mixamorig:LeftShoulder",
    "ValveBiped.Bip01_L_UpperArm": "mixamorig:LeftArm",
    "ValveBiped.Bip01_L_Forearm": "mixamorig:LeftForeArm",
    "ValveBiped.Bip01_L_Hand": "mixamorig:LeftHand",
    "ValveBiped.Bip01_L_Thigh": "mixamorig:LeftUpLeg",
    "ValveBiped.Bip01_L_Calf": "mixamorig:LeftLeg",
    "ValveBiped.Bip01_L_Foot": "mixamorig:LeftFoot",
    "ValveBiped.Bip01_L_Toe0": "mixamorig:LeftToeBase",
    "ValveBiped.Bip01_R_Clavicle": "mixamorig:RightShoulder",
    "ValveBiped.Bip01_R_UpperArm": "mixamorig:RightArm",
    "ValveBiped.Bip01_R_Forearm": "mixamorig:RightForeArm",
    "ValveBiped.Bip01_R_Hand": "mixamorig:RightHand",
    "ValveBiped.Bip01_R_Thigh": "mixamorig:RightUpLeg",
    "ValveBiped.Bip01_R_Calf": "mixamorig:RightLeg",
    "ValveBiped.Bip01_R_Foot": "mixamorig:RightFoot",
    "ValveBiped.Bip01_R_Toe0": "mixamorig:RightToeBase",

    # MMD English and Japanese body names. Control/root names stay unmatched.
    "Upper Body": "mixamorig:Spine",
    "Upper Body2": "mixamorig:Spine1",
    "Left Shoulder": "mixamorig:LeftShoulder",
    "Left Arm": "mixamorig:LeftArm",
    "Left Elbow": "mixamorig:LeftForeArm",
    "Left Wrist": "mixamorig:LeftHand",
    "Left Leg": "mixamorig:LeftUpLeg",
    "Left Knee": "mixamorig:LeftLeg",
    "Left Ankle": "mixamorig:LeftFoot",
    "Left Toe": "mixamorig:LeftToeBase",
    "Right Shoulder": "mixamorig:RightShoulder",
    "Right Arm": "mixamorig:RightArm",
    "Right Elbow": "mixamorig:RightForeArm",
    "Right Wrist": "mixamorig:RightHand",
    "Right Leg": "mixamorig:RightUpLeg",
    "Right Knee": "mixamorig:RightLeg",
    "Right Ankle": "mixamorig:RightFoot",
    "Right Toe": "mixamorig:RightToeBase",
    "下半身": "mixamorig:Hips",
    "上半身": "mixamorig:Spine",
    "上半身2": "mixamorig:Spine1",
    "腰": "mixamorig:Hips",
    "首": "mixamorig:Neck",
    "頭": "mixamorig:Head",
    "左肩": "mixamorig:LeftShoulder",
    "左腕": "mixamorig:LeftArm",
    "左ひじ": "mixamorig:LeftForeArm",
    "左手首": "mixamorig:LeftHand",
    "左足": "mixamorig:LeftUpLeg",
    "左ひざ": "mixamorig:LeftLeg",
    "左足首": "mixamorig:LeftFoot",
    "左つま先": "mixamorig:LeftToeBase",
    "右肩": "mixamorig:RightShoulder",
    "右腕": "mixamorig:RightArm",
    "右ひじ": "mixamorig:RightForeArm",
    "右手首": "mixamorig:RightHand",
    "右足": "mixamorig:RightUpLeg",
    "右ひざ": "mixamorig:RightLeg",
    "右足首": "mixamorig:RightFoot",
    "右つま先": "mixamorig:RightToeBase",
}


for _side_tag, _mix_side in (("L", "Left"), ("R", "Right")):
    _COMMON_ALIAS_TO_FULL.update({
        f"{_mix_side}Clavicle": f"mixamorig:{_mix_side}Shoulder",
        f"{_mix_side}Collar": f"mixamorig:{_mix_side}Shoulder",
        f"{_mix_side}Shoulder": f"mixamorig:{_mix_side}Shoulder",
        f"{_mix_side}UpperArm": f"mixamorig:{_mix_side}Arm",
        f"{_mix_side}LowerArm": f"mixamorig:{_mix_side}ForeArm",
        f"{_mix_side}ForeArm": f"mixamorig:{_mix_side}ForeArm",
        f"{_mix_side}Hand": f"mixamorig:{_mix_side}Hand",
        f"{_mix_side}UpperLeg": f"mixamorig:{_mix_side}UpLeg",
        f"{_mix_side}Thigh": f"mixamorig:{_mix_side}UpLeg",
        f"{_mix_side}LowerLeg": f"mixamorig:{_mix_side}Leg",
        f"{_mix_side}Calf": f"mixamorig:{_mix_side}Leg",
        f"{_mix_side}Shin": f"mixamorig:{_mix_side}Leg",
        f"{_mix_side}Foot": f"mixamorig:{_mix_side}Foot",
        f"{_mix_side}Toe": f"mixamorig:{_mix_side}ToeBase",
        f"{_mix_side}Toes": f"mixamorig:{_mix_side}ToeBase",
        f"clavicle.{_side_tag}": f"mixamorig:{_mix_side}Shoulder",
        f"upper_arm.{_side_tag}": f"mixamorig:{_mix_side}Arm",
        f"lower_arm.{_side_tag}": f"mixamorig:{_mix_side}ForeArm",
        f"forearm.{_side_tag}": f"mixamorig:{_mix_side}ForeArm",
        f"hand.{_side_tag}": f"mixamorig:{_mix_side}Hand",
        f"upper_leg.{_side_tag}": f"mixamorig:{_mix_side}UpLeg",
        f"thigh.{_side_tag}": f"mixamorig:{_mix_side}UpLeg",
        f"lower_leg.{_side_tag}": f"mixamorig:{_mix_side}Leg",
        f"calf.{_side_tag}": f"mixamorig:{_mix_side}Leg",
        f"shin.{_side_tag}": f"mixamorig:{_mix_side}Leg",
        f"foot.{_side_tag}": f"mixamorig:{_mix_side}Foot",
        f"toe.{_side_tag}": f"mixamorig:{_mix_side}ToeBase",
        f"toe0.{_side_tag}": f"mixamorig:{_mix_side}ToeBase",
        f"DEF-upper_arm.{_side_tag}.01": f"mixamorig:{_mix_side}Arm",
        f"DEF-upper_arm.{_side_tag}.001": f"mixamorig:{_mix_side}Arm",
        f"DEF-forearm.{_side_tag}.01": f"mixamorig:{_mix_side}ForeArm",
        f"DEF-forearm.{_side_tag}.001": f"mixamorig:{_mix_side}ForeArm",
        f"DEF-thigh.{_side_tag}.01": f"mixamorig:{_mix_side}UpLeg",
        f"DEF-thigh.{_side_tag}.001": f"mixamorig:{_mix_side}UpLeg",
        f"DEF-shin.{_side_tag}.01": f"mixamorig:{_mix_side}Leg",
        f"DEF-shin.{_side_tag}.001": f"mixamorig:{_mix_side}Leg",
    })

    for _finger, _mix_finger, _mmd_finger, _daz_finger in (
        ("Thumb", "Thumb", "Thumb", "Thumb"),
        ("Index", "Index", "Fore", "Index"),
        ("Middle", "Middle", "Middle", "Mid"),
        ("Ring", "Ring", "Third", "Ring"),
        ("Pinky", "Pinky", "Little", "Pinky"),
        ("Little", "Pinky", "Little", "Pinky"),
    ):
        for _idx, _part in ((1, "Proximal"), (2, "Intermediate"), (3, "Distal")):
            _COMMON_ALIAS_TO_FULL.update({
                f"{_mix_side}{_finger}{_idx}": f"mixamorig:{_mix_side}Hand{_mix_finger}{_idx}",
                f"{_mix_side}{_finger}{_part}": f"mixamorig:{_mix_side}Hand{_mix_finger}{_idx}",
                f"{_finger.lower()}_0{_idx}_{_side_tag.lower()}": f"mixamorig:{_mix_side}Hand{_mix_finger}{_idx}",
                f"{_mmd_finger}{_idx}.{_side_tag}": f"mixamorig:{_mix_side}Hand{_mix_finger}{_idx}",
                f"{_side_tag.lower()}{_daz_finger}{_idx}": f"mixamorig:{_mix_side}Hand{_mix_finger}{_idx}",
            })

    for _rigify_stem, _mix_finger in (
        ("thumb", "Thumb"),
        ("finger_index", "Index"),
        ("finger_middle", "Middle"),
        ("finger_ring", "Ring"),
        ("finger_pinky", "Pinky"),
    ):
        _COMMON_ALIAS_TO_FULL.update({
            f"DEF-{_rigify_stem}.01.{_side_tag}.02": f"mixamorig:{_mix_side}Hand{_mix_finger}1",
            f"DEF-{_rigify_stem}.02.{_side_tag}": f"mixamorig:{_mix_side}Hand{_mix_finger}2",
            f"DEF-{_rigify_stem}.03.{_side_tag}": f"mixamorig:{_mix_side}Hand{_mix_finger}3",
        })

for _jp_side, _mix_side in (("左", "Left"), ("右", "Right")):
    for _jp_finger, _mix_finger in (
        ("親指", "Thumb"),
        ("人指", "Index"),
        ("中指", "Middle"),
        ("薬指", "Ring"),
        ("小指", "Pinky"),
    ):
        for _idx in (1, 2, 3):
            _COMMON_ALIAS_TO_FULL[f"{_jp_side}{_jp_finger}{_idx}"] = (
                f"mixamorig:{_mix_side}Hand{_mix_finger}{_idx}"
            )
del (
    _side_tag, _mix_side, _finger, _mix_finger, _mmd_finger,
    _daz_finger, _idx, _part, _rigify_stem, _jp_side, _jp_finger,
)


def _nkey(s: str) -> str:
    """Strip any mixamorig prefix, lowercase, drop separators."""
    s = re.sub(r"^mixamorig\d*:", "", s, flags=re.IGNORECASE)
    return re.sub(r"[\W_]+", "", s.lower(), flags=re.UNICODE)

# Canonical lookup: normalized_key → full prefixed name
_CANONICAL: dict = {}
for _aliases in (_MIXAMO_SHORT_TO_FULL, _COMMON_ALIAS_TO_FULL):
    for _short, _full in _aliases.items():
        _CANONICAL[_nkey(_full)] = _full
        _CANONICAL[_nkey(_full.replace("mixamorig:", ""))] = _full
        _CANONICAL[_nkey(_short)] = _full
del _aliases, _short, _full


def _canonical(bone_name: str, standard: str):
    """Return canonical name in the requested standard, or None."""
    full = _CANONICAL.get(_nkey(bone_name))
    if full is None:
        return None
    return full if standard == "MIXAMO_PREFIXED" else full.replace("mixamorig:", "")


# ── Internal helpers ─────────────────────────────────────────────────

def _poll_arm(self, obj):
    return obj.type == "ARMATURE"


def _mesh_children(arm_obj):
    return [c for c in arm_obj.children if c.type == "MESH"]


def _rename_bone_atomic(arm_obj, old: str, new: str):
    """Rename one bone AND all vertex groups on child meshes — one undo step."""
    bone = arm_obj.data.bones.get(old)
    if bone:
        bone.name = new
    for mesh_obj in _mesh_children(arm_obj):
        vg = mesh_obj.vertex_groups.get(old)
        if vg:
            vg.name = new


def _diff(src_obj, tgt_obj):
    """Return (matched, src_only, tgt_only) as sorted lists."""
    src = set(src_obj.data.bones.keys())
    tgt = set(tgt_obj.data.bones.keys())
    return sorted(src & tgt), sorted(src - tgt), sorted(tgt - src)


def _complexity_label(n_matched, n_src_only, n_tgt_only):
    n = n_src_only  # only source-only bones require user resolution
    if n == 0:
        return f"Ready — {n_matched} matched, no renames needed"
    elif n <= 4:
        return f"Fast merge — {n_matched} matched, {n} to resolve"
    elif n <= 14:
        return f"Moderate merge — {n_matched} matched, {n} to resolve"
    else:
        return f"Complex merge — {n_matched} matched, {n} to resolve"


def _populate_entries(settings, src_obj, tgt_obj):
    """Rebuild bone_entries from current armature state."""
    matched, src_only, tgt_only = _diff(src_obj, tgt_obj)
    settings.bone_entries.clear()
    settings.stage2_verified = False
    settings.dry_run_done = False
    settings.dry_run_report = ""
    # Unresolved first, then target-only, matched last
    for name in src_only:
        it = settings.bone_entries.add()
        it.source_bone = name
        it.proposed = name
        it.status = "SRC_ONLY"
    for name in tgt_only:
        it = settings.bone_entries.add()
        it.target_bone = name
        it.proposed = name
        it.status = "TGT_ONLY"
    for name in matched:
        it = settings.bone_entries.add()
        it.source_bone = name
        it.target_bone = name
        it.proposed = name
        it.status = "MATCHED"
    settings.scope_label = _complexity_label(len(matched), len(src_only), len(tgt_only))


def _unresolved_count(settings):
    return sum(
        1 for it in settings.bone_entries
        if it.status == "SRC_ONLY"
    )


def _apply_batch_pattern(pattern: str, bone_name: str, index: int) -> str:
    """Expand {bone}, {side}, {index} tokens."""
    side = ""
    if re.search(r"(?i)(left|[._\-]l[._\-]|[._\-]l$|lefthand|leftup)", bone_name):
        side = "L"
    elif re.search(r"(?i)(right|[._\-]r[._\-]|[._\-]r$|righthand|rightup)", bone_name):
        side = "R"
    result = pattern.replace("{bone}", bone_name)
    result = result.replace("{side}", side)
    result = result.replace("{index}", str(index))
    return result


def _create_backup(context, src_obj, tgt_obj) -> str:
    """Duplicate source + target armatures and their meshes into a hidden collection."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    col_name = f"BF_BoneMerge_Backup_{ts}"
    col = bpy.data.collections.new(col_name)
    context.scene.collection.children.link(col)
    col.hide_viewport = True
    col.hide_render = True

    def _dup(obj):
        dup = obj.copy()
        dup.data = obj.data.copy()
        dup.name = obj.name + "_BF_Bak"
        col.objects.link(dup)
        dup.hide_set(True)

    for arm_obj in (src_obj, tgt_obj):
        _dup(arm_obj)
        for mesh in _mesh_children(arm_obj):
            _dup(mesh)

    return col.name


# ── PropertyGroups ───────────────────────────────────────────────────

class BoneMergeItem(PropertyGroup):
    source_bone: StringProperty(name="Source Bone")
    target_bone: StringProperty(name="Target Bone")
    proposed: StringProperty(name="Proposed Name")
    status: EnumProperty(
        name="Status",
        items=[
            ("MATCHED",  "Matched",             "Same name in both — will merge"),
            ("SRC_ONLY", "Source Only",          "Only in source — needs resolution"),
            ("TGT_ONLY", "Target Only",          "Only in target — kept as-is"),
            ("UNIQUE",   "Intentionally Unique", "Source bone kept separate, added to target"),
        ],
        default="MATCHED",
    )
    sel: BoolProperty(name="Select for Batch", default=False)


class BoneMergeSettings(PropertyGroup):
    source_armature: PointerProperty(
        name="Merges into Base",
        description=(
            "The clothing, hair, or accessory armature to be absorbed. "
            "Its bones are transferred into Base and it is hidden after the merge."
        ),
        type=bpy.types.Object,
        poll=_poll_arm,
    )
    target_armature: PointerProperty(
        name="Base",
        description=(
            "The body or primary armature that survives the merge. "
            "All bones and meshes from the secondary armature are added here."
        ),
        type=bpy.types.Object,
        poll=_poll_arm,
    )
    naming_standard: EnumProperty(
        name="Naming Standard",
        items=[
            ("MIXAMO_PREFIXED", "Mixamo (prefixed)",
             "Normalize to mixamorig:Hips, mixamorig:LeftArm, …"),
            ("MIXAMO_STRIPPED", "Mixamo (stripped)",
             "Normalize to Hips, LeftArm, … (prefix removed)"),
            ("CUSTOM", "Custom", "No auto-proposal — rename each bone manually"),
        ],
        default="MIXAMO_PREFIXED",
    )
    stage: IntProperty(default=1, min=1, max=3)
    scope_acknowledged: BoolProperty(default=False)
    stage2_verified: BoolProperty(default=False)
    dry_run_done: BoolProperty(default=False)
    scope_label: StringProperty(default="")
    bone_entries: CollectionProperty(type=BoneMergeItem)
    active_entry: IntProperty(default=0)
    batch_pattern: StringProperty(
        name="Pattern",
        description="Tokens: {bone}=original name  {side}=L or R  {index}=row number",
        default="{bone}",
    )
    dry_run_report: StringProperty(default="")
    backup_collection_name: StringProperty(default="")


# ── UIList ───────────────────────────────────────────────────────────

class BONEFORGE_UL_bone_merge(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        _ICON = {
            "MATCHED":  "CHECKMARK",
            "SRC_ONLY": "ADD",
            "TGT_ONLY": "REMOVE",
            "UNIQUE":   "PINNED",
        }
        row = layout.row(align=True)
        row.prop(item, "sel", text="")
        row.label(text="", icon=_ICON.get(item.status, "DOT"))
        if item.status == "MATCHED":
            row.label(text=item.source_bone)
        elif item.status == "SRC_ONLY":
            row.label(text=item.source_bone)
            if item.proposed and item.proposed != item.source_bone:
                row.label(text="→ " + item.proposed)
        elif item.status == "TGT_ONLY":
            row.label(text=item.target_bone)
        else:
            row.label(text=item.source_bone or item.target_bone)


# ── Operators ────────────────────────────────────────────────────────

class BONEFORGE_OT_bone_merge_analyze(Operator):
    bl_idname = "boneforge.bone_merge_analyze"
    bl_label = "Analyze"
    bl_description = "Compare both armatures and populate the bone diff table"
    bl_options = {"UNDO"}

    def execute(self, context):
        s = context.scene.bf_bone_merge
        src, tgt = s.source_armature, s.target_armature
        if not src or not tgt:
            self.report({"ERROR"}, "Select both armatures first")
            return {"CANCELLED"}
        if src == tgt:
            self.report({"ERROR"}, "Source and target must be different objects")
            return {"CANCELLED"}
        s.scope_acknowledged = False
        s.stage = 1
        _populate_entries(s, src, tgt)
        self.report({"INFO"}, s.scope_label)
        return {"FINISHED"}


class BONEFORGE_OT_bone_merge_acknowledge(Operator):
    bl_idname = "boneforge.bone_merge_acknowledge"
    bl_label = "Acknowledge Scope — Proceed to Rename"
    bl_description = "Confirm you have reviewed the bone diff; unlock Stage 2"
    bl_options = {"UNDO"}

    def execute(self, context):
        s = context.scene.bf_bone_merge
        s.scope_acknowledged = True
        s.stage = 2
        return {"FINISHED"}


class BONEFORGE_OT_bone_merge_normalize(Operator):
    """Symmetric prefix strip: apply same naming standard to BOTH armatures."""
    bl_idname = "boneforge.bone_merge_normalize"
    bl_label = "Normalize Both Armatures"
    bl_description = (
        "Rename all known bones in SOURCE and TARGET simultaneously to the "
        "selected standard. Vertex groups on all child meshes update atomically."
    )
    bl_options = {"UNDO"}

    def execute(self, context):
        s = context.scene.bf_bone_merge
        if s.naming_standard == "CUSTOM":
            self.report({"WARNING"}, "Custom standard — rename manually per bone")
            return {"CANCELLED"}
        count = 0
        for arm_obj in (s.source_armature, s.target_armature):
            for bone in list(arm_obj.data.bones):
                c = _canonical(bone.name, s.naming_standard)
                if c and c != bone.name:
                    _rename_bone_atomic(arm_obj, bone.name, c)
                    count += 1
        _populate_entries(s, s.source_armature, s.target_armature)
        self.report({"INFO"}, f"Normalized {count} bone(s) in both armatures")
        return {"FINISHED"}


class BONEFORGE_OT_bone_merge_propose(Operator):
    bl_idname = "boneforge.bone_merge_propose"
    bl_label = "Auto-Propose Renames"
    bl_description = "Fill proposed names for unresolved SRC_ONLY bones using the selected standard"
    bl_options = {"UNDO"}

    def execute(self, context):
        s = context.scene.bf_bone_merge
        if s.naming_standard == "CUSTOM":
            self.report({"WARNING"}, "Select Mixamo standard to use auto-propose")
            return {"CANCELLED"}
        count = 0
        for it in s.bone_entries:
            if it.status != "SRC_ONLY":
                continue
            c = _canonical(it.source_bone, s.naming_standard)
            if c and c != it.source_bone:
                it.proposed = c
                count += 1
        self.report({"INFO"}, f"Proposed renames for {count} bone(s)")
        return {"FINISHED"}


class BONEFORGE_OT_bone_merge_apply_rename(Operator):
    """Apply proposed rename for ONE entry (the active one). Atomic — one undo step."""
    bl_idname = "boneforge.bone_merge_apply_rename"
    bl_label = "Apply Rename"
    bl_description = "Rename this bone and its vertex groups atomically (one undo step)"
    bl_options = {"UNDO"}

    def execute(self, context):
        s = context.scene.bf_bone_merge
        idx = s.active_entry
        if idx < 0 or idx >= len(s.bone_entries):
            self.report({"ERROR"}, "No active bone entry")
            return {"CANCELLED"}
        it = s.bone_entries[idx]
        if it.status not in ("SRC_ONLY", "TGT_ONLY"):
            self.report({"INFO"}, "Only SRC_ONLY or TGT_ONLY bones can be renamed here")
            return {"CANCELLED"}
        old = it.source_bone if it.status == "SRC_ONLY" else it.target_bone
        new = it.proposed
        if not new or new == old:
            self.report({"INFO"}, "Proposed name matches current — nothing to do")
            return {"CANCELLED"}
        arm = s.source_armature if it.status == "SRC_ONLY" else s.target_armature
        _rename_bone_atomic(arm, old, new)
        _populate_entries(s, s.source_armature, s.target_armature)
        return {"FINISHED"}


class BONEFORGE_OT_bone_merge_batch(Operator):
    bl_idname = "boneforge.bone_merge_batch"
    bl_label = "Apply Batch Pattern"
    bl_description = "Apply the pattern to all selected SRC_ONLY entries and rename atomically"
    bl_options = {"UNDO"}

    def execute(self, context):
        s = context.scene.bf_bone_merge
        pattern = s.batch_pattern
        targets = [it for it in s.bone_entries if it.sel and it.status == "SRC_ONLY"]
        if not targets:
            self.report({"WARNING"}, "No SRC_ONLY entries selected")
            return {"CANCELLED"}
        # Check for collisions before committing anything
        proposed_names = [_apply_batch_pattern(pattern, it.source_bone, i)
                          for i, it in enumerate(targets)]
        if len(proposed_names) != len(set(proposed_names)):
            self.report({"ERROR"}, "Batch pattern produces duplicate names — fix pattern and retry")
            return {"CANCELLED"}
        count = 0
        for i, it in enumerate(targets):
            new_name = proposed_names[i]
            if new_name != it.source_bone:
                _rename_bone_atomic(s.source_armature, it.source_bone, new_name)
                count += 1
        _populate_entries(s, s.source_armature, s.target_armature)
        self.report({"INFO"}, f"Batch renamed {count} bone(s)")
        return {"FINISHED"}


class BONEFORGE_OT_bone_merge_mark_unique(Operator):
    bl_idname = "boneforge.bone_merge_mark_unique"
    bl_label = "Mark as Unique"
    bl_description = "Mark active SRC_ONLY bone as intentionally unique — it will be added to target without merging"
    bl_options = {"UNDO"}

    def execute(self, context):
        s = context.scene.bf_bone_merge
        idx = s.active_entry
        if idx < 0 or idx >= len(s.bone_entries):
            self.report({"ERROR"}, "No active entry")
            return {"CANCELLED"}
        it = s.bone_entries[idx]
        if it.status != "SRC_ONLY":
            self.report({"INFO"}, "Only SRC_ONLY bones can be marked unique")
            return {"CANCELLED"}
        it.status = "UNIQUE"
        return {"FINISHED"}


class BONEFORGE_OT_bone_merge_verify_stage2(Operator):
    bl_idname = "boneforge.bone_merge_verify_stage2"
    bl_label = "Verify Rename — Proceed to Merge"
    bl_description = "Check all SRC_ONLY bones are resolved; unlock Stage 3 if clear"
    bl_options = {"UNDO"}

    def execute(self, context):
        s = context.scene.bf_bone_merge
        remaining = _unresolved_count(s)
        if remaining:
            self.report({"ERROR"},
                        f"{remaining} SRC_ONLY bone(s) still unresolved — "
                        f"rename to match a target bone or mark as Unique")
            return {"CANCELLED"}
        s.stage2_verified = True
        s.stage = 3
        return {"FINISHED"}


class BONEFORGE_OT_bone_merge_dry_run(Operator):
    """Non-destructive preview: run full merge logic on current data, report only."""
    bl_idname = "boneforge.bone_merge_dry_run"
    bl_label = "Run Merge Preview"
    bl_description = (
        "Execute full merge logic against a read-only snapshot. "
        "No data is modified. Review the report before committing."
    )
    bl_options = {"UNDO"}

    def execute(self, context):
        s = context.scene.bf_bone_merge
        src, tgt = s.source_armature, s.target_armature

        matched, src_only, tgt_only = _diff(src, tgt)
        # UNIQUE entries stay separate but are still added to target
        unique_names = {it.source_bone for it in s.bone_entries if it.status == "UNIQUE"}

        will_merge = matched
        will_add = src_only  # includes UNIQUE bones
        will_keep = tgt_only

        src_meshes = _mesh_children(src)
        tgt_meshes = _mesh_children(tgt)
        all_meshes = src_meshes + tgt_meshes

        # Vertex group impact
        vg_impact_lines = []
        for mesh in all_meshes:
            vg_names = {vg.name for vg in mesh.vertex_groups}
            merge_count = len(vg_names & set(will_merge))
            add_count = len(vg_names & set(will_add))
            orphan = vg_names - set(will_merge) - set(will_add) - set(will_keep) - set(src_only) - set(tgt_only)
            line = f"  {mesh.name}: {merge_count} merge, {add_count} new"
            if orphan:
                line += f", {len(orphan)} orphaned VG(s)"
            vg_impact_lines.append(line)

        # Warnings
        warnings = []
        for mesh in all_meshes:
            for vg in mesh.vertex_groups:
                all_bones = set(will_merge) | set(will_add) | set(will_keep)
                if vg.name not in all_bones:
                    warnings.append(f"  VG '{vg.name}' on '{mesh.name}' has no receiving bone")

        lines = [
            "=== BONE MERGE DRY-RUN PREVIEW ===",
            f"Source: {src.name}  ({len(src.data.bones)} bones, {len(src_meshes)} mesh(es))",
            f"Target: {tgt.name}  ({len(tgt.data.bones)} bones, {len(tgt_meshes)} mesh(es))",
            "",
            f"WILL MERGE ({len(will_merge)} bones — source deduped into target):",
        ]
        for name in will_merge[:15]:
            lines.append(f"  {name}")
        if len(will_merge) > 15:
            lines.append(f"  … and {len(will_merge)-15} more")
        lines += [
            "",
            f"WILL ADD TO TARGET ({len(will_add)} source-only):",
        ]
        for name in will_add[:10]:
            tag = " [unique]" if name in unique_names else ""
            lines.append(f"  {name}{tag}")
        if len(will_add) > 10:
            lines.append(f"  … and {len(will_add)-10} more")
        lines += [
            "",
            f"TARGET-ONLY PRESERVED ({len(will_keep)}):",
        ]
        for name in will_keep[:8]:
            lines.append(f"  {name}")
        if len(will_keep) > 8:
            lines.append(f"  … and {len(will_keep)-8} more")
        lines += ["", "VERTEX GROUP IMPACT:"]
        lines.extend(vg_impact_lines or ["  (no meshes)"])
        if warnings:
            lines += ["", f"WARNINGS ({len(warnings)}):"]
            lines.extend(warnings[:6])
            if len(warnings) > 6:
                lines.append(f"  … and {len(warnings)-6} more")
        else:
            lines += ["", "WARNINGS: None"]

        s.dry_run_report = "\n".join(lines)
        s.dry_run_done = True
        self.report({"INFO"}, "Dry-run complete — review the report, then merge")
        return {"FINISHED"}


class BONEFORGE_OT_bone_merge_execute(Operator):
    bl_idname = "boneforge.bone_merge_execute"
    bl_label = "Merge Armatures"
    bl_description = (
        "Create a backup collection, then merge source into target. "
        "Source-only bones are copied to target; source meshes are reparented."
    )
    bl_options = {"UNDO"}

    def execute(self, context):
        s = context.scene.bf_bone_merge
        src, tgt = s.source_armature, s.target_armature

        if not s.dry_run_done:
            self.report({"ERROR"}, "Run the dry-run preview first")
            return {"CANCELLED"}

        # ── Step 1: auto-backup (Unanimous addition #3) ──────────────
        backup_name = _create_backup(context, src, tgt)
        s.backup_collection_name = backup_name

        matched, src_only, tgt_only = _diff(src, tgt)

        # ── Step 2: copy source-only bones into target ───────────────
        # Read source bone data in edit mode first
        prev_active = context.view_layer.objects.active
        context.view_layer.objects.active = src
        bpy.ops.object.mode_set(mode="EDIT")
        bone_data = {}
        try:
            src_edit = src.data.edit_bones
            for bname in src_only:
                eb = src_edit.get(bname)
                if eb is None:
                    continue
                bone_data[bname] = {
                    "head":        eb.head.copy(),
                    "tail":        eb.tail.copy(),
                    "roll":        eb.roll,
                    "use_deform":  eb.use_deform,
                    "use_connect": eb.use_connect,
                    "parent":      eb.parent.name if eb.parent else None,
                }
        finally:
            bpy.ops.object.mode_set(mode="OBJECT")

        # Write into target edit mode
        context.view_layer.objects.active = tgt
        bpy.ops.object.mode_set(mode="EDIT")
        try:
            tgt_edit = tgt.data.edit_bones

            for bname, d in bone_data.items():
                nb = tgt_edit.new(bname)
                nb.head = d["head"]
                nb.tail = d["tail"]
                nb.roll = d["roll"]
                nb.use_deform = d["use_deform"]

            # Second pass: parent relationships
            for bname, d in bone_data.items():
                pname = d["parent"]
                if pname and pname in tgt_edit and bname in tgt_edit:
                    tgt_edit[bname].parent = tgt_edit[pname]
                    tgt_edit[bname].use_connect = d["use_connect"]
        finally:
            bpy.ops.object.mode_set(mode="OBJECT")

        # ── Step 3: reparent source meshes to target ─────────────────
        reparented = []
        for mesh in list(src.children):
            if mesh.type != "MESH":
                continue
            for mod in mesh.modifiers:
                if mod.type == "ARMATURE" and mod.object == src:
                    mod.object = tgt
            mesh.parent = tgt
            reparented.append(mesh.name)

        # ── Step 4: hide source armature ─────────────────────────────
        src.hide_viewport = True
        src.hide_render = True

        # ── Step 5: restore context ───────────────────────────────────
        context.view_layer.objects.active = tgt
        if prev_active and prev_active.name in bpy.data.objects:
            context.view_layer.objects.active = prev_active

        # Build post-merge summary
        summary = (
            f"Merge complete. "
            f"Merged: {len(matched)} bones, "
            f"Added: {len(src_only)} bones, "
            f"Reparented: {len(reparented)} mesh(es). "
            f"Backup: {backup_name}"
        )
        self.report({"INFO"}, summary)

        # Reset stage
        s.stage = 1
        s.scope_acknowledged = False
        s.stage2_verified = False
        s.dry_run_done = False
        s.scope_label = summary
        s.bone_entries.clear()

        return {"FINISHED"}


# ── Panel ────────────────────────────────────────────────────────────

class BONEFORGE_PT_bone_merge(Panel):
    bl_label = " "
    bl_idname = "BONEFORGE_PT_bone_merge"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BoneCraft"
    bl_parent_id = "BF_PT_sb_setup"
    bl_order = 2
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        self.layout.label(text=T("Bone Merge"))

    def draw(self, context):
        layout = self.layout
        s = context.scene.bf_bone_merge

        # ── Stage 1 — Scope ──────────────────────────────────────────
        box1 = layout.box()
        h1 = box1.row()
        h1.label(
            text=T("Stage 1 — Scope"),
            icon="CHECKMARK" if s.scope_acknowledged else "RADIOBUT_OFF",
        )

        # Explainer: always visible so new users understand the direction.
        info = box1.box()
        icol = info.column(align=True)
        icol.scale_y = 0.8
        icol.label(text=T("Base — body armature that stays."))
        icol.label(text=T("Merges into — clothing/hair added to Base, then hidden."))

        col = box1.column(align=True)
        col.prop(s, "target_armature", text=T("Base"))
        col.prop(s, "source_armature", text=T("Merges into ↑"))
        col.separator()
        col.operator("boneforge.bone_merge_analyze", icon="VIEWZOOM")

        if s.scope_label:
            box1.label(text=s.scope_label, icon="INFO")

        if s.bone_entries and not s.scope_acknowledged:
            box1.operator("boneforge.bone_merge_acknowledge", icon="FORWARD")

        # ── Stage 2 — Rename ─────────────────────────────────────────
        box2 = layout.box()
        box2.enabled = s.scope_acknowledged
        h2 = box2.row()
        h2.label(
            text=T("Stage 2 — Rename"),
            icon="CHECKMARK" if s.stage2_verified else "RADIOBUT_OFF",
        )
        if not s.scope_acknowledged:
            box2.label(text=T("Complete Stage 1 first"), icon="LOCKED")
        else:
            col2 = box2.column()
            col2.prop(s, "naming_standard", text="")

            row_ops = box2.row(align=True)
            row_ops.operator("boneforge.bone_merge_normalize", icon='SORTALPHA')
            row_ops.operator("boneforge.bone_merge_propose",   icon="SHADERFX")

            unresolved = _unresolved_count(s)
            if unresolved:
                box2.label(
                    text=f"{unresolved} bone(s) need resolution",
                    icon="ERROR",
                )

            if s.bone_entries:
                box2.template_list(
                    "BONEFORGE_UL_bone_merge", "",
                    s, "bone_entries",
                    s, "active_entry",
                    rows=6,
                )
                active_row = box2.row(align=True)
                active_row.operator("boneforge.bone_merge_apply_rename", icon='RENAME')
                active_row.operator("boneforge.bone_merge_mark_unique",  icon="PINNED")

                # Active entry proposed field
                if 0 <= s.active_entry < len(s.bone_entries):
                    it = s.bone_entries[s.active_entry]
                    if it.status in ("SRC_ONLY", "TGT_ONLY"):
                        box2.prop(it, "proposed", text=T("Rename to"))

                # Batch rename
                bsec = box2.box()
                bsec.label(text=T("Batch Rename (selected rows)"))
                bsec.prop(s, "batch_pattern", text=T("Pattern"))
                bsec.label(text=T("{bone}  {side}  {index}"), icon="INFO")
                bsec.operator("boneforge.bone_merge_batch", icon="FORWARD")

            box2.separator()
            verify_row = box2.row()
            verify_row.enabled = unresolved == 0
            verify_row.operator("boneforge.bone_merge_verify_stage2", icon="FORWARD")

        # ── Stage 3 — Merge ──────────────────────────────────────────
        box3 = layout.box()
        box3.enabled = s.stage2_verified
        h3 = box3.row()
        h3.label(text=T("Stage 3 — Merge"), icon="RADIOBUT_OFF")

        if not s.stage2_verified:
            box3.label(text=T("Complete Stage 2 first"), icon="LOCKED")
        else:
            box3.operator("boneforge.bone_merge_dry_run", icon="HIDE_OFF")

            if s.dry_run_report:
                rbox = box3.box()
                for line in s.dry_run_report.split("\n"):
                    if line:
                        rbox.label(text=line)

            merge_row = box3.row()
            merge_row.enabled = s.dry_run_done
            merge_row.scale_y = 1.4
            merge_row.operator("boneforge.bone_merge_execute", icon='AUTOMERGE_ON')

            if s.backup_collection_name:
                box3.label(
                    text=f"Backup: {s.backup_collection_name}",
                )


# ── Registration ─────────────────────────────────────────────────────

_classes = (
    BoneMergeItem,
    BoneMergeSettings,
    BONEFORGE_UL_bone_merge,
    BONEFORGE_OT_bone_merge_analyze,
    BONEFORGE_OT_bone_merge_acknowledge,
    BONEFORGE_OT_bone_merge_normalize,
    BONEFORGE_OT_bone_merge_propose,
    BONEFORGE_OT_bone_merge_apply_rename,
    BONEFORGE_OT_bone_merge_batch,
    BONEFORGE_OT_bone_merge_mark_unique,
    BONEFORGE_OT_bone_merge_verify_stage2,
    BONEFORGE_OT_bone_merge_dry_run,
    BONEFORGE_OT_bone_merge_execute,
    BONEFORGE_PT_bone_merge,
)


def register():
    for cls in _classes:
        try:
            bpy.utils.register_class(cls)
        except RuntimeError as e:
            logger.error("[BoneCraft BoneMerge] Failed to register %s: %s", cls.__name__, e)
    bpy.types.Scene.bf_bone_merge = PointerProperty(type=BoneMergeSettings)


def unregister():
    if hasattr(bpy.types.Scene, "bf_bone_merge"):
        del bpy.types.Scene.bf_bone_merge
    for cls in reversed(_classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass


def _get_manifest():
    from boneforge.core.tool_registry import ToolManifest
    return ToolManifest(
        id="bone_merge",
        name="Bone Merge",
        description=(
            "Three-stage armature merge pipeline: normalize naming, "
            "dry-run preview, auto-backup, weight-safe merge."
        ),
        icon="ARMATURE_DATA",
        default_enabled=True,
        register_fn=register,
        unregister_fn=unregister,
    )
