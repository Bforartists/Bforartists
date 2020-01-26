# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####
#
# <pep8 compliant>
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

def point_on_edge(p, edge):
    """Find Point on Edge.

    Args:
        p:        vector
        edge:     tuple containing 2 vectors.

    Returns:
        True if point p happens to lie on the edge, False otherwise.
    """

    pt, _percent = intersect_point_line(p, *edge)
    on_line = (pt - p).length < 1.0e-5
    return on_line and (0.0 <= _percent <= 1.0)


def line_from_edge_intersect(edge1, edge2):
    """Get New Line from Intersections.

    Prepares input for sending to intersect_line_line

    Args:
        edge1, edge2: tuples containing 2 vectors.

    Returns:
        Output of intersect_line_line.
    """

    [p1, p2], [p3, p4] = edge1, edge2
    return intersect_line_line(p1, p2, p3, p4)


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


def test_coplanar(edge1, edge2):
    """Test 2 Edges are Co-planar.

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


def closest_idx(pt, e):
    """Get Closest Vertex to input point.

    If both points in e are equally far from pt, then v1 is returned.

    Args:
        pt:       vector
        e:        bmesh edge

    Returns:
        Index of vertex closest to pt.
    """

    if isinstance(e, bmesh.types.BMEdge):
        ev = e.verts
        v1 = ev[0].co
        v2 = ev[1].co
        distance_test = (v1 - pt).length <= (v2 - pt).length
        return ev[0].index if distance_test else ev[1].index

    debug(f"Received {e}, check expected input in docstring ")


def closest_vector(pt, e):
    """Return Closest Vector to input Point.

    If both points in e are equally far from pt, then v1 is returned.

    Args:
        pt:       vector
        e:        tuple containing 2 vectors

    Returns:
        Vector closest to pt.
    """

    if isinstance(e, tuple) and all([isinstance(co, Vector) for co in e]):
        v1, v2 = e
        distance_test = (v1 - pt).length <= (v2 - pt).length
        return v1 if distance_test else v2

    debug(f"Received {e}, check expected input in docstring ")


def coords_tuple_from_edge_idx(bm, idx):
    """Return Tuple from Vertex."""
    return tuple(v.co for v in bm.edges[idx].verts)


def vectors_from_indices(bm, raw_vert_indices):
    """Return List of vectors from input indices."""
    return [bm.verts[i].co for i in raw_vert_indices]


def vertex_indices_from_edges_tuple(bm, edge_tuple):
    """Return List of vertices.

    Args:
        bm:           is a bmesh representation
        edge_tuple:   contains 2 edge indices.

    Returns:
        The vertex indices of edge_tuple.
    """

    def k(v, w):
        return bm.edges[edge_tuple[v]].verts[w].index

    return [k(i >> 1, i % 2) for i in range(4)]


def get_vert_indices_from_bmedges(edges):
    """Return List of Edges for evaluation.

    Args:
        bmedges:      a list of 2 bm edges

    Returns:
        The vertex indices of edge_tuple as a flat list.
    """
    temp_edges = []
    debug(edges)
    for e in edges:
        for v in e.verts:
            temp_edges.append(v.index)
    return temp_edges


def num_edges_point_lies_on(pt, edges):
    """Returns the number of edges that a point lies on."""
    res = [point_on_edge(pt, edge) for edge in [edges[:2], edges[2:]]]
    return len([i for i in res if i])


def find_intersecting_edges(bm, pt, idx1, idx2):
    """Find Intercecting Edges.

    Args:
        pt:           Vector
        idx1, ix2:    edge indices

    Returns:
        The list of edge indices where pt is on those edges.
    """
    if not pt:
        return []
    idxs = [idx1, idx2]
    edges = [coords_tuple_from_edge_idx(bm, idx) for idx in idxs]
    return [idx for edge, idx in zip(edges, idxs) if point_on_edge(pt, edge)]


def vert_idxs_from_edge_idx(bm, idx):
    edge = bm.edges[idx]
    return edge.verts[0].index, edge.verts[1].index
