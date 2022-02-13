# SPDX-License-Identifier: Apache-2.0
# Copyright 2018-2021 The glTF-Blender-IO authors.

from math import sin, cos

def texture_transform_blender_to_gltf(mapping_transform):
    """
    Converts the offset/rotation/scale from a Mapping node applied in Blender's
    UV space to the equivalent KHR_texture_transform.
    """
    offset = mapping_transform.get('offset', [0, 0])
    rotation = mapping_transform.get('rotation', 0)
    scale = mapping_transform.get('scale', [1, 1])
    return {
        'offset': [
            offset[0] - scale[1] * sin(rotation),
            1 - offset[1] - scale[1] * cos(rotation),
        ],
        'rotation': rotation,
        'scale': [scale[0], scale[1]],
    }

def texture_transform_gltf_to_blender(texture_transform):
    """
    Converts a KHR_texture_transform into the equivalent offset/rotation/scale
    for a Mapping node applied in Blender's UV space.
    """
    offset = texture_transform.get('offset', [0, 0])
    rotation = texture_transform.get('rotation', 0)
    scale = texture_transform.get('scale', [1, 1])
    return {
        'offset': [
            offset[0] + scale[1] * sin(rotation),
            1 - offset[1] - scale[1] * cos(rotation),
        ],
        'rotation': rotation,
        'scale': [scale[0], scale[1]],
    }

def get_target(property):
    return {
        "delta_location": "translation",
        "delta_rotation_euler": "rotation",
        "location": "translation",
        "rotation_axis_angle": "rotation",
        "rotation_euler": "rotation",
        "rotation_quaternion": "rotation",
        "scale": "scale",
        "value": "weights"
    }.get(property)
