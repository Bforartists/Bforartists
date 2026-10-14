# SPDX-License-Identifier: GPL-2.0-or-later

from __future__ import annotations

from itertools import chain
from math import isclose
from statistics import fmean

import networkx as nx
from bpy.types import Node as BlenderNode
from mathutils import Vector

from .. import config
from ..utils import get_ntree, move
from .graph import (
  FROM_SOCKET,
  TO_SOCKET,
  Cluster,
  ClusterGraph,
  Kind,
  Node,
  Socket,
  add_dummy_edge,
  get_reroute_paths,
  is_real,
  socket_graph,
)


def is_safe_to_remove(v: Node) -> bool:
    if not is_real(v):
        return True

    if v.node.label:
        return False

    for val in config.multi_input_sort_ids.values():
        if any(v == i[0].owner for i in val):
            return False

    return all(
      s.node.select for s in chain(
      config.linked_sockets[v.node.inputs[0]],
      config.linked_sockets[v.node.outputs[0]],
      ))


def dissolve_reroute_edges(G: nx.DiGraph[Node], path: list[Node]) -> None:
    if not G[path[-1]]:
        return

    try:
        u, _, o = next(iter(G.in_edges(path[0], data=FROM_SOCKET)))
    except StopIteration:
        return

    succ_inputs = [e[2] for e in G.out_edges(path[-1], data=TO_SOCKET)]

    # Check if a reroute has been used to link the same output to the same multi-input multiple
    # times
    for *_, d in G.out_edges(u, data=True):
        if d[FROM_SOCKET] == o and d[TO_SOCKET] in succ_inputs:
            path.clear()
            return

    links = get_ntree().links
    for i in succ_inputs:
        G.add_edge(u, i.owner, from_socket=o, to_socket=i)
        links.new(o.bpy, i.bpy)


def remove_reroutes(CG: ClusterGraph) -> None:
    reroute_clusters = {#
      c for c in CG.S
      if all(v.type != Kind.CLUSTER and v.is_reroute for v in CG.T[c])}
    for path in get_reroute_paths(CG, is_safe_to_remove):
        if path[0].cluster in reroute_clusters:
            if len(path) > 2:
                u, *between, v = path
                add_dummy_edge(CG.G, u, v)
                CG.remove_nodes_from(between)
        else:
            dissolve_reroute_edges(CG.G, path)
            CG.remove_nodes_from(path)


_Y_TOL = 5


def simplify_path(CG: ClusterGraph, path: list[Node]) -> None:
    G = CG.G
    pred_output = lambda w: next(iter(G.in_edges(w, data=FROM_SOCKET)))[2]
    succ_input = lambda w: next(iter(G.out_edges(w, data=TO_SOCKET)))[2]

    if len(path) == 1:
        v = path[0]

        if not G.pred[v] or G.out_degree[v] != 1 or v.col is None or is_real(v):
            return

        p = pred_output(v)
        q = succ_input(v)
        if isclose(p.y, q.y, rel_tol=0, abs_tol=_Y_TOL):
            G.add_edge(p.owner, q.owner, from_socket=p, to_socket=q)
            CG.remove_nodes_from(path)
            path.clear()

        return

    u, *between, v = path

    if G.pred[u] and isclose((p := pred_output(u)).y, u.y, rel_tol=0, abs_tol=_Y_TOL):
        between.append(u)
    else:
        p = Socket(u, 0, True)

    if G.out_degree[v] == 1 and isclose(v.y, (q := succ_input(v)).y, rel_tol=0, abs_tol=_Y_TOL):
        between.append(v)
    else:
        q = Socket(v, 0, False)

    if p.owner != u or q.owner != v or between:
        G.add_edge(p.owner, q.owner, from_socket=p, to_socket=q)

    CG.remove_nodes_from(between)
    for v in between:
        path.remove(v)


def add_reroute(v: Node) -> None:
    reroute = get_ntree().nodes.new(type='NodeReroute')
    assert v.cluster
    reroute.parent = v.cluster.node
    config.selected.append(reroute)
    v.node = reroute
    v.type = Kind.NODE


def realize_edges(G: nx.DiGraph[Node]) -> None:
    links = get_ntree().links
    for u, v, d in G.edges.data():
        if u.is_reroute or v.is_reroute:
            links.new(d[FROM_SOCKET].bpy, d[TO_SOCKET].bpy)


def realize_dummy_nodes(CG: ClusterGraph) -> None:
    for path in get_reroute_paths(CG, is_safe_to_remove, aligned=True):
        simplify_path(CG, path)

        for v in path:
            if not is_real(v):
                add_reroute(v)

    realize_edges(CG.G)


def restore_multi_input_orders(G: nx.MultiDiGraph[Node]) -> None:
    links = get_ntree().links
    H = socket_graph(G)
    for socket, sort_ids in config.multi_input_sort_ids.items():
        multi_input = socket.bpy
        assert multi_input

        as_links = {l.from_socket: l for l in links if l.to_socket == multi_input}

        for output in {s.bpy for s in H.pred[socket]} - as_links.keys():
            assert output
            as_links[output] = links.new(output, multi_input)

        if len(as_links) != len({l.multi_input_sort_id for l in as_links.values()}):
            for link in as_links.values():
                links.remove(link)

            for output in as_links:
                as_links[output] = links.new(output, multi_input)

        SH = H.subgraph({i[0] for i in sort_ids} | {socket} | {v for v in H if v.owner.is_reroute})
        seen = set()
        for base_from_socket, sort_id in sort_ids:
            other = min(as_links.values(), key=lambda l: abs(l.multi_input_sort_id - sort_id))
            from_socket = next(
              s for s, t in nx.edge_dfs(SH, base_from_socket) if t == socket and s not in seen)
            as_links[from_socket.bpy].swap_multi_input_sort_id(other)  # type: ignore
            seen.add(from_socket)


def realize_locations(G: nx.DiGraph[Node], old_center: Vector) -> None:
    new_center = (fmean([v.x for v in G]), fmean([v.y for v in G]))
    offset_x, offset_y = -Vector(new_center) + old_center

    for v in G:
        assert isinstance(v.node, BlenderNode)
        assert v.cluster

        # Optimization: avoid using bpy.ops for as many nodes as possible (see `utils.move()`)
        v.node.parent = None

        x, y = v.node.location
        v.x += offset_x
        v.y += offset_y
        move(v.node, x=v.x - x, y=v.corrected_y() - y)

        v.node.parent = v.cluster.node


def resize_unshrunken_frame(CG: ClusterGraph, cluster: Cluster) -> None:
    frame = cluster.node

    if not frame or frame.shrink:
        return

    real_children = [v for v in CG.T[cluster] if is_real(v)]

    for v in real_children:
        v.node.parent = None

    frame.shrink = False
    frame.shrink = True

    for v in real_children:
        v.node.parent = frame


def realize_layout(CG: ClusterGraph, old_center: Vector) -> None:
    if config.SETTINGS.add_reroutes:
        realize_dummy_nodes(CG)

    restore_multi_input_orders(CG.G)
    realize_locations(CG.G, old_center)
    for c in CG.S:
        resize_unshrunken_frame(CG, c)
