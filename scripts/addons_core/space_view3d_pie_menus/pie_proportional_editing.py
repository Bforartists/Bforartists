# SPDX-FileCopyrightText: 2016-2024 Blender Foundation
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.types import Menu, Operator
from bpy.props import StringProperty
from .op_pie_wrappers import WM_OT_call_menu_pie_drag_only


class PIE_MT_proportional_edit(Menu):
    bl_idname = "PIE_MT_proportional_edit"
    bl_label = "Proportional Edit"

    def draw(self, context):
        ts = context.tool_settings
        layout = self.layout
        pie = layout.menu_pie()

        # 4 - LEFT
        pie.operator(
            "object.set_proportional_falloff", text="Smooth", icon='SMOOTHCURVE'
        ).falloff_shape = 'SMOOTH'

        # 6 - RIGHT
        if context.mode == 'OBJECT':
            pie.menu(
                "PIE_MT_proportional_edit_obj_more", text="More...", icon='THREE_DOTS'
            )
        else:
            pie.menu(
                "PIE_MT_proportional_edit_mesh_more", text="More...", icon='THREE_DOTS'
            )

        # 2 - BOTTOM
        pie.operator(
            "object.set_proportional_falloff", text="Sharp", icon='SHARPCURVE'
        ).falloff_shape = 'SHARP'

        if context.mode == 'OBJECT':
            # 8 - TOP
            pie.prop(ts, "use_proportional_edit_objects", text="Toggle Proportional")
            # 7 - TOP - LEFT
            pie.operator(
                "object.set_proportional_falloff", text="Root", icon='ROOTCURVE'
            ).falloff_shape = 'ROOT'
            # 9 - TOP - RIGHT
            pie.operator(
                "object.set_proportional_falloff",
                text="Inverse Square",
                icon='INVERSESQUARECURVE',
            ).falloff_shape = 'INVERSE_SQUARE'
        else:
            # 8 - TOP
            pie.prop(
                ts, "use_proportional_edit", text="Toggle Proportional", icon='PROP_ON'
            )
            # 7 - TOP - LEFT
            pie.prop(
                ts,
                "use_proportional_connected",
                text="Toggle Connected",
                icon='PROP_CON',
            )
            # 9 - TOP - RIGHT
            pie.prop(
                ts,
                "use_proportional_projected",
                text="Toggle Projected",
                icon='PROP_PROJECTED',
            )

        # 1 - BOTTOM - LEFT
        pie.operator(
            "object.set_proportional_falloff", text="Linear", icon='LINCURVE'
        ).falloff_shape = 'LINEAR'

        # 3 - BOTTOM - RIGHT
        pie.operator(
            "object.set_proportional_falloff", text="Sphere", icon='SPHERECURVE'
        ).falloff_shape = 'SPHERE'


class PIE_MT_proportional_edit_mesh_more(Menu):
    bl_idname = "PIE_MT_proportional_edit_mesh_more"
    bl_label = "More Falloff Shapes"

    def draw(self, context):
        layout = self.layout
        layout.operator(
            "object.set_proportional_falloff", text="Root", icon='ROOTCURVE'
        ).falloff_shape = 'ROOT'
        layout.operator(
            "object.set_proportional_falloff",
            text="Inverse Square",
            icon='INVERSESQUARECURVE',
        ).falloff_shape = 'INVERSE_SQUARE'
        layout.operator(
            "object.set_proportional_falloff", text="Constant", icon='NOCURVE'
        ).falloff_shape = 'CONSTANT'
        layout.operator(
            "object.set_proportional_falloff", text="Random", icon='RNDCURVE'
        ).falloff_shape = 'RANDOM'


class PIE_MT_proportional_edit_obj_more(Menu):
    bl_idname = "PIE_MT_proportional_edit_obj_more"
    bl_label = "More Falloff Shapes"

    def draw(self, context):
        layout = self.layout
        layout.operator(
            "object.set_proportional_falloff", text="Constant", icon='NOCURVE'
        ).falloff_shape = 'CONSTANT'
        layout.operator(
            "object.set_proportional_falloff", text="Random", icon='RNDCURVE'
        ).falloff_shape = 'RANDOM'


class OBJECT_OT_set_proportional_falloff(Operator):
    """Enable proportional editing and set the falloff curve"""

    bl_idname = "object.set_proportional_falloff"
    bl_label = "Set Proportional Editing Falloff"
    bl_options = {'REGISTER', 'UNDO'}

    falloff_shape: StringProperty()

    def execute(self, context):
        ts = context.tool_settings
        if context.mode == 'OBJECT':
            ts.use_proportional_edit_objects = True
        else:
            ts.use_proportional_edit = True
        ts.proportional_edit_falloff = self.falloff_shape

        return {'FINISHED'}


registry = (
    PIE_MT_proportional_edit,
    PIE_MT_proportional_edit_mesh_more,
    PIE_MT_proportional_edit_obj_more,
    OBJECT_OT_set_proportional_falloff,
)


def register():
    for km_name, proportional_name in [('Object Mode', 'use_proportional_edit_objects'), ('Mesh', 'use_proportional_edit')]:
        WM_OT_call_menu_pie_drag_only.register_drag_hotkey(
            keymap_name=km_name,
            pie_name=PIE_MT_proportional_edit.bl_idname,
            hotkey_kwargs={'type': "O", 'value': "PRESS"},
            default_fallback_op='wm.context_toggle',
            default_fallback_kwargs={"data_path": f"scene.tool_settings.{proportional_name}"},
        )
