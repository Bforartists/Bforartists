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


def export_sheen(blender_material, export_settings):
    sheen_extension = {}

    sheenTint_socket = get_socket(blender_material, "Sheen Tint")
    sheenRoughness_socket = get_socket(blender_material, "Sheen Roughness")
    sheen_socket = get_socket(blender_material, "Sheen Weight")

    if sheenTint_socket.socket is None or sheenRoughness_socket.socket is None or sheen_socket.socket is None:
        return None, {}, {}

    if sheen_socket.socket.is_linked is False and sheen_socket.socket.default_value == 0.0:
        return None, {}, {}

    uvmap_infos = {}
    udim_infos = {}

    #TODOExt : What to do if sheen_socket is linked? or is not between 0 and 1?

    sheenTint_non_linked = isinstance(sheenTint_socket.socket, bpy.types.NodeSocket) and not sheenTint_socket.socket.is_linked
    sheenRoughness_non_linked = isinstance(sheenRoughness_socket.socket, bpy.types.NodeSocket) and not sheenRoughness_socket.socket.is_linked


    if sheenTint_non_linked is True:
        color = sheenTint_socket.socket.default_value[:3]
        if color != (0.0, 0.0, 0.0):
            sheen_extension['sheenColorFactor'] = color
    else:
        # Factor
        fac = get_factor_from_socket(sheenTint_socket, kind='RGB')
        if fac is None:
            fac = [1.0, 1.0, 1.0] # Default is 0.0/0.0/0.0, so we need to set it to 1 if no factor
        if fac is not None and fac != [0.0, 0.0, 0.0]:
            sheen_extension['sheenColorFactor'] = fac

        # Texture
        if has_image_node_from_socket(sheenTint_socket, export_settings):
            original_sheenColor_texture, uvmap_info, udim_info, _ = gltf2_blender_gather_texture_info.gather_texture_info(
                sheenTint_socket,
                (sheenTint_socket,),
                export_settings,
            )
            sheen_extension['sheenColorTexture'] = original_sheenColor_texture
            uvmap_infos.update({'sheenColorTexture': uvmap_info})
            udim_infos.update({'sheenColorTexture': udim_info} if len(udim_info) > 0 else {})

    if sheenRoughness_non_linked is True:
        fac = sheenRoughness_socket.socket.default_value
        if fac != 0.0:
            sheen_extension['sheenRoughnessFactor'] = fac
    else:
        # Factor
        fac = get_factor_from_socket(sheenRoughness_socket, kind='VALUE')
        if fac is None:
            fac = 1.0 # Default is 0.0 so we need to set it to 1.0 if no factor
        if fac is not None and fac != 0.0:
            sheen_extension['sheenRoughnessFactor'] = fac

        # Texture
        if has_image_node_from_socket(sheenRoughness_socket, export_settings):
            original_sheenRoughness_texture, uvmap_info , udim_info, _ = gltf2_blender_gather_texture_info.gather_texture_info(
                sheenRoughness_socket,
                (sheenRoughness_socket,),
                export_settings,
            )
            sheen_extension['sheenRoughnessTexture'] = original_sheenRoughness_texture
            uvmap_infos.update({'sheenRoughnessTexture': uvmap_info})
            udim_infos.update({'sheenRoughnessTexture': udim_info} if len(udim_info) > 0 else {})

    return Extension('KHR_materials_sheen', sheen_extension, False), uvmap_infos, udim_infos
