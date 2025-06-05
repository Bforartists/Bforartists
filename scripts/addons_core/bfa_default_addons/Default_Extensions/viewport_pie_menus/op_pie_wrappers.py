# SPDX-FileCopyrightText: 2016-2024 Blender Foundation
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty
import json


class WM_OT_call_menu_pie_drag_only(Operator):
    """Summon a pie menu only on mouse drag, otherwise pass the hotkey through"""
    # This wrapper class is necessary for cases where we want to overwrite a built-in shortcut
    # which triggers on Press, with a pie menu that only appears on Drag, and otherwise (on Click)
    # it can run the operator that would normally be triggered on Press.
    bl_idname = "wm.call_menu_pie_drag_only"
    bl_label = "Pie Menu on Drag"
    bl_options = {'REGISTER', 'INTERNAL'}

    name: StringProperty(options={'SKIP_SAVE'})
    on_drag: BoolProperty(
        name="On Drag",
        default=True,
        description="Only show this pie menu on mouse drag, otherwise execute a default operator",
        options={'SKIP_SAVE'},
    )
    fallback_operator: StringProperty(options={'SKIP_SAVE'})
    op_kwargs: StringProperty(default="{}", options={'SKIP_SAVE'})

    def invoke(self, context, event):
        if not self.on_drag:
            return self.execute(context)
        self.init_mouse_x = event.mouse_x
        self.init_mouse_y = event.mouse_y
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.value == 'RELEASE':
            if self.fallback_operator:
                parts = self.fallback_operator.split(".")
                op = bpy.ops
                for part in parts:
                    op = getattr(op, part)
                kwargs = json.loads(self.op_kwargs)
                if op.poll():
                    op('INVOKE_DEFAULT', **kwargs)
                return {'CANCELLED'}
        threshold = context.preferences.inputs.drag_threshold
        delta_x = abs(event.mouse_x - self.init_mouse_x)
        delta_y = abs(event.mouse_y - self.init_mouse_y)
        if delta_x > threshold or delta_y > threshold:
            return self.execute(context)

        return {'RUNNING_MODAL'}

    def execute(self, context):
        bpy.ops.wm.call_menu_pie(name=self.name)
        return {'FINISHED'}


class WM_OT_call_menu_pie_wrapper(Operator):
    """Summon a pie menu"""
    # This class helps us hide a pie menu from Menu Search, which would spam the console
    # in some cases with useless warnings 
    # (like if a pie menu has a shortcut and draws Float or StringProps, eg. Camera Pie)
    bl_idname = "wm.call_menu_pie_wrapper"
    bl_label = "Pie Menu"
    bl_options = {'REGISTER', 'INTERNAL'}

    name: StringProperty()

    def execute(self, context):
        bpy.ops.wm.call_menu_pie(name=self.name)
        return {'FINISHED'}


registry = [
    WM_OT_call_menu_pie_drag_only,
    WM_OT_call_menu_pie_wrapper,
]
