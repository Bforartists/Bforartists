"""BoneCraft Phase 2 — Rigify Auto-Enhancement.

Detects Rigify-generated armatures and automatically populates Phase 1
picker layouts, bookmarks, and a property panel for IK/FK/stretch/follow
controls. Writes Phase 1 data via JSON custom properties only — no
cross-phase imports.
"""

import bpy
import json

from boneforge.i18n import T
from boneforge.core import (
    active_armature,
    is_rigify_human,
    read_custom_json,
    write_custom_json,
    addon_prefs,
)


# ── Rigify bone/collection mapping ─────────────────────────────

# Standard Rigify humanoid picker zones: name → collection target
_HUMANOID_BODY_ZONES = [
    {"name": "Head", "target_type": "collection", "target": "Head",
     "polygon": [[0.45, 0.9], [0.55, 0.9], [0.55, 0.98], [0.45, 0.98]],
     "color": [0.8, 0.7, 0.5]},
    {"name": "Neck", "target_type": "collection", "target": "Neck",
     "polygon": [[0.47, 0.86], [0.53, 0.86], [0.53, 0.9], [0.47, 0.9]],
     "color": [0.7, 0.6, 0.5]},
    {"name": "Spine", "target_type": "collection", "target": "Spine",
     "polygon": [[0.4, 0.55], [0.6, 0.55], [0.6, 0.86], [0.4, 0.86]],
     "color": [0.5, 0.6, 0.8]},
    {"name": "Hips", "target_type": "collection", "target": "Hips",
     "polygon": [[0.38, 0.45], [0.62, 0.45], [0.62, 0.55], [0.38, 0.55]],
     "color": [0.5, 0.5, 0.7]},
    {"name": "Upper Arm.L", "target_type": "collection", "target": "Upper Arm.L (FK)",
     "polygon": [[0.2, 0.7], [0.4, 0.7], [0.4, 0.85], [0.2, 0.85]],
     "color": [0.4, 0.6, 0.9]},
    {"name": "Upper Arm.R", "target_type": "collection", "target": "Upper Arm.R (FK)",
     "polygon": [[0.6, 0.7], [0.8, 0.7], [0.8, 0.85], [0.6, 0.85]],
     "color": [0.4, 0.6, 0.9]},
    {"name": "Forearm.L", "target_type": "collection", "target": "Forearm.L (FK)",
     "polygon": [[0.05, 0.55], [0.2, 0.55], [0.2, 0.7], [0.05, 0.7]],
     "color": [0.3, 0.5, 0.8]},
    {"name": "Forearm.R", "target_type": "collection", "target": "Forearm.R (FK)",
     "polygon": [[0.8, 0.55], [0.95, 0.55], [0.95, 0.7], [0.8, 0.7]],
     "color": [0.3, 0.5, 0.8]},
    {"name": "Hand.L", "target_type": "collection", "target": "Hand.L",
     "polygon": [[0.0, 0.42], [0.12, 0.42], [0.12, 0.55], [0.0, 0.55]],
     "color": [0.9, 0.7, 0.5]},
    {"name": "Hand.R", "target_type": "collection", "target": "Hand.R",
     "polygon": [[0.88, 0.42], [1.0, 0.42], [1.0, 0.55], [0.88, 0.55]],
     "color": [0.9, 0.7, 0.5]},
    {"name": "Thigh.L", "target_type": "collection", "target": "Thigh.L (FK)",
     "polygon": [[0.35, 0.25], [0.48, 0.25], [0.48, 0.45], [0.35, 0.45]],
     "color": [0.4, 0.7, 0.5]},
    {"name": "Thigh.R", "target_type": "collection", "target": "Thigh.R (FK)",
     "polygon": [[0.52, 0.25], [0.65, 0.25], [0.65, 0.45], [0.52, 0.45]],
     "color": [0.4, 0.7, 0.5]},
    {"name": "Shin.L", "target_type": "collection", "target": "Shin.L (FK)",
     "polygon": [[0.33, 0.08], [0.46, 0.08], [0.46, 0.25], [0.33, 0.25]],
     "color": [0.3, 0.6, 0.4]},
    {"name": "Shin.R", "target_type": "collection", "target": "Shin.R (FK)",
     "polygon": [[0.54, 0.08], [0.67, 0.08], [0.67, 0.25], [0.54, 0.25]],
     "color": [0.3, 0.6, 0.4]},
    {"name": "Foot.L", "target_type": "collection", "target": "Foot.L",
     "polygon": [[0.3, 0.0], [0.45, 0.0], [0.45, 0.08], [0.3, 0.08]],
     "color": [0.8, 0.6, 0.4]},
    {"name": "Foot.R", "target_type": "collection", "target": "Foot.R",
     "polygon": [[0.55, 0.0], [0.7, 0.0], [0.7, 0.08], [0.55, 0.08]],
     "color": [0.8, 0.6, 0.4]},
]

_HUMANOID_FACE_ZONES = [
    {"name": "Eyes", "target_type": "collection", "target": "Eyes",
     "polygon": [[0.3, 0.6], [0.7, 0.6], [0.7, 0.75], [0.3, 0.75]],
     "color": [0.5, 0.8, 0.9]},
    {"name": "Jaw", "target_type": "collection", "target": "Jaw",
     "polygon": [[0.35, 0.2], [0.65, 0.2], [0.65, 0.4], [0.35, 0.4]],
     "color": [0.8, 0.5, 0.5]},
    {"name": "Brow", "target_type": "collection", "target": "Brow",
     "polygon": [[0.25, 0.75], [0.75, 0.75], [0.75, 0.9], [0.25, 0.9]],
     "color": [0.6, 0.7, 0.5]},
    {"name": "Nose", "target_type": "collection", "target": "Nose",
     "polygon": [[0.4, 0.45], [0.6, 0.45], [0.6, 0.6], [0.4, 0.6]],
     "color": [0.7, 0.6, 0.8]},
    {"name": "Lips", "target_type": "collection", "target": "Lips",
     "polygon": [[0.35, 0.3], [0.65, 0.3], [0.65, 0.45], [0.35, 0.45]],
     "color": [0.9, 0.4, 0.4]},
    {"name": "Cheek.L", "target_type": "collection", "target": "Cheek.L",
     "polygon": [[0.1, 0.4], [0.3, 0.4], [0.3, 0.6], [0.1, 0.6]],
     "color": [0.8, 0.6, 0.6]},
    {"name": "Cheek.R", "target_type": "collection", "target": "Cheek.R",
     "polygon": [[0.7, 0.4], [0.9, 0.4], [0.9, 0.6], [0.7, 0.6]],
     "color": [0.8, 0.6, 0.6]},
]

# Default visibility bookmarks for Rigify
_DEFAULT_BOOKMARKS = [
    {"name": "Full Rig", "collections": None},  # All visible
    {"name": "IK Body", "filter_prefix": "IK"},
    {"name": "FK Body", "filter_prefix": "FK"},
    {"name": "Face Controls", "filter_prefix": "Face"},
    {"name": "Deform Only", "filter_prefix": "DEF"},
]

# Rigify custom property names commonly found on control bones
_RIGIFY_PROP_GROUPS = {
    "Arm.L": {
        "bone": "upper_arm_parent.L",
        "props": ["IK_FK", "IK_Stretch", "IK_parent"],
    },
    "Arm.R": {
        "bone": "upper_arm_parent.R",
        "props": ["IK_FK", "IK_Stretch", "IK_parent"],
    },
    "Leg.L": {
        "bone": "thigh_parent.L",
        "props": ["IK_FK", "IK_Stretch", "IK_parent"],
    },
    "Leg.R": {
        "bone": "thigh_parent.R",
        "props": ["IK_FK", "IK_Stretch", "IK_parent"],
    },
    "Torso": {
        "bone": "torso",
        "props": ["neck_follow", "head_follow"],
    },
}


# ── Enhancement logic ───────────────────────────────────────────

def _populate_picker(arm_obj):
    """Write default humanoid picker layout to Phase 1 JSON property.

    Only writes if no picker layout exists yet.
    Returns True if picker was populated.
    """
    existing = read_custom_json(arm_obj, "boneforge_picker_layout")
    if existing and (existing.get("body_zones") or existing.get("face_zones")):
        return False

    # Filter zones to only include collections that exist on this armature
    arm_data = arm_obj.data
    coll_names = {c.name for c in arm_data.collections}

    body_zones = []
    for zone in _HUMANOID_BODY_ZONES:
        if zone["target"] in coll_names or zone["target_type"] == "bone":
            body_zones.append(zone)

    face_zones = []
    for zone in _HUMANOID_FACE_ZONES:
        if zone["target"] in coll_names or zone["target_type"] == "bone":
            face_zones.append(zone)

    layout = {"body_zones": body_zones, "face_zones": face_zones}
    write_custom_json(arm_obj, "boneforge_picker_layout", layout)
    return True


def _populate_bookmarks(arm_obj):
    """Write default visibility bookmarks to Phase 1 JSON property.

    Only fills bookmark slots that are not already set.
    Returns the number of bookmarks created.
    """
    existing = read_custom_json(arm_obj, "boneforge_bookmarks")
    existing_names = set()
    if existing and isinstance(existing, list):
        for bm in existing:
            if bm.get("is_set"):
                existing_names.add(bm.get("name", ""))

    arm_data = arm_obj.data
    coll_names = {c.name for c in arm_data.collections}
    created = 0
    bookmarks = existing if isinstance(existing, list) else []

    for bm_def in _DEFAULT_BOOKMARKS:
        name = bm_def["name"]
        if name in existing_names:
            continue

        # Build visibility state
        state = {}
        if bm_def.get("collections") is None:
            # Full Rig — all visible
            state = {c: True for c in coll_names}
        else:
            prefix = bm_def.get("filter_prefix", "")
            for c in coll_names:
                # SIG-7 fix: Use startswith only — no broad substring match
                # that would catch unrelated names like "Linking" for "IK"
                state[c] = c.startswith(prefix)

        bookmarks.append({
            "name": name,
            "state_json": json.dumps(state),
            "color": [0.4, 0.6, 1.0],
            "is_set": True,
        })
        created += 1

    if created > 0:
        write_custom_json(arm_obj, "boneforge_bookmarks", bookmarks)

    return created


def _count_exposed_properties(arm_obj):
    """Count how many Rigify properties can be found on control bones."""
    count = 0
    for group_name, info in _RIGIFY_PROP_GROUPS.items():
        pbone = arm_obj.pose.bones.get(info["bone"])
        if pbone is None:
            continue
        for prop_name in info["props"]:
            if prop_name in pbone:
                count += 1
    return count


# ── Operators ───────────────────────────────────────────────────

class BF_OT_RigifyAutoEnhance(bpy.types.Operator):
    """Detect Rigify rig and apply automatic enhancements"""
    bl_idname = "boneforge.rigify_auto_enhance"
    bl_label = "Rigify Auto-Enhance"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        arm = active_armature(context)
        if arm is None:
            return False
        return is_rigify_human(arm)

    def execute(self, context):
        arm = active_armature(context)
        results = []

        picker_done = _populate_picker(arm)
        if picker_done:
            results.append("populated picker layout")

        bm_count = _populate_bookmarks(arm)
        if bm_count > 0:
            results.append(f"created {bm_count} bookmarks")

        prop_count = _count_exposed_properties(arm)
        if prop_count > 0:
            results.append(f"exposed {prop_count} properties")

        # Mark as enhanced
        arm["boneforge_rigify_enhanced"] = 1

        if results:
            msg = "Enhancement complete: " + ", ".join(results)
        else:
            msg = "Enhancement complete — all slots were already configured"

        self.report({'INFO'}, msg)
        return {'FINISHED'}


class BF_OT_RigifyReEnhance(bpy.types.Operator):
    """Re-run Rigify enhancement after rig updates"""
    bl_idname = "boneforge.rigify_re_enhance"
    bl_label = "Re-run Enhancement"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        arm = active_armature(context)
        if arm is None:
            return False
        return is_rigify_human(arm) and arm.get("boneforge_rigify_enhanced", 0) == 1

    def execute(self, context):
        arm = active_armature(context)
        # Reset marker to allow re-population of empty slots
        arm["boneforge_rigify_enhanced"] = 0

        # Re-run the enhancement
        bpy.ops.boneforge.rigify_auto_enhance()
        return {'FINISHED'}


# ── Panels ──────────────────────────────────────────────────────

class BF_PT_RigifyPropertiesPanel(bpy.types.Panel):
    """Rigify IK/FK blend, stretch, and follow controls"""
    bl_idname = "BONEFORGE_PT_rigify_properties"
    bl_label = " "
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BoneCraft"
    bl_order = 40

    def draw_header(self, context):
        self.layout.label(text=T("Rigify Properties"))

    @classmethod
    def poll(cls, context):
        arm = active_armature(context)
        return arm is not None and is_rigify_human(arm)

    def draw(self, context):
        layout = self.layout
        arm = active_armature(context)

        found_any = False
        for group_name, info in _RIGIFY_PROP_GROUPS.items():
            pbone = arm.pose.bones.get(info["bone"])
            if pbone is None:
                continue

            has_props = any(p in pbone for p in info["props"])
            if not has_props:
                continue

            found_any = True
            box = layout.box()
            box.label(text=group_name, icon='BONE_DATA')

            for prop_name in info["props"]:
                if prop_name in pbone:
                    row = box.row()
                    row.prop(pbone, f'["{prop_name}"]', text=prop_name, slider=True)

        if not found_any:
            layout.label(text=T("No Rigify properties found"), icon='INFO')
            layout.label(text=T("Generate the rig first in Rigify"))


class BF_PT_RigifyEnhancePanel(bpy.types.Panel):
    """Rigify auto-enhancement controls"""
    bl_idname = "BONEFORGE_PT_rigify_enhance"
    bl_label = " "
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BoneCraft"
    bl_order = 41
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text=T("Rigify Enhancement"))

    @classmethod
    def poll(cls, context):
        arm = active_armature(context)
        return arm is not None and is_rigify_human(arm)

    def draw(self, context):
        layout = self.layout
        arm = active_armature(context)

        enhanced = arm.get("boneforge_rigify_enhanced", 0)
        if enhanced:
            layout.label(text=T("Rig has been enhanced"), icon='CHECKMARK')
            layout.operator("boneforge.rigify_re_enhance",
                            text=T("Re-run Enhancement"), icon='FILE_REFRESH')
        else:
            layout.label(text=T("Rigify rig detected"))
            layout.operator("boneforge.rigify_auto_enhance",
                            text=T("Auto-Enhance"), icon='AUTO')


# ── Registration ────────────────────────────────────────────────

classes = (
    BF_OT_RigifyAutoEnhance,
    BF_OT_RigifyReEnhance,
    BF_PT_RigifyPropertiesPanel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
