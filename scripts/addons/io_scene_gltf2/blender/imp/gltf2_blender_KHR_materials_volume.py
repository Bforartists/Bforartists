# SPDX-License-Identifier: Apache-2.0
# Copyright 2018-2021 The glTF-Blender-IO authors.

from ...io.com.gltf2_io import TextureInfo
from .gltf2_blender_texture import texture

def volume(mh, location, volume_socket, thickness_socket):
    # implementation based on https://github.com/KhronosGroup/glTF-Blender-IO/issues/1454#issuecomment-928319444
    try:
        ext = mh.pymat.extensions['KHR_materials_volume']
    except Exception:
        return

    # Attenuation Color
    attenuationColor = \
            mh.pymat.extensions['KHR_materials_volume'] \
            .get('attenuationColor')
    # glTF is color3, Blender adds alpha
    if attenuationColor is None:
        attenuationColor = [1.0, 1.0, 1.0, 1.0]
    else:
        attenuationColor.extend([1.0])
    volume_socket.node.inputs[0].default_value = attenuationColor

    # Attenuation Distance / Density
    attenuationDistance = mh.pymat.extensions['KHR_materials_volume'].get('attenuationDistance')
    if attenuationDistance is None:
        density = 0
    else:
        density = 1.0 / attenuationDistance
    volume_socket.node.inputs[1].default_value = density

    # thicknessFactor / thicknessTexture
    x, y = location
    try:
        ext = mh.pymat.extensions['KHR_materials_volume']
    except Exception:
        return
    thickness_factor = ext.get('thicknessFactor', 0)
    tex_info = ext.get('thicknessTexture')
    if tex_info is not None:
        tex_info = TextureInfo.from_dict(tex_info)

    if thickness_socket is None:
        return

    if tex_info is None:
        thickness_socket.default_value = thickness_factor
        return

    # Mix thickness factor
    if thickness_factor != 1:
        node = mh.node_tree.nodes.new('ShaderNodeMath')
        node.label = 'Thickness Factor'
        node.location = x - 140, y
        node.operation = 'MULTIPLY'
        # Outputs
        mh.node_tree.links.new(thickness_socket, node.outputs[0])
        # Inputs
        thickness_socket = node.inputs[0]
        node.inputs[1].default_value = thickness_factor

        x -= 200

    # Separate RGB
    node = mh.node_tree.nodes.new('ShaderNodeSeparateColor')
    node.location = x - 150, y - 75
    # Outputs
    mh.node_tree.links.new(thickness_socket, node.outputs['Green'])
    # Inputs
    thickness_socket = node.inputs[0]

    x -= 200

    texture(
        mh,
        tex_info=tex_info,
        label='THICKNESS',
        location=(x, y),
        is_data=True,
        color_socket=thickness_socket,
    )
