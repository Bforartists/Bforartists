# SPDX-FileCopyrightText: 2023 Robin Hohnsbeen
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy


def get_vdm_bake_material():
    """Creates a material that is used to bake the displacement from a plane against its UVs.

    Returns:
    material: Baking material
    """
    material_name = 'VDM_baking_material'
    if material_name in bpy.data.materials:
        # Recreate material every time to ensure it is unchanged by the user which could lead to issues.
        # I would like to keep it directly after bake though so people could look
        # at how it is made, if they are interested.
        bpy.data.materials.remove(bpy.data.materials[material_name])

    new_material = bpy.data.materials.new(name=material_name)

    new_material.use_nodes = True
    nodes = new_material.node_tree.nodes
    principled_node = next(n for n in new_material.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    nodes.remove(principled_node)
    material_output = next(n for n in new_material.node_tree.nodes if n.type == "OUTPUT_MATERIAL")

    # Create relevant nodes
    combine_node = nodes.new('ShaderNodeCombineXYZ')

    separate_node1 = nodes.new('ShaderNodeSeparateXYZ')
    separate_node2 = nodes.new('ShaderNodeSeparateXYZ')

    vector_subtract_node = nodes.new('ShaderNodeVectorMath')
    vector_subtract_node.operation = 'SUBTRACT'

    vector_multiply_node = nodes.new('ShaderNodeVectorMath')
    vector_multiply_node.operation = 'MULTIPLY'
    vector_multiply_node.inputs[1].default_value = [2.0, 2.0, 2.0]

    vector_add_node = nodes.new('ShaderNodeVectorMath')
    vector_add_node.operation = 'ADD'
    vector_add_node.inputs[1].default_value = [-0.5, -0.5, -0.5]

    tex_coord_node = nodes.new('ShaderNodeTexCoord')

    image_node = nodes.new('ShaderNodeTexImage')
    image_node.name = "VDMTexture"

    # Connect nodes
    tree = new_material.node_tree
    tree.links.new(combine_node.outputs[0], material_output.inputs[0])

    tree.links.new(separate_node1.outputs[0], combine_node.inputs[0])
    tree.links.new(separate_node1.outputs[1], combine_node.inputs[1])

    tree.links.new(
        vector_subtract_node.outputs[0], separate_node1.inputs[0])

    tree.links.new(
        vector_multiply_node.outputs[0], vector_subtract_node.inputs[1])

    tree.links.new(
        vector_add_node.outputs[0], vector_multiply_node.inputs[0])

    tree.links.new(tex_coord_node.outputs[2], vector_add_node.inputs[0])
    tree.links.new(
        tex_coord_node.outputs[3], vector_subtract_node.inputs[0])
    tree.links.new(tex_coord_node.outputs[3], separate_node2.inputs[0])
    tree.links.new(separate_node2.outputs[2], combine_node.inputs[2])

    return bpy.data.materials[material_name]
