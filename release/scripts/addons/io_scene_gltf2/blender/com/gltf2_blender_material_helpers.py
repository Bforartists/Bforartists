# SPDX-License-Identifier: Apache-2.0
# Copyright 2018-2021 The glTF-Blender-IO authors.

import bpy

def get_gltf_node_name():
    return "glTF Settings"

def create_settings_group(name):
    gltf_node_group = bpy.data.node_groups.new(name, 'ShaderNodeTree')
    gltf_node_group.inputs.new("NodeSocketFloat", "Occlusion")
    thicknessFactor  = gltf_node_group.inputs.new("NodeSocketFloat", "Thickness")
    thicknessFactor.default_value = 1.0
    gltf_node_group.nodes.new('NodeGroupOutput')
    gltf_node_group_input = gltf_node_group.nodes.new('NodeGroupInput')
    gltf_node_group_input.location = -200, 0
    return gltf_node_group

def get_gltf_pbr_non_converted_name():
    return "original glTF PBR data"

def create_gltf_pbr_non_converted_group(name):
    gltf_node_group = bpy.data.node_groups.new(name, 'ShaderNodeTree')

    specular = gltf_node_group.inputs.new("NodeSocketFloat", "specular glTF")
    specular.default_value = 1.0
    specularColor = gltf_node_group.inputs.new("NodeSocketColor", "specularColor glTF")
    specularColor.default_value = [1.0,1.0,1.0,1.0]

    gltf_node_group.nodes.new('NodeGroupOutput')
    gltf_node_group_input = gltf_node_group.nodes.new('NodeGroupInput')
    gltf_node_group_input.location = -400, 0
    return gltf_node_group    