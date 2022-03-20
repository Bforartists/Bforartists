# SPDX-License-Identifier: Apache-2.0
# Copyright 2018-2021 The glTF-Blender-IO authors.

import bpy

def get_gltf_node_name():
    return "glTF Settings"

def create_settings_group(name):
    gltf_node_group = bpy.data.node_groups.new(name, 'ShaderNodeTree')
    gltf_node_group.inputs.new("NodeSocketFloat", "Occlusion")
    gltf_node_group.nodes.new('NodeGroupOutput')
    gltf_node_group_input = gltf_node_group.nodes.new('NodeGroupInput')
    gltf_node_group_input.location = -200, 0
    return gltf_node_group