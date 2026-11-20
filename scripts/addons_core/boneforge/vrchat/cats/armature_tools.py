"""BoneCraft VRChat CATS — Armature Tools.

Standalone (non-wizard-gated) armature utilities:
  - Merge Armatures: join a secondary armature into the active one, preserving
    mesh children and optionally re-parenting orphaned bones to the root.

Available at any time from the CATS sidebar tab.

Category: VRChat Cats Tools.
"""

import logging

import bpy
from bpy.props import BoolProperty, EnumProperty, PointerProperty
from bpy.types import Operator, Panel, PropertyGroup

from boneforge.i18n import T
from boneforge.vrchat.cats import pipeline

logger = logging.getLogger(__name__)

_SOURCE_BONE_NAME_PROP = "_boneforge_merge_source_name"


def _poll_armature(_self, obj):
    return obj is not None and obj.type == 'ARMATURE'


# ── Settings PropertyGroup ───────────────────────────────────────────────────

class BF_ArmatureToolsSettings(PropertyGroup):
    """Per-scene settings for Armature Tools."""

    target_armature: PointerProperty(
        name="Base / Root Armature",
        description=(
            "The armature that survives the merge. The final object keeps "
            "this armature's name."
        ),
        type=bpy.types.Object,
        poll=_poll_armature,
    )
    source_armature: PointerProperty(
        name="Incoming Armature",
        description=(
            "The secondary armature that is joined into the Base / Root "
            "armature."
        ),
        type=bpy.types.Object,
        poll=_poll_armature,
    )
    auto_parent_bones: BoolProperty(
        name="Auto-Parent Orphan Bones",
        description="Auto-parent unparented bones from source to active armature root",
        default=True,
    )
    join_meshes_after: BoolProperty(
        name="Join Meshes After",
        description="Join all mesh children after merge using shape-key-safe join",
        default=False,
    )
    naming_standard: EnumProperty(
        name="Naming",
        description="Optional pre-merge bone naming cleanup",
        items=[
            ("NONE", "Do Not Rename", "Leave both armatures as-is"),
            ("MIXAMO_PREFIXED", "Mixamo Prefixed", "Normalize to mixamorig:Hips style names"),
            ("MIXAMO_STRIPPED", "Mixamo Stripped", "Normalize to Hips style names"),
        ],
        default="NONE",
    )


# ── Helpers ──────────────────────────────────────────────────────────────────

def _apply_scale(context, obj):
    """Apply scale transform on *obj* to prevent scale mismatch after join."""
    _ensure_object_mode(context)
    bpy.ops.object.select_all(action='DESELECT')
    context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(scale=True)
    obj.select_set(False)


def _ensure_object_mode(context):
    active = context.view_layer.objects.active
    if active is not None and active.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')


def _in_active_view_layer(context, obj):
    return context.view_layer.objects.get(obj.name) == obj


def _root_bone_name(arm_obj):
    """Return the name of the first top-level bone, or None when absent."""
    for bone in arm_obj.data.bones:
        if bone.parent is None:
            return bone.name
    return None


def _tag_source_bones(arm_obj):
    for bone in arm_obj.data.bones:
        bone[_SOURCE_BONE_NAME_PROP] = bone.name


def _clear_source_bone_tags(arm_obj):
    if arm_obj is None or arm_obj.type != 'ARMATURE':
        return
    for bone in arm_obj.data.bones:
        if _SOURCE_BONE_NAME_PROP in bone:
            del bone[_SOURCE_BONE_NAME_PROP]


def _meshes_using_armature(arm_obj):
    meshes = {child for child in arm_obj.children if child.type == 'MESH'}
    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue
        for mod in obj.modifiers:
            if mod.type == 'ARMATURE' and mod.object is arm_obj:
                meshes.add(obj)
                break
    return meshes


def _merge_vertex_group(mesh_obj, src_name, dst_name):
    src_group = mesh_obj.vertex_groups.get(src_name)
    if src_group is None:
        return False
    dst_group = mesh_obj.vertex_groups.get(dst_name)
    if dst_group is None:
        dst_group = mesh_obj.vertex_groups.new(name=dst_name)

    for vert in mesh_obj.data.vertices:
        for group in vert.groups:
            if group.group == src_group.index:
                dst_group.add([vert.index], group.weight, 'ADD')
                break
    mesh_obj.vertex_groups.remove(src_group)
    return True


def _retarget_armature_references(old_arm, new_arm):
    if old_arm is None or old_arm is new_arm:
        return 0

    changed = 0

    def retarget_constraints(constraints):
        nonlocal changed
        for constraint in constraints:
            if getattr(constraint, "target", None) is old_arm:
                constraint.target = new_arm
                changed += 1

    for obj in bpy.data.objects:
        for mod in getattr(obj, "modifiers", ()):
            if mod.type == 'ARMATURE' and mod.object is old_arm:
                mod.object = new_arm
                changed += 1
        retarget_constraints(getattr(obj, "constraints", ()))
        pose = getattr(obj, "pose", None)
        if pose is not None:
            for pose_bone in pose.bones:
                retarget_constraints(pose_bone.constraints)

    return changed


def _retarget_constraint_subtargets(arm_obj, duplicate_to_base):
    changed = 0

    def retarget_constraints(constraints):
        nonlocal changed
        for constraint in constraints:
            if getattr(constraint, "target", None) is not arm_obj:
                continue
            subtarget = getattr(constraint, "subtarget", "")
            if subtarget in duplicate_to_base:
                constraint.subtarget = duplicate_to_base[subtarget]
                changed += 1

    for obj in bpy.data.objects:
        retarget_constraints(getattr(obj, "constraints", ()))
        pose = getattr(obj, "pose", None)
        if pose is not None:
            for pose_bone in pose.bones:
                retarget_constraints(pose_bone.constraints)

    return changed


def _merge_joined_duplicate_bones(context, arm_obj, target_bone_names):
    duplicate_to_base = {}
    for bone in arm_obj.data.bones:
        source_name = bone.get(_SOURCE_BONE_NAME_PROP)
        if source_name in target_bone_names and bone.name != source_name:
            duplicate_to_base[bone.name] = source_name

    if not duplicate_to_base:
        _clear_source_bone_tags(arm_obj)
        return 0, 0, 0

    merged_groups = 0
    for mesh_obj in _meshes_using_armature(arm_obj):
        for duplicate_name, base_name in duplicate_to_base.items():
            if _merge_vertex_group(mesh_obj, duplicate_name, base_name):
                merged_groups += 1

    context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')
    edit_bones = arm_obj.data.edit_bones
    removed = 0
    for duplicate_name, base_name in duplicate_to_base.items():
        duplicate = edit_bones.get(duplicate_name)
        base = edit_bones.get(base_name)
        if duplicate is None or base is None:
            continue
        for child in list(edit_bones):
            if child.parent == duplicate:
                child.parent = base
                child.use_connect = False
        edit_bones.remove(duplicate)
        removed += 1
    bpy.ops.object.mode_set(mode='OBJECT')

    retargeted = _retarget_constraint_subtargets(arm_obj, duplicate_to_base)
    _clear_source_bone_tags(arm_obj)
    return removed, merged_groups, retargeted


# ── Operator ─────────────────────────────────────────────────────────────────

class BF_OT_CATS_MergeArmatures(Operator):
    """Merge a secondary armature into the active armature"""

    bl_idname = "boneforge.cats_merge_armatures"
    bl_label = "Merge Armatures"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        settings = context.scene.boneforge_cats_armature_tools_settings
        if settings.target_armature is None:
            self.report({'ERROR'}, "Choose the Base / Root armature first")
            return {'CANCELLED'}
        if settings.source_armature is None:
            self.report({'ERROR'}, "Choose the Incoming armature first")
            return {'CANCELLED'}
        if settings.source_armature is settings.target_armature:
            self.report({'ERROR'}, "Base and Incoming armatures must be different objects")
            return {'CANCELLED'}
        return self.execute(context)

    def execute(self, context):
        scene = context.scene
        settings = scene.boneforge_cats_armature_tools_settings

        target_arm = settings.target_armature
        if target_arm is None:
            self.report({'ERROR'}, "Choose the Base / Root armature first")
            return {'CANCELLED'}
        if target_arm.type != 'ARMATURE':
            self.report({'ERROR'}, "Base / Root object is not an ARMATURE")
            return {'CANCELLED'}

        source_arm = settings.source_armature
        if source_arm is None:
            self.report({'ERROR'}, "Choose the Incoming armature first")
            return {'CANCELLED'}
        if source_arm.type != 'ARMATURE':
            self.report({'ERROR'}, "Incoming object is not an ARMATURE")
            return {'CANCELLED'}

        if source_arm is target_arm:
            self.report({'ERROR'}, "Base and Incoming armatures must be different objects")
            return {'CANCELLED'}
        if not _in_active_view_layer(context, target_arm):
            self.report({'ERROR'}, f"Base / Root armature '{target_arm.name}' is not in this view layer; enable its collection or pick a visible armature")
            return {'CANCELLED'}
        if not _in_active_view_layer(context, source_arm):
            self.report({'ERROR'}, f"Incoming armature '{source_arm.name}' is not in this view layer; enable its collection or pick a visible armature")
            return {'CANCELLED'}

        _ensure_object_mode(context)

        source_name = source_arm.name
        target_name = target_arm.name
        target_bone_names = {bone.name for bone in target_arm.data.bones}

        # ── Step 1: Apply scale on both armatures ──────────────────────────
        _apply_scale(context, target_arm)
        _apply_scale(context, source_arm)

        # ── Step 2: Record source bone names that have no parent ───────────
        source_root_bones = {
            bone.name for bone in source_arm.data.bones if bone.parent is None
        }

        # ── Step 3: Record source mesh children ───────────────────────────
        source_meshes = list(_meshes_using_armature(source_arm))

        # ── Step 4: Record all source bone names before join ───────────────
        _tag_source_bones(source_arm)

        # ── Step 5: Join armatures ─────────────────────────────────────────
        bpy.ops.object.select_all(action='DESELECT')
        source_arm.select_set(True)
        target_arm.select_set(True)
        context.view_layer.objects.active = target_arm
        if not bpy.ops.object.join.poll():
            _clear_source_bone_tags(source_arm)
            self.report({'ERROR'}, "Could not merge armatures: make both armatures visible and selectable")
            return {'CANCELLED'}
        try:
            bpy.ops.object.join()
        except Exception as exc:
            _clear_source_bone_tags(source_arm)
            self.report({'ERROR'}, f"Could not merge armatures: {exc}")
            return {'CANCELLED'}

        # After join, source_arm is gone; target_arm is the merged result
        merged_arm = bpy.data.objects.get(target_name)
        if merged_arm is None:
            self.report({'ERROR'}, "Merged armature object not found — join may have failed")
            return {'CANCELLED'}

        # ── Step 6: Auto-parent orphaned source bones ──────────────────────
        old_source_arm = bpy.data.objects.get(source_name)
        retargeted_references = 0
        if old_source_arm is not None and old_source_arm is not merged_arm:
            retargeted_references = _retarget_armature_references(old_source_arm, merged_arm)

        merged_bones, merged_groups, retargeted_constraints = _merge_joined_duplicate_bones(
            context,
            merged_arm,
            target_bone_names,
        )

        if settings.auto_parent_bones and source_root_bones:
            context.view_layer.objects.active = merged_arm
            bpy.ops.object.mode_set(mode='EDIT')

            edit_bones = merged_arm.data.edit_bones
            root_name = _root_bone_name(merged_arm)

            # Find the target root (a bone named "Root", or the first parentless bone
            # that was NOT from the source's own root set)
            target_root_eb = None
            if root_name is not None:
                # Prefer a bone explicitly named "Root" from the target
                named_root = edit_bones.get("Root")
                if named_root is not None:
                    target_root_eb = named_root
                else:
                    # Fall back to whatever the first parentless bone is that isn't
                    # one of the source root bones
                    for eb in edit_bones:
                        if eb.parent is None and eb.name not in source_root_bones:
                            target_root_eb = eb
                            break

            if target_root_eb is not None:
                for eb in edit_bones:
                    if eb.name in source_root_bones and eb.parent is None:
                        eb.parent = target_root_eb
                        eb.use_connect = False

            bpy.ops.object.mode_set(mode='OBJECT')

        # ── Step 7: Re-parent source mesh children to merged armature ─────
        for mesh_obj in source_meshes:
            if mesh_obj.name in bpy.data.objects:
                mesh_obj.parent = merged_arm

        # ── Step 8: Optionally join meshes ─────────────────────────────────
        old_source_arm = bpy.data.objects.get(source_name)
        if old_source_arm is not None and old_source_arm is not merged_arm:
            bpy.data.objects.remove(old_source_arm, do_unlink=True)

        if settings.join_meshes_after:
            if hasattr(bpy.ops.boneforge, "vrc_join_meshes"):
                context.view_layer.objects.active = merged_arm
                merged_arm.select_set(True)
                try:
                    bpy.ops.boneforge.vrc_join_meshes()
                except Exception as exc:
                    logger.warning(f"[BoneCraft] Join meshes after merge failed: {exc}")
            else:
                logger.warning("[BoneCraft] boneforge.vrc_join_meshes not registered; skipping post-merge join")

        details = []
        if merged_bones:
            details.append(f"folded {merged_bones} matching bone(s)")
        if merged_groups:
            details.append(f"merged {merged_groups} duplicate vertex group(s)")
        if retargeted_constraints:
            details.append(f"retargeted {retargeted_constraints} constraint(s)")
        if retargeted_references:
            details.append(f"retargeted {retargeted_references} armature reference(s)")
        detail_text = f" ({', '.join(details)})" if details else ""
        msg = f"Merged '{source_name}' into '{target_name}'{detail_text}"
        self.report({'INFO'}, "Armatures merged" + detail_text)
        pipeline.append_ledger(scene, "merge_armatures", pipeline.OUTCOME_CHANGED, msg)

        return {'FINISHED'}


class BF_OT_CATS_NormalizeMergeNames(Operator):
    """Normalize selected merge armatures to the same Mixamo naming style"""

    bl_idname = "boneforge.cats_normalize_merge_names"
    bl_label = "Normalize Merge Names"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = context.scene.boneforge_cats_armature_tools_settings
        if settings.naming_standard == "NONE":
            self.report({'INFO'}, "Choose a naming style first")
            return {'CANCELLED'}
        if settings.target_armature is None or settings.source_armature is None:
            self.report({'ERROR'}, "Choose Base / Root and Incoming armatures first")
            return {'CANCELLED'}

        from boneforge import bone_merge

        renamed = 0
        for arm in (settings.target_armature, settings.source_armature):
            for bone in list(arm.data.bones):
                new_name = bone_merge._canonical(bone.name, settings.naming_standard)
                if new_name and new_name != bone.name:
                    bone_merge._rename_bone_atomic(arm, bone.name, new_name)
                    renamed += 1

        self.report({'INFO'}, f"Normalized {renamed} bone name(s)")
        return {'FINISHED'}


# ── Panel ────────────────────────────────────────────────────────────────────

def draw_merge_armatures_ui(layout, context):
    settings = getattr(context.scene, "boneforge_cats_armature_tools_settings", None)
    if settings is None:
        layout.label(text=T("Armature merge settings unavailable"), icon='ERROR')
        return

    target_arm = settings.target_armature
    source_arm = settings.source_armature
    ready = (
        target_arm is not None
        and source_arm is not None
        and target_arm is not source_arm
    )

    pick = layout.column(align=True)
    pick.prop(settings, "target_armature", text=T("Base / Root"))
    pick.prop(settings, "source_armature", text=T("Incoming"))

    layout.separator(factor=0.5)

    direction = layout.box()
    direction.label(text=T("Merge Direction"))
    row = direction.row(align=True)
    row.label(text=T("Base stays"))
    row.label(text=target_arm.name if target_arm else T("Choose base armature"))
    row = direction.row(align=True)
    row.label(text=T("Incoming merges in"))
    row.label(text=source_arm.name if source_arm else T("Choose incoming armature"))

    if target_arm is not None and source_arm is not None:
        if target_arm is source_arm:
            direction.label(text=T("Choose two different armatures"), icon='ERROR')
        else:
            direction.label(text=f"{source_arm.name} -> {target_arm.name}", icon='FORWARD')
            direction.label(text=T("Result keeps the Base armature name"), icon='INFO')
            direction.label(text=T("Same-name bones fold into the Base"), icon='INFO')
    else:
        direction.label(text=T("Pick both armatures from the scene"), icon='INFO')

    layout.separator(factor=0.5)
    naming = layout.box()
    naming.label(text=T("Naming Prep"))
    # The two options are named after Mixamo, which reads as "only for
    # Mixamo rigs". They are really a generic two-pass name unifier for
    # merging any two armatures, so spell the workflow out here.
    guide = naming.column(align=True)
    guide.label(
        text=T("Match bone names for clean armature merges"), icon='INFO'
    )
    guide.label(text=T("Works on any rig — not just Mixamo imports"))
    guide.label(text=T("1. Select Mixamo Prefixed, then Normalize"))
    guide.label(text=T("2. Select Mixamo Stripped, then Normalize again"))
    guide.label(text=T("Both rigs end on unified names, ready to merge"))
    naming.separator(factor=0.35)
    naming.prop(settings, "naming_standard", text="")
    name_row = naming.row()
    name_row.enabled = ready and settings.naming_standard != "NONE"
    name_row.operator(
        "boneforge.cats_normalize_merge_names",
        text=T("Normalize Merge Names"),
        icon='SORTALPHA',
    )

    layout.separator(factor=0.5)
    layout.prop(settings, "auto_parent_bones", toggle=False)
    layout.prop(settings, "join_meshes_after", toggle=False)

    layout.separator(factor=0.5)
    row = layout.row()
    row.scale_y = 1.4
    row.enabled = ready
    row.operator(
        "boneforge.cats_merge_armatures",
        text=T("Merge Incoming Into Base"),
        icon='AUTOMERGE_ON',
    )


class CATS_PT_armature_tools_standalone(Panel):
    """Armature Tools panel in the CATS sidebar tab."""

    bl_label = " "
    bl_idname = "CATS_PT_armature_tools_standalone"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "CATS"

    def draw_header(self, context):
        self.layout.label(text=T("Armature Tools"))

    @classmethod
    def poll(cls, context):
        return False  # Displayed via CATS_PT_armature_tools in cats_panel.py

    def draw(self, context):
        draw_merge_armatures_ui(self.layout, context)


# ── Registration ─────────────────────────────────────────────────────────────

_classes = (
    BF_ArmatureToolsSettings,
    BF_OT_CATS_MergeArmatures,
    BF_OT_CATS_NormalizeMergeNames,
)


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.boneforge_cats_armature_tools_settings = bpy.props.PointerProperty(
        type=BF_ArmatureToolsSettings
    )


def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
    if hasattr(bpy.types.Scene, "boneforge_cats_armature_tools_settings"):
        del bpy.types.Scene.boneforge_cats_armature_tools_settings
