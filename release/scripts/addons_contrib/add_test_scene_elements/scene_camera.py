# gpl: author meta-androcto

import bpy
import mathutils
import math
from math import pi
from bpy.props import *
from mathutils import Vector


class add_scene_camera(bpy.types.Operator):
    bl_idname = "camera.add_scene"
    bl_label = "Camera Only"
    bl_description = "Empty scene with Camera"
    bl_register = True
    bl_undo = True

    def execute(self, context):
        blend_data = context.blend_data
        ob = bpy.context.active_object

# add new scene
        bpy.ops.scene.new(type="NEW")
        scene = bpy.context.scene
        scene.name = "scene_camera"

# render settings
        render = scene.render
        render.resolution_x = 1920
        render.resolution_y = 1080
        render.resolution_percentage = 50

# add new world
        world = bpy.data.worlds.new("Camera_World")
        scene.world = world
        world.use_sky_blend = True
        world.use_sky_paper = True
        world.horizon_color = (0.004393, 0.02121, 0.050)
        world.zenith_color = (0.03335, 0.227, 0.359)
        world.light_settings.use_ambient_occlusion = True
        world.light_settings.ao_factor = 0.25

# add camera
        bpy.ops.object.camera_add(location=(7.48113, -6.50764, 5.34367), rotation=(1.109319, 0.010817, 0.814928),)
        cam = bpy.context.active_object.data
        cam.lens = 35
        cam.draw_size = 0.1
        bpy.ops.view3d.viewnumpad(type='CAMERA')
        return {"FINISHED"}
