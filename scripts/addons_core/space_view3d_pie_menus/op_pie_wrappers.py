# SPDX-FileCopyrightText: 2016-2024 Blender Foundation
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty
import json
from .hotkeys import register_hotkey


def idname_to_op_class(idname: str):
    parts = idname.split(".")
    op = bpy.ops
    for part in parts:
        op = getattr(op, part)
    return op


class WM_OT_call_menu_pie_drag_only(Operator):
    """Summon a pie menu only on mouse drag, otherwise initiate an operator"""
    # This class is for cases where we want to overwrite a built-in shortcut which triggers on Press, 
    # with a pie menu that only appears on mouse drag. 
    # If the user does not mouse drag, invoke the provided fallback operator.
    # In register_drag_hotkey(), the fallback operator is automagically extracted from the keymap,
    # at the moment the hotkey is registered.

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
    fallback_op_kwargs: StringProperty(default="{}", options={'SKIP_SAVE'})

    def invoke(self, context, event):
        if not self.on_drag:
            return self.execute(context)
        self.init_mouse_x = event.mouse_x
        self.init_mouse_y = event.mouse_y
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def invoke_fallback_operator(self):
        op_cls = idname_to_op_class(self.fallback_operator)
        if not op_cls:
            return

        fallback_op_kwargs = json.loads(self.fallback_op_kwargs)
        if type(fallback_op_kwargs) == str:
            # Not sure why json.loads seems to sometimes return a string, but it does 
            # when eg. setting Shift+C to drag, and using it when first launching Blender. 
            # After Reload Scripts, it works fine without this workaround. Weird af.
            fallback_op_kwargs = json.loads(fallback_op_kwargs)

        if op_cls.poll():
            try:
                return op_cls('INVOKE_DEFAULT', **fallback_op_kwargs)
            except TypeError:
                # This can apparently happen sometimes, see issue #86.
                print(f"Pie Menu Fallback Operator failed: {self.fallback_operator}, {self.fallback_op_kwargs}")

    def modal(self, context, event):
        if event.value == 'RELEASE':
            if self.fallback_operator:
                self.invoke_fallback_operator()
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

    @classmethod
    def register_drag_hotkey(
        cls,
        *,
        keymap_name: str,
        pie_name: str,
        hotkey_kwargs={'type': "SPACE", 'value': "PRESS"},
        default_fallback_op="",
        default_fallback_kwargs={},
        on_drag=True,
    ):
        context = bpy.context
        fallback_operator = default_fallback_op
        fallback_op_kwargs = default_fallback_kwargs
        user_kc = context.window_manager.keyconfigs.user
        km = user_kc.keymaps.get(keymap_name)
        if km:
            for kmi in km.keymap_items:
                if all([
                    kmi.type == hotkey_kwargs.get('type', ""),
                    kmi.value == hotkey_kwargs.get('value', "PRESS"),
                    kmi.ctrl == hotkey_kwargs.get('ctrl', False),
                    kmi.shift == hotkey_kwargs.get('shift', False),
                    kmi.alt == hotkey_kwargs.get('alt', False),
                    kmi.oskey == hotkey_kwargs.get('oskey', False),
                    kmi.any == hotkey_kwargs.get('any', False),
                    kmi.key_modifier == hotkey_kwargs.get('key_modifier', 'NONE'),
                    kmi.active
                ]):
                    fallback_operator = kmi.idname
                    if kmi.properties:
                        fallback_op_kwargs = {k:getattr(kmi.properties, k) if hasattr(kmi.properties, k) else v for k, v in kmi.properties.items()}
                    break

        register_hotkey(
            cls.bl_idname,
            op_kwargs={
                'name': pie_name, 
                'fallback_operator': fallback_operator, 
                'fallback_op_kwargs': json.dumps(fallback_op_kwargs),
                'on_drag': on_drag,
            },
            hotkey_kwargs=hotkey_kwargs,
            keymap_name=keymap_name,
        )


registry = [
    WM_OT_call_menu_pie_drag_only,
]
