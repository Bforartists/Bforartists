# SPDX-License-Identifier: Apache-2.0
# Copyright 2018-2022 The glTF-Blender-IO authors.

import bpy
from io_scene_gltf2.io.com.gltf2_io_extensions import Extension
from io_scene_gltf2.blender.exp import gltf2_blender_get
from io_scene_gltf2.io.com.gltf2_io_constants import GLTF_IOR
from io_scene_gltf2.blender.com.gltf2_blender_default import BLENDER_SPECULAR, BLENDER_SPECULAR_TINT
from io_scene_gltf2.blender.exp import gltf2_blender_gather_texture_info



def export_original_specular(blender_material, export_settings):
    specular_extension = {}

    original_specular_socket = gltf2_blender_get.get_socket_old(blender_material, 'Specular')
    original_specularcolor_socket = gltf2_blender_get.get_socket_old(blender_material, 'Specular Color')

    if original_specular_socket is None or original_specularcolor_socket is None:
        return None, None

    specular_non_linked = isinstance(original_specular_socket, bpy.types.NodeSocket) and not original_specular_socket.is_linked
    specularcolor_non_linked = isinstance(original_specularcolor_socket, bpy.types.NodeSocket) and not original_specularcolor_socket.is_linked


    use_actives_uvmaps = []

    if specular_non_linked is True:
        fac = original_specular_socket.default_value
        if fac != 1.0:
            specular_extension['specularFactor'] = fac
    else:
        # Factor
        fac = gltf2_blender_get.get_factor_from_socket(original_specular_socket, kind='VALUE')
        if fac is not None and fac != 1.0:
            specular_extension['specularFactor'] = fac
        
        # Texture
        if gltf2_blender_get.has_image_node_from_socket(original_specular_socket):
            original_specular_texture, original_specular_use_active_uvmap, _ = gltf2_blender_gather_texture_info.gather_texture_info(
                original_specular_socket,
                (original_specular_socket,),
                export_settings,
            )
            specular_extension['specularTexture'] = original_specular_texture
            if original_specular_use_active_uvmap:
                use_actives_uvmaps.append("specularTexture")


    if specularcolor_non_linked is True:
        color = original_specularcolor_socket.default_value[:3]
        if color != [1.0, 1.0, 1.0]:
            specular_extension['specularColorFactor'] = color
    else:
        # Factor
        fac = gltf2_blender_get.get_factor_from_socket(original_specularcolor_socket, kind='RGB')
        if fac is not None and fac != [1.0, 1.0, 1.0]:
            specular_extension['specularColorFactor'] = fac

        # Texture
        if gltf2_blender_get.has_image_node_from_socket(original_specularcolor_socket):
            original_specularcolor_texture, original_specularcolor_use_active_uvmap, _ = gltf2_blender_gather_texture_info.gather_texture_info(
                original_specularcolor_socket,
                (original_specularcolor_socket,),
                export_settings,
            )
            specular_extension['specularColorTexture'] = original_specularcolor_texture
            if original_specularcolor_use_active_uvmap:
                use_actives_uvmaps.append("specularColorTexture")
    
    return Extension('KHR_materials_specular', specular_extension, False), use_actives_uvmaps

def export_specular(blender_material, export_settings):

    if export_settings['gltf_original_specular'] is True:
        return export_original_specular(blender_material, export_settings)

    specular_extension = {}
    specular_ext_enabled = False

    specular_socket = gltf2_blender_get.get_socket(blender_material, 'Specular')
    specular_tint_socket = gltf2_blender_get.get_socket(blender_material, 'Specular Tint')
    base_color_socket = gltf2_blender_get.get_socket(blender_material, 'Base Color')
    transmission_socket = gltf2_blender_get.get_socket(blender_material, 'Transmission')
    ior_socket = gltf2_blender_get.get_socket(blender_material, 'IOR')

    if base_color_socket is None:
        return None, None

    # TODOExt replace by __has_image_node_from_socket calls
    specular_not_linked = isinstance(specular_socket, bpy.types.NodeSocket) and not specular_socket.is_linked
    specular_tint_not_linked = isinstance(specular_tint_socket, bpy.types.NodeSocket) and not specular_tint_socket.is_linked
    base_color_not_linked = isinstance(base_color_socket, bpy.types.NodeSocket) and not base_color_socket.is_linked
    transmission_not_linked = isinstance(transmission_socket, bpy.types.NodeSocket) and not transmission_socket.is_linked
    ior_not_linked = isinstance(ior_socket, bpy.types.NodeSocket) and not ior_socket.is_linked

    specular = specular_socket.default_value if specular_not_linked else None
    specular_tint = specular_tint_socket.default_value if specular_tint_not_linked else None
    transmission = transmission_socket.default_value if transmission_not_linked else None
    ior = ior_socket.default_value if ior_not_linked else GLTF_IOR   # textures not supported #TODOExt add warning?
    base_color = base_color_socket.default_value[0:3]

    no_texture = (transmission_not_linked and specular_not_linked and specular_tint_not_linked and
        (specular_tint == 0.0 or (specular_tint != 0.0 and base_color_not_linked)))

    use_actives_uvmaps = []

    if no_texture:
        if specular != BLENDER_SPECULAR or specular_tint != BLENDER_SPECULAR_TINT:
            import numpy as np
            # See https://gist.github.com/proog128/d627c692a6bbe584d66789a5a6437a33
            specular_ext_enabled = True

            def normalize(c):
                luminance = lambda c: 0.3 * c[0] + 0.6 * c[1] + 0.1 * c[2]
                assert(len(c) == 3)
                l = luminance(c)
                if l == 0:
                    return np.array(c)
                return np.array([c[0] / l, c[1] / l, c[2] / l])            

            f0_from_ior = ((ior - 1)/(ior + 1))**2
            if f0_from_ior == 0:
                specular_color = [1.0, 1.0, 1.0]
            else:
                tint_strength = (1 - specular_tint) + normalize(base_color) * specular_tint
                specular_color = (1 - transmission) * (1 / f0_from_ior) * 0.08 * specular * tint_strength + transmission * tint_strength
                specular_color = list(specular_color)
            specular_extension['specularColorFactor'] = specular_color
    else:
        if specular_not_linked and specular == BLENDER_SPECULAR and specular_tint_not_linked and specular_tint == BLENDER_SPECULAR_TINT:
            return None, None

        # Trying to identify cases where exporting a texture will not be needed
        if specular_not_linked and transmission_not_linked and \
            specular == 0.0 and transmission == 0.0:

            specular_extension['specularColorFactor'] = [0.0, 0.0, 0.0]
            return specular_extension, []


        # There will be a texture, with a complex calculation (no direct channel mapping)
        sockets = (specular_socket, specular_tint_socket, base_color_socket, transmission_socket, ior_socket)
        # Set primary socket having a texture
        primary_socket = specular_socket
        if specular_not_linked:
            primary_socket = specular_tint_socket
            if specular_tint_not_linked:
                primary_socket = base_color_socket
                if base_color_not_linked:
                    primary_socket = transmission_socket

        specularColorTexture, use_active_uvmap, specularColorFactor = gltf2_blender_gather_texture_info.gather_texture_info(
            primary_socket, 
            sockets, 
            export_settings,
            filter_type='ANY')
        if specularColorTexture is None:
            return None, None
        if use_active_uvmap:
            use_actives_uvmaps.append("specularColorTexture")

        specular_ext_enabled = True
        specular_extension['specularColorTexture'] = specularColorTexture


        if specularColorFactor is not None:
            specular_extension['specularColorFactor'] = specularColorFactor
            

    specular_extension = Extension('KHR_materials_specular', specular_extension, False) if specular_ext_enabled else None
    return specular_extension, use_actives_uvmaps