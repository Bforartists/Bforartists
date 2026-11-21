"""BoneCraft VRChat — Performance Rank Calculator.

Analyzes avatar performance across multiple metrics and assigns a performance
rank (Excellent, Good, Medium, Poor, VeryPoor). Tracks metrics like polygon
count, bone count, material slots, skinned meshes, PhysBones, and contacts.
Category: Performance.
"""

import time
import bpy
from bpy.props import (
    StringProperty,
    IntProperty,
    FloatProperty,
    PointerProperty,
)

from boneforge.i18n import T
from bpy.types import Operator, Panel, PropertyGroup

from boneforge.core import active_armature

# ── Performance thresholds ──────────────────────────────────────

THRESHOLDS = {
    "polygons": {"Excellent": 32000, "Good": 70000, "Medium": 120000, "Poor": 200000},
    "skinned_meshes": {"Excellent": 1, "Good": 2, "Medium": 8, "Poor": 16},
    "material_slots": {"Excellent": 4, "Good": 8, "Medium": 16, "Poor": 32},
    "bone_count": {"Excellent": 75, "Good": 150, "Medium": 256, "Poor": 400},
    "physbones": {"Excellent": 4, "Good": 8, "Medium": 16, "Poor": 32},
    "contacts": {"Excellent": 4, "Good": 8, "Medium": 16, "Poor": 32},
}

RANK_ORDER = ["Excellent", "Good", "Medium", "Poor", "VeryPoor"]

RANK_COLORS = {
    "Excellent": (0.0, 1.0, 0.0, 1.0),  # Green
    "Good": (0.5, 1.0, 0.0, 1.0),       # Light green
    "Medium": (1.0, 1.0, 0.0, 1.0),     # Amber
    "Poor": (1.0, 0.5, 0.0, 1.0),       # Orange
    "VeryPoor": (1.0, 0.0, 0.0, 1.0),   # Red
}

# ── Debounce timer for depsgraph updates ────────────────────────

_last_rank_update = 0.0
_rank_update_delay = 0.5


# ── Statistics helper ───────────────────────────────────────────

def count_avatar_stats(armature):
    """Count avatar performance statistics.

    Args:
        armature: Armature object (not data)

    Returns:
        dict with keys: polygon_count, skinned_mesh_count, material_count,
        bone_count, physbone_count, contact_count
    """
    if armature is None or armature.type != 'ARMATURE':
        return {
            "polygon_count": 0,
            "skinned_mesh_count": 0,
            "material_count": 0,
            "bone_count": 0,
            "physbone_count": 0,
            "contact_count": 0,
        }

    polygon_count = 0
    skinned_mesh_count = 0
    material_count = 0
    bone_count = len(armature.data.bones)
    physbone_count = 0
    contact_count = 0

    # Find all meshes in the armature's children
    for obj in bpy.context.scene.objects:
        if obj.type != 'MESH':
            continue

        # Check if mesh belongs to this armature (modifier OR parent)
        is_deformed = False
        for mod in obj.modifiers:
            if mod.type == 'ARMATURE' and mod.object == armature:
                is_deformed = True
                break

        if not is_deformed:
            # Also check if object is a direct child of the armature
            if obj.parent == armature:
                is_deformed = True

        if not is_deformed:
            continue

        # Count polygons
        polygon_count += len(obj.data.polygons)

        # Count material slots
        material_count += len(obj.data.materials)

        # Check if mesh has vertex groups (skinning).
        # v3.0.16 fix: vertex_groups lives on the Object, not on the
        # Mesh data — `obj.data.vertex_groups` raises AttributeError
        # on Blender 4.x / Bforartists 5.2.
        if len(obj.vertex_groups) > 0:
            skinned_mesh_count += 1

    # Count PhysBones — stored as custom properties on bones
    for bone in armature.data.bones:
        if 'boneforge_vrchat_physbone' in bone:
            physbone_count += 1

    # Count VRChat Contacts — stored as custom properties on bones
    for bone in armature.data.bones:
        if 'boneforge_vrchat_contact' in bone:
            contact_count += 1

    return {
        "polygon_count": polygon_count,
        "skinned_mesh_count": skinned_mesh_count,
        "material_count": material_count,
        "bone_count": bone_count,
        "physbone_count": physbone_count,
        "contact_count": contact_count,
    }


# ── Rank calculation ────────────────────────────────────────────

def calculate_category_rank(category, value):
    """Calculate rank for a single category.

    Args:
        category: Category name (e.g., "polygons", "bone_count")
        value: Numeric value to rank

    Returns:
        Rank string: "Excellent", "Good", "Medium", "Poor", or "VeryPoor"
    """
    if category not in THRESHOLDS:
        return "Excellent"

    thresholds = THRESHOLDS[category]

    # Check in reverse order (best to worst)
    if value <= thresholds["Excellent"]:
        return "Excellent"
    elif value <= thresholds["Good"]:
        return "Good"
    elif value <= thresholds["Medium"]:
        return "Medium"
    elif value <= thresholds["Poor"]:
        return "Poor"
    else:
        return "VeryPoor"


def calculate_overall_rank(armature):
    """Calculate overall avatar rank and per-category details.

    Args:
        armature: Armature object

    Returns:
        Tuple of (overall_rank_string, category_details_dict)
        category_details_dict maps category name to {"rank": rank_string, "value": numeric_value, "threshold": next_tier_threshold}
    """
    stats = count_avatar_stats(armature)

    category_map = {
        "polygons": stats["polygon_count"],
        "skinned_meshes": stats["skinned_mesh_count"],
        "material_slots": stats["material_count"],
        "bone_count": stats["bone_count"],
        "physbones": stats["physbone_count"],
        "contacts": stats["contact_count"],
    }

    category_details = {}
    worst_rank_index = 0

    for category, value in category_map.items():
        rank = calculate_category_rank(category, value)
        rank_index = RANK_ORDER.index(rank)

        if rank_index > worst_rank_index:
            worst_rank_index = rank_index

        # Calculate next tier threshold
        thresholds = THRESHOLDS[category]
        if rank == "VeryPoor":
            next_threshold = None  # Already at worst
        else:
            next_rank = RANK_ORDER[rank_index + 1]
            next_threshold = thresholds.get(next_rank)

        category_details[category] = {
            "rank": rank,
            "value": value,
            "threshold": next_threshold,
        }

    overall_rank = RANK_ORDER[worst_rank_index]
    return overall_rank, category_details


# ── Property group for scene storage ────────────────────────────

class BF_VRCPerformanceData(PropertyGroup):
    """Cached performance rank data on scene."""

    overall_rank: StringProperty(
        name="Overall Rank",
        default="Excellent",
    )
    polygon_count: IntProperty(name="Polygon Count", default=0)
    skinned_mesh_count: IntProperty(name="Skinned Mesh Count", default=0)
    material_count: IntProperty(name="Material Count", default=0)
    bone_count: IntProperty(name="Bone Count", default=0)
    physbone_count: IntProperty(name="PhysBone Count", default=0)
    contact_count: IntProperty(name="Contact Count", default=0)

    last_update: FloatProperty(name="Last Update Time", default=0.0)


# ── Depsgraph handler ───────────────────────────────────────────

def _on_depsgraph_update(scene, depsgraph):
    """Debounced depsgraph update handler to auto-calculate rank."""
    global _last_rank_update

    current_time = time.time()
    if current_time - _last_rank_update < _rank_update_delay:
        return

    _last_rank_update = current_time

    arm = active_armature(bpy.context)
    if arm is None:
        return

    overall_rank, details = calculate_overall_rank(arm)

    perf_data = scene.boneforge_vrc_performance
    perf_data.overall_rank = overall_rank
    perf_data.polygon_count = details["polygons"]["value"]
    perf_data.skinned_mesh_count = details["skinned_meshes"]["value"]
    perf_data.material_count = details["material_slots"]["value"]
    perf_data.bone_count = details["bone_count"]["value"]
    perf_data.physbone_count = details["physbones"]["value"]
    perf_data.contact_count = details["contacts"]["value"]
    perf_data.last_update = current_time


# ── Operator ────────────────────────────────────────────────────

class BF_OT_VRC_CalculateRank(Operator):
    """Calculate and update avatar performance rank."""
    bl_idname = "boneforge.vrc_calculate_rank"
    bl_label = "Calculate Performance Rank"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return active_armature(context) is not None

    def execute(self, context):
        arm = active_armature(context)
        if arm is None:
            self.report({'WARNING'}, "No active armature")
            return {'CANCELLED'}

        overall_rank, details = calculate_overall_rank(arm)

        perf_data = context.scene.boneforge_vrc_performance
        perf_data.overall_rank = overall_rank
        perf_data.polygon_count = details["polygons"]["value"]
        perf_data.skinned_mesh_count = details["skinned_meshes"]["value"]
        perf_data.material_count = details["material_slots"]["value"]
        perf_data.bone_count = details["bone_count"]["value"]
        perf_data.physbone_count = details["physbones"]["value"]
        perf_data.contact_count = details["contacts"]["value"]

        self.report({'INFO'}, f"Avatar rank: {overall_rank}")
        return {'FINISHED'}


# ── Panel ───────────────────────────────────────────────────────

class BONEFORGE_PT_vrc_performance(Panel):
    """VRChat Avatar Performance Analyzer."""
    bl_idname = "BONEFORGE_PT_vrc_performance"
    bl_label = " "
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BoneCraft"

    def draw_header(self, context):
        self.layout.label(text=T("VRChat Performance"))

    @classmethod
    def poll(cls, context):
        # Suppressed from Tool tab — displayed via BoneForge tab VRChat hub.
        return False

    def draw(self, context):
        layout = self.layout
        arm = active_armature(context)

        if arm is None:
            layout.label(text=T("No active armature"), icon='INFO')
            return

        perf_data = context.scene.boneforge_vrc_performance
        overall_rank, details = calculate_overall_rank(arm)

        # Overall rank display
        rank_color = RANK_COLORS.get(overall_rank, (1, 1, 1, 1))
        row = layout.row()
        row.label(text=f"Overall Rank: {overall_rank}")

        # Stats table
        layout.separator()
        layout.label(text=T("Performance Breakdown:"))

        categories = [
            ("polygons", "Polygons"),
            ("skinned_meshes", "Skinned Meshes"),
            ("material_slots", "Material Slots"),
            ("bone_count", "Bones"),
            ("physbones", "PhysBones"),
            ("contacts", "Contacts"),
        ]

        for cat_key, cat_label in categories:
            detail = details[cat_key]
            rank = detail["rank"]
            value = detail["value"]
            threshold = detail["threshold"]

            box = layout.box()
            row = box.row()
            row.label(text=cat_label)
            row.label(text=f"{value}")
            row.label(text=rank, icon='DOT')

            if threshold is not None:
                gap = threshold - value
                row = box.row()
                row.label(text=f"  Next tier at {threshold} (+{gap})", icon='BLANK1')

        layout.separator()
        layout.operator("boneforge.vrc_calculate_rank", icon='FILE_REFRESH')


# ── Registration ────────────────────────────────────────────────

classes = (
    BF_VRCPerformanceData,
    BF_OT_VRC_CalculateRank,
    BONEFORGE_PT_vrc_performance,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.boneforge_vrc_performance = PointerProperty(
        type=BF_VRCPerformanceData,
        name="BoneCraft VRChat Performance Data",
    )

    bpy.app.handlers.depsgraph_update_post.append(_on_depsgraph_update)


def unregister():
    bpy.app.handlers.depsgraph_update_post.remove(_on_depsgraph_update)

    del bpy.types.Scene.boneforge_vrc_performance

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
