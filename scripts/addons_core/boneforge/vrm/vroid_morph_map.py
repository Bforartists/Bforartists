"""VRoid standard morph names → VRChat viseme auto-mapping.

VRoid Studio exports a fixed set of blend shape names on the Face mesh.
This module maps those names to:
  1. ``boneforge_viseme_*`` custom props on the mesh object (used by
     the existing VRChat viseme mapper).
  2. ``boneforge_vroid_expression_*`` props for non-viseme expressions
     (blink, look, brow emotions) so the BoneCraft expression panel
     can surface them.

Viseme mapping (VRChat SDK V2 names):
    Fcl_MTH_A  → vrc.v_aa   / boneforge_viseme_a
    Fcl_MTH_I  → vrc.v_ih   / boneforge_viseme_i
    Fcl_MTH_U  → vrc.v_ou   / boneforge_viseme_u
    Fcl_MTH_E  → vrc.v_E    / boneforge_viseme_e
    Fcl_MTH_O  → vrc.v_oh   / boneforge_viseme_o
    Fcl_MTH_Close → vrc.v_sil / boneforge_viseme_neutral

Expressions stored for reference (not VRChat visemes):
    Fcl_EYE_Close{,_L,_R}
    Fcl_BRW_{Angry,Fun,Joy,Sorrow,Surprised}
    Fcl_ALL_{Angry,Fun,Joy,Sorrow,Surprised}

Receipt stored under ``boneforge_vroid_morph_receipt`` on each mesh
and a summary under the same key on the armature.
"""

import bpy
from bpy.types import Operator

import logging

logger = logging.getLogger(__name__)


# ── Mapping tables ────────────────────────────────────────────────

# VRoid face morph → (VRChat viseme SDK name, boneforge_viseme_* key)
_VISEME_MAP: dict[str, tuple[str, str]] = {
    "Fcl_MTH_A":     ("vrc.v_aa",  "a"),
    "Fcl_MTH_I":     ("vrc.v_ih",  "i"),
    "Fcl_MTH_U":     ("vrc.v_ou",  "u"),
    "Fcl_MTH_E":     ("vrc.v_E",   "e"),
    "Fcl_MTH_O":     ("vrc.v_oh",  "o"),
    "Fcl_MTH_Close": ("vrc.v_sil", "neutral"),
}

# Non-viseme expression morphs stored separately for reference.
_EXPRESSION_KEYS: list[str] = [
    "Fcl_EYE_Close",
    "Fcl_EYE_Close_L",
    "Fcl_EYE_Close_R",
    "Fcl_BRW_Angry",
    "Fcl_BRW_Fun",
    "Fcl_BRW_Joy",
    "Fcl_BRW_Sorrow",
    "Fcl_BRW_Surprised",
    "Fcl_ALL_Angry",
    "Fcl_ALL_Fun",
    "Fcl_ALL_Joy",
    "Fcl_ALL_Sorrow",
    "Fcl_ALL_Surprised",
    # VRM 1.0 expression names (lowercase used in newer VRoid exports)
    "happy", "angry", "sad", "relaxed", "surprised",
    "blink", "blink_l", "blink_r",
    "lookUp", "lookDown", "lookLeft", "lookRight",
    "neutral",
    "aa", "ih", "ou", "ee", "oh",
]

# Some older VRoid exports use uppercase A/I/U/E/O directly.
_ALT_VISEME_MAP: dict[str, tuple[str, str]] = {
    "A": ("vrc.v_aa",  "a"),
    "I": ("vrc.v_ih",  "i"),
    "U": ("vrc.v_ou",  "u"),
    "E": ("vrc.v_E",   "e"),
    "O": ("vrc.v_oh",  "o"),
}


def _map_mesh(mesh_obj: bpy.types.Object) -> dict:
    """Write viseme + expression props onto *mesh_obj*. Returns receipt."""
    sk = mesh_obj.data.shape_keys
    if sk is None:
        return {"visemes_mapped": 0, "expressions_mapped": 0, "skipped": True}

    key_names_lower = {k.name.lower(): k.name for k in sk.key_blocks}
    key_names_exact = {k.name: k.name for k in sk.key_blocks}

    visemes_mapped  = 0
    exprs_mapped    = 0
    needs_manual    = []

    # Primary VRoid Fcl_ viseme names
    for morph_name, (vrc_name, bf_key) in _VISEME_MAP.items():
        actual = key_names_exact.get(morph_name)
        if actual is None:
            actual = key_names_lower.get(morph_name.lower())
        if actual:
            mesh_obj[f"boneforge_viseme_{bf_key}"] = actual
            mesh_obj[f"boneforge_vrc_viseme_{bf_key}"] = vrc_name
            visemes_mapped += 1
            logger.debug("[BoneCraft] VRoid viseme %s → %s on %s",
                         morph_name, actual, mesh_obj.name)

    # Fallback: plain A/I/U/E/O keys
    if visemes_mapped == 0:
        for morph_name, (vrc_name, bf_key) in _ALT_VISEME_MAP.items():
            actual = key_names_exact.get(morph_name)
            if actual:
                mesh_obj[f"boneforge_viseme_{bf_key}"] = actual
                mesh_obj[f"boneforge_vrc_viseme_{bf_key}"] = vrc_name
                visemes_mapped += 1

    # Non-viseme expressions
    for expr_key in _EXPRESSION_KEYS:
        actual = key_names_exact.get(expr_key)
        if actual is None:
            actual = key_names_lower.get(expr_key.lower())
        if actual:
            mesh_obj[f"boneforge_vroid_expression_{expr_key.lower()}"] = actual
            exprs_mapped += 1

    return {
        "visemes_mapped":    visemes_mapped,
        "expressions_mapped": exprs_mapped,
        "needs_manual":      needs_manual,
    }


# ── Operator ─────────────────────────────────────────────────────

class BF_OT_VRoidMapVisemes(Operator):
    """Map VRoid standard morph names to VRChat visemes on all child meshes."""

    bl_idname  = "boneforge.vroid_map_visemes"
    bl_label   = "Map VRoid Visemes"
    bl_description = (
        "Scan child meshes for VRoid standard morph names (Fcl_MTH_A, "
        "Fcl_MTH_I, etc.) and write boneforge_viseme_* props so the "
        "VRChat viseme tools can find them automatically. "
        "Also maps expression morphs (blink, emotion)."
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == "ARMATURE"

    def execute(self, context):
        arm_obj = context.active_object
        mesh_children = [
            c for c in arm_obj.children if c.type == "MESH"
        ]
        if not mesh_children:
            self.report({"WARNING"}, "No mesh children found on this armature.")
            return {"CANCELLED"}

        total_visemes = 0
        total_exprs   = 0
        mesh_results  = []

        for mesh_obj in mesh_children:
            result = _map_mesh(mesh_obj)
            if result.get("skipped"):
                continue
            v = result["visemes_mapped"]
            e = result["expressions_mapped"]
            total_visemes += v
            total_exprs   += e
            if v > 0 or e > 0:
                mesh_results.append({
                    "mesh":              mesh_obj.name,
                    "visemes_mapped":    v,
                    "expressions_mapped": e,
                })
            from boneforge.core import write_custom_json
            write_custom_json(mesh_obj, "boneforge_vroid_morph_receipt", result)

        if total_visemes == 0 and total_exprs == 0:
            self.report(
                {"WARNING"},
                "No VRoid morph names found on any child mesh. "
                "This armature may not be a VRoid avatar, or morphs "
                "may use non-standard names.",
            )
            return {"CANCELLED"}

        from boneforge.core import write_custom_json
        summary = {
            "total_visemes":     total_visemes,
            "total_expressions": total_exprs,
            "meshes":            mesh_results,
        }
        write_custom_json(arm_obj, "boneforge_vroid_morph_receipt", summary)

        self.report(
            {"INFO"},
            f"VRoid morph map: {total_visemes} viseme(s) + "
            f"{total_exprs} expression(s) mapped across "
            f"{len(mesh_results)} mesh(es)",
        )
        return {"FINISHED"}
