# SPDX-License-Identifier: Apache-2.0
# Copyright 2018-2022 The glTF-Blender-IO authors.

import bpy
from io_scene_gltf2.io.com.gltf2_io_extensions import Extension
from io_scene_gltf2.blender.exp import gltf2_blender_get
from io_scene_gltf2.blender.exp import gltf2_blender_gather_texture_info

def export_transmission(blender_material, export_settings):
    transmission_enabled = False
    has_transmission_texture = False

    transmission_extension = {}
    transmission_slots = ()

    transmission_socket = gltf2_blender_get.get_socket(blender_material, 'Transmission')

    if isinstance(transmission_socket, bpy.types.NodeSocket) and not transmission_socket.is_linked:
        transmission_extension['transmissionFactor'] = transmission_socket.default_value
        transmission_enabled = transmission_extension['transmissionFactor'] > 0
    elif gltf2_blender_get.has_image_node_from_socket(transmission_socket):
        fac = gltf2_blender_get.get_factor_from_socket(transmission_socket, kind='VALUE')
        transmission_extension['transmissionFactor'] = fac if fac is not None else 1.0
        has_transmission_texture = True
        transmission_enabled = True

    if not transmission_enabled:
        return None, None

    # Pack transmission channel (R).
    if has_transmission_texture:
        transmission_slots = (transmission_socket,)

    use_actives_uvmaps = []

    if len(transmission_slots) > 0:
        combined_texture, use_active_uvmap, _ = gltf2_blender_gather_texture_info.gather_texture_info(
            transmission_socket,
            transmission_slots,
            export_settings,
        )
        if has_transmission_texture:
            transmission_extension['transmissionTexture'] = combined_texture
        if use_active_uvmap:
            use_actives_uvmaps.append("transmissionTexture")

    return Extension('KHR_materials_transmission', transmission_extension, False), use_actives_uvmaps