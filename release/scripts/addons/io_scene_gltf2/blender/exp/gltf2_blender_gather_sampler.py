# Copyright 2018 The glTF-Blender-IO authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import bpy
from io_scene_gltf2.io.com import gltf2_io
from io_scene_gltf2.blender.exp.gltf2_blender_gather_cache import cached
from io_scene_gltf2.io.exp.gltf2_io_user_extensions import export_user_extensions


@cached
def gather_sampler(blender_shader_node: bpy.types.Node, export_settings):
    if not __filter_sampler(blender_shader_node, export_settings):
        return None

    sampler = gltf2_io.Sampler(
        extensions=__gather_extensions(blender_shader_node, export_settings),
        extras=__gather_extras(blender_shader_node, export_settings),
        mag_filter=__gather_mag_filter(blender_shader_node, export_settings),
        min_filter=__gather_min_filter(blender_shader_node, export_settings),
        name=__gather_name(blender_shader_node, export_settings),
        wrap_s=__gather_wrap_s(blender_shader_node, export_settings),
        wrap_t=__gather_wrap_t(blender_shader_node, export_settings)
    )

    export_user_extensions('gather_sampler_hook', export_settings, sampler, blender_shader_node)

    return sampler


def __filter_sampler(blender_shader_node, export_settings):
    if not blender_shader_node.interpolation == 'Closest' and not blender_shader_node.extension == 'EXTEND':
        return False
    return True


def __gather_extensions(blender_shader_node, export_settings):
    return None


def __gather_extras(blender_shader_node, export_settings):
    return None


def __gather_mag_filter(blender_shader_node, export_settings):
    if blender_shader_node.interpolation == 'Closest':
        return 9728  # NEAREST
    return 9729  # LINEAR


def __gather_min_filter(blender_shader_node, export_settings):
    if blender_shader_node.interpolation == 'Closest':
        return 9984  # NEAREST_MIPMAP_NEAREST
    return 9986  # NEAREST_MIPMAP_LINEAR


def __gather_name(blender_shader_node, export_settings):
    return None


def __gather_wrap_s(blender_shader_node, export_settings):
    if blender_shader_node.extension == 'EXTEND':
        return 33071
    return None


def __gather_wrap_t(blender_shader_node, export_settings):
    if blender_shader_node.extension == 'EXTEND':
        return 33071
    return None
