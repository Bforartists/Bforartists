# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****

# -----------------------------------------------------------------------
# Author: Alan Odom (Clockmender), Rune Morling (ermo) Copyright (c) 2019
# -----------------------------------------------------------------------
#
# Common Functions used in more than one place in PDT Operations

import bpy
import bmesh
import bgl
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
    PDT_ERR_SEL_1_EDGEM
)


def debug(msg, prefix=""):
    """Print a debug message to the console if PDT's or Blender's debug flags are set.

    The printed message will be of the form:

    {prefix}{caller file name:line number}| {msg}
    """

    pdt_debug = bpy.context.preferences.addons[__package__].preferences.debug
    if  bpy.app.debug or bpy.app.debug_python or pdt_debug:
        import traceback

        def extract_filename(fullpath):
            """Return only the filename part of fullpath (excluding its path)."""
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

    Displays error message in a popup.

    Args:
        context: Blender bpy.context instance.

    Note:
        Uses pg.error scene variable
    """

    scene = context.scene
    pg = scene.pdt_pg
    self.layout.label(text=pg.error)


def setMode(mode_pl):
    """Sets Active Axes for View Orientation.

    Sets indices of axes for locational vectors

    Args:
        mode_pl: Plane Selector variable as input

    Returns:
        3 Integer indices.
    """

    if mode_pl == "XY":
        # a1 = x a2 = y a3 = z
        return 0, 1, 2
    if mode_pl == "XZ":
        # a1 = x a2 = z a3 = y
        return 0, 2, 1
    if mode_pl == "YZ":
        # a1 = y a2 = z a3 = x
        return 1, 2, 0
    #FIXME: This needs a proper specification and a default


def setAxis(mode_pl):
    """Sets Active Axes for View Orientation.

    Sets indices for axes from taper vectors

    Args:
        mode_pl: Taper Axis Selector variable as input

    Note:
        Axis order: Rotate Axis, Move Axis, Height Axis

    Returns:
        3 Integer Indicies.
    """

    if mode_pl == "RX-MY":
        return 0, 1, 2
    if mode_pl == "RX-MZ":
        return 0, 2, 1
    if mode_pl == "RY-MX":
        return 1, 0, 2
    if mode_pl == "RY-MZ":
        return 1, 2, 0
    if mode_pl == "RZ-MX":
        return 2, 0, 1
    if mode_pl == "RZ-MY":
        return 2, 1, 0
    #FIXME: This needs a proper specification and a default


def checkSelection(num, bm, obj):
    """Check that the Object's select_history has sufficient entries.

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
    else:
        actE = bm.select_history[-1]
    if isinstance(actE, bmesh.types.BMVert):
        actV = actE.co
        if num == 1:
            return actV
        elif num == 2:
            othV = bm.select_history[-2].co
            return actV, othV
        elif num == 3:
            othV = bm.select_history[-2].co
            lstV = bm.select_history[-3].co
            return actV, othV, lstV
        elif num == 4:
            othV = bm.select_history[-2].co
            lstV = bm.select_history[-3].co
            fstV = bm.select_history[-4].co
            return actV, othV, lstV, fstV
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


def updateSel(bm, verts, edges, faces):
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


def viewCoords(x_loc, y_loc, z_loc):
    """Converts input Vector values to new Screen Oriented Vector.

    Args:
        x_loc: X coordinate from vector
        y_loc: Y coordinate from vector
        z_loc: Z coordinate from vector

    Returns:
        Vector adjusted to View's Inverted Tranformation Matrix.
    """

    areas = [a for a in bpy.context.screen.areas if a.type == "VIEW_3D"]
    if len(areas) > 0:
        vm = areas[0].spaces.active.region_3d.view_matrix
        vm = vm.to_3x3().normalized().inverted()
        vl = Vector((x_loc, y_loc, z_loc))
        vw = vm @ vl
        return vw
    else:
        return Vector((0, 0, 0))


def viewCoordsI(x_loc, y_loc, z_loc):
    """Converts Screen Oriented input Vector values to new World Vector.

    Converts View tranformation Matrix to Rotational Matrix

    Args:
        x_loc: X coordinate from vector
        y_loc: Y coordinate from vector
        z_loc: Z coordinate from vector

    Returns:
        Vector adjusted to View's Transformation Matrix.
    """

    areas = [a for a in bpy.context.screen.areas if a.type == "VIEW_3D"]
    if len(areas) > 0:
        vm = areas[0].spaces.active.region_3d.view_matrix
        vm = vm.to_3x3().normalized()
        vl = Vector((x_loc, y_loc, z_loc))
        vw = vm @ vl
        return vw
    else:
        return Vector((0, 0, 0))


def viewDir(dis_v, ang_v):
    """Converts Distance and Angle to View Oriented Vector.

    Converts View Transformation Matrix to Rotational Matrix (3x3)
    Angles are converted to Radians from degrees.

    Args:
        dis_v: Scene distance
        ang_v: Scene angle

    Returns:
        World Vector.
    """

    areas = [a for a in bpy.context.screen.areas if a.type == "VIEW_3D"]
    if len(areas) > 0:
        vm = areas[0].spaces.active.region_3d.view_matrix
        vm = vm.to_3x3().normalized().inverted()
        vl = Vector((0, 0, 0))
        vl.x = dis_v * cos(ang_v * pi / 180)
        vl.y = dis_v * sin(ang_v * pi / 180)
        vw = vm @ vl
        return vw
    else:
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
    qx = (np.sin(roll/2) * np.cos(pitch/2) * np.cos(yaw/2)
          - np.cos(roll/2) * np.sin(pitch/2) * np.sin(yaw/2))
    qy = (np.cos(roll/2) * np.sin(pitch/2) * np.cos(yaw/2)
          + np.sin(roll/2) * np.cos(pitch/2) * np.sin(yaw/2))
    qz = (np.cos(roll/2) * np.cos(pitch/2) * np.sin(yaw/2)
          - np.sin(roll/2) * np.sin(pitch/2) * np.cos(yaw/2))
    qw = (np.cos(roll/2) * np.cos(pitch/2) * np.cos(yaw/2)
          + np.sin(roll/2) * np.sin(pitch/2) * np.sin(yaw/2))
    # fmt: on
    return Quaternion((qw, qx, qy, qz))


def arcCentre(actV, othV, lstV):
    """Calculates Centre of Arc from 3 Vector Locations using standard Numpy routine

    Args:
        actV: Active vector location
        othV: Other vector location
        lstV: Last vector location

    Returns:
        Vector representing Arc Centre and Float representing Arc Radius.
    """

    A = np.array([actV.x, actV.y, actV.z])
    B = np.array([othV.x, othV.y, othV.z])
    C = np.array([lstV.x, lstV.y, lstV.z])
    a = np.linalg.norm(C - B)
    b = np.linalg.norm(C - A)
    c = np.linalg.norm(B - A)
    # fmt: off
    s = (a+b+c) / 2
    R = a*b*c/4 / np.sqrt(s * (s-a) * (s-b) * (s-c))
    b1 = a*a * (b*b + c*c - a*a)
    b2 = b*b * (a*a + c*c - b*b)
    b3 = c*c * (a*a + b*b - c*c)
    # fmt: on
    P = np.column_stack((A, B, C)).dot(np.hstack((b1, b2, b3)))
    P /= b1 + b2 + b3
    return Vector((P[0], P[1], P[2])), R


def intersection(actV, othV, lstV, fstV, plane):
    """Calculates Intersection Point of 2 Imagined Lines from 4 Vectors.

    Calculates Converging Intersect Location and indication of
    whether the lines are convergent using standard Numpy Routines

    Args:
        actV: Active vector location of first line
        othV: Other vector location of first line
        lstV: Last vector location of 2nd line
        fstV: First vector location of 2nd line
        plane: Working Plane 4 Vector Locations representing 2 lines and Working Plane

    Returns:
        Intersection Vector and Boolean for convergent state.
    """

    if plane == "LO":
        disV = othV - actV
        othV = viewCoordsI(disV.x, disV.y, disV.z)
        disV = lstV - actV
        lstV = viewCoordsI(disV.x, disV.y, disV.z)
        disV = fstV - actV
        fstV = viewCoordsI(disV.x, disV.y, disV.z)
        refV = Vector((0, 0, 0))
        ap1 = (fstV.x, fstV.y)
        ap2 = (lstV.x, lstV.y)
        bp1 = (othV.x, othV.y)
        bp2 = (refV.x, refV.y)
    else:
        a1, a2, a3 = setMode(plane)
        ap1 = (fstV[a1], fstV[a2])
        ap2 = (lstV[a1], lstV[a2])
        bp1 = (othV[a1], othV[a2])
        bp2 = (actV[a1], actV[a2])
    s = np.vstack([ap1, ap2, bp1, bp2])
    h = np.hstack((s, np.ones((4, 1))))
    l1 = np.cross(h[0], h[1])
    l2 = np.cross(h[2], h[3])
    x, y, z = np.cross(l1, l2)
    if z == 0:
        return Vector((0, 0, 0)), False
    nx = x / z
    nz = y / z
    if plane == "LO":
        ly = 0
    else:
        ly = actV[a3]
    # Order Vector Delta
    if plane == "XZ":
        vector_delta = Vector((nx, ly, nz))
    elif plane == "XY":
        vector_delta = Vector((nx, nz, ly))
    elif plane == "YZ":
        vector_delta = Vector((ly, nx, nz))
    elif plane == "LO":
        vector_delta = viewCoords(nx, nz, ly) + actV
    return vector_delta, True


def getPercent(obj, flip_p, per_v, data, scene):
    """Calculates a Percentage Distance between 2 Vectors.

    Calculates a point that lies a set percentage between two given points
    using standard Numpy Routines.

    Works for either 2 vertices for an object in Edit mode
    or 2 selected objects in Object mode.

    Args:
        obj: The Object under consideration
        flip_p: Setting this to True measures the percentage starting from the second vector
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
            actV = verts[0].co
            othV = verts[1].co
            if actV is None:
                pg.error = PDT_ERR_VERT_MODE
                bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return None
        else:
            pg.error = PDT_ERR_SEL_2_V_1_E + str(len(verts)) + " Vertices"
            bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return None
        p1 = np.array([actV.x, actV.y, actV.z])
        p2 = np.array([othV.x, othV.y, othV.z])
    if obj.mode == "OBJECT":
        objs = bpy.context.view_layer.objects.selected
        if len(objs) != 2:
            pg.error = PDT_ERR_SEL_2_OBJS + str(len(objs)) + ")"
            bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return None
        p1 = np.array(
            [
                objs[-1].matrix_world.decompose()[0].x,
                objs[-1].matrix_world.decompose()[0].y,
                objs[-1].matrix_world.decompose()[0].z,
            ]
        )
        p2 = np.array(
            [
                objs[-2].matrix_world.decompose()[0].x,
                objs[-2].matrix_world.decompose()[0].y,
                objs[-2].matrix_world.decompose()[0].z,
            ]
        )
    p4 = np.array([0, 0, 0])
    p3 = p2 - p1
    _per_v = per_v
    if (flip_p and data != "MV") or data == "MV":
        _per_v = 100 - per_v
    V = (p4+p3) * (_per_v / 100) + p1
    return Vector((V[0], V[1], V[2]))


def objCheck(obj, scene, oper):
    """Check Object & Selection Validity.

    Args:
        obj: Active Object
        scene: Active Scene
        oper: Operation to check

    Returns:
        Object Bmesh and Validity Boolean.
    """

    pg = scene.pdt_pg
    _oper = oper.upper()

    if obj is None:
        pg.error = PDT_ERR_NO_ACT_OBJ
        bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        return None, False
    if obj.mode == "EDIT":
        bm = bmesh.from_edit_mesh(obj.data)
        if _oper == "S":
            if len(bm.edges) < 1:
                pg.error = f"{PDT_ERR_SEL_1_EDGEM} {len(bm.edges)})"
                bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return None, False
            else:
                return bm, True
        if len(bm.select_history) >= 1:
            if _oper not in {"D", "E", "F", "G", "N", "S"}:
                actV = checkSelection(1, bm, obj)
            else:
                verts = [v for v in bm.verts if v.select]
                if len(verts) > 0:
                    actV = verts[0]
                else:
                    actV = None
            if actV is None:
                pg.error = PDT_ERR_VERT_MODE
                bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return None, False
        return bm, True
    elif obj.mode == "OBJECT":
        return None, True


def disAng(vals, flip_a, plane, scene):
    """Set Working Axes when using Direction command.

    Args:
        vals: Input Arguments (Values)
        flip_a: Whether to flip the angle
        plane: Working Plane
        scene: Current Scene

    Returns:
        Directional Offset as a Vector.
    """

    pg = scene.pdt_pg
    dis_v = float(vals[0])
    ang_v = float(vals[1])
    if flip_a:
        if ang_v > 0:
            ang_v = ang_v - 180
        else:
            ang_v = ang_v + 180
        pg.angle = ang_v
    if plane == "LO":
        vector_delta = viewDir(dis_v, ang_v)
    else:
        a1, a2, _ = setMode(plane)
        vector_delta = Vector((0, 0, 0))
        # fmt: off
        vector_delta[a1] = vector_delta[a1] + (dis_v * cos(ang_v * pi/180))
        vector_delta[a2] = vector_delta[a2] + (dis_v * sin(ang_v * pi/180))
        # FIXME: Is a3 just ignored?
        # fmt: on
    return vector_delta


# Shader for displaying the Pivot Point as Graphics.
#
shader = gpu.shader.from_builtin("3D_UNIFORM_COLOR") if not bpy.app.background else None


def draw3D(coords, gtype, rgba, context):
    """Draw Pivot Point Graphics.

    Draws either Lines Points, or Tris using defined shader

    Args:
        coords: Input Coordinates List
        gtype: Graphic Type
        rgba: Colour in RGBA format
        context: Blender bpy.context instance.

    Returns:
        Nothing.
    """

    batch = batch_for_shader(shader, gtype, {"pos": coords})

    try:
        if coords is not None:
            bgl.glEnable(bgl.GL_BLEND)
            shader.bind()
            shader.uniform_float("color", rgba)
            batch.draw(shader)
    except:
        pass


def drawCallback3D(self, context):
    """Create Coordinate List for Pivot Point Graphic.

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
    w = context.region.width
    x = pg.pivot_loc.x
    y = pg.pivot_loc.y
    z = pg.pivot_loc.z
    # Scale it from view
    areas = [a for a in context.screen.areas if a.type == "VIEW_3D"]
    if len(areas) > 0:
        sf = abs(areas[0].spaces.active.region_3d.window_matrix.decompose()[2][1])
    # Check for orhtographic view and resize
    if areas[0].spaces.active.region_3d.is_orthographic_side_view:
        a = w / sf / 60000 * pg.pivot_size
    else:
        a = w / sf / 5000 * pg.pivot_size
    b = a * 0.65
    c = a * 0.05 + (pg.pivot_width * a * 0.02)
    o = c / 3

    # fmt: off
    # X Axis
    coords = [
        (x, y, z),
        (x+b, y-o, z),
        (x+b, y+o, z),
        (x+a, y, z),
        (x+b, y+c, z),
        (x+b, y-c, z),
    ]
    # fmt: on
    colour = (1.0, 0.0, 0.0, pg.pivot_alpha)
    draw3D(coords, "TRIS", colour, context)
    coords = [(x, y, z), (x+a, y, z)]
    draw3D(coords, "LINES", colour, context)
    # fmt: off
    # Y Axis
    coords = [
        (x, y, z),
        (x-o, y+b, z),
        (x+o, y+b, z),
        (x, y+a, z),
        (x+c, y+b, z),
        (x-c, y+b, z),
    ]
    # fmt: on
    colour = (0.0, 1.0, 0.0, pg.pivot_alpha)
    draw3D(coords, "TRIS", colour, context)
    coords = [(x, y, z), (x, y + a, z)]
    draw3D(coords, "LINES", colour, context)
    # fmt: off
    # Z Axis
    coords = [
        (x, y, z),
        (x-o, y, z+b),
        (x+o, y, z+b),
        (x, y, z+a),
        (x+c, y, z+b),
        (x-c, y, z+b),
    ]
    # fmt: on
    colour = (0.2, 0.5, 1.0, pg.pivot_alpha)
    draw3D(coords, "TRIS", colour, context)
    coords = [(x, y, z), (x, y, z + a)]
    draw3D(coords, "LINES", colour, context)
    # Centre
    coords = [(x, y, z)]
    colour = (1.0, 1.0, 0.0, pg.pivot_alpha)
    draw3D(coords, "POINTS", colour, context)


def scale_set(self, context):
    """Sets Scale by dividing Pivot Distance by System Distance.

    Sets Pivot Point Scale Factors by Measurement

    Args:
        context: Blender bpy.context instance.

    Note:
        Uses pg.pivotdis & pg.distance scene variables

    Returns:
        Status Set.
    """

    scene = context.scene
    pg = scene.pdt_pg
    sys_dis = pg.distance
    scale_dis = pg.pivot_dis
    if scale_dis > 0:
        scale_fac = scale_dis / sys_dis
        pg.pivot_scale = Vector((scale_fac, scale_fac, scale_fac))
