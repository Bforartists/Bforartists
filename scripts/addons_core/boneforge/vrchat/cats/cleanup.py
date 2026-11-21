"""BoneCraft VRChat — Zero Weight Bones and Loose Geometry Cleanup.

Identify and remove deformation bones with zero influence.
Shows bone list before removing for confirmation.

Category: VRChat Cats Tools.
"""

from typing import List, Tuple

import bpy
from bpy.types import Operator, Panel

from boneforge.core import active_armature
from boneforge.i18n import T


# ─────────────────────────────────────────────────────────────────
# Detection
# ─────────────────────────────────────────────────────────────────

def _find_zero_weight_bones(armature) -> List[Tuple[str, float]]:
    """Find all deform bones with negligible influence.

    Scans all mesh children and checks vertex group weights.
    Returns bones with total influence < 0.001.

    Args:
        armature: The armature object

    Returns:
        List of (bone_name, max_influence) tuples
    """
    zero_weight_bones = {}
    arm_data = armature.data

    # Collect all deform bones
    deform_bones = {bone.name for bone in arm_data.bones if bone.use_deform}

    # Scan mesh children for vertex group weights
    for child in armature.children:
        if child.type != 'MESH':
            continue

        mesh = child.data
        for bone_name in deform_bones:
            # Try to find vertex group with matching bone name
            vgroup = child.vertex_groups.get(bone_name)
            if vgroup is None:
                # Bone has no vertex group → zero weight
                if bone_name not in zero_weight_bones:
                    zero_weight_bones[bone_name] = 0.0
                continue

            # Find max weight in this group
            max_weight = 0.0
            for vert in mesh.vertices:
                for group in vert.groups:
                    if group.group == vgroup.index:
                        max_weight = max(max_weight, group.weight)

            # Update tracking
            if bone_name not in zero_weight_bones:
                zero_weight_bones[bone_name] = max_weight
            else:
                zero_weight_bones[bone_name] = max(zero_weight_bones[bone_name], max_weight)

    # Filter to only truly zero-weight bones
    result = [(name, weight) for name, weight in zero_weight_bones.items() if weight < 0.001]
    result.sort(key=lambda x: x[1])

    return result


def _remove_zero_weight_bones(context, arm, zero_weight_bones=None) -> int:
    """Remove zero-weight bones and reparent children to each removed bone's parent."""
    zero_weight_bones = zero_weight_bones if zero_weight_bones is not None else _find_zero_weight_bones(arm)
    bone_names_to_remove = {name for name, _ in zero_weight_bones}
    if not bone_names_to_remove:
        return 0

    # B-11: Must enter Edit Mode to reparent children before removal
    # Bone.parent is read-only; only EditBone supports reparenting
    saved_active = context.view_layer.objects.active
    context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')

    try:
        edit_bones = arm.data.edit_bones
        removed_count = 0

        for bone_name in bone_names_to_remove:
            if bone_name not in edit_bones:
                continue

            edit_bone = edit_bones[bone_name]
            parent = edit_bone.parent

            # Reparent all children to this bone's parent (grandparent)
            for child in list(edit_bone.children):
                child.parent = parent

            # Now safe to remove
            edit_bones.remove(edit_bone)
            removed_count += 1
    finally:
        bpy.ops.object.mode_set(mode='OBJECT')
        if saved_active and saved_active.name in bpy.data.objects:
            context.view_layer.objects.active = bpy.data.objects[saved_active.name]

    return removed_count


# ─────────────────────────────────────────────────────────────────
# Operator
# ─────────────────────────────────────────────────────────────────

class BF_OT_VRC_RemoveZeroWeightBones(Operator):
    """Remove deformation bones with zero influence"""

    bl_idname = "boneforge.vrc_cleanup_zero_weight_bones"
    bl_label = "Remove Zero Weight Bones"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        """Execute zero-weight bone removal."""
        arm = active_armature(context)
        if arm is None:
            self.report({'ERROR'}, "No active armature")
            return {'CANCELLED'}

        # Find zero-weight bones
        zero_weight_bones = _find_zero_weight_bones(arm)
        if not zero_weight_bones:
            self.report({'INFO'}, "No zero-weight bones found")
            return {'FINISHED'}

        removed_count = _remove_zero_weight_bones(context, arm, zero_weight_bones)
        self.report({'INFO'}, f"Removed {removed_count} zero-weight bones")
        return {'FINISHED'}


# ─────────────────────────────────────────────────────────────────
# Panel
# ─────────────────────────────────────────────────────────────────

class BONEFORGE_PT_vrc_cleanup(Panel):
    """VRChat Cleanup panel"""

    bl_label = " "
    bl_idname = "BONEFORGE_PT_vrc_cleanup"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'data'

    def draw_header(self, context):
        self.layout.label(text=T("Cleanup"))

    def draw(self, context):
        """Draw the panel UI."""
        layout = self.layout
        arm = active_armature(context)

        if arm is None:
            layout.label(text=T("No active armature"), icon='INFO')
            return

        # Detect zero-weight bones
        zero_weight_bones = _find_zero_weight_bones(arm)

        if not zero_weight_bones:
            layout.label(text=T("No zero-weight bones found"), icon='INFO')
        else:
            layout.label(text=f"Found {len(zero_weight_bones)} zero-weight bones:", icon='ERROR')
            layout.separator()

            # Show each bone
            for bone_name, weight in zero_weight_bones:
                row = layout.row()
                row.label(text=bone_name, icon='BONE_DATA')
                row.label(text=f"Max influence: {weight:.6f}")

            layout.separator()
            layout.operator("boneforge.vrc_cleanup_zero_weight_bones", icon='TRASH')


# ─────────────────────────────────────────────────────────────────
# Registration
# ─────────────────────────────────────────────────────────────────

def register():
    """Register cleanup classes."""
    bpy.utils.register_class(BF_OT_VRC_RemoveZeroWeightBones)


def unregister():
    """Unregister cleanup classes."""
    bpy.utils.unregister_class(BF_OT_VRC_RemoveZeroWeightBones)
