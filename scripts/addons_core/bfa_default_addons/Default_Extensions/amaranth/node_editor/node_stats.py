# SPDX-FileCopyrightText: 2010-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
Nodes Stats

Display the number of selected and total nodes in the compositor.
"""

import bpy
from ..utils import is_blender_version_4

def node_stats(self, context):
    scene = context.scene
    is_compositor = context.space_data.tree_type == 'CompositorNodeTree'
    node_tree = scene.node_tree if is_blender_version_4() else scene.compositing_node_group

    if is_compositor == 'CompositorNodeTree' and node_tree:
        nodes = node_tree.nodes
        skip_node_types = ['REROUTE', 'FRAME']
        nodes_total = len([n for n in nodes if n.type not in skip_node_types])
        nodes_selected = 0

        for n in nodes:
            if n.type in skip_node_types:
                continue

            if n.select:
                nodes_selected = nodes_selected + 1

        layout = self.layout
        row = layout.row(align=True)
        row.label(text="Nodes: %s/%s" % (nodes_selected, str(nodes_total)))


def register():
    bpy.types.NODE_HT_header.append(node_stats)


def unregister():
    bpy.types.NODE_HT_header.remove(node_stats)
