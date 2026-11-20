"""
Macro operators for the p10 animation assistant.

Provides operators for running preset macros, managing custom macros,
and executing individual macro steps.
"""

import bpy
from bpy.props import IntProperty, StringProperty

from ..core.logging import get_logger
from ..core.p10_properties import get_p10
from ..core.p10_macro_engine import (
    execute_macro,
    validate_macro,
    build_macro_from_property,
    macro_breakdown_offset,
    macro_proxy_workflow,
    macro_switch_compensate,
    macro_diagnose_jump,
    macro_mirror_match,
)
from ..core.p10_audit import log_operation

_log = get_logger(__name__)


class AA_OT_p10_macro_breakdown_offset(bpy.types.Operator):
    """Run the breakdown + offset preset macro"""
    bl_idname = "animassist.p10_macro_breakdown_offset"
    bl_label = "Breakdown + Offset"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from ..core import p10_recovery as recovery

        p10 = get_p10(context)
        if p10 and p10.recovery_enabled:
            recovery.take_snapshot(context, self.bl_label)

        steps = macro_breakdown_offset()
        result = execute_macro(steps, context)
        log_operation(
            self.bl_idname,
            result.success,
            f"{result.steps_run}/{result.steps_run + result.steps_skipped} steps",
            result.elapsed_ms
        )

        if result.success:
            self.report({'INFO'}, f"{self.bl_label}: {result.steps_run} steps completed")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, f"{self.bl_label}: {len(result.errors)} error(s)")
            return {'FINISHED'}


class AA_OT_p10_macro_proxy_workflow(bpy.types.Operator):
    """Run the proxy workflow preset macro"""
    bl_idname = "animassist.p10_macro_proxy_workflow"
    bl_label = "Proxy Workflow"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from ..core import p10_recovery as recovery

        p10 = get_p10(context)
        if p10 and p10.recovery_enabled:
            recovery.take_snapshot(context, self.bl_label)

        steps = macro_proxy_workflow()
        result = execute_macro(steps, context)
        log_operation(
            self.bl_idname,
            result.success,
            f"{result.steps_run}/{result.steps_run + result.steps_skipped} steps",
            result.elapsed_ms
        )

        if result.success:
            self.report({'INFO'}, f"{self.bl_label}: {result.steps_run} steps completed")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, f"{self.bl_label}: {len(result.errors)} error(s)")
            return {'FINISHED'}


class AA_OT_p10_macro_switch_compensate(bpy.types.Operator):
    """Run the switch + compensate preset macro"""
    bl_idname = "animassist.p10_macro_switch_compensate"
    bl_label = "Switch + Compensate"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from ..core import p10_recovery as recovery

        p10 = get_p10(context)
        if p10 and p10.recovery_enabled:
            recovery.take_snapshot(context, self.bl_label)

        steps = macro_switch_compensate()
        result = execute_macro(steps, context)
        log_operation(
            self.bl_idname,
            result.success,
            f"{result.steps_run}/{result.steps_run + result.steps_skipped} steps",
            result.elapsed_ms
        )

        if result.success:
            self.report({'INFO'}, f"{self.bl_label}: {result.steps_run} steps completed")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, f"{self.bl_label}: {len(result.errors)} error(s)")
            return {'FINISHED'}


class AA_OT_p10_macro_diagnose_jump(bpy.types.Operator):
    """Run the diagnose + jump preset macro"""
    bl_idname = "animassist.p10_macro_diagnose_jump"
    bl_label = "Diagnose + Jump"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from ..core import p10_recovery as recovery

        p10 = get_p10(context)
        if p10 and p10.recovery_enabled:
            recovery.take_snapshot(context, self.bl_label)

        steps = macro_diagnose_jump()
        result = execute_macro(steps, context)
        log_operation(
            self.bl_idname,
            result.success,
            f"{result.steps_run}/{result.steps_run + result.steps_skipped} steps",
            result.elapsed_ms
        )

        if result.success:
            self.report({'INFO'}, f"{self.bl_label}: {result.steps_run} steps completed")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, f"{self.bl_label}: {len(result.errors)} error(s)")
            return {'FINISHED'}


class AA_OT_p10_macro_mirror_match(bpy.types.Operator):
    """Run the mirror + match preset macro"""
    bl_idname = "animassist.p10_macro_mirror_match"
    bl_label = "Mirror + Match"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from ..core import p10_recovery as recovery

        p10 = get_p10(context)
        if p10 and p10.recovery_enabled:
            recovery.take_snapshot(context, self.bl_label)

        steps = macro_mirror_match()
        result = execute_macro(steps, context)
        log_operation(
            self.bl_idname,
            result.success,
            f"{result.steps_run}/{result.steps_run + result.steps_skipped} steps",
            result.elapsed_ms
        )

        if result.success:
            self.report({'INFO'}, f"{self.bl_label}: {result.steps_run} steps completed")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, f"{self.bl_label}: {len(result.errors)} error(s)")
            return {'FINISHED'}


class AA_OT_p10_run_custom_macro(bpy.types.Operator):
    """Run a user-defined macro from the macros collection"""
    bl_idname = "animassist.p10_run_custom_macro"
    bl_label = "Run Custom Macro"
    bl_options = {'REGISTER', 'UNDO'}

    index: IntProperty(
        name="Macro Index",
        description="Index of the macro in the p10.macros collection",
        min=0
    )

    def execute(self, context):
        from ..core import p10_recovery as recovery

        p10 = get_p10(context)
        if not p10:
            self.report({'ERROR'}, "Workspace settings are not initialised. Run First Run Setup from Properties > Scene > Anim Assist > Setup")
            return {'CANCELLED'}

        if self.index >= len(p10.macros):
            self.report({'ERROR'}, f"Select a macro in the list first")
            return {'CANCELLED'}

        macro_prop = p10.macros[self.index]
        macro_name = macro_prop.name

        if p10.recovery_enabled:
            recovery.take_snapshot(context, f"Custom Macro: {macro_name}")

        steps = build_macro_from_property(macro_prop)
        result = execute_macro(steps, context)
        log_operation(
            self.bl_idname,
            result.success,
            f"{result.steps_run}/{result.steps_run + result.steps_skipped} steps",
            result.elapsed_ms
        )

        if result.success:
            self.report({'INFO'}, f"{macro_name}: {result.steps_run} steps completed")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, f"{macro_name}: {len(result.errors)} error(s)")
            return {'FINISHED'}


class AA_OT_p10_add_macro(bpy.types.Operator):
    """Add a new empty macro entry"""
    bl_idname = "animassist.p10_add_macro"
    bl_label = "Add Macro"
    bl_options = {'REGISTER', 'UNDO'}

    name: StringProperty(
        name="Name",
        description="Name of the new macro",
        default="New Macro"
    )

    def execute(self, context):
        p10 = get_p10(context)
        if not p10:
            self.report({'ERROR'}, "Workspace settings are not initialised. Run First Run Setup from Properties > Scene > Anim Assist > Setup")
            return {'CANCELLED'}

        macro = p10.macros.add()
        macro.name = self.name

        log_operation(
            self.bl_idname,
            True,
            f"Added macro '{self.name}'",
            0
        )

        self.report({'INFO'}, f"Added macro '{self.name}'")
        return {'FINISHED'}


class AA_OT_p10_remove_macro(bpy.types.Operator):
    """Remove a macro by index"""
    bl_idname = "animassist.p10_remove_macro"
    bl_label = "Remove Macro"
    bl_options = {'REGISTER', 'UNDO'}

    index: IntProperty(
        name="Macro Index",
        description="Index of the macro to remove",
        min=0
    )

    def execute(self, context):
        p10 = get_p10(context)
        if not p10:
            self.report({'ERROR'}, "Workspace settings are not initialised. Run First Run Setup from Properties > Scene > Anim Assist > Setup")
            return {'CANCELLED'}

        if self.index >= len(p10.macros):
            self.report({'ERROR'}, f"Select a macro in the list first")
            return {'CANCELLED'}

        macro_name = p10.macros[self.index].name
        p10.macros.remove(self.index)

        log_operation(
            self.bl_idname,
            True,
            f"Removed macro '{macro_name}'",
            0
        )

        self.report({'INFO'}, f"Removed macro '{macro_name}'")
        return {'FINISHED'}


class AA_OT_p10_add_macro_step(bpy.types.Operator):
    """Add a step to a macro"""
    bl_idname = "animassist.p10_add_macro_step"
    bl_label = "Add Macro Step"
    bl_options = {'REGISTER', 'UNDO'}

    macro_index: IntProperty(
        name="Macro Index",
        description="Index of the macro",
        min=0
    )

    op_id: StringProperty(
        name="Operator ID",
        description="Blender operator ID (e.g., 'wm.open_mainfile')",
        default=""
    )

    label: StringProperty(
        name="Step Label",
        description="User-friendly label for the step",
        default="Step"
    )

    def execute(self, context):
        p10 = get_p10(context)
        if not p10:
            self.report({'ERROR'}, "Workspace settings are not initialised. Run First Run Setup from Properties > Scene > Anim Assist > Setup")
            return {'CANCELLED'}

        if self.macro_index >= len(p10.macros):
            self.report({'ERROR'}, f"Select a macro in the list first")
            return {'CANCELLED'}

        macro = p10.macros[self.macro_index]
        step = macro.steps.add()
        step.op_id = self.op_id
        step.label = self.label

        log_operation(
            self.bl_idname,
            True,
            f"Added step '{self.label}' to macro '{macro.name}'",
            0
        )

        self.report({'INFO'}, f"Added step '{self.label}'")
        return {'FINISHED'}


class AA_OT_p10_remove_macro_step(bpy.types.Operator):
    """Remove a step from a macro"""
    bl_idname = "animassist.p10_remove_macro_step"
    bl_label = "Remove Macro Step"
    bl_options = {'REGISTER', 'UNDO'}

    macro_index: IntProperty(
        name="Macro Index",
        description="Index of the macro",
        min=0
    )

    step_index: IntProperty(
        name="Step Index",
        description="Index of the step to remove",
        min=0
    )

    def execute(self, context):
        p10 = get_p10(context)
        if not p10:
            self.report({'ERROR'}, "Workspace settings are not initialised. Run First Run Setup from Properties > Scene > Anim Assist > Setup")
            return {'CANCELLED'}

        if self.macro_index >= len(p10.macros):
            self.report({'ERROR'}, f"Select a macro in the list first")
            return {'CANCELLED'}

        macro = p10.macros[self.macro_index]
        if self.step_index >= len(macro.steps):
            self.report({'ERROR'}, f"Select a macro step in the list first")
            return {'CANCELLED'}

        step_label = macro.steps[self.step_index].label
        macro.steps.remove(self.step_index)

        log_operation(
            self.bl_idname,
            True,
            f"Removed step '{step_label}' from macro '{macro.name}'",
            0
        )

        self.report({'INFO'}, f"Removed step '{step_label}'")
        return {'FINISHED'}


class AA_OT_p10_validate_macro(bpy.types.Operator):
    """Validate all steps in a macro"""
    bl_idname = "animassist.p10_validate_macro"
    bl_label = "Validate Macro"
    bl_options = {'REGISTER'}

    index: IntProperty(
        name="Macro Index",
        description="Index of the macro to validate",
        min=0
    )

    def execute(self, context):
        p10 = get_p10(context)
        if not p10:
            self.report({'ERROR'}, "Workspace settings are not initialised. Run First Run Setup from Properties > Scene > Anim Assist > Setup")
            return {'CANCELLED'}

        if self.index >= len(p10.macros):
            self.report({'ERROR'}, f"Select a macro in the list first")
            return {'CANCELLED'}

        macro_prop = p10.macros[self.index]
        steps = build_macro_from_property(macro_prop)

        errors = validate_macro(steps)

        log_operation(
            self.bl_idname,
            success=len(errors) == 0,
            detail=f"Macro '{macro_prop.name}' validation: {len(steps)} steps, {len(errors)} error(s)",
            elapsed_ms=0,
        )

        if not errors:
            self.report({'INFO'}, f"Macro '{macro_prop.name}' is valid")
            return {'FINISHED'}
        else:
            error_msg = "; ".join(errors)
            self.report({'WARNING'}, f"Macro validation failed: {error_msg}")
            return {'FINISHED'}


CLASSES = (
    AA_OT_p10_macro_breakdown_offset,
    AA_OT_p10_macro_proxy_workflow,
    AA_OT_p10_macro_switch_compensate,
    AA_OT_p10_macro_diagnose_jump,
    AA_OT_p10_macro_mirror_match,
    AA_OT_p10_run_custom_macro,
    AA_OT_p10_add_macro,
    AA_OT_p10_remove_macro,
    AA_OT_p10_add_macro_step,
    AA_OT_p10_remove_macro_step,
    AA_OT_p10_validate_macro,
)
