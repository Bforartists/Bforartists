# SPDX-FileCopyrightText: 2016-2024 Blender Foundation
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.types import Menu, Operator
from bpy.props import EnumProperty, BoolProperty

from .op_pie_wrappers import WM_OT_call_menu_pie_drag_only


class PIE_MT_manipulator(Menu):
    bl_idname = "PIE_MT_manipulator"
    bl_label = "Manipulator"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        space = context.space_data

        # 4 - LEFT
        pie.operator(
            'view3d.set_manipulator', text="Rotation", icon='CON_ROTLIKE', depress=space.show_gizmo_object_rotate
        ).manipulator = 'ROT'
        # 6 - RIGHT
        pie.operator(
            'view3d.set_manipulator', text="Scale", icon='CON_SIZELIKE', depress=space.show_gizmo_object_scale
        ).manipulator = 'SCALE'
        # 2 - BOTTOM
        pie.operator(
            'view3d.set_manipulator', text="None", icon='X'
        ).manipulator='NONE'
        # 8 - TOP
        pie.operator(
            'view3d.set_manipulator', text="Location", icon='CON_LOCLIKE', depress=space.show_gizmo_object_translate
        ).manipulator = 'LOC'
        
        # 7 - TOP-LEFT
        pie.operator(
            'view3d.set_manipulator', text="Loc/Rot", icon='CON_LOCLIKE', depress=space.show_gizmo_object_translate and space.show_gizmo_object_rotate
        ).manipulator='LOCROT'
        # 9 - TOP-RIGHT
        pie.operator(
            'view3d.set_manipulator', text="Loc/Scale", icon='CON_SIZELIKE', depress=space.show_gizmo_object_translate and space.show_gizmo_object_scale
        ).manipulator='LOCSCALE'
        # 1 - BOT-LEFT
        pie.operator(
            'view3d.set_manipulator', text="Loc/Rot/Scale", icon='CON_LOCLIKE', depress=space.show_gizmo_object_translate and space.show_gizmo_object_rotate and space.show_gizmo_object_scale
        ).manipulator = 'LOCROTSCALE'


class VIEW3D_OT_set_manipulator(Operator):
    """Set manipulator type.\nShift: Toggle this manipulator instead"""

    bl_idname = "view3d.set_manipulator"
    bl_label = "Set Manipulator Type"
    bl_options = {'REGISTER', 'UNDO'}

    manipulator: EnumProperty(
        name="Manipulator",
        items=(
            ('NONE', "None", "None"),
            ('LOC', "Translate", "Translate"),
            ('ROT', "Rotate", "Rotate"),
            ('SCALE', "Scale", "Scale"),
            ('LOCROT', "Translate & Rotate", "Translate & Rotate"),
            ('LOCSCALE', "Translate & Scale", "Translate & Scale"),
            ('LOCROTSCALE', "All", "All"),
        ),
        description="Set manipulator type",
        default='LOC',
    )

    toggle: BoolProperty(
        name="Toggle",
        description="Hold Shift to toggle the selected manipulator rather than setting it as the only active one",
        default=False,
        options={'SKIP_SAVE'}
    )

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space and space.type == 'VIEW_3D'

    def invoke(self, context, event):
        self.toggle = event.shift
        return self.execute(context)

    def execute(self, context):
        space = context.space_data

        if self.manipulator != 'NONE':
            space.show_gizmo = True
        if self.toggle:
            if 'SCALE' in self.manipulator:
                space.show_gizmo_object_scale = not space.show_gizmo_object_scale
            if 'ROT' in self.manipulator:
                space.show_gizmo_object_rotate = not space.show_gizmo_object_rotate
            if 'LOC' in self.manipulator:
                space.show_gizmo_object_translate = not space.show_gizmo_object_translate
        else:
            space.show_gizmo_object_scale = 'SCALE' in self.manipulator
            space.show_gizmo_object_rotate = 'ROT' in self.manipulator
            space.show_gizmo_object_translate = 'LOC' in self.manipulator

        return {'FINISHED'}


registry = [
    PIE_MT_manipulator,
    VIEW3D_OT_set_manipulator,
]


def register():
    WM_OT_call_menu_pie_drag_only.register_drag_hotkey(
        keymap_name="3D View",
        pie_name=PIE_MT_manipulator.bl_idname,
        hotkey_kwargs={'type': "SPACE", 'value': "PRESS", 'alt': True},
        on_drag=False,
    )
