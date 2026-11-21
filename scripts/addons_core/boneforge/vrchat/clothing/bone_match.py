"""BoneCraft VRChat — Bone Matching and Confidence Scoring.

Matches clothing armature bones to base avatar bones with confidence levels:
HIGH (exact/near-exact name match), MEDIUM (partial match or position-based),
LOW (position only), UNMATCHED (no candidate found).

Category: Clothing.
"""

import bpy
from bpy.types import Operator, Panel
from typing import NamedTuple, Optional
from mathutils import Vector, kdtree

from boneforge.i18n import T


# ── Confidence Levels ───────────────────────────────────────────

class ConfidenceLevel:
    """Confidence level constants."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNMATCHED = "UNMATCHED"


class BoneMatch(NamedTuple):
    """Result of bone matching between clothing and base armature."""
    clothing_bone: str
    base_bone: Optional[str]
    confidence: str
    score: float


# Minimum name similarity score (0.0-1.0) to consider a partial match
SIMILARITY_THRESHOLD = 0.7

# Maximum world-space distance (Blender units) for position-based matching
POSITION_MATCH_MAX_DISTANCE = 0.5


# ── Bone Matching Functions ─────────────────────────────────────

def _strip_bone_prefix(name: str) -> str:
    """Strip common prefixes like 'Armature.001' from bone name."""
    if "." in name:
        return name.split(".")[-1]
    return name


def _normalize_name(name: str) -> str:
    """Normalize bone name for comparison (lowercase, strip common prefixes)."""
    cleaned = _strip_bone_prefix(name).lower()
    return cleaned


def _similarity_score(name1: str, name2: str) -> float:
    """Calculate string similarity (0.0 to 1.0) between two names."""
    n1 = _normalize_name(name1)
    n2 = _normalize_name(name2)

    if n1 == n2:
        return 1.0

    # Levenshtein-like simple comparison
    if n1 in n2 or n2 in n1:
        return 0.8

    # Count matching characters
    common = sum(1 for c in n1 if c in n2)
    max_len = max(len(n1), len(n2))
    if max_len == 0:
        return 0.0

    return common / max_len


def _build_position_kdtree(armature_obj: bpy.types.Object) -> tuple:
    """Build KDTree from bone positions for spatial matching in world space.

    Returns (kdtree, bone_list) where bone_list is ordered matching kdtree indices.
    """
    bones = list(armature_obj.data.bones)
    if not bones:
        return None, []
    kd = kdtree.KDTree(len(bones))

    for idx, bone in enumerate(bones):
        # Transform bone position to world space using armature's world matrix
        world_pos = armature_obj.matrix_world @ bone.head_local
        kd.insert((world_pos.x, world_pos.y, world_pos.z), idx)

    kd.balance()
    return kd, bones


def _find_closest_bone_by_position(target_position: Vector,
                                   kdtree_data: tuple,
                                   max_distance: float = float('inf')) -> Optional[str]:
    """Find closest bone to target position using KDTree.

    Args:
        target_position: Vector position to search near
        kdtree_data: (kdtree, bone_list) tuple from _build_position_kdtree
        max_distance: Maximum distance to consider

    Returns:
        Bone name or None if no bone within distance
    """
    kdtree, bones = kdtree_data
    pos_tuple = (target_position.x, target_position.y, target_position.z)

    closest = kdtree.find(pos_tuple)
    if closest is None:
        return None

    co, idx, dist = closest
    if dist <= max_distance:
        return bones[idx].name
    return None


def match_bones(base_armature: bpy.types.Object,
                clothing_armature: bpy.types.Object) -> list[BoneMatch]:
    """Match clothing armature bones to base avatar bones.

    Attempts matching in order:
    1. Exact name match (HIGH confidence)
    2. Name similarity > 0.7 (MEDIUM confidence)
    3. Position-based nearest bone (LOW confidence)
    4. No match found (UNMATCHED)

    Args:
        base_armature: Base avatar armature object
        clothing_armature: Clothing armature object

    Returns:
        List of BoneMatch tuples
    """
    if not (base_armature and base_armature.type == 'ARMATURE'):
        return []
    if not (clothing_armature and clothing_armature.type == 'ARMATURE'):
        return []

    base_data = base_armature.data
    clothing_data = clothing_armature.data

    # Build base bone lookup
    base_bones_by_name = {bone.name: bone for bone in base_data.bones}
    base_bones_normalized = {_normalize_name(bone.name): bone.name
                             for bone in base_data.bones}

    # Build KDTree for position-based matching in world space
    kdtree_data = _build_position_kdtree(base_armature)
    if kdtree_data[0] is None:
        kdtree_data = None

    matches = []

    for clothing_bone in clothing_data.bones:
        base_bone = None
        confidence = ConfidenceLevel.UNMATCHED
        score = 0.0

        # Step 1: Exact name match
        if clothing_bone.name in base_bones_by_name:
            base_bone = clothing_bone.name
            confidence = ConfidenceLevel.HIGH
            score = 1.0

        # Step 2: Name similarity match
        if base_bone is None:
            norm_clothing = _normalize_name(clothing_bone.name)
            if norm_clothing in base_bones_normalized:
                base_bone = base_bones_normalized[norm_clothing]
                confidence = ConfidenceLevel.HIGH
                score = 0.99
            else:
                # Find best partial match
                best_match = None
                best_score = SIMILARITY_THRESHOLD
                for base_name in base_bones_by_name:
                    sim = _similarity_score(clothing_bone.name, base_name)
                    if sim > best_score:
                        best_score = sim
                        best_match = base_name

                if best_match is not None:
                    base_bone = best_match
                    confidence = ConfidenceLevel.MEDIUM
                    score = best_score

        # Step 3: Position-based matching
        if base_bone is None and kdtree_data is not None:
            # Transform clothing bone position to world space
            clothing_world_pos = clothing_armature.matrix_world @ clothing_bone.head_local

            closest = _find_closest_bone_by_position(clothing_world_pos, kdtree_data,
                                                      max_distance=POSITION_MATCH_MAX_DISTANCE)
            if closest is not None:
                base_bone = closest
                confidence = ConfidenceLevel.LOW
                score = 0.5

        matches.append(BoneMatch(
            clothing_bone=clothing_bone.name,
            base_bone=base_bone,
            confidence=confidence,
            score=score
        ))

    return matches


# ── Operators ───────────────────────────────────────────────────

class BF_OT_VRC_MatchBones(Operator):
    """Analyze and display bone matching between clothing and base armature."""
    bl_idname = "boneforge.vrc_match_bones"
    bl_label = "Match Clothing Bones"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        scene = context.scene

        # Get selected armatures
        base_arm = None
        clothing_arm = None

        for obj in context.selected_objects:
            if obj.type == 'ARMATURE':
                if base_arm is None:
                    base_arm = obj
                elif clothing_arm is None:
                    clothing_arm = obj
                    break

        if base_arm is None or clothing_arm is None:
            self.report({'ERROR'}, "Select two armatures: base and clothing")
            return {'CANCELLED'}

        # Run matching
        matches = match_bones(base_arm, clothing_arm)

        # Store results in scene for panel display
        scene.boneforge_vrc_match_results = str(matches)

        # Summary
        high_count = sum(1 for m in matches if m.confidence == ConfidenceLevel.HIGH)
        medium_count = sum(1 for m in matches if m.confidence == ConfidenceLevel.MEDIUM)
        low_count = sum(1 for m in matches if m.confidence == ConfidenceLevel.LOW)
        unmatched_count = sum(1 for m in matches if m.confidence == ConfidenceLevel.UNMATCHED)

        self.report({'INFO'},
                   f"Matched: {high_count} HIGH, {medium_count} MEDIUM, "
                   f"{low_count} LOW, {unmatched_count} UNMATCHED")

        return {'FINISHED'}


# ── Panel ───────────────────────────────────────────────────────

class BONEFORGE_PT_vrc_bone_match(Panel):
    """Display bone matching results."""
    bl_label = " "
    bl_idname = "BONEFORGE_PT_vrc_bone_match"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BoneCraft"

    def draw_header(self, context):
        self.layout.label(text=T("Bone Matching"))

    @classmethod
    def poll(cls, context):
        # Suppressed from Tool tab — displayed via BoneForge tab VRChat hub.
        return False

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)
        col.label(text=T("Bone Matching"))
        col.operator("boneforge.vrc_match_bones", text=T("Match Bones"))


# ── Registration ────────────────────────────────────────────────

def register():
    """Register bone matching module."""
    bpy.utils.register_class(BF_OT_VRC_MatchBones)
    bpy.utils.register_class(BONEFORGE_PT_vrc_bone_match)

    # Scene property for storing match results
    from bpy.props import StringProperty
    bpy.types.Scene.boneforge_vrc_match_results = StringProperty(default="")


def unregister():
    """Unregister bone matching module."""
    bpy.utils.unregister_class(BONEFORGE_PT_vrc_bone_match)
    bpy.utils.unregister_class(BF_OT_VRC_MatchBones)

    if hasattr(bpy.types.Scene, 'boneforge_vrc_match_results'):
        del bpy.types.Scene.boneforge_vrc_match_results
