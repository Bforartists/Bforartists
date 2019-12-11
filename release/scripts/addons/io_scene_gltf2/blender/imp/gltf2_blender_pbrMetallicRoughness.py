# Copyright 2018-2019 The glTF-Blender-IO authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import bpy
from .gltf2_blender_material_utils import make_texture_block
from ..com.gltf2_blender_conversion import texture_transform_gltf_to_blender


class BlenderPbr():
    """Blender Pbr."""
    def __new__(cls, *args, **kwargs):
        raise RuntimeError("%s should not be instantiated" % cls)

    def create(gltf, pypbr, mat_name, vertex_color):
        """Pbr creation."""
        engine = bpy.context.scene.render.engine
        if engine in ['CYCLES', 'BLENDER_EEVEE']:
            BlenderPbr.create_nodetree(gltf, pypbr, mat_name, vertex_color)

    def create_nodetree(gltf, pypbr, mat_name, vertex_color, nodetype='principled'):
        """Nodetree creation."""
        material = bpy.data.materials[mat_name]
        material.use_nodes = True
        node_tree = material.node_tree

        # If there is no diffuse texture, but only a color, wihtout
        # vertex_color, we set this color in viewport color
        if pypbr.color_type == gltf.SIMPLE and not vertex_color:
            # Manage some change in beta version on 20190129
            if len(material.diffuse_color) == 3:
                material.diffuse_color = pypbr.base_color_factor[:3]
            else:
                material.diffuse_color = pypbr.base_color_factor

        # delete all nodes except output
        for node in list(node_tree.nodes):
            if not node.type == 'OUTPUT_MATERIAL':
                node_tree.nodes.remove(node)

        output_node = node_tree.nodes[0]
        output_node.location = 1250, 0

        # create Main node
        if nodetype == "principled":
            main_node = node_tree.nodes.new('ShaderNodeBsdfPrincipled')
            main_node.location = 0, 0
        elif nodetype == "unlit":
            main_node = node_tree.nodes.new('ShaderNodeEmission')
            main_node.location = 750, -300

        if pypbr.color_type == gltf.SIMPLE:

            if not vertex_color:

                # change input values
                main_node.inputs[0].default_value = pypbr.base_color_factor
                if nodetype == "principled":
                    # TODO : currently set metallic & specular in same way
                    main_node.inputs[5].default_value = pypbr.metallic_factor
                    main_node.inputs[7].default_value = pypbr.roughness_factor

            else:
                # Create attribute node to get COLOR_0 data
                vertexcolor_node = node_tree.nodes.new('ShaderNodeVertexColor')
                vertexcolor_node.layer_name = 'Col'
                vertexcolor_node.location = -500, 0

                if nodetype == "principled":
                    # TODO : currently set metallic & specular in same way
                    main_node.inputs[5].default_value = pypbr.metallic_factor
                    main_node.inputs[7].default_value = pypbr.roughness_factor

                # links
                rgb_node = node_tree.nodes.new('ShaderNodeMixRGB')
                rgb_node.blend_type = 'MULTIPLY'
                rgb_node.inputs['Fac'].default_value = 1.0
                rgb_node.inputs['Color1'].default_value = pypbr.base_color_factor
                node_tree.links.new(rgb_node.inputs['Color2'], vertexcolor_node.outputs[0])
                node_tree.links.new(main_node.inputs[0], rgb_node.outputs[0])

        elif pypbr.color_type == gltf.TEXTURE_FACTOR:

            # TODO alpha ?
            if vertex_color:
                # TODO tree locations
                # Create attribute / separate / math nodes
                vertexcolor_node = node_tree.nodes.new('ShaderNodeVertexColor')
                vertexcolor_node.layer_name = 'Col'

                vc_mult_node = node_tree.nodes.new('ShaderNodeMixRGB')
                vc_mult_node.blend_type = 'MULTIPLY'
                vc_mult_node.inputs['Fac'].default_value = 1.0

            # create UV Map / Mapping / Texture nodes / separate & math and combine
            text_node = make_texture_block(
                gltf,
                node_tree,
                pypbr.base_color_texture,
                location=(-1000, 500),
                label='BASE COLOR',
                name='baseColorTexture',
            )

            mult_node = node_tree.nodes.new('ShaderNodeMixRGB')
            mult_node.blend_type = 'MULTIPLY'
            mult_node.inputs['Fac'].default_value = 1.0
            mult_node.inputs['Color2'].default_value = [
                                                        pypbr.base_color_factor[0],
                                                        pypbr.base_color_factor[1],
                                                        pypbr.base_color_factor[2],
                                                        pypbr.base_color_factor[3],
                                                        ]

            # Create links
            if vertex_color:
                node_tree.links.new(vc_mult_node.inputs[2], vertexcolor_node.outputs[0])
                node_tree.links.new(vc_mult_node.inputs[1], mult_node.outputs[0])
                node_tree.links.new(main_node.inputs[0], vc_mult_node.outputs[0])

            else:
                node_tree.links.new(main_node.inputs[0], mult_node.outputs[0])

            # Common for both mode (non vertex color / vertex color)
            node_tree.links.new(mult_node.inputs[1], text_node.outputs[0])

        elif pypbr.color_type == gltf.TEXTURE:

            # TODO alpha ?
            if vertex_color:
                # Create attribute / separate / math nodes
                vertexcolor_node = node_tree.nodes.new('ShaderNodeVertexColor')
                vertexcolor_node.layer_name = 'Col'
                vertexcolor_node.location = -2000, 250

                vc_mult_node = node_tree.nodes.new('ShaderNodeMixRGB')
                vc_mult_node.blend_type = 'MULTIPLY'
                vc_mult_node.inputs['Fac'].default_value = 1.0

            # create UV Map / Mapping / Texture nodes / separate & math and combine
            if vertex_color:
                location = -2000, 500
            else:
                location = -500, 500
            text_node = make_texture_block(
                gltf,
                node_tree,
                pypbr.base_color_texture,
                location=location,
                label='BASE COLOR',
                name='baseColorTexture',
            )

            # Create links
            if vertex_color:
                node_tree.links.new(vc_mult_node.inputs[2], vertexcolor_node.outputs[0])
                node_tree.links.new(vc_mult_node.inputs[1], text_node.outputs[0])
                node_tree.links.new(main_node.inputs[0], vc_mult_node.outputs[0])

            else:
                node_tree.links.new(main_node.inputs[0], text_node.outputs[0])

        if nodetype == 'principled':
            # Says metallic, but it means metallic & Roughness values
            if pypbr.metallic_type == gltf.SIMPLE:
                main_node.inputs[4].default_value = pypbr.metallic_factor
                main_node.inputs[7].default_value = pypbr.roughness_factor

            elif pypbr.metallic_type == gltf.TEXTURE:

                metallic_text = make_texture_block(
                    gltf,
                    node_tree,
                    pypbr.metallic_roughness_texture,
                    location=(-500, 0),
                    label='METALLIC ROUGHNESS',
                    name='metallicRoughnessTexture',
                    colorspace='NONE',
                )

                metallic_separate = node_tree.nodes.new('ShaderNodeSeparateRGB')
                metallic_separate.location = -250, 0

                # links
                node_tree.links.new(metallic_separate.inputs[0], metallic_text.outputs[0])
                node_tree.links.new(main_node.inputs[4], metallic_separate.outputs[2])  # metallic
                node_tree.links.new(main_node.inputs[7], metallic_separate.outputs[1])  # Roughness

            elif pypbr.metallic_type == gltf.TEXTURE_FACTOR:

                metallic_text = make_texture_block(
                    gltf,
                    node_tree,
                    pypbr.metallic_roughness_texture,
                    location=(-1000, 0),
                    label='METALLIC ROUGHNESS',
                    name='metallicRoughnessTexture',
                    colorspace='NONE',
                )

                metallic_separate = node_tree.nodes.new('ShaderNodeSeparateRGB')
                metallic_separate.location = -500, 0

                metallic_math = node_tree.nodes.new('ShaderNodeMath')
                metallic_math.operation = 'MULTIPLY'
                metallic_math.inputs[1].default_value = pypbr.metallic_factor
                metallic_math.location = -250, 100

                roughness_math = node_tree.nodes.new('ShaderNodeMath')
                roughness_math.operation = 'MULTIPLY'
                roughness_math.inputs[1].default_value = pypbr.roughness_factor
                roughness_math.location = -250, -100

                # links
                node_tree.links.new(metallic_separate.inputs[0], metallic_text.outputs[0])

                # metallic
                node_tree.links.new(metallic_math.inputs[0], metallic_separate.outputs[2])
                node_tree.links.new(main_node.inputs[4], metallic_math.outputs[0])

                # roughness
                node_tree.links.new(roughness_math.inputs[0], metallic_separate.outputs[1])
                node_tree.links.new(main_node.inputs[7], roughness_math.outputs[0])

        # link node to output
        if nodetype == 'principled':
            node_tree.links.new(output_node.inputs[0], main_node.outputs[0])
        elif nodetype == 'unlit':
            mix = node_tree.nodes.new('ShaderNodeMixShader')
            mix.location = 1000, 0
            path = node_tree.nodes.new('ShaderNodeLightPath')
            path.location = 500, 300
            if pypbr.color_type != gltf.SIMPLE:
                math = node_tree.nodes.new('ShaderNodeMath')
                math.location = 750, 200
                math.operation = 'MULTIPLY'

                # Set material alpha mode to blend
                # This is needed for Eevee
                material.blend_method = 'HASHED' # TODO check best result in eevee

            transparent = node_tree.nodes.new('ShaderNodeBsdfTransparent')
            transparent.location = 750, 0

            node_tree.links.new(output_node.inputs[0], mix.outputs[0])
            node_tree.links.new(mix.inputs[2], main_node.outputs[0])
            node_tree.links.new(mix.inputs[1], transparent.outputs[0])
            if pypbr.color_type != gltf.SIMPLE:
                node_tree.links.new(math.inputs[0], path.outputs[0])
                node_tree.links.new(math.inputs[1], text_node.outputs[1])
                node_tree.links.new(mix.inputs[0], math.outputs[0])
            else:
                node_tree.links.new(mix.inputs[0], path.outputs[0])

