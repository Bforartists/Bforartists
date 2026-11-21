"""VRM SpringBone → VRC PhysBone conversion.

Reads the spring bone groups previously preserved by ``vrm/meta.py``
(``boneforge_vrm_spring_groups`` on the armature) and writes VRC
PhysBone parameter JSON onto each chain's root bone.

Handles both VRM 0.x (``bone_groups`` with ``bones`` list) and
VRM 1.0 (``springs`` with ``joints`` list) data shapes — the
preserved JSON mirrors whichever upstream shape was present.

Special VRoid handling: bone names starting with ``J_Sec_Hair`` are
treated as hair chains and get the Hair PhysBone preset.  Chains
whose root matches ``J_Sec_Skirt`` get the Skirt preset.  Everything
else gets the generic Hair preset as a conservative default.

Receipt stored under ``boneforge_vrm_springbone_receipt``.
"""

import json
import logging

import bpy
from bpy.types import Operator

logger = logging.getLogger(__name__)


# ── Presets ───────────────────────────────────────────────────────

_PRESET_HAIR = {
    "version": 1, "pull": 0.2, "spring": 0.4, "stiffness": 0.2,
    "gravity": 0.3, "gravity_falloff": 1.0,
    "immobile_type": "ALL_MOTION", "immobile": 0.0,
    "max_angle": 60.0, "radius": 0.02,
    "grab_permission": True, "pose_permission": True,
    "source": "vrm_springbone",
}
_PRESET_SKIRT = {
    **_PRESET_HAIR,
    "pull": 0.15, "spring": 0.3, "stiffness": 0.1,
    "gravity": 0.5, "max_angle": 90.0, "radius": 0.03,
}


def _pick_preset(root_name: str) -> dict:
    n = root_name.lower()
    if "skirt" in n or "cape" in n or "coat" in n:
        return dict(_PRESET_SKIRT)
    return dict(_PRESET_HAIR)


# ── Helpers ───────────────────────────────────────────────────────

def _extract_bone_names(group: dict | list) -> list[str]:
    """Pull bone names from a spring group regardless of VRM spec shape."""
    names: list[str] = []
    if isinstance(group, dict):
        # VRM 0.x: {"bones": ["boneName", ...], ...}
        # VRM 1.0: {"joints": [{"node": {"bone_name": "..."}}, ...]}
        raw_bones = group.get("bones")
        if raw_bones:
            names = [b for b in raw_bones if isinstance(b, str)]
        raw_joints = group.get("joints")
        if raw_joints and not names:
            for j in raw_joints:
                if isinstance(j, dict):
                    node = j.get("node") or {}
                    bn = node.get("bone_name") or node.get("value")
                    if bn:
                        names.append(bn)
    elif isinstance(group, list):
        # Flat list of bone names (some upstream versions)
        names = [b for b in group if isinstance(b, str)]
    return names


def _chain_root(arm_obj: bpy.types.Object, bone_names: list[str]) -> str | None:
    """Return the topmost bone in *bone_names* (fewest ancestors)."""
    name_set = set(bone_names)
    best = None
    best_depth = 10_000
    for name in bone_names:
        bone = arm_obj.data.bones.get(name)
        if bone is None:
            continue
        depth = 0
        cur = bone.parent
        while cur is not None:
            depth += 1
            cur = cur.parent
        if depth < best_depth:
            best_depth = depth
            best = name
    return best


# ── Operator ─────────────────────────────────────────────────────

class BF_OT_VRMConvertSpringBones(Operator):
    """Convert preserved VRM SpringBone groups to VRC PhysBone parameters."""

    bl_idname  = "boneforge.vrm_convert_springbones"
    bl_label   = "Convert SpringBones → PhysBones"
    bl_description = (
        "Read the VRM spring bone groups preserved on this armature and "
        "write VRC PhysBone parameters onto each chain root bone. "
        "VRoid hair chains (J_Sec_Hair*) use the Hair preset; "
        "skirt chains use the Skirt preset."
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if obj is None or obj.type != "ARMATURE":
            return False
        return obj.get("boneforge_vrm_spring_groups") is not None

    def execute(self, context):
        arm_obj = context.active_object
        from boneforge.core import read_custom_json, write_custom_json

        groups = read_custom_json(arm_obj, "boneforge_vrm_spring_groups",
                                  default=[])
        if not groups:
            self.report(
                {"WARNING"},
                "No spring bone data found on this armature. "
                "Import a VRM file first via BoneCraft VRM panel.",
            )
            return {"CANCELLED"}

        converted = []
        skipped   = []

        for i, group in enumerate(groups):
            bone_names = _extract_bone_names(group)
            if not bone_names:
                skipped.append(f"group_{i} (no bones)")
                continue

            root = _chain_root(arm_obj, bone_names)
            if root is None:
                skipped.append(f"group_{i} (bones not in armature)")
                continue

            config = _pick_preset(root)
            config["chain_length"] = len(bone_names)

            bone = arm_obj.data.bones.get(root)
            if bone is None:
                skipped.append(root)
                continue

            bone["boneforge_vrchat_physbone"] = json.dumps(config)
            converted.append({"root": root, "bones": len(bone_names)})
            logger.info("[BoneCraft] SpringBone→PhysBone root=%s len=%d",
                        root, len(bone_names))

        receipt = {
            "converted": converted,
            "skipped":   skipped,
            "total_groups": len(groups),
        }
        write_custom_json(arm_obj, "boneforge_vrm_springbone_receipt", receipt)

        self.report(
            {"INFO"},
            f"SpringBone→PhysBone: {len(converted)} chain(s) converted, "
            f"{len(skipped)} skipped — see armature custom props",
        )
        return {"FINISHED"}
