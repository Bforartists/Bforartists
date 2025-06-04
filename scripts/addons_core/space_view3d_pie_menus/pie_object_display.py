# SPDX-FileCopyrightText: 2016-2024 Blender Foundation
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.types import Menu, Operator
from .hotkeys import register_hotkey


class PIE_MT_object_display(Menu):
    bl_idname = "PIE_MT_object_display"
    bl_label = "Object Display"

    @classmethod
    def poll(cls, context):
        return context.active_object

    def draw(self, context):
        pie = self.layout.menu_pie()
        obj = context.active_object

        # 4 - LEFT
        pie.prop(obj, 'show_in_front', icon='XRAY')

        # 6 - RIGHT
        if obj.type in ('MESH', 'CURVE'):
            pie.prop(obj, 'show_wire', text="Wireframe", icon='SHADING_WIRE')
        else:
            pie.separator()

        # 2 - BOTTOM
        pie.prop_menu_enum(obj, 'display_type', text="Display Mode", icon='THREE_DOTS')

        # 8 - TOP
        if obj.type in ('MESH', 'CURVE'):
            box = pie.box().column(align=True)
            box.label(text="Color")
            row = box.row(align=True)
            row.prop(obj, 'color', text="")
            row.operator('view3d.copy_property_to_selected', text="", icon='LOOP_FORWARDS').rna_path='color'
            box.prop(self, 'color')
        else:
            pie.separator()

        # 7 - TOP - LEFT
        if obj.type == 'ARMATURE':
            pie.prop(obj.data, 'show_names', text="Bone Names", icon='FILE_TEXT')
        else:
            pie.prop(obj, 'show_name', text="Object Name", icon='FILE_TEXT')

        # 9 - TOP - RIGHT
        pie.separator()

        # 1 - BOTTOM - LEFT
        if obj.type == 'ARMATURE':
            pie.prop(obj.data, 'show_axes', text="Bone Axes", icon='EMPTY_AXIS')
        else:
            pie.prop(obj, 'show_axis', icon='EMPTY_AXIS')

        # 3 - BOTTOM - RIGHT
        if obj.type in ('MESH', 'CURVE'):
            pie.menu('OBJECT_MT_set_object_shading', icon='THREE_DOTS')
        elif obj.type == 'ARMATURE':
            pie.prop_menu_enum(obj.data, 'display_type', text="Bone Display", icon='THREE_DOTS')
        elif obj.type == 'EMPTY':
            pie.prop_menu_enum(obj, 'empty_display_type', icon='THREE_DOTS')
        else:
            pie.separator()


class OBJECT_MT_set_object_shading(Menu):
    bl_idname = "OBJECT_MT_set_object_shading"
    bl_label = "Shading Operators"

    def draw(self, context):
        layout = self.layout

        layout.operator('object.shade_flat', icon='MESH_UVSPHERE')
        layout.operator('object.shade_smooth', icon='NODE_MATERIAL')
        if context.active_object.type == 'MESH':
            layout.operator('object.shade_auto_smooth', icon='MODIFIER')

        if context.active_object.type == 'MESH':
            layout.separator()
            layout.operator('OBJECT_OT_reset_normals', icon='LOOP_BACK')


class OBJECT_OT_reset_normals(Operator):
    """Reset mesh normals by clearing custom split normals if any, recalculating mesh normals, and setting all faces to smooth shading"""

    bl_idname = "object.reset_normals"
    bl_label = "Reset Normals"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue
            with context.temp_override(active_object=obj, object=obj):
                bpy.ops.mesh.customdata_custom_splitnormals_clear()
            obj.data.shade_smooth()

        org_mode = context.active_object.mode
        if org_mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.reveal()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.normals_make_consistent()

        if context.active_object.mode != org_mode:
            bpy.ops.object.mode_set(mode=org_mode)

        return {'FINISHED'}


registry = [
    PIE_MT_object_display,
    OBJECT_MT_set_object_shading,
    OBJECT_OT_reset_normals,
]


def register():
    register_hotkey(
        'wm.call_menu_pie',
        op_kwargs={'name': 'PIE_MT_object_display'},
        hotkey_kwargs={'type': "W", 'value': "PRESS", 'shift': True},
        key_cat="3D View",
    )
