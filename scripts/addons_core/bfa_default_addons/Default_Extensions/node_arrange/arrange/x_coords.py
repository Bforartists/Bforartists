# SPDX-License-Identifier: GPL-2.0-or-later

from __future__ import annotations

from collections import defaultdict
from collections.abc import Collection, Sequence
from itertools import chain
from typing import cast

import networkx as nx
from mathutils.geometry import intersect_line_line_2d

from .. import config
from ..utils import frame_padding, group_by
from .graph import (
  FROM_SOCKET,
  TO_SOCKET,
  Cluster,
  Kind,
  MultiEdge,
  Node,
  Socket,
  add_dummy_nodes_to_edge,
  lowest_common_cluster,
)


def frame_padding_of_col(
  columns: Sequence[Collection[Node]],
  i: int,
  T: nx.DiGraph[Node | Cluster],
) -> float:
    col = columns[i]

    if col == columns[-1]:
        return 0

    clusters1 = {cast(Cluster, v.cluster) for v in col}
    clusters2 = {cast(Cluster, v.cluster) for v in columns[i + 1]}

    if not clusters1 ^ clusters2:
        return 0

    ST1 = T.subgraph(chain(clusters1, *[nx.ancestors(T, c) for c in clusters1])).copy()
    ST2 = T.subgraph(chain(clusters2, *[nx.ancestors(T, c) for c in clusters2])).copy()

    for *e, d in ST1.edges(data=True):
        d['weight'] = int(e not in ST2.edges)  # type: ignore

    for *e, d in ST2.edges(data=True):
        d['weight'] = int(e not in ST1.edges)  # type: ignore

    dist = nx.dag_longest_path_length(ST1) + nx.dag_longest_path_length(ST2)  # type: ignore
    return frame_padding() * dist


def assign_x_coords(G: nx.DiGraph[Node], T: nx.DiGraph[Node | Cluster]) -> None:
    columns: list[list[Node]] = G.graph['columns']
    x = 0
    for i, col in enumerate(columns):
        max_width = max([v.width for v in col])

        for v in col:
            v.x = x if v.is_reroute else x - (v.width - max_width) / 2

        # https://doi.org/10.7155/jgaa.00220 (p. 139)
        delta_i = sum([
          1 for *_, d in G.out_edges(col, data=True)
          if abs(d[TO_SOCKET].y - d[FROM_SOCKET].y) >= config.MARGIN.x * 3])
        spacing = (1 + min(delta_i / 4, 2)) * config.MARGIN.x
        x += max_width + spacing + frame_padding_of_col(columns, i, T)


_MIN_X_DIFF = 30
_MIN_Y_DIFF = 8


def is_unnecessary_bend_point(socket: Socket, other_socket: Socket) -> bool:
    v = socket.owner

    if v.is_reroute:
        return False

    i = v.col.index(v)
    is_above = other_socket.y > socket.y

    try:
        nbr = v.col[i - 1] if is_above else v.col[i + 1]
    except IndexError:
        return True

    if nbr.is_reroute:
        return True

    nbr_x_offset, nbr_y_offset = config.MARGIN / 2
    nbr_y = nbr.y - nbr.height - nbr_y_offset if is_above else nbr.y + nbr_y_offset

    assert nbr.cluster
    if nbr.cluster.node and nbr.cluster != v.cluster:
        nbr_x_offset += frame_padding()
        if is_above:
            nbr_y -= frame_padding()
        else:
            nbr_y += frame_padding() + nbr.cluster.label_height()

    line_a = ((nbr.x - nbr_x_offset, nbr_y), (nbr.x + nbr.width + nbr_x_offset, nbr_y))
    line_b = ((socket.x, socket.y), (other_socket.x, other_socket.y))
    return intersect_line_line_2d(*line_a, *line_b) is None


def add_bend_points(
  G: nx.MultiDiGraph[Node],
  v: Node,
  bend_points: defaultdict[MultiEdge, list[Node]],
) -> None:
    d: dict[str, Socket]
    largest = max(v.col, key=lambda w: w.width)
    for u, w, k, d in *G.out_edges(v, data=True, keys=True), *G.in_edges(v, data=True, keys=True):
        socket = d[FROM_SOCKET] if v == u else d[TO_SOCKET]
        bend_point = Node(type=Kind.DUMMY)
        bend_point.x = largest.x + largest.width if socket.is_output else largest.x

        if abs(socket.x - bend_point.x) <= _MIN_X_DIFF:
            continue

        bend_point.y = socket.y
        other_socket = next(s for s in d.values() if s != socket)

        if abs(other_socket.y - bend_point.y) <= _MIN_Y_DIFF:
            continue

        if is_unnecessary_bend_point(socket, other_socket):
            continue

        bend_points[u, w, k].append(bend_point)


def node_overlaps_edge(
  v: Node,
  edge_line: tuple[tuple[float, float], tuple[float, float]],
) -> bool:
    if v.is_reroute:
        return False

    top_line = ((v.x, v.y), (v.x + v.width, v.y))
    if intersect_line_line_2d(*edge_line, *top_line):
        return True

    bottom_line = (
      (v.x, v.y - v.height),
      (v.x + v.width, v.y - v.height),
    )
    if intersect_line_line_2d(*edge_line, *bottom_line):
        return True

    return False


def route_edges(G: nx.MultiDiGraph[Node], T: nx.DiGraph[Node | Cluster]) -> None:
    bend_points = defaultdict(list)
    for v in chain(*G.graph['columns']):
        add_bend_points(G, v, bend_points)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    edge_of = {b: e for e, d in bend_points.items() for b in d}
    key = lambda b: (G.edges[edge_of[b]][FROM_SOCKET], b.x, b.y)
    for (target, *redundant), (from_socket, *_) in group_by(edge_of, key=key).items():
        for b in redundant:
            dummy_nodes = bend_points[edge_of[b]]
            dummy_nodes[dummy_nodes.index(b)] = target

        u = from_socket.owner
        if not u.is_reroute or G.out_degree[u] < 2:
            continue

        for e in G.out_edges(u, keys=True):
            if target not in bend_points[e] and G.edges[e][TO_SOCKET].y == target.y:
                bend_points[e].append(target)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    for e, dummy_nodes in tuple(bend_points.items()):
        dummy_nodes.sort(key=lambda b: b.x)
        from_socket = G.edges[e][FROM_SOCKET]
        for e_ in G.out_edges(e[0], keys=True):
            d = G.edges[e_]

            if d[FROM_SOCKET] != from_socket or e_ in bend_points:
                continue

            if d[TO_SOCKET].x <= dummy_nodes[-1].x:
                continue

            b = dummy_nodes[-1]
            line = ((b.x, b.y), (d[TO_SOCKET].x, d[TO_SOCKET].y))
            if any(node_overlaps_edge(v, line) for v in e[1].col):
                continue

            bend_points[e_] = dummy_nodes

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    lca = lowest_common_cluster(T, bend_points)
    for (u, v, k), dummy_nodes in bend_points.items():
        add_dummy_nodes_to_edge(G, (u, v, k), dummy_nodes)

        c = lca.get((u, v), u.cluster)
        for w in dummy_nodes:
            w.cluster = c
            T.add_edge(c, w)
