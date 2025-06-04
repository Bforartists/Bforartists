# SPDX-FileCopyrightText: 2016-2024 Blender Foundation
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.types import Menu, Operator
from bpy.props import StringProperty

from .op_pie_wrappers import WM_OT_call_menu_pie_drag_only


class PIE_MT_set_origin(Menu):
    bl_idname = "PIE_MT_set_origin"
    bl_label = "Set Origin"

    def draw(self, context):
        pie = self.layout.menu_pie()

        # 4 - LEFT
        pie.operator(
            "object.origin_set_any_mode",
            text="Geometry -> Origin",
            icon='TRANSFORM_ORIGINS',
        ).type = 'GEOMETRY_ORIGIN'
        # 6 - RIGHT
        pie.operator(
            "object.origin_set_any_mode",
            text="Origin -> Geometry",
            icon='SNAP_PEEL_OBJECT',
        ).type = 'ORIGIN_GEOMETRY'
        # 2 - BOTTOM
        pie.operator(
            "object.origin_set_to_bottom", text="Origin -> Bottom", icon='TRIA_DOWN'
        )
        # 8 - TOP
        pie.operator(
            "object.origin_set_to_selection",
            text="Origin -> Selection",
            icon='RESTRICT_SELECT_OFF',
        )
        # 7 - TOP - LEFT
        pie.operator(
            "object.origin_set_any_mode", text="Origin -> Cursor", icon='PIVOT_CURSOR'
        ).type = 'ORIGIN_CURSOR'
        # 9 - TOP - RIGHT
        pie.operator(
            "object.origin_set_any_mode", text="Origin -> Mass", icon='SNAP_FACE_CENTER'
        ).type = 'ORIGIN_CENTER_OF_MASS'
        # 1 - BOTTOM - LEFT
        pie.separator()
        # 3 - BOTTOM - RIGHT
        pie.operator(
            "object.origin_set_any_mode",
            text="Origin -> Volume",
            icon='SNAP_FACE_CENTER',
        ).type = 'ORIGIN_CENTER_OF_MASS'


class OBJECT_OT_set_origin_to_selection(Operator):
    bl_idname = "object.origin_set_to_selection"
    bl_label = "Origin To Selection"
    bl_description = "Snap the origin to the selection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        org_mode = 'OBJECT'
        if context.active_object:
            org_mode = context.active_object.mode
        saved_location = context.scene.cursor.location.copy()
        bpy.ops.view3d.snap_cursor_to_selected()
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
        bpy.ops.object.mode_set(mode=org_mode)
        context.scene.cursor.location = saved_location

        self.report({'INFO'}, "Snapped the origin point to the selection.")

        return {'FINISHED'}


class OBJECT_OT_set_origin_to_bottom(Operator):
    bl_idname = "object.origin_set_to_bottom"
    bl_label = "Origin To Bottom"
    bl_description = "Apply transforms and set the Object Origin to the centered lowest point of each selected object"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if not any(
            [ob.type in {'MESH', 'ARMATURE'} for ob in context.selected_objects]
        ):
            cls.poll_message_set("No mesh or armature objects selected.")
            return False
        return True

    def execute(self, context):
        org_active_obj = context.active_object

        for obj in context.selected_objects:
            if obj.type not in ('MESH', 'ARMATURE'):
                obj.select_set(False)

        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')

        counter = 0
        for obj in context.selected_objects:
            counter += int(self.origin_to_bottom(context, obj))

        context.view_layer.objects.active = org_active_obj
        self.report(
            {'INFO'}, f"Moved the origins of {counter} objects to their lowest point."
        )

        return {'FINISHED'}

    @staticmethod
    def origin_to_bottom(context, obj) -> bool:
        if obj.type not in {'MESH', 'ARMATURE'}:
            return False

        org_mode = obj.mode

        try:
            if obj.type == 'MESH':
                bpy.ops.object.mode_set(mode='OBJECT')
                min_z = min([v.co.z for v in obj.data.vertices])
            elif obj.type == 'ARMATURE':
                context.view_layer.objects.active = obj
                bpy.ops.object.mode_set(mode='EDIT')
                min_z = min(
                    [min([bone.head.z, bone.tail.z]) for bone in obj.data.edit_bones]
                )
            else:
                return False
        except ValueError:
            # min([]) would result in this error, so if the object is empty.
            return False

        if obj.type == 'MESH':
            for vert in obj.data.vertices:
                vert.co.z -= min_z
        elif obj.type == 'ARMATURE':
            for bone in obj.data.edit_bones:
                bone.head.z -= min_z
                bone.tail.z -= min_z

        obj.location.z += min_z

        bpy.ops.object.mode_set(mode=org_mode)
        return True


class OBJECT_OT_set_origin_any_mode(Operator):
    bl_idname = "object.origin_set_any_mode"
    bl_label = "Set Origin"
    bl_description = "Set the Object Origin"
    bl_options = {'REGISTER', 'UNDO'}

    type: StringProperty()

    messages = {
        'GEOMETRY_ORIGIN': "Snapped the geometry to the object's origin.",
        'ORIGIN_CURSOR': "Snapped the object's origin to the 3D cursor.",
        'ORIGIN_CENTER_OF_MASS': "Snapped the origin to the geometry's center of mass.",
        'ORIGIN_CENTER_OF_VOLUME': "Snapped the origin to the geometry's center of volume.",
        'ORIGIN_GEOMETRY': "Snapped the origin to the geometry.",
    }

    @classmethod
    def description(cls, context, params):
        return cls.messages[params.type].replace("Snapped", "Snap")[:-1]

    def execute(self, context):
        org_mode = 'OBJECT'
        if context.active_object:
            org_mode = context.active_object.mode

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.origin_set(type=self.type)
        bpy.ops.object.mode_set(mode=org_mode)

        self.report({'INFO'}, self.messages[self.type])

        return {'FINISHED'}


registry = [
    PIE_MT_set_origin,
    OBJECT_OT_set_origin_to_selection,
    OBJECT_OT_set_origin_to_bottom,
    OBJECT_OT_set_origin_any_mode,
]


def register():
    WM_OT_call_menu_pie_drag_only.register_drag_hotkey(
        keymap_name='3D View',
        pie_name=PIE_MT_set_origin.bl_idname,
        hotkey_kwargs={'type': "X", 'value': "PRESS", 'ctrl': True, 'alt': True},
        on_drag=False,
    )
