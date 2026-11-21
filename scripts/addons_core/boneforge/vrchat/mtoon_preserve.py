"""MToon material detection and VRChat preservation check.

VRChat natively supports MToon shading when avatars are uploaded via
the VRC SDK.  Converting MToon materials to Principled BSDF destroys
the distinctive VTuber look and is a common mistake when exporting
from Blender.

This module:
  1. Detects MToon materials on child meshes (by node group name,
     custom property flag, or material name pattern).
  2. Reports which materials are MToon-safe (leave alone), which are
     already BSDF (fine for non-VRM targets), and which need review.
  3. Stamps ``boneforge_mtoon_preserved = True`` on detected MToon
     materials so the export path can gate conversion logic.

Called from:
  - The VRChat export panel "Check MToon" button.
  - Automatically during VRM import post-pass (non-blocking, best-effort).

Receipt stored under ``boneforge_mtoon_receipt`` on the armature.
"""

import bpy
from bpy.types import Operator

import logging

logger = logging.getLogger(__name__)


# ── Detection heuristics ─────────────────────────────────────────

_MTOON_NODE_GROUP_PATTERNS = (
    "mtoon",
    "MToon",
    "VRM_ADDON_development_mtoon",
    "shader_mtoon",
    "mmd_shader",     # MMD materials also need preservation
)

_MTOON_MAT_NAME_PATTERNS = (
    "MToon",
    "mtoon",
)


def _is_mtoon(mat: bpy.types.Material) -> bool:
    """Return True if *mat* appears to be an MToon material."""
    if mat is None:
        return False

    # 1. Explicit BoneForge stamp from a previous detection pass.
    if mat.get("boneforge_mtoon_preserved"):
        return True

    # 2. Node group inside the material node tree.
    if mat.use_nodes and mat.node_tree is not None:
        for node in mat.node_tree.nodes:
            if node.type != "GROUP":
                continue
            ng = node.node_tree
            if ng is None:
                continue
            ng_name = ng.name.lower()
            for pat in _MTOON_NODE_GROUP_PATTERNS:
                if pat.lower() in ng_name:
                    return True

    # 3. Material name heuristic (weak, last resort).
    for pat in _MTOON_MAT_NAME_PATTERNS:
        if pat in mat.name:
            return True

    return False


def _classify_material(mat: bpy.types.Material) -> str:
    """Return 'mtoon', 'principled', or 'other'."""
    if _is_mtoon(mat):
        return "mtoon"
    if mat.use_nodes and mat.node_tree is not None:
        for node in mat.node_tree.nodes:
            if node.type == "BSDF_PRINCIPLED":
                return "principled"
    return "other"


# ── Operator ─────────────────────────────────────────────────────

class BF_OT_VRCCheckMToon(Operator):
    """Detect and preserve MToon materials for VRChat export."""

    bl_idname  = "boneforge.vrc_check_mtoon"
    bl_label   = "Check / Preserve MToon"
    bl_description = (
        "Scan child meshes for MToon materials and stamp them as "
        "VRChat-safe so the export path does not convert them to "
        "Principled BSDF. VRChat supports MToon natively — converting "
        "it destroys the VTuber look."
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == "ARMATURE"

    def execute(self, context):
        arm_obj = context.active_object

        mtoon_mats      = []
        principled_mats = []
        other_mats      = []

        for child in arm_obj.children:
            if child.type != "MESH":
                continue
            for slot in child.material_slots:
                mat = slot.material
                if mat is None:
                    continue
                kind = _classify_material(mat)
                if kind == "mtoon":
                    mat["boneforge_mtoon_preserved"] = True
                    if mat.name not in mtoon_mats:
                        mtoon_mats.append(mat.name)
                elif kind == "principled":
                    if mat.name not in principled_mats:
                        principled_mats.append(mat.name)
                else:
                    if mat.name not in other_mats:
                        other_mats.append(mat.name)

        from boneforge.core import write_custom_json
        receipt = {
            "mtoon_preserved": mtoon_mats,
            "principled":      principled_mats,
            "other":           other_mats,
        }
        write_custom_json(arm_obj, "boneforge_mtoon_receipt", receipt)

        if mtoon_mats:
            self.report(
                {"INFO"},
                f"MToon check: {len(mtoon_mats)} MToon material(s) preserved "
                f"(will NOT be converted on VRChat export), "
                f"{len(principled_mats)} Principled BSDF, "
                f"{len(other_mats)} other",
            )
        else:
            self.report(
                {"INFO"},
                "No MToon materials detected. "
                f"{len(principled_mats)} Principled BSDF, "
                f"{len(other_mats)} other. "
                "If you imported a VRM, try re-importing via BoneCraft.",
            )
        return {"FINISHED"}


# ── Registration ──────────────────────────────────────────────────

_CLASSES = (BF_OT_VRCCheckMToon,)


def register():
    for cls in _CLASSES:
        try:
            bpy.utils.register_class(cls)
        except ValueError:
            pass


def unregister():
    for cls in reversed(_CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except (RuntimeError, ValueError):
            pass
