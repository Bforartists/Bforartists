# SPDX-FileCopyrightText: 2018-2022 The glTF-Blender-IO authors
#
# SPDX-License-Identifier: Apache-2.0

from ...io.com.gltf2_io import TextureInfo
from .gltf2_blender_texture import texture

def sheen(  mh,
            location_sheenTint,
            location_sheenRoughness,
            sheen_socket,
            sheenTint_socket,
            sheenRoughness_socket
            ):

    x_sheenTint, y_sheenTint = location_sheenTint
    x_sheenRoughness, y_sheenRoughness = location_sheenRoughness

    try:
        ext = mh.pymat.extensions['KHR_materials_sheen']
    except Exception:
        return

    sheen_socket.default_value = 1.0
    sheenTintFactor = ext.get('sheenColorFactor', [0.0, 0.0, 0.0])
    tex_info_color = ext.get('sheenColorTexture')
    if tex_info_color is not None:
        tex_info_color = TextureInfo.from_dict(tex_info_color)

    sheenRoughnessFactor = ext.get('sheenRoughnessFactor', 0.0)
    tex_info_roughness = ext.get('sheenRoughnessTexture')
    if tex_info_roughness is not None:
        tex_info_roughness = TextureInfo.from_dict(tex_info_roughness)

    if tex_info_color is None:
        sheenTintFactor.extend([1.0])
        sheenTint_socket.default_value = sheenTintFactor
    else:
        # Mix sheenTint factor
        sheenTintFactor = sheenTintFactor + [1.0]
        if sheenTintFactor != [1.0, 1.0, 1.0, 1.0]:
            node = mh.node_tree.nodes.new('ShaderNodeMix')
            node.label = 'sheenTint Factor'
            node.data_type = 'RGBA'
            node.location = x_sheenTint - 140, y_sheenTint
            node.blend_type = 'MULTIPLY'
            # Outputs
            mh.node_tree.links.new(sheenTint_socket, node.outputs[2])
            # Inputs
            node.inputs['Factor'].default_value = 1.0
            sheenTint_socket = node.inputs[6]
            node.inputs[7].default_value = sheenTintFactor
            x_sheenTint -= 200

        texture(
            mh,
            tex_info=tex_info_color,
            label='SHEEN COLOR',
            location=(x_sheenTint, y_sheenTint),
            color_socket=sheenTint_socket
            )

    if tex_info_roughness is None:
        sheenRoughness_socket.default_value = sheenRoughnessFactor
    else:
         # Mix sheenRoughness factor
        if sheenRoughnessFactor != 1.0:
            node = mh.node_tree.nodes.new('ShaderNodeMath')
            node.label = 'shennRoughness Factor'
            node.location = x_sheenRoughness - 140, y_sheenRoughness
            node.operation = 'MULTIPLY'
            # Outputs
            mh.node_tree.links.new(sheenRoughness_socket, node.outputs[0])
            # Inputs
            sheenRoughness_socket = node.inputs[0]
            node.inputs[1].default_value = sheenRoughnessFactor
            x_sheenRoughness -= 200

        texture(
            mh,
            tex_info=tex_info_roughness,
            label='SHEEN ROUGHNESS',
            location=(x_sheenRoughness, y_sheenRoughness),
            is_data=True,
            color_socket=None,
            alpha_socket=sheenRoughness_socket
            )
    return
