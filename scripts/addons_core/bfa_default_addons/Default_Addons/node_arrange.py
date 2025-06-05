# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Node Arrange",
    "author": "JuhaW",
    "version": (0, 2, 2),
    "blender": (2, 80, 4),
    "location": "Node Editor > Properties > Trees",
    "description": "Node Tree Arrangement Tools",
    "warning": "",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/node/node_arrange.html",
    "tracker_url": "https://github.com/JuhaW/NodeArrange/issues",
    "category": "Node"
}


import sys
import bpy
from collections import OrderedDict
from itertools import repeat
import pprint
import pdb
from bpy.types import Operator, Panel
from bpy.props import (
    IntProperty,
)
from copy import copy


#From Node Wrangler
def get_nodes_linked(context):
    tree = context.space_data.node_tree

    # Get nodes from currently edited tree.
    # If user is editing a group, space_data.node_tree is still the base level (outside group).
    # context.active_node is in the group though, so if space_data.node_tree.nodes.active is not
    # the same as context.active_node, the user is in a group.
    # Check recursively until we find the real active node_tree:
    if tree.nodes.active:
        while tree.nodes.active != context.active_node:
            tree = tree.nodes.active.node_tree

    return tree.nodes, tree.links

class NA_OT_AlignNodes(Operator):
    '''Align the selected nodes/Tidy loose nodes'''
    bl_idname = "node.na_align_nodes"
    bl_label = "Align Nodes"
    bl_options = {'REGISTER', 'UNDO'}
    margin: IntProperty(name='Margin', default=50, description='The amount of space between nodes')

    def execute(self, context):
        nodes, links = get_nodes_linked(context)
        margin = self.margin

        selection = []
        for node in nodes:
            if node.select and node.type != 'FRAME':
                selection.append(node)

        # If no nodes are selected, align all nodes
        active_loc = None
        if not selection:
            selection = nodes
        elif nodes.active in selection:
            active_loc = copy(nodes.active.location)  # make a copy, not a reference

        # Check if nodes should be laid out horizontally or vertically
        x_locs = [n.location.x + (n.dimensions.x / 2) for n in selection]  # use dimension to get center of node, not corner
        y_locs = [n.location.y - (n.dimensions.y / 2) for n in selection]
        x_range = max(x_locs) - min(x_locs)
        y_range = max(y_locs) - min(y_locs)
        mid_x = (max(x_locs) + min(x_locs)) / 2
        mid_y = (max(y_locs) + min(y_locs)) / 2
        horizontal = x_range > y_range

        # Sort selection by location of node mid-point
        if horizontal:
            selection = sorted(selection, key=lambda n: n.location.x + (n.dimensions.x / 2))
        else:
            selection = sorted(selection, key=lambda n: n.location.y - (n.dimensions.y / 2), reverse=True)

        # Alignment
        current_pos = 0
        for node in selection:
            current_margin = margin
            current_margin = current_margin * 0.5 if node.hide else current_margin  # use a smaller margin for hidden nodes

            if horizontal:
                node.location.x = current_pos
                current_pos += current_margin + node.dimensions.x
                node.location.y = mid_y + (node.dimensions.y / 2)
            else:
                node.location.y = current_pos
                current_pos -= (current_margin * 0.3) + node.dimensions.y  # use half-margin for vertical alignment
                node.location.x = mid_x - (node.dimensions.x / 2)

        # If active node is selected, center nodes around it
        if active_loc is not None:
            active_loc_diff = active_loc - nodes.active.location
            for node in selection:
                node.location += active_loc_diff
        else:  # Position nodes centered around where they used to be
            locs = ([n.location.x + (n.dimensions.x / 2) for n in selection]) if horizontal else ([n.location.y - (n.dimensions.y / 2) for n in selection])
            new_mid = (max(locs) + min(locs)) / 2
            for node in selection:
                if horizontal:
                    node.location.x += (mid_x - new_mid)
                else:
                    node.location.y += (mid_y - new_mid)

        return {'FINISHED'}

class values():
    average_y = 0
    x_last = 0
    margin_x = 100
    mat_name = ""
    margin_y = 20


class NA_PT_NodePanel(Panel):
    bl_label = "Node Arrange"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Arrange"

    def draw(self, context):
        if context.active_node is not None:
            layout = self.layout
            row = layout.row()
            col = layout.column
            row.operator('node.button')

            row = layout.row()
            row.prop(bpy.context.scene, 'nodemargin_x', text="Margin x")
            row = layout.row()
            row.prop(bpy.context.scene, 'nodemargin_y', text="Margin y")
            row = layout.row()
            row.prop(context.scene, 'node_center', text="Center nodes")

            row = layout.row()
            row.operator('node.na_align_nodes', text="Align to Selected")

            row = layout.row()
            node = context.space_data.node_tree.nodes.active
            if node and node.select:
                row.prop(node, 'location', text = "Node X", index = 0)
                row.prop(node, 'location', text = "Node Y", index = 1)
                row = layout.row()
                row.prop(node, 'width', text = "Node width")

            row = layout.row()
            row.operator('node.button_odd')

class NA_OT_NodeButton(Operator):

    '''Arrange Connected Nodes/Arrange All Nodes'''
    bl_idname = 'node.button'
    bl_label = 'Arrange All Nodes'

    def execute(self, context):
        nodemargin(self, context)
        bpy.context.space_data.node_tree.nodes.update()
        bpy.ops.node.view_all()

        return {'FINISHED'}

    # not sure this is doing what you expect.
    # blender.org/api/blender_python_api_current/bpy.types.Operator.html#invoke
    def invoke(self, context, value):
        values.mat_name = bpy.context.space_data.node_tree
        nodemargin(self, context)
        return {'FINISHED'}


class NA_OT_NodeButtonOdd(Operator):

    'Show the nodes for this material'
    bl_idname = 'node.button_odd'
    bl_label = 'Select Unlinked'

    def execute(self, context):
        values.mat_name = bpy.context.space_data.node_tree
        #mat = bpy.context.object.active_material
        nodes_iterate(context.space_data.node_tree, False)
        return {'FINISHED'}


class NA_OT_NodeButtonCenter(Operator):

    'Show the nodes for this material'
    bl_idname = 'node.button_center'
    bl_label = 'Center nodes (0,0)'

    def execute(self, context):
        values.mat_name = ""  # reset
        mat = bpy.context.object.active_material
        nodes_center(mat)
        return {'FINISHED'}


def nodemargin(self, context):

    values.margin_x = context.scene.nodemargin_x
    values.margin_y = context.scene.nodemargin_y

    ntree = context.space_data.node_tree

    #first arrange nodegroups
    n_groups = []
    for i in ntree.nodes:
        if i.type == 'GROUP':
            n_groups.append(i)

    while n_groups:
        j = n_groups.pop(0)
        nodes_iterate(j.node_tree)
        for i in j.node_tree.nodes:
            if i.type == 'GROUP':
                n_groups.append(i)

    nodes_iterate(ntree)

    # arrange nodes + this center nodes together
    if context.scene.node_center:
        nodes_center(ntree)


class NA_OT_ArrangeNodesOp(bpy.types.Operator):
    bl_idname = 'node.arrange_nodetree'
    bl_label = 'Nodes Private Op'

    mat_name : bpy.props.StringProperty()
    margin_x : bpy.props.IntProperty(default=120)
    margin_y : bpy.props.IntProperty(default=120)

    def nodemargin2(self, context):
        mat = None
        mat_found = bpy.data.materials.get(self.mat_name)
        if self.mat_name and mat_found:
            mat = mat_found
            #print(mat)

        if not mat:
            return
        else:
            values.mat_name = self.mat_name
            scn = context.scene
            scn.nodemargin_x = self.margin_x
            scn.nodemargin_y = self.margin_y
            nodes_iterate(mat)
            if scn.node_center:
                nodes_center(mat)

    def execute(self, context):
        self.nodemargin2(context)
        return {'FINISHED'}


def outputnode_search(ntree):    # return node/None

    outputnodes = []
    for node in ntree.nodes:
        if not node.outputs:
            for input in node.inputs:
                if input.is_linked:
                    outputnodes.append(node)
                    break

    if not outputnodes:
        print("No output node found")
        return None
    return outputnodes


###############################################################
def nodes_iterate(ntree, arrange=True):

    nodeoutput = outputnode_search(ntree)
    if nodeoutput is None:
        #print ("nodeoutput is None")
        return None
    a = []
    a.append([])
    for i in nodeoutput:
        a[0].append(i)


    level = 0

    while a[level]:
        a.append([])

        for node in a[level]:
            inputlist = [i for i in node.inputs if i.is_linked]

            if inputlist:

                for input in inputlist:
                    for nlinks in input.links:
                        node1 = nlinks.from_node
                        a[level + 1].append(node1)

            else:
                pass

        level += 1

    del a[level]
    level -= 1

    #remove duplicate nodes at the same level, first wins
    for x, nodes in enumerate(a):
        a[x] = list(OrderedDict(zip(a[x], repeat(None))))

    #remove duplicate nodes in all levels, last wins
    top = level
    for row1 in range(top, 1, -1):
        for col1 in a[row1]:
            for row2 in range(row1-1, 0, -1):
                for col2 in a[row2]:
                    if col1 == col2:
                        a[row2].remove(col2)
                        break

    """
    for x, i in enumerate(a):
        print (x)
        for j in i:
            print (j)
        #print()
    """
    """
    #add node frames to nodelist
    frames = []
    print ("Frames:")
    print ("level:", level)
    print ("a:",a)
    for row in range(level, 0, -1):

        for i, node in enumerate(a[row]):
            if node.parent:
                print ("Frame found:", node.parent, node)
                #if frame already added to the list ?
                frame = node.parent
                #remove node
                del a[row][i]
                if frame not in frames:
                    frames.append(frame)
                    #add frame to the same place than node was
                    a[row].insert(i, frame)

    pprint.pprint(a)
    """
    #return None
    ########################################



    if not arrange:
        nodelist = [j for i in a for j in i]
        nodes_odd(ntree, nodelist=nodelist)
        return None

    ########################################

    levelmax = level + 1
    level = 0
    values.x_last = 0

    while level < levelmax:

        values.average_y = 0
        nodes = [x for x in a[level]]
        #print ("level, nodes:", level, nodes)
        nodes_arrange(nodes, level)

        level = level + 1

    return None


###############################################################
def nodes_odd(ntree, nodelist):

    nodes = ntree.nodes
    for i in nodes:
        i.select = False

    a = [x for x in nodes if x not in nodelist]
    # print ("odd nodes:",a)
    for i in a:
        i.select = True


def nodes_arrange(nodelist, level):

    parents = []
    for node in nodelist:
        parents.append(node.parent)
        node.parent = None
        bpy.context.space_data.node_tree.nodes.update()


    #print ("nodes arrange def")
    # node x positions

    widthmax = max([x.dimensions.x for x in nodelist])
    xpos = values.x_last - (widthmax + values.margin_x) if level != 0 else 0
    #print ("nodelist, xpos", nodelist,xpos)
    values.x_last = xpos

    # node y positions
    x = 0
    y = 0

    for node in nodelist:

        if node.hide:
            hidey = (node.dimensions.y / 2) - 8
            y = y - hidey
        else:
            hidey = 0

        node.location.y = y
        y = y - values.margin_y - node.dimensions.y + hidey

        node.location.x = xpos #if node.type != "FRAME" else xpos + 1200

    y = y + values.margin_y

    center = (0 + y) / 2
    values.average_y = center - values.average_y

    #for node in nodelist:

        #node.location.y -= values.average_y

    for i, node in enumerate(nodelist):
        node.parent =  parents[i]

def nodetree_get(mat):

    return mat.node_tree.nodes


def nodes_center(ntree):

    bboxminx = []
    bboxmaxx = []
    bboxmaxy = []
    bboxminy = []

    for node in ntree.nodes:
        if not node.parent:
            bboxminx.append(node.location.x)
            bboxmaxx.append(node.location.x + node.dimensions.x)
            bboxmaxy.append(node.location.y)
            bboxminy.append(node.location.y - node.dimensions.y)

    # print ("bboxminy:",bboxminy)
    bboxminx = min(bboxminx)
    bboxmaxx = max(bboxmaxx)
    bboxminy = min(bboxminy)
    bboxmaxy = max(bboxmaxy)
    center_x = (bboxminx + bboxmaxx) / 2
    center_y = (bboxminy + bboxmaxy) / 2
    '''
    print ("minx:",bboxminx)
    print ("maxx:",bboxmaxx)
    print ("miny:",bboxminy)
    print ("maxy:",bboxmaxy)

    print ("bboxes:", bboxminx, bboxmaxx, bboxmaxy, bboxminy)
    print ("center x:",center_x)
    print ("center y:",center_y)
    '''

    x = 0
    y = 0

    for node in ntree.nodes:

        if not node.parent:
            node.location.x -= center_x
            node.location.y += -center_y

classes = [
    NA_PT_NodePanel,
    NA_OT_NodeButton,
    NA_OT_NodeButtonOdd,
    NA_OT_NodeButtonCenter,
    NA_OT_ArrangeNodesOp,
    NA_OT_AlignNodes
]

def register():
    for c in classes:
        bpy.utils.register_class(c)

    bpy.types.Scene.nodemargin_x = bpy.props.IntProperty(default=100, update=nodemargin)
    bpy.types.Scene.nodemargin_y = bpy.props.IntProperty(default=20, update=nodemargin)
    bpy.types.Scene.node_center = bpy.props.BoolProperty(default=True, update=nodemargin)



def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)

    del bpy.types.Scene.nodemargin_x
    del bpy.types.Scene.nodemargin_y
    del bpy.types.Scene.node_center

if __name__ == "__main__":
    register()
