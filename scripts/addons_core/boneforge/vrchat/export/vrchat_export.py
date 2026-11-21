"""BoneCraft VRChat — VRChat-Aware FBX Export.

Exports rigged avatars to FBX format with VRChat-compatible settings.
Includes pre-export validation, optional sidecar generation, and summary reporting.

Category: VRChat Export.
"""

import os
from typing import Tuple, List

import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator, PropertyGroup

from boneforge.core import active_armature, read_custom_json
from boneforge.vrchat.humanoid.mapper import HumanoidMapping, REQUIRED_SLOTS
from boneforge.io_hub.bone_naming import (
    naming_items, draw_naming, export_copies, make_plan, remap_sidecar,
    deselect_objects, object_export_context,
)

import logging

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────
# Property Group
# ─────────────────────────────────────────────────────────────────

class BF_VRCExportSettings(PropertyGroup):
    bone_naming: EnumProperty(
        name="Bone Names", items=naming_items, default=0,
        description="Bone naming preset for export copies only",
    )
    """VRChat export settings stored on the scene."""

    export_path: StringProperty(
        name="Export Path",
        description="Directory to export FBX and sidecar files to",
        subtype='DIR_PATH',
        default="//",
    )
    avatar_name: StringProperty(
        name="Avatar Name",
        description="Name for the exported avatar",
        default="Avatar",
    )
    include_clothing_separate: BoolProperty(
        name="Include Clothing Separate",
        description="Export clothing as separate meshes (do not merge with body)",
        default=True,
    )
    merge_all_meshes: BoolProperty(
        name="Merge All Meshes",
        description="Join all meshes into a single mesh object",
        default=False,
    )
    apply_shape_keys_to_basis: BoolProperty(
        name="Remove Shape Keys",
        description=(
            "Delete ALL shape keys (blendshapes) from the exported meshes, "
            "collapsing them to the basis shape. Leave OFF to keep "
            "blendshapes (visemes, blinking, MMD morphs, etc.) in the FBX"
        ),
        default=False,
    )
    export_sidecar: BoolProperty(
        name="Export Sidecar",
        description="Generate .bfvrc JSON sidecar with metadata",
        default=True,
    )
    embed_textures: BoolProperty(
        name="Embed Textures",
        description="Pack image textures into the FBX for easier Unity material import",
        default=True,
    )
    include_helper_meshes: BoolProperty(
        name="Include Helper Meshes",
        description="Include hidden/render-disabled/custom-shape helper meshes in the FBX",
        default=False,
    )


# ─────────────────────────────────────────────────────────────────
# Validation Helpers
# ─────────────────────────────────────────────────────────────────

def _check_required_armature(armature) -> List[str]:
    """Check basic armature requirements for VRChat export."""
    failures = []

    if armature is None:
        failures.append("No active armature selected")
        return failures

    if armature.type != 'ARMATURE':
        failures.append(f"Object '{armature.name}' is not an armature")
        return failures

    if not armature.data.bones:
        failures.append("Armature has no bones")

    return failures


def _check_required_meshes(armature) -> List[str]:
    """Check that armature has at least one skinned mesh child."""
    failures = []
    mesh_children = _exportable_mesh_children(armature)

    if not mesh_children:
        failures.append("Armature has no mesh children to export")
        return failures

    has_skinned = any(
        m.data.shape_keys or any(mod.type == 'ARMATURE' for mod in m.modifiers)
        for m in mesh_children
    )
    if not has_skinned:
        failures.append("No skinned meshes found (meshes must be rigged with armature modifier)")

    return failures


def _custom_shape_object_names(armature) -> set:
    pose = getattr(armature, "pose", None)
    if pose is None:
        return set()
    names = set()
    for pose_bone in pose.bones:
        custom_shape = getattr(pose_bone, "custom_shape", None)
        if custom_shape is not None:
            names.add(custom_shape.name)
    return names


def _exportable_mesh_children(armature, include_helper_meshes=False) -> List:
    """Return avatar meshes, excluding rig helper/control shapes by default."""
    helper_names = _custom_shape_object_names(armature)
    meshes = []
    for child in armature.children:
        if child.type != 'MESH':
            continue
        if not include_helper_meshes:
            if child.name in helper_names:
                continue
            if getattr(child, "hide_render", False):
                continue
            if child.get("boneforge_export") is False:
                continue
        meshes.append(child)
    return meshes


def _check_required_humanoid(armature) -> List[str]:
    """Check Unity humanoid mapping completeness."""
    failures = []
    humanoid_data = read_custom_json(armature, "boneforge_vrchat_humanoid", {})

    mapping = HumanoidMapping(humanoid_data if isinstance(humanoid_data, dict) else {})
    missing = mapping.validate_required(armature)
    if missing:
        mapped_slots = len(REQUIRED_SLOTS) - len(missing)
        preview = ", ".join(missing[:5])
        suffix = "..." if len(missing) > 5 else ""
        failures.append(
            f"Unity humanoid mapping incomplete or invalid: only "
            f"{mapped_slots}/{len(REQUIRED_SLOTS)} required slots mapped "
            f"(missing/invalid: {preview}{suffix})"
        )

    return failures


def _resolve_export_dir(settings) -> str:
    """Resolve the scene export folder, keeping unsaved // paths invalid."""
    raw_path = (settings.export_path or "").strip()
    if not raw_path:
        return ""
    if raw_path.startswith("//") and not bpy.data.filepath:
        return ""
    return bpy.path.abspath(raw_path)


def _check_required_export_path() -> List[str]:
    """Check that an export path has been configured."""
    failures = []
    settings = bpy.context.scene.boneforge_vrc_export_settings
    export_path = _resolve_export_dir(settings)

    if not export_path:
        failures.append("FBX export path is not set (save the .blend or choose an export folder)")

    return failures


def _check_required_vertex_groups(armature) -> List[str]:
    """Check for vertex groups referencing non-existent bones."""
    failures = []
    bone_names = set(b.name for b in armature.data.bones)
    mesh_children = [c for c in armature.children if c.type == 'MESH']

    for mesh_obj in mesh_children:
        for vgroup in mesh_obj.vertex_groups:
            if vgroup.name not in bone_names:
                failures.append(
                    f"Mesh '{mesh_obj.name}' has vertex group '{vgroup.name}' with no matching bone"
                )
                break

    return failures


def _check_recommended(armature) -> List[str]:
    """Run recommended (non-blocking) pre-export checks."""
    warnings = []
    arm_data = armature.data

    # Viseme completeness
    viseme_data = read_custom_json(armature, "boneforge_vrchat_visemes", {})
    if isinstance(viseme_data, dict):
        viseme_count = len([v for v in viseme_data.values() if v])
        if viseme_count < 14:
            warnings.append(f"Only {viseme_count}/14 VRChat visemes configured (non-blocking)")

    # Eye bones
    left_eye, right_eye = None, None
    # M-08: Include VRoid eye bone patterns
    eye_patterns = ["eye", "Eye", "目", "J_Bip_", "mixamorig:Eye", "j_bip_c_eye"]
    for bone in arm_data.bones:
        bone_lower = bone.name.lower()
        if any(pat in bone.name for pat in eye_patterns):
            if "left" in bone_lower or ".l" in bone_lower:
                left_eye = bone.name
            elif "right" in bone_lower or ".r" in bone_lower:
                right_eye = bone.name
    if not left_eye or not right_eye:
        warnings.append("Missing eye bones for VRChat eye tracking (at least one per side)")

    # Performance rank
    # v3.1.6 (C-1): the previous "from . import performance" resolved to
    # boneforge.vrchat.export.performance (which doesn't exist) and the
    # ImportError silently disabled this warning. Import the function
    # directly from rank.py and only suppress the failure if the module
    # itself is genuinely unavailable.
    try:
        from boneforge.vrchat.performance.rank import calculate_overall_rank
    except ImportError as exc:
        logger.warning("[BoneCraft] performance rank unavailable: %s", exc)
    else:
        rank, _ = calculate_overall_rank(armature)
        if rank == "VeryPoor":
            warnings.append("Avatar performance rank is VeryPoor (optimization recommended)")

    # Bone name constraints
    for bone in arm_data.bones:
        if len(bone.name) > 63:
            warnings.append(f"Bone '{bone.name}' exceeds 63 character limit (Unity constraint)")
            break
        if " " in bone.name or any(c in bone.name for c in "!@#$%^&*()[]{}"):
            warnings.append(
                f"Bone '{bone.name}' contains spaces or special characters (may cause Unity issues)"
            )
            break

    # General sanity
    if len(arm_data.bones) < 15:
        warnings.append("Armature has very few bones (< 15). Is this intentional?")

    for bone in arm_data.bones:
        if abs(bone.length) < 0.001:
            warnings.append(f"Bone '{bone.name}' may have zero scale/length")
            break

    return warnings


def _run_pre_export_checks(armature) -> Tuple[List[str], List[str]]:
    """Run pre-export validation on the armature.

    Checks both required VRChat-specific constraints and recommended best practices.

    Returns:
        (required_failures, recommended_warnings) - two lists of human-readable messages
    """
    required = []

    # Required checks (any failure blocks export)
    required.extend(_check_required_armature(armature))
    if required:
        return required, []

    required.extend(_check_required_meshes(armature))
    required.extend(_check_required_humanoid(armature))
    required.extend(_check_required_export_path())
    required.extend(_check_required_vertex_groups(armature))

    # Recommended checks (warnings only)
    recommended = _check_recommended(armature)

    return required, recommended


def _select_avatar_objects(armature) -> None:
    """Select the armature and all mesh/curve children for export.

    Args:
        armature: The armature object to select along with its children
    """
    # Deselect all
    deselect_objects(bpy.context)

    # Select armature
    armature.select_set(True)

    # Select all mesh and curve children
    for child in armature.children:
        if child.type in ('MESH', 'CURVE'):
            child.select_set(True)


def _apply_mesh_modifiers_nonarmature(meshes: List, context=None) -> None:
    """Apply all non-armature modifiers on the given mesh objects.

    v3.1.6 (C-2): bpy.ops.object.modifier_apply operates on the active
    object, not the iterated mesh — without setting the active object
    per iteration the call either errors out (and the RuntimeError was
    silently swallowed) or applies the wrong modifier stack. Use
    context.temp_override on Blender 3.2+ to scope active object cleanly,
    falling back to manual save/restore on older versions.

    Args:
        meshes: List of mesh objects to process
        context: Blender context (defaults to bpy.context if None)
    """
    if context is None:
        context = bpy.context

    view_layer = context.view_layer

    for mesh_obj in meshes:
        if mesh_obj.type != 'MESH':
            continue

        # Blendshape fix: modifier_apply refuses meshes with shape keys
        # ("Modifier cannot be applied to a mesh with shape keys"), so skip
        # them here — the export path strips those modifiers from the temp
        # copies instead, preserving the shape keys.
        if mesh_obj.data.shape_keys and len(mesh_obj.data.shape_keys.key_blocks) > 1:
            logger.warning(
                "[BoneCraft] skipping modifier apply on '%s' (has shape keys)",
                mesh_obj.name,
            )
            continue

        # Snapshot of modifier names — the list mutates as we apply.
        applicable = [m.name for m in mesh_obj.modifiers if m.type != 'ARMATURE']

        for mod_name in applicable:
            try:
                if hasattr(context, 'temp_override'):
                    # Blendshape fix: must override 'object' as well — with
                    # only active_object set, modifier_apply silently no-ops.
                    with context.temp_override(object=mesh_obj,
                                               active_object=mesh_obj,
                                               selected_objects=[mesh_obj]):
                        bpy.ops.object.modifier_apply(modifier=mod_name)
                else:
                    saved_active = view_layer.objects.active
                    view_layer.objects.active = mesh_obj
                    try:
                        bpy.ops.object.modifier_apply(modifier=mod_name)
                    finally:
                        view_layer.objects.active = saved_active
            except RuntimeError as exc:
                logger.warning(
                    "[BoneCraft] could not apply modifier '%s' on '%s': %s",
                    mod_name, mesh_obj.name, exc,
                )


def _merge_shape_keys_to_basis(mesh_obj) -> None:
    """Collapse all shape keys to basis shape.

    Args:
        mesh_obj: Mesh object with potential shape keys
    """
    if not mesh_obj.data.shape_keys:
        return

    # Set basis to current state by evaluating all shape keys to 0
    for kb in mesh_obj.data.shape_keys.key_blocks[1:]:
        kb.value = 0.0

    # Remove all non-basis shape keys
    for kb in list(mesh_obj.data.shape_keys.key_blocks[1:]):
        mesh_obj.shape_key_remove(kb)


# ─────────────────────────────────────────────────────────────────
# Main Export Operator
# ─────────────────────────────────────────────────────────────────

class BF_OT_VRC_ExportToUnity(Operator):
    """Export avatar to VRChat-compatible FBX with validation and optional sidecar"""

    bl_idname = "boneforge.vrc_export_to_unity"
    bl_label = "Export to VRChat (Unity)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        try:
            with object_export_context(context):
                return self._execute_object_mode(context)
        except (RuntimeError, ValueError, OSError) as exc:
            self.report({'ERROR'}, f'Export failed: {exc}')
            return {'CANCELLED'}

    def _execute_object_mode(self, context):
        """Main export workflow."""
        arm = active_armature(context)
        if arm is None:
            self.report({'ERROR'}, "No active armature")
            return {'CANCELLED'}

        settings = context.scene.boneforge_vrc_export_settings

        # ─ Step 1: Run pre-export checklist ─
        required_failures, recommended_warnings = _run_pre_export_checks(arm)

        if required_failures:
            fail_text = "\n".join(f"  • {msg}" for msg in required_failures)
            self.report({'ERROR'}, f"Export blocked by required checks:\n{fail_text}")
            return {'CANCELLED'}

        if recommended_warnings:
            warn_text = "\n".join(f"  • {msg}" for msg in recommended_warnings)
            logger.warning(f"[BoneCraft] Export warnings (non-blocking):\n{warn_text}")

        # ─ Step 2: Validate paths ─
        export_dir = _resolve_export_dir(settings)
        if not os.path.isdir(export_dir):
            self.report({'ERROR'}, f"Export directory does not exist: {export_dir}")
            return {'CANCELLED'}

        # Construct FBX path
        avatar_name = settings.avatar_name or "Avatar"
        fbx_filename = f"{avatar_name}.fbx"
        fbx_path = os.path.join(export_dir, fbx_filename)

        # ─ Step 3: Prepare scene state ─
        saved_selection = set(obj.name for obj in context.selected_objects)
        saved_active = context.view_layer.objects.active
        saved_frame = context.scene.frame_current

        temp_meshes = []
        renamed = []               # (orig_obj, name, orig_data, data_name)
        shapekey_mod_warnings = []

        try:
            # Collect all children
            mesh_children = _exportable_mesh_children(
                arm,
                settings.include_helper_meshes,
            )

            # ─ Step 4: Prepare temp duplicates for destructive ops ─
            # Blendshape fix: the duplicates are exported under the ORIGINAL
            # names (the originals are parked as "<name>.bfexport_orig" and
            # restored in `finally`), so Unity sees "Body" instead of
            # "__BF_EXPORT_TMP_Body".
            for mesh_obj in mesh_children:
                world_matrix = mesh_obj.matrix_world.copy()
                orig_name = mesh_obj.name
                orig_data = mesh_obj.data
                orig_data_name = orig_data.name
                dup = mesh_obj.copy()
                dup.data = mesh_obj.data.copy()
                mesh_obj.name = f"{orig_name}.bfexport_orig"
                orig_data.name = f"{orig_data_name}.bfexport_orig"
                dup.name = orig_name
                dup.data.name = orig_data_name
                renamed.append((mesh_obj, orig_name, orig_data, orig_data_name))
                context.scene.collection.objects.link(dup)
                dup.parent = mesh_obj.parent
                dup.matrix_parent_inverse = mesh_obj.matrix_parent_inverse.copy()
                dup.matrix_world = world_matrix
                temp_meshes.append(dup)

            if settings.apply_shape_keys_to_basis and temp_meshes:
                for mesh_obj in temp_meshes:
                    _merge_shape_keys_to_basis(mesh_obj)

            # ─ Step 5: Protect blendshapes from the FBX modifier bake ─
            # Blendshape fix: with use_mesh_modifiers=True (the exporter
            # default), Blender's FBX exporter silently DROPS every shape key
            # on any mesh that still has an enabled non-armature modifier —
            # the modifier stack is baked via an evaluated mesh, which
            # carries no shape-key data. Remove those modifiers from the
            # temp copies so blendshapes survive. Meshes WITHOUT shape keys
            # are untouched: the exporter bakes their modifiers as before.
            for dup in temp_meshes:
                keys = dup.data.shape_keys
                if not keys or len(keys.key_blocks) <= 1:
                    continue
                dropped = []
                for mod in list(dup.modifiers):
                    if mod.type == 'ARMATURE':
                        continue
                    if mod.show_render or mod.show_viewport:
                        dropped.append(mod.name)
                    dup.modifiers.remove(mod)
                if dropped:
                    shapekey_mod_warnings.append(
                        f"{dup.name} ({', '.join(dropped)})"
                    )

            # ─ Step 6: Select arm + temp copies for export ─
            deselect_objects(context)
            arm.select_set(True)
            for t in temp_meshes:
                t.select_set(True)
            context.view_layer.objects.active = arm

            # ─ Step 7: Call FBX export ─
            with export_copies(context, [arm] + temp_meshes, settings.bone_naming) as export_objects:
                result = bpy.ops.export_scene.fbx(
                    filepath=fbx_path,
                    use_selection=True,
                    apply_unit_scale=True,
                    apply_scale_options='FBX_SCALE_ALL',
                    axis_forward='-Z',
                    axis_up='Y',
                    use_armature_deform_only=True,
                    add_leaf_bones=False,
                    primary_bone_axis='Y',
                    secondary_bone_axis='X',
                    path_mode='COPY',
                    embed_textures=settings.embed_textures,
                    mesh_smooth_type='FACE',
                    bake_anim=False,
                )

                if 'FINISHED' not in result:
                    raise RuntimeError('FBX exporter cancelled')

                # ─ Step 8: Generate sidecar if enabled ─
                if settings.export_sidecar:
                    try:
                        from . import sidecar
                        sidecar_data = remap_sidecar(
                            sidecar.generate_sidecar(arm, settings),
                            *make_plan(arm, settings.bone_naming),
                        )
                        sidecar_path = fbx_path.replace('.fbx', '.bfvrc')
                        sidecar.write_sidecar(sidecar_data, sidecar_path)
                    except Exception as e:
                        self.report({'WARNING'}, f"Sidecar generation failed: {e}")

            # ─ Step 9: Post-export summary ─
            self.report({'INFO'}, f"Exported to {fbx_path}")
            if shapekey_mod_warnings:
                self.report(
                    {'WARNING'},
                    "Blendshapes kept, but these modifiers were NOT baked "
                    "into the FBX (they cannot be applied to meshes with "
                    "shape keys — apply or remove them manually if you need "
                    "their geometry): " + "; ".join(shapekey_mod_warnings)
                )

        except (RuntimeError, ValueError) as exc:
            self.report({'ERROR'}, f'Export failed: {exc}')
            return {'CANCELLED'}

        finally:
            # Remove temp duplicates (also on error paths — the previous
            # implementation leaked them if the FBX exporter raised).
            for t in temp_meshes:
                try:
                    dup_data = t.data
                    bpy.data.objects.remove(t, do_unlink=True)
                    # Also purge the copied mesh datablock — leaving it
                    # orphaned would keep the original names occupied
                    # (".001" drift) until the next save/purge.
                    if dup_data is not None and dup_data.users == 0:
                        bpy.data.meshes.remove(dup_data)
                except (ReferenceError, RuntimeError) as exc:
                    logger.debug("temp mesh cleanup failed: %s", exc)
            # Give the originals their names back (after the dups are gone,
            # so Blender doesn't dodge a collision with ".001" suffixes).
            for orig_obj, orig_name, orig_data, orig_data_name in renamed:
                try:
                    orig_obj.name = orig_name
                    orig_data.name = orig_data_name
                except (ReferenceError, RuntimeError) as exc:
                    logger.debug("name restore failed: %s", exc)
            # Restore scene state
            deselect_objects(context)
            for obj_name in saved_selection:
                try:
                    bpy.data.objects[obj_name].select_set(True)
                except KeyError as exc:
                    logger.debug("./vrchat/export/vrchat_export.py suppressed KeyError: %s", exc)
            if saved_active and saved_active.name in bpy.data.objects:
                context.view_layer.objects.active = bpy.data.objects[saved_active.name]
            context.scene.frame_current = saved_frame

        return {'FINISHED'}


def draw_export_settings(layout, context):
    """Draw VRChat export settings next to any export button."""
    settings = getattr(context.scene, "boneforge_vrc_export_settings", None)
    if settings is None:
        layout.label(text="Export settings unavailable", icon='ERROR')
        return

    box = layout.box()
    box.label(text="Export Settings")
    box.prop(settings, "export_path", text="Folder")
    box.prop(settings, "avatar_name", text="Avatar")
    draw_naming(box, settings, context)

    row = box.row(align=True)
    row.prop(settings, "export_sidecar", text="Sidecar")
    row.prop(settings, "merge_all_meshes", text="Merge Meshes")

    row = box.row(align=True)
    row.prop(settings, "include_clothing_separate", text="Separate Clothing")
    row.prop(settings, "apply_shape_keys_to_basis", text="Remove Shape Keys")

    row = box.row(align=True)
    row.prop(settings, "embed_textures", text="Embed Textures")
    row.prop(settings, "include_helper_meshes", text="Helper Meshes")

    armature = active_armature(context)
    box.separator(factor=0.5)
    if armature is None:
        box.label(text="Humanoid: select an armature to map", icon='ERROR')
        return

    humanoid_data = read_custom_json(armature, "boneforge_vrchat_humanoid", {})
    if not isinstance(humanoid_data, dict):
        humanoid_data = {}
    mapping = HumanoidMapping(humanoid_data)
    missing = mapping.validate_required(armature)
    mapped = len(REQUIRED_SLOTS) - len(missing)

    row = box.row(align=True)
    row.label(
        text=f"Humanoid: {mapped}/{len(REQUIRED_SLOTS)} required slots",
        icon='CHECKMARK' if not missing else 'ERROR',
    )

    if missing:
        box.label(text=f"Missing/invalid: {', '.join(missing[:5])}", icon='INFO')

    # Every required slot missing almost always means the mapping step
    # simply hasn't been run yet — not that the rig is unusable. Say so,
    # instead of leaving a wall of red slot names as the only feedback.
    if mapped == 0:
        hint = box.column(align=True)
        hint.label(text="Not mapped yet — this is the first step", icon='INFO')
        hint.label(text="Click Auto-Map Humanoid below to detect bones")

    row = box.row(align=True)
    row.operator(
        "boneforge.vrc_auto_map_humanoid",
        text="Auto-Map Humanoid",
        icon='AUTO',
    )
    row.operator(
        "boneforge.vrc_normalize_humanoid_names",
        text="Normalize Names",
        icon='SORTALPHA',
    )
    row = box.row(align=True)
    row.operator(
        "boneforge.vrc_validate_humanoid_mapping",
        text="Validate",
        icon='CHECKMARK',
    )


# ─────────────────────────────────────────────────────────────────
# Registration
# ─────────────────────────────────────────────────────────────────

def register():
    """Register export classes."""
    bpy.utils.register_class(BF_VRCExportSettings)
    bpy.utils.register_class(BF_OT_VRC_ExportToUnity)

    # Add property to scene
    bpy.types.Scene.boneforge_vrc_export_settings = bpy.props.PointerProperty(
        type=BF_VRCExportSettings
    )


def unregister():
    """Unregister export classes."""
    bpy.utils.unregister_class(BF_OT_VRC_ExportToUnity)
    bpy.utils.unregister_class(BF_VRCExportSettings)

    # Remove property from scene
    if hasattr(bpy.types.Scene, 'boneforge_vrc_export_settings'):
        del bpy.types.Scene.boneforge_vrc_export_settings
