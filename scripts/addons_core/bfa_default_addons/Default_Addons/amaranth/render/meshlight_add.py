# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from mathutils import Vector
from amaranth.utils import cycles_exists


# FEATURE: Add Meshlight
class AMTH_OBJECT_OT_meshlight_add(bpy.types.Operator):

    """Add a light emitting mesh"""
    bl_idname = "object.meshlight_add"
    bl_label = "Add Meshlight"
    bl_options = {'REGISTER', 'UNDO'}

    single_sided: bpy.props.BoolProperty(
        name="Single Sided",
        default=True,
        description="Only emit light on one side",
        )

    is_constant: bpy.props.BoolProperty(
        name="Constant Falloff",
        default=False,
        description="Energy is constant (i.e. the Sun), "
                    "independent of how close to the source you are",
        )

    visible: bpy.props.BoolProperty(
        name="Visible on Camera",
        default=False,
        description="Whether to show the meshlight source on Camera",
        )

    size: bpy.props.FloatProperty(
        name="Size",
        description="Meshlight size. Lower is sharper shadows, higher is softer",
        min=0.01, max=100.0,
        default=1.0,
        )

    strength: bpy.props.FloatProperty(
        name="Strength",
        min=0.01, max=100000.0,
        default=1.5,
        step=0.25,
        )

    temperature: bpy.props.FloatProperty(
        name="Temperature",
        min=800, max=12000.0,
        default=5500.0,
        step=100.0,
        description="Temperature in Kelvin. Lower is warmer, higher is colder",
        )

    rotation: bpy.props.FloatVectorProperty(
        name="Rotation",
        subtype='EULER',
        )

    def execute(self, context):
        scene = context.scene
        # exists = False
        number = 1

        for obs in bpy.data.objects:
            if obs.name.startswith("light_meshlight"):
                number += 1

        meshlight_name = 'light_meshlight_%.2d' % number

        bpy.ops.mesh.primitive_grid_add(
            x_subdivisions=4, y_subdivisions=4,
            rotation=self.rotation, size=self.size)

        bpy.context.object.name = meshlight_name
        meshlight = scene.objects[meshlight_name]
        meshlight.show_wire = True
        meshlight.show_all_edges = True

        material = bpy.data.materials.get(meshlight_name)

        if not material:
            material = bpy.data.materials.new(meshlight_name)

        bpy.ops.object.material_slot_add()
        meshlight.active_material = material

        material.use_nodes = True
        material.diffuse_color = (1, 0.5, 0, 1)
        nodes = material.node_tree.nodes
        links = material.node_tree.links

        # clear default nodes to start nice fresh
        for no in nodes:
            nodes.remove(no)

        if self.single_sided:
            geometry = nodes.new(type="ShaderNodeNewGeometry")

            transparency = nodes.new(type="ShaderNodeBsdfTransparent")
            transparency.inputs[0].default_value = (1, 1, 1, 1)
            transparency.location = geometry.location
            transparency.location += Vector((0.0, -55.0))

            emission = nodes.new(type="ShaderNodeEmission")
            emission.inputs['Strength'].default_value = self.strength
            emission.location = transparency.location
            emission.location += Vector((0.0, -80.0))

            blackbody = nodes.new(type="ShaderNodeBlackbody")
            blackbody.inputs['Temperature'].default_value = self.temperature
            blackbody.location = emission.location
            blackbody.location += Vector((-180.0, 0.0))
            blackbody.label = 'Temperature'

            mix = nodes.new(type="ShaderNodeMixShader")
            mix.location = geometry.location
            mix.location += Vector((180.0, 0.0))
            mix.inputs[2].show_expanded = True

            output = nodes.new(type="ShaderNodeOutputMaterial")
            output.inputs[1].hide = True
            output.inputs[2].hide = True
            output.location = mix.location
            output.location += Vector((180.0, 0.0))

            # Make links
            links.new(geometry.outputs['Backfacing'], mix.inputs[0])
            links.new(transparency.outputs['BSDF'], mix.inputs[1])
            links.new(emission.outputs['Emission'], mix.inputs[2])
            links.new(blackbody.outputs['Color'], emission.inputs['Color'])
            links.new(mix.outputs['Shader'], output.inputs['Surface'])

            for sockets in geometry.outputs:
                sockets.hide = True
        else:
            emission = nodes.new(type="ShaderNodeEmission")
            emission.inputs['Strength'].default_value = self.strength

            blackbody = nodes.new(type="ShaderNodeBlackbody")
            blackbody.inputs['Temperature'].default_value = self.temperature
            blackbody.location = emission.location
            blackbody.location += Vector((-180.0, 0.0))
            blackbody.label = 'Temperature'

            output = nodes.new(type="ShaderNodeOutputMaterial")
            output.inputs[1].hide = True
            output.inputs[2].hide = True
            output.location = emission.location
            output.location += Vector((180.0, 0.0))

            links.new(blackbody.outputs['Color'], emission.inputs['Color'])
            links.new(emission.outputs['Emission'], output.inputs['Surface'])

        if self.is_constant:
            falloff = nodes.new(type="ShaderNodeLightFalloff")
            falloff.inputs['Strength'].default_value = self.strength
            falloff.location = emission.location
            falloff.location += Vector((-180.0, -80.0))

            links.new(falloff.outputs['Constant'], emission.inputs['Strength'])

            for sockets in falloff.outputs:
                sockets.hide = True

        # so it shows slider on properties editor
        for sockets in emission.inputs:
            sockets.show_expanded = True

        material.cycles.sample_as_light = True
        meshlight.visible_shadow = False
        meshlight.visible_camera = self.visible

        return {'FINISHED'}


def ui_menu_lamps_add(self, context):
    if cycles_exists() and context.scene.render.engine == 'CYCLES':
        self.layout.separator()
        self.layout.operator(
            AMTH_OBJECT_OT_meshlight_add.bl_idname,
            icon="LIGHT_AREA", text="Meshlight")

# //FEATURE: Add Meshlight: Single Sided


def register():
    bpy.utils.register_class(AMTH_OBJECT_OT_meshlight_add)
    bpy.types.VIEW3D_MT_light_add.append(ui_menu_lamps_add)


def unregister():
    bpy.utils.unregister_class(AMTH_OBJECT_OT_meshlight_add)
    bpy.types.VIEW3D_MT_light_add.remove(ui_menu_lamps_add)
