# SPDX-FileCopyrightText: 2019-2022 Alan Odom (Clockmender)
# SPDX-FileCopyrightText: 2019-2022 Rune Morling (ermo)
#
# SPDX-License-Identifier: GPL-2.0-or-later

# Common Functions used in more than one place in PDT Operations

import bpy
import bmesh
import gpu
import numpy as np
from mathutils import Vector, Quaternion
from gpu_extras.batch import batch_for_shader
from math import cos, sin, pi
from .pdt_msg_strings import (
    PDT_ERR_VERT_MODE,
    PDT_ERR_SEL_2_V_1_E,
    PDT_ERR_SEL_2_OBJS,
    PDT_ERR_NO_ACT_OBJ,
    PDT_ERR_SEL_1_EDGEM,
)
from . import pdt_exception
PDT_ShaderError = pdt_exception.ShaderError


def debug(msg, prefix=""):
    """Print a debug message to the console if PDT's or Blender's debug flags are set.

    Note:
        The printed message will be of the form:

        {prefix}{caller file name:line number}| {msg}

    Args:
        msg: Incoming message to display
        prefix: Always Blank

    Returns:
        Nothing.
    """

    pdt_debug = bpy.context.preferences.addons[__package__].preferences.debug
    if  bpy.app.debug or bpy.app.debug_python or pdt_debug:
        import traceback

        def extract_filename(fullpath):
            """Return only the filename part of fullpath (excluding its path).

            Args:
                fullpath: Filename's full path

            Returns:
                filename.
            """
            # Expected to end up being a string containing only the filename
            # (i.e. excluding its preceding '/' separated path)
            filename = fullpath.split('/')[-1]
            #print(filename)
            # something went wrong
            if len(filename) < 1:
                return fullpath
            # since this is a string, just return it
            return filename

        # stack frame corresponding to the line where debug(msg) was called
        #print(traceback.extract_stack()[-2])
        laststack = traceback.extract_stack()[-2]
        #print(laststack[0])
        # laststack[0] is the caller's full file name, laststack[1] is the line number
        print(f"{prefix}{extract_filename(laststack[0])}:{laststack[1]}| {msg}")

def oops(self, context):
    """Error Routine.

    Note:
        Displays error message in a popup.

    Args:
        context: Blender bpy.context instance.

    Returns:
        Nothing.
    """

    scene = context.scene
    pg = scene.pdt_pg
    self.layout.label(text=pg.error)


def set_mode(mode_pl):
    """Sets Active Axes for View Orientation.

    Note:
        Sets indices of axes for locational vectors:
        a3 is normal to screen, or depth
        "XY": a1 = x, a2 = y, a3 = z
        "XZ": a1 = x, a2 = z, a3 = y
        "YZ": a1 = y, a2 = z, a3 = x

    Args:
        mode_pl: Plane Selector variable as input

    Returns:
        3 Integer indices.
    """

    order = {
        "XY": (0, 1, 2),
        "XZ": (0, 2, 1),
        "YZ": (1, 2, 0),
        "LO": (0, 1, 2),
    }
    return order[mode_pl]


def set_axis(mode_pl):
    """Sets Active Axes for View Orientation.

    Note:
        Sets indices for axes from taper vectors
        Axis order: Rotate Axis, Move Axis, Height Axis

    Args:
        mode_pl: Taper Axis Selector variable as input

    Returns:
        3 Integer Indices.
    """

    order = {
        "RX-MY": (0, 1, 2),
        "RX-MZ": (0, 2, 1),
        "RY-MX": (1, 0, 2),
        "RY-MZ": (1, 2, 0),
        "RZ-MX": (2, 0, 1),
        "RZ-MY": (2, 1, 0),
    }
    return order[mode_pl]


def check_selection(num, bm, obj):
    """Check that the Object's select_history has sufficient entries.

    Note:
        If selection history is not Verts, clears selection and history.

    Args:
        num: The number of entries required for each operation
        bm: The Bmesh from the Object
        obj: The Object

    Returns:
        list of 3D points as Vectors.
    """

    if len(bm.select_history) < num:
        return None
    active_vertex = bm.select_history[-1]
    if isinstance(active_vertex, bmesh.types.BMVert):
        vector_a = active_vertex.co
        if num == 1:
            return vector_a
        if num == 2:
            vector_b = bm.select_history[-2].co
            return vector_a, vector_b
        if num == 3:
            vector_b = bm.select_history[-2].co
            vector_c = bm.select_history[-3].co
            return vector_a, vector_b, vector_c
        if num == 4:
            vector_b = bm.select_history[-2].co
            vector_c = bm.select_history[-3].co
            vector_d = bm.select_history[-4].co
            return vector_a, vector_b, vector_c, vector_d
    else:
        for f in bm.faces:
            f.select_set(False)
        for e in bm.edges:
            e.select_set(False)
        for v in bm.verts:
            v.select_set(False)
        bmesh.update_edit_mesh(obj.data)
        bm.select_history.clear()
    return None


def update_sel(bm, verts, edges, faces):
    """Updates Vertex, Edge and Face Selections following a function.

    Args:
        bm: Object Bmesh
        verts: New Selection for Vertices
        edges: The Edges on which to operate
        faces: The Faces on which to operate

    Returns:
        Nothing.
    """
    for f in bm.faces:
        f.select_set(False)
    for e in bm.edges:
        e.select_set(False)
    for v in bm.verts:
        v.select_set(False)
    for v in verts:
        v.select_set(True)
    for e in edges:
        e.select_set(True)
    for f in faces:
        f.select_set(True)


def view_coords(x_loc, y_loc, z_loc):
    """Converts input Vector values to new Screen Oriented Vector.

    Args:
        x_loc: X coordinate from vector
        y_loc: Y coordinate from vector
        z_loc: Z coordinate from vector

    Returns:
        Vector adjusted to View's Inverted Transformation Matrix.
    """

    areas = [a for a in bpy.context.screen.areas if a.type == "VIEW_3D"]
    if len(areas) > 0:
        view_matrix = areas[0].spaces.active.region_3d.view_matrix
        view_matrix = view_matrix.to_3x3().normalized().inverted()
        view_location = Vector((x_loc, y_loc, z_loc))
        new_view_location = view_matrix @ view_location
        return new_view_location

    return Vector((0, 0, 0))


def view_coords_i(x_loc, y_loc, z_loc):
    """Converts Screen Oriented input Vector values to new World Vector.

    Note:
        Converts View transformation Matrix to Rotational Matrix

    Args:
        x_loc: X coordinate from vector
        y_loc: Y coordinate from vector
        z_loc: Z coordinate from vector

    Returns:
        Vector adjusted to View's Transformation Matrix.
    """

    areas = [a for a in bpy.context.screen.areas if a.type == "VIEW_3D"]
    if len(areas) > 0:
        view_matrix = areas[0].spaces.active.region_3d.view_matrix
        view_matrix = view_matrix.to_3x3().normalized()
        view_location = Vector((x_loc, y_loc, z_loc))
        new_view_location = view_matrix @ view_location
        return new_view_location

    return Vector((0, 0, 0))


def view_dir(dis_v, ang_v):
    """Converts Distance and Angle to View Oriented Vector.

    Note:
        Converts View Transformation Matrix to Rotational Matrix (3x3)
        Angles are Converts to Radians from degrees.

    Args:
        dis_v: Scene PDT distance
        ang_v: Scene PDT angle

    Returns:
        World Vector.
    """

    areas = [a for a in bpy.context.screen.areas if a.type == "VIEW_3D"]
    if len(areas) > 0:
        view_matrix = areas[0].spaces.active.region_3d.view_matrix
        view_matrix = view_matrix.to_3x3().normalized().inverted()
        view_location = Vector((0, 0, 0))
        view_location.x = dis_v * cos(ang_v * pi / 180)
        view_location.y = dis_v * sin(ang_v * pi / 180)
        new_view_location = view_matrix @ view_location
        return new_view_location

    return Vector((0, 0, 0))


def euler_to_quaternion(roll, pitch, yaw):
    """Converts Euler Rotation to Quaternion Rotation.

    Args:
        roll: Roll in Euler rotation
        pitch: Pitch in Euler rotation
        yaw: Yaw in Euler rotation

    Returns:
        Quaternion Rotation.
    """

    # fmt: off
    quat_x = (np.sin(roll/2) * np.cos(pitch/2) * np.cos(yaw/2)
              - np.cos(roll/2) * np.sin(pitch/2) * np.sin(yaw/2))
    quat_y = (np.cos(roll/2) * np.sin(pitch/2) * np.cos(yaw/2)
              + np.sin(roll/2) * np.cos(pitch/2) * np.sin(yaw/2))
    quat_z = (np.cos(roll/2) * np.cos(pitch/2) * np.sin(yaw/2)
              - np.sin(roll/2) * np.sin(pitch/2) * np.cos(yaw/2))
    quat_w = (np.cos(roll/2) * np.cos(pitch/2) * np.cos(yaw/2)
              + np.sin(roll/2) * np.sin(pitch/2) * np.sin(yaw/2))
    # fmt: on
    return Quaternion((quat_w, quat_x, quat_y, quat_z))


def arc_centre(vector_a, vector_b, vector_c):
    """Calculates Centre of Arc from 3 Vector Locations using standard Numpy routine

    Args:
        vector_a: Active vector location
        vector_b: Second vector location
        vector_c: Third vector location

    Returns:
        Vector representing Arc Centre and Float representing Arc Radius.
    """

    coord_a = np.array([vector_a.x, vector_a.y, vector_a.z])
    coord_b = np.array([vector_b.x, vector_b.y, vector_b.z])
    coord_c = np.array([vector_c.x, vector_c.y, vector_c.z])
    line_a = np.linalg.norm(coord_c - coord_b)
    line_b = np.linalg.norm(coord_c - coord_a)
    line_c = np.linalg.norm(coord_b - coord_a)
    # fmt: off
    line_s = (line_a+line_b+line_c) / 2
    radius = (
        line_a*line_b*line_c/4
        / np.sqrt(line_s
                  * (line_s-line_a)
                  * (line_s-line_b)
                  * (line_s-line_c))
        )
    base_1 = line_a*line_a * (line_b*line_b + line_c*line_c - line_a*line_a)
    base_2 = line_b*line_b * (line_a*line_a + line_c*line_c - line_b*line_b)
    base_3 = line_c*line_c * (line_a*line_a + line_b*line_b - line_c*line_c)
    # fmt: on
    intersect_coord = np.column_stack((coord_a, coord_b, coord_c))
    intersect_coord = intersect_coord.dot(np.hstack((base_1, base_2, base_3)))
    intersect_coord /= base_1 + base_2 + base_3
    return Vector((intersect_coord[0], intersect_coord[1], intersect_coord[2])), radius


def intersection(vertex_a, vertex_b, vertex_c, vertex_d, plane):
    """Calculates Intersection Point of 2 Imagined Lines from 4 Vectors.

    Note:
       Calculates Converging Intersect Location and indication of
       whether the lines are convergent using standard Numpy Routines

    Args:
        vertex_a: Active vector location of first line
        vertex_b: Second vector location of first line
        vertex_c: Third vector location of 2nd line
        vertex_d: Fourth vector location of 2nd line
        plane: Working Plane 4 Vector Locations representing 2 lines and Working Plane

    Returns:
        Intersection Vector and Boolean for convergent state.
    """

    if plane == "LO":
        vertex_offset = vertex_b - vertex_a
        vertex_b = view_coords_i(vertex_offset.x, vertex_offset.y, vertex_offset.z)
        vertex_offset = vertex_d - vertex_a
        vertex_d = view_coords_i(vertex_offset.x, vertex_offset.y, vertex_offset.z)
        vertex_offset = vertex_c - vertex_a
        vertex_c = view_coords_i(vertex_offset.x, vertex_offset.y, vertex_offset.z)
        vector_ref = Vector((0, 0, 0))
        coord_a = (vertex_c.x, vertex_c.y)
        coord_b = (vertex_d.x, vertex_d.y)
        coord_c = (vertex_b.x, vertex_b.y)
        coord_d = (vector_ref.x, vector_ref.y)
    else:
        a1, a2, a3 = set_mode(plane)
        coord_a = (vertex_c[a1], vertex_c[a2])
        coord_b = (vertex_d[a1], vertex_d[a2])
        coord_c = (vertex_a[a1], vertex_a[a2])
        coord_d = (vertex_b[a1], vertex_b[a2])
    v_stack = np.vstack([coord_a, coord_b, coord_c, coord_d])
    h_stack = np.hstack((v_stack, np.ones((4, 1))))
    line_a = np.cross(h_stack[0], h_stack[1])
    line_b = np.cross(h_stack[2], h_stack[3])
    x_loc, y_loc, z_loc = np.cross(line_a, line_b)
    if z_loc == 0:
        return Vector((0, 0, 0)), False
    new_x_loc = x_loc / z_loc
    new_z_loc = y_loc / z_loc
    if plane == "LO":
        new_y_loc = 0
    else:
        new_y_loc = vertex_a[a3]
    # Order Vector Delta
    if plane == "XZ":
        vector_delta = Vector((new_x_loc, new_y_loc, new_z_loc))
    elif plane == "XY":
        vector_delta = Vector((new_x_loc, new_z_loc, new_y_loc))
    elif plane == "YZ":
        vector_delta = Vector((new_y_loc, new_x_loc, new_z_loc))
    else:
        # Must be Local View Plane
        vector_delta = view_coords(new_x_loc, new_z_loc, new_y_loc) + vertex_a
    return vector_delta, True


def get_percent(obj, flip_percent, per_v, data, scene):
    """Calculates a Percentage Distance between 2 Vectors.

    Note:
        Calculates a point that lies a set percentage between two given points
        using standard Numpy Routines.

        Works for either 2 vertices for an object in Edit mode
        or 2 selected objects in Object mode.

    Args:
        obj: The Object under consideration
        flip_percent: Setting this to True measures the percentage starting from the second vector
        per_v: Percentage Input Value
        data: pg.flip, pg.percent scene variables & Operational Mode
        scene: Context Scene

    Returns:
        World Vector.
    """

    pg = scene.pdt_pg

    if obj.mode == "EDIT":
        bm = bmesh.from_edit_mesh(obj.data)
        verts = [v for v in bm.verts if v.select]
        if len(verts) == 2:
            vector_a = verts[0].co
            vector_b = verts[1].co
            if vector_a is None:
                pg.error = PDT_ERR_VERT_MODE
                bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return None
        else:
            pg.error = PDT_ERR_SEL_2_V_1_E + str(len(verts)) + " Vertices"
            bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return None
        coord_a = np.array([vector_a.x, vector_a.y, vector_a.z])
        coord_b = np.array([vector_b.x, vector_b.y, vector_b.z])
    if obj.mode == "OBJECT":
        objs = bpy.context.view_layer.objects.selected
        if len(objs) != 2:
            pg.error = PDT_ERR_SEL_2_OBJS + str(len(objs)) + ")"
            bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return None
        coord_a = np.array(
            [
                objs[-1].matrix_world.decompose()[0].x,
                objs[-1].matrix_world.decompose()[0].y,
                objs[-1].matrix_world.decompose()[0].z,
            ]
        )
        coord_b = np.array(
            [
                objs[-2].matrix_world.decompose()[0].x,
                objs[-2].matrix_world.decompose()[0].y,
                objs[-2].matrix_world.decompose()[0].z,
            ]
        )
    coord_c = coord_b - coord_a
    coord_d = np.array([0, 0, 0])
    _per_v = per_v
    if (flip_percent and data != "MV") or data == "MV":
        _per_v = 100 - per_v
    coord_out = (coord_d+coord_c) * (_per_v / 100) + coord_a
    return Vector((coord_out[0], coord_out[1], coord_out[2]))


def obj_check(obj, scene, operation):
    """Check Object & Selection Validity.

    Args:
        obj: Active Object
        scene: Active Scene
        operation: The Operation e.g. Create New Vertex

    Returns:
        Object Bmesh
        Validity Boolean.
    """

    pg = scene.pdt_pg
    _operation = operation.upper()

    if obj is None:
        pg.error = PDT_ERR_NO_ACT_OBJ
        bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        return None, False
    if obj.mode == "EDIT":
        bm = bmesh.from_edit_mesh(obj.data)
        if _operation == "S":
            if len(bm.edges) < 1:
                pg.error = f"{PDT_ERR_SEL_1_EDGEM} {len(bm.edges)})"
                bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return None, False
            return bm, True
        if len(bm.select_history) >= 1:
            vector_a = None
            if _operation not in {"D", "E", "F", "G", "N", "S"}:
                vector_a = check_selection(1, bm, obj)
            else:
                verts = [v for v in bm.verts if v.select]
                if len(verts) > 0:
                    vector_a = verts[0]
            if vector_a is None:
                pg.error = PDT_ERR_VERT_MODE
                bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return None, False
        return bm, True
    return None, True


def dis_ang(values, flip_angle, plane, scene):
    """Set Working Axes when using Direction command.

    Args:
        values: Input Arguments
        flip_angle: Whether to flip the angle
        plane: Working Plane
        scene: Current Scene

    Returns:
        Directional Offset as a Vector.
    """

    pg = scene.pdt_pg
    dis_v = float(values[0])
    ang_v = float(values[1])
    if flip_angle:
        if ang_v > 0:
            ang_v = ang_v - 180
        else:
            ang_v = ang_v + 180
        pg.angle = ang_v
    if plane == "LO":
        vector_delta = view_dir(dis_v, ang_v)
    else:
        a1, a2, _ = set_mode(plane)
        vector_delta = Vector((0, 0, 0))
        # fmt: off
        vector_delta[a1] = vector_delta[a1] + (dis_v * cos(ang_v * pi/180))
        vector_delta[a2] = vector_delta[a2] + (dis_v * sin(ang_v * pi/180))
        # fmt: on
    return vector_delta


# Shader for displaying the Pivot Point as Graphics.
#
SHADER = gpu.shader.from_builtin("UNIFORM_COLOR") if not bpy.app.background else None


def draw_3d(coords, gtype, rgba, context):
    """Draw Pivot Point Graphics.

    Note:
        Draws either Lines Points, or Tris using defined shader

    Args:
        coords: Input Coordinates List
        gtype: Graphic Type
        rgba: Colour in RGBA format
        context: Blender bpy.context instance.

    Returns:
        Nothing.
    """

    batch = batch_for_shader(SHADER, gtype, {"pos": coords})

    try:
        if coords is not None:
            gpu.state.blend_set('ALPHA')
            SHADER.bind()
            SHADER.uniform_float("color", rgba)
            batch.draw(SHADER)
    except:
        raise PDT_ShaderError


def draw_callback_3d(self, context):
    """Create Coordinate List for Pivot Point Graphic.

    Note:
        Creates coordinates for Pivot Point Graphic consisting of 6 Tris
        and one Point colour coded Red; X axis, Green; Y axis, Blue; Z axis
        and a yellow point based upon screen scale

    Args:
        context: Blender bpy.context instance.

    Returns:
        Nothing.
    """

    scene = context.scene
    pg = scene.pdt_pg
    region_width = context.region.width
    x_loc = pg.pivot_loc.x
    y_loc = pg.pivot_loc.y
    z_loc = pg.pivot_loc.z
    # Scale it from view
    areas = [a for a in context.screen.areas if a.type == "VIEW_3D"]
    if len(areas) > 0:
        scale_factor = abs(areas[0].spaces.active.region_3d.window_matrix.decompose()[2][1])
    # Check for orhtographic view and resize
    #if areas[0].spaces.active.region_3d.is_orthographic_side_view:
    #    dim_a = region_width / sf / 60000 * pg.pivot_size
    #else:
    #    dim_a = region_width / sf / 5000 * pg.pivot_size
    dim_a = region_width / scale_factor / 50000 * pg.pivot_size
    dim_b = dim_a * 0.65
    dim_c = dim_a * 0.05 + (pg.pivot_width * dim_a * 0.02)
    dim_o = dim_c / 3

    # fmt: off
    # X Axis
    coords = [
        (x_loc, y_loc, z_loc),
        (x_loc+dim_b, y_loc-dim_o, z_loc),
        (x_loc+dim_b, y_loc+dim_o, z_loc),
        (x_loc+dim_a, y_loc, z_loc),
        (x_loc+dim_b, y_loc+dim_c, z_loc),
        (x_loc+dim_b, y_loc-dim_c, z_loc),
    ]
    # fmt: on
    colour = (1.0, 0.0, 0.0, pg.pivot_alpha)
    draw_3d(coords, "TRIS", colour, context)
    coords = [(x_loc, y_loc, z_loc), (x_loc+dim_a, y_loc, z_loc)]
    draw_3d(coords, "LINES", colour, context)
    # fmt: off
    # Y Axis
    coords = [
        (x_loc, y_loc, z_loc),
        (x_loc-dim_o, y_loc+dim_b, z_loc),
        (x_loc+dim_o, y_loc+dim_b, z_loc),
        (x_loc, y_loc+dim_a, z_loc),
        (x_loc+dim_c, y_loc+dim_b, z_loc),
        (x_loc-dim_c, y_loc+dim_b, z_loc),
    ]
    # fmt: on
    colour = (0.0, 1.0, 0.0, pg.pivot_alpha)
    draw_3d(coords, "TRIS", colour, context)
    coords = [(x_loc, y_loc, z_loc), (x_loc, y_loc + dim_a, z_loc)]
    draw_3d(coords, "LINES", colour, context)
    # fmt: off
    # Z Axis
    coords = [
        (x_loc, y_loc, z_loc),
        (x_loc-dim_o, y_loc, z_loc+dim_b),
        (x_loc+dim_o, y_loc, z_loc+dim_b),
        (x_loc, y_loc, z_loc+dim_a),
        (x_loc+dim_c, y_loc, z_loc+dim_b),
        (x_loc-dim_c, y_loc, z_loc+dim_b),
    ]
    # fmt: on
    colour = (0.2, 0.5, 1.0, pg.pivot_alpha)
    draw_3d(coords, "TRIS", colour, context)
    coords = [(x_loc, y_loc, z_loc), (x_loc, y_loc, z_loc + dim_a)]
    draw_3d(coords, "LINES", colour, context)
    # Centre
    coords = [(x_loc, y_loc, z_loc)]
    colour = (1.0, 1.0, 0.0, pg.pivot_alpha)
    draw_3d(coords, "POINTS", colour, context)


def scale_set(self, context):
    """Sets Scale by dividing Pivot Distance by System Distance.

    Note:
        Sets Pivot Point Scale Factors by Measurement
        Uses pg.pivotdis & pg.distance scene variables

    Args:
        context: Blender bpy.context instance.

    Returns:
        Status Set.
    """

    scene = context.scene
    pg = scene.pdt_pg
    sys_distance = pg.distance
    scale_distance = pg.pivot_dis
    if scale_distance > 0:
        scale_factor = scale_distance / sys_distance
        pg.pivot_scale = Vector((scale_factor, scale_factor, scale_factor))
