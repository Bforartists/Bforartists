# SPDX-License-Identifier: Apache-2.0
# Copyright 2018-2021 The glTF-Blender-IO authors.

import typing
import bpy
from io_scene_gltf2.blender.exp.gltf2_blender_gather_cache import cached

from io_scene_gltf2.io.com import gltf2_io
from io_scene_gltf2.blender.exp import gltf2_blender_gather_sampler
from io_scene_gltf2.blender.exp import gltf2_blender_search_node_tree
from io_scene_gltf2.blender.exp import gltf2_blender_gather_image
from io_scene_gltf2.io.com import gltf2_io_debug
from io_scene_gltf2.io.exp.gltf2_io_user_extensions import export_user_extensions


@cached
def gather_texture(
        blender_shader_sockets: typing.Tuple[bpy.types.NodeSocket],
        export_settings):
    """
    Gather texture sampling information and image channels from a blender shader texture attached to a shader socket.

    :param blender_shader_sockets: The sockets of the material which should contribute to the texture
    :param export_settings: configuration of the export
    :return: a glTF 2.0 texture with sampler and source embedded (will be converted to references by the exporter)
    """

    if not __filter_texture(blender_shader_sockets, export_settings):
        return None, None

    source, factor = __gather_source(blender_shader_sockets, export_settings)

    texture = gltf2_io.Texture(
        extensions=__gather_extensions(blender_shader_sockets, export_settings),
        extras=__gather_extras(blender_shader_sockets, export_settings),
        name=__gather_name(blender_shader_sockets, export_settings),
        sampler=__gather_sampler(blender_shader_sockets, export_settings),
        source= source
    )

    # although valid, most viewers can't handle missing source properties
    # This can have None source for "keep original", when original can't be found
    if texture.source is None:
        return None, None

    export_user_extensions('gather_texture_hook', export_settings, texture, blender_shader_sockets)

    return texture, factor


def __filter_texture(blender_shader_sockets, export_settings):
    # User doesn't want to export textures
    if export_settings['gltf_image_format'] == "NONE":
        return None
    return True


def __gather_extensions(blender_shader_sockets, export_settings):
    return None


def __gather_extras(blender_shader_sockets, export_settings):
    return None


def __gather_name(blender_shader_sockets, export_settings):
    return None


def __gather_sampler(blender_shader_sockets, export_settings):
    shader_nodes = [__get_tex_from_socket(socket) for socket in blender_shader_sockets]
    if len(shader_nodes) > 1:
        gltf2_io_debug.print_console("WARNING",
                                     "More than one shader node tex image used for a texture. "
                                     "The resulting glTF sampler will behave like the first shader node tex image.")
    first_valid_shader_node = next(filter(lambda x: x is not None, shader_nodes)).shader_node
    return gltf2_blender_gather_sampler.gather_sampler(
        first_valid_shader_node,
        export_settings)


def __gather_source(blender_shader_sockets, export_settings):
    return gltf2_blender_gather_image.gather_image(blender_shader_sockets, export_settings)

# Helpers

# TODOExt deduplicate
def __get_tex_from_socket(socket):
    result = gltf2_blender_search_node_tree.from_socket(
        socket,
        gltf2_blender_search_node_tree.FilterByType(bpy.types.ShaderNodeTexImage))
    if not result:
        return None
    return result[0]
