# SPDX-FileCopyrightText: 2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy_extras.node_utils import connect_sockets
from math import hypot


def force_update(context):
    context.space_data.node_tree.update_tag()


def dpi_fac():
    prefs = bpy.context.preferences.system
    return prefs.dpi / 72


def prefs_line_width():
    prefs = bpy.context.preferences.system
    return prefs.pixel_size


def node_mid_pt(node, axis):
    if axis == 'x':
        d = node.location.x + (node.dimensions.x / 2)
    elif axis == 'y':
        d = node.location.y - (node.dimensions.y / 2)
    else:
        d = 0
    return d


def autolink(node1, node2, links):
    available_inputs = [inp for inp in node2.inputs if inp.enabled]
    available_outputs = [outp for outp in node1.outputs if outp.enabled]
    for outp in available_outputs:
        for inp in available_inputs:
            if not inp.is_linked and inp.name == outp.name:
                connect_sockets(outp, inp)
                return True

    for outp in available_outputs:
        for inp in available_inputs:
            if not inp.is_linked and inp.type == outp.type:
                connect_sockets(outp, inp)
                return True

    # force some connection even if the type doesn't match
    if available_outputs:
        for inp in available_inputs:
            if not inp.is_linked:
                connect_sockets(available_outputs[0], inp)
                return True

    # even if no sockets are open, force one of matching type
    for outp in available_outputs:
        for inp in available_inputs:
            if inp.type == outp.type:
                connect_sockets(outp, inp)
                return True

    # do something!
    for outp in available_outputs:
        for inp in available_inputs:
            connect_sockets(outp, inp)
            return True

    print("Could not make a link from " + node1.name + " to " + node2.name)
    return False


def abs_node_location(node):
    abs_location = node.location
    if node.parent is None:
        return abs_location
    return abs_location + abs_node_location(node.parent)


def node_at_pos(nodes, context, event):
    nodes_under_mouse = []
    target_node = None

    store_mouse_cursor(context, event)
    x, y = context.space_data.cursor_location

    # Make a list of each corner (and middle of border) for each node.
    # Will be sorted to find nearest point and thus nearest node
    node_points_with_dist = []
    for node in nodes:
        skipnode = False
        if node.type != 'FRAME':  # no point trying to link to a frame node
            dimx = node.dimensions.x / dpi_fac()
            dimy = node.dimensions.y / dpi_fac()
            locx, locy = abs_node_location(node)

            if not skipnode:
                node_points_with_dist.append([node, hypot(x - locx, y - locy)])  # Top Left
                node_points_with_dist.append([node, hypot(x - (locx + dimx), y - locy)])  # Top Right
                node_points_with_dist.append([node, hypot(x - locx, y - (locy - dimy))])  # Bottom Left
                node_points_with_dist.append([node, hypot(x - (locx + dimx), y - (locy - dimy))])  # Bottom Right

                node_points_with_dist.append([node, hypot(x - (locx + (dimx / 2)), y - locy)])  # Mid Top
                node_points_with_dist.append([node, hypot(x - (locx + (dimx / 2)), y - (locy - dimy))])  # Mid Bottom
                node_points_with_dist.append([node, hypot(x - locx, y - (locy - (dimy / 2)))])  # Mid Left
                node_points_with_dist.append([node, hypot(x - (locx + dimx), y - (locy - (dimy / 2)))])  # Mid Right

    nearest_node = sorted(node_points_with_dist, key=lambda k: k[1])[0][0]

    for node in nodes:
        if node.type != 'FRAME' and skipnode == False:
            locx, locy = abs_node_location(node)
            dimx = node.dimensions.x / dpi_fac()
            dimy = node.dimensions.y / dpi_fac()
            if (locx <= x <= locx + dimx) and \
               (locy - dimy <= y <= locy):
                nodes_under_mouse.append(node)

    if len(nodes_under_mouse) == 1:
        if nodes_under_mouse[0] != nearest_node:
            target_node = nodes_under_mouse[0]  # use the node under the mouse if there is one and only one
        else:
            target_node = nearest_node  # else use the nearest node
    else:
        target_node = nearest_node
    return target_node


def store_mouse_cursor(context, event):
    space = context.space_data
    v2d = context.region.view2d
    tree = space.edit_tree

    # convert mouse position to the View2D for later node placement
    if context.region.type == 'WINDOW':
        space.cursor_location_from_region(event.mouse_region_x, event.mouse_region_y)
    else:
        space.cursor_location = tree.view_center


def get_active_tree(context):
    tree = context.space_data.node_tree
    path = []
    # Get nodes from currently edited tree.
    # If user is editing a group, space_data.node_tree is still the base level (outside group).
    # context.active_node is in the group though, so if space_data.node_tree.nodes.active is not
    # the same as context.active_node, the user is in a group.
    # Check recursively until we find the real active node_tree:
    if tree.nodes.active:
        while tree.nodes.active != context.active_node:
            tree = tree.nodes.active.node_tree
            path.append(tree)
    return tree, path


def get_nodes_links(context):
    tree, path = get_active_tree(context)
    return tree.nodes, tree.links


viewer_socket_name = "tmp_viewer"


def is_viewer_socket(socket):
    # checks if a internal socket is a valid viewer socket
    return socket.name == viewer_socket_name and socket.NWViewerSocket


def get_internal_socket(socket):
    # get the internal socket from a socket inside or outside the group
    node = socket.node
    if node.type == 'GROUP_OUTPUT':
        iterator = node.id_data.interface.items_tree
    elif node.type == 'GROUP_INPUT':
        iterator = node.id_data.interface.items_tree
    elif hasattr(node, "node_tree"):
        iterator = node.node_tree.interface.items_tree
    else:
        return None

    for s in iterator:
        if s.identifier == socket.identifier:
            return s
    return iterator[0]


def is_viewer_link(link, output_node):
    if link.to_node == output_node and link.to_socket == output_node.inputs[0]:
        return True
    if link.to_node.type == 'GROUP_OUTPUT':
        socket = get_internal_socket(link.to_socket)
        if is_viewer_socket(socket):
            return True
    return False


def get_group_output_node(tree):
    for node in tree.nodes:
        if node.type == 'GROUP_OUTPUT' and node.is_active_output:
            return node


def get_output_location(tree):
    # get right-most location
    sorted_by_xloc = (sorted(tree.nodes, key=lambda x: x.location.x))
    max_xloc_node = sorted_by_xloc[-1]

    # get average y location
    sum_yloc = 0
    for node in tree.nodes:
        sum_yloc += node.location.y

    loc_x = max_xloc_node.location.x + max_xloc_node.dimensions.x + 80
    loc_y = sum_yloc / len(tree.nodes)
    return loc_x, loc_y


def nw_check(context):
    space = context.space_data
    valid_trees = ["ShaderNodeTree", "CompositorNodeTree", "TextureNodeTree", "GeometryNodeTree"]

    if (space.type == 'NODE_EDITOR'
            and space.node_tree is not None
            and space.node_tree.library is None
            and space.tree_type in valid_trees):
        return True

    return False


def get_first_enabled_output(node):
    for output in node.outputs:
        if output.enabled:
            return output
    else:
        return node.outputs[0]


def is_visible_socket(socket):
    return not socket.hide and socket.enabled and socket.type != 'CUSTOM'


class NWBase:
    @classmethod
    def poll(cls, context):
        return nw_check(context)
