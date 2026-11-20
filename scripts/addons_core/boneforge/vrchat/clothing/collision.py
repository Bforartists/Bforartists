"""BoneCraft VRChat — Bone Name Collision Detection.

Detects and resolves bone name collisions between base and clothing armatures.
Provides collision detection and renaming with clothing item prefix.

Category: Clothing.
"""

import bpy
from bpy.props import StringProperty
from bpy.types import Operator, Panel

import logging

from boneforge.i18n import T

logger = logging.getLogger(__name__)


# ── Collision Detection ──────────────────────────────────────────

def detect_collisions(base_armature: bpy.types.Object,
                      clothing_armature: bpy.types.Object) -> list[dict]:
    """Detect bone name collisions between base and clothing armatures.

    Args:
        base_armature: Base avatar armature object
        clothing_armature: Clothing armature object

    Returns:
        List of collision dicts with:
        {
            'bone_name': str (clothing bone name),
            'proposed_rename': str (suggested new name with prefix),
            'collision_with': str (base armature bone name)
        }
    """
    if not (base_armature and base_armature.type == 'ARMATURE'):
        return []
    if not (clothing_armature and clothing_armature.type == 'ARMATURE'):
        return []

    base_data = base_armature.data
    clothing_data = clothing_armature.data

    # Build set of base bone names for quick lookup
    base_bone_names = {bone.name for bone in base_data.bones}

    # Get clothing item name from armature (or use generic suffix)
    clothing_name = clothing_armature.name.replace("Armature", "").replace(".001", "").strip()
    if not clothing_name:
        clothing_name = "Clothing"

    collisions = []

    for clothing_bone in clothing_data.bones:
        if clothing_bone.name in base_bone_names:
            proposed_rename = f"{clothing_name}_{clothing_bone.name}"
            collisions.append({
                'bone_name': clothing_bone.name,
                'proposed_rename': proposed_rename,
                'collision_with': clothing_bone.name
            })

    return collisions


def resolve_collisions(clothing_armature: bpy.types.Object,
                       collision_list: list[dict]) -> int:
    """Apply collision-resolved renames to clothing armature bones.

    Args:
        clothing_armature: Clothing armature to rename
        collision_list: List of collision dicts from detect_collisions

    Returns:
        Number of bones successfully renamed
    """
    if not (clothing_armature and clothing_armature.type == 'ARMATURE'):
        return 0

    clothing_data = clothing_armature.data
    renamed_count = 0

    for collision in collision_list:
        bone_name = collision.get('bone_name')
        new_name = collision.get('proposed_rename')

        if bone_name in clothing_data.bones:
            try:
                bone = clothing_data.bones[bone_name]
                bone.name = new_name
                renamed_count += 1
            except RuntimeError as e:
                logger.error(f"[BoneCraft] Failed to rename bone '{bone_name}': {e}")

    return renamed_count


# ── Operators ───────────────────────────────────────────────────

class BF_OT_VRC_DetectCollisions(Operator):
    """Detect bone name collisions between base and clothing armatures."""
    bl_idname = "boneforge.vrc_detect_collisions"
    bl_label = "Detect Collisions"
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

        # Detect collisions
        collisions = detect_collisions(base_arm, clothing_arm)

        # Store in scene
        import json
        scene.boneforge_vrc_detected_collisions = json.dumps(collisions)

        if collisions:
            self.report({'WARNING'}, f"Found {len(collisions)} collision(s)")
        else:
            self.report({'INFO'}, "No collisions detected")

        return {'FINISHED'}


class BF_OT_VRC_ResolveCollisions(Operator):
    """Apply collision-resolved renames to clothing armature."""
    bl_idname = "boneforge.vrc_resolve_collisions"
    bl_label = "Resolve Collisions"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (context.mode == 'OBJECT' and
                context.active_object and
                context.active_object.type == 'ARMATURE')

    def execute(self, context):
        scene = context.scene
        clothing_arm = context.active_object

        # Retrieve stored collisions
        import json
        try:
            collisions = json.loads(scene.boneforge_vrc_detected_collisions)
        except Exception:
            self.report({'ERROR'}, "No collision data found. Run Detect Collisions first.")
            return {'CANCELLED'}

        # Resolve
        renamed_count = resolve_collisions(clothing_arm, collisions)

        self.report({'INFO'}, f"Renamed {renamed_count} bones")

        return {'FINISHED'}


# ── Panel ───────────────────────────────────────────────────────

class BONEFORGE_PT_vrc_collision(Panel):
    """Collision detection and resolution panel."""
    bl_label = " "
    bl_idname = "BONEFORGE_PT_vrc_collision"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BoneCraft"

    def draw_header(self, context):
        self.layout.label(text=T("Collision Detection"))

    @classmethod
    def poll(cls, context):
        # Suppressed from Tool tab — displayed via BoneForge tab VRChat hub.
        return False

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        col = layout.column(align=True)
        col.label(text=T("Collision Detection"))
        col.operator("boneforge.vrc_detect_collisions", text=T("Detect Collisions"))

        # Display detected collisions
        try:
            import json
            collisions = json.loads(scene.boneforge_vrc_detected_collisions)
            if collisions:
                col.separator()
                col.label(text=f"Found: {len(collisions)} collision(s)")

                for collision in collisions[:5]:  # Show first 5
                    box = col.box()
                    box.label(text=collision['bone_name'], icon='ERROR')
                    box.label(text=f"→ {collision['proposed_rename']}")

                if len(collisions) > 5:
                    col.label(text=f"... and {len(collisions) - 5} more")

                col.separator()
                col.operator("boneforge.vrc_resolve_collisions",
                           text=T("Accept Renames"))
        except (json.JSONDecodeError, KeyError):
            pass  # No collision data to display


# ── Registration ────────────────────────────────────────────────

def register():
    """Register collision detection module."""
    bpy.utils.register_class(BF_OT_VRC_DetectCollisions)
    bpy.utils.register_class(BF_OT_VRC_ResolveCollisions)
    bpy.utils.register_class(BONEFORGE_PT_vrc_collision)

    # Scene property for storing detected collisions
    from bpy.props import StringProperty
    bpy.types.Scene.boneforge_vrc_detected_collisions = StringProperty(default="[]")


def unregister():
    """Unregister collision detection module."""
    bpy.utils.unregister_class(BONEFORGE_PT_vrc_collision)
    bpy.utils.unregister_class(BF_OT_VRC_ResolveCollisions)
    bpy.utils.unregister_class(BF_OT_VRC_DetectCollisions)

    if hasattr(bpy.types.Scene, 'boneforge_vrc_detected_collisions'):
        del bpy.types.Scene.boneforge_vrc_detected_collisions
