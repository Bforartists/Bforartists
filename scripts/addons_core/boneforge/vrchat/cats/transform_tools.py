"""BoneCraft VRChat CATS — Transform Tools and FBT Utilities.

Apply All Transformations: applies loc/rot/scale to the armature and all mesh
children.  Meshes with shape keys use a shape-key-safe path that transforms
each key's vertex positions directly instead of calling transform_apply
(which would destroy shape keys in Blender 4.1+).

Fix FBT: adjusts hip and leg bone positions for Full Body Tracking alignment.

Remove FBT: deletes helper bones whose names match FBT helper patterns.

Category: VRChat Cats Tools.
"""

import logging
import re

import bpy
from bpy.types import Operator, Panel
from mathutils import Matrix, Vector

from boneforge.core import active_armature
from boneforge.i18n import T
from boneforge.vrchat.cats import pipeline

logger = logging.getLogger(__name__)

_FBT_HELPER_PATTERN = re.compile(r"^(Hip_WGT.*|FBT_.*)$", re.IGNORECASE)
_HIPS_NAMES = {"hips", "hip"}
_LEFT_LEG_NAMES = {"left leg", "leftleg", "leg_l", "leg.l", "左足"}
_RIGHT_LEG_NAMES = {"right leg", "rightleg", "leg_r", "leg.r", "右足"}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _mesh_has_shape_keys(obj):
    """Return True when *obj* has at least one non-Basis shape key."""
    if obj.data.shape_keys is None:
        return False
    return len(obj.data.shape_keys.key_blocks) > 0


def _apply_matrix_to_shape_keys(obj):
    """Apply obj.matrix_world (loc/rot/scale) to all shape key vertex positions.

    Shape key vertex coordinates are stored in local object space.  To "apply
    the transform" we multiply every coordinate by the 3×3 basis of the world
    matrix (handles rotation + scale) and then add the world-space translation
    only to the Basis key (all non-Basis keys store absolute local positions;
    adding the translation equally to all keys preserves their deltas).

    After updating the coordinates the object's loc/rot/scale are zeroed so
    Blender considers the transform applied.
    """
    mat = obj.matrix_world.copy()          # 4×4 world matrix
    mat3 = mat.to_3x3()                    # rotation + scale only

    key_blocks = obj.data.shape_keys.key_blocks
    n_verts = len(obj.data.vertices)
    n_floats = n_verts * 3

    # Build a flat list of (mat3 @ co) for every key block
    world_translation = mat.translation

    for kb in key_blocks:
        cos = [0.0] * n_floats
        kb.data.foreach_get("co", cos)

        new_cos = [0.0] * n_floats
        for i in range(n_verts):
            idx = i * 3
            v = Vector((cos[idx], cos[idx + 1], cos[idx + 2]))
            v_transformed = mat3 @ v
            # Add world translation to every key so that the object "moves"
            # to its world position in local space.
            new_cos[idx]     = v_transformed.x + world_translation.x
            new_cos[idx + 1] = v_transformed.y + world_translation.y
            new_cos[idx + 2] = v_transformed.z + world_translation.z

        kb.data.foreach_set("co", new_cos)

    obj.data.update()

    # Zero the object transform — transform is now baked into vertex data
    obj.location = Vector((0.0, 0.0, 0.0))
    obj.rotation_euler = (0.0, 0.0, 0.0)
    obj.scale = Vector((1.0, 1.0, 1.0))


# ── Apply All Transforms ──────────────────────────────────────────────────────

class BF_OT_CATS_ApplyAllTransforms(Operator):
    """Apply location, rotation, and scale to the active armature and all its
    mesh children.  Meshes with shape keys use a shape-key-safe code path that
    bakes the transform into vertex positions rather than calling
    bpy.ops.object.transform_apply (which destroys shape keys)"""

    bl_idname = "boneforge.cats_apply_all_transforms"
    bl_label = "Apply All Transforms"
    bl_description = ("Apply location, rotation and scale to the armature and its meshes. "
                      "Shape keys are kept")
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        arm = active_armature(context)
        if arm is None:
            self.report({'ERROR'}, "No active armature in context")
            return {'CANCELLED'}

        saved_active = context.view_layer.objects.active
        saved_selection = {obj.name for obj in context.selected_objects}

        processed = 0

        try:
            # ── Armature: standard transform_apply (no shape keys on armature data) ──
            bpy.ops.object.select_all(action='DESELECT')
            context.view_layer.objects.active = arm
            arm.select_set(True)
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            arm.select_set(False)
            processed += 1

            # ── Mesh children ──────────────────────────────────────────────────────
            mesh_children = [ch for ch in arm.children if ch.type == 'MESH']

            for mesh_obj in mesh_children:
                context.view_layer.objects.active = mesh_obj
                mesh_obj.select_set(True)

                if not _mesh_has_shape_keys(mesh_obj):
                    # Safe to use the standard operator — no shape keys to destroy
                    bpy.ops.object.transform_apply(
                        location=True, rotation=True, scale=True
                    )
                else:
                    # Shape-key-safe path: bake matrix into vertex data directly
                    _apply_matrix_to_shape_keys(mesh_obj)

                mesh_obj.select_set(False)
                processed += 1

        except Exception as exc:
            logger.exception("[BoneCraft ApplyTransforms] Error: %s", exc)
            self.report({'ERROR'}, f"Transform apply failed: {exc}")
            return {'CANCELLED'}

        finally:
            # Restore selection state
            bpy.ops.object.select_all(action='DESELECT')
            for name in saved_selection:
                obj = bpy.data.objects.get(name)
                if obj is not None:
                    obj.select_set(True)
            if saved_active is not None and saved_active.name in bpy.data.objects:
                context.view_layer.objects.active = bpy.data.objects[saved_active.name]

        scene = context.scene
        msg = f"Applied transforms to {processed} objects"
        pipeline.append_ledger(scene, "apply_transforms", pipeline.OUTCOME_CHANGED, msg)
        pipeline.set_phase_complete(scene, "apply_transforms", pipeline.OUTCOME_CHANGED)

        self.report({'INFO'}, msg)
        return {'FINISHED'}


# ── Fix FBT ───────────────────────────────────────────────────────────────────

class BF_OT_CATS_FixFBT(Operator):
    """Adjust hip and leg bones for Full Body Tracking compatibility.
    Moves the hip bone head to a safe height if it sits too low, and ensures
    leg bones extend downward"""

    bl_idname = "boneforge.cats_fix_fbt"
    bl_label = "Fix FBT"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        arm = active_armature(context)
        if arm is None:
            self.report({'ERROR'}, "No active armature in context")
            return {'CANCELLED'}

        adjustments = []

        try:
            context.view_layer.objects.active = arm
            bpy.ops.object.mode_set(mode='EDIT')
            edit_bones = arm.data.edit_bones

            # ── Hips bone ──────────────────────────────────────────────────────
            hips_bone = None
            for eb in edit_bones:
                if eb.name.lower() in _HIPS_NAMES:
                    hips_bone = eb
                    break

            if hips_bone is not None:
                hip_z = hips_bone.head.z
                if hip_z < 0.8:
                    old_z = hip_z
                    direction = hips_bone.tail - hips_bone.head
                    hips_bone.head.z = 1.0
                    hips_bone.tail = hips_bone.head + direction
                    adjustments.append(
                        f"Hips raised from z={old_z:.3f} to z=1.000"
                    )
                    logger.info("[BoneCraft FixFBT] %s", adjustments[-1])

            # ── Leg bones: ensure tail is below head ───────────────────────────
            for eb in edit_bones:
                eb_lower = eb.name.lower()
                is_leg = (
                    any(pat in eb_lower for pat in _LEFT_LEG_NAMES)
                    or any(pat in eb_lower for pat in _RIGHT_LEG_NAMES)
                )
                if not is_leg:
                    continue
                if eb.tail.z >= eb.head.z:
                    old_tail_z = eb.tail.z
                    eb.tail.z = eb.head.z - abs(
                        (eb.tail - eb.head).length
                    )
                    adjustments.append(
                        f"'{eb.name}' tail corrected to extend downward"
                    )
                    logger.info("[BoneCraft FixFBT] %s", adjustments[-1])

        except Exception as exc:
            logger.exception("[BoneCraft FixFBT] Error: %s", exc)
            self.report({'ERROR'}, f"Fix FBT failed: {exc}")
            return {'CANCELLED'}

        finally:
            try:
                bpy.ops.object.mode_set(mode='OBJECT')
            except RuntimeError:
                pass

        scene = context.scene
        if adjustments:
            msg = "FBT bones adjusted: " + "; ".join(adjustments)
            outcome = pipeline.OUTCOME_CHANGED
            self.report({'INFO'}, "FBT bones adjusted")
        else:
            msg = "FBT: no adjustments needed"
            outcome = pipeline.OUTCOME_CLEAN
            self.report({'INFO'}, "FBT: no adjustments needed")

        pipeline.append_ledger(scene, "fix_fbt", outcome, msg)
        pipeline.set_phase_complete(scene, "fix_fbt", outcome)

        return {'FINISHED'}


# ── Remove FBT ────────────────────────────────────────────────────────────────

class BF_OT_CATS_RemoveFBT(Operator):
    """Remove FBT helper bones whose names match the Hip_WGT* or FBT_* patterns"""

    bl_idname = "boneforge.cats_remove_fbt"
    bl_label = "Remove FBT Bones"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        arm = active_armature(context)
        if arm is None:
            self.report({'ERROR'}, "No active armature in context")
            return {'CANCELLED'}

        removed = []

        try:
            context.view_layer.objects.active = arm
            bpy.ops.object.mode_set(mode='EDIT')
            edit_bones = arm.data.edit_bones

            bones_to_remove = [
                eb for eb in edit_bones
                if _FBT_HELPER_PATTERN.match(eb.name)
            ]

            for eb in bones_to_remove:
                name = eb.name
                edit_bones.remove(eb)
                removed.append(name)
                logger.info("[BoneCraft RemoveFBT] Removed bone '%s'", name)

        except Exception as exc:
            logger.exception("[BoneCraft RemoveFBT] Error: %s", exc)
            self.report({'ERROR'}, f"Remove FBT failed: {exc}")
            return {'CANCELLED'}

        finally:
            try:
                bpy.ops.object.mode_set(mode='OBJECT')
            except RuntimeError:
                pass

        scene = context.scene
        if removed:
            msg = f"Removed {len(removed)} FBT bone(s): {', '.join(removed)}"
            outcome = pipeline.OUTCOME_CHANGED
            self.report({'INFO'}, msg)
        else:
            msg = "No FBT bones found"
            outcome = pipeline.OUTCOME_CLEAN
            self.report({'INFO'}, "No FBT bones found")

        pipeline.append_ledger(scene, "remove_fbt", outcome, msg)
        pipeline.set_phase_complete(scene, "remove_fbt", outcome)

        return {'FINISHED'}


# ── Panel ─────────────────────────────────────────────────────────────────────

class CATS_PT_transform_tools(Panel):
    """CATS Transform Tools and FBT Utilities panel."""

    bl_label = " "
    bl_idname = "CATS_PT_transform_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "CATS"

    def draw_header(self, context):
        self.layout.label(text=T("Transforms & FBT"))

    @classmethod
    def poll(cls, context):
        return False  # Displayed via CATS_PT_transforms in cats_panel.py

    def draw(self, context):
        layout = self.layout

        # ── Apply Transforms ───────────────────────────────────────────────
        box = layout.box()
        box.label(text=T("Apply All Transforms"))
        box.label(
            text=T("Shape-key-safe — bakes matrix into vertex data"),
            icon='INFO',
        )
        box.operator(
            "boneforge.cats_apply_all_transforms",
            text=T("Apply All Transforms"),
            icon='APPLYALL',
        )

        layout.separator()

        # ── FBT ───────────────────────────────────────────────────────────
        box2 = layout.box()
        box2.label(text=T("Full Body Tracking"))

        row = box2.row(align=True)
        row.operator(
            "boneforge.cats_fix_fbt",
            text=T("Fix FBT"),
            icon='MODIFIER',
        )
        row.operator(
            "boneforge.cats_remove_fbt",
            text=T("Remove FBT"),
            icon='TRASH',
        )


# ── Registration ──────────────────────────────────────────────────────────────

_classes = (
    BF_OT_CATS_ApplyAllTransforms,
    BF_OT_CATS_FixFBT,
    BF_OT_CATS_RemoveFBT,
)


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
