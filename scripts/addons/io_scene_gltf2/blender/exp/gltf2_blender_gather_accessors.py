# SPDX-License-Identifier: Apache-2.0
# Copyright 2018-2021 The glTF-Blender-IO authors.


from io_scene_gltf2.blender.exp.gltf2_blender_gather_cache import cached
from io_scene_gltf2.io.com import gltf2_io
from io_scene_gltf2.io.com import gltf2_io_constants
from io_scene_gltf2.io.exp import gltf2_io_binary_data


@cached
def gather_accessor(buffer_view: gltf2_io_binary_data.BinaryData,
                    component_type: gltf2_io_constants.ComponentType,
                    count,
                    max,
                    min,
                    type: gltf2_io_constants.DataType,
                    export_settings) -> gltf2_io.Accessor:
    return gltf2_io.Accessor(
        buffer_view=buffer_view,
        byte_offset=None,
        component_type=component_type,
        count=count,
        extensions=None,
        extras=None,
        max=list(max) if max is not None else None,
        min=list(min) if min is not None else None,
        name=None,
        normalized=None,
        sparse=None,
        type=type
    )
