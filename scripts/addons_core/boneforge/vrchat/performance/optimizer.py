"""BoneCraft VRChat — Automatic Optimization Operators.

Quick-fix operators for common performance issues. Can be toggled in
What-If mode to preview changes before applying them.
Category: Performance.
"""

import bpy
from bpy.props import (
    BoolProperty,
    PointerProperty,
)

from boneforge.i18n import T
from bpy.types import Operator, Panel, PropertyGroup

from boneforge.core import active_armature

# ── Settings property group ────────────────────────────────────

class BF_VRCOptimizerSettings(PropertyGroup):
    """Optimizer What-If mode settings."""

    what_if_mode: BoolProperty(
        name="What-If Mode",
        description="Preview changes without applying them",
        default=True,
    )
    remove_zero_weight_bones: BoolProperty(
        name="Remove Zero-Weight Bones",
        description="Remove deform bones with <0.001 total influence",
        default=False,
    )
    merge_same_material_meshes: BoolProperty(
        name="Merge Same-Material Meshes",
        description="Merge mesh objects that share the same material",
        default=False,
    )
    remove_unused_shape_keys: BoolProperty(
        name="Remove Unused Shape Keys",
        description="Remove shape keys with all-zero deltas",
        default=False,
    )
    remove_unused_vertex_groups: BoolProperty(
        name="Remove Unused Vertex Groups",
        description="Remove vertex groups with no vertices assigned",
        default=False,
    )


# ── Helpers ─────────────────────────────────────────────────────

def _calculate_bone_weight_influence(armature, bone_name):
    """Calculate total weight influence of a bone across all meshes.

    Args:
        armature: Armature object
        bone_name: Name of the bone

    Returns:
        float: Sum of weights across all vertices in all meshes
    """
    total_influence = 0.0

    for obj in bpy.context.scene.objects:
        if obj.type != 'MESH':
            continue

        # Check if mesh is deformed by this armature
        has_armature_modifier = False
        for mod in obj.modifiers:
            if mod.type == 'ARMATURE' and mod.object == armature:
                has_armature_modifier = True
                break

        if not has_armature_modifier:
            continue

        # Find vertex group matching this bone.
        # v3.0.16 fix: vertex_groups is on the Object, not the Mesh data.
        if bone_name not in obj.vertex_groups:
            continue

        vgroup = obj.vertex_groups[bone_name]

        # Sum weights for this vertex group
        for vert in obj.data.vertices:
            for g in vert.groups:
                if g.group == vgroup.index:
                    total_influence += g.weight

    return total_influence


def _get_mesh_objects(armature):
    """Get all mesh objects deformed by the armature.

    Args:
        armature: Armature object

    Returns:
        list of mesh objects
    """
    meshes = []

    for obj in bpy.context.scene.objects:
        if obj.type != 'MESH':
            continue

        for mod in obj.modifiers:
            if mod.type == 'ARMATURE' and mod.object == armature:
                meshes.append(obj)
                break

    return meshes


# ── Operators ───────────────────────────────────────────────────

class BF_OT_VRC_RemoveZeroWeightBones(Operator):
    """Remove deform bones with negligible influence."""
    bl_idname = "boneforge.vrc_remove_zero_weight_bones"
    bl_label = "Remove Zero-Weight Bones"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return active_armature(context) is not None

    def execute(self, context):
        arm = active_armature(context)
        if arm is None:
            self.report({'WARNING'}, "No active armature")
            return {'CANCELLED'}

        settings = context.scene.boneforge_vrc_optimizer
        zero_weight_bones = []

        # Find bones with negligible influence
        for bone in arm.data.bones:
            if not bone.use_deform:
                continue

            influence = _calculate_bone_weight_influence(arm, bone.name)
            if influence < 0.001:
                zero_weight_bones.append(bone.name)

        if not zero_weight_bones:
            self.report({'INFO'}, "No zero-weight bones found")
            return {'FINISHED'}

        # In What-If mode, just report
        if settings.what_if_mode:
            self.report({'INFO'}, f"Would remove {len(zero_weight_bones)} bones: "
                        f"{', '.join(zero_weight_bones[:3])}")
            return {'FINISHED'}

        # Remove bones (set use_deform = False instead of deleting)
        for bone_name in zero_weight_bones:
            bone = arm.data.bones[bone_name]
            bone.use_deform = False

        self.report({'INFO'}, f"Disabled {len(zero_weight_bones)} zero-weight bones")
        return {'FINISHED'}


class BF_OT_VRC_MergeSameMaterialMeshes(Operator):
    """Merge meshes that share the same material."""
    bl_idname = "boneforge.vrc_merge_same_material_meshes"
    bl_label = "Merge Same-Material Meshes"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        arm = active_armature(context)
        return arm is not None and len(_get_mesh_objects(arm)) > 1

    def execute(self, context):
        arm = active_armature(context)
        if arm is None:
            self.report({'WARNING'}, "No active armature")
            return {'CANCELLED'}

        settings = context.scene.boneforge_vrc_optimizer
        meshes = _get_mesh_objects(arm)

        # Group meshes by material
        material_groups = {}
        for mesh_obj in meshes:
            if not mesh_obj.data.materials:
                mat_key = "__NO_MATERIAL__"
            else:
                mat_key = mesh_obj.data.materials[0].name

            if mat_key not in material_groups:
                material_groups[mat_key] = []
            material_groups[mat_key].append(mesh_obj)

        # Count mergeable groups
        mergeable_count = sum(1 for g in material_groups.values() if len(g) > 1)

        if mergeable_count == 0:
            self.report({'INFO'}, "No mesh groups with shared materials found")
            return {'FINISHED'}

        # In What-If mode, just report
        if settings.what_if_mode:
            self.report({'INFO'}, f"Would merge {mergeable_count} groups of same-material meshes")
            return {'FINISHED'}

        # Merge meshes in each group
        for mat_key, mesh_list in material_groups.items():
            if len(mesh_list) <= 1:
                continue

            # Select all meshes in group
            bpy.ops.object.select_all(action='DESELECT')
            for mesh_obj in mesh_list[1:]:
                mesh_obj.select_set(True)

            context.view_layer.objects.active = mesh_list[0]
            mesh_list[0].select_set(True)

            # Join
            bpy.ops.object.join()

        self.report({'INFO'}, f"Merged {mergeable_count} groups")
        return {'FINISHED'}


class BF_OT_VRC_RemoveUnusedShapeKeys(Operator):
    """Remove shape keys with all-zero deltas."""
    bl_idname = "boneforge.vrc_remove_unused_shape_keys"
    bl_label = "Remove Unused Shape Keys"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return (obj and obj.type == 'MESH' and
                obj.data.shape_keys is not None)

    def execute(self, context):
        mesh_obj = context.object

        if mesh_obj.data.shape_keys is None:
            self.report({'INFO'}, "No shape keys on this mesh")
            return {'CANCELLED'}

        settings = context.scene.boneforge_vrc_optimizer
        unused_keys = []

        # v3.1.6 (C-3): The previous test compared key_point.co.length
        # (absolute world coordinate magnitude) against an epsilon. For
        # any mesh that isn't centred on the world origin — i.e. nearly
        # every avatar — this reported every shape key as non-empty and
        # the operator removed nothing. Compare the delta vs the Basis
        # key instead, which is what "unused shape key" actually means.
        basis_block = mesh_obj.data.shape_keys.key_blocks.get("Basis")
        if basis_block is None:
            self.report({'WARNING'}, "Mesh has no Basis shape key")
            return {'CANCELLED'}
        basis_data = basis_block.data
        epsilon_sq = 1e-5 * 1e-5  # squared length avoids the sqrt per vert

        for shape_key in mesh_obj.data.shape_keys.key_blocks:
            if shape_key.name == "Basis":
                continue

            is_empty = True
            for i, key_point in enumerate(shape_key.data):
                delta = key_point.co - basis_data[i].co
                if delta.length_squared > epsilon_sq:
                    is_empty = False
                    break

            if is_empty:
                unused_keys.append(shape_key.name)

        if not unused_keys:
            self.report({'INFO'}, "No unused shape keys found")
            return {'FINISHED'}

        # In What-If mode, just report
        if settings.what_if_mode:
            self.report({'INFO'}, f"Would remove {len(unused_keys)} shape keys: "
                        f"{', '.join(unused_keys[:3])}")
            return {'FINISHED'}

        # Remove unused keys
        for key_name in unused_keys:
            idx = mesh_obj.data.shape_keys.key_blocks.find(key_name)
            if idx >= 0:
                mesh_obj.shape_key_remove(mesh_obj.data.shape_keys.key_blocks[idx])

        self.report({'INFO'}, f"Removed {len(unused_keys)} unused shape keys")
        return {'FINISHED'}


class BF_OT_VRC_RemoveUnusedVertexGroups(Operator):
    """Remove vertex groups with no assigned vertices."""
    bl_idname = "boneforge.vrc_remove_unused_vertex_groups"
    bl_label = "Remove Unused Vertex Groups"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'MESH'

    def execute(self, context):
        mesh_obj = context.object

        settings = context.scene.boneforge_vrc_optimizer
        empty_groups = []

        # Find empty vertex groups
        for vgroup in mesh_obj.vertex_groups:
            has_assigned = False
            for vert in mesh_obj.data.vertices:
                for g in vert.groups:
                    if g.group == vgroup.index and g.weight > 0:
                        has_assigned = True
                        break
                if has_assigned:
                    break

            if not has_assigned:
                empty_groups.append(vgroup.name)

        if not empty_groups:
            self.report({'INFO'}, "No empty vertex groups found")
            return {'FINISHED'}

        # In What-If mode, just report
        if settings.what_if_mode:
            self.report({'INFO'}, f"Would remove {len(empty_groups)} vertex groups: "
                        f"{', '.join(empty_groups[:3])}")
            return {'FINISHED'}

        # Remove empty groups
        for group_name in empty_groups:
            vgroup = mesh_obj.vertex_groups.get(group_name)
            if vgroup:
                mesh_obj.vertex_groups.remove(vgroup)

        self.report({'INFO'}, f"Removed {len(empty_groups)} empty vertex groups")
        return {'FINISHED'}


# ── Panel ───────────────────────────────────────────────────────

class BONEFORGE_PT_vrc_optimizer(Panel):
    """VRChat Automatic Optimizer."""
    bl_idname = "BONEFORGE_PT_vrc_optimizer"
    bl_label = " "
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BoneCraft"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text=T("VRChat Optimizer"))

    @classmethod
    def poll(cls, context):
        # Suppressed from Tool tab — displayed via BoneForge tab VRChat hub.
        return False

    def draw(self, context):
        layout = self.layout
        settings = context.scene.boneforge_vrc_optimizer

        # What-If mode toggle
        row = layout.row()
        row.prop(settings, "what_if_mode", text=T("What-If Mode"),
                 icon='QUESTION' if settings.what_if_mode else 'CHECKMARK')

        if settings.what_if_mode:
            layout.label(text=T("Changes will be simulated only"), icon='INFO')
        else:
            layout.label(text=T("Changes will be applied directly"), icon='ERROR')

        layout.separator()

        # one button per fix (the four toggles that stood here fed nothing and are gone)
        layout.label(text=T("Fixes:"))

        # Individual buttons
        col = layout.column(align=True)

        op = col.operator(
            "boneforge.vrc_remove_zero_weight_bones",
            text=T("Remove Zero-Weight Bones"),
            icon='TRASH'
        )

        col.operator(
            "boneforge.vrc_merge_same_material_meshes",
            text=T("Merge Same-Material Meshes"),
            icon='JOIN'
        )

        col.operator(
            "boneforge.vrc_remove_unused_shape_keys",
            text=T("Remove Unused Shape Keys"),
            icon='SHAPEKEY_DATA'
        )

        col.operator(
            "boneforge.vrc_remove_unused_vertex_groups",
            text=T("Remove Unused Vertex Groups"),
            icon='GROUP_VERTEX'
        )


# ── Registration ────────────────────────────────────────────────

classes = (
    BF_VRCOptimizerSettings,
    BF_OT_VRC_RemoveZeroWeightBones,
    BF_OT_VRC_MergeSameMaterialMeshes,
    BF_OT_VRC_RemoveUnusedShapeKeys,
    BF_OT_VRC_RemoveUnusedVertexGroups,
    BONEFORGE_PT_vrc_optimizer,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.boneforge_vrc_optimizer = PointerProperty(
        type=BF_VRCOptimizerSettings,
        name="BoneCraft VRChat Optimizer Settings",
    )


def unregister():
    del bpy.types.Scene.boneforge_vrc_optimizer

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
