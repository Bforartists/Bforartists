# SPDX-FileCopyrightText: 2013-2023 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
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
        return (
            context.space_data.type == 'NODE_EDITOR' and
            context.space_data.tree_type == 'CompositorNodeTree'
        )


class ShaderNodeCategory(SortedNodeCategory):
    @classmethod
    def poll(cls, context):
        return (
            context.space_data.type == 'NODE_EDITOR' and
            context.space_data.tree_type == 'ShaderNodeTree'
        )


# Menu entry for node group tools.
def group_tools_draw(_self, layout, _context):
    layout.operator("node.group_make", icon = "NODE_MAKEGROUP") # BFA icon
    layout.operator("node.group_insert", text = " Insert into Group ", icon = "NODE_GROUPINSERT") # BFA icon
    layout.operator("node.group_ungroup", icon = "NODE_UNGROUP") # BFA icon
    layout.separator()
    layout.operator("node.group_edit", text = " Toggle Edit Group", icon = "NODE_EDITGROUP").exit = False # BFA icon
    layout.separator()


# Maps node tree type to group node type.
node_tree_group_type = {
    'CompositorNodeTree': 'CompositorNodeGroup',
    'ShaderNodeTree': 'ShaderNodeGroup',
    'TextureNodeTree': 'TextureNodeGroup',
    'GeometryNodeTree': 'GeometryNodeGroup',
}


def register():
    pass


def unregister():
    pass
