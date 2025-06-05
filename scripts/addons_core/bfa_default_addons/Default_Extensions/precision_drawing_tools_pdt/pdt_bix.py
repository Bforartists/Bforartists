# SPDX-FileCopyrightText: 2016-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

#
# ----------------------------------------------------------
# Author: Zeffii
# Modified by: Alan Odom (Clockmender) & Rune Morling (ermo)
# ----------------------------------------------------------
#
#
import bpy
import bmesh
from . import pdt_cad_module as cm
from .pdt_msg_strings import (
    PDT_ERR_2CPNPE,
    PDT_ERR_NCEDGES,
    PDT_ERR_EDOB_MODE,
)
from .pdt_functions import debug, oops


def add_line_to_bisection(context):
    """Computes Bisector of 2 Co-Planar Edges.

    Args:
        context: Blender bpy.context instance

    Returns:
        Nothing.
    """

    obj = context.object
    if all([bool(obj), obj.type == "MESH", obj.mode == "EDIT"]):
        pg = context.scene.pdt_pg
        obj_data = obj.data
        bm = bmesh.from_edit_mesh(obj_data)

        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()

        edges = [e for e in bm.edges if e.select and not e.hide]

        if not len(edges) == 2:
            pg.error = f"{PDT_ERR_2CPNPE}"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return

        [[vector_a, vector_b], [vector_c, vector_d]] = [[v.co for v in e.verts] for e in edges]
        debug(f"vectors found:\n {vector_a}\n {vector_b}\n {vector_c}\n {vector_d}")

        dist1 = (vector_a - vector_b).length
        dist2 = (vector_c - vector_d).length
        bdist = min([dist1, dist2])
        edge1 = (vector_a, vector_b)
        edge2 = (vector_c, vector_d)

        if not cm.test_coplanar(edge1, edge2):
            pg.error = PDT_ERR_NCEDGES
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return

        # get intersect_point and pick farthest vertex from (projected) intersections
        intersect_point = cm.get_intersection(edge1, edge2)
        far1 = (
            vector_b
            if (vector_a - intersect_point).length < (vector_b - intersect_point).length
            else vector_a
        )
        far2 = (
            vector_d
            if (vector_c - intersect_point).length < (vector_d - intersect_point).length
            else vector_c
        )

        dex1 = far1 - intersect_point
        dex2 = far2 - intersect_point
        dex1 = dex1 * (bdist / dex1.length)
        dex2 = dex2 * (bdist / dex2.length)
        intersect_point2 = intersect_point + (dex1).lerp(dex2, 0.5)
        intersect_point3 = intersect_point2.lerp(intersect_point, 2.0)

        vec1 = bm.verts.new(intersect_point2)
        vec2 = bm.verts.new(intersect_point)
        vec3 = bm.verts.new(intersect_point3)
        bm.edges.new((vec1, vec2))
        bm.edges.new((vec2, vec3))
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
        bmesh.update_edit_mesh(obj_data)
    else:
        pg.error = f"{PDT_ERR_EDOB_MODE},{obj.mode})"
        context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        return


class PDT_OT_LineOnBisection(bpy.types.Operator):
    """Create Bisector between 2 Selected Edges"""

    bl_idname = "pdt.linetobisect"
    bl_label = "Add Edges Bisector"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """Only allow operation on a mesh object in EDIT mode.

        Args:
            context: Blender bpy.context instance.

        Returns:
            Boolean.
        """

        obj = context.active_object
        if obj is None:
            return False
        return all([obj is not None, obj.type == "MESH", obj.mode == "EDIT"])

    def execute(self, context):
        """Computes Bisector of 2 Co-Planar Edges.

        Note:
            Requires an Active Object
            Active Object must be Mesh type
            Active Object must be in Edit Mode.

        Args:
            context: Blender bpy.context instance.

        Returns:
            Status Set.
        """

        pg = context.scene.pdt_pg
        pg.command = f"bis"
        return {"FINISHED"}
