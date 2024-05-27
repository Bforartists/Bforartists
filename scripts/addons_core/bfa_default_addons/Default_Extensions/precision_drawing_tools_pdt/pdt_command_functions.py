# SPDX-FileCopyrightText: 2019-2022 Alan Odom (Clockmender)
# SPDX-FileCopyrightText: 2019-2022 Rune Morling (ermo)
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bmesh
import numpy as np
from math import sqrt, tan, pi
from mathutils import Vector
from mathutils.geometry import intersect_point_line
from .pdt_functions import (
    set_mode,
    oops,
    get_percent,
    dis_ang,
    check_selection,
    arc_centre,
    intersection,
    view_coords_i,
    view_coords,
    view_dir,
    set_axis,
)

from . import pdt_exception
PDT_SelectionError = pdt_exception.SelectionError
PDT_InvalidVector = pdt_exception.InvalidVector
PDT_ObjectModeError = pdt_exception.ObjectModeError
PDT_InfRadius = pdt_exception.InfRadius
PDT_NoObjectError = pdt_exception.NoObjectError
PDT_IntersectionError = pdt_exception.IntersectionError
PDT_InvalidOperation = pdt_exception.InvalidOperation
PDT_VerticesConnected = pdt_exception.VerticesConnected
PDT_InvalidAngle = pdt_exception.InvalidAngle

from .pdt_msg_strings import (
    PDT_ERR_BAD3VALS,
    PDT_ERR_BAD2VALS,
    PDT_ERR_BAD1VALS,
    PDT_ERR_CONNECTED,
    PDT_ERR_SEL_2_VERTS,
    PDT_ERR_EDOB_MODE,
    PDT_ERR_NO_ACT_OBJ,
    PDT_ERR_VERT_MODE,
    PDT_ERR_SEL_3_VERTS,
    PDT_ERR_SEL_3_OBJS,
    PDT_ERR_EDIT_MODE,
    PDT_ERR_NON_VALID,
    PDT_LAB_NOR,
    PDT_ERR_STRIGHT_LINE,
    PDT_LAB_ARCCENTRE,
    PDT_ERR_SEL_4_VERTS,
    PDT_ERR_INT_NO_ALL,
    PDT_LAB_INTERSECT,
    PDT_ERR_SEL_4_OBJS,
    PDT_INF_OBJ_MOVED,
    PDT_ERR_SEL_2_VERTIO,
    PDT_ERR_SEL_2_OBJS,
    PDT_ERR_SEL_3_VERTIO,
    PDT_ERR_TAPER_ANG,
    PDT_ERR_TAPER_SEL,
    PDT_ERR_INT_LINES,
    PDT_LAB_PLANE,
)


def vector_build(context, pg, obj, operation, values, num_values):
    """Build Movement Vector from Input Fields.

    Args:
        context: Blender bpy.context instance.
        pg: PDT Parameters Group - our variables
        obj: The Active Object
        operation: The Operation e.g. Create New Vertex
        values: The parameters passed e.g. 1,4,3 for Cartesian Coordinates
        num_values: The number of values passed - determines the function

    Returns:
        Vector to position, or offset, items.
    """

    scene = context.scene
    plane = pg.plane
    flip_angle = pg.flip_angle
    flip_percent= pg.flip_percent

    # Cartesian 3D coordinates
    if num_values == 3 and len(values) == 3:
        output_vector = Vector((float(values[0]), float(values[1]), float(values[2])))
    # Polar 2D coordinates
    elif num_values == 2 and len(values) == 2:
        output_vector = dis_ang(values, flip_angle, plane, scene)
    # Percentage of imaginary line between two 3D coordinates
    elif num_values == 1 and len(values) == 1:
        output_vector = get_percent(obj, flip_percent, float(values[0]), operation, scene)
    else:
        if num_values == 3:
            pg.error = PDT_ERR_BAD3VALS
        elif num_values == 2:
            pg.error = PDT_ERR_BAD2VALS
        else:
            pg.error = PDT_ERR_BAD1VALS
        context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        raise PDT_InvalidVector
    return output_vector


def placement_normal(context, operation):
    """Manipulates Geometry, or Objects by Normal Intersection between 3 points.

    Args:
        context: Blender bpy.context instance.
        operation: The Operation e.g. Create New Vertex

    Returns:
        Status Set.
    """

    scene = context.scene
    pg = scene.pdt_pg
    extend_all = pg.extend
    obj = context.view_layer.objects.active

    if obj.mode == "EDIT":
        if obj is None:
            pg.error = PDT_ERR_NO_ACT_OBJ
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            raise PDT_ObjectModeError
        obj_loc = obj.matrix_world.decompose()[0]
        bm = bmesh.from_edit_mesh(obj.data)
        if len(bm.select_history) == 3:
            vector_a, vector_b, vector_c = check_selection(3, bm, obj)
            if vector_a is None:
                pg.error = PDT_ERR_VERT_MODE
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                raise PDT_FeatureError
        else:
            pg.error = f"{PDT_ERR_SEL_3_VERTIO} {len(bm.select_history)})"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            raise PDT_SelectionError
    elif obj.mode == "OBJECT":
        objs = context.view_layer.objects.selected
        if len(objs) != 3:
            pg.error = f"{PDT_ERR_SEL_3_OBJS} {len(objs)})"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            raise PDT_SelectionError
        objs_s = [ob for ob in objs if ob.name != obj.name]
        vector_a = obj.matrix_world.decompose()[0]
        vector_b = objs_s[-1].matrix_world.decompose()[0]
        vector_c = objs_s[-2].matrix_world.decompose()[0]
    vector_delta = intersect_point_line(vector_a, vector_b, vector_c)[0]
    if operation == "C":
        if obj.mode == "EDIT":
            scene.cursor.location = obj_loc + vector_delta
        elif obj.mode == "OBJECT":
            scene.cursor.location = vector_delta
    elif operation == "P":
        if obj.mode == "EDIT":
            pg.pivot_loc = obj_loc + vector_delta
        elif obj.mode == "OBJECT":
            pg.pivot_loc = vector_delta
    elif operation == "G":
        if obj.mode == "EDIT":
            if extend_all:
                for v in [v for v in bm.verts if v.select]:
                    v.co = vector_delta
                bm.select_history.clear()
                bmesh.ops.remove_doubles(bm, verts=[v for v in bm.verts if v.select], dist=0.0001)
            else:
                bm.select_history[-1].co = vector_delta
                bm.select_history.clear()
            bmesh.update_edit_mesh(obj.data)
        elif obj.mode == "OBJECT":
            context.view_layer.objects.active.location = vector_delta
    elif operation == "N":
        if obj.mode == "EDIT":
            vertex_new = bm.verts.new(vector_delta)
            bmesh.update_edit_mesh(obj.data)
            bm.select_history.clear()
            for v in [v for v in bm.verts if v.select]:
                v.select_set(False)
            vertex_new.select_set(True)
        else:
            pg.error = f"{PDT_ERR_EDIT_MODE} {obj.mode})"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
    elif operation == "V" and obj.mode == "EDIT":
        vector_new = vector_delta
        vertex_new = bm.verts.new(vector_new)
        if extend_all:
            for v in [v for v in bm.verts if v.select]:
                bm.edges.new([v, vertex_new])
        else:
            bm.edges.new([bm.select_history[-1], vertex_new])
        for v in [v for v in bm.verts if v.select]:
            v.select_set(False)
        vertex_new.select_set(True)
        bmesh.update_edit_mesh(obj.data)
        bm.select_history.clear()
    else:
        pg.error = f"{operation} {PDT_ERR_NON_VALID} {PDT_LAB_NOR}"
        context.window_manager.popup_menu(oops, title="Error", icon="ERROR")


def placement_arc_centre(context, operation):
    """Manipulates Geometry, or Objects to an Arc Centre defined by 3 points on an Imaginary Arc.

    Args:
        context: Blender bpy.context instance.
        operation: The Operation e.g. Create New Vertex

    Returns:
        Status Set.
    """

    scene = context.scene
    pg = scene.pdt_pg
    extend_all = pg.extend
    obj = context.view_layer.objects.active

    if obj.mode == "EDIT":
        if obj is None:
            pg.error = PDT_ERR_NO_ACT_OBJ
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            raise PDT_ObjectModeError
        obj = context.view_layer.objects.active
        obj_loc = obj.matrix_world.decompose()[0]
        bm = bmesh.from_edit_mesh(obj.data)
        verts = [v for v in bm.verts if v.select]
        if len(verts) != 3:
            pg.error = f"{PDT_ERR_SEL_3_VERTS} {len(verts)})"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            raise PDT_SelectionError
        vector_a = verts[0].co
        vector_b = verts[1].co
        vector_c = verts[2].co
        vector_delta, radius = arc_centre(vector_a, vector_b, vector_c)
        if str(radius) == "inf":
            pg.error = PDT_ERR_STRIGHT_LINE
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            raise PDT_InfRadius
        pg.distance = radius
        if operation == "C":
            scene.cursor.location = obj_loc + vector_delta
        elif operation == "P":
            pg.pivot_loc = obj_loc + vector_delta
        elif operation == "N":
            vector_new = vector_delta
            vertex_new = bm.verts.new(vector_new)
            for v in [v for v in bm.verts if v.select]:
                v.select_set(False)
            vertex_new.select_set(True)
            bmesh.update_edit_mesh(obj.data)
            bm.select_history.clear()
            vertex_new.select_set(True)
        elif operation == "G":
            if extend_all:
                for v in [v for v in bm.verts if v.select]:
                    v.co = vector_delta
                bm.select_history.clear()
                bmesh.ops.remove_doubles(bm, verts=[v for v in bm.verts if v.select], dist=0.0001)
            else:
                bm.select_history[-1].co = vector_delta
                bm.select_history.clear()
            bmesh.update_edit_mesh(obj.data)
        elif operation == "V":
            vertex_new = bm.verts.new(vector_delta)
            if extend_all:
                for v in [v for v in bm.verts if v.select]:
                    bm.edges.new([v, vertex_new])
                    v.select_set(False)
                vertex_new.select_set(True)
                bm.select_history.clear()
                bmesh.ops.remove_doubles(bm, verts=[v for v in bm.verts if v.select], dist=0.0001)
                bmesh.update_edit_mesh(obj.data)
            else:
                bm.edges.new([bm.select_history[-1], vertex_new])
                bmesh.update_edit_mesh(obj.data)
                bm.select_history.clear()
        else:
            pg.error = f"{operation} {PDT_ERR_NON_VALID} {PDT_LAB_ARCCENTRE}"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
    elif obj.mode == "OBJECT":
        if len(context.view_layer.objects.selected) != 3:
            pg.error = f"{PDT_ERR_SEL_3_OBJS} {len(context.view_layer.objects.selected)})"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            raise PDT_SelectionError
        vector_a = context.view_layer.objects.selected[0].matrix_world.decompose()[0]
        vector_b = context.view_layer.objects.selected[1].matrix_world.decompose()[0]
        vector_c = context.view_layer.objects.selected[2].matrix_world.decompose()[0]
        vector_delta, radius = arc_centre(vector_a, vector_b, vector_c)
        pg.distance = radius
        if operation == "C":
            scene.cursor.location = vector_delta
        elif operation == "P":
            pg.pivot_loc = vector_delta
        elif operation == "G":
            context.view_layer.objects.active.location = vector_delta
        else:
            pg.error = f"{operation} {PDT_ERR_NON_VALID} {PDT_LAB_ARCCENTRE}"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")


def placement_intersect(context, operation):
    """Manipulates Geometry, or Objects by Convergence Intersection between 4 points, or 2 Edges.

    Args:
        context: Blender bpy.context instance.
        operation: The Operation e.g. Create New Vertex

    Returns:
        Status Set.
    """

    scene = context.scene
    pg = scene.pdt_pg
    plane = pg.plane
    obj = context.view_layer.objects.active
    if obj.mode == "EDIT":
        if obj is None:
            pg.error = PDT_ERR_NO_ACT_OBJ
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            raise PDT_NoObjectError
        obj_loc = obj.matrix_world.decompose()[0]
        bm = bmesh.from_edit_mesh(obj.data)
        edges = [e for e in bm.edges if e.select]
        extend_all = pg.extend

        if len(edges) == 2:
            vertex_a = edges[0].verts[0]
            vertex_b = edges[0].verts[1]
            vertex_c = edges[1].verts[0]
            vertex_d = edges[1].verts[1]
        else:
            if len(bm.select_history) != 4:
                pg.error = (
                    PDT_ERR_SEL_4_VERTS
                    + str(len(bm.select_history))
                    + " Vertices/"
                    + str(len(edges))
                    + " Edges)"
                )
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                raise PDT_SelectionError
            vertex_a = bm.select_history[-1]
            vertex_b = bm.select_history[-2]
            vertex_c = bm.select_history[-3]
            vertex_d = bm.select_history[-4]

        vector_delta, done = intersection(vertex_a.co, vertex_b.co, vertex_c.co, vertex_d.co, plane)
        if not done:
            pg.error = f"{PDT_ERR_INT_LINES} {plane}  {PDT_LAB_PLANE}"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            raise PDT_IntersectionError

        if operation == "C":
            scene.cursor.location = obj_loc + vector_delta
        elif operation == "P":
            pg.pivot_loc = obj_loc + vector_delta
        elif operation == "N":
            vector_new = vector_delta
            vertex_new = bm.verts.new(vector_new)
            for v in [v for v in bm.verts if v.select]:
                v.select_set(False)
            for f in bm.faces:
                f.select_set(False)
            for e in bm.edges:
                e.select_set(False)
            vertex_new.select_set(True)
            bmesh.update_edit_mesh(obj.data)
            bm.select_history.clear()
        elif operation in {"G", "V"}:
            vertex_new = None
            process = False

            if (vertex_a.co - vector_delta).length < (vertex_b.co - vector_delta).length:
                if operation == "G":
                    vertex_a.co = vector_delta
                    process = True
                else:
                    vertex_new = bm.verts.new(vector_delta)
                    bm.edges.new([vertex_a, vertex_new])
                    process = True
            else:
                if operation == "G" and extend_all:
                    vertex_b.co = vector_delta
                elif operation == "V" and extend_all:
                    vertex_new = bm.verts.new(vector_delta)
                    bm.edges.new([vertex_b, vertex_new])
                else:
                    return

            if (vertex_c.co - vector_delta).length < (vertex_d.co - vector_delta).length:
                if operation == "G" and extend_all:
                    vertex_c.co = vector_delta
                elif operation == "V" and extend_all:
                    bm.edges.new([vertex_c, vertex_new])
                else:
                    return
            else:
                if operation == "G" and extend_all:
                    vertex_d.co = vector_delta
                elif operation == "V" and extend_all:
                    bm.edges.new([vertex_d, vertex_new])
                else:
                    return
            bm.select_history.clear()
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)

            if not process and not extend_all:
                pg.error = PDT_ERR_INT_NO_ALL
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                bmesh.update_edit_mesh(obj.data)
                return
            for v in bm.verts:
                v.select_set(False)
            for f in bm.faces:
                f.select_set(False)
            for e in bm.edges:
                e.select_set(False)

            if vertex_new is not None:
                vertex_new.select_set(True)
            for v in bm.select_history:
                if v is not None:
                    v.select_set(True)
            bmesh.update_edit_mesh(obj.data)
        else:
            pg.error = f"{operation} {PDT_ERR_NON_VALID} {PDT_LAB_INTERSECT}"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            raise PDT_InvalidOperation

    elif obj.mode == "OBJECT":
        if len(context.view_layer.objects.selected) != 4:
            pg.error = f"{PDT_ERR_SEL_4_OBJS} {len(context.view_layer.objects.selected)})"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            raise PDT_SelectionError
        order = pg.object_order.split(",")
        objs = sorted(context.view_layer.objects.selected, key=lambda x: x.name)
        pg.error = (
            "Original Object Order (1,2,3,4) was: "
            + objs[0].name
            + ", "
            + objs[1].name
            + ", "
            + objs[2].name
            + ", "
            + objs[3].name
        )
        context.window_manager.popup_menu(oops, title="Info", icon="INFO")

        vector_a = objs[int(order[0]) - 1].matrix_world.decompose()[0]
        vector_b = objs[int(order[1]) - 1].matrix_world.decompose()[0]
        vector_c = objs[int(order[2]) - 1].matrix_world.decompose()[0]
        vector_d = objs[int(order[3]) - 1].matrix_world.decompose()[0]
        vector_delta, done = intersection(vector_a, vector_b, vector_c, vector_d, plane)
        if not done:
            pg.error = f"{PDT_ERR_INT_LINES} {plane}  {PDT_LAB_PLANE}"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            raise PDT_IntersectionError
        if operation == "C":
            scene.cursor.location = vector_delta
        elif operation == "P":
            pg.pivot_loc = vector_delta
        elif operation == "G":
            context.view_layer.objects.active.location = vector_delta
            pg.error = f"{PDT_INF_OBJ_MOVED} {context.view_layer.objects.active.name}"
            context.window_manager.popup_menu(oops, title="Info", icon="INFO")
        else:
            pg.error = f"{operation} {PDT_ERR_NON_VALID} {PDT_LAB_INTERSECT}"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        return
    else:
        return


def join_two_vertices(context):
    """Joins 2 Free Vertices that do not form part of a Face.

    Note:
        Joins two vertices that do not form part of a single face
        It is designed to close open Edge Loops, where a face is not required
        or to join two disconnected Edges.

    Args:
        context: Blender bpy.context instance.

    Returns:
        Status Set.
    """

    scene = context.scene
    pg = scene.pdt_pg
    obj = context.view_layer.objects.active
    if all([bool(obj), obj.type == "MESH", obj.mode == "EDIT"]):
        bm = bmesh.from_edit_mesh(obj.data)
        verts = [v for v in bm.verts if v.select]
        if len(verts) == 2:
            try:
                bm.edges.new([verts[-1], verts[-2]])
                bmesh.update_edit_mesh(obj.data)
                bm.select_history.clear()
                return
            except ValueError:
                pg.error = PDT_ERR_CONNECTED
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                raise PDT_VerticesConnected
        else:
            pg.error = f"{PDT_ERR_SEL_2_VERTS} {len(verts)})"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            raise PDT_SelectionError
    else:
        pg.error = f"{PDT_ERR_EDOB_MODE},{obj.mode})"
        context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        raise PDT_ObjectModeError


def set_angle_distance_two(context):
    """Measures Angle and Offsets between 2 Points in View Plane.

    Note:
        Uses 2 Selected Vertices to set pg.angle and pg.distance scene variables
        also sets delta offset from these 2 points using standard Numpy Routines
        Works in Edit and Object Modes.

    Args:
        context: Blender bpy.context instance.

    Returns:
        Status Set.
    """

    scene = context.scene
    pg = scene.pdt_pg
    plane = pg.plane
    flip_angle = pg.flip_angle
    obj = context.view_layer.objects.active
    if obj is None:
        pg.error = PDT_ERR_NO_ACT_OBJ
        context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        return
    if obj.mode == "EDIT":
        bm = bmesh.from_edit_mesh(obj.data)
        verts = [v for v in bm.verts if v.select]
        if len(verts) == 2:
            if len(bm.select_history) == 2:
                vector_a, vector_b = check_selection(2, bm, obj)
                if vector_a is None:
                    pg.error = PDT_ERR_VERT_MODE
                    context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                    raise PDT_FeatureError
            else:
                pg.error = f"{PDT_ERR_SEL_2_VERTIO} {len(bm.select_history)})"
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                raise PDT_SelectionError
        else:
            pg.error = f"{PDT_ERR_SEL_2_VERTIO} {len(verts)})"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            raise PDT_SelectionError
    elif obj.mode == "OBJECT":
        objs = context.view_layer.objects.selected
        if len(objs) < 2:
            pg.error = f"{PDT_ERR_SEL_2_OBJS} {len(objs)})"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            raise PDT_SelectionError
        objs_s = [ob for ob in objs if ob.name != obj.name]
        vector_a = obj.matrix_world.decompose()[0]
        vector_b = objs_s[-1].matrix_world.decompose()[0]
    if plane == "LO":
        vector_difference = vector_b - vector_a
        vector_b = view_coords_i(vector_difference.x, vector_difference.y, vector_difference.z)
        vector_a = Vector((0, 0, 0))
        v0 = np.array([vector_a.x + 1, vector_a.y]) - np.array([vector_a.x, vector_a.y])
        v1 = np.array([vector_b.x, vector_b.y]) - np.array([vector_a.x, vector_a.y])
    else:
        a1, a2, _ = set_mode(plane)
        v0 = np.array([vector_a[a1] + 1, vector_a[a2]]) - np.array([vector_a[a1], vector_a[a2]])
        v1 = np.array([vector_b[a1], vector_b[a2]]) - np.array([vector_a[a1], vector_a[a2]])
    ang = np.rad2deg(np.arctan2(np.linalg.det([v0, v1]), np.dot(v0, v1)))
    decimal_places = context.preferences.addons[__package__].preferences.pdt_input_round
    if flip_angle:
        if ang > 0:
            pg.angle = round(ang - 180, decimal_places)
        else:
            pg.angle = round(ang - 180, decimal_places)
    else:
        pg.angle = round(ang, decimal_places)
    if plane == "LO":
        pg.distance = round(sqrt(
            (vector_a.x - vector_b.x) ** 2 +
            (vector_a.y - vector_b.y) ** 2), decimal_places)
    else:
        pg.distance = round(sqrt(
            (vector_a[a1] - vector_b[a1]) ** 2 +
            (vector_a[a2] - vector_b[a2]) ** 2), decimal_places)
    pg.cartesian_coords = Vector(([round(i, decimal_places) for i in vector_b - vector_a]))


def set_angle_distance_three(context):
    """Measures Angle and Offsets between 3 Points in World Space, Also sets Deltas.

    Note:
        Uses 3 Selected Vertices to set pg.angle and pg.distance scene variables
        also sets delta offset from these 3 points using standard Numpy Routines
        Works in Edit and Object Modes.

    Args:
        context: Blender bpy.context instance.

    Returns:
        Status Set.
    """

    pg = context.scene.pdt_pg
    flip_angle = pg.flip_angle
    obj = context.view_layer.objects.active
    if obj is None:
        pg.error = PDT_ERR_NO_ACT_OBJ
        context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        raise PDT_NoObjectError
    if obj.mode == "EDIT":
        bm = bmesh.from_edit_mesh(obj.data)
        verts = [v for v in bm.verts if v.select]
        if len(verts) == 3:
            if len(bm.select_history) == 3:
                vector_a, vector_b, vector_c = check_selection(3, bm, obj)
                if vector_a is None:
                    pg.error = PDT_ERR_VERT_MODE
                    context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                    raise PDT_FeatureError
            else:
                pg.error = f"{PDT_ERR_SEL_3_VERTIO} {len(bm.select_history)})"
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                raise PDT_SelectionError
        else:
            pg.error = f"{PDT_ERR_SEL_3_VERTIO} {len(verts)})"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            raise PDT_SelectionError
    elif obj.mode == "OBJECT":
        objs = context.view_layer.objects.selected
        if len(objs) < 3:
            pg.error = PDT_ERR_SEL_3_OBJS + str(len(objs))
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            raise PDT_SelectionError
        objs_s = [ob for ob in objs if ob.name != obj.name]
        vector_a = obj.matrix_world.decompose()[0]
        vector_b = objs_s[-1].matrix_world.decompose()[0]
        vector_c = objs_s[-2].matrix_world.decompose()[0]
    ba = np.array([vector_b.x, vector_b.y, vector_b.z]) - np.array(
        [vector_a.x, vector_a.y, vector_a.z]
    )
    bc = np.array([vector_c.x, vector_c.y, vector_c.z]) - np.array(
        [vector_a.x, vector_a.y, vector_a.z]
    )
    angle_cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    ang = np.degrees(np.arccos(angle_cosine))
    decimal_places = context.preferences.addons[__package__].preferences.pdt_input_round
    if flip_angle:
        if ang > 0:
            pg.angle = round(ang - 180, decimal_places)
        else:
            pg.angle = round(ang - 180, decimal_places)
    else:
        pg.angle = round(ang, decimal_places)
    pg.distance = round((vector_a - vector_b).length, decimal_places)
    pg.cartesian_coords = Vector(([round(i, decimal_places) for i in vector_b - vector_a]))


def origin_to_cursor(context):
    """Sets Object Origin in Edit Mode to Cursor Location.

    Note:
        Keeps geometry static in World Space whilst moving Object Origin
        Requires cursor location
        Works in Edit and Object Modes.

    Args:
        context: Blender bpy.context instance.

    Returns:
        Status Set.
    """

    scene = context.scene
    pg = context.scene.pdt_pg
    obj = context.view_layer.objects.active
    if obj is None:
        pg.error = PDT_ERR_NO_ACT_OBJ
        context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        return
    obj_loc = obj.matrix_world.decompose()[0]
    cur_loc = scene.cursor.location
    diff_v = obj_loc - cur_loc
    if obj.mode == "EDIT":
        bm = bmesh.from_edit_mesh(obj.data)
        for v in bm.verts:
            v.co = v.co + diff_v
        obj.location = cur_loc
        bmesh.update_edit_mesh(obj.data)
        bm.select_history.clear()
    elif obj.mode == "OBJECT":
        for v in obj.data.vertices:
            v.co = v.co + diff_v
        obj.location = cur_loc
    else:
        pg.error = f"{PDT_ERR_EDOB_MODE} {obj.mode})"
        context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        raise PDT_ObjectModeError


def taper(context):
    """Taper Geometry along World Axes.

    Note:
        Similar to Shear command except that it shears by angle rather than displacement.
        Rotates about World Axes and displaces along World Axes, angle must not exceed +-80 degrees.
        Rotation axis is centred on Active Vertex.
        Works only in Edit mode.

    Args:
        context: Blender bpy.context instance.

    Note:
        Uses pg.taper & pg.angle scene variables

    Returns:
        Status Set.
    """

    scene = context.scene
    pg = scene.pdt_pg
    tap_ax = pg.taper
    ang_v = pg.angle
    obj = context.view_layer.objects.active
    if all([bool(obj), obj.type == "MESH", obj.mode == "EDIT"]):
        if ang_v > 80 or ang_v < -80:
            pg.error = f"{PDT_ERR_TAPER_ANG} {ang_v})"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            raise PDT_InvalidAngle
        if obj is None:
            pg.error = PDT_ERR_NO_ACT_OBJ
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            raise PDT_NoObjectError
        _, a2, a3 = set_axis(tap_ax)
        bm = bmesh.from_edit_mesh(obj.data)
        if len(bm.select_history) >= 1:
            rotate_vertex = bm.select_history[-1]
            view_vector = view_coords(rotate_vertex.co.x, rotate_vertex.co.y, rotate_vertex.co.z)
        else:
            pg.error = f"{PDT_ERR_TAPER_SEL} {len(bm.select_history)})"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            raise PDT_SelectionError
        for v in [v for v in bm.verts if v.select]:
            if pg.plane == "LO":
                v_loc = view_coords(v.co.x, v.co.y, v.co.z)
                dis_v = sqrt((view_vector.x - v_loc.x) ** 2 + (view_vector.y - v_loc.y) ** 2)
                x_loc = dis_v * tan(ang_v * pi / 180)
                view_matrix = view_dir(x_loc, 0)
                v.co = v.co - view_matrix
            else:
                dis_v = sqrt(
                    (rotate_vertex.co[a3] - v.co[a3]) ** 2 + (rotate_vertex.co[a2] - v.co[a2]) ** 2
                )
                v.co[a2] = v.co[a2] - (dis_v * tan(ang_v * pi / 180))
        bmesh.update_edit_mesh(obj.data)
        bm.select_history.clear()
    else:
        pg.error = f"{PDT_ERR_EDOB_MODE},{obj.mode})"
        context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        raise PDT_ObjectModeError
