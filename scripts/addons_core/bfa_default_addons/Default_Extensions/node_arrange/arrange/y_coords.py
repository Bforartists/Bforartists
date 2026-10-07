# SPDX-License-Identifier: GPL-2.0-or-later

# http://dx.doi.org/10.1007/3-540-45848-4_3
# http://dx.doi.org/10.1007/978-3-319-27261-0_12
# https://arxiv.org/abs/2008.01252

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Collection, Iterable, Iterator, Sequence
from itertools import pairwise
from math import ceil, floor, inf
from statistics import fmean
from typing import Any, cast

import networkx as nx

from .. import config
from .graph import FROM_SOCKET, TO_SOCKET, Cluster, Edge, Kind, Node, Socket


def marked_conflicts(
  G: nx.DiGraph[Node],
  *,
  should_ensure_alignment: Callable[[Node], Any],
) -> set[frozenset[Node]]:
    columns = G.graph['columns']
    marked_edges = set()
    for i, col in enumerate(columns[1:], 1):
        k_0 = 0
        l = 0
        for l_1, u in enumerate(col):
            if should_ensure_alignment(u):
                upper_nbr = next(iter(G.pred[u]))
                k_1 = upper_nbr.col.index(upper_nbr)
            elif u == col[-1]:
                k_1 = len(columns[i - 1]) - 1
            else:
                continue

            while l <= l_1:
                v = col[l]
                l += 1

                if should_ensure_alignment(v):
                    continue

                for pred in G.pred[v]:
                    k = pred.col.index(pred)
                    if k < k_0 or k > k_1:
                        marked_edges.add(frozenset((pred, v)))

            k_0 = k_1

    return marked_edges


def horizontal_alignment(
  G: nx.DiGraph[Node],
  marked_edges: Collection[frozenset[Node]],
  marked_nodes: Collection[Node],
) -> None:
    for col in G.graph['columns']:
        prev_i = -1
        for v in col:
            predecessors = sorted(G.pred[v], key=lambda u: u.col.index(u))
            m = (len(predecessors) - 1) / 2
            for u in predecessors[floor(m):ceil(m) + 1]:
                i = u.col.index(u)

                if v.aligned != v or {u, v} in marked_edges or prev_i >= i:
                    continue

                if u.cluster != v.cluster and {u, v} & marked_nodes:  # type: ignore
                    continue

                u.aligned = v
                v.root = u.root
                v.aligned = v.root
                prev_i = i


def iter_block(start: Node) -> Iterator[Node]:
    yield start
    w = start
    while (w := w.aligned) != start:
        yield w


def should_use_inner_shift(v: Node, w: Node, is_right: bool) -> bool:
    if v.is_reroute or w.is_reroute:
        return True

    if config.SETTINGS.socket_alignment == 'NONE':
        return False

    if config.SETTINGS.socket_alignment == 'FULL':
        return True

    if v.cluster != w.cluster or Kind.STACK in {v.type, w.type}:
        return True

    if not is_right:
        v, w = w, v

    if v.height > w.height and not getattr(w.node, 'hide', False):
        return False

    return abs(v.height - w.height) > fmean((v.height, w.height)) / 2


def inner_shift(G: nx.MultiDiGraph[Node], is_right: bool, is_up: bool) -> None:
    for root in {v.root for v in G}:
        for v, w in pairwise(iter_block(root)):
            if not should_use_inner_shift(v, w, is_right):
                w.inner_shift = v.inner_shift
                continue

            inner_shifts = []
            for k in G[v][w]:
                p: Socket = G[v][w][k][FROM_SOCKET]
                q: Socket = G[v][w][k][TO_SOCKET]
                if p.owner != v:
                    p, q = q, p

                if is_up:
                    inner_shifts.append(v.inner_shift - p._offset_y + q._offset_y)
                else:
                    inner_shifts.append(v.inner_shift + p._offset_y - q._offset_y)

            w.inner_shift = fmean(inner_shifts)


def place_block(v: Node, is_up: bool) -> None:
    if cast(float | None, v.y) is not None:
        return

    v.y = 0
    initial = True
    for w in iter_block(v):
        i = w.col.index(w)

        if i == 0:
            continue

        n = w.col[i - 1]
        u = n.root
        place_block(u, is_up)

        if v.sink == v:
            v.sink = u.sink

        if v.sink == u.sink:
            delta_l = n.height + config.MARGIN.y if is_up else w.height + config.MARGIN.y
            s_b = u.y + n.inner_shift - w.inner_shift + delta_l
            v.y = s_b if initial else max(v.y, s_b)
            initial = False

    for w in iter_block(v):
        w.y = v.y
        w.sink = v.sink


def vertical_compaction(G: nx.DiGraph[Node], is_up: bool) -> None:
    for v in G:
        if v.root == v:
            place_block(v, is_up)

    columns = G.graph['columns']
    neighborings: defaultdict[tuple[Node, ...], set[Edge]] = defaultdict(set)

    for col in columns:
        for v, u in pairwise(reversed(col)):
            if u.sink != v.sink:
                neighborings[tuple(v.sink.col)].add((u, v))

    for col in columns:
        if col[0].sink.shift == inf:
            col[0].sink.shift = 0

        for u, v in neighborings[tuple(col)]:
            delta_l = u.height + config.MARGIN.y if is_up else v.height + config.MARGIN.y
            s_c = v.y + v.inner_shift - u.y - u.inner_shift - delta_l
            u.sink.shift = min(u.sink.shift, v.sink.shift + s_c)

    for v in G:
        v.y += v.sink.shift + v.inner_shift


def get_merged_lines(lines: Iterable[tuple[float, float]]) -> list[tuple[float, float]]:
    merged = []
    for line in sorted(lines, key=lambda l: l[0]):
        if merged and merged[-1][1] >= line[0]:
            a, b = merged[-1]
            merged[-1] = (a, max(b, line[1]))
        else:
            merged.append(line)

    return merged


def has_large_gaps_in_frame(cluster: Cluster, T: nx.DiGraph[Cluster | Node], is_up: bool) -> bool:
    lines = []
    for v in T[cluster]:
        if v.type == Kind.VERTICAL_BORDER:
            continue

        if v.type != Kind.CLUSTER:
            line = (v.y, v.y + v.height) if is_up else (v.y - v.height, v.y)
        else:
            vertical_border_roots = {w.root for w in T[v] if w.type == Kind.VERTICAL_BORDER}
            w, z = sorted(vertical_border_roots, key=lambda w: w.y)
            line = (w.y, z.y + z.height) if is_up else (w.y - w.height, z.y)

        lines.append(line)

    merged = get_merged_lines(lines)
    return any(l2[0] - l1[1] > config.MARGIN.y for l1, l2 in pairwise(merged))


def get_marked_nodes(
  G: nx.DiGraph[Node],
  T: nx.DiGraph[Node | Cluster],
  old_marked_nodes: set[Node],
  is_up: bool,
) -> set[Node]:
    marked_nodes = set()
    for cluster in T:
        if cluster.type != Kind.CLUSTER or cluster.nesting_level != 1:
            continue

        descendant_clusters = cast(
          set[Cluster],
          (nx.descendants(T, cluster) & (T.nodes - G.nodes)) | {cluster},
        )
        for nested_cluster in sorted(
          descendant_clusters,
          key=lambda c: cast(int, c.nesting_level),
          reverse=True,
        ):
            children = {v for v in T[nested_cluster] if v.type != Kind.CLUSTER}

            if children <= old_marked_nodes:
                continue

            if not has_large_gaps_in_frame(nested_cluster, T, is_up):
                continue

            if children & old_marked_nodes:
                marked_nodes.update(children)
                continue

            for root in {v.root for v in children}:
                b = tuple(iter_block(root))
                for u, v in pairwise(b):
                    if u.is_reroute and v.is_reroute and (u in children != v in children):
                        break
                else:
                    marked_nodes.update(children.intersection(b))

    return marked_nodes


def balance(G: nx.DiGraph[Node], layouts: list[list[float]]) -> None:

    def min_y(layout: Sequence[float]) -> float:
        return min([y - v.height for v, y in zip(G, layout)])

    smallest_layout = min(layouts, key=lambda l: max(l) - min_y(l))

    movement = min_y(smallest_layout)
    for i in range(len(smallest_layout)):
        smallest_layout[i] -= movement

    for i, layout in enumerate(layouts):
        if layout == smallest_layout:
            continue

        func = min_y if i % 2 != 1 else max
        movement = func(smallest_layout) - func(layout)
        for j in range(len(layout)):
            layout[j] += movement


_ITER_LIMIT = 20
_DIRECTION_TO_IDX = {'RIGHT_DOWN': 0, 'RIGHT_UP': 1, 'LEFT_DOWN': 2, 'LEFT_UP': 3}


def bk_assign_y_coords(G: nx.MultiDiGraph[Node], T: nx.DiGraph[Node | Cluster]) -> None:
    columns = G.graph['columns']
    for col in columns:
        col.reverse()

    is_incident_to_inner_segment = lambda v: v.is_reroute and any(u.is_reroute for u in G.pred[v])
    is_incident_to_vertical_border = lambda v: v.type == Kind.VERTICAL_BORDER and G.pred[v]
    marked_edges = marked_conflicts(G, should_ensure_alignment=is_incident_to_inner_segment)
    marked_edges |= marked_conflicts(G, should_ensure_alignment=is_incident_to_vertical_border)

    layouts = []
    for dir_x in (-1, 1):
        G = nx.reverse_view(G)  # type: ignore
        columns.reverse()
        for dir_y in (-1, 1):
            i = 0
            marked_nodes = set()
            is_up = dir_y == 1
            while i < _ITER_LIMIT:
                i += 1
                horizontal_alignment(G, marked_edges, marked_nodes)
                inner_shift(G, dir_x == 1, is_up)
                vertical_compaction(G, is_up)

                if new_marked_nodes := get_marked_nodes(G, T, marked_nodes, is_up):
                    marked_nodes.update(new_marked_nodes)
                    for v in G:
                        v.bk_reset()
                else:
                    break
            layouts.append([v.y * -dir_y for v in G])

            for v in G:
                v.bk_reset()

            for col in columns:
                col.reverse()

    for col in columns:
        col.reverse()

    if config.SETTINGS.direction == 'BALANCED':
        balance(G, layouts)
        for i, v in enumerate(G):
            values = [l[i] for l in layouts]
            values.sort()
            v.y = fmean(values[1:3])
    else:
        i = _DIRECTION_TO_IDX[config.SETTINGS.direction]
        for v, y in zip(G, layouts[i]):
            v.y = y
