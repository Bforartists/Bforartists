"""
Pie menu operators for Animation Assistant.
These operators invoke pie menu UI classes defined in ui/p10_pie_menus.py.
"""

import bpy
from ..core.logging import get_logger

_log = get_logger(__name__)


class AA_OT_p10_pie_key_tools(bpy.types.Operator):
    """Invoke the Key Tools pie menu"""
    bl_idname = "animassist.p10_pie_key_tools"
    bl_label = "Key Tools Pie"
    bl_options = {'REGISTER'}

    def execute(self, context):
        bpy.ops.wm.call_menu_pie(name="ANIMASSIST_MT_p10_pie_key_tools")
        return {'FINISHED'}


class AA_OT_p10_pie_breakdown(bpy.types.Operator):
    """Invoke the Breakdown pie menu"""
    bl_idname = "animassist.p10_pie_breakdown"
    bl_label = "Breakdown Pie"
    bl_options = {'REGISTER'}

    def execute(self, context):
        bpy.ops.wm.call_menu_pie(name="ANIMASSIST_MT_p10_pie_breakdown")
        return {'FINISHED'}


class AA_OT_p10_pie_transform(bpy.types.Operator):
    """Invoke the Transform pie menu"""
    bl_idname = "animassist.p10_pie_transform"
    bl_label = "Transform Pie"
    bl_options = {'REGISTER'}

    def execute(self, context):
        bpy.ops.wm.call_menu_pie(name="ANIMASSIST_MT_p10_pie_transform")
        return {'FINISHED'}


class AA_OT_p10_pie_proxy(bpy.types.Operator):
    """Invoke the Proxy Controls pie menu"""
    bl_idname = "animassist.p10_pie_proxy"
    bl_label = "Proxy Controls Pie"
    bl_options = {'REGISTER'}

    def execute(self, context):
        bpy.ops.wm.call_menu_pie(name="ANIMASSIST_MT_p10_pie_proxy")
        return {'FINISHED'}


class AA_OT_p10_pie_switch(bpy.types.Operator):
    """Invoke the Space Switch pie menu"""
    bl_idname = "animassist.p10_pie_switch"
    bl_label = "Space Switch Pie"
    bl_options = {'REGISTER'}

    def execute(self, context):
        bpy.ops.wm.call_menu_pie(name="ANIMASSIST_MT_p10_pie_switch")
        return {'FINISHED'}


class AA_OT_p10_pie_symmetry(bpy.types.Operator):
    """Invoke the Symmetry pie menu"""
    bl_idname = "animassist.p10_pie_symmetry"
    bl_label = "Symmetry Pie"
    bl_options = {'REGISTER'}

    def execute(self, context):
        bpy.ops.wm.call_menu_pie(name="ANIMASSIST_MT_p10_pie_symmetry")
        return {'FINISHED'}


CLASSES = (
    AA_OT_p10_pie_key_tools,
    AA_OT_p10_pie_breakdown,
    AA_OT_p10_pie_transform,
    AA_OT_p10_pie_proxy,
    AA_OT_p10_pie_switch,
    AA_OT_p10_pie_symmetry,
)
