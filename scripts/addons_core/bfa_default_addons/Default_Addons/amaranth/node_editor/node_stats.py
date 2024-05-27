# SPDX-FileCopyrightText: 2010-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
Nodes Stats

Display the number of selected and total nodes on the compositor. On the
Compositing Nodes Editor.
"""

import bpy


def node_stats(self, context):
    if context.scene.node_tree:
        tree_type = context.space_data.tree_type
        nodes = context.scene.node_tree.nodes
        nodes_total = len(nodes.keys())
        nodes_selected = 0
        for n in nodes:
            if n.select:
                nodes_selected = nodes_selected + 1

        if tree_type == 'CompositorNodeTree':
            layout = self.layout
            row = layout.row(align=True)
            row.label(text="Nodes: %s/%s" % (nodes_selected, str(nodes_total)))


def register():
    bpy.types.NODE_HT_header.append(node_stats)


def unregister():
    bpy.types.NODE_HT_header.remove(node_stats)
