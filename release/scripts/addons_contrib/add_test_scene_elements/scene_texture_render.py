# gpl: author meta-androcto

import bpy
import mathutils
import math
from math import pi
from bpy.props import *
from mathutils import Vector


class add_texture_scene(bpy.types.Operator):
    bl_idname = "objects_texture.add_scene"
    bl_label = "Create test scene"
    bl_description = "Cycles Scene with Objects"
    bl_register = True
    bl_undo = True

    def execute(self, context):
        blend_data = context.blend_data
        ob = bpy.context.active_object

# add new scene
        bpy.ops.scene.new(type="NEW")
        scene = bpy.context.scene
        bpy.context.scene.render.engine = 'CYCLES'
        scene.name = "scene_texture_cycles"

# render settings
        render = scene.render
        render.resolution_x = 1080
        render.resolution_y = 1080
        render.resolution_percentage = 100

# add new world
        world = bpy.data.worlds.new("Cycles_Textures_World")
        scene.world = world
        world.use_sky_blend = True
        world.use_sky_paper = True
        world.horizon_color = (0.004393, 0.02121, 0.050)
        world.zenith_color = (0.03335, 0.227, 0.359)
        world.light_settings.use_ambient_occlusion = True
        world.light_settings.ao_factor = 0.5

# add camera
        bpy.ops.view3d.viewnumpad(type='TOP')
        bpy.ops.object.camera_add(location=(0, 0, 2.1850), rotation=(0, 0, 0), view_align = True)
        cam = bpy.context.active_object.data
        cam.lens = 35
        cam.draw_size = 0.1

### add plane
        bpy.ops.mesh.primitive_plane_add(enter_editmode=True, location=(0, 0, 0))
        bpy.ops.mesh.subdivide(number_cuts=10, smoothness=0)
        bpy.ops.uv.unwrap(method='CONFORMAL', margin=0.001)
        bpy.ops.object.editmode_toggle()
        plane = bpy.context.active_object

# add plane material
        planeMaterial = blend_data.materials.new("Cycles_Plane_Material")
        bpy.ops.object.material_slot_add()
        plane.material_slots[0].material = planeMaterial
# Diffuse
        planeMaterial.preview_render_type = "FLAT"
        planeMaterial.diffuse_color = (0.2, 0.2, 0.2)
# Cycles
        planeMaterial.use_nodes = True


# Back to Scene
        sc = bpy.context.scene

        return {'FINISHED'}
