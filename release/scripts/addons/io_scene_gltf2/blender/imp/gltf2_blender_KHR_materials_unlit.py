# SPDX-License-Identifier: Apache-2.0
# Copyright 2018-2021 The glTF-Blender-IO authors.

from .gltf2_blender_pbrMetallicRoughness import base_color, make_output_nodes


def unlit(mh):
    """Creates node tree for unlit materials."""
    # Emission node for the base color
    emission_node = mh.node_tree.nodes.new('ShaderNodeEmission')
    emission_node.location = 10, 126

    # Lightpath trick: makes Emission visible only to camera rays.
    # [Is Camera Ray] => [Mix] =>
    #   [Transparent] => [   ]
    #      [Emission] => [   ]
    lightpath_node = mh.node_tree.nodes.new('ShaderNodeLightPath')
    transparent_node = mh.node_tree.nodes.new('ShaderNodeBsdfTransparent')
    mix_node = mh.node_tree.nodes.new('ShaderNodeMixShader')
    lightpath_node.location = 10, 600
    transparent_node.location = 10, 240
    mix_node.location = 260, 320
    mh.node_tree.links.new(mix_node.inputs['Fac'], lightpath_node.outputs['Is Camera Ray'])
    mh.node_tree.links.new(mix_node.inputs[1], transparent_node.outputs[0])
    mh.node_tree.links.new(mix_node.inputs[2], emission_node.outputs[0])

    _emission_socket, alpha_socket = make_output_nodes(
        mh,
        location=(420, 280) if mh.is_opaque() else (150, 130),
        shader_socket=mix_node.outputs[0],
        make_emission_socket=False,
        make_alpha_socket=not mh.is_opaque(),
    )

    base_color(
        mh,
        location=(-200, 380),
        color_socket=emission_node.inputs['Color'],
        alpha_socket=alpha_socket,
    )
