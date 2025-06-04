# SPDX-FileCopyrightText: 2016-2024 Blender Foundation
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Requested by users here: https://projects.blender.org/extensions/space_view3d_pie_menus/issues/67

from bpy.types import Menu
from .op_pie_wrappers import WM_OT_call_menu_pie_drag_only


class PIE_MT_object_add(Menu):
    bl_idname = "PIE_MT_object_add"
    bl_label = "Add Object"

    def draw(self, context):
        pie = self.layout.menu_pie()

        # 4 - LEFT
        pie.operator('mesh.primitive_uv_sphere_add', icon='MESH_UVSPHERE', text="UV Sphere")

        # 6 - RIGHT
        pie.operator('mesh.primitive_cube_add', icon='MESH_CUBE', text="Cube")

        # 2 - BOTTOM
        pie.operator('mesh.primitive_monkey_add', icon='MESH_MONKEY', text="Suzanne")

        # 8 - TOP
        pie.operator('mesh.primitive_plane_add', icon='MESH_PLANE', text="Plane")

        # 1 - BOTTOM - LEFT
        pie.operator('mesh.primitive_cylinder_add', icon='MESH_CYLINDER', text="Cylinder")
        # 3 - BOTTOM - RIGHT
        pie.operator('mesh.primitive_circle_add', icon='MESH_CIRCLE', text="Circle")

        pie.operator('curve.primitive_bezier_curve_add', icon='CURVE_BEZCURVE', text="Bezier Curve")

        pie.menu('VIEW3D_MT_add', text="More...", icon='THREE_DOTS')


registry = [PIE_MT_object_add]


def register():
    # TODO: Shouldn't this also work in Mesh Edit mode?
    WM_OT_call_menu_pie_drag_only.register_drag_hotkey(
        keymap_name="Object Mode",
        pie_name=PIE_MT_object_add.bl_idname,
        hotkey_kwargs={'type': "A", 'value': "PRESS", 'shift': True, 'ctrl': True},
        on_drag=False,
    )
