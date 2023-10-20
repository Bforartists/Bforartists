# SPDX-FileCopyrightText: 2009-2023 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

__all__ = (
    "find_node_input",
)


def find_base_socket_type(socket):
    """
    Find the base class of the socket.

    Sockets can have a subtype such as NodeSocketFloatFactor,
    but only the base type is allowed, e. g. NodeSocketFloat
    """
    if socket.type == 'CUSTOM':
        # Custom socket types are used directly
        return socket.bl_idname
    if socket.type == 'VALUE':
        return 'NodeSocketFloat'
    if socket.type == 'INT':
        return 'NodeSocketInt'
    if socket.type == 'BOOLEAN':
        return 'NodeSocketBoolean'
    if socket.type == 'VECTOR':
        return 'NodeSocketVector'
    if socket.type == 'ROTATION':
        return 'NodeSocketRotation'
    if socket.type == 'STRING':
        return 'NodeSocketString'
    if socket.type == 'RGBA':
        return 'NodeSocketColor'
    if socket.type == 'SHADER':
        return 'NodeSocketShader'
    if socket.type == 'OBJECT':
        return 'NodeSocketObject'
    if socket.type == 'IMAGE':
        return 'NodeSocketImage'
    if socket.type == 'GEOMETRY':
        return 'NodeSocketGeometry'
    if socket.type == 'COLLECTION':
        return 'NodeSocketCollection'
    if socket.type == 'TEXTURE':
        return 'NodeSocketTexture'
    if socket.type == 'MATERIAL':
        return 'NodeSocketMaterial'


def connect_sockets(input, output):
    """
    Connect sockets in a node tree.

    This is useful because the links created through the normal Python API are
    invalid when one of the sockets is a virtual socket (grayed out sockets in
    Group Input and Group Output nodes).

    It replaces node_tree.links.new(input, output)
    """
    import bpy

    # Swap sockets if they are not passed in the proper order
    if input.is_output and not output.is_output:
        input, output = output, input

    input_node = output.node
    output_node = input.node

    if input_node.id_data is not output_node.id_data:
        print("Sockets do not belong to the same node tree")
        return

    if type(input) == type(output) == bpy.types.NodeSocketVirtual:
        print("Cannot connect two virtual sockets together")
        return

    if output_node.type == 'GROUP_OUTPUT' and type(input) == bpy.types.NodeSocketVirtual:
        output_type = find_base_socket_type(output)
        socket_interface = output_node.id_data.interface.new_socket(
            name=output.name, socket_type=output_type, in_out='OUTPUT'
        )
        input = output_node.inputs[-2]

    if input_node.type == 'GROUP_INPUT' and type(output) == bpy.types.NodeSocketVirtual:
        input_type = find_base_socket_type(input)
        socket_interface = input_node.id_data.interface.new_socket(
            name=input.name, socket_type=input_type, in_out='INPUT'
        )
        output = input_node.outputs[-2]

    return input_node.id_data.links.new(input, output)


# XXX Names are not unique. Returns the first match.
def find_node_input(node, name):
    for input in node.inputs:
        if input.name == name:
            return input

    return None
