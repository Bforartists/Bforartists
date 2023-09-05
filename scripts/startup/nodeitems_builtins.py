# SPDX-FileCopyrightText: 2013-2023 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
import nodeitems_utils
from nodeitems_utils import (
    NodeCategory,
    NodeItem,
    NodeItemCustom,
)


# Subclasses for standard node types

class SortedNodeCategory(NodeCategory):
    def __init__(self, identifier, name, description="", items=None):
        # for builtin nodes the convention is to sort by name
        if isinstance(items, list):
            items = sorted(items, key=lambda item: item.label.lower())

        super().__init__(identifier, name, description=description, items=items)


class CompositorNodeCategory(SortedNodeCategory):
    @classmethod
    def poll(cls, context):
        return (context.space_data.type == 'NODE_EDITOR' and
                context.space_data.tree_type == 'CompositorNodeTree')


class ShaderNodeCategory(SortedNodeCategory):
    @classmethod
    def poll(cls, context):
        return (context.space_data.type == 'NODE_EDITOR' and
                context.space_data.tree_type == 'ShaderNodeTree')


# Menu entry for node group tools.
def group_tools_draw(_self, layout, _context):
    layout.operator("node.group_make")
    layout.operator("node.group_ungroup")
    layout.separator()


# Maps node tree type to group node type.
node_tree_group_type = {
    'CompositorNodeTree': 'CompositorNodeGroup',
    'ShaderNodeTree': 'ShaderNodeGroup',
    'TextureNodeTree': 'TextureNodeGroup',
    'GeometryNodeTree': 'GeometryNodeGroup',
}


# Generic node group items generator for shader, compositor, geometry and texture node groups.
def node_group_items(context):
    if context is None:
        return
    space = context.space_data
    if not space:
        return

    yield NodeItemCustom(draw=group_tools_draw)

    if group_input_output_item_poll(context):
        yield NodeItem("NodeGroupInput")
        yield NodeItem("NodeGroupOutput")

    ntree = space.edit_tree
    if not ntree:
        return

    yield NodeItemCustom(draw=lambda self, layout, context: layout.separator())

    for group in context.blend_data.node_groups:
        if group.bl_idname != ntree.bl_idname:
            continue
        # Filter out recursive groups.
        if group.contains_tree(ntree):
            continue
        # Filter out hidden node-trees.
        if group.name.startswith('.'):
            continue
        yield NodeItem(node_tree_group_type[group.bl_idname],
                       label=group.name,
                       settings={"node_tree": "bpy.data.node_groups[%r]" % group.name})


# only show input/output nodes inside node groups
def group_input_output_item_poll(context):
    space = context.space_data
    if space.edit_tree in bpy.data.node_groups.values():
        return True
    return False


def register():
    pass


def unregister():
    pass


if __name__ == "__main__":
    register()
