"""BoneCraft VRChat — Face Tracking Setup.

Configure SteamVR Unified Expressions (68 shape keys) for avatar face tracking.
Collapsed by default with note that face tracking is optional.
Category: VRChat Setup.
"""

import json
from pathlib import Path

import bpy
from bpy.types import Operator, Panel

from boneforge.core import active_armature
from boneforge.vrchat.visemes.utils import collect_shape_key_names, find_shape_key, get_mesh_objects

import logging
from boneforge.i18n import T

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────

UNIFIED_EXPRESSIONS = [
    # Eyes (14)
    "EyeClosedLeft", "EyeClosedRight",
    "EyeOpenLeft", "EyeOpenRight",
    "EyeSquintLeft", "EyeSquintRight",
    "EyeDownLeft", "EyeDownRight",
    "EyeLeftLeft", "EyeLeftRight",
    "EyeRightLeft", "EyeRightRight",
    "EyeUpLeft", "EyeUpRight",
    # Brows (5)
    "BrowDownLeft", "BrowDownRight",
    "BrowInnerUp",
    "BrowOuterUpLeft", "BrowOuterUpRight",
    # Cheeks (4)
    "CheekPuffLeft", "CheekPuffRight",
    "CheekSquintLeft", "CheekSquintRight",
    # Jaw (4)
    "JawForward", "JawLeft", "JawOpen", "JawRight",
    # Mouth (30)
    "MouthClose", "MouthDimpleLeft", "MouthDimpleRight",
    "MouthFrownLeft", "MouthFrownRight",
    "MouthFunnel",
    "MouthLeft",
    "MouthLowerDownLeft", "MouthLowerDownRight",
    "MouthOpen",
    "MouthPressLeft", "MouthPressRight",
    "MouthPucker",
    "MouthRight",
    "MouthRollLower", "MouthRollUpper",
    "MouthShrugLower", "MouthShrugUpper",
    "MouthSmileLeft", "MouthSmileRight",
    "MouthStretchLeft", "MouthStretchRight",
    "MouthUpperUpLeft", "MouthUpperUpRight",
    # Nose (2)
    "NoseSneerLeft", "NoseSneerRight",
    # Tongue (2)
    "TongueOut", "TongueUp",
]


# ── Utility functions ────────────────────────────────────────────────

def _load_expressions_data():
    """Load unified expressions definitions from JSON file."""
    data_dir = Path(__file__).parent / "data"
    expr_file = data_dir / "unified_expressions.json"
    if expr_file.exists():
        with open(expr_file, "r") as f:
            return json.load(f)
    return {"expressions": []}


def auto_map_expressions(mesh_objects):
    """Auto-map shape keys to Unified Expressions.

    Returns dict mapping expression_name -> shape_key_name.
    """
    mapping = {}
    all_shape_keys = collect_shape_key_names(mesh_objects)

    for expr in UNIFIED_EXPRESSIONS:
        match = find_shape_key(expr, all_shape_keys)
        if match:
            mapping[expr] = match

    return mapping


def get_expressions_mapping(armature):
    """Retrieve stored expressions mapping from armature custom properties."""
    key = "boneforge_vrchat_expressions"
    if hasattr(armature, key):
        try:
            data = json.loads(getattr(armature, key))
            return data
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            # M-07: Log JSON parse errors for debugging
            logger.error(f"[BoneCraft] JSON parse error loading expressions mapping: {e}")
    return {}


def set_expressions_mapping(armature, mapping):
    """Store expressions mapping in armature custom properties."""
    key = "boneforge_vrchat_expressions"
    armature[key] = json.dumps(mapping)


# ── Operators ────────────────────────────────────────────────────────

class BF_OT_VRC_AutoMapExpressions(Operator):
    """Auto-map all Unified Expressions shape keys."""

    bl_idname = "boneforge.vrc_auto_map_expressions"
    bl_label = "Auto-Map Expressions"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        arm = active_armature(context)
        if not arm:
            self.report({"ERROR"}, "No active armature selected")
            return {"CANCELLED"}

        meshes = get_mesh_objects(arm)
        if not meshes:
            self.report({"ERROR"}, "No mesh objects found on armature")
            return {"CANCELLED"}

        mapping = auto_map_expressions(meshes)
        set_expressions_mapping(arm, mapping)

        unmapped_count = len(UNIFIED_EXPRESSIONS) - len(mapping)
        self.report(
            {"INFO"},
            f"Mapped {len(mapping)}/{len(UNIFIED_EXPRESSIONS)} expressions"
        )

        return {"FINISHED"}


# ── Panel ────────────────────────────────────────────────────────────

class BONEFORGE_PT_vrc_face_tracking(Panel):
    """Face Tracking Setup panel."""

    bl_label = " "
    bl_idname = "BONEFORGE_PT_vrc_face_tracking"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_parent_id = "BONEFORGE_PT_vrc_main"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        self.layout.label(text=T("Face Tracking (SteamVR)"))

    @classmethod
    def poll(cls, context):
        return active_armature(context) is not None

    def draw(self, context):
        arm = active_armature(context)
        layout = self.layout

        if not arm:
            return

        # Info banner
        box = layout.box()
        box.label(text=T("Face tracking is optional."), icon="INFO")
        box.label(text=T("Most users do not need this."))

        layout.separator()

        # Auto-map button
        layout.operator(
            "boneforge.vrc_auto_map_expressions",
            text=T("Auto-Map All Expressions")
        )

        layout.separator()

        # Expression count
        mapping = get_expressions_mapping(arm)
        row = layout.row()
        row.label(
            text=f"Mapped: {len(mapping)}/{len(UNIFIED_EXPRESSIONS)}"
        )

        # List expressions by category
        layout.label(text=T("Expressions by Category:"))

        expr_data = _load_expressions_data()
        categories = {}
        for expr in expr_data.get("expressions", []):
            cat = expr.get("category", "Other")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(expr["name"])

        for category in sorted(categories.keys()):
            box = layout.box()
            row = box.row()
            row.label(text=category, icon="DOWNARROW_HLT")

            expr_list = categories[category]
            mapped_in_cat = sum(1 for e in expr_list if e in mapping)
            row.label(text=f"{mapped_in_cat}/{len(expr_list)}")


# ── Registration ─────────────────────────────────────────────────────

classes = (
    BF_OT_VRC_AutoMapExpressions,
    BONEFORGE_PT_vrc_face_tracking,
)


def register():
    """Register face tracking classes."""
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    """Unregister face tracking classes."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
