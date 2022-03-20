# SPDX-License-Identifier: GPL-2.0-or-later

import bpy

class GP_OT_camera_flip_x(bpy.types.Operator):
    bl_idname = "gp.camera_flip_x"
    bl_label = "Camera Flip X"
    bl_description = "Invert active camera scale.x to flip view horizontally"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return context.space_data.region_3d.view_perspective == 'CAMERA'

    def execute(self, context):
        context.scene.camera.scale.x *= -1
        return {"FINISHED"}

def register():
    bpy.utils.register_class(GP_OT_camera_flip_x)

def unregister():
    bpy.utils.unregister_class(GP_OT_camera_flip_x)
