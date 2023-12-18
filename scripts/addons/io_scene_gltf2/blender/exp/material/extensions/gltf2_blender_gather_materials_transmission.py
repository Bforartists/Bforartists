# SPDX-FileCopyrightText: 2018-2022 The glTF-Blender-IO authors
#
# SPDX-License-Identifier: Apache-2.0

import bpy
from .....io.com.gltf2_io_extensions import Extension
from ...material import gltf2_blender_gather_texture_info
from ..gltf2_blender_search_node_tree import \
    has_image_node_from_socket, \
    get_socket, \
    get_factor_from_socket

def export_transmission(blender_material, export_settings):
    transmission_enabled = False
    has_transmission_texture = False

    transmission_extension = {}
    transmission_slots = ()

    transmission_socket = get_socket(blender_material, 'Transmission Weight')

    if isinstance(transmission_socket.socket, bpy.types.NodeSocket) and not transmission_socket.socket.is_linked:
        transmission_extension['transmissionFactor'] = transmission_socket.socket.default_value
        transmission_enabled = transmission_extension['transmissionFactor'] > 0
    elif has_image_node_from_socket(transmission_socket, export_settings):
        fac = get_factor_from_socket(transmission_socket, kind='VALUE')
        transmission_extension['transmissionFactor'] = fac if fac is not None else 1.0
        has_transmission_texture = True
        transmission_enabled = True

    if not transmission_enabled:
        return None, {}, {}

    uvmap_info = {}
    udim_info = {}

    # Pack transmission channel (R).
    if has_transmission_texture:
        transmission_slots = (transmission_socket,)

    if len(transmission_slots) > 0:
        combined_texture, uvmap_info, udim_info, _ = gltf2_blender_gather_texture_info.gather_texture_info(
            transmission_socket,
            transmission_slots,
            export_settings,
        )
        if has_transmission_texture:
            transmission_extension['transmissionTexture'] = combined_texture

    return Extension('KHR_materials_transmission', transmission_extension, False), {'transmissionTexture': uvmap_info}, {'transmissionTexture': udim_info} if len(udim_info) > 0 else {}
