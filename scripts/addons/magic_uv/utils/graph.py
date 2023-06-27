# SPDX-FileCopyrightText: 2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.6"
__date__ = "22 Apr 2022"


class Node:
    def __init__(self, key, value=None):
        self.key = key
        self.value = value
        self.edges = []

    def degree(self):
        return len(self.edges)

    def connected_nodes(self):
        return [e.other(self) for e in self.edges]


class Edge:
    def __init__(self, node_1, node_2):
        self.node_1 = node_1
        self.node_2 = node_2

    def other(self, node):
        if self.node_1 == node and self.node_2 == node:
            raise RuntimeError("Loop edge in {} is not supported."
                               .format(node.key))
        if node not in (self.node_1, self.node_2):
            raise RuntimeError("Node {} does not belong to this edge."
                               .format(node.key))
        if self.node_1 == node:
            return self.node_2
        return self.node_1


class Graph:
    def __init__(self):
        self.edges = []
        self.nodes = {}

    def add_node(self, node):
        if node.key in self.nodes:
            raise RuntimeError("Node '{}' is already registered."
                               .format(node.key))
        self.nodes[node.key] = node

    def add_edge(self, node_1, node_2):
        if node_1.key not in self.nodes:
            raise RuntimeError("Node '{}' is not registered."
                               .format(node_1.key))
        if node_2.key not in self.nodes:
            raise RuntimeError("Node '{}' is not registered."
                               .format(node_2.key))

        edge = Edge(node_1, node_2)
        self.edges.append(edge)
        node_1.edges.append(edge)
        node_2.edges.append(edge)

    def get_node(self, key):
        return self.nodes[key]


def dump_graph(graph):
    print("=== Node ===")
    for _, node in graph.nodes.items():
        print("Key: {}, Value {}".format(node.key, node.value))

    print("=== Edge ===")
    for edge in graph.edges:
        print("{} - {}".format(edge.node_1.key, edge.node_2.key))


# VF2 algorithm
#   Ref: https://stackoverflow.com/questions/8176298/
#            vf2-algorithm-steps-with-example
#   Ref: https://github.com/satemochi/saaaaah/blob/master/geometric_misc/
#            isomorph/vf2/vf2.py
def graph_is_isomorphic(graph_1, graph_2):
    def is_iso(pairs, matching_node, new_node):
        # Algorithm:
        #   1. The degree is same (It's faster).
        #   2. The connected node is same.
        if matching_node.degree() != new_node.degree():
            return False

        matching_connected = [c.key for c in matching_node.connected_nodes()]
        new_connected = [c.key for c in new_node.connected_nodes()]

        for p in pairs:
            n1 = p[0]
            n2 = p[1]
            if n1 in matching_connected and n2 not in new_connected:
                return False
            if n1 not in matching_connected and n2 in new_connected:
                return False

        return True

    def dfs(graph_1, graph_2):
        def generate_pair(g1, g2, pairs):
            remove_1 = [p[0] for p in pairs]
            remove_2 = [p[1] for p in pairs]

            keys_1 = sorted(list(set(g1.nodes.keys()) - set(remove_1)))
            keys_2 = sorted(list(set(g2.nodes.keys()) - set(remove_2)))
            for k1 in keys_1:
                for k2 in keys_2:
                    yield (k1, k2)

        pairs = []
        stack = [generate_pair(graph_1, graph_2, pairs)]
        while stack:
            try:
                k1, k2 = next(stack[-1])
                n1 = graph_1.get_node(k1)
                n2 = graph_2.get_node(k2)
                if is_iso(pairs, n1, n2):
                    pairs.append([k1, k2])
                    stack.append(generate_pair(graph_1, graph_2, pairs))
                    if len(pairs) == len(graph_1.nodes):
                        return True, pairs
            except StopIteration:
                stack.pop()
                diff = len(pairs) - len(stack)
                for _ in range(diff):
                    pairs.pop()

        return False, []

    # First, check simple condition.
    if len(graph_1.nodes) != len(graph_2.nodes):
        return False, {}
    if len(graph_1.edges) != len(graph_2.edges):
        return False, {}

    is_isomorphic, pairs = dfs(graph_1, graph_2)

    node_pairs = {}
    for pair in pairs:
        n1 = pair[0]
        n2 = pair[1]
        node_1 = graph_1.get_node(n1)
        node_2 = graph_2.get_node(n2)
        node_pairs[node_1] = node_2

    return is_isomorphic, node_pairs
