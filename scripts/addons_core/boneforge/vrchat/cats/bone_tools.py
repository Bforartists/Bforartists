"""BoneCraft VRChat CATS — Bone Tools.

Three standalone bone utilities:
  - Create Root Bone: inserts a single root bone and re-parents all top-level
    bones under it.
  - Merge Short Bones: transfers vertex weights to parent and deletes bones
    whose length falls below a configurable threshold.
  - Duplicate Bones: duplicates the current Edit-Mode selection.

Category: VRChat Cats Tools.
"""

import logging

import bpy
from bpy.props import FloatProperty, StringProperty
from bpy.types import Operator, Panel, PropertyGroup

from boneforge.core import active_armature
from boneforge.i18n import T
from boneforge.vrchat.cats import pipeline

logger = logging.getLogger(__name__)


# ── Settings PropertyGroup ───────────────────────────────────────────────────

class BF_BoneToolsSettings(PropertyGroup):
    """Per-scene settings for the Bone Tools panel."""

    root_bone_name: StringProperty(
        name="Root Bone Name",
        description="Name for the new root bone",
        default="Root",
    )
    merge_threshold: FloatProperty(
        name="Merge Threshold",
        description="Bones shorter than this (in Blender units) will have weights merged into their nearest parent",
        default=0.01,
        min=0.001,
        max=1.0,
        unit='LENGTH',
    )


# ── Operator: Create Root Bone ───────────────────────────────────────────────

class BF_OT_CATS_CreateBoneRoot(Operator):
    """Insert a root bone and re-parent all current root bones under it"""

    bl_idname = "boneforge.cats_create_bone_root"
    bl_label = "Create Root Bone"
    bl_options = {'REGISTER', 'UNDO'}

    # an option, tuned after the click in Adjust Last Operation (act first, tune later)
    root_name: StringProperty(
        name="Root Name",
        description="Name for the new root bone",
        default="Root",
    )

    def execute(self, context):
        scene = context.scene
        arm = active_armature(context)

        if arm is None:
            self.report({'ERROR'}, "No active armature")
            return {'CANCELLED'}

        root_name = self.root_name.strip() or "Root"

        # Enter Edit Mode
        saved_active = context.view_layer.objects.active
        context.view_layer.objects.active = arm
        bpy.ops.object.mode_set(mode='EDIT')

        edit_bones = arm.data.edit_bones

        # Collect current root bones (no parent) before creating the new one
        current_roots = [eb for eb in edit_bones if eb.parent is None]

        # Create the new root bone
        new_root = edit_bones.new(root_name)
        new_root.head = (0.0, 0.0, 0.0)
        new_root.tail = (0.0, 0.0, 0.1)
        new_root.parent = None

        # Re-parent existing root bones under the new root
        for eb in current_roots:
            eb.parent = new_root
            eb.use_connect = False

        bpy.ops.object.mode_set(mode='OBJECT')
        context.view_layer.objects.active = saved_active

        n = len(current_roots)
        msg = f"Root bone '{root_name}' created, {n} bone(s) reparented"
        self.report({'INFO'}, msg)
        pipeline.append_ledger(scene, "bone_root", pipeline.OUTCOME_CHANGED, msg)

        return {'FINISHED'}


# ── Operator: Merge Short Bones ──────────────────────────────────────────────

class BF_OT_CATS_MergeBones(Operator):
    """Merge bones shorter than the threshold into their parent, transferring vertex weights"""

    bl_idname = "boneforge.cats_merge_bones"
    bl_label = "Merge Short Bones"
    bl_options = {'REGISTER', 'UNDO'}

    # an option, tuned after the click in Adjust Last Operation
    threshold: FloatProperty(
        name="Merge Threshold",
        description="Bones shorter than this (in Blender units) have their weights merged into the parent",
        default=0.01, min=0.001,
    )

    def _transfer_weights(self, mesh_obj, src_name, dst_name):
        """Add src vertex-group weights into dst vertex group, then remove src group."""
        src_vg = mesh_obj.vertex_groups.get(src_name)
        if src_vg is None:
            return

        dst_vg = mesh_obj.vertex_groups.get(dst_name)
        if dst_vg is None:
            dst_vg = mesh_obj.vertex_groups.new(name=dst_name)

        for vert in mesh_obj.data.vertices:
            src_w = 0.0
            for grp in vert.groups:
                if grp.group == src_vg.index:
                    src_w = grp.weight
                    break
            if src_w > 0.0:
                dst_vg.add([vert.index], src_w, 'ADD')

        mesh_obj.vertex_groups.remove(src_vg)

    def execute(self, context):
        scene = context.scene
        arm = active_armature(context)

        if arm is None:
            self.report({'ERROR'}, "No active armature")
            return {'CANCELLED'}

        threshold = self.threshold
        mesh_children = [c for c in arm.children if c.type == 'MESH']

        # Identify short bones with parents (in Object Mode)
        candidates = []
        for bone in arm.data.bones:
            if bone.length < threshold and bone.parent is not None:
                candidates.append((bone.name, bone.parent.name))

        if not candidates:
            self.report({'INFO'}, "No short bones found below threshold")
            return {'FINISHED'}

        # Transfer vertex weights on all mesh children
        for short_name, parent_name in candidates:
            for mesh_obj in mesh_children:
                self._transfer_weights(mesh_obj, short_name, parent_name)

        # Delete the short bones in Edit Mode
        saved_active = context.view_layer.objects.active
        context.view_layer.objects.active = arm
        bpy.ops.object.mode_set(mode='EDIT')

        edit_bones = arm.data.edit_bones
        short_names_set = {name for name, _ in candidates}
        for eb in list(edit_bones):
            if eb.name in short_names_set:
                edit_bones.remove(eb)

        bpy.ops.object.mode_set(mode='OBJECT')
        context.view_layer.objects.active = saved_active

        count = len(candidates)
        msg = f"Merged {count} short bone(s) into parent(s) (threshold {threshold:.4f})"
        self.report({'INFO'}, msg)
        pipeline.append_ledger(scene, "merge_bones", pipeline.OUTCOME_CHANGED, msg)

        return {'FINISHED'}


# ── Operator: Duplicate Bones ────────────────────────────────────────────────

class BF_OT_CATS_DuplicateBones(Operator):
    """Duplicate selected bones in Edit Mode"""

    bl_idname = "boneforge.cats_duplicate_bones"
    bl_label = "Duplicate Bones"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        arm = active_armature(context)

        if arm is None:
            self.report({'ERROR'}, "No active armature")
            return {'CANCELLED'}

        saved_active = context.view_layer.objects.active
        context.view_layer.objects.active = arm

        prev_mode = arm.mode
        if prev_mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')

        # Count selected bones before duplicating
        selected_count = sum(
            1 for eb in arm.data.edit_bones if eb.select
        )

        if selected_count == 0:
            if prev_mode != 'EDIT':
                bpy.ops.object.mode_set(mode=prev_mode)
            context.view_layer.objects.active = saved_active
            self.report({'WARNING'}, "No bones selected to duplicate")
            return {'CANCELLED'}

        bpy.ops.armature.duplicate()

        if prev_mode != 'EDIT':
            bpy.ops.object.mode_set(mode=prev_mode)

        context.view_layer.objects.active = saved_active

        msg = f"Duplicated {selected_count} selected bone(s)"
        self.report({'INFO'}, msg)
        pipeline.append_ledger(scene, "duplicate_bones", pipeline.OUTCOME_CHANGED, msg)

        return {'FINISHED'}


# ── Panel ────────────────────────────────────────────────────────────────────

class CATS_PT_bone_tools_standalone(Panel):
    """Bone Tools panel in the CATS sidebar tab."""

    bl_label = " "
    bl_idname = "CATS_PT_bone_tools_standalone"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "CATS"

    def draw_header(self, context):
        self.layout.label(text=T("Bone Tools"))

    @classmethod
    def poll(cls, context):
        return False  # Displayed via CATS_PT_bone_tools in cats_panel.py

    def draw(self, context):
        layout = self.layout
        settings = context.scene.boneforge_cats_bone_tools_settings

        # ── Root bone section ──
        box = layout.box()
        box.label(text=T("Root Bone:"))
        box.operator(
            "boneforge.cats_create_bone_root",
            text=T("Create Root Bone"),
            icon='ADD',
        )

        layout.separator()

        # ── Merge section ──
        box = layout.box()
        box.label(text=T("Merge Short Bones:"))
        box.operator(
            "boneforge.cats_merge_bones",
            text=T("Merge Short Bones"),
            icon='AUTOMERGE_ON',
        )

        layout.separator()

        # ── Duplicate section ──
        box = layout.box()
        box.label(text=T("Duplicate Bones:"))
        box.operator(
            "boneforge.cats_duplicate_bones",
            text=T("Duplicate Selected Bones"),
            icon='DUPLICATE',
        )


# ── Registration ─────────────────────────────────────────────────────────────

_classes = (
    BF_BoneToolsSettings,
    BF_OT_CATS_CreateBoneRoot,
    BF_OT_CATS_MergeBones,
    BF_OT_CATS_DuplicateBones,
)


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.boneforge_cats_bone_tools_settings = bpy.props.PointerProperty(
        type=BF_BoneToolsSettings
    )


def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
    if hasattr(bpy.types.Scene, "boneforge_cats_bone_tools_settings"):
        del bpy.types.Scene.boneforge_cats_bone_tools_settings
