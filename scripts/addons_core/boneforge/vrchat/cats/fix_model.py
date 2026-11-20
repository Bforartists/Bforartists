"""BoneCraft VRChat — Fix Model One-Click.

Apply common model fixes: merge by distance, recalculate normals,
remove loose geometry, remove empty vertex groups, optionally remove
zero-weight bones, and apply non-armature modifiers. Shows checklist
of operations before running.

Category: VRChat Cats Tools.
"""

import logging

import bpy
from bpy.props import BoolProperty
from bpy.types import Operator, Panel, PropertyGroup

from boneforge.core import active_armature
from boneforge.i18n import T
from boneforge.vrchat.cats.cleanup import _remove_zero_weight_bones

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────
# Settings
# ─────────────────────────────────────────────────────────────────

class BF_VRCFixModelSettings(PropertyGroup):
    """Settings for the Fix Model operation."""

    apply_modifiers: BoolProperty(
        name="Apply Modifiers",
        description="Apply all non-armature modifiers to mesh children",
        default=True,
    )
    remove_doubles: BoolProperty(
        name="Remove Doubles",
        description="Merge vertices by distance (0.0001 threshold)",
        default=True,
    )
    recalculate_normals: BoolProperty(
        name="Recalculate Normals",
        description="Recalculate mesh normals facing outward",
        default=True,
    )
    remove_loose: BoolProperty(
        name="Remove Loose",
        description="Delete loose geometry not connected to main mesh",
        default=True,
    )
    remove_empty_groups: BoolProperty(
        name="Remove Empty Groups",
        description="Delete vertex groups with zero weight influence",
        default=True,
    )
    remove_zero_weight_bones: BoolProperty(
        name="Remove Zero-Weight Bones",
        description="Delete deform bones with no meaningful mesh influence",
        default=False,
    )
    remove_constraints: BoolProperty(
        name="Remove Constraints",
        description="Remove all non-armature constraints from pose bones",
        default=True,
    )
    remove_rigidbodies: BoolProperty(
        name="Remove Rigidbodies",
        description="Remove all Rigid Body physics from mesh children",
        default=True,
    )


# ─────────────────────────────────────────────────────────────────
# Operator
# ─────────────────────────────────────────────────────────────────

class BF_OT_VRC_FixModel(Operator):
    """Fix common model issues in a single undoable step"""

    bl_idname = "boneforge.vrc_fix_model"
    bl_label = "Fix Model"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        """Execute the fix model workflow."""
        arm = active_armature(context)
        if arm is None:
            self.report({'ERROR'}, "No active armature")
            return {'CANCELLED'}

        settings = context.scene.boneforge_vrc_fix_model_settings

        # Collect all mesh children
        mesh_children = [child for child in arm.children if child.type == 'MESH']
        if not mesh_children:
            self.report({'WARNING'}, "Armature has no mesh children")
            return {'CANCELLED'}

        # Save selection state
        saved_selection = set(obj.name for obj in context.selected_objects)
        saved_active = context.view_layer.objects.active

        operations_done = []

        try:

            # ─ Apply modifiers ─
            if settings.apply_modifiers:
                for mesh_obj in mesh_children:
                    # B-10: modifier_apply operates on the active object
                    context.view_layer.objects.active = mesh_obj
                    mesh_obj.select_set(True)
                    for mod in list(mesh_obj.modifiers):
                        if mod.type == 'ARMATURE':
                            continue
                        try:
                            bpy.ops.object.modifier_apply(modifier=mod.name)
                        except RuntimeError as e:
                            logger.warning(f"[BoneCraft] Could not apply modifier '{mod.name}' on '{mesh_obj.name}': {e}")
                    mesh_obj.select_set(False)
                operations_done.append("Applied modifiers")

            # ─ Remove doubles ─
            if settings.remove_doubles:
                for mesh_obj in mesh_children:
                    context.view_layer.objects.active = mesh_obj
                    mesh_obj.select_set(True)
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.mesh.select_all(action='SELECT')
                    bpy.ops.mesh.remove_doubles(threshold=0.0001)
                    bpy.ops.object.mode_set(mode='OBJECT')
                    mesh_obj.select_set(False)
                operations_done.append("Removed doubles")

            # ─ Recalculate normals ─
            if settings.recalculate_normals:
                for mesh_obj in mesh_children:
                    context.view_layer.objects.active = mesh_obj
                    mesh_obj.select_set(True)
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.mesh.select_all(action='SELECT')
                    bpy.ops.mesh.normals_make_consistent(inside=False)
                    bpy.ops.object.mode_set(mode='OBJECT')
                    mesh_obj.select_set(False)
                operations_done.append("Recalculated normals")

            # ─ Remove loose ─
            if settings.remove_loose:
                for mesh_obj in mesh_children:
                    context.view_layer.objects.active = mesh_obj
                    mesh_obj.select_set(True)
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.mesh.select_all(action='DESELECT')
                    bpy.ops.mesh.select_loose()
                    bpy.ops.mesh.delete(type='VERT')
                    bpy.ops.object.mode_set(mode='OBJECT')
                    mesh_obj.select_set(False)
                operations_done.append("Removed loose geometry")

            # ─ Remove empty vertex groups ─
            if settings.remove_empty_groups:
                for mesh_obj in mesh_children:
                    # Identify unused groups
                    used_groups = set()
                    for vert in mesh_obj.data.vertices:
                        for group in vert.groups:
                            used_groups.add(group.group)

                    # Remove unused groups in reverse order
                    for idx in sorted(set(range(len(mesh_obj.vertex_groups))) - used_groups, reverse=True):
                        mesh_obj.vertex_groups.remove(mesh_obj.vertex_groups[idx])

                operations_done.append("Removed empty vertex groups")

            if settings.remove_zero_weight_bones:
                removed_count = _remove_zero_weight_bones(context, arm)
                if removed_count:
                    operations_done.append(f"Removed {removed_count} zero-weight bones")

            # ─ Remove pose constraints ─
            if settings.remove_constraints:
                if arm.pose:
                    for pbone in arm.pose.bones:
                        for con in list(pbone.constraints):
                            if con.type not in ('ARMATURE',):
                                pbone.constraints.remove(con)
                operations_done.append("Removed pose constraints")

            # ─ Remove rigidbodies ─
            if settings.remove_rigidbodies:
                for mesh_obj in mesh_children:
                    if mesh_obj.rigid_body is not None:
                        context.view_layer.objects.active = mesh_obj
                        mesh_obj.select_set(True)
                        try:
                            bpy.ops.rigidbody.object_remove()
                        except RuntimeError:
                            pass
                        mesh_obj.select_set(False)
                operations_done.append("Removed rigidbodies")

            # Report
            if operations_done:
                ops_text = ", ".join(operations_done)
                self.report({'INFO'}, f"Fixed model: {ops_text}")

        finally:
            # Restore selection state
            bpy.ops.object.select_all(action='DESELECT')
            for obj_name in saved_selection:
                try:
                    bpy.data.objects[obj_name].select_set(True)
                except KeyError as exc:
                    logger.debug("./vrchat/cats/fix_model.py suppressed KeyError: %s", exc)
            if saved_active and saved_active.name in bpy.data.objects:
                context.view_layer.objects.active = bpy.data.objects[saved_active.name]

        from boneforge.vrchat.cats import pipeline as _pipeline
        outcome = _pipeline.OUTCOME_CHANGED if operations_done else _pipeline.OUTCOME_CLEAN
        _pipeline.append_ledger(
            context.scene,
            "fix_model",
            outcome,
            ", ".join(operations_done) if operations_done else "nothing to do",
        )
        _pipeline.set_phase_complete(context.scene, "fix_model", outcome)

        return {'FINISHED'}


# ─────────────────────────────────────────────────────────────────
# Panel
# ─────────────────────────────────────────────────────────────────

class BONEFORGE_PT_vrc_fix_model(Panel):
    """VRChat Fix Model panel"""

    bl_label = " "
    bl_idname = "BONEFORGE_PT_vrc_fix_model"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'scene'

    def draw_header(self, context):
        self.layout.label(text=T("Fix Model"))

    def draw(self, context):
        """Draw the panel UI."""
        layout = self.layout
        settings = context.scene.boneforge_vrc_fix_model_settings

        # Options
        layout.label(text=T("Operations to perform:"))
        layout.prop(settings, "apply_modifiers", toggle=True)
        layout.prop(settings, "remove_doubles", toggle=True)
        layout.prop(settings, "recalculate_normals", toggle=True)
        layout.prop(settings, "remove_loose", toggle=True)
        layout.prop(settings, "remove_empty_groups", toggle=True)
        layout.prop(settings, "remove_zero_weight_bones", toggle=True)
        layout.prop(settings, "remove_constraints", toggle=True)
        layout.prop(settings, "remove_rigidbodies", toggle=True)

        # Execute button
        layout.separator()
        layout.operator("boneforge.vrc_fix_model", text=T("Fix Model"), icon='MODIFIER')


# ─────────────────────────────────────────────────────────────────
# Registration
# ─────────────────────────────────────────────────────────────────

def register():
    """Register fix model classes."""
    bpy.utils.register_class(BF_VRCFixModelSettings)
    bpy.utils.register_class(BF_OT_VRC_FixModel)

    # Add property to scene
    bpy.types.Scene.boneforge_vrc_fix_model_settings = bpy.props.PointerProperty(
        type=BF_VRCFixModelSettings
    )


def unregister():
    """Unregister fix model classes."""
    bpy.utils.unregister_class(BF_OT_VRC_FixModel)
    bpy.utils.unregister_class(BF_VRCFixModelSettings)

    # Remove property from scene
    if hasattr(bpy.types.Scene, 'boneforge_vrc_fix_model_settings'):
        del bpy.types.Scene.boneforge_vrc_fix_model_settings
