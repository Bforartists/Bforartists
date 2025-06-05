# SPDX-FileCopyrightText: 2022-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy

class VIEW3D_OT_camera_flip_x(bpy.types.Operator):
    bl_idname = "view3d.camera_flip_x"
    bl_label = "Camera Flip X"
    bl_description = "Invert active camera scale.x to flip view horizontally"
    bl_options = {"REGISTER", "UNDO_GROUPED"}

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D' \
            and context.space_data.region_3d.view_perspective == 'CAMERA'

    def execute(self, context):
        context.scene.camera.scale.x *= -1
        return {"FINISHED"}

def register():
    bpy.utils.register_class(VIEW3D_OT_camera_flip_x)

def unregister():
    bpy.utils.unregister_class(VIEW3D_OT_camera_flip_x)
