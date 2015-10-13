#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
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
