# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

import unittest
import bpy


def create_object_mode_mesh_tool_tree(name, tool_idname):
    tree = bpy.data.node_groups.new(name, "GeometryNodeTree")
    tree.is_tool = True
    tree.is_mode_object = True
    tree.is_type_mesh = True
    tree.node_tool_idname = tool_idname
    return tree


def create_join_geometry_tool(tool_idname):
    """
    Create a geometry node group set up as an object-mode tool.
    Returns the node tree and the identifier of the Object input socket.
    """
    tree = create_object_mode_mesh_tool_tree("TestNodeTool", tool_idname)

    tree.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    obj_socket = tree.interface.new_socket("Object", in_out='INPUT', socket_type='NodeSocketObject')
    tree.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    group_input = tree.nodes.new("NodeGroupInput")
    group_output = tree.nodes.new("NodeGroupOutput")
    obj_info = tree.nodes.new("GeometryNodeObjectInfo")
    join_geo = tree.nodes.new("GeometryNodeJoinGeometry")

    tree.links.new(group_input.outputs["Geometry"], join_geo.inputs["Geometry"])
    tree.links.new(group_input.outputs["Object"], obj_info.inputs["Object"])
    tree.links.new(obj_info.outputs["Geometry"], join_geo.inputs["Geometry"])
    tree.links.new(join_geo.outputs["Geometry"], group_output.inputs["Geometry"])

    return tree, obj_socket.identifier


class TestNodeTool(unittest.TestCase):
    def setUp(self):
        bpy.ops.wm.read_factory_settings(use_empty=True)

    def test_join_geometry_with_object_input(self):
        from bpy.types import WindowManager
        # Add a cube (the active object the tool will run on).
        bpy.ops.mesh.primitive_cube_add()
        cube = bpy.context.active_object
        cube_vertex_count = len(cube.data.vertices)

        # Add a monkey/Suzanne (the tool's object input, joined into the cube).
        bpy.ops.mesh.primitive_monkey_add()
        monkey = bpy.context.active_object
        monkey_vertex_count = len(monkey.data.vertices)

        # Make the cube the active, selected object.
        bpy.context.view_layer.objects.active = cube
        for obj in bpy.context.scene.objects:
            obj.select_set(obj == cube)

        _tree, obj_input_identifier = create_join_geometry_tool("geometry.test_node_tool_join_geometry")

        WindowManager.register_node_group_operators()

        bpy.ops.geometry.test_node_tool_join_geometry(
            'EXEC_DEFAULT',
            inputs={obj_input_identifier: {"value": monkey.name}},
        )

        # The cube's mesh should now contain geometry from both the cube and the
        # monkey, so the vertex count should be the sum of both.
        expected_vertex_count = cube_vertex_count + monkey_vertex_count
        self.assertEqual(len(cube.data.vertices), expected_vertex_count)

    def test_string_inputs_store_named_attribute(self):
        from bpy.types import WindowManager

        bpy.ops.mesh.primitive_cube_add()
        cube = bpy.context.active_object

        tree = create_object_mode_mesh_tool_tree(
            "TestNodeToolStringInputs", "geometry.test_node_tool_string_inputs"
        )
        tree.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
        str_default_socket = tree.interface.new_socket(
            "Name With Default", in_out='INPUT', socket_type='NodeSocketString')
        str_default_socket.default_value = "attr_with_default"
        str_no_default_socket = tree.interface.new_socket(
            "Name Without Default", in_out='INPUT', socket_type='NodeSocketString')
        tree.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

        group_input = tree.nodes.new("NodeGroupInput")
        group_output = tree.nodes.new("NodeGroupOutput")
        store_default = tree.nodes.new("GeometryNodeStoreNamedAttribute")
        store_no_default = tree.nodes.new("GeometryNodeStoreNamedAttribute")

        tree.links.new(group_input.outputs["Geometry"], store_default.inputs["Geometry"])
        tree.links.new(store_default.outputs["Geometry"], store_no_default.inputs["Geometry"])
        tree.links.new(store_no_default.outputs["Geometry"], group_output.inputs["Geometry"])
        tree.links.new(group_input.outputs["Name With Default"], store_default.inputs["Name"])
        tree.links.new(group_input.outputs["Name Without Default"], store_no_default.inputs["Name"])

        WindowManager.register_node_group_operators()

        # The string with a default value is left at its default ("attr_with_default").
        # The string without a default is explicitly set when calling the tool.
        bpy.ops.geometry.test_node_tool_string_inputs(
            'EXEC_DEFAULT',
            inputs={str_no_default_socket.identifier: {"value": "attr_without_default"}},
        )

        attribute_names = {attr.name for attr in cube.data.attributes}
        self.assertIn("attr_with_default", attribute_names)
        self.assertIn("attr_without_default", attribute_names)


if __name__ == "__main__":
    import sys
    sys.argv = [__file__] + (sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    unittest.main()
