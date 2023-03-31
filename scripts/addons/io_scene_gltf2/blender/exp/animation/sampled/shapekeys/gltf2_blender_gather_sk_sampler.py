# SPDX-License-Identifier: Apache-2.0
# Copyright 2018-2022 The glTF-Blender-IO authors.

import bpy
from ......io.com import gltf2_io, gltf2_io_constants
from ......io.exp import gltf2_io_binary_data
from ......io.exp.gltf2_io_user_extensions import export_user_extensions
from .....com.gltf2_blender_math import mathutils_to_gltf
from ....gltf2_blender_gather_accessors import gather_accessor
from .gltf2_blender_gather_sk_keyframes import gather_sk_sampled_keyframes

def gather_sk_sampled_animation_sampler(
        obj_uuid,
        action_name,
        export_settings
        ):

    keyframes = __gather_keyframes(
        obj_uuid,
        action_name,
        export_settings)

    if keyframes is None:
        # After check, no need to animate this node for this channel
        return None

    # Now we are raw input/output, we need to convert to glTF data
    input, output = __convert_keyframes(obj_uuid, keyframes, action_name, export_settings)

    sampler = gltf2_io.AnimationSampler(
        extensions=None,
        extras=None,
        input=input,
        interpolation=__gather_interpolation(export_settings),
        output=output
    )

    blender_object = export_settings['vtree'].nodes[obj_uuid].blender_object
    export_user_extensions('animation_gather_sk_channels', export_settings, blender_object, action_name)

    return sampler

def __gather_keyframes(
        obj_uuid,
        action_name,
        export_settings):

    keyframes = gather_sk_sampled_keyframes(
        obj_uuid,
        action_name,
        export_settings
    )

    if keyframes is None:
        # After check, no need to animation this node
        return None

    return keyframes

def __convert_keyframes(obj_uuid, keyframes, action_name: str, export_settings):

    # Sliding can come from:
    # - option SLIDE for negative frames
    # - option to start animation at frame 0 for looping
    if obj_uuid in export_settings['slide'].keys() and action_name in export_settings['slide'][obj_uuid].keys():
        for k in keyframes:
            k.frame += -export_settings['slide'][obj_uuid][action_name]
            k.seconds = k.frame / bpy.context.scene.render.fps

    times = [k.seconds for k in keyframes]
    input = gather_accessor(
        gltf2_io_binary_data.BinaryData.from_list(times, gltf2_io_constants.ComponentType.Float),
        gltf2_io_constants.ComponentType.Float,
        len(times),
        tuple([max(times)]),
        tuple([min(times)]),
        gltf2_io_constants.DataType.Scalar,
        export_settings)

    values = []
    for keyframe in keyframes:
        keyframe_value = mathutils_to_gltf(keyframe.value)
        values += keyframe_value

    component_type = gltf2_io_constants.ComponentType.Float
    data_type = gltf2_io_constants.DataType.Scalar

    output = gltf2_io.Accessor(
        buffer_view=gltf2_io_binary_data.BinaryData.from_list(values, component_type),
        byte_offset=None,
        component_type=component_type,
        count=len(values) // gltf2_io_constants.DataType.num_elements(data_type),
        extensions=None,
        extras=None,
        max=None,
        min=None,
        name=None,
        normalized=None,
        sparse=None,
        type=data_type
        )

    return input, output

def __gather_interpolation(export_settings):
    # TODO: check if the SK was animated with CONSTANT
    return 'LINEAR'
