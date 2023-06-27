# SPDX-FileCopyrightText: 2019-2022 Alan Odom (Clockmender)
# SPDX-FileCopyrightText: 2019-2022 Rune Morling (ermo)
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
import bmesh
from math import sqrt, floor, asin, sin, cos, pi
from mathutils import Vector
from bpy.types import Operator

from .pdt_functions import (
    oops,
    arc_centre,
    set_mode,
    view_coords,
    view_coords_i,
)

from .pdt_msg_strings import (
    PDT_OBJ_MODE_ERROR,
    PDT_ERR_NO_ACT_OBJ,
    PDT_ERR_SEL_3_VERTS,
    PDT_ERR_SEL_1_VERT,
    PDT_ERR_BADDISTANCE,
    PDT_ERR_MATHSERROR,
    PDT_ERR_SAMERADII,
    PDT_ERR_VERT_MODE,
)

from . import pdt_exception

PDT_ObjectModeError = pdt_exception.ObjectModeError
PDT_SelectionError = pdt_exception.SelectionError


def get_tangent_intersect_outer(hloc_0, vloc_0, hloc_1, vloc_1, radius_0, radius_1):
    """Return Location in 2 Dimensions of the Intersect Point for Outer Tangents.

    Args:
        hloc_0: Horizontal Coordinate of Centre of First Arc
        vloc_0: Vertical Coordinate of Centre of First Arc
        hloc_1: Horizontal Coordinate of Centre of Second Arc
        vloc_1: Vertical Coordinate of Centre of Second Arc
        radius_0: Radius of First Arc
        radius_1: Radius of Second Arc

    Returns:
        hloc_p: Horizontal Coordinate of Centre of Intersection
        vloc_p: Vertical Coordinate of Centre of Intersection.
    """

    hloc_p = ((hloc_1 * radius_0) - (hloc_0 * radius_1)) / (radius_0 - radius_1)
    vloc_p = ((vloc_1 * radius_0) - (vloc_0 * radius_1)) / (radius_0 - radius_1)

    return hloc_p, vloc_p


def get_tangent_intersect_inner(hloc_0, vloc_0, hloc_1, vloc_1, radius_0, radius_1):
    """Return Location in 2 Dimensions of the Intersect Point for Inner Tangents.

    Args:
        hloc_0: Horizontal Coordinate of Centre of First Arc
        vloc_0: Vertical Coordinate of Centre of First Arc
        hloc_1: Horizontal Coordinate of Centre of Second Arc
        vloc_1: Vertical Coordinate of Centre of Second Arc
        radius_0: Radius of First Arc
        radius_1: Radius of Second Arc

    Returns:
        hloc_p: Horizontal Coordinate of Centre of Intersection
        vloc_p: Vertical Coordinate of Centre of Intersection.
    """

    hloc_p = ((hloc_1 * radius_0) + (hloc_0 * radius_1)) / (radius_0 + radius_1)
    vloc_p = ((vloc_1 * radius_0) + (vloc_0 * radius_1)) / (radius_0 + radius_1)

    return hloc_p, vloc_p


def get_tangent_points(context, hloc_0, vloc_0, radius_0, hloc_p, vloc_p):
    """Return Location in 2 Dimensions of the Tangent Points.

    Args:
        context: Blender bpy.context instance
        hloc_0: Horizontal Coordinate of Centre of First Arc
        vloc_0: Vertical Coordinate of Centre of First Arc
        radius_0: Radius of First Arc
        hloc_p: Horizontal Coordinate of Intersection
        vloc_p: Vertical Coordinate of Intersection

    Returns:
        hloc_t1: Horizontal Location of First Tangent Point
        hloc_t2: Horizontal Location of Second Tangent Point
        vloc_t1: Vertical Location of First Tangent Point
        vloc_t2: Vertical Location of Second Tangent Point
    """

    # Uses basic Pythagorus' theorem to compute locations
    #
    numerator = (radius_0 ** 2 * (hloc_p - hloc_0)) + (
        radius_0
        * (vloc_p - vloc_0)
        * sqrt((hloc_p - hloc_0) ** 2 + (vloc_p - vloc_0) ** 2 - radius_0 ** 2)
    )
    denominator = (hloc_p - hloc_0) ** 2 + (vloc_p - vloc_0) ** 2
    hloc_t1 = round((numerator / denominator) + hloc_0, 5)

    numerator = (radius_0 ** 2 * (hloc_p - hloc_0)) - (
        radius_0
        * (vloc_p - vloc_0)
        * sqrt((hloc_p - hloc_0) ** 2 + (vloc_p - vloc_0) ** 2 - radius_0 ** 2)
    )
    denominator = (hloc_p - hloc_0) ** 2 + (vloc_p - vloc_0) ** 2
    hloc_t2 = round((numerator / denominator) + hloc_0, 5)

    # Get Y values
    numerator = (radius_0 ** 2 * (vloc_p - vloc_0)) - (
        radius_0
        * (hloc_p - hloc_0)
        * sqrt((hloc_p - hloc_0) ** 2 + (vloc_p - vloc_0) ** 2 - radius_0 ** 2)
    )
    denominator = (hloc_p - hloc_0) ** 2 + (vloc_p - vloc_0) ** 2
    vloc_t1 = round((numerator / denominator) + vloc_0, 5)

    numerator = (radius_0 ** 2 * (vloc_p - vloc_0)) + (
        radius_0
        * (hloc_p - hloc_0)
        * sqrt((hloc_p - hloc_0) ** 2 + (vloc_p - vloc_0) ** 2 - radius_0 ** 2)
    )
    denominator = (hloc_p - hloc_0) ** 2 + (vloc_p - vloc_0) ** 2
    vloc_t2 = round((numerator / denominator) + vloc_0, 5)

    return hloc_t1, hloc_t2, vloc_t1, vloc_t2


def make_vectors(coords, a1, a2, a3, pg):
    """Return Vectors of the Tangent Points.

    Args:
        coords: A List of Coordinates in 2D space of the tangent points
                & a third dimension for the vectors
        a1: Index of horizontal axis
        a2: Index of vertical axis
        a3: Index of depth axis
        pg: PDT Parameters Group - our variables

    Returns:
        tangent_vector_o1: Location of First Tangent Point
        tangent_vector_o2: Location of Second Tangent Point
        tangent_vector_o3: Location of First Tangent Point
        tangent_vector_o4: Location of Second Tangent Point
    """

    tangent_vector_o1 = Vector((0, 0, 0))
    tangent_vector_o1[a1] = coords[0]
    tangent_vector_o1[a2] = coords[1]
    tangent_vector_o1[a3] = coords[8]
    tangent_vector_o2 = Vector((0, 0, 0))
    tangent_vector_o2[a1] = coords[2]
    tangent_vector_o2[a2] = coords[3]
    tangent_vector_o2[a3] = coords[8]
    tangent_vector_o3 = Vector((0, 0, 0))
    tangent_vector_o3[a1] = coords[4]
    tangent_vector_o3[a2] = coords[5]
    tangent_vector_o3[a3] = coords[8]
    tangent_vector_o4 = Vector((0, 0, 0))
    tangent_vector_o4[a1] = coords[6]
    tangent_vector_o4[a2] = coords[7]
    tangent_vector_o4[a3] = coords[8]

    if pg.plane == "LO":
        # Reset coordinates from view local (Horiz, Vert, depth) to World XYZ.
        #
        tangent_vector_o1 = view_coords(
            tangent_vector_o1[a1], tangent_vector_o1[a2], tangent_vector_o1[a3]
        )
        tangent_vector_o2 = view_coords(
            tangent_vector_o2[a1], tangent_vector_o2[a2], tangent_vector_o2[a3]
        )
        tangent_vector_o3 = view_coords(
            tangent_vector_o3[a1], tangent_vector_o3[a2], tangent_vector_o3[a3]
        )
        tangent_vector_o4 = view_coords(
            tangent_vector_o4[a1], tangent_vector_o4[a2], tangent_vector_o4[a3]
        )

    return (tangent_vector_o1, tangent_vector_o2, tangent_vector_o3, tangent_vector_o4)


def tangent_setup(context, pg, plane, obj_data, centre_0, centre_1, centre_2, radius_0, radius_1):
    """This section sets up all the variables required for the tangent functions.

    Args:
        context: Blender bpy.context instance
        pg: PDT Parameter Group of variables
        plane: Working plane
        obj_data: All the data of the chosen object
        centre_0: Centre coordinates of the first arc
        centre_1: Centre coordinates of the second arc
        centre_2: Coordinates of the point
        radius_0: Radius of the first Arc
        radius_1: Radius of the second Arc

    Returns:
        Status Set.
    """

    a1, a2, a3 = set_mode(plane)
    mode = pg.tangent_mode
    if plane == "LO":
        # Translate world coordinates into view local (horiz, vert, depth)
        #
        centre_0 = view_coords_i(centre_0[a1], centre_0[a2], centre_0[a3])
        centre_1 = view_coords_i(centre_1[a1], centre_1[a2], centre_1[a3])
        centre_2 = view_coords_i(centre_2[a1], centre_2[a2], centre_2[a3])
    if pg.tangent_mode == "point":
        vector_difference = centre_2 - centre_0
        distance = sqrt(vector_difference[a1] ** 2 + vector_difference[a2] ** 2)
    else:
        vector_difference = centre_1 - centre_0
        distance = sqrt(vector_difference[a1] ** 2 + vector_difference[a2] ** 2)

    if (
        (distance <= radius_0 and mode in {"point"}) or
        (distance <= (radius_0 + radius_1) and mode in {"inner", "both"}) or
        (distance <= radius_0 or distance <= radius_1 and mode in {"outer", "both"})
        ):
        # Cannot execute, centres are too close.
        #
        pg.error = f"{PDT_ERR_BADDISTANCE}"
        context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        return {"FINISHED"}

    """This next section will draw Point based Tangents.

        These are drawn from a point to an Arc
    """

    if mode == "point":
        if (
            (centre_2[a1] - centre_0[a1]) ** 2 + (centre_2[a2] - centre_0[a2]) ** 2 - radius_0 ** 2
        ) > 0:
            hloc_to1, hloc_to2, vloc_to1, vloc_to2 = get_tangent_points(
                context, centre_0[a1], centre_0[a2], radius_0, centre_2[a1], centre_2[a2]
            )
        else:
            pg.error = PDT_ERR_MATHSERROR
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return {"FINISHED"}
        # Point Tangents
        #
        tangent_vector_o1 = Vector((0, 0, 0))
        tangent_vector_o1[a1] = hloc_to1
        tangent_vector_o1[a2] = vloc_to1
        tangent_vector_o1[a3] = centre_2[a3]
        tangent_vector_o2 = Vector((0, 0, 0))
        tangent_vector_o2[a1] = hloc_to2
        tangent_vector_o2[a2] = vloc_to2
        tangent_vector_o2[a3] = centre_2[a3]
        if pg.plane == "LO":
            # Translate view local coordinates (horiz, vert, depth) into World XYZ
            #
            centre_2 = view_coords(centre_2[a1], centre_2[a2], centre_2[a3])
            tangent_vector_o1 = view_coords(
                tangent_vector_o1[a1], tangent_vector_o1[a2], tangent_vector_o1[a3]
            )
            tangent_vector_o2 = view_coords(
                tangent_vector_o2[a1], tangent_vector_o2[a2], tangent_vector_o2[a3]
            )
        tangent_vectors = (centre_2, tangent_vector_o1, tangent_vector_o2)
        draw_tangents(tangent_vectors, obj_data)

        return {"FINISHED"}

    """This next section will draw Arc based Outer Tangents.

        These are drawn from an Arc to another Arc
    """

    if mode in {"outer", "both"}:
        # Uses basic trigonometry and Pythagorus' theorem to compute locations
        #
        if radius_0 == radius_1:
            # No intersection point for outer tangents
            #
            sin_angle = (centre_1[a2] - centre_0[a2]) / distance
            cos_angle = (centre_1[a1] - centre_0[a1]) / distance
            hloc_to1 = centre_0[a1] + (radius_0 * sin_angle)
            hloc_to2 = centre_0[a1] - (radius_0 * sin_angle)
            hloc_to3 = centre_1[a1] + (radius_0 * sin_angle)
            hloc_to4 = centre_1[a1] - (radius_0 * sin_angle)
            vloc_to1 = centre_0[a2] - (radius_0 * cos_angle)
            vloc_to2 = centre_0[a2] + (radius_0 * cos_angle)
            vloc_to3 = centre_1[a2] - (radius_0 * cos_angle)
            vloc_to4 = centre_1[a2] + (radius_0 * cos_angle)
        else:
            hloc_po, vloc_po = get_tangent_intersect_outer(
                centre_0[a1], centre_0[a2], centre_1[a1], centre_1[a2], radius_0, radius_1
            )

            if ((hloc_po - centre_0[a1]) ** 2 + (vloc_po - centre_0[a2]) ** 2 - radius_0 ** 2) > 0:
                hloc_to1, hloc_to2, vloc_to1, vloc_to2 = get_tangent_points(
                    context, centre_0[a1], centre_0[a2], radius_0, hloc_po, vloc_po
                )
            else:
                pg.error = PDT_ERR_MATHSERROR
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return {"FINISHED"}
            if ((hloc_po - centre_0[a1]) ** 2 + (vloc_po - centre_0[a2]) ** 2 - radius_1 ** 2) > 0:
                hloc_to3, hloc_to4, vloc_to3, vloc_to4 = get_tangent_points(
                    context, centre_1[a1], centre_1[a2], radius_1, hloc_po, vloc_po
                )
            else:
                pg.error = PDT_ERR_MATHSERROR
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return {"FINISHED"}

        dloc_p = centre_0[a3]
        coords_in = (
            hloc_to1,
            vloc_to1,
            hloc_to2,
            vloc_to2,
            hloc_to3,
            vloc_to3,
            hloc_to4,
            vloc_to4,
            dloc_p,
        )
        tangent_vectors = make_vectors(coords_in, a1, a2, a3, pg)
        draw_tangents(tangent_vectors, obj_data)

    """This next section will draw Arc based Inner Tangents.

        These are drawn from an Arc to another Arc
    """

    if mode in {"inner", "both"}:
        # Uses basic trigonometry and Pythagorus' theorem to compute locations
        #
        hloc_pi, vloc_pi = get_tangent_intersect_inner(
            centre_0[a1], centre_0[a2], centre_1[a1], centre_1[a2], radius_0, radius_1
        )
        if ((hloc_pi - centre_0[a1]) ** 2 + (vloc_pi - centre_0[a2]) ** 2 - radius_0 ** 2) > 0:
            hloc_to1, hloc_to2, vloc_to1, vloc_to2 = get_tangent_points(
                context, centre_0[a1], centre_0[a2], radius_0, hloc_pi, vloc_pi
            )
        else:
            pg.error = PDT_ERR_MATHSERROR
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return {"FINISHED"}
        if ((hloc_pi - centre_0[a1]) ** 2 + (vloc_pi - centre_0[a2]) ** 2 - radius_0 ** 2) > 0:
            hloc_to3, hloc_to4, vloc_to3, vloc_to4 = get_tangent_points(
                context, centre_1[a1], centre_1[a2], radius_1, hloc_pi, vloc_pi
            )
        else:
            pg.error = PDT_ERR_MATHSERROR
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return {"FINISHED"}

        dloc_p = centre_0[a3]
        coords_in = (
            hloc_to1,
            vloc_to1,
            hloc_to2,
            vloc_to2,
            hloc_to3,
            vloc_to3,
            hloc_to4,
            vloc_to4,
            dloc_p,
        )
        tangent_vectors = make_vectors(coords_in, a1, a2, a3, pg)
        draw_tangents(tangent_vectors, obj_data)

    return {"FINISHED"}


def draw_tangents(tangent_vectors, obj_data):
    """Add Edges Representing the Tangents.

    Note:
        The length of the tanget_vectors determines which tangents will be
        drawn, 3 gives Point Tangents, 4 gives Inner/Outer tangents

    Args:
        tangent_vectors: A list of vectors representing the tangents
        obj_data: A list giving Object, Object Location and Object Bmesh

    Returns:
        Nothing.
    """
    obj = obj_data[0]
    obj_loc = obj_data[1]
    bm = obj_data[2]
    if len(tangent_vectors) == 3:
        point_vertex_outer = bm.verts.new(tangent_vectors[0] - obj_loc)
        tangent_vertex_o1 = bm.verts.new(tangent_vectors[1] - obj_loc)
        tangent_vertex_o2 = bm.verts.new(tangent_vectors[2] - obj_loc)
        bm.edges.new([tangent_vertex_o1, point_vertex_outer])
        bm.edges.new([tangent_vertex_o2, point_vertex_outer])
    else:
        tangent_vertex_o1 = bm.verts.new(tangent_vectors[0] - obj_loc)
        tangent_vertex_o2 = bm.verts.new(tangent_vectors[2] - obj_loc)
        tangent_vertex_o3 = bm.verts.new(tangent_vectors[1] - obj_loc)
        tangent_vertex_o4 = bm.verts.new(tangent_vectors[3] - obj_loc)
        bm.edges.new([tangent_vertex_o1, tangent_vertex_o2])
        bm.edges.new([tangent_vertex_o3, tangent_vertex_o4])
    bmesh.update_edit_mesh(obj.data)


def analyse_arc(context, pg):
    """Analyses an Arc inferred from Selected Vertices.

    Note:
        Will work if more than 3 vertices are selected, taking the
        first, the nearest to the middle and the last.

    Args:
        context: Blender bpy.context instance
        pg: PDT Parameters Group - our variables

    Returns:
        vector_delta: Location of Arc Centre
        radius: Radius of Arc.
    """
    obj = context.view_layer.objects.active
    if obj is None:
        pg.error = PDT_ERR_NO_ACT_OBJ
        context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        raise PDT_ObjectModeError
    if obj.mode == "EDIT":
        obj_loc = obj.matrix_world.decompose()[0]
        bm = bmesh.from_edit_mesh(obj.data)
        verts = [v for v in bm.verts if v.select]
        if len(verts) < 3:
            pg.error = f"{PDT_ERR_SEL_3_VERTS} {len(verts)})"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            raise PDT_SelectionError
        vector_a = verts[0].co
        # Get the nearest to middle vertex of the arc
        #
        vector_b = verts[int(floor(len(verts) / 2))].co
        vector_c = verts[-1].co
        vector_delta, radius = arc_centre(vector_a, vector_b, vector_c)

        return vector_delta, radius


class PDT_OT_TangentOperate(Operator):
    """Calculate Tangents from Inputs."""

    bl_idname = "pdt.tangentoperate"
    bl_label = "Calculate Tangents"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Calculate Tangents to Arcs from Points or Other Arcs"

    @classmethod
    def poll(cls, context):
        ob = context.object
        if ob is None:
            return False
        return all([bool(ob), ob.type == "MESH", ob.mode == "EDIT"])

    def execute(self, context):
        """Calculate Tangents from Inputs.

        Note:
            Uses pg.plane, pg.tangent_point0, pg.tangent_radius0, pg.tangent_point1
            pg.tangent_radius1, pg.tangent_point2 to place tangents.

            Analyses distance between arc centres, or arc centre and tangent point
            to determine which mode is possible (Inner, Outer, or Point). If centres are
            both contained within 1 inferred circle, Inner tangents are not possible.

            Arcs of same radius will have no intersection for outer tangents so these
            are calculated differently.

        Args:
            context: Blender bpy.context instance.

        Returns:
            Nothing.
        """

        scene = context.scene
        pg = scene.pdt_pg
        plane = pg.plane
        # Get Object
        obj = context.view_layer.objects.active
        if obj is not None:
            if obj.mode not in {"EDIT"} or obj.type != "MESH":
                pg.error = PDT_OBJ_MODE_ERROR
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return {"FINISHED"}
        else:
            pg.error = PDT_ERR_NO_ACT_OBJ
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return {"FINISHED"}
        bm = bmesh.from_edit_mesh(obj.data)
        obj_loc = obj.matrix_world.decompose()[0]
        obj_data = (obj, obj_loc, bm)

        radius_0 = pg.tangent_radius0
        radius_1 = pg.tangent_radius1
        centre_0 = pg.tangent_point0
        centre_1 = pg.tangent_point1
        centre_2 = pg.tangent_point2

        tangent_setup(
            context, pg, plane, obj_data, centre_0, centre_1, centre_2, radius_0, radius_1
        )

        return {"FINISHED"}


class PDT_OT_TangentOperateSel(Operator):
    """Calculate Tangents from Selection."""

    bl_idname = "pdt.tangentoperatesel"
    bl_label = "Calculate Tangents"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Calculate Tangents to Arcs from 2 Selected Vertices, or 1 & Point in Menu"

    @classmethod
    def poll(cls, context):
        ob = context.object
        if ob is None:
            return False
        return all([bool(ob), ob.type == "MESH", ob.mode == "EDIT"])

    def execute(self, context):
        """Calculate Tangents from Selection.

        Note:
            Uses pg.plane & 2 or more selected Vertices to place tangents.
            One vertex must be on each arc.

            Analyses distance between arc centres, or arc centre and tangent point
            to determine which mode is possible (Inner, Outer, or Point). If centres are
            both contained within 1 inferred circle, Inner tangents are not possible.

            Arcs of same radius will have no intersection for outer tangents so these
            are calculated differently.

        Args:
            context: Blender bpy.context instance.

        Returns:
            Nothing.
        """

        scene = context.scene
        pg = scene.pdt_pg
        plane = pg.plane
        # Get Object
        obj = context.view_layer.objects.active
        if obj is not None:
            if obj.mode not in {"EDIT"} or obj.type != "MESH":
                pg.error = PDT_OBJ_MODE_ERROR
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return {"FINISHED"}
        else:
            pg.error = PDT_ERR_NO_ACT_OBJ
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return {"FINISHED"}
        bm = bmesh.from_edit_mesh(obj.data)
        obj_loc = obj.matrix_world.decompose()[0]
        obj_data = (obj, obj_loc, bm)

        # Get All Values from Selected Vertices
        verts = [v for v in bm.verts if v.select]
        if len(verts) <= 0:
            pg.error = f"{PDT_ERR_SEL_1_VERT} 0"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return {"FINISHED"}
        v1 = verts[0]
        vn = verts[-1]
        for v in bm.verts:
            v.select_set(False)
        for e in bm.edges:
            e.select_set(False)
        v1.select_set(True)
        bpy.ops.mesh.select_linked()
        verts1 = [v for v in bm.verts if v.select].copy()
        if len(verts1) < 3:
            pg.error = f"{PDT_ERR_VERT_MODE} or Less than 3 vertices in your Arc(s)"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return {"FINISHED"}
        for v in bm.verts:
            v.select_set(False)
        for e in bm.edges:
            e.select_set(False)
        vn.select_set(True)
        bpy.ops.mesh.select_linked()
        vertsn = [v for v in bm.verts if v.select].copy()
        for v in bm.verts:
            v.select_set(False)
        for e in bm.edges:
            e.select_set(False)
        bmesh.update_edit_mesh(obj.data)
        bm.select_history.clear()
        # Select the nearest to middle vertex in the arc
        #
        verts1 = [verts1[0].co, verts1[int(floor(len(verts1) / 2))].co, verts1[-1].co]
        vertsn = [vertsn[0].co, vertsn[int(floor(len(vertsn) / 2))].co, vertsn[-1].co]
        centre_0, radius_0 = arc_centre(verts1[0], verts1[1], verts1[2])
        centre_1, radius_1 = arc_centre(vertsn[0], vertsn[1], vertsn[2])
        centre_2 = pg.tangent_point2

        tangent_setup(
            context, pg, plane, obj_data, centre_0, centre_1, centre_2, radius_0, radius_1
        )

        return {"FINISHED"}


class PDT_OT_TangentSet1(Operator):
    """Calculates Centres & Radii from 3 Vectors."""

    bl_idname = "pdt.tangentset1"
    bl_label = "Calculate Centres & Radii"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Calculate Centres & Radii from Selected Vertices"

    @classmethod
    def poll(cls, context):
        ob = context.object
        if ob is None:
            return False
        return all([bool(ob), ob.type == "MESH", ob.mode == "EDIT"])

    def execute(self, context):
        """Sets Input Tangent Point 1 to analysis of Arc.

        Args:
            context: Blender bpy.context instance.

        Returns:
            Nothing.
        """
        scene = context.scene
        pg = scene.pdt_pg
        vector_delta, radius = analyse_arc(context, pg)
        pg.tangent_point0 = vector_delta
        pg.tangent_radius0 = radius
        return {"FINISHED"}


class PDT_OT_TangentSet2(Operator):
    """Calculates Centres & Radii from 3 Vectors."""

    bl_idname = "pdt.tangentset2"
    bl_label = "Calculate Centres & Radii"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Calculate Centres & Radii from Selected Vertices"

    @classmethod
    def poll(cls, context):
        obj = context.object
        if obj is None:
            return False
        return all([bool(obj), obj.type == "MESH", obj.mode == "EDIT"])

    def execute(self, context):
        """Sets Input Tangent Point 2 to analysis of Arc.

        Args:
            context: Blender bpy.context instance.

        Returns:
            Nothing.
        """
        scene = context.scene
        pg = scene.pdt_pg
        vector_delta, radius = analyse_arc(context, pg)
        pg.tangent_point1 = vector_delta
        pg.tangent_radius1 = radius
        return {"FINISHED"}


class PDT_OT_TangentSet3(Operator):
    """Set Tangent Origin Point from Cursor."""

    bl_idname = "pdt.tangentset3"
    bl_label = "Set Tangent Origin Point from Cursor"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Set Tangent Origin Point from Cursor"

    @classmethod
    def poll(cls, context):
        obj = context.object
        if obj is None:
            return False
        return all([bool(obj), obj.type == "MESH", obj.mode == "EDIT"])

    def execute(self, context):
        """Sets Input Tangent Point 3 to analysis of Arc.

        Args:
            context: Blender bpy.context instance.

        Returns:
            Nothing.
        """
        scene = context.scene
        pg = scene.pdt_pg
        pg.tangent_point2 = scene.cursor.location
        return {"FINISHED"}


class PDT_OT_TangentSet4(Operator):
    """Set Tangent Origin Point from Cursor."""

    bl_idname = "pdt.tangentset4"
    bl_label = "Set Tangent Origin Point from Vertex"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Set Tangent Origin Point from Vertex"

    @classmethod
    def poll(cls, context):
        obj = context.object
        if obj is None:
            return False
        return all([bool(obj), obj.type == "MESH", obj.mode == "EDIT"])

    def execute(self, context):
        """Sets Input Tangent Point 2 to selected Vertex.

        Args:
            context: Blender bpy.context instance.

        Returns:
            Nothing.
        """
        scene = context.scene
        pg = scene.pdt_pg
        obj = context.object
        bm = bmesh.from_edit_mesh(obj.data)
        verts = [v for v in bm.verts if v.select]
        if len(verts) != 1:
            pg.error = f"{PDT_ERR_SEL_1_VERT} {len(verts)})"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            raise PDT_SelectionError
        pg.tangent_point2 = verts[0].co
        return {"FINISHED"}


class PDT_OT_TangentExpandMenu(Operator):
    """Expand/Collapse Tangent Menu."""

    bl_idname = "pdt.tangentexpandmenu"
    bl_label = "Expand/Collapse Tangent Menu"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Expand/Collapse Tangent Menu to Show/Hide Input Options"

    def execute(self, context):
        """Expand/Collapse Tangent Menu.

        Note:
            This is used to add further options to the menu.

        Args:
            context: Blender bpy.context instance.

        Returns:
            Nothing.
        """
        scene = context.scene
        pg = scene.pdt_pg
        if pg.menu_expand:
            pg.menu_expand = False
        else:
            pg.menu_expand = True
        return {"FINISHED"}
