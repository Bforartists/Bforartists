# SPDX-License-Identifier: GPL-2.0-or-later

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass, field
from enum import Enum, auto
from functools import cached_property
from itertools import chain, pairwise, product
from math import inf
from typing import Any, Literal, Sequence, TypeGuard

import bpy
import networkx as nx
from bpy.types import Node as BlenderNode
from bpy.types import NodeFrame, NodeSocket

from .. import config
from ..utils import (
  REROUTE_DIM,
  abs_loc,
  dimensions,
  frame_padding,
  get_bottom,
  get_ntree,
  get_top,
  group_by,
)
from .structs import bNodeSocket

# -------------------------------------------------------------------


class Kind(Enum):
    NODE = auto()
    STACK = auto()
    DUMMY = auto()
    CLUSTER = auto()
    HORIZONTAL_BORDER = auto()
    VERTICAL_BORDER = auto()


_NonCluster = Literal[
  Kind.NODE,
  Kind.STACK,
  Kind.DUMMY,
  Kind.HORIZONTAL_BORDER,
  Kind.VERTICAL_BORDER,]


@dataclass(slots=True)
class CrossingReduction:
    socket_ranks: dict[Socket, float] = field(default_factory=dict)
    barycenter: float | None = None

    def reset(self) -> None:
        self.socket_ranks.clear()
        self.barycenter = None


class Node:
    node: BlenderNode | None
    cluster: Cluster | None
    type: _NonCluster

    is_reroute: bool
    width: float
    height: float

    rank: int
    po_num: int
    lowest_po_num: int
    is_fill_dummy: bool

    col: list[Node]
    cr: CrossingReduction

    x: float
    y: float

    root: Node
    aligned: Node
    inner_shift: float
    sink: Node
    shift: float

    __slots__ = tuple(__annotations__)

    def __init__(
      self,
      node: BlenderNode | None = None,
      cluster: Cluster | None = None,
      type: _NonCluster = Kind.NODE,
      rank: int | None = None,
    ) -> None:
        real = isinstance(node, BlenderNode)

        self.node = node
        self.cluster = cluster
        self.type = type
        self.rank = rank  # type: ignore

        if type == Kind.DUMMY or (real and node.bl_idname == 'NodeReroute'):
            self.is_reroute = True
            self.width = REROUTE_DIM.x
            self.height = REROUTE_DIM.y
        elif real:
            self.is_reroute = False
            self.width = dimensions(node).x
            self.height = get_top(node) - get_bottom(node)
        else:
            self.is_reroute = type == Kind.VERTICAL_BORDER
            self.width = 0
            self.height = 0

        self.po_num = None  # type: ignore
        self.lowest_po_num = None  # type: ignore
        self.is_fill_dummy = False

        self.col = None  # type: ignore
        self.cr = CrossingReduction()

        self.x = None  # type: ignore
        self.bk_reset()

    def __hash__(self) -> int:
        return id(self)

    def bk_reset(self) -> None:
        self.root = self
        self.aligned = self
        self.inner_shift = 0

        self.sink = self
        self.shift = inf

        self.y = None  # type: ignore

    def corrected_y(self) -> float:
        assert is_real(self)
        return self.y + (abs_loc(self.node).y - get_top(self.node))


class _RealNode(Node):
    node: BlenderNode  # type: ignore


def is_real(v: Node | Cluster) -> TypeGuard[_RealNode]:
    return isinstance(v.node, BlenderNode)


def node_name(v: Node) -> str:
    return getattr(v.node, 'name', '')


Edge = tuple[Node, Node]
MultiEdge = tuple[Node, Node, int]


def opposite(v: Node, e: tuple[Node, Node] | tuple[Node, Node, ...]) -> Node:
    return e[0] if v != e[0] else e[1]


@dataclass(slots=True)
class Cluster:
    node: NodeFrame | None
    cluster: Cluster
    nesting_level: int | None = None
    cr: CrossingReduction = field(default_factory=CrossingReduction)
    left: Node = field(init=False)
    right: Node = field(init=False)

    def __post_init__(self) -> None:
        self.left = Node(None, self, Kind.HORIZONTAL_BORDER)
        self.right = Node(None, self, Kind.HORIZONTAL_BORDER)

    def __hash__(self) -> int:
        return id(self)

    @property
    def type(self) -> Literal[Kind.CLUSTER]:
        return Kind.CLUSTER

    def label_height(self) -> float:
        frame = self.node
        if frame and frame.label:
            return -(frame_padding() / 2 - frame.label_size * 1.25)
        else:
            return 0


# -------------------------------------------------------------------


def get_nesting_relations(v: Node | Cluster) -> Iterator[tuple[Cluster, Node | Cluster]]:
    if c := v.cluster:
        yield (c, v)
        yield from get_nesting_relations(c)


def lowest_common_cluster(
  T: nx.DiGraph[Node | Cluster],
  edges: Iterable[tuple[Node, Node, Any]],
) -> dict[Edge, Cluster]:
    pairs = {(u, v) for u, v, _ in edges if u.cluster != v.cluster}
    return dict(nx.tree_all_pairs_lowest_common_ancestor(T, pairs=pairs))


def add_dummy_edge(G: nx.DiGraph[Node], u: Node, v: Node) -> None:
    G.add_edge(u, v, from_socket=Socket(u, 0, True), to_socket=Socket(v, 0, False))


def add_dummy_nodes_to_edge(
  G: nx.MultiDiGraph[Node],
  edge: MultiEdge,
  dummy_nodes: Sequence[Node],
) -> None:
    if not dummy_nodes:
        return

    for pair in pairwise(dummy_nodes):
        if pair not in G.edges:
            add_dummy_edge(G, *pair)

    u, v, _ = edge
    d = G.edges[edge]  # type: ignore

    w = dummy_nodes[0]
    if w not in G[u]:
        G.add_edge(u, w, from_socket=d[FROM_SOCKET], to_socket=Socket(w, 0, False))

    z = dummy_nodes[-1]
    G.add_edge(z, v, from_socket=Socket(z, 0, True), to_socket=d[TO_SOCKET])

    G.remove_edge(*edge)

    if not is_real(u) or not is_real(v):
        return

    links = get_ntree().links
    if d[TO_SOCKET].bpy.is_multi_input:
        target_link = (d[FROM_SOCKET].bpy, d[TO_SOCKET].bpy)
        links.remove(next(l for l in links if (l.from_socket, l.to_socket) == target_link))


def assign_clusters(
  dummy_nodes: Iterable[Node],
  start: Cluster,
  stop: Cluster,
  is_within_cluster: Callable[[Node, Cluster], bool],
) -> None:
    c = start
    for w in dummy_nodes:
        while c != stop and not is_within_cluster(w, c):
            c = c.cluster

        if c == stop:
            break

        w.cluster = c


def improve_cluster_assignment(e: Edge, dummy_nodes: Sequence[Node]) -> None:
    if config.SETTINGS.keep_reroutes_outside_frames:
        return

    u, v = e
    assert u.cluster and v.cluster
    c1 = u.cluster
    c2 = v.cluster

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    if not (c1.node and c2.node) or c1.right.rank >= c2.left.rank:
        if c2.node and u.rank < c2.left.rank:
            c1 = None
            while c2.cluster.node and u.rank < c2.cluster.left.rank:
                c2 = c2.cluster
        elif c1.node and v.rank > c1.right.rank:
            c2 = None
            while c1.cluster.node and v.rank > c1.cluster.right.rank:
                c1 = c1.cluster
        else:
            return
    else:
        while True:
            parent1 = c1.cluster
            if parent1.node and parent1.right.rank < c2.left.rank:
                c1 = parent1
                continue

            parent2 = c2.cluster
            if parent2.node and c1.right.rank < parent2.left.rank:
                c2 = parent2
                continue

            break

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    if c1:
        assign_clusters(
          dummy_nodes,
          u.cluster,
          c1.cluster,
          lambda w, c: w.rank <= c.right.rank,
        )

    if c2:
        assign_clusters(
          reversed(dummy_nodes),
          v.cluster,
          c2.cluster,
          lambda w, c: w.rank >= c.left.rank,
        )


# https://api.semanticscholar.org/CorpusID:14932050
class ClusterGraph:
    G: nx.MultiDiGraph[Node]
    T: nx.DiGraph[Node | Cluster]
    S: set[Cluster]
    __slots__ = tuple(__annotations__)

    def __init__(self, G: nx.MultiDiGraph[Node]) -> None:
        self.G = G
        self.T = nx.DiGraph(chain(*map(get_nesting_relations, G)))
        self.S = {v for v in self.T if v.type == Kind.CLUSTER}

    def remove_nodes_from(self, nodes: Iterable[Node]) -> None:
        ntree = get_ntree()
        for v in nodes:
            self.G.remove_node(v)
            self.T.remove_node(v)
            if v.col:
                v.col.remove(v)

            if not is_real(v):
                continue

            sockets = {*v.node.inputs, *v.node.outputs}

            for socket in sockets:
                config.linked_sockets.pop(socket, None)

            for val in config.linked_sockets.values():
                val -= sockets

            config.selected.remove(v.node)
            ntree.nodes.remove(v.node)

    def merge_edges(self) -> None:
        G = self.G
        T = self.T
        groups = group_by(G.edges, key=lambda e: G.edges[e][FROM_SOCKET])
        edges: tuple[MultiEdge, ...]
        for edges, from_socket in groups.items():
            long_edges = [(u, v, k) for u, v, k in edges if v.rank - u.rank > 1]

            if len(long_edges) < 2:
                continue

            long_edges.sort(key=lambda e: e[1].rank)
            lca = lowest_common_cluster(T, long_edges)
            dummy_nodes = []
            for u, v, k in long_edges:
                if dummy_nodes and dummy_nodes[-1].rank == v.rank - 1:
                    w = dummy_nodes[-1]
                else:
                    assert u.cluster
                    c = lca.get((u, v), u.cluster)
                    w = Node(None, c, Kind.DUMMY, v.rank - 1)
                    dummy_nodes.append(w)

                add_dummy_nodes_to_edge(G, (u, v, k), [w])
                G.remove_edge(u, w)

            for pair in pairwise(dummy_nodes):
                add_dummy_edge(G, *pair)

            w = dummy_nodes[0]
            G.add_edge(u, w, from_socket=from_socket, to_socket=Socket(w, 0, False))

            improve_cluster_assignment((u, v), dummy_nodes)
            for w in dummy_nodes:
                T.add_edge(w.cluster, w)

    def insert_dummy_nodes(self) -> None:
        G = self.G
        T = self.T

        # -------------------------------------------------------------------

        for c in self.S:
            descendants = [v for v in nx.descendants(T, c) if v.type != Kind.CLUSTER]
            c.left = min(descendants, key=lambda v: v.rank)
            c.right = max(descendants, key=lambda v: v.rank)

        # -------------------------------------------------------------------

        long_edges = [(u, v, k) for u, v, k in G.edges(keys=True) if v.rank - u.rank > 1]
        lca = lowest_common_cluster(T, long_edges)
        for u, v, k in long_edges:
            assert u.cluster
            c = lca.get((u, v), u.cluster)
            dummy_nodes = []
            for i in range(u.rank + 1, v.rank):
                w = Node(None, c, Kind.DUMMY, i)
                dummy_nodes.append(w)

            improve_cluster_assignment((u, v), dummy_nodes)
            add_dummy_nodes_to_edge(G, (u, v, k), dummy_nodes)

        for w in G.nodes - T.nodes:
            assert w.cluster
            T.add_edge(w.cluster, w)

        # -------------------------------------------------------------------

        for c in self.S:
            if not c.node:
                continue

            ranks = sorted({v.rank for v in nx.descendants(T, c) if v.type != Kind.CLUSTER})
            for i, j in pairwise(ranks):
                for k in range(i + 1, j):
                    v = Node(None, c, Kind.DUMMY, k)
                    v.is_fill_dummy = True
                    G.add_node(v)
                    T.add_edge(c, v)

    def add_vertical_border_nodes(self) -> None:
        T = self.T
        G = self.G
        columns = G.graph['columns']
        for c in self.S:
            if not c.node:
                continue

            descendants = [v for v in nx.descendants(T, c) if v.type != Kind.CLUSTER]
            lower_border_nodes = []
            upper_border_nodes = []
            for subcol in group_by(descendants, key=lambda v: columns.index(v.col), sort=True):
                col = subcol[0].col
                indices = [col.index(v) for v in subcol]

                lower_v = Node(None, c, Kind.VERTICAL_BORDER)
                col.insert(max(indices) + 1, lower_v)
                lower_v.col = col
                T.add_edge(c, lower_v)
                lower_border_nodes.append(lower_v)

                upper_v = Node(None, c, Kind.VERTICAL_BORDER)
                upper_v.height += c.label_height()
                col.insert(min(indices), upper_v)
                upper_v.col = col
                T.add_edge(c, upper_v)
                upper_border_nodes.append(upper_v)

            G.add_nodes_from(lower_border_nodes + upper_border_nodes)
            for p in *pairwise(lower_border_nodes), *pairwise(upper_border_nodes):
                add_dummy_edge(G, *p)


# -------------------------------------------------------------------


def get_socket_y(socket: NodeSocket) -> float:
    b_socket = bNodeSocket.from_address(socket.as_pointer())
    ui_scale = bpy.context.preferences.system.ui_scale  # type: ignore
    return b_socket.runtime.contents.location[1] / ui_scale


@dataclass(frozen=True)
class Socket:
    owner: Node
    idx: int
    is_output: bool
    prescribed_offset_y: float | None = field(default=None, hash=False, compare=False)

    @property
    def bpy(self) -> NodeSocket | None:
        v = self.owner

        if not is_real(v):
            return None

        sockets = v.node.outputs if self.is_output else v.node.inputs
        return sockets[self.idx]

    @property
    def x(self) -> float:
        v = self.owner
        return v.x + v.width if self.is_output else v.x

    @cached_property
    def _offset_y(self) -> float:
        if self.prescribed_offset_y is not None:
            return self.prescribed_offset_y

        v = self.owner

        if v.is_reroute or not is_real(v):
            return 0

        assert self.bpy
        return get_socket_y(self.bpy) - get_top(v.node)

    @property
    def y(self) -> float:
        return self.owner.y + self._offset_y


FROM_SOCKET = 'from_socket'
TO_SOCKET = 'to_socket'


def socket_graph(G: nx.MultiDiGraph[Node]) -> nx.DiGraph[Socket]:
    H = nx.DiGraph()
    H.add_edges_from([(d[FROM_SOCKET], d[TO_SOCKET]) for *_, d in G.edges.data()])
    for sockets in group_by(H, key=lambda s: s.owner):
        outputs = {s for s in sockets if s.is_output}
        H.add_edges_from(product(set(sockets) - outputs, outputs))

    return H


# -------------------------------------------------------------------


def get_reroute_paths(
  CG: ClusterGraph,
  function: Callable | None = None,
  *,
  preserve_reroute_clusters: bool = True,
  aligned: bool = False,
  linear: bool = True,
) -> list[list[Node]]:
    G = CG.G
    reroutes = {v for v in G if v.is_reroute and (not function or function(v))}
    H = nx.DiGraph(G.subgraph(reroutes))

    K = G if linear else H
    for v in H:
        if K.out_degree[v] > 1:
            H.remove_edges_from(tuple(H.out_edges(v)))

    if preserve_reroute_clusters:
        reroute_clusters = {#
          c for c in CG.S
          if all(v.is_reroute for v in CG.T[c] if v.type != Kind.CLUSTER)}
        H.remove_edges_from([#
          (u, v) for u, v in H.edges
          if u.cluster != v.cluster and {u.cluster, v.cluster} & reroute_clusters])

    if aligned:
        H.remove_edges_from([(u, v) for u, v in H.edges if u.y != v.y])

    indicies = {v: i for i, v in enumerate(nx.topological_sort(G)) if v in reroutes}
    paths = [sorted(c, key=lambda v: indicies[v]) for c in nx.weakly_connected_components(H)]
    paths.sort(key=lambda p: sum([indicies[v] for v in p]))
    return paths
