# SPDX-License-Identifier: GPL-2.0-or-later

from __future__ import annotations

from collections import deque
from collections.abc import Hashable, Iterable
from dataclasses import dataclass, field
from math import inf
from typing import TypeVar, cast

import networkx as nx

from .. import config
from ..utils import get_top
from .graph import (
  FROM_SOCKET,
  TO_SOCKET,
  Cluster,
  ClusterGraph,
  Edge,
  Kind,
  MultiEdge,
  Node,
  Socket,
  get_socket_y,
  is_real,
  node_name,
  opposite,
)


@dataclass(slots=True)
class NodeStack:
    rep_node: Node
    path: list[Node]
    stack_sockets_to_originals: dict[Socket, Socket] = field(default_factory=dict)


T = TypeVar('T', bound=Hashable)


# Adapted from NetworkX, to make it deterministic:
# https://github.com/networkx/networkx/blob/36e8a1ee85ca0ab4195a486451ca7d72153e2e00/networkx/algorithms/bipartite/matching.py#L59
def deterministic_hopcroft_karp_matching(G: nx.Graph[T], top_nodes: Iterable[T]) -> dict[T, T]:

    def bfs() -> bool:
        for u in pair_U:
            if pair_U[u] is None:
                dist[u] = 0
                Q.append(u)
            else:
                dist[u] = inf

        dist[None] = inf
        while Q:
            u = Q.popleft()
            if dist[u] < dist[None]:
                for v in G[u]:
                    if dist[pair_V[v]] == inf:
                        dist[pair_V[v]] = dist[u] + 1
                        Q.append(pair_V[v])

        return dist[None] != inf

    def dfs(u: T | None) -> bool:
        if u is None:
            return True

        for v in G[u]:
            if dist[pair_V[v]] == dist[u] + 1 and dfs(pair_V[v]):
                pair_V[v] = u
                pair_U[u] = v
                return True

        dist[u] = inf
        return False

    pair_U: dict[T, T | None] = {v: None for v in top_nodes}
    pair_V: dict[T, T | None] = {v: None for v in G if v not in pair_U}
    dist = {}
    Q = deque()

    while bfs():
        for u, v in pair_U.items():
            if v is None:
                dfs(u)

    return {k: v for k, v in (pair_U | pair_V).items() if v is not None}


def max_linear_branching(G: nx.MultiDiGraph[Node]) -> nx.MultiDiGraph[Node]:
    # To make results deterministic
    nodes = sorted(G, key=node_name)
    edges = sorted(G.edges(keys=False), key=lambda e: node_name(e[0]) + node_name(e[1]))

    out_nodes = [(v, 'out') for v in nodes]
    in_nodes = [(v, 'in') for v in nodes]

    B: nx.Graph[tuple[Node, str]] = nx.Graph()
    B.add_nodes_from(out_nodes, bipartite=0)
    B.add_nodes_from(in_nodes, bipartite=1)
    for u, v in edges:
        B.add_edge((u, 'out'), (v, 'in'))

    matching = deterministic_hopcroft_karp_matching(B, out_nodes)
    H = nx.MultiDiGraph()
    H.add_nodes_from(nodes)
    for u_out in out_nodes:
        if u_out in matching:
            H.add_edge(u_out[0], matching[u_out][0])

    return H


_WEIGHT = 'weight'


# http://dx.doi.org/10.1016/S0020-0190(02)00491-X
def minimum_feedback_arc_set(G: nx.MultiDiGraph[Node]) -> set[MultiEdge]:
    G_ = G.copy()
    while not nx.is_directed_acyclic_graph(G_):
        pairs = nx.utils.pairwise(next(nx.simple_cycles(G_)), cyclic=True)
        C = [(u, v, next(iter(G_[u][v]))) for u, v in pairs]
        min_weight = min([G.edges[e][_WEIGHT] for e in C])
        for e in C:
            d = G.edges[e]
            d[_WEIGHT] -= min_weight
            if d[_WEIGHT] == 0:
                G_.remove_edge(*e)

    for e in G.edges:
        if e in G_.edges:
            continue

        G_.add_edge(*e)
        if not nx.is_directed_acyclic_graph(G_):
            G_.remove_edge(*e)

    return set(G.edges - G_.edges)


def edges_preventing_acyclic_contraction(
  G: nx.MultiDiGraph[Node],
  K: nx.MultiDiGraph[Node],
) -> list[Edge]:
    G_ = G.copy()
    for u, v, k, d in tuple(G_.edges(data=True, keys=True)):
        if (u, v, k) in K.edges:
            d[_WEIGHT] = 1
            G_.remove_edge(u, v, k)
            G_.add_edge(v, u, k, **d)
        else:
            d[_WEIGHT] = inf

    F = minimum_feedback_arc_set(G_)
    return [(v, u) for u, v, _ in F]


def relabel_sockets(
  edges: nx.classes.reportviews.OutMultiEdgeView[Node],
  v: Node,
  node_stack: NodeStack,
  y: float,
) -> None:
    assert is_real(v)
    external_edges = [#
      (u, w, d) for u, w, d in edges(v, data=True)
      if opposite(v, (u, w)) not in node_stack.path]

    if not external_edges:
        return

    is_output = external_edges[0][0] == v
    attr = FROM_SOCKET if is_output else TO_SOCKET
    external_edges.sort(key=lambda e: e[2][attr].idx)

    for *_, d in external_edges:
        sockets = node_stack.stack_sockets_to_originals
        i = max([s.idx for s in sockets], default=-1) + 1
        socket = Socket(
          node_stack.rep_node,
          i,
          is_output,
          get_socket_y(d[attr].bpy) - get_top(v.node) - y,
        )
        sockets[socket] = d[attr]
        d[attr] = socket


def contracted_node_stacks(CG: ClusterGraph) -> list[NodeStack]:
    G = CG.G
    T = CG.T

    collapsed_math_nodes = [ # yapf: disable
      v for v in G
      if is_real(v)
      and v.node.hide
      and v.node.bl_idname in {'ShaderNodeMath', 'ShaderNodeVectorMath'}]
    H: nx.MultiDiGraph[Node] = nx.MultiDiGraph(G.subgraph(collapsed_math_nodes))

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    H.remove_edges_from([(u, v, k) for u, v, k in H.edges if u.cluster != v.cluster])

    for u, a in H.adj.copy().items():
        for v, d in a.items():
            if len(d) > 1:
                H.remove_edges_from([(u, v, k) for k in d])  # type: ignore

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    for c in nx.weakly_connected_components(H):
        H_c = H.subgraph(c)
        B = max_linear_branching(H_c)  # type: ignore
        H.remove_edges_from(H_c.edges - B.edges)

    for c in nx.weakly_connected_components(H):
        H.remove_edges_from(edges_preventing_acyclic_contraction(G, H.subgraph(c)))  # type: ignore

    H.remove_edges_from(edges_preventing_acyclic_contraction(G, H))

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    order = {v: i for i, v in enumerate(nx.topological_sort(H))}
    node_stacks = []
    for c in nx.weakly_connected_components(H):
        if len(c) == 1:
            continue

        rep_node = Node(type=Kind.STACK)
        path: list[Node] = sorted(c, key=order.get)  # type: ignore
        node_stack = NodeStack(rep_node, path)

        y = 0
        for v in path:
            relabel_sockets(G.in_edges, v, node_stack, y)
            relabel_sockets(G.out_edges, v, node_stack, y)
            y += v.height + config.MARGIN.y * config.SETTINGS.stack_margin_y_fac

        rep_node.height = y
        rep_node.width = max([v.width for v in path])

        cluster = cast(Cluster, path[0].cluster)
        rep_node.cluster = cluster
        T.add_edge(cluster, rep_node)

        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

        for u, v, k, d in *G.in_edges(path, keys=True, data=True), *G.out_edges(path, keys=True,
          data=True):
            if u in path and v in path:
                continue

            G.remove_edge(u, v, k)
            e_ = (rep_node, v) if u in path else (u, rep_node)
            G.add_edge(*e_, **d)

        G.remove_nodes_from(path)
        T.remove_nodes_from(path)

        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

        node_stacks.append(node_stack)

    assert nx.is_directed_acyclic_graph(G)

    return node_stacks


def expand_node_stack(CG: ClusterGraph, node_stack: NodeStack) -> None:
    G = CG.G
    rep_node = node_stack.rep_node
    path = node_stack.path

    for stack_socket, original_socket in node_stack.stack_sockets_to_originals.items():
        if stack_socket.is_output:
            for _, v, k, d in tuple(G.out_edges(rep_node, data=True, keys=True)):
                if d[FROM_SOCKET] != stack_socket:
                    continue

                G.remove_edge(rep_node, v, k)
                G.add_edge(
                  original_socket.owner,
                  v,
                  from_socket=original_socket,
                  to_socket=d[TO_SOCKET],
                )
        else:
            for u, _, k, d in G.in_edges(rep_node, data=True, keys=True):
                if d[TO_SOCKET] == stack_socket:
                    break
            G.remove_edge(u, rep_node, k)
            G.add_edge(
              u,
              original_socket.owner,
              from_socket=d[FROM_SOCKET],
              to_socket=original_socket,
            )

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    G.add_nodes_from(path)

    i = rep_node.col.index(rep_node)
    rep_node.col[i:i] = path

    y = rep_node.y
    for v in path:
        CG.T.add_edge(cast(Cluster, rep_node.cluster), v)
        v.x = rep_node.x - (v.width - rep_node.width) / 2
        v.y = y
        y -= v.height + config.MARGIN.y * config.SETTINGS.stack_margin_y_fac

    CG.remove_nodes_from([rep_node])
