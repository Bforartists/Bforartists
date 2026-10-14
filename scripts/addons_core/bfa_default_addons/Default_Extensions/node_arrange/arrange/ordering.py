# SPDX-License-Identifier: GPL-2.0-or-later

# https://link.springer.com/chapter/10.1007/3-540-36151-0_26
# https://doi.org/10.1016/j.jvlc.2013.11.005
# https://doi.org/10.1007/978-3-642-11805-0_14
# https://link.springer.com/chapter/10.1007/978-3-540-31843-9_22
# https://doi.org/10.7155/jgaa.00088

from __future__ import annotations

import random
from collections import defaultdict
from collections.abc import Callable, Collection, Iterable, Iterator, Sequence
from dataclasses import replace
from functools import cache
from itertools import chain, pairwise
from math import inf
from operator import itemgetter
from statistics import fmean
from typing import TypeAlias, cast

import networkx as nx

from .. import config
from .graph import FROM_SOCKET, TO_SOCKET, Cluster, Kind, Node, Socket, socket_graph

# -------------------------------------------------------------------

_MixedGraph: TypeAlias = 'nx.DiGraph[Node | Cluster]'


def get_col_nesting_trees(
  columns: Sequence[Collection[Node]],
  T: _MixedGraph,
) -> list[_MixedGraph]:
    trees = []
    for col in columns:
        LT = nx.DiGraph()
        edges = nx.edge_bfs(T, col, orientation='reverse')
        LT.add_edges_from([e[:2] for e in edges])
        trees.append(LT)

    return trees


def expand_multi_inputs(G: nx.MultiDiGraph[Node]) -> None:
    H = socket_graph(G)
    reroutes = {v for v in H if v.owner.is_reroute}
    for v in {s.owner for s in config.multi_input_sort_ids}:
        inputs = sorted({e[2] for e in G.in_edges(v, data=TO_SOCKET)}, key=lambda s: s.idx)
        i = inputs[0].idx
        for socket in inputs:
            if socket not in config.multi_input_sort_ids:
                if i != socket.idx:
                    d = next(d for *_, d in G.in_edges(v, data=True) if d[TO_SOCKET] == socket)
                    d[TO_SOCKET] = replace(socket, idx=i)
                i += 1
                continue

            sort_ids = config.multi_input_sort_ids[socket]
            SH = H.subgraph({i[0] for i in sort_ids} | {socket} | reroutes)
            seen = set()
            for base_from_socket in sorted(sort_ids, key=itemgetter(1), reverse=True):
                from_socket = next(
                  s for s, t in nx.edge_dfs(SH, base_from_socket) if t == socket and s not in seen)
                d = next(
                  d for d in G[from_socket.owner][v].values()
                  if d[TO_SOCKET] == socket and d[FROM_SOCKET] == from_socket)
                d[TO_SOCKET] = replace(socket, idx=i)
                seen.add(from_socket)
                i += 1


@cache
def reflexive_transitive_closure(LT: _MixedGraph) -> _MixedGraph:
    return cast(_MixedGraph, nx.transitive_closure(LT, reflexive=True))


@cache
def topologically_sorted_clusters(LT: _MixedGraph) -> list[Cluster]:
    return [h for h in nx.topological_sort(LT) if h.type == Kind.CLUSTER]


def crossing_reduction_graph(
  h: Cluster,
  LT: _MixedGraph,
  G: nx.MultiDiGraph[Node],
) -> nx.MultiDiGraph[Node | Cluster]:
    G_h = nx.MultiDiGraph()
    G_h.add_nodes_from(LT[h])
    TC = reflexive_transitive_closure(LT)
    for s, t, k, d in G.in_edges(TC[h], data=True, keys=True):  # type: ignore
        c = next(c for c in TC.pred[t] if c in LT[h])

        input_k = TO_SOCKET
        output_k = FROM_SOCKET
        if d[output_k].owner != s:
            input_k, output_k = output_k, input_k

        if (s, c, k) in G_h.edges and G_h.edges[s, c, k][output_k] == d[output_k]:
            G_h.edges[s, c, k]['weight'] += 1
            continue

        to_socket = d[input_k] if c.type != Kind.CLUSTER else replace(d[input_k], owner=c, idx=0)
        G_h.add_edge(s, c, weight=1, from_socket=d[output_k], to_socket=to_socket)

    return G_h


_BALANCING_FAC = 1


class _CrossingReductionGraph:
    graph: nx.MultiDiGraph[Node | Cluster]

    fixed_LT: _MixedGraph
    free_LT: _MixedGraph

    fixed_col: list[Node]
    free_col: list[Node]

    expanded_fixed_col: list[Node]
    reduced_free_col: list[Node | Cluster]

    fixed_sockets: dict[Node, list[Socket]]
    free_sockets: dict[Node | Cluster, list[Socket]]

    border_pairs: dict[tuple[Node, Node], list[Node]]
    constrained_clusters: list[Cluster]

    N: list[Socket]
    S: list[Socket]
    bipartite_edges: list[tuple[Socket, Socket, int]]

    __slots__ = tuple(__annotations__)

    def _insert_border_edges(self, is_forwards: bool) -> None:
        self.border_pairs = {}
        free_clusters = {v for v in self.reduced_free_col if v.type == Kind.CLUSTER}
        for c in free_clusters & self.fixed_LT.nodes:
            upper_v = Node(type=Kind.VERTICAL_BORDER)
            lower_v = Node(type=Kind.VERTICAL_BORDER)
            self.expanded_fixed_col.extend((upper_v, lower_v))

            fac = 1 + len((nx.descendants(self.free_LT, c) & self.fixed_LT.nodes))
            for border_v in upper_v, lower_v:
                self.graph.add_edge(
                  border_v,
                  c,
                  weight=(0.5 * _BALANCING_FAC) * fac,
                  from_socket=Socket(border_v, 0, is_forwards),
                  to_socket=Socket(c, 0, not is_forwards),  # type: ignore
                )

            bordered_nodes = [
              v for v in nx.descendants(self.fixed_LT, c) if v.type != Kind.CLUSTER]
            self.border_pairs[upper_v, lower_v] = bordered_nodes

    def _add_bipartite_edges(self) -> None:
        edges = [(d[FROM_SOCKET], d[TO_SOCKET], d) for *_, d in self.graph.edges.data()]

        if not edges:
            self.N = []
            self.S = []
            self.bipartite_edges = []
            return

        B = nx.DiGraph()
        B.add_edges_from(edges)

        N, S = map(set, zip(*B.edges))
        if len(S) > len(N):
            N, S = S, N
            B = nx.reverse_view(B)

        self.N = sorted(N, key=lambda d: d.idx)
        self.S = sorted(S, key=lambda d: d.idx)
        self.bipartite_edges = list(B.edges.data('weight'))

    def __init__(
      self,
      G: nx.MultiDiGraph[Node],
      h: Cluster,
      fixed_LT: _MixedGraph,
      free_LT: _MixedGraph,
      is_forwards: bool,
    ) -> None:
        G_h = crossing_reduction_graph(h, free_LT, G)
        self.graph = G_h

        self.fixed_LT = fixed_LT
        self.free_LT = free_LT

        fixed_col = next(v.col for v in fixed_LT if v.type != Kind.CLUSTER)
        self.fixed_col = fixed_col
        self.free_col = next(v.col for v in free_LT if v.type != Kind.CLUSTER)

        G_h.add_nodes_from(fixed_col)

        self.expanded_fixed_col = fixed_col.copy()
        pos = lambda v: v.col.index(v) if v.type != Kind.CLUSTER else inf
        self.reduced_free_col = sorted(free_LT[h], key=pos)

        self._insert_border_edges(is_forwards)

        self.fixed_sockets = {}
        for u in self.expanded_fixed_col:
            if sockets := {e[2] for e in G_h.out_edges(u, data=FROM_SOCKET)}:
                self.fixed_sockets[u] = sorted(sockets, key=lambda d: d.idx, reverse=is_forwards)

        self.free_sockets = {}
        for v in self.reduced_free_col:
            self.free_sockets[v] = [e[2] for e in G_h.in_edges(v, data=FROM_SOCKET)]

        self.constrained_clusters = [
          cast(Cluster, v) for v in self.reduced_free_col if v in fixed_LT]

        self._add_bipartite_edges()


def crossing_reduction_items(
  trees: Iterable[_MixedGraph],
  G: nx.MultiDiGraph[Node],
  is_forwards: bool,
) -> list[list[_CrossingReductionGraph]]:
    items = []
    for fixed_LT, free_LT in pairwise(trees):
        crossing_reduction_graphs = [
          _CrossingReductionGraph(G, h, fixed_LT, free_LT, is_forwards)
          for h in topologically_sorted_clusters(free_LT)]
        items.append(crossing_reduction_graphs)

    return items


# -------------------------------------------------------------------


def sort_expanded_fixed_col(H: _CrossingReductionGraph) -> None:
    pos: dict[Node, float] = {v: i for i, v in enumerate(H.fixed_col)}

    for (upper_v, lower_v), bordered_nodes in H.border_pairs.items():
        positions = [pos[v] for v in bordered_nodes]
        pos[upper_v] = min(positions) - 0.1
        pos[lower_v] = max(positions) + 0.1

    H.expanded_fixed_col.sort(key=pos.get)  # type: ignore


def calc_socket_ranks(H: _CrossingReductionGraph, is_forwards: bool) -> None:
    for v, sockets in H.fixed_sockets.items():
        incr = 1 / (len(sockets) + 1)
        rank = H.expanded_fixed_col.index(v) + 1
        if is_forwards:
            incr = -incr

        for socket in sockets:
            rank += incr
            v.cr.socket_ranks[socket] = rank


def random_perturbation() -> float:
    random_amount = random.uniform(-1, 1)
    return random.uniform(0, 1) * random_amount - random_amount / 2


def calc_barycenters(H: _CrossingReductionGraph) -> None:
    for w in H.reduced_free_col:
        if sockets := H.free_sockets[w]:
            w.cr.barycenter = (
              fmean([s.owner.cr.socket_ranks[s] for s in sockets]) + random_perturbation())


def get_barycenter(v: Node | Cluster) -> float:
    barycenter = v.cr.barycenter
    assert barycenter is not None
    return barycenter


def fill_in_unknown_barycenters(col: list[Node | Cluster], is_first_sweep: bool) -> None:
    if is_first_sweep:
        max_b = max([b for v in col if (b := v.cr.barycenter) is not None], default=0) + 2
        for v in col:
            if v.cr.barycenter is None:
                v.cr.barycenter = random.uniform(0, 1) * max_b - 1 + random_perturbation()
        return

    for i, v in enumerate(col):
        if v.cr.barycenter is not None:
            continue

        prev_b = get_barycenter(col[i - 1]) if i != 0 else 0
        next_b = next((b for w in col[i + 1:] if (b := w.cr.barycenter) is not None), prev_b + 1)
        v.cr.barycenter = (prev_b + next_b) / 2 + random_perturbation()


def find_violated_constraint(GC: _MixedGraph) -> tuple[Node | Cluster, Node | Cluster] | None:
    active = [v for v in GC if GC[v] and not GC.pred[v]]
    incoming_constraints = defaultdict(list)
    while active:
        v = active.pop(0)

        for c in incoming_constraints[v]:
            if c[0].cr.barycenter >= v.cr.barycenter:
                return c

        for t in GC[v]:
            incoming_constraints[t].insert(0, (v, t))
            if len(incoming_constraints[t]) == GC.in_degree[t]:
                active.append(t)

    return None


def handle_constraints(H: _CrossingReductionGraph) -> None:

    # Optimization: don't pass constraints to `nx.DiGraph` constructor
    GC = nx.DiGraph()
    GC.add_edges_from(pairwise(H.constrained_clusters))

    unconstrained = set(H.reduced_free_col) - GC.nodes
    L = {v: [v] for v in H.reduced_free_col}

    deg = {v: H.graph.degree[v] for v in GC}
    while c := find_violated_constraint(GC):
        v_c = Node(type=Kind.DUMMY)
        s, t = c

        deg[v_c] = deg[s] + deg[t]
        assert s.cr.barycenter and t.cr.barycenter
        if deg[v_c] > 0:
            v_c.cr.barycenter = (s.cr.barycenter * deg[s] + t.cr.barycenter * deg[t]) / deg[v_c]
        else:
            v_c.cr.barycenter = (s.cr.barycenter + t.cr.barycenter) / 2

        L[v_c] = L[s] + L[t]

        nx.relabel_nodes(GC, {s: v_c, t: v_c}, copy=False)
        if (v_c, v_c) in GC.edges:
            GC.remove_edge(v_c, v_c)

        if v_c not in GC:
            unconstrained.add(v_c)

    groups = sorted(unconstrained | GC.nodes, key=get_barycenter)
    for i, v in enumerate(chain(*[L[v] for v in groups])):
        v.cr.barycenter = i


def get_cross_count(H: _CrossingReductionGraph) -> int:
    edges = H.bipartite_edges

    if not edges:
        return 0

    reduced_free_col = set(H.reduced_free_col)

    def pos(s: Socket) -> float:
        v = s.owner
        if v in reduced_free_col:
            return v.cr.barycenter  # type: ignore
        else:
            return H.expanded_fixed_col.index(v)

    H.N.sort(key=pos)
    H.S.sort(key=pos)

    south_indicies = {k: i for i, k in enumerate(H.S)}
    north_indicies = {k: i for i, k in enumerate(H.N)}

    edges.sort(key=lambda e: south_indicies[e[1]])
    edges.sort(key=lambda e: north_indicies[e[0]])

    first_idx = 1
    while first_idx < len(H.S):
        first_idx *= 2

    tree = [0] * (2 * first_idx - 1)
    first_idx -= 1

    cross_weight = 0
    for _, v, weight in edges:
        idx = south_indicies[v] + first_idx
        tree[idx] += weight
        weight_sum = 0
        while idx > 0:
            if idx % 2 == 1:
                weight_sum += tree[idx + 1]

            idx = (idx - 1) // 2
            tree[idx] += weight

        cross_weight += weight * weight_sum

    return cross_weight


def get_new_col_order(v: Node | Cluster, LT: _MixedGraph) -> Iterator[Node]:
    if v.type == Kind.CLUSTER:
        for w in sorted(LT[v], key=get_barycenter):
            yield from get_new_col_order(w, LT)
    else:
        yield v


@cache
def non_cluster_descendant(T: _MixedGraph, c: Cluster) -> Node:
    return next(v for _, v in nx.bfs_edges(T, c) if v.type != Kind.CLUSTER)


def sort_reduced_free_columns(items: Iterable[Sequence[_CrossingReductionGraph]]) -> None:
    for crossing_reduction_graphs in items:

        def pos(v: Node | Cluster) -> int:
            w = non_cluster_descendant(H.free_LT, v) if v.type == Kind.CLUSTER else v
            return H.free_col.index(w)

        for H in crossing_reduction_graphs:
            H.reduced_free_col.sort(key=pos)


# -------------------------------------------------------------------


def minimized_cross_count(
  columns: Sequence[list[Node]],
  forward_items: list[list[_CrossingReductionGraph]],
  backward_items: list[list[_CrossingReductionGraph]],
  T: _MixedGraph,
) -> float:
    cross_count = inf
    is_forwards = random.choice((True, False))
    is_first_sweep = True
    while True:
        for v in T:
            v.cr.reset()

        if cross_count == 0:
            return 0

        is_forwards = not is_forwards
        old_cross_count = cross_count
        cross_count = 0

        items = forward_items if is_forwards else backward_items
        for i, crossing_reduction_graphs in enumerate(items):
            if i == 0:
                clusters = {
                  c: j
                  for j, v in enumerate(crossing_reduction_graphs[0].fixed_col)
                  for c in nx.ancestors(T, v)}
                key = cast(Callable[[Cluster], int], clusters.get)
            else:
                key = get_barycenter

            for H in crossing_reduction_graphs:
                H.constrained_clusters.sort(key=key)
                sort_expanded_fixed_col(H)

                calc_socket_ranks(H, is_forwards)
                calc_barycenters(H)
                fill_in_unknown_barycenters(H.reduced_free_col, is_first_sweep)
                handle_constraints(H)

                cross_count += get_cross_count(H)

            root = topologically_sorted_clusters(H.free_LT)[0]
            new_order = tuple(get_new_col_order(root, H.free_LT))
            H.free_col.sort(key=new_order.index)

        if old_cross_count > cross_count:
            sort_reduced_free_columns(forward_items + backward_items)
            best_columns = [c.copy() for c in columns]
            is_first_sweep = False
        else:
            for col, best_col in zip(columns, best_columns):
                col.sort(key=best_col.index)
            break

    return old_cross_count


def minimize_crossings(G: nx.MultiDiGraph[Node], T: _MixedGraph) -> None:
    columns = G.graph['columns']
    trees = get_col_nesting_trees(columns, T)
    G_ = G.copy()

    expand_multi_inputs(G_)

    forward_items = crossing_reduction_items(trees, G_, True)

    G__ = cast('nx.MultiDiGraph[Node]', nx.reverse_view(G_))  # type: ignore
    backward_items = crossing_reduction_items(reversed(trees), G__, False)

    # -------------------------------------------------------------------

    random.seed(0)
    best_cross_count = inf
    best_columns = [c.copy() for c in columns]
    for _ in range(config.SETTINGS.iterations):
        cross_count = minimized_cross_count(columns, forward_items, backward_items, T)
        if cross_count < best_cross_count:
            best_cross_count = cross_count
            best_columns = [c.copy() for c in columns]
            if best_cross_count == 0:
                break
        else:
            for col, best_col in zip(columns, best_columns):
                col.sort(key=best_col.index)
            sort_reduced_free_columns(forward_items + backward_items)
