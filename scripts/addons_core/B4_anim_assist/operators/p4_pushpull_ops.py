# --- OFFSET TOOLS ---
"""Push/Pull one-click operators.

Six thin subclasses — Push X/Y/Z, Pull X/Y/Z — that delegate to the
core offset pipeline with a hardcoded axis and sign.
"""

from __future__ import annotations

import bpy

from .p4_offset_ops import _OffsetBase


class AA_OT_p4_push_x(_OffsetBase, bpy.types.Operator):
    bl_idname = "animassist.p4_push_x"
    bl_label = "Push X"
    bl_description = (
        "Applies a positive translation delta on X using the current "
        "push/pull amount. Space, falloff, and mirror sign apply."
    )

    def execute(self, context):
        return self._run(context, push_axis="X", push_sign=1.0)


class AA_OT_p4_push_y(_OffsetBase, bpy.types.Operator):
    bl_idname = "animassist.p4_push_y"
    bl_label = "Push Y"
    bl_description = (
        "Applies a positive translation delta on Y using the current "
        "push/pull amount."
    )

    def execute(self, context):
        return self._run(context, push_axis="Y", push_sign=1.0)


class AA_OT_p4_push_z(_OffsetBase, bpy.types.Operator):
    bl_idname = "animassist.p4_push_z"
    bl_label = "Push Z"
    bl_description = (
        "Applies a positive translation delta on Z. Common for vertical "
        "overshoot on jumps and squashes."
    )

    def execute(self, context):
        return self._run(context, push_axis="Z", push_sign=1.0)


class AA_OT_p4_pull_x(_OffsetBase, bpy.types.Operator):
    bl_idname = "animassist.p4_pull_x"
    bl_label = "Pull X"
    bl_description = (
        "Applies a negative translation delta on X using the current "
        "push/pull amount. Inverse of Push X."
    )

    def execute(self, context):
        return self._run(context, push_axis="X", push_sign=-1.0)


class AA_OT_p4_pull_y(_OffsetBase, bpy.types.Operator):
    bl_idname = "animassist.p4_pull_y"
    bl_label = "Pull Y"
    bl_description = (
        "Applies a negative translation delta on Y. Inverse of Push Y."
    )

    def execute(self, context):
        return self._run(context, push_axis="Y", push_sign=-1.0)


class AA_OT_p4_pull_z(_OffsetBase, bpy.types.Operator):
    bl_idname = "animassist.p4_pull_z"
    bl_label = "Pull Z"
    bl_description = (
        "Applies a negative translation delta on Z. Inverse of Push Z."
    )

    def execute(self, context):
        return self._run(context, push_axis="Z", push_sign=-1.0)


CLASSES: tuple[type, ...] = (
    AA_OT_p4_push_x,
    AA_OT_p4_push_y,
    AA_OT_p4_push_z,
    AA_OT_p4_pull_x,
    AA_OT_p4_pull_y,
    AA_OT_p4_pull_z,
)
