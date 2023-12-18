# SPDX-FileCopyrightText: 2018-2022 The glTF-Blender-IO authors
#
# SPDX-License-Identifier: Apache-2.0

import bpy
from .gltf2_blender_image import TmpImageGuard, make_temp_image_copy, StoreImage, StoreData
import numpy as np
from .....io.com.gltf2_io_extensions import Extension
from ....com.gltf2_blender_conversion import get_anisotropy_rotation_blender_to_gltf
from ...material import gltf2_blender_gather_texture_info
from ..gltf2_blender_search_node_tree import detect_anisotropy_nodes, get_socket, has_image_node_from_socket, get_factor_from_socket

def export_anisotropy(blender_material, export_settings):

    anisotropy_extension = {}
    uvmap_infos = {}
    udim_infos = {}

    anisotropy_socket = get_socket(blender_material, 'Anisotropic')
    anisotropic_rotation_socket = get_socket(blender_material, 'Anisotropic Rotation')
    anisotropy_tangent_socket = get_socket(blender_material, 'Tangent')

    if anisotropy_socket.socket is None or anisotropic_rotation_socket.socket is None or anisotropy_tangent_socket.socket is None:
        return None, {}, {}

    if anisotropy_socket.socket.is_linked is False and anisotropic_rotation_socket.socket.is_linked is False:
        # We don't need the complex node setup, just export the value
        anisotropyStrength = anisotropy_socket.socket.default_value
        if anisotropyStrength != 0.0:
            anisotropy_extension['anisotropyStrength'] = anisotropyStrength
        anisotropyRotation = get_anisotropy_rotation_blender_to_gltf(anisotropic_rotation_socket.socket.default_value)
        if anisotropyRotation != 0.0:
            anisotropy_extension['anisotropyRotation'] = anisotropyRotation

        if len(anisotropy_extension) == 0:
            return None, {}, {}

        return Extension('KHR_materials_anisotropy', anisotropy_extension, False), uvmap_infos, udim_infos

    # Get complex node setup

    is_anisotropy, anisotropy_data = detect_anisotropy_nodes(
        anisotropy_socket,
        anisotropic_rotation_socket,
        anisotropy_tangent_socket,
        export_settings
    )

    if not is_anisotropy:
        # Trying to export from grayscale textures
        anisotropy_texture, uvmap_info = export_anisotropy_from_grayscale_textures(blender_material, export_settings)
        if anisotropy_texture is None:
            return None, {}, {}

        fac = get_factor_from_socket(anisotropy_socket, kind='VALUE')
        if fac is None and anisotropy_texture is not None:
            anisotropy_extension['anisotropyStrength'] = 1.0
        elif fac != 0.0 and anisotropy_texture is not None:
            anisotropy_extension['anisotropyStrength'] = fac

        fac = get_factor_from_socket(anisotropic_rotation_socket, kind='VALUE')
        if fac is None and anisotropy_texture is not None:
            pass # Rotation 0 is default
        elif fac != 0.0 and anisotropy_texture is not None:
            anisotropy_extension['anisotropyRotation'] = get_anisotropy_rotation_blender_to_gltf(fac)

        anisotropy_extension['anisotropyTexture'] = anisotropy_texture
        uvmap_infos.update({'anisotropyTexture': uvmap_info})

        return Extension('KHR_materials_anisotropy', anisotropy_extension, False), uvmap_infos, udim_infos


    # Export from complex node setup

    if anisotropy_data['anisotropyStrength'] != 0.0:
        anisotropy_extension['anisotropyStrength'] = anisotropy_data['anisotropyStrength']
    if anisotropy_data['anisotropyRotation'] != 0.0:
        anisotropy_extension['anisotropyRotation'] = anisotropy_data['anisotropyRotation']

    # Get texture data
    # No need to check here that we have a texture, this check is already done insode detect_anisotropy_nodes
    anisotropy_texture, uvmap_info , udim_info, _ = gltf2_blender_gather_texture_info.gather_texture_info(
        anisotropy_data['tex_socket'],
        (anisotropy_data['tex_socket'],),
        export_settings,
    )
    anisotropy_extension['anisotropyTexture'] = anisotropy_texture
    uvmap_infos.update({'anisotropyTexture': uvmap_info})
    udim_infos.update({'anisotropyTexture' : udim_info} if len(udim_info.keys()) > 0 else {})


    return Extension('KHR_materials_anisotropy', anisotropy_extension, False), uvmap_infos, udim_infos

def export_anisotropy_from_grayscale_textures(blender_material, export_settings):
    # There will be a texture, with a complex calculation (no direct channel mapping)

    anisotropy_socket = get_socket(blender_material, 'Anisotropic')
    anisotropic_rotation_socket = get_socket(blender_material, 'Anisotropic Rotation')
    anisotropy_tangent_socket = get_socket(blender_material, 'Tangent')

    sockets = (anisotropy_socket, anisotropic_rotation_socket, anisotropy_tangent_socket)

    # Set primary socket having a texture
    primary_socket = anisotropy_socket
    if not has_image_node_from_socket(primary_socket, export_settings):
        primary_socket = anisotropic_rotation_socket

    anisotropyTexture, uvmap_info, _, _ = gltf2_blender_gather_texture_info.gather_texture_info(
        primary_socket,
        sockets,
        export_settings,
        filter_type='ANY')

    if anisotropyTexture is None:
        return None, {}

    return anisotropyTexture, uvmap_info


def grayscale_anisotropy_calculation(stored, export_settings):

    # Find all Blender images used
    images = []
    for fill in stored.values():
        if isinstance(fill, StoreImage):
            if fill.image not in images:
                images.append(fill.image)

    if not images:
        # No ImageFills; use a 1x1 white pixel
        pixels = np.array([1.0, 1.0, 1.0, 1.0], np.float32)
        return pixels, 1, 1

    width = max(image.size[0] for image in images)
    height = max(image.size[1] for image in images)

    buffers = {}

    def rgb2gray(rgb):
        r, g, b = rgb[:,:,0], rgb[:,:,1], rgb[:,:,2]
        gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
        return gray

    for identifier, image in [(ident, store.image) for (ident, store) in stored.items() if isinstance(store, StoreImage)]:
        tmp_buf = np.empty(width * height * 4, np.float32)

        if image.size[0] == width and image.size[1] == height:
            image.pixels.foreach_get(tmp_buf)
        else:
            # Image is the wrong size; make a temp copy and scale it.
            with TmpImageGuard() as guard:
                make_temp_image_copy(guard, src_image=image)
                tmp_image = guard.image
                tmp_image.scale(width, height)
                tmp_image.pixels.foreach_get(tmp_buf)

        buffers[identifier] = np.reshape(tmp_buf, [width, height, 4])
        buffers[identifier] = rgb2gray(buffers[identifier])

    for identifier, data in [(ident, data) for (ident, data) in stored.items() if isinstance(data, StoreData)]:
        buffers[identifier] =  np.full((width, height), 1) # Set to white / 1.0, as value is set as factor

    # Combine the image
    out_buf = np.zeros((width, height, 4), np.float32)
    out_buf[:,:,3] = 1.0  # A : Alpha
    out_buf[:,:,2] = buffers['anisotropy']  # B : Strength (Anisotropic socket)

    # Rotation needs to be converted from 0-1 to 0-2pi, and then vectorized it, normalized, and apply to R & G channels
    # with mapping

    buffers['anisotropic_rotation'] = buffers['anisotropic_rotation'] * 2 * np.pi
    buffers['anisotropic_rotation'] = np.stack((np.cos(buffers['anisotropic_rotation']), np.sin(buffers['anisotropic_rotation'])), axis=-1)
    buffers['anisotropic_rotation'] = buffers['anisotropic_rotation'] / np.linalg.norm(buffers['anisotropic_rotation'], axis=-1, keepdims=True)
    buffers['anisotropic_rotation'] = (buffers['anisotropic_rotation'] + 1.0) / 2.0

    out_buf[:,:,0] = buffers['anisotropic_rotation'][:,:,0]  # R : Rotation X
    out_buf[:,:,1] = buffers['anisotropic_rotation'][:,:,1]  # G : Rotation Y

    out_buf = np.reshape(out_buf, (width * height * 4))


    return np.float32(out_buf), width, height, None
