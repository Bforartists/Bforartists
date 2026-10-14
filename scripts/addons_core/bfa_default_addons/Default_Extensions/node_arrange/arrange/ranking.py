# SPDX-License-Identifier: GPL-2.0-or-later

# http://dx.doi.org/10.1109/32.221135

from __future__ import annotations

from functools import cache
from math import sqrt
from typing import TYPE_CHECKING

import networkx as nx

from ..utils import group_by
from .graph import Kind, MultiEdge, Node, opposite

if TYPE_CHECKING:
    from .sugiyama import ClusterGraph


# https://api.semanticscholar.org/CorpusID:14932050
def get_nesting_graph(CG: ClusterGraph) -> nx.MultiDiGraph[Node]:
    H = CG.G.copy()
    for u, v in CG.T.edges:
        if u.type == Kind.CLUSTER:
            if v.type != Kind.CLUSTER:
                H.add_edges_from(((u.left, v), (v, u.right)))
            else:
                H.add_edges_from(((u.left, v.left), (v.right, u.right)))

    return H


@cache
def get_adj_edges_H(H: nx.MultiDiGraph[Node], v: Node) -> tuple[MultiEdge, ...]:
    return (*H.in_edges(v, keys=True), *H.out_edges(v, keys=True))


@cache
def get_adj_edges_T(T: nx.MultiDiGraph[Node], v: Node) -> tuple[MultiEdge, ...]:
    return (*T.in_edges(v, keys=True), *T.out_edges(v, keys=True))


def get_slack(e: MultiEdge) -> int:
    u, v, _ = e
    min_length = 1
    return v.rank - u.rank - min_length


def tight_tree(
  H: nx.MultiDiGraph[Node],
  T: nx.MultiDiGraph[Node],
  v: Node,
  visited: set[MultiEdge] | None = None,
) -> int:
    if visited is None:
        visited = set()

    T.add_node(v)

    for e in get_adj_edges_H(H, v):
        if e in visited:
            continue

        visited.add(e)

        u, w, _ = e
        other = u if v != u else w
        if e in T.edges:
            tight_tree(H, T, other, visited)
        elif other not in T and get_slack(e) == 0:
            T.add_edge(*e)
            tight_tree(H, T, other, visited)

    return len(T)


def set_post_order_numbers(v: Node, T: nx.MultiDiGraph[Node]) -> None:
    visited = set()
    num = 0

    def recurse(w: Node) -> int:
        nums = []
        for e in get_adj_edges_T(T, w):
            if e in visited:
                continue

            visited.add(e)
            nums.append(recurse(opposite(w, e)))

        nonlocal num
        w.po_num = num
        w.lowest_po_num = min(nums + [num])
        num += 1
        return w.lowest_po_num

    recurse(v)


def compute_cut_values(H: nx.MultiDiGraph[Node], T: nx.MultiDiGraph[Node]) -> None:
    unknown_cut_values = {}
    leaves = []
    for v in H:
        adj_edges = get_adj_edges_T(T, v)
        unknown_cut_values[v] = list(adj_edges)
        if len(adj_edges) == 1:
            leaves.append(v)

    for v in leaves:
        while len(unknown_cut_values[v]) == 1:
            to_determine = unknown_cut_values[v][0]
            d = T.edges[to_determine]
            d['cut_value'] = H.edges[to_determine]['weight']
            u, w, _ = to_determine
            for e in get_adj_edges_H(H, v):
                if e == to_determine:
                    continue

                weight = H.edges[e]['weight']
                if e in T.edges:
                    if u == e[0] or w == e[1]:
                        d['cut_value'] -= T.edges[e]['cut_value'] - weight
                    else:
                        d['cut_value'] += T.edges[e]['cut_value'] - weight
                else:
                    if (v == u and e[0] != v) or (v != u and e[0] == v):
                        weight = -weight
                    d['cut_value'] += weight

            unknown_cut_values[u].remove(to_determine)
            unknown_cut_values[w].remove(to_determine)
            v = w if u == v else u


def feasible_tree(H: nx.MultiDiGraph[Node]) -> nx.MultiDiGraph[Node]:
    generations = nx.topological_generations(nx.reverse_view(H))  # type: ignore
    for i, col in enumerate(reversed(tuple(generations))):
        for v in col:
            v.rank = i

    T = nx.MultiDiGraph()
    v_root = next(iter(H))

    while tight_tree(H, T, v_root) < len(H):
        incident_edges = [(u, v, k) for u, v, k in H.edges(keys=True) if (u in T) ^ (v in T)]
        e = min(incident_edges, key=get_slack)
        slack = -get_slack(e) if e[1] in T else get_slack(e)
        for v in T:
            v.rank += slack

    set_post_order_numbers(v_root, T)
    compute_cut_values(H, T)

    return T


def leave_edge(T: nx.MultiDiGraph[Node]) -> MultiEdge | None:
    return next(((u, v, k) for u, v, k, c in T.edges.data('cut_value', keys=True) if c < 0), None)


def is_in_head(v: Node, e: MultiEdge) -> bool:
    u, w, _ = e

    if u.lowest_po_num <= v.po_num and v.po_num <= u.po_num and w.lowest_po_num <= v.po_num and v.po_num <= w.po_num:
        return u.po_num >= w.po_num

    return u.po_num < w.po_num


def enter_edge(H: nx.MultiDiGraph[Node], e: MultiEdge) -> MultiEdge:
    edges = [f for f in H.edges(keys=True) if is_in_head(f[0], e) and not is_in_head(f[1], e)]
    return min(edges, key=get_slack)


def exchange(
  H: nx.MultiDiGraph[Node],
  T: nx.MultiDiGraph[Node],
  leave: MultiEdge,
  enter: MultiEdge,
) -> None:
    T.remove_edge(*leave)
    T.add_edge(*enter)

    slack = get_slack(enter)
    if not is_in_head(enter[1], leave):
        slack = -slack

    for v in H:
        if not is_in_head(v, leave):
            v.rank += slack

    get_adj_edges_T.cache_clear()

    set_post_order_numbers(v, T)
    compute_cut_values(H, T)


def normalize_and_balance(CG: ClusterGraph, H: nx.DiGraph[Node]) -> None:
    for cc in nx.weakly_connected_components(CG.G):
        c = next(iter(cc)).cluster
        assert c

        if any(v.cluster != c for v in cc):
            continue

        ranked = group_by(cc, key=lambda v: v.rank, sort=True)

        if c.node:
            start = min(v.rank for v in CG.T[c] if v.type != Kind.CLUSTER)
        else:
            start = c.left.rank - (max(ranked.values()) - min(ranked.values()))

        for i, col in enumerate(ranked, start):
            for v in col:
                v.rank = i

    col_sizes = []
    for i, col in enumerate(group_by(H, key=lambda v: v.rank, sort=True)):
        col_sizes.append(len(col))
        for v in col:
            v.rank = i

    for v in H:
        if len(H.in_edges(v)) != len(H.out_edges(v)):
            continue

        start = v.rank - min([v.rank - u.rank for u in H.pred[v]], default=-1) + 1
        stop = v.rank + min([w.rank - v.rank for w in H[v]], default=-1)
        new_rank = max(range(start, stop), key=lambda i: col_sizes[i], default=v.rank)

        if col_sizes[new_rank] < col_sizes[v.rank]:
            col_sizes[v.rank] -= 1
            col_sizes[new_rank] += 1
            v.rank = new_rank


_BASE_ITER_LIMIT = 50


def compute_ranks(CG: ClusterGraph) -> None:
    for i, layer in enumerate(nx.topological_generations(CG.T)):
        for c in CG.S.intersection(layer):
            c.nesting_level = i

    H = get_nesting_graph(CG)
    nx.set_edge_attributes(H, 1, 'weight')  # type: ignore

    T = feasible_tree(H)
    i = 0
    iter_limit = _BASE_ITER_LIMIT * sqrt(len(H))
    while (e := leave_edge(T)) and i < iter_limit:
        exchange(H, T, e, enter_edge(H, e))
        i += 1

    root = next(c for c in CG.S if not CG.T.pred[c])
    H.remove_nodes_from((root.left, root.right))
    normalize_and_balance(CG, H)
