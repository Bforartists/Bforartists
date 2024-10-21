# SPDX-FileCopyrightText: 2012-2023 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

from __future__ import annotations

import bpy
from bpy.types import (
    FileHandler,
    Operator,
    PropertyGroup,
)
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatVectorProperty,
    StringProperty,
)
from mathutils import (
    Vector,
)

from bpy.app.translations import (
    pgettext_tip as tip_,
    pgettext_rpt as rpt_,
)

from nodeitems_builtins import node_tree_group_type


class NodeSetting(PropertyGroup):
    value: StringProperty(
        name="Value",
        description="Python expression to be evaluated "
        "as the initial node setting",
        default="",
    )


# Base class for node "Add" operators.
class NodeAddOperator:

    use_transform: BoolProperty(
        name="Use Transform",
        description="Start transform operator after inserting the node",
        default=False,
    )
    settings: CollectionProperty(
        name="Settings",
        description="Settings to be applied on the newly created node",
        type=NodeSetting,
        options={'SKIP_SAVE'},
    )

    @staticmethod
    def store_mouse_cursor(context, event):
        space = context.space_data
        tree = space.edit_tree

        # convert mouse position to the View2D for later node placement
        if context.region.type == 'WINDOW':
            # convert mouse position to the View2D for later node placement
            space.cursor_location_from_region(event.mouse_region_x, event.mouse_region_y)
        else:
            space.cursor_location = tree.view_center

    # Deselect all nodes in the tree.
    @staticmethod
    def deselect_nodes(context):
        space = context.space_data
        tree = space.edit_tree
        for n in tree.nodes:
            n.select = False

    def create_node(self, context, node_type):
        space = context.space_data
        tree = space.edit_tree

        try:
            node = tree.nodes.new(type=node_type)
        except RuntimeError as ex:
            self.report({'ERROR'}, str(ex))
            return None

        for setting in self.settings:
            # XXX catch exceptions here?
            value = eval(setting.value)
            node_data = node
            node_attr_name = setting.name

            # Support path to nested data.
            if '.' in node_attr_name:
                node_data_path, node_attr_name = node_attr_name.rsplit(".", 1)
                node_data = node.path_resolve(node_data_path)

            try:
                setattr(node_data, node_attr_name, value)
            except AttributeError as ex:
                self.report(
                    {'ERROR_INVALID_INPUT'},
                    rpt_("Node has no attribute {:s}").format(setting.name))
                print(str(ex))
                # Continue despite invalid attribute

        node.select = True
        tree.nodes.active = node
        node.location = space.cursor_location
        return node

    @classmethod
    def poll(cls, context):
        space = context.space_data
        # needs active node editor and a tree to add nodes to
        return (space and (space.type == 'NODE_EDITOR') and
                space.edit_tree and space.edit_tree.is_editable)

    # Default invoke stores the mouse position to place the node correctly
    # and optionally invokes the transform operator
    def invoke(self, context, event):
        self.store_mouse_cursor(context, event)
        result = self.execute(context)

        if self.use_transform and ('FINISHED' in result):
            # removes the node again if transform is canceled
            bpy.ops.node.translate_attach_remove_on_cancel('INVOKE_DEFAULT')

        return result


# Simple basic operator for adding a node.
class NODE_OT_add_node(NodeAddOperator, Operator):
    """Add a node to the active tree"""
    bl_idname = "node.add_node"
    bl_label = "Add Node"
    bl_options = {'REGISTER', 'UNDO'}

    type: StringProperty(
        name="Node Type",
        description="Node type",
    )

    # Default execute simply adds a node.
    def execute(self, context):
        if self.properties.is_property_set("type"):
            self.deselect_nodes(context)
            self.create_node(context, self.type)
            return {'FINISHED'}
        else:
            return {'CANCELLED'}

    @classmethod
    def description(cls, _context, properties):
        nodetype = properties["type"]
        if nodetype in node_tree_group_type.values():
            for setting in properties.settings:
                if setting.name == "node_tree":
                    node_group = eval(setting.value)
                    if node_group.description:
                        return node_group.description
        bl_rna = bpy.types.Node.bl_rna_get_subclass(nodetype)
        if bl_rna is not None:
            return tip_(bl_rna.description)
        else:
            return ""


class NodeAddZoneOperator(NodeAddOperator):
    offset: FloatVectorProperty(
        name="Offset",
        description="Offset of nodes from the cursor when added",
        size=2,
        default=(150, 0),
    )

    add_default_geometry_link = True

    def execute(self, context):
        space = context.space_data
        tree = space.edit_tree

        self.deselect_nodes(context)
        input_node = self.create_node(context, self.input_node_type)
        output_node = self.create_node(context, self.output_node_type)
        if input_node is None or output_node is None:
            return {'CANCELLED'}

        # Simulation input must be paired with the output.
        input_node.pair_with_output(output_node)

        input_node.location -= Vector(self.offset)
        output_node.location += Vector(self.offset)

        if self.add_default_geometry_link:
            # Connect geometry sockets by default if available.
            # Get the sockets by their types, because the name is not guaranteed due to i18n.
            from_socket = next(s for s in input_node.outputs if s.type == 'GEOMETRY')
            to_socket = next(s for s in output_node.inputs if s.type == 'GEOMETRY')
            tree.links.new(to_socket, from_socket)

        return {'FINISHED'}


class NODE_OT_add_simulation_zone(NodeAddZoneOperator, Operator):
    """Add simulation zone input and output nodes to the active tree"""
    bl_idname = "node.add_simulation_zone"
    bl_label = "Add Simulation Zone"
    bl_options = {'REGISTER', 'UNDO'}

    input_node_type = "GeometryNodeSimulationInput"
    output_node_type = "GeometryNodeSimulationOutput"


class NODE_OT_add_repeat_zone(NodeAddZoneOperator, Operator):
    """Add a repeat zone that allows executing nodes a dynamic number of times"""
    bl_idname = "node.add_repeat_zone"
    bl_label = "Add Repeat Zone"
    bl_options = {'REGISTER', 'UNDO'}

    input_node_type = "GeometryNodeRepeatInput"
    output_node_type = "GeometryNodeRepeatOutput"


class NODE_OT_add_foreach_geometry_element_zone(NodeAddZoneOperator, Operator):
    """Add a For Each Geometry Element zone that allows executing nodes e.g. for each vertex separately"""
    bl_idname = "node.add_foreach_geometry_element_zone"
    bl_label = "Add For Each Geometry Element Zone"
    bl_options = {'REGISTER', 'UNDO'}

    input_node_type = "GeometryNodeForeachGeometryElementInput"
    output_node_type = "GeometryNodeForeachGeometryElementOutput"
    add_default_geometry_link = False


class NODE_OT_collapse_hide_unused_toggle(Operator):
    """Toggle collapsed nodes and hide unused sockets"""
    bl_idname = "node.collapse_hide_unused_toggle"
    bl_label = "Collapse and Hide Unused Sockets"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        space = context.space_data
        # needs active node editor and a tree
        return (space and (space.type == 'NODE_EDITOR') and
                (space.edit_tree and space.edit_tree.is_editable))

    def execute(self, context):
        space = context.space_data
        tree = space.edit_tree

        for node in tree.nodes:
            if node.select:
                hide = (not node.hide)

                node.hide = hide
                # Note: connected sockets are ignored internally
                for socket in node.inputs:
                    socket.hide = hide
                for socket in node.outputs:
                    socket.hide = hide

        return {'FINISHED'}


class NODE_OT_tree_path_parent(Operator):
    """Go to parent node tree"""
    bl_idname = "node.tree_path_parent"
    bl_label = "Parent Node Tree"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        space = context.space_data
        # needs active node editor and a tree
        return (space and (space.type == 'NODE_EDITOR') and len(space.path) > 1)

    def execute(self, context):
        space = context.space_data

        space.path.pop()

        return {'FINISHED'}


class NodeInterfaceOperator():
    @classmethod
    def poll(cls, context):
        space = context.space_data
        if not space or space.type != 'NODE_EDITOR' or not space.edit_tree:
            return False
        if space.edit_tree.is_embedded_data:
            return False
        return True


class NODE_OT_interface_item_new(Operator): # -bfa separated the add operators with their own descriptions.
    # Returns a valid socket type for the given tree or None.
    @staticmethod
    def find_valid_socket_type(tree):
        socket_type = 'NodeSocketFloat'
        # Socket type validation function is only available for custom
        # node trees. Assume that 'NodeSocketFloat' is valid for
        # built-in node tree types.
        if not hasattr(tree, "valid_socket_type") or tree.valid_socket_type(socket_type):
            return socket_type
        # Custom nodes may not support float sockets, search all
        # registered socket subclasses.
        types_to_check = [bpy.types.NodeSocket]
        while types_to_check:
            t = types_to_check.pop()
            idname = getattr(t, "bl_idname", "")
            if tree.valid_socket_type(idname):
                return idname
            # Test all subclasses
            types_to_check.extend(t.__subclasses__())

    def execute(self, context):
        snode = context.space_data
        tree = snode.edit_tree
        interface = tree.interface

        # Remember active item and position to determine target position.
        active_item = interface.active
        active_pos = active_item.position if active_item else -1

        if self.item_type == 'INPUT':
            item = interface.new_socket("Socket", socket_type=self.find_valid_socket_type(tree), in_out='INPUT')
        elif self.item_type == 'OUTPUT':
            item = interface.new_socket("Socket", socket_type=self.find_valid_socket_type(tree), in_out='OUTPUT')
        elif self.item_type == 'PANEL':
            item = interface.new_panel("Panel")
        else:
            return {'CANCELLED'}

        if active_item:
            # Insert into active panel if possible, otherwise insert after active item.
            if active_item.item_type == 'PANEL' and item.item_type != 'PANEL':
                interface.move_to_parent(item, active_item, len(active_item.interface_items))
            else:
                interface.move_to_parent(item, active_item.parent, active_pos + 1)
        interface.active = item

        return {'FINISHED'}


class NODE_OT_interface_item_new_input(NODE_OT_interface_item_new):# -bfa separated add input operator with own description.
    """Add a new input socket"""
    bl_idname = "node.interface_item_new_input"
    bl_label = "New Input Socket"
    bl_options = {'REGISTER', 'UNDO'}

    item_type: EnumProperty(
        name="Item Type",
        items=(('INPUT', "Input", ""),),
        default='INPUT'
    )


class NODE_OT_interface_item_new_panel(NODE_OT_interface_item_new):# -bfa separated add output operator with own description.
    """Add a new panel interface"""
    bl_idname = "node.interface_item_new_panel"
    bl_label = "New Panel Interface"
    bl_options = {'REGISTER', 'UNDO'}

    item_type: EnumProperty(
        name="Item Type",
        items=(('PANEL', "Panel", ""),),
        default='PANEL'
    )


class NODE_OT_interface_item_new_output(NODE_OT_interface_item_new):# -bfa separated add panel operator with own description.
    """Add a new output socket"""
    bl_idname = "node.interface_item_new_output"
    bl_label = "New Output Socket"
    bl_options = {'REGISTER', 'UNDO'}

    item_type: EnumProperty(
        name="Item Type",
        items=(('OUTPUT', "Output", ""),),
        default='OUTPUT'
    )


class NODE_OT_interface_item_duplicate(NodeInterfaceOperator, Operator):
    """Add a copy of the active item to the interface"""
    bl_idname = "node.interface_item_duplicate"
    bl_label = "Duplicate Item"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if not super().poll(context):
            return False

        snode = context.space_data
        tree = snode.edit_tree
        interface = tree.interface
        return interface.active is not None

    def execute(self, context):
        snode = context.space_data
        tree = snode.edit_tree
        interface = tree.interface
        item = interface.active

        if item:
            item_copy = interface.copy(item)
            interface.active = item_copy

        return {'FINISHED'}


class NODE_OT_interface_item_remove(NodeInterfaceOperator, Operator):
    """Remove active item from the interface"""
    bl_idname = "node.interface_item_remove"
    bl_label = "Remove Item"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        snode = context.space_data
        tree = snode.edit_tree
        interface = tree.interface
        item = interface.active

        if item:
            interface.remove(item)
            interface.active_index = min(interface.active_index, len(interface.items_tree) - 1)

        return {'FINISHED'}

## BFA - BFA operator for GUI buttons to re-order items - Start
class NODE_OT_interface_item_move(NodeInterfaceOperator, Operator):
    """Move the active item to the specified direction\nYou can also alternatively drag and drop the active item to reorder"""
    bl_idname = "node.interface_item_move"
    bl_label = "Move Item"
    bl_options = {'REGISTER', 'UNDO'}

    direction: EnumProperty(
        name="Direction",
        description="Specifies which direction the active item is moved towards",
        items=(
            ('UP', "Move Up", ""),
            ('DOWN', "Move Down", "")
        ),
    )

    @classmethod
    def poll(cls, context):
        if not super().poll(context):
            return False

        snode = context.space_data
        tree = snode.edit_tree
        interface = tree.interface
        return interface.active is not None

    @staticmethod
    def fetch_all_parents(interface):
        # The root panel that sockets are parented to by default is not directly accessible
        # Hence we retrieve it by creating a new socket and getting its parent
        new_socket = interface.new_socket(name="DUMMY_SOCKET")
        yield new_socket.parent
        interface.remove(new_socket)

        # Retrieve all other panels
        for item in interface.items_tree:
            if item.item_type == 'PANEL':
                yield item

    @staticmethod
    def get_prev_parent(parents, current_parent):
        prev_parent = parents[0]

        for parent in parents:
            if parent == current_parent:
                break

            prev_parent = parent

        return prev_parent

    @staticmethod
    def get_next_parent(parents, current_parent):
        iter_parents = iter(parents)
        for parent in iter_parents:
            if parent == current_parent:
                break

        try:
            next_parent = next(iter_parents)
        except StopIteration:
            next_parent = parent

        return next_parent

    def execute(self, context):
        interface = context.space_data.edit_tree.interface
        active_item = interface.active

        offset = -1 if self.direction == 'UP' else 2

        old_position = active_item.position
        interface.move(active_item, active_item.position + offset)

        if active_item.position == old_position and active_item.item_type == 'SOCKET':
            parents = tuple(self.fetch_all_parents(interface))

            if self.direction == 'UP':
                new_parent = self.get_prev_parent(parents, active_item.parent)
                new_position = len(new_parent.interface_items)
            else:
                new_parent = self.get_next_parent(parents, active_item.parent)
                new_position = 0

            if new_parent != active_item.parent:
                interface.move_to_parent(active_item, new_parent, new_position)
            else:
                return {'CANCELLED'}

        interface.active_index = active_item.index
        return {'FINISHED'}
## BFA - BFA operator for GUI buttons to re-order items - End

class NODE_FH_image_node(FileHandler):
    bl_idname = "NODE_FH_image_node"
    bl_label = "Image node"
    bl_import_operator = "node.add_file"
    bl_file_extensions = ";".join((*bpy.path.extensions_image, *bpy.path.extensions_movie))

    @classmethod
    def poll_drop(cls, context):
        return (
            (context.area is not None) and
            (context.area.type == 'NODE_EDITOR') and
            (context.region is not None) and
            (context.region.type == 'WINDOW')
        )


classes = (
    NodeSetting,

    NODE_FH_image_node,

    NODE_OT_add_node,
    NODE_OT_add_simulation_zone,
    NODE_OT_add_repeat_zone,
    NODE_OT_add_foreach_geometry_element_zone,
    NODE_OT_collapse_hide_unused_toggle,
    NODE_OT_interface_item_new_input, # BFA separated add input operator with own description.
    NODE_OT_interface_item_new_output, # BFA separated add output operator with own description.
    NODE_OT_interface_item_new_panel, # BFA separated add panel operator with own description.
    NODE_OT_interface_item_duplicate,
    NODE_OT_interface_item_remove,
    NODE_OT_interface_item_move, # BFA operator for GUI buttons to re-order items
    NODE_OT_tree_path_parent,
)
