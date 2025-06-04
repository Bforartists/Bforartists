# SPDX-FileCopyrightText: 2016-2024 Blender Foundation
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.types import Menu, Operator
from bpy.props import EnumProperty

from .op_pie_wrappers import WM_OT_call_menu_pie_drag_only


class PIE_MT_mesh_flatten(Menu):
    bl_idname = "PIE_MT_mesh_flatten"
    bl_label = "Mesh Flatten"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        # 4 - LEFT
        box = pie.box().column(align=True)

        box.label(text="Selection Bounds", icon='PIVOT_BOUNDBOX')
        for axis in "XYZ":
            row = box.row()
            op = row.operator("transform.flatten_to_selection_bounding_box", text=f"    -{axis}")
            op.axis = axis
            op.side = 'NEGATIVE'
            op = row.operator("transform.flatten_to_selection_bounding_box", text=f"     +{axis}")
            op.axis = axis
            op.side = 'POSITIVE'

        # 6 - RIGHT
        pie.separator()

        # 2 - BOTTOM
        pie.operator("transform.flatten_to_origin", text="Origin Y", icon='OBJECT_ORIGIN').axis = 'Y'
        # 8 - TOP
        pie.operator("transform.flatten_to_center", text="Center Y", icon='ORIENTATION_GLOBAL').axis = 'Y'
        # 7 - TOP - LEFT
        pie.operator("transform.flatten_to_center", text="Center X", icon='ORIENTATION_GLOBAL').axis = 'X'
        # 9 - TOP - RIGHT
        pie.operator("transform.flatten_to_center", text="Center Z", icon='ORIENTATION_GLOBAL').axis = 'Z'
        # 1 - BOTTOM - LEFT
        pie.operator("transform.flatten_to_origin", text="Origin X", icon='OBJECT_ORIGIN').axis = 'X'
        # 3 - BOTTOM - RIGHT
        pie.operator("transform.flatten_to_origin", text="Origin Z", icon='OBJECT_ORIGIN').axis = 'Z'


class TRANSFORM_OT_flatten_to_center(Operator):
    """Flatten selection along a global axis"""

    bl_idname = "transform.flatten_to_center"
    bl_label = "Flatten to Center"
    bl_options = {'REGISTER', 'UNDO'}

    axis: EnumProperty(
        name="Axis",
        items=(
            ('X', "X", "X Axis"),
            ('Y', "Y", "Y Axis"),
            ('Z', "Z", "Z Axis"),
        ),
        description="Choose an axis for alignment",
        default='X',
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == "MESH"

    def execute(self, context):
        values = {
            'X': [(0, 1, 1), (True, False, False)],
            'Y': [(1, 0, 1), (False, True, False)],
            'Z': [(1, 1, 0), (False, False, True)],
        }
        chosen_value = values[self.axis][0]
        constraint_value = values[self.axis][1]
        bpy.ops.transform.resize(
            value=chosen_value,
            constraint_axis=constraint_value,
            orient_type='GLOBAL',
            mirror=False,
            use_proportional_edit=False,
        )
        return {'FINISHED'}


class TRANSFORM_OT_flatten_to_object_origin(Operator):
    """Flatten selection to the object's origin"""

    bl_idname = "transform.flatten_to_origin"
    bl_label = "Flatten to Origin"
    bl_options = {'REGISTER', 'UNDO'}

    axis: EnumProperty(
        name="Axis",
        items=(
            ('X', "X", "X Axis"),
            ('Y', "Y", "Y Axis"),
            ('Z', "Z", "Z Axis"),
        ),
        description="Choose an axis for alignment",
        default='X',
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == "MESH"

    def execute(self, context):
        bpy.ops.object.mode_set(mode='OBJECT')
        index = "XYZ".find(self.axis)
        for vert in bpy.context.object.data.vertices:
            if vert.select:
                vert.co[index] = 0
        bpy.ops.object.editmode_toggle()

        return {'FINISHED'}


class TRANSFORM_OT_flatten_to_selection_bounding_box(Operator):
    """Flatten to bounding box of the selection"""

    bl_idname = "transform.flatten_to_selection_bounding_box"
    bl_label = "Flatten to Selection Bounding Box"
    bl_options = {'REGISTER', 'UNDO'}

    axis: EnumProperty(
        name="Axis",
        items=(
            ('X', "X", "X Axis"),
            ('Y', "Y", "Y Axis"),
            ('Z', "Z", "Z Axis"),
        ),
        description="Choose an axis for alignment",
        default='X',
    )
    side: EnumProperty(
        name="Side",
        items=[
            ('POSITIVE', "Front", "Align on the positive chosen axis"),
            ('NEGATIVE', "Back", "Align acriss the negative chosen axis"),
        ],
        description="Choose a side for alignment",
        default='POSITIVE',
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == "MESH"

    def execute(self, context):
        bpy.ops.object.mode_set(mode='OBJECT')
        count = 0
        axis_idx = "XYZ".find(self.axis)
        for vert in bpy.context.object.data.vertices:
            if vert.select:
                if count == 0:
                    maxv = vert.co[axis_idx]
                    count += 1
                    continue
                count += 1
                if self.side == 'POSITIVE':
                    if vert.co[axis_idx] > maxv:
                        maxv = vert.co[axis_idx]
                else:
                    if vert.co[axis_idx] < maxv:
                        maxv = vert.co[axis_idx]

        bpy.ops.object.mode_set(mode='OBJECT')

        for vert in bpy.context.object.data.vertices:
            if vert.select:
                vert.co[axis_idx] = maxv
        bpy.ops.object.mode_set(mode='EDIT')

        return {'FINISHED'}


registry = [
    PIE_MT_mesh_flatten,
    TRANSFORM_OT_flatten_to_center,
    TRANSFORM_OT_flatten_to_object_origin,
    TRANSFORM_OT_flatten_to_selection_bounding_box,
]


def register():
    WM_OT_call_menu_pie_drag_only.register_drag_hotkey(
        keymap_name="Mesh",
        pie_name=PIE_MT_mesh_flatten.bl_idname,
        hotkey_kwargs={'type': "X", 'value': "PRESS", 'alt': True},
        on_drag=False,
    )
