# SPDX-License-Identifier: GPL-2.0-or-later

from __future__ import annotations

from collections.abc import Iterable, Sequence
from itertools import chain
from statistics import fmean
from typing import cast

import blf
import bpy
import networkx as nx
from bpy.types import Node as BlenderNode
from bpy.types import NodeFrame, NodeTree
from mathutils import Vector

from .. import config
from ..utils import abs_loc, get_ntree, group_by
from .graph import (
  FROM_SOCKET,
  TO_SOCKET,
  Cluster,
  ClusterGraph,
  Kind,
  Node,
  Socket,
  get_reroute_paths,
  is_real,
  node_name,
)
from .ordering import minimize_crossings
from .ranking import compute_ranks
from .realize import realize_layout, remove_reroutes
from .stacking import contracted_node_stacks, expand_node_stack
from .x_coords import assign_x_coords, route_edges
from .y_coords import bk_assign_y_coords

# -------------------------------------------------------------------


def get_display_name_of(node: BlenderNode) -> str:
    if node.label:
        return node.label

    if node.bl_idname.endswith('NodeGroup') and node.node_tree:  # type: ignore
        return node.node_tree.name  # type: ignore

    if node.bl_idname.endswith('Math') or node.bl_idname == 'FunctionNodeCompare':
        return node.operation  # type: ignore

    relevant_node_types = {'ShaderNodeTexImage', 'ShaderNodeTexEnvironment', 'CompositorNodeImage'}
    if node.bl_idname in relevant_node_types and node.image:  # type: ignore
        return node.image.name  # type: ignore

    return node.bl_label


NODE_LABEL_SIZE = 11
LABEL_LEFT_OFFSET = 23
LABEL_RIGHT_OFFSET = LABEL_LEFT_OFFSET


def optimize_sizes(nodes: Iterable[BlenderNode]) -> None:
    blf.size(0, NODE_LABEL_SIZE)

    for node in nodes:
        if not node.hide:
            continue

        display_name = get_display_name_of(node)
        optimized_width = (
          blf.dimensions(0, display_name)[0] + LABEL_LEFT_OFFSET + LABEL_RIGHT_OFFSET)
        node.width = max(optimized_width, node.bl_width_min)

    bpy.ops.wm.redraw_timer(type='DRAW', iterations=0)


# -------------------------------------------------------------------


def precompute_links(ntree: NodeTree) -> None:

    # Precompute links to ignore invalid/hidden links, and avoid `O(len(ntree.links))` time

    for link in ntree.links:
        if not link.is_hidden and link.is_valid:
            config.linked_sockets[link.to_socket].add(link.from_socket)
            config.linked_sockets[link.from_socket].add(link.to_socket)


def get_multidigraph() -> nx.MultiDiGraph[Node]:
    parents = {
      n.parent: Cluster(cast(NodeFrame | None, n.parent), None)  # type: ignore
      for n in get_ntree().nodes}
    for c in parents.values():
        if c.node:
            c.cluster = parents[c.node.parent]

    G = nx.MultiDiGraph()
    G.add_nodes_from([
      Node(n, parents[n.parent]) for n in config.selected if n.bl_idname != 'NodeFrame'])
    for u in G:
        for i, from_output in enumerate(u.node.outputs):
            for to_input in config.linked_sockets[from_output]:
                if not to_input.node.select:
                    continue

                v = next(v for v in G if v.node == to_input.node)
                j = to_input.node.inputs[:].index(to_input)
                G.add_edge(u, v, from_socket=Socket(u, i, True), to_socket=Socket(v, j, False))

    return G


def save_multi_input_orders(G: nx.MultiDiGraph[Node]) -> None:
    links = {(l.from_socket, l.to_socket): l for l in get_ntree().links}
    for v, w, d in G.edges.data():
        to_socket = d[TO_SOCKET]

        if not to_socket.bpy.is_multi_input:
            continue

        if v.is_reroute:
            for z, u in chain([(w, v)], nx.bfs_edges(G, v, reverse=True)):
                if not u.is_reroute:
                    break
            base_from_socket = G.edges[u, z, 0][FROM_SOCKET]
        else:
            base_from_socket = d[FROM_SOCKET]

        link = links[(d[FROM_SOCKET].bpy, to_socket.bpy)]
        config.multi_input_sort_ids[to_socket].append((base_from_socket, link.multi_input_sort_id))


def add_columns(G: nx.DiGraph[Node]) -> None:
    columns = [list(c) for c in group_by(G, key=lambda v: v.rank, sort=True)]
    G.graph['columns'] = columns

    y_loc = lambda v: abs_loc(v.node).y if is_real(v) and nx.is_isolate(G, v) else 0
    for col in columns:
        col.sort(key=node_name)
        col.sort(key=y_loc, reverse=True)
        for v in col:
            v.col = col


def dissolve_dummy_nodes(CG: ClusterGraph) -> None:
    paths = get_reroute_paths(
      CG,
      lambda v: v.is_reroute and not is_real(v),
      preserve_reroute_clusters=False,
    )
    G = CG.G
    for path in paths:
        if G.pred[path[0]]:
            u, _, o = next(iter(G.in_edges(path[0], data=FROM_SOCKET)))
            succ_inputs = [e[2] for e in G.out_edges(path[-1], data=TO_SOCKET)]
            for i in succ_inputs:
                G.add_edge(u, i.owner, from_socket=o, to_socket=i)

        CG.remove_nodes_from(path)


# -------------------------------------------------------------------


def get_foreign_sockets_of(path: Sequence[Node], G: nx.DiGraph[Node]) -> list[Socket]:
    inputs = G.in_edges(path[0], data=FROM_SOCKET)
    outputs = G.out_edges(path[-1], data=TO_SOCKET)
    return [e[2] for e in chain(inputs, outputs)]


def align_reroutes_with_sockets(CG: ClusterGraph) -> None:
    reroute_paths: dict[tuple[Node, ...], list[Socket]] = {}
    for p in get_reroute_paths(CG, preserve_reroute_clusters=False, aligned=True, linear=False):
        reroute_paths[tuple(p)] = get_foreign_sockets_of(p, CG.G)

    reroute_path_of = {v: p for p in reroute_paths for v in p}

    while True:
        changed = False
        for p1, foreign_sockets in tuple(reroute_paths.items()):
            if p1 not in reroute_paths:
                continue

            y = p1[0].y
            foreign_sockets.sort(key=lambda s: abs(y - s.y))
            foreign_sockets.sort(key=lambda s: y == s.owner.y, reverse=True)
            foreign_sockets.sort(key=lambda s: s.owner.is_reroute, reverse=True)

            if not foreign_sockets or y == foreign_sockets[0].y:
                del reroute_paths[p1]
                continue

            movement = y - foreign_sockets[0].y
            y -= movement
            if movement < 0:
                above_y_vals = [
                  (n := v.col[v.col.index(v) - 1]).y - n.height for v in p1 if v != v.col[0]]
                if above_y_vals and y > min(above_y_vals) - config.MARGIN.y:
                    continue
            else:
                below_y_vals = [v.col[v.col.index(v) + 1].y for v in p1 if v != v.col[-1]]
                if below_y_vals and max(below_y_vals) + config.MARGIN.y > y - p1[0].height:
                    continue

            for v in p1:
                v.y -= movement

            w = foreign_sockets[0].owner
            if w.is_reroute:
                p2 = reroute_path_of[w]
                p3 = p1 + p2 if w.rank > p1[-1].rank else p2 + p1
                reroute_paths[p3] = get_foreign_sockets_of(p3, CG.G)
                del reroute_paths[p1]
                reroute_paths.pop(p2, None)
                for v in p3:
                    reroute_path_of[v] = p3

            changed = True

        if not changed:
            if reroute_paths:
                for foreign_sockets in reroute_paths.values():
                    del foreign_sockets[0]
            else:
                break


# -------------------------------------------------------------------


def sugiyama_layout(ntree: NodeTree) -> None:
    locs = [abs_loc(n) for n in config.selected if n.bl_idname != 'NodeFrame']

    if not locs:
        return

    old_center = Vector(map(fmean, zip(*locs)))

    if config.SETTINGS.optimize_sizes:
        optimize_sizes(config.selected)

    precompute_links(ntree)
    CG = ClusterGraph(get_multidigraph())
    G = CG.G
    T = CG.T

    save_multi_input_orders(G)
    if config.SETTINGS.add_reroutes:
        remove_reroutes(CG)

    if config.SETTINGS.stack_collapsed:
        node_stacks = contracted_node_stacks(CG)

    compute_ranks(CG)
    CG.merge_edges()
    CG.insert_dummy_nodes()

    add_columns(G)
    minimize_crossings(G, T)

    CG.add_vertical_border_nodes()
    CG.remove_nodes_from([v for v in G if v.is_fill_dummy])
    bk_assign_y_coords(G, T)

    if not config.SETTINGS.add_reroutes:
        dissolve_dummy_nodes(CG)

    align_reroutes_with_sockets(CG)
    CG.remove_nodes_from([v for v in G if v.type == Kind.VERTICAL_BORDER])
    assign_x_coords(G, T)
    if config.SETTINGS.add_reroutes:
        route_edges(G, T)

    if config.SETTINGS.stack_collapsed:
        for node_stack in node_stacks:
            expand_node_stack(CG, node_stack)

    realize_layout(CG, old_center)
