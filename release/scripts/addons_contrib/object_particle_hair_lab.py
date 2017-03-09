# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Grass Lab",
    "author": "Ondrej Raha(lokhorn), meta-androcto",
    "version": (0, 5),
    "blender": (2, 75, 0),
    "location": "View3D > ToolShelf > Create Tab",
    "description": "Creates particle grass with material",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Object/Hair_Lab",
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
    "category": "Object"}


import bpy
from bpy.props import *

# Returns the action we want to take
def getActionToDo(obj):
    if not obj or obj.type != 'MESH':
        return 'NOT_OBJ_DO_NOTHING'
    elif obj.type == 'MESH':
        return 'GENERATE'
    else:
        return "DO_NOTHING"

# TO DO
"""
class saveSelectionPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'

    bl_label = "Selection Save"
    bl_options = {'DEFAULT_CLOSED'}
    bl_context = "particlemode"


    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        col.operator("save.selection", text="Save Selection 1")
"""
######GRASS########################
class grassLabPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_label = "Grass Lab"
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}
    bl_category = "Create"

    def draw(self, context):
        active_obj = bpy.context.active_object
        active_scn = bpy.context.scene.name
        layout = self.layout
        col = layout.column(align=True)

        WhatToDo = getActionToDo(active_obj)


        if WhatToDo == "GENERATE":
            col.operator("grass.generate_grass", text="Create grass")

            col.prop(context.scene, "grass_type")
        else:
            col.label(text="Select mesh object")

        if active_scn == "TestgrassScene":
            col.operator("grass.switch_back", text="Switch back to scene")
        else:
            col.operator("grass.test_scene", text="Create Test Scene")

# TO DO
"""
class saveSelection(bpy.types.Operator):
    bl_idname = "save.selection"
    bl_label = "Save Selection"
    bl_description = "Save selected particles"
    bl_register = True
    bl_undo = True

    def execute(self, context):

        return {'FINISHED'}
"""
class testScene1(bpy.types.Operator):
    bl_idname = "grass.switch_back"
    bl_label = "Switch back to scene"
    bl_description = "If you want keep this scene, switch scene in info window"
    bl_register = True
    bl_undo = True

    def execute(self, context):
        scene = bpy.context.scene
        bpy.data.scenes.remove(scene)

        return {'FINISHED'}


class testScene2(bpy.types.Operator):
    bl_idname = "grass.test_scene"
    bl_label = "Create test scene"
    bl_description = "You can switch scene in info panel"
    bl_register = True
    bl_undo = True

    def execute(self, context):
# add new scene
        bpy.ops.scene.new(type="NEW")
        scene = bpy.context.scene
        scene.name = "TestgrassScene"
# render settings
        render = scene.render
        render.resolution_x = 1920
        render.resolution_y = 1080
        render.resolution_percentage = 50
# add new world
        world = bpy.data.worlds.new("grassWorld")
        scene.world = world
        world.use_sky_blend = True
        world.use_sky_paper = True
        world.horizon_color = (0.004393,0.02121,0.050)
        world.zenith_color = (0.03335,0.227,0.359)

# add text
        bpy.ops.object.text_add(location=(-0.292,0,-0.152), rotation =(1.571,0,0))
        text = bpy.context.active_object
        text.scale = (0.05,0.05,0.05)
        text.data.body = "Grass Lab"

# add material to text
        textMaterial = bpy.data.materials.new('textMaterial')
        text.data.materials.append(textMaterial)
        textMaterial.use_shadeless = True

# add camera
        bpy.ops.object.camera_add(location = (0,-1,0),rotation = (1.571,0,0))
        cam = bpy.context.active_object.data
        cam.lens = 50
        cam.draw_size = 0.1

# add spot lamp
        bpy.ops.object.lamp_add(type="SPOT", location = (-0.7,-0.5,0.3), rotation =(1.223,0,-0.960))
        lamp1 = bpy.context.active_object.data
        lamp1.name = "Key Light"
        lamp1.energy = 1.5
        lamp1.distance = 1.5
        lamp1.shadow_buffer_soft = 5
        lamp1.shadow_buffer_size = 8192
        lamp1.shadow_buffer_clip_end = 1.5
        lamp1.spot_blend = 0.5

# add spot lamp2
        bpy.ops.object.lamp_add(type="SPOT", location = (0.7,-0.6,0.1), rotation =(1.571,0,0.785))
        lamp2 = bpy.context.active_object.data
        lamp2.name = "Fill Light"
        lamp2.color = (0.874,0.874,1)
        lamp2.energy = 0.5
        lamp2.distance = 1.5
        lamp2.shadow_buffer_soft = 5
        lamp2.shadow_buffer_size = 4096
        lamp2.shadow_buffer_clip_end = 1.5
        lamp2.spot_blend = 0.5

# light Rim
        """
        # add spot lamp3
        bpy.ops.object.lamp_add(type="SPOT", location = (0.191,0.714,0.689), rotation =(0.891,0,2.884))
        lamp3 = bpy.context.active_object.data
        lamp3.name = "Rim Light"
        lamp3.color = (0.194,0.477,1)
        lamp3.energy = 3
        lamp3.distance = 1.5
        lamp3.shadow_buffer_soft = 5
        lamp3.shadow_buffer_size = 4096
        lamp3.shadow_buffer_clip_end = 1.5
        lamp3.spot_blend = 0.5
        """
# add sphere
# add sphere
        bpy.ops.mesh.primitive_uv_sphere_add(size=0.1)
        bpy.ops.object.shade_smooth()

        return {'FINISHED'}


class Generategrass(bpy.types.Operator):
    bl_idname = "grass.generate_grass"
    bl_label = "Generate grass"
    bl_description = "Create a grass"
    bl_register = True
    bl_undo = True

    def execute(self, context):
# Make variable that is the current .blend file main data blocks
        blend_data = context.blend_data
        ob = bpy.context.active_object
        scene = context.scene

######################################################################
########################Test screen grass########################
        if scene.grass_type == '0':

###############Create New Material##################
# add new material
            grassMaterial = bpy.data.materials.new('greengrassMat')
            ob.data.materials.append(grassMaterial)

#Material settings
            grassMaterial.preview_render_type = "HAIR"
            grassMaterial.diffuse_color = (0.09710, 0.288, 0.01687)
            grassMaterial.specular_color = (0.604, 0.465, 0.136)
            grassMaterial.specular_intensity = 0.3
            grassMaterial.ambient = 0
            grassMaterial.use_cubic = True
            grassMaterial.use_transparency = True
            grassMaterial.alpha = 0
            grassMaterial.use_transparent_shadows = True
            #strand
            grassMaterial.strand.use_blender_units = True
            grassMaterial.strand.root_size = 0.00030
            grassMaterial.strand.tip_size = 0.00010
            grassMaterial.strand.size_min = 0.7
            grassMaterial.strand.width_fade = 0.1
            grassMaterial.strand.shape = 0.061
            grassMaterial.strand.blend_distance = 0.001


# add texture
            grassTex = bpy.data.textures.new("greengrassTex", type='BLEND')
            grassTex.use_preview_alpha = True
            grassTex.use_color_ramp = True
            ramp = grassTex.color_ramp
            rampElements = ramp.elements
            rampElements[0].position = 0
            rampElements[0].color = [0.114,0.375,0.004025,0.38]
            rampElements[1].position = 1
            rampElements[1].color = [0.267,0.155,0.02687,0]
            rampElement1 = rampElements.new(0.111)
            rampElement1.color = [0.281,0.598,0.03157,0.65]
            rampElement2 = rampElements.new(0.366)
            rampElement2.color = [0.119,0.528,0.136,0.87]
            rampElement3 = rampElements.new(0.608)
            rampElement3.color = [0.247,0.713,0.006472,0.8]
            rampElement4 = rampElements.new(0.828)
            rampElement4.color = [0.01943,0.163,0.01242,0.64]

# add texture to material
            MTex = grassMaterial.texture_slots.add()
            MTex.texture = grassTex
            MTex.texture_coords = "STRAND"
            MTex.use_map_alpha = True



###############  Create Particles  ##################
# Add new particle system

            NumberOfMaterials = 0
            for i in ob.data.materials:
                NumberOfMaterials +=1


            bpy.ops.object.particle_system_add()
#Particle settings setting it up!
            grassParticles = bpy.context.object.particle_systems.active
            grassParticles.name = "greengrassPar"
            grassParticles.settings.type = "HAIR"
            grassParticles.settings.use_advanced_hair = True
            grassParticles.settings.count = 500
            grassParticles.settings.normal_factor = 0.05
            grassParticles.settings.factor_random = 0.001
            grassParticles.settings.use_dynamic_rotation = True

            grassParticles.settings.material = NumberOfMaterials

            grassParticles.settings.use_strand_primitive = True
            grassParticles.settings.use_hair_bspline = True
            grassParticles.settings.render_step = 5
            grassParticles.settings.length_random = 0.5
            grassParticles.settings.draw_step = 5
# children
            grassParticles.settings.rendered_child_count = 50
            grassParticles.settings.child_type = "INTERPOLATED"
            grassParticles.settings.child_length = 0.250
            grassParticles.settings.create_long_hair_children = True
            grassParticles.settings.clump_shape = 0.074
            grassParticles.settings.clump_factor = 0.55
            grassParticles.settings.roughness_endpoint = 0.080
            grassParticles.settings.roughness_end_shape = 0.80
            grassParticles.settings.roughness_2 = 0.043
            grassParticles.settings.roughness_2_size = 0.230


######################################################################
######################  Field Grass  ########################
        if scene.grass_type == '1':
###############Create New Material##################
# add new material
            grassMaterial = bpy.data.materials.new('fieldgrassMat')
            ob.data.materials.append(grassMaterial)

#Material settings
            grassMaterial.preview_render_type = "HAIR"
            grassMaterial.diffuse_color = (0.229, 0.800, 0.010)
            grassMaterial.specular_color = (0.010, 0.06072, 0.000825)
            grassMaterial.specular_intensity = 0.3
            grassMaterial.specular_hardness = 100
            grassMaterial.use_specular_ramp = True

            ramp = grassMaterial.specular_ramp
            rampElements = ramp.elements
            rampElements[0].position = 0
            rampElements[0].color = [0.0356,0.0652,0.009134,0]
            rampElements[1].position = 1
            rampElements[1].color = [0.352,0.750,0.231,1]
            rampElement1 = rampElements.new(0.255)
            rampElement1.color = [0.214,0.342,0.0578,0.31]
            rampElement2 = rampElements.new(0.594)
            rampElement2.color = [0.096,0.643,0.0861,0.72]

            grassMaterial.ambient = 0
            grassMaterial.use_cubic = True
            grassMaterial.use_transparency = True
            grassMaterial.alpha = 0
            grassMaterial.use_transparent_shadows = True
            #strand
            grassMaterial.strand.use_blender_units = True
            grassMaterial.strand.root_size = 0.00030
            grassMaterial.strand.tip_size = 0.00015
            grassMaterial.strand.size_min = 0.450
            grassMaterial.strand.width_fade = 0.1
            grassMaterial.strand.shape = 0.02
            grassMaterial.strand.blend_distance = 0.001


# add texture
            grassTex = bpy.data.textures.new("feildgrassTex", type='BLEND')
            grassTex.name = "feildgrassTex"
            grassTex.use_preview_alpha = True
            grassTex.use_color_ramp = True
            ramp = grassTex.color_ramp
            rampElements = ramp.elements
            rampElements[0].position = 0
            rampElements[0].color = [0.009721,0.006049,0.003677,0.38]
            rampElements[1].position = 1
            rampElements[1].color = [0.04231,0.02029,0.01444,0.16]
            rampElement1 = rampElements.new(0.111)
            rampElement1.color = [0.01467,0.005307,0.00316,0.65]
            rampElement2 = rampElements.new(0.366)
            rampElement2.color = [0.0272,0.01364,0.01013,0.87]
            rampElement3 = rampElements.new(0.608)
            rampElement3.color = [0.04445,0.02294,0.01729,0.8]
            rampElement4 = rampElements.new(0.828)
            rampElement4.color = [0.04092,0.0185,0.01161,0.64]

# add texture to material
            MTex = grassMaterial.texture_slots.add()
            MTex.texture = grassTex
            MTex.texture_coords = "STRAND"
            MTex.use_map_alpha = True


###############Create Particles##################
# Add new particle system

            NumberOfMaterials = 0
            for i in ob.data.materials:
                NumberOfMaterials +=1


            bpy.ops.object.particle_system_add()
#Particle settings setting it up!
            grassParticles = bpy.context.object.particle_systems.active
            grassParticles.name = "fieldgrassPar"
            grassParticles.settings.type = "HAIR"
            grassParticles.settings.use_emit_random = True
            grassParticles.settings.use_even_distribution = True
            grassParticles.settings.use_advanced_hair = True
            grassParticles.settings.count = 2000
#Particle settings Velocity
            grassParticles.settings.normal_factor = 0.060
            grassParticles.settings.factor_random = 0.045
            grassParticles.settings.use_dynamic_rotation = False
            grassParticles.settings.brownian_factor = 0.070
            grassParticles.settings.damping = 0.160
            grassParticles.settings.material = NumberOfMaterials
 # strands
            grassParticles.settings.use_strand_primitive = True
            grassParticles.settings.use_hair_bspline = True
            grassParticles.settings.render_step = 7
            grassParticles.settings.length_random = 1.0
            grassParticles.settings.draw_step = 2
# children
            grassParticles.settings.child_type = "INTERPOLATED"
            grassParticles.settings.child_length = 0.160
            grassParticles.settings.create_long_hair_children = False
            grassParticles.settings.clump_factor = 0.000
            grassParticles.settings.clump_shape = 0.000
            grassParticles.settings.roughness_endpoint = 0.000
            grassParticles.settings.roughness_end_shape = 1
            grassParticles.settings.roughness_2 = 0.200
            grassParticles.settings.roughness_2_size = 0.230


######################################################################
########################Short Clumpped grass##########################
        elif scene.grass_type == '2':
###############Create New Material##################
# add new material
            grassMaterial = bpy.data.materials.new('clumpygrassMat')
            ob.data.materials.append(grassMaterial)

#Material settings
            grassMaterial.preview_render_type = "HAIR"
            grassMaterial.diffuse_color = (0.01504, 0.05222, 0.007724)
            grassMaterial.specular_color = (0.02610, 0.196, 0.04444)
            grassMaterial.specular_intensity = 0.5
            grassMaterial.specular_hardness = 100
            grassMaterial.ambient = 0
            grassMaterial.use_cubic = True
            grassMaterial.use_transparency = True
            grassMaterial.alpha = 0
            grassMaterial.use_transparent_shadows = True
#strand
            grassMaterial.strand.use_blender_units = True
            grassMaterial.strand.root_size = 0.000315
            grassMaterial.strand.tip_size = 0.00020
            grassMaterial.strand.size_min = 0.2
            grassMaterial.strand.width_fade = 0.1
            grassMaterial.strand.shape = -0.900
            grassMaterial.strand.blend_distance = 0.001

# add texture
            grassTex = bpy.data.textures.new("clumpygrasstex", type='BLEND')
            grassTex.use_preview_alpha = True
            grassTex.use_color_ramp = True
            ramp = grassTex.color_ramp
            rampElements = ramp.elements
            rampElements[0].position = 0
            rampElements[0].color = [0.004025,0.002732,0.002428,0.38]
            rampElements[1].position = 1
            rampElements[1].color = [0.141,0.622,0.107,0.2]
            rampElement1 = rampElements.new(0.202)
            rampElement1.color = [0.01885,0.2177,0.01827,0.65]
            rampElement2 = rampElements.new(0.499)
            rampElement2.color = [0.114,0.309,0.09822,0.87]
            rampElement3 = rampElements.new(0.828)
            rampElement3.color = [0.141,0.427,0.117,0.64]

# add texture to material
            MTex = grassMaterial.texture_slots.add()
            MTex.texture = grassTex
            MTex.texture_coords = "STRAND"
            MTex.use_map_alpha = True


###############Create Particles##################
# Add new particle system

            NumberOfMaterials = 0
            for i in ob.data.materials:
                NumberOfMaterials +=1


            bpy.ops.object.particle_system_add()
#Particle settings setting it up!
            grassParticles = bpy.context.object.particle_systems.active
            grassParticles.name = "clumpygrass"
            grassParticles.settings.type = "HAIR"
            grassParticles.settings.use_advanced_hair = True
            grassParticles.settings.hair_step = 2
            grassParticles.settings.count = 250
            grassParticles.settings.normal_factor = 0.0082
            grassParticles.settings.tangent_factor = 0.001
            grassParticles.settings.tangent_phase = 0.250
            grassParticles.settings.factor_random = 0.001
            grassParticles.settings.use_dynamic_rotation = True

            grassParticles.settings.material = NumberOfMaterials

            grassParticles.settings.use_strand_primitive = True
            grassParticles.settings.use_hair_bspline = True
            grassParticles.settings.render_step = 3
            grassParticles.settings.length_random = 0.3
            grassParticles.settings.draw_step = 3
# children
            grassParticles.settings.child_type = "INTERPOLATED"
            grassParticles.settings.child_length = 0.667
            grassParticles.settings.child_length_threshold = 0.111
            grassParticles.settings.rendered_child_count = 200
            grassParticles.settings.virtual_parents = 1
            grassParticles.settings.clump_factor = 0.425
            grassParticles.settings.clump_shape = -0.999
            grassParticles.settings.roughness_endpoint = 0.003
            grassParticles.settings.roughness_end_shape = 5



        return {'FINISHED'}

####
######### HAIR LAB ##########
####
class HairLabPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_label = "Hair Lab"
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}
    bl_category = "Create"

    def draw(self, context):
        active_obj = bpy.context.active_object
        active_scn = bpy.context.scene.name
        layout = self.layout
        col = layout.column(align=True)

        WhatToDo = getActionToDo(active_obj)


        if WhatToDo == "GENERATE":
            col.operator("hair.generate_hair", text="Create Hair")

            col.prop(context.scene, "hair_type")
        else:
            col.label(text="Select mesh object")

        if active_scn == "TestHairScene":
            col.operator("hair.switch_back", text="Switch back to scene")
        else:
            col.operator("hair.test_scene", text="Create Test Scene")

# TO DO
"""
class saveSelection(bpy.types.Operator):
    bl_idname = "save.selection"
    bl_label = "Save Selection"
    bl_description = "Save selected particles"
    bl_register = True
    bl_undo = True

    def execute(self, context):

        return {'FINISHED'}
"""
class testScene3(bpy.types.Operator):
    bl_idname = "hair.switch_back"
    bl_label = "Switch back to scene"
    bl_description = "If you want keep this scene, switch scene in info window"
    bl_register = True
    bl_undo = True

    def execute(self, context):
        scene = bpy.context.scene
        bpy.data.scenes.remove(scene)

        return {'FINISHED'}


class testScene4(bpy.types.Operator):
    bl_idname = "hair.test_scene"
    bl_label = "Create test scene"
    bl_description = "You can switch scene in info panel"
    bl_register = True
    bl_undo = True

    def execute(self, context):
# add new scene
        bpy.ops.scene.new(type="NEW")
        scene = bpy.context.scene
        scene.name = "TestHairScene"
# render settings
        render = scene.render
        render.resolution_x = 1920
        render.resolution_y = 1080
        render.resolution_percentage = 50
# add new world
        world = bpy.data.worlds.new("HairWorld")
        scene.world = world
        world.use_sky_blend = True
        world.use_sky_paper = True
        world.horizon_color = (0.004393,0.02121,0.050)
        world.zenith_color = (0.03335,0.227,0.359)

# add text
        bpy.ops.object.text_add(location=(-0.292,0,-0.152), rotation =(1.571,0,0))
        text = bpy.context.active_object
        text.scale = (0.05,0.05,0.05)
        text.data.body = "Hair Lab"

# add material to text
        textMaterial = bpy.data.materials.new('textMaterial')
        text.data.materials.append(textMaterial)
        textMaterial.use_shadeless = True

# add camera
        bpy.ops.object.camera_add(location = (0,-1,0),rotation = (1.571,0,0))
        cam = bpy.context.active_object.data
        cam.lens = 50
        cam.draw_size = 0.1

# add spot lamp
        bpy.ops.object.lamp_add(type="SPOT", location = (-0.7,-0.5,0.3), rotation =(1.223,0,-0.960))
        lamp1 = bpy.context.active_object.data
        lamp1.name = "Key Light"
        lamp1.energy = 1.5
        lamp1.distance = 1.5
        lamp1.shadow_buffer_soft = 5
        lamp1.shadow_buffer_size = 8192
        lamp1.shadow_buffer_clip_end = 1.5
        lamp1.spot_blend = 0.5

# add spot lamp2
        bpy.ops.object.lamp_add(type="SPOT", location = (0.7,-0.6,0.1), rotation =(1.571,0,0.785))
        lamp2 = bpy.context.active_object.data
        lamp2.name = "Fill Light"
        lamp2.color = (0.874,0.874,1)
        lamp2.energy = 0.5
        lamp2.distance = 1.5
        lamp2.shadow_buffer_soft = 5
        lamp2.shadow_buffer_size = 4096
        lamp2.shadow_buffer_clip_end = 1.5
        lamp2.spot_blend = 0.5

# light Rim
        """
        # add spot lamp3
        bpy.ops.object.lamp_add(type="SPOT", location = (0.191,0.714,0.689), rotation =(0.891,0,2.884))
        lamp3 = bpy.context.active_object.data
        lamp3.name = "Rim Light"
        lamp3.color = (0.194,0.477,1)
        lamp3.energy = 3
        lamp3.distance = 1.5
        lamp3.shadow_buffer_soft = 5
        lamp3.shadow_buffer_size = 4096
        lamp3.shadow_buffer_clip_end = 1.5
        lamp3.spot_blend = 0.5
        """
# add sphere
        bpy.ops.mesh.primitive_uv_sphere_add(size=0.1)
        bpy.ops.object.shade_smooth()
        return {'FINISHED'}


class GenerateHair(bpy.types.Operator):
    bl_idname = "hair.generate_hair"
    bl_label = "Generate Hair"
    bl_description = "Create a Hair"
    bl_register = True
    bl_undo = True

    def execute(self, context):
# Make variable that is the current .blend file main data blocks
        blend_data = context.blend_data
        ob = bpy.context.active_object
        scene = context.scene

######################################################################
########################Long Red Straight Hair########################
        if scene.hair_type == '0':

###############Create New Material##################
# add new material
            hairMaterial = bpy.data.materials.new('LongRedStraightHairMat')
            ob.data.materials.append(hairMaterial)

#Material settings
            hairMaterial.preview_render_type = "HAIR"
            hairMaterial.diffuse_color = (0.287, 0.216, 0.04667)
            hairMaterial.specular_color = (0.604, 0.465, 0.136)
            hairMaterial.specular_intensity = 0.3
            hairMaterial.ambient = 0
            hairMaterial.use_cubic = True
            hairMaterial.use_transparency = True
            hairMaterial.alpha = 0
            hairMaterial.use_transparent_shadows = True
#strand
            hairMaterial.strand.use_blender_units = True
            hairMaterial.strand.root_size = 0.00030
            hairMaterial.strand.tip_size = 0.00010
            hairMaterial.strand.size_min = 0.7
            hairMaterial.strand.width_fade = 0.1
            hairMaterial.strand.shape = 0.061
            hairMaterial.strand.blend_distance = 0.001


# add texture
            hairTex = bpy.data.textures.new("LongRedStraightHairTex", type='BLEND')
            hairTex.use_preview_alpha = True
            hairTex.use_color_ramp = True
            ramp = hairTex.color_ramp
            rampElements = ramp.elements
            rampElements[0].position = 0
            rampElements[0].color = [0.114,0.05613,0.004025,0.38]
            rampElements[1].position = 1
            rampElements[1].color = [0.267,0.155,0.02687,0]
            rampElement1 = rampElements.new(0.111)
            rampElement1.color = [0.281,0.168,0.03157,0.65]
            rampElement2 = rampElements.new(0.366)
            rampElement2.color = [0.288,0.135,0.006242,0.87]
            rampElement3 = rampElements.new(0.608)
            rampElement3.color = [0.247,0.113,0.006472,0.8]
            rampElement4 = rampElements.new(0.828)
            rampElement4.color = [0.253,0.09919,0.01242,0.64]

# add texture to material
            MTex = hairMaterial.texture_slots.add()
            MTex.texture = hairTex
            MTex.texture_coords = "STRAND"
            MTex.use_map_alpha = True



###############Create Particles##################
# Add new particle system

            NumberOfMaterials = 0
            for i in ob.data.materials:
                NumberOfMaterials +=1


            bpy.ops.object.particle_system_add()
#Particle settings setting it up!
            hairParticles = bpy.context.object.particle_systems.active
            hairParticles.name = "LongRedStraightHairPar"
            hairParticles.settings.type = "HAIR"
            hairParticles.settings.use_advanced_hair = True
            hairParticles.settings.count = 500
            hairParticles.settings.normal_factor = 0.05
            hairParticles.settings.factor_random = 0.001
            hairParticles.settings.use_dynamic_rotation = True

            hairParticles.settings.material = NumberOfMaterials

            hairParticles.settings.use_strand_primitive = True
            hairParticles.settings.use_hair_bspline = True
            hairParticles.settings.render_step = 5
            hairParticles.settings.length_random = 0.5
            hairParticles.settings.draw_step = 5
# children
            hairParticles.settings.child_type = "INTERPOLATED"
            hairParticles.settings.create_long_hair_children = True
            hairParticles.settings.clump_factor = 0.55
            hairParticles.settings.roughness_endpoint = 0.005
            hairParticles.settings.roughness_end_shape = 5
            hairParticles.settings.roughness_2 = 0.003
            hairParticles.settings.roughness_2_size = 0.230


######################################################################
########################Long Brown Curl Hair##########################
        if scene.hair_type == '1':
###############Create New Material##################
# add new material
            hairMaterial = bpy.data.materials.new('LongBrownCurlHairMat')
            ob.data.materials.append(hairMaterial)

#Material settings
            hairMaterial.preview_render_type = "HAIR"
            hairMaterial.diffuse_color = (0.662, 0.518, 0.458)
            hairMaterial.specular_color = (0.351, 0.249, 0.230)
            hairMaterial.specular_intensity = 0.3
            hairMaterial.specular_hardness = 100
            hairMaterial.use_specular_ramp = True

            ramp = hairMaterial.specular_ramp
            rampElements = ramp.elements
            rampElements[0].position = 0
            rampElements[0].color = [0.0356,0.0152,0.009134,0]
            rampElements[1].position = 1
            rampElements[1].color = [0.352,0.250,0.231,1]
            rampElement1 = rampElements.new(0.255)
            rampElement1.color = [0.214,0.08244,0.0578,0.31]
            rampElement2 = rampElements.new(0.594)
            rampElement2.color = [0.296,0.143,0.0861,0.72]

            hairMaterial.ambient = 0
            hairMaterial.use_cubic = True
            hairMaterial.use_transparency = True
            hairMaterial.alpha = 0
            hairMaterial.use_transparent_shadows = True
#strand
            hairMaterial.strand.use_blender_units = True
            hairMaterial.strand.root_size = 0.00030
            hairMaterial.strand.tip_size = 0.00015
            hairMaterial.strand.size_min = 0.450
            hairMaterial.strand.width_fade = 0.1
            hairMaterial.strand.shape = 0.02
            hairMaterial.strand.blend_distance = 0.001


# add texture
            hairTex = bpy.data.textures.new("HairTex", type='BLEND')
            hairTex.name = "LongBrownCurlHairTex"
            hairTex.use_preview_alpha = True
            hairTex.use_color_ramp = True
            ramp = hairTex.color_ramp
            rampElements = ramp.elements
            rampElements[0].position = 0
            rampElements[0].color = [0.009721,0.006049,0.003677,0.38]
            rampElements[1].position = 1
            rampElements[1].color = [0.04231,0.02029,0.01444,0.16]
            rampElement1 = rampElements.new(0.111)
            rampElement1.color = [0.01467,0.005307,0.00316,0.65]
            rampElement2 = rampElements.new(0.366)
            rampElement2.color = [0.0272,0.01364,0.01013,0.87]
            rampElement3 = rampElements.new(0.608)
            rampElement3.color = [0.04445,0.02294,0.01729,0.8]
            rampElement4 = rampElements.new(0.828)
            rampElement4.color = [0.04092,0.0185,0.01161,0.64]

# add texture to material
            MTex = hairMaterial.texture_slots.add()
            MTex.texture = hairTex
            MTex.texture_coords = "STRAND"
            MTex.use_map_alpha = True


###############Create Particles##################
# Add new particle system

            NumberOfMaterials = 0
            for i in ob.data.materials:
                NumberOfMaterials +=1


            bpy.ops.object.particle_system_add()
#Particle settings setting it up!
            hairParticles = bpy.context.object.particle_systems.active
            hairParticles.name = "LongBrownCurlHairPar"
            hairParticles.settings.type = "HAIR"
            hairParticles.settings.use_advanced_hair = True
            hairParticles.settings.count = 500
            hairParticles.settings.normal_factor = 0.05
            hairParticles.settings.factor_random = 0.001
            hairParticles.settings.use_dynamic_rotation = True

            hairParticles.settings.material = NumberOfMaterials

            hairParticles.settings.use_strand_primitive = True
            hairParticles.settings.use_hair_bspline = True
            hairParticles.settings.render_step = 7
            hairParticles.settings.length_random = 0.5
            hairParticles.settings.draw_step = 5
# children
            hairParticles.settings.child_type = "INTERPOLATED"
            hairParticles.settings.create_long_hair_children = True
            hairParticles.settings.clump_factor = 0.523
            hairParticles.settings.clump_shape = 0.383
            hairParticles.settings.roughness_endpoint = 0.002
            hairParticles.settings.roughness_end_shape = 5
            hairParticles.settings.roughness_2 = 0.003
            hairParticles.settings.roughness_2_size = 2

            hairParticles.settings.kink = "CURL"
            hairParticles.settings.kink_amplitude = 0.007597
            hairParticles.settings.kink_frequency = 6
            hairParticles.settings.kink_shape = 0.4
            hairParticles.settings.kink_flat = 0.8


######################################################################
########################Short Dark Hair##########################
        elif scene.hair_type == '2':
###############Create New Material##################
# add new material
            hairMaterial = bpy.data.materials.new('ShortDarkHairMat')
            ob.data.materials.append(hairMaterial)

#Material settings
            hairMaterial.preview_render_type = "HAIR"
            hairMaterial.diffuse_color = (0.560, 0.536, 0.506)
            hairMaterial.specular_color = (0.196, 0.177, 0.162)
            hairMaterial.specular_intensity = 0.5
            hairMaterial.specular_hardness = 100
            hairMaterial.ambient = 0
            hairMaterial.use_cubic = True
            hairMaterial.use_transparency = True
            hairMaterial.alpha = 0
            hairMaterial.use_transparent_shadows = True
#strand
            hairMaterial.strand.use_blender_units = True
            hairMaterial.strand.root_size = 0.0002
            hairMaterial.strand.tip_size = 0.0001
            hairMaterial.strand.size_min = 0.3
            hairMaterial.strand.width_fade = 0.1
            hairMaterial.strand.shape = 0
            hairMaterial.strand.blend_distance = 0.001

# add texture
            hairTex = bpy.data.textures.new("ShortDarkHair", type='BLEND')
            hairTex.use_preview_alpha = True
            hairTex.use_color_ramp = True
            ramp = hairTex.color_ramp
            rampElements = ramp.elements
            rampElements[0].position = 0
            rampElements[0].color = [0.004025,0.002732,0.002428,0.38]
            rampElements[1].position = 1
            rampElements[1].color = [0.141,0.122,0.107,0.2]
            rampElement1 = rampElements.new(0.202)
            rampElement1.color = [0.01885,0.0177,0.01827,0.65]
            rampElement2 = rampElements.new(0.499)
            rampElement2.color = [0.114,0.109,0.09822,0.87]
            rampElement3 = rampElements.new(0.828)
            rampElement3.color = [0.141,0.127,0.117,0.64]

# add texture to material
            MTex = hairMaterial.texture_slots.add()
            MTex.texture = hairTex
            MTex.texture_coords = "STRAND"
            MTex.use_map_alpha = True


###############Create Particles##################
# Add new particle system

            NumberOfMaterials = 0
            for i in ob.data.materials:
                NumberOfMaterials +=1


            bpy.ops.object.particle_system_add()
#Particle settings setting it up!
            hairParticles = bpy.context.object.particle_systems.active
            hairParticles.name = "ShortDarkHair"
            hairParticles.settings.type = "HAIR"
            hairParticles.settings.use_advanced_hair = True
            hairParticles.settings.hair_step = 2
            hairParticles.settings.count = 450
            hairParticles.settings.normal_factor = 0.007
            hairParticles.settings.factor_random = 0.001
            hairParticles.settings.use_dynamic_rotation = True

            hairParticles.settings.material = NumberOfMaterials

            hairParticles.settings.use_strand_primitive = True
            hairParticles.settings.use_hair_bspline = True
            hairParticles.settings.render_step = 3
            hairParticles.settings.length_random = 0.3
            hairParticles.settings.draw_step = 3
# children
            hairParticles.settings.child_type = "INTERPOLATED"
            hairParticles.settings.rendered_child_count = 200
            hairParticles.settings.virtual_parents = 1
            hairParticles.settings.clump_factor = 0.425
            hairParticles.settings.clump_shape = 0.1
            hairParticles.settings.roughness_endpoint = 0.003
            hairParticles.settings.roughness_end_shape = 5



        return {'FINISHED'}
####
######## FUR LAB ########
####

class FurLabPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_label = "Fur Lab"
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}
    bl_category = "Create"

    def draw(self, context):
        active_obj = bpy.context.active_object
        active_scn = bpy.context.scene.name
        layout = self.layout
        col = layout.column(align=True)

        WhatToDo = getActionToDo(active_obj)


        if WhatToDo == "GENERATE":
            col.operator("fur.generate_fur", text="Create Fur")

            col.prop(context.scene, "fur_type")
        else:
            col.label(text="Select mesh object")

        if active_scn == "TestFurScene":
            col.operator("hair.switch_back", text="Switch back to scene")
        else:
            col.operator("fur.test_scene", text="Create Test Scene")

# TO DO
"""
class saveSelection(bpy.types.Operator):
    bl_idname = "save.selection"
    bl_label = "Save Selection"
    bl_description = "Save selected particles"
    bl_register = True
    bl_undo = True

    def execute(self, context):

        return {'FINISHED'}
"""
class testScene5(bpy.types.Operator):
    bl_idname = "fur.switch_back"
    bl_label = "Switch back to scene"
    bl_description = "If you want keep this scene, switch scene in info window"
    bl_register = True
    bl_undo = True

    def execute(self, context):
        scene = bpy.context.scene
        bpy.data.scenes.remove(scene)

        return {'FINISHED'}


class testScene6(bpy.types.Operator):
    bl_idname = "fur.test_scene"
    bl_label = "Create test scene"
    bl_description = "You can switch scene in info panel"
    bl_register = True
    bl_undo = True

    def execute(self, context):
# add new scene
        bpy.ops.scene.new(type="NEW")
        scene = bpy.context.scene
        scene.name = "TestFurScene"
# render settings
        render = scene.render
        render.resolution_x = 1920
        render.resolution_y = 1080
        render.resolution_percentage = 50
# add new world
        world = bpy.data.worlds.new("FurWorld")
        scene.world = world
        world.use_sky_blend = True
        world.use_sky_paper = True
        world.horizon_color = (0.004393,0.02121,0.050)
        world.zenith_color = (0.03335,0.227,0.359)

# add text
        bpy.ops.object.text_add(location=(-0.292,0,-0.152), rotation =(1.571,0,0))
        text = bpy.context.active_object
        text.scale = (0.05,0.05,0.05)
        text.data.body = "Fur Lab"

# add material to text
        textMaterial = bpy.data.materials.new('textMaterial')
        text.data.materials.append(textMaterial)
        textMaterial.use_shadeless = True

# add camera
        bpy.ops.object.camera_add(location = (0,-1,0),rotation = (1.571,0,0))
        cam = bpy.context.active_object.data
        cam.lens = 50
        cam.draw_size = 0.1

# add spot lamp
        bpy.ops.object.lamp_add(type="SPOT", location = (-0.7,-0.5,0.3), rotation =(1.223,0,-0.960))
        lamp1 = bpy.context.active_object.data
        lamp1.name = "Key Light"
        lamp1.energy = 1.5
        lamp1.distance = 1.5
        lamp1.shadow_buffer_soft = 5
        lamp1.shadow_buffer_size = 8192
        lamp1.shadow_buffer_clip_end = 1.5
        lamp1.spot_blend = 0.5

# add spot lamp2
        bpy.ops.object.lamp_add(type="SPOT", location = (0.7,-0.6,0.1), rotation =(1.571,0,0.785))
        lamp2 = bpy.context.active_object.data
        lamp2.name = "Fill Light"
        lamp2.color = (0.874,0.874,1)
        lamp2.energy = 0.5
        lamp2.distance = 1.5
        lamp2.shadow_buffer_soft = 5
        lamp2.shadow_buffer_size = 4096
        lamp2.shadow_buffer_clip_end = 1.5
        lamp2.spot_blend = 0.5

# light Rim
        """
        # add spot lamp3
        bpy.ops.object.lamp_add(type="SPOT", location = (0.191,0.714,0.689), rotation =(0.891,0,2.884))
        lamp3 = bpy.context.active_object.data
        lamp3.name = "Rim Light"
        lamp3.color = (0.194,0.477,1)
        lamp3.energy = 3
        lamp3.distance = 1.5
        lamp3.shadow_buffer_soft = 5
        lamp3.shadow_buffer_size = 4096
        lamp3.shadow_buffer_clip_end = 1.5
        lamp3.spot_blend = 0.5
        """
# add sphere
        bpy.ops.mesh.primitive_uv_sphere_add(size=0.1)
        bpy.ops.object.shade_smooth()
        return {'FINISHED'}


class GenerateFur(bpy.types.Operator):
    bl_idname = "fur.generate_fur"
    bl_label = "Generate Fur"
    bl_description = "Create a Fur"
    bl_register = True
    bl_undo = True

    def execute(self, context):
# Make variable that is the current .blend file main data blocks
        blend_data = context.blend_data
        ob = bpy.context.active_object
        scene = context.scene

######################################################################
########################Short Fur########################
        if scene.fur_type == '0':

###############Create New Material##################
# add new material
            furMaterial = bpy.data.materials.new('Fur 1')
            ob.data.materials.append(furMaterial)

#Material settings
            furMaterial.preview_render_type = "HAIR"
            furMaterial.diffuse_color = (0.287, 0.216, 0.04667)
            furMaterial.specular_color = (0.604, 0.465, 0.136)
            furMaterial.specular_intensity = 0.3
            furMaterial.ambient = 0
            furMaterial.use_cubic = True
            furMaterial.use_transparency = True
            furMaterial.alpha = 0
            furMaterial.use_transparent_shadows = True
#strand
            furMaterial.strand.use_blender_units = True
            furMaterial.strand.root_size = 0.00030
            furMaterial.strand.tip_size = 0.00010
            furMaterial.strand.size_min = 0.7
            furMaterial.strand.width_fade = 0.1
            furMaterial.strand.shape = 0.061
            furMaterial.strand.blend_distance = 0.001


# add texture
            furTex = bpy.data.textures.new("Fur1Tex", type='BLEND')
            furTex.use_preview_alpha = True
            furTex.use_color_ramp = True
            ramp = furTex.color_ramp
            rampElements = ramp.elements
            rampElements[0].position = 0
            rampElements[0].color = [0.114,0.05613,0.004025,0.38]
            rampElements[1].position = 1
            rampElements[1].color = [0.267,0.155,0.02687,0]
            rampElement1 = rampElements.new(0.111)
            rampElement1.color = [0.281,0.168,0.03157,0.65]
            rampElement2 = rampElements.new(0.366)
            rampElement2.color = [0.288,0.135,0.006242,0.87]
            rampElement3 = rampElements.new(0.608)
            rampElement3.color = [0.247,0.113,0.006472,0.8]
            rampElement4 = rampElements.new(0.828)
            rampElement4.color = [0.253,0.09919,0.01242,0.64]

# add texture to material
            MTex = furMaterial.texture_slots.add()
            MTex.texture = furTex
            MTex.texture_coords = "STRAND"
            MTex.use_map_alpha = True


###############Create Particles##################
# Add new particle system

            NumberOfMaterials = 0
            for i in ob.data.materials:
                NumberOfMaterials +=1


            bpy.ops.object.particle_system_add()
#Particle settings setting it up!
            furParticles = bpy.context.object.particle_systems.active
            furParticles.name = "Fur1Par"
            furParticles.settings.type = "HAIR"
            furParticles.settings.use_advanced_hair = True
            furParticles.settings.count = 500
            furParticles.settings.normal_factor = 0.05
            furParticles.settings.factor_random = 0.001
            furParticles.settings.use_dynamic_rotation = True

            furParticles.settings.material = NumberOfMaterials

            furParticles.settings.use_strand_primitive = True
            furParticles.settings.use_hair_bspline = True
            furParticles.settings.render_step = 5
            furParticles.settings.length_random = 0.5
            furParticles.settings.draw_step = 5
# children
            furParticles.settings.child_type = "INTERPOLATED"
            furParticles.settings.child_length = 0.134
            furParticles.settings.create_long_hair_children = True
            furParticles.settings.clump_factor = 0.55
            furParticles.settings.roughness_endpoint = 0.005
            furParticles.settings.roughness_end_shape = 5
            furParticles.settings.roughness_2 = 0.003
            furParticles.settings.roughness_2_size = 0.230


######################################################################
########################Dalmation Fur##########################
        if scene.fur_type == '1':
###############Create New Material##################
# add new material
            furMaterial = bpy.data.materials.new('Fur2Mat')
            ob.data.materials.append(furMaterial)

#Material settings
            furMaterial.preview_render_type = "HAIR"
            furMaterial.diffuse_color = (0.300, 0.280, 0.280)
            furMaterial.specular_color = (1.0, 1.0, 1.0)
            furMaterial.specular_intensity = 0.500
            furMaterial.specular_hardness = 50

            furMaterial.ambient = 0
            furMaterial.use_cubic = True
            furMaterial.use_transparency = True
            furMaterial.alpha = 0
            furMaterial.use_transparent_shadows = True
#strand
            furMaterial.strand.use_blender_units = True
            furMaterial.strand.root_size = 0.00030
            furMaterial.strand.tip_size = 0.00010
            furMaterial.strand.size_min = 0.7
            furMaterial.strand.width_fade = 0.1
            furMaterial.strand.shape = 0.061
            furMaterial.strand.blend_distance = 0.001


# add texture
            furTex = bpy.data.textures.new("Fur2Tex", type='BLEND')
            furTex.name = "Fur2"
            furTex.use_preview_alpha = True
            furTex.use_color_ramp = True
            ramp = furTex.color_ramp
            rampElements = ramp.elements
            rampElements[0].position = 0
            rampElements[0].color = [1.0,1.0,1.0,1.0]
            rampElements[1].position = 1
            rampElements[1].color = [1.0,1.0,1.0,0.0]
            rampElement1 = rampElements.new(0.116)
            rampElement1.color = [1.0,1.0,1.0,1.0]


# add texture to material
            MTex = furMaterial.texture_slots.add()
            MTex.texture = furTex
            MTex.texture_coords = "STRAND"
            MTex.use_map_alpha = True

# add texture 2
            furTex = bpy.data.textures.new("Fur2bTex", type='CLOUDS')
            furTex.name = "Fur2b"
            furTex.use_preview_alpha = False
            furTex.cloud_type = "COLOR"
            furTex.noise_type = "HARD_NOISE"
            furTex.noise_scale = 0.06410
            furTex.use_color_ramp = True
            ramp = furTex.color_ramp
            rampElements = ramp.elements
            rampElements[0].position = 0
            rampElements[0].color = [1.0,1.0,1.0, 1.0]
            rampElements[1].position = 1
            rampElements[1].color = [0.0,0.0,0.0,1.0]
            rampElement1 = rampElements.new(0.317)
            rampElement1.color = [1.0,1.0,1.0,1.0]
            rampElement2 = rampElements.new(0.347)
            rampElement2.color = [0.0,0.0,0.0,1.0]

# add texture 2 to material
            MTex = furMaterial.texture_slots.add()
            MTex.texture = furTex
            MTex.texture_coords = "GLOBAL"
            MTex.use_map_alpha = True

###############Create Particles##################
# Add new particle system

            NumberOfMaterials = 0
            for i in ob.data.materials:
                NumberOfMaterials +=1


            bpy.ops.object.particle_system_add()
#Particle settings setting it up!
            furParticles = bpy.context.object.particle_systems.active
            furParticles.name = "Fur2Par"
            furParticles.settings.type = "HAIR"
            furParticles.settings.use_advanced_hair = True
            furParticles.settings.count = 500
            furParticles.settings.normal_factor = 0.05
            furParticles.settings.factor_random = 0.001
            furParticles.settings.use_dynamic_rotation = True

            furParticles.settings.material = NumberOfMaterials

            furParticles.settings.use_strand_primitive = True
            furParticles.settings.use_hair_bspline = True
            furParticles.settings.render_step = 5
            furParticles.settings.length_random = 0.5
            furParticles.settings.draw_step = 5
# children
            furParticles.settings.child_type = "INTERPOLATED"
            furParticles.settings.child_length = 0.07227
            furParticles.settings.create_long_hair_children = True
            furParticles.settings.clump_factor = 0.55
            furParticles.settings.roughness_endpoint = 0.005
            furParticles.settings.roughness_end_shape = 5
            furParticles.settings.roughness_2 = 0.003
            furParticles.settings.roughness_2_size = 0.230

######################################################################
########################Spotted_fur##########################
        elif scene.fur_type == '2':

###############Create New Material##################
# add new material
            furMaterial = bpy.data.materials.new('Fur3Mat')
            ob.data.materials.append(furMaterial)

#Material settings
            furMaterial.preview_render_type = "HAIR"
            furMaterial.diffuse_color = (0.300, 0.280, 0.280)
            furMaterial.specular_color = (1.0, 1.0, 1.0)
            furMaterial.specular_intensity = 0.500
            furMaterial.specular_hardness = 50
            furMaterial.use_specular_ramp = True

            ramp = furMaterial.specular_ramp
            rampElements = ramp.elements
            rampElements[0].position = 0
            rampElements[0].color = [0.0356,0.0152,0.009134,0]
            rampElements[1].position = 1
            rampElements[1].color = [0.352,0.250,0.231,1]
            rampElement1 = rampElements.new(0.255)
            rampElement1.color = [0.214,0.08244,0.0578,0.31]
            rampElement2 = rampElements.new(0.594)
            rampElement2.color = [0.296,0.143,0.0861,0.72]

            furMaterial.ambient = 0
            furMaterial.use_cubic = True
            furMaterial.use_transparency = True
            furMaterial.alpha = 0
            furMaterial.use_transparent_shadows = True
#strand
            furMaterial.strand.use_blender_units = True
            furMaterial.strand.root_size = 0.00030
            furMaterial.strand.tip_size = 0.00015
            furMaterial.strand.size_min = 0.450
            furMaterial.strand.width_fade = 0.1
            furMaterial.strand.shape = 0.02
            furMaterial.strand.blend_distance = 0.001


# add texture
            furTex = bpy.data.textures.new("Fur3Tex", type='BLEND')
            furTex.name = "Fur3"
            furTex.use_preview_alpha = True
            furTex.use_color_ramp = True
            ramp = furTex.color_ramp
            rampElements = ramp.elements
            rampElements[0].position = 0
            rampElements[0].color = [0.009721,0.006049,0.003677,0.38]
            rampElements[1].position = 1
            rampElements[1].color = [0.04231,0.02029,0.01444,0.16]
            rampElement1 = rampElements.new(0.111)
            rampElement1.color = [0.01467,0.005307,0.00316,0.65]
            rampElement2 = rampElements.new(0.366)
            rampElement2.color = [0.0272,0.01364,0.01013,0.87]
            rampElement3 = rampElements.new(0.608)
            rampElement3.color = [0.04445,0.02294,0.01729,0.8]
            rampElement4 = rampElements.new(0.828)
            rampElement4.color = [0.04092,0.0185,0.01161,0.64]

# add texture to material
            MTex = furMaterial.texture_slots.add()
            MTex.texture = furTex
            MTex.texture_coords = "STRAND"
            MTex.use_map_alpha = True

# add texture 2
            furTex = bpy.data.textures.new("Fur3bTex", type='CLOUDS')
            furTex.name = "Fur3b"
            furTex.use_preview_alpha = True
            furTex.cloud_type = "COLOR"
            furTex.use_color_ramp = True
            ramp = furTex.color_ramp
            rampElements = ramp.elements
            rampElements[0].position = 0
            rampElements[0].color = [0.009721,0.006049,0.003677,0.38]
            rampElements[1].position = 1
            rampElements[1].color = [0.04231,0.02029,0.01444,0.16]
            rampElement1 = rampElements.new(0.111)
            rampElement1.color = [0.01467,0.005307,0.00316,0.65]
            rampElement2 = rampElements.new(0.366)
            rampElement2.color = [0.0272,0.01364,0.01013,0.87]
            rampElement3 = rampElements.new(0.608)
            rampElement3.color = [0.04445,0.02294,0.01729,0.8]
            rampElement4 = rampElements.new(0.828)
            rampElement4.color = [0.04092,0.0185,0.01161,0.64]

# add texture 2 to material
            MTex = furMaterial.texture_slots.add()
            MTex.texture = furTex
            MTex.texture_coords = "GLOBAL"
            MTex.use_map_alpha = False

###############Create Particles##################
# Add new particle system

            NumberOfMaterials = 0
            for i in ob.data.materials:
                NumberOfMaterials +=1


            bpy.ops.object.particle_system_add()
#Particle settings setting it up!
            furParticles = bpy.context.object.particle_systems.active
            furParticles.name = "Fur3Par"
            furParticles.settings.type = "HAIR"
            furParticles.settings.use_advanced_hair = True
            furParticles.settings.count = 500
            furParticles.settings.normal_factor = 0.05
            furParticles.settings.factor_random = 0.001
            furParticles.settings.use_dynamic_rotation = True

            furParticles.settings.material = NumberOfMaterials

            furParticles.settings.use_strand_primitive = True
            furParticles.settings.use_hair_bspline = True
            furParticles.settings.render_step = 5
            furParticles.settings.length_random = 0.5
            furParticles.settings.draw_step = 5
# children
            furParticles.settings.child_type = "INTERPOLATED"
            furParticles.settings.child_length = 0.134
            furParticles.settings.create_long_hair_children = True
            furParticles.settings.clump_factor = 0.55
            furParticles.settings.roughness_endpoint = 0.005
            furParticles.settings.roughness_end_shape = 5
            furParticles.settings.roughness_2 = 0.003
            furParticles.settings.roughness_2_size = 0.230

        return {'FINISHED'}
def register():
    bpy.utils.register_module(__name__)
    bpy.types.Scene.grass_type = EnumProperty(
        name="Type",
        description="Select the type of grass",
        items=[("0","Green Grass","Generate particle grass"),
               ("1","Grassy Field","Generate particle grass"),
               ("2","Clumpy Grass","Generate particle grass"),

              ],
        default='0')
    bpy.types.Scene.hair_type = EnumProperty(
        name="Type",
        description="Select the type of hair",
        items=[("0","Long Red Straight Hair","Generate particle Hair"),
               ("1","Long Brown Curl Hair","Generate particle Hair"),
               ("2","Short Dark Hair","Generate particle Hair"),

              ],
        default='0')
    bpy.types.Scene.fur_type = EnumProperty(
        name="Type",
        description="Select the type of fur",
        items=[("0","Short Fur","Generate particle Fur"),
               ("1","Dalmation","Generate particle Fur"),
               ("2","Fur3","Generate particle Fur"),

              ],
        default='0')

def unregister():
    bpy.utils.unregister_module(__name__)
    del bpy.types.Scene.hair_type

if __name__ == "__main__":
    register()



