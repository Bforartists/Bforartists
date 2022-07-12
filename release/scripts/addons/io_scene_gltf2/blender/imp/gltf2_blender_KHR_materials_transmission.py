# SPDX-License-Identifier: Apache-2.0
# Copyright 2018-2022 The glTF-Blender-IO authors.


from ...io.com.gltf2_io import TextureInfo, MaterialNormalTextureInfoClass
from .gltf2_blender_texture import texture


# [Texture] => [Separate R] => [Transmission Factor] =>
def transmission(mh, location, transmission_socket):
    x, y = location
    try:
        ext = mh.pymat.extensions['KHR_materials_transmission']
    except Exception:
        return
    transmission_factor = ext.get('transmissionFactor', 0)

    # Default value is 0, so no transmission
    if transmission_factor == 0:
        return

    tex_info = ext.get('transmissionTexture')
    if tex_info is not None:
        tex_info = TextureInfo.from_dict(tex_info)

    if transmission_socket is None:
        return

    if tex_info is None:
        transmission_socket.default_value = transmission_factor
        return

    # Mix transmission factor
    if transmission_factor != 1:
        node = mh.node_tree.nodes.new('ShaderNodeMath')
        node.label = 'Transmission Factor'
        node.location = x - 140, y
        node.operation = 'MULTIPLY'
        # Outputs
        mh.node_tree.links.new(transmission_socket, node.outputs[0])
        # Inputs
        transmission_socket = node.inputs[0]
        node.inputs[1].default_value = transmission_factor

        x -= 200

    # Separate RGB
    node = mh.node_tree.nodes.new('ShaderNodeSeparateColor')
    node.location = x - 150, y - 75
    # Outputs
    mh.node_tree.links.new(transmission_socket, node.outputs['Red'])
    # Inputs
    transmission_socket = node.inputs[0]

    x -= 200

    texture(
        mh,
        tex_info=tex_info,
        label='TRANSMISSION',
        location=(x, y),
        is_data=True,
        color_socket=transmission_socket,
    )
