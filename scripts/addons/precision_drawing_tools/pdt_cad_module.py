# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

#
# ----------------------------------------------------------
# Author: Zeffii
# Modified by: Alan Odom (Clockmender) & Rune Morling (ermo)
# ----------------------------------------------------------
#
import bmesh
from mathutils import Vector
from mathutils.geometry import intersect_line_line, intersect_point_line
from .pdt_functions import debug


def point_on_edge(point, edge):
    """Find Point on Edge.

    Args:
        point:    vector
        edge:     tuple containing 2 vectors.

    Returns:
        True if point happens to lie on the edge, False otherwise.
    """

    intersect_point, _percent = intersect_point_line(point, *edge)
    on_line = (intersect_point - point).length < 1.0e-5
    return on_line and (0.0 <= _percent <= 1.0)


def line_from_edge_intersect(edge1, edge2):
    """Get New Line from Intersections.

    Note:
        Prepares input for sending to intersect_line_line

    Args:
        edge1, edge2: tuples containing 2 vectors.

    Returns:
        Output of intersect_line_line.
    """

    [intersect_point1, intersect_point2], [intersect_point3, intersect_point4] = edge1, edge2
    return intersect_line_line(
        intersect_point1, intersect_point2, intersect_point3, intersect_point4
    )


def get_intersection(edge1, edge2):
    """Get Intersections of 2 Edges.

    Args:
        edge1, edge2: tuples containing 2 vectors.

    Returns:
        The point halfway on line. See intersect_line_line.
    """

    line = line_from_edge_intersect(edge1, edge2)
    if line:
        return (line[0] + line[1]) / 2
    return None


def test_coplanar(edge1, edge2):
    """Test 2 Edges are Co-planar.

    Note:
        The line that describes the shortest line between the two edges would be short if the
        lines intersect mathematically. If this line is longer than 1.0e-5 then they are either
        coplanar or parallel

    Args:
        edge1, edge2: tuples containing 2 vectors.

    Returns:
        True if edge1 and edge2 or coplanar, False otherwise.
    """

    line = line_from_edge_intersect(edge1, edge2)
    if line:
        return (line[0] - line[1]).length < 1.0e-5
    return None


def closest_idx(intersect_point, edge):
    """Get Closest Vertex to input point.

    Note:
        If both points in edge are equally far from intersect_point, then v1 is returned.

    Args:
        intersect_point:       vector
        edge:        bmesh edge

    Returns:
        Index of vertex closest to intersect_point.
    """

    if isinstance(edge, bmesh.types.BMEdge):
        edge_verts = edge.verts
        vector_a = edge_verts[0].co
        vector_b = edge_verts[1].co
        distance_test = (vector_a - intersect_point).length <= (vector_b - intersect_point).length
        return edge_verts[0].index if distance_test else edge_verts[1].index

    debug(f"Received {edge}, check expected input in docstring ")
    return None


def closest_vector(intersect_point, edge):
    """Return Closest Vector to input Point.

    Note:
        If both points in e are equally far from intersect_point, then v1 is returned.

    Args:
        intersect_point:       vector
        edge:        tuple containing 2 vectors

    Returns:
        Vector closest to intersect_point.
    """

    if isinstance(edge, tuple) and all([isinstance(co, Vector) for co in edge]):
        vector_a, vector_b = edge
        distance_test = (vector_a - intersect_point).length <= (vector_b - intersect_point).length
        return vector_a if distance_test else vector_b

    debug(f"Received {edge}, check expected input in docstring ")
    return None


def coords_tuple_from_edge_idx(bm, idx):
    """Return Tuple from Vertices.

    Args:
        bm: Object Bmesh
        idx: Index of chosen Edge

    Returns:
        Tuple from Edge Vertices.
    """

    return tuple(v.co for v in bm.edges[idx].verts)


def vectors_from_indices(bm, raw_vert_indices):
    """Return List of vectors from input Vertex Indices.

    Args:
        bm: Object Bmesh
        raw_vert_indices: List of Chosen Vertex Indices

    Returns:
        List of Vertex coordinates.
    """

    return [bm.verts[i].co for i in raw_vert_indices]


def vertex_indices_from_edges_tuple(bm, edge_tuple):
    """Return List of vertices.

    Args:
        bm:           Active object's Bmesh
        edge_tuple:   contains 2 edge indices.

    Returns:
        The vertex indices of edge_tuple as an Integer list.
    """

    def find_verts(ind_v, ind_w):
        return bm.edges[edge_tuple[ind_v]].verts[ind_w].index

    return [find_verts(i >> 1, i % 2) for i in range(4)]


def get_vert_indices_from_bmedges(edges):
    """Return List of Edges for evaluation.

    Args:
        edges:      a list of 2 bm edges

    Returns:
        The vertex indices of edge_tuple as a flat list.
    """

    temp_edges = []
    debug(edges)
    for e in edges:
        for v in e.verts:
            temp_edges.append(v.index)
    return temp_edges


def num_edges_point_lies_on(intersect_point, edges):
    """Returns the number of edges that a point lies on.

    Args:
        intersection_point: Vector describing 3D coordinates of intersection point
        edges: List of Bmesh edges

    Returns:
        Number of Intersecting Edges (Integer).
    """

    res = [point_on_edge(intersect_point, edge) for edge in [edges[:2], edges[2:]]]
    return len([i for i in res if i])


def find_intersecting_edges(bm, intersect_point, idx1, idx2):
    """Find Intercecting Edges.

    Args:
        intersect_point: Vector describing 3D coordinates of intersection point
        idx1, idx2:    edge indices

    Returns:
        The list of edge indices where intersect_point is on those edges.
    """

    if not intersect_point:
        return []
    idxs = [idx1, idx2]
    edges = [coords_tuple_from_edge_idx(bm, idx) for idx in idxs]
    return [idx for edge, idx in zip(edges, idxs) if point_on_edge(intersect_point, edge)]


def vert_idxs_from_edge_idx(bm, idx):
    """Find Vertex Indices form Edge Indices.

    Args:
        bm: Object's Bmesh
        idx: Selection Index

    Returns:
        Vertex Indices of Edge.
    """

    edge = bm.edges[idx]
    return edge.verts[0].index, edge.verts[1].index
