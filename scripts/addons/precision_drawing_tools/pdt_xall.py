# SPDX-FileCopyrightText: 2016-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

#
# ----------------------------------------------------------
# Author: Zeffii
# Modified by: Alan Odom (Clockmender) & Rune Morling (ermo)
# ----------------------------------------------------------
#
import bpy
import bmesh
from mathutils.geometry import intersect_line_line as LineIntersect
import itertools
from collections import defaultdict
from . import pdt_cad_module as cm
from .pdt_functions import oops
from .pdt_msg_strings import (
    PDT_ERR_EDOB_MODE
)


def order_points(edge, point_list):
    """Order these edges from distance to v1, then sandwich the sorted list with v1, v2."""
    v1, v2 = edge

    def dist(coord):
        """Measure distance between two coordinates."""

        return (v1 - coord).length

    point_list = sorted(point_list, key=dist)
    return [v1] + point_list + [v2]


def remove_permutations_that_share_a_vertex(bm, permutations):
    """Get useful Permutations.

    Args:
        bm: Object's Bmesh
        permutations: Possible Intersection Edges as a list

    Returns:
        List of Edges.
    """

    final_permutations = []
    for edges in permutations:
        raw_vert_indices = cm.vertex_indices_from_edges_tuple(bm, edges)
        if len(set(raw_vert_indices)) < 4:
            continue

        # reaches this point if they do not share.
        final_permutations.append(edges)

    return final_permutations


def get_valid_permutations(bm, edge_indices):
    """Get useful Permutations.

    Args:
        bm: Object's Bmesh
        edge_indices: List of indices of Edges to consider

    Returns:
        List of suitable Edges.
    """

    raw_permutations = itertools.permutations(edge_indices, 2)
    permutations = [r for r in raw_permutations if r[0] < r[1]]
    return remove_permutations_that_share_a_vertex(bm, permutations)


def can_skip(closest_points, vert_vectors):
    """Check if the intersection lies on both edges and return True
    when criteria are not met, and thus this point can be skipped.

    Args:
        closest_points: List of Coordinates of points to consider
        vert_vectors: List of Coordinates of vertices to consider

    Returns:
        Boolean.
    """

    if not closest_points:
        return True
    if not isinstance(closest_points[0].x, float):
        return True
    if cm.num_edges_point_lies_on(closest_points[0], vert_vectors) < 2:
        return True

    # if this distance is larger than than 1.0e-5, we can skip it.
    cpa, cpb = closest_points
    return (cpa - cpb).length > 1.0e-5


def get_intersection_dictionary(bm, edge_indices):
    """Return a dictionary of edge indices and points found on those edges.

    Args:
        bm, Object's Bmesh
        edge_indices: List of Edge Indices

    Returns:
        Dictionary of Vectors.
    """

    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()

    permutations = get_valid_permutations(bm, edge_indices)

    list_k = defaultdict(list)
    list_d = defaultdict(list)

    for edges in permutations:
        raw_vert_indices = cm.vertex_indices_from_edges_tuple(bm, edges)
        vert_vectors = cm.vectors_from_indices(bm, raw_vert_indices)

        points = LineIntersect(*vert_vectors)

        # some can be skipped.    (NaN, None, not on both edges)
        if can_skip(points, vert_vectors):
            continue

        # reaches this point only when an intersection happens on both edges.
        [list_k[edge].append(points[0]) for edge in edges]

    # list_k will contain a dict of edge indices and points found on those edges.
    for edge_idx, unordered_points in list_k.items():
        tv1, tv2 = bm.edges[edge_idx].verts
        v1 = bm.verts[tv1.index].co
        v2 = bm.verts[tv2.index].co
        ordered_points = order_points((v1, v2), unordered_points)
        list_d[edge_idx].extend(ordered_points)

    return list_d


def update_mesh(bm, int_dict):
    """Make new geometry (delete old first).

    Args:
        bm, Object's Bmesh
        int_dict: Dictionary of Indices of Vertices

    Returns:
        Nothing.
    """

    orig_e = bm.edges
    orig_v = bm.verts

    new_verts = []
    collect = new_verts.extend
    for _, point_list in int_dict.items():
        num_edges_to_add = len(point_list) - 1
        for i in range(num_edges_to_add):
            coord_a = orig_v.new(point_list[i])
            coord_b = orig_v.new(point_list[i + 1])
            orig_e.new((coord_a, coord_b))
            bm.normal_update()
            collect([coord_a, coord_b])

    bmesh.ops.delete(bm, geom=[edge for edge in bm.edges if edge.select], context="EDGES")
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)


def unselect_nonintersecting(bm, d_edges, edge_indices):
    """Deselects Non-Intersection Edges.

    Args:
        bm, Object's Bmesh
        d_edges: List of Intersecting Edges
        edge_indices: List of Edge Indices to consider

    Returns:
        Nothing.
    """

    if len(edge_indices) > len(d_edges):
        reserved_edges = set(edge_indices) - set(d_edges)
        for edge in reserved_edges:
            bm.edges[edge].select = False


def intersect_all(context):
    """Computes All intersections with Crossing Geometry.

    Note:
        Deletes original edges and replaces with new intersected edges

    Args:
        context: Blender bpy.context instance.

    Returns:
        Status Set.
    """

    pg = context.scene.pdt_pg
    obj = context.active_object
    if all([bool(obj), obj.type == "MESH", obj.mode == "EDIT"]):
        # must force edge selection mode here
        bpy.context.tool_settings.mesh_select_mode = (False, True, False)


        if obj.mode == "EDIT":
            bm = bmesh.from_edit_mesh(obj.data)

            selected_edges = [edge for edge in bm.edges if edge.select]
            edge_indices = [i.index for i in selected_edges]

            int_dict = get_intersection_dictionary(bm, edge_indices)

            unselect_nonintersecting(bm, int_dict.keys(), edge_indices)
            update_mesh(bm, int_dict)

            bmesh.update_edit_mesh(obj.data)
        else:
            pg.error = f"{PDT_ERR_EDOB_MODE},{obj.mode})"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return

        return
    else:
        pg.error = f"{PDT_ERR_EDOB_MODE},{obj.mode})"
        context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        return

class PDT_OT_IntersectAllEdges(bpy.types.Operator):
    """Cut Selected Edges at All Intersections"""

    bl_idname = "pdt.intersectall"
    bl_label = "Intersect All Edges"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """Check to see object is in correct condition.

        Args:
            context: Blender bpy.context instance.

        Returns:
            Boolean
        """
        obj = context.active_object
        if obj is None:
            return False
        return obj is not None and obj.type == "MESH" and obj.mode == "EDIT"

    def execute(self, context):
        """Computes All intersections with Crossing Geometry.

        Note:
            Deletes original edges and replaces with new intersected edges

        Args:
            context: Blender bpy.context instance.

        Returns:
            Status Set.
        """

        pg = context.scene.pdt_pg
        pg.command = f"intall"
        return {"FINISHED"}
