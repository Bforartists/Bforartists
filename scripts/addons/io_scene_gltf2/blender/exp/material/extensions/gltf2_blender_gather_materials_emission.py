# SPDX-FileCopyrightText: 2018-2022 The glTF-Blender-IO authors
#
# SPDX-License-Identifier: Apache-2.0

import bpy
from .....io.com.gltf2_io_extensions import Extension
from ...material import gltf2_blender_gather_texture_info
from ..gltf2_blender_search_node_tree import \
    get_const_from_default_value_socket, \
    get_socket, \
    get_factor_from_socket, \
    get_const_from_socket, \
    NodeSocket, \
    get_socket_from_gltf_material_node

def export_emission_factor(blender_material, export_settings):
    emissive_socket = get_socket(blender_material, "Emissive")
    if emissive_socket.socket is None:
        emissive_socket = get_socket_from_gltf_material_node(blender_material, "EmissiveFactor")
    if isinstance(emissive_socket.socket, bpy.types.NodeSocket):
        if export_settings['gltf_image_format'] != "NONE":
            factor = get_factor_from_socket(emissive_socket, kind='RGB')
        else:
            factor = get_const_from_default_value_socket(emissive_socket, kind='RGB')

        if factor is None and emissive_socket.socket.is_linked:
            # In glTF, the default emissiveFactor is all zeros, so if an emission texture is connected,
            # we have to manually set it to all ones.
            factor = [1.0, 1.0, 1.0]

        if factor is None: factor = [0.0, 0.0, 0.0]

        # Handle Emission Strength
        strength_socket = None
        if emissive_socket.socket.node.type == 'EMISSION':
            strength_socket = emissive_socket.socket.node.inputs['Strength']
        elif 'Emission Strength' in emissive_socket.socket.node.inputs:
            strength_socket = emissive_socket.socket.node.inputs['Emission Strength']
        strength = (
            get_const_from_socket(NodeSocket(strength_socket, emissive_socket.group_path), kind='VALUE')
            if strength_socket is not None
            else None
        )
        if strength is not None:
            factor = [f * strength for f in factor]

        # Clamp to range [0,1]
        # Official glTF clamp to range [0,1]
        # If we are outside, we need to use extension KHR_materials_emissive_strength

        if factor == [0, 0, 0]: factor = None

        return factor

    return None

def export_emission_texture(blender_material, export_settings):
    emissive = get_socket(blender_material, "Emissive")
    if emissive.socket is None:
        emissive = get_socket_from_gltf_material_node(blender_material, "Emissive")
    emissive_texture, uvmap_info, udim_info, _ = gltf2_blender_gather_texture_info.gather_texture_info(emissive, (emissive,), export_settings)
    return emissive_texture, {'emissiveTexture': uvmap_info}, {'emissiveTexture': udim_info} if len(udim_info.keys()) > 0 else {}

def export_emission_strength_extension(emissive_factor, export_settings):
    emissive_strength_extension = {}
    emissive_strength_extension['emissiveStrength'] = max(emissive_factor)

    return Extension('KHR_materials_emissive_strength', emissive_strength_extension, False)
