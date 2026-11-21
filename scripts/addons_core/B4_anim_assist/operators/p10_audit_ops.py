# --- BATCH OPERATIONS AND AUTOMATION ---
"""Audit trail and history operators."""

from __future__ import annotations

import bpy
from bpy.props import IntProperty

from ..core.logging import get_logger
from ..core.helpers import confirm_dialog

_log = get_logger(__name__)


class AA_OT_p10_show_history(bpy.types.Operator):
    """Display recent operation history in the info area."""
    bl_idname = "animassist.p10_show_history"
    bl_label = "Show Operation History"
    bl_options = {'REGISTER'}

    limit: IntProperty(name="Limit", default=20, min=1, max=100)  # type: ignore[valid-type]

    def execute(self, context):
        from ..core import p10_audit as audit
        history = audit.get_history(self.limit)
        if not history:
            self.report({'INFO'}, "No operations recorded")
        else:
            for h in history:
                status = "OK" if h["success"] else "FAIL"
                self.report({'INFO'}, f"  {h['op_id']} [{status}] {h['detail']}")
            self.report({'INFO'}, f"Showing {len(history)} recent operation(s)")
        return {'FINISHED'}


class AA_OT_p10_show_errors(bpy.types.Operator):
    """Display recent errors in the info area."""
    bl_idname = "animassist.p10_show_errors"
    bl_label = "Show Error Log"
    bl_options = {'REGISTER'}

    limit: IntProperty(name="Limit", default=20, min=1, max=100)  # type: ignore[valid-type]

    def execute(self, context):
        from ..core import p10_audit as audit
        errors = audit.get_errors(self.limit)
        if not errors:
            self.report({'INFO'}, "No errors recorded")
        else:
            for e in errors:
                self.report({'WARNING'}, f"  [{e['source']}] {e['message']}")
            self.report({'INFO'}, f"Showing {len(errors)} recent error(s)")
        return {'FINISHED'}


class AA_OT_p10_show_stats(bpy.types.Operator):
    """Display session audit statistics."""
    bl_idname = "animassist.p10_show_stats"
    bl_label = "Session Statistics"
    bl_options = {'REGISTER'}

    def execute(self, context):
        from ..core import p10_audit as audit
        stats = audit.get_stats()
        self.report({'INFO'}, f"Operations: {stats['total_operations']}")
        self.report({'INFO'}, f"Failures: {stats['total_failures']}")
        self.report({'INFO'}, f"Success rate: {stats['success_rate']:.1f}%")
        self.report({'INFO'}, f"Uptime: {stats['session_uptime_s']:.0f}s")
        return {'FINISHED'}


class AA_OT_p10_clear_history(bpy.types.Operator):
    """Clear the operation history buffer."""
    bl_idname = "animassist.p10_clear_history"
    bl_label = "Clear History"
    bl_options = {'REGISTER'}

    def invoke(self, context, event):  # type: ignore[no-untyped-def]
        return confirm_dialog(self, context, event, 'Clear the whole operation history? This cannot be undone.')

    def execute(self, context):
        from ..core import p10_audit as audit
        audit.clear_history()
        self.report({'INFO'}, "Operation history cleared")
        return {'FINISHED'}


class AA_OT_p10_clear_errors(bpy.types.Operator):
    """Clear the error log."""
    bl_idname = "animassist.p10_clear_errors"
    bl_label = "Clear Errors"
    bl_options = {'REGISTER'}

    def invoke(self, context, event):  # type: ignore[no-untyped-def]
        return confirm_dialog(self, context, event, 'Clear the error log? This cannot be undone.')

    def execute(self, context):
        from ..core import p10_audit as audit
        audit.clear_errors()
        self.report({'INFO'}, "Error log cleared")
        return {'FINISHED'}


CLASSES: tuple[type, ...] = (
    AA_OT_p10_show_history,
    AA_OT_p10_show_errors,
    AA_OT_p10_show_stats,
    AA_OT_p10_clear_history,
    AA_OT_p10_clear_errors,
)
