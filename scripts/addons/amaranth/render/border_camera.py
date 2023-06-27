# SPDX-FileCopyrightText: 2019-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
Set Camera Bounds as Render Border

When in camera view, we can now set the border-render to be the same size
of the camera, so we don't render outside the view. Makes faster render
preview. Under Specials menu W, when in Camera view.
"""

import bpy


class AMTH_VIEW3D_OT_render_border_camera(bpy.types.Operator):

    """Set camera bounds as render border"""
    bl_idname = "view3d.render_border_camera"
    bl_label = "Camera as Render Border"

    @classmethod
    def poll(cls, context):
        return context.space_data == 'VIEW_3D' and context.space_data.region_3d.view_perspective == "CAMERA"

    def execute(self, context):
        render = context.scene.render
        render.use_border = True
        render.border_min_x = 0
        render.border_min_y = 0
        render.border_max_x = 1
        render.border_max_y = 1

        return {"FINISHED"}


def button_render_border_camera(self, context):
    view3d = context.space_data.region_3d

    if view3d.view_perspective == "CAMERA":
        layout = self.layout
        layout.separator()
        layout.operator(AMTH_VIEW3D_OT_render_border_camera.bl_idname,
                        text="Camera as Render Border",
                        icon="FULLSCREEN_ENTER")


def register():
    bpy.utils.register_class(AMTH_VIEW3D_OT_render_border_camera)
    bpy.types.VIEW3D_MT_object_context_menu.append(button_render_border_camera)


def unregister():
    bpy.utils.unregister_class(AMTH_VIEW3D_OT_render_border_camera)
    bpy.types.VIEW3D_MT_object_context_menu.remove(button_render_border_camera)
