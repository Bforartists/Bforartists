# SPDX-FileCopyrightText: 2019-2022 Alan Odom (Clockmender)
# SPDX-FileCopyrightText: 2019-2022 Rune Morling (ermo)
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
import bmesh
import math
from bpy.types import Operator
from mathutils import Vector
from .pdt_functions import (
    debug,
    intersection,
    obj_check,
    oops,
    update_sel,
    view_coords,
    view_dir,
)
from .pdt_command_functions import (
    vector_build,
    join_two_vertices,
    set_angle_distance_two,
    set_angle_distance_three,
    origin_to_cursor,
    taper,
    placement_normal,
    placement_arc_centre,
    placement_intersect,
)
from .pdt_msg_strings import (
    PDT_ERR_ADDVEDIT,
    PDT_ERR_BADFLETTER,
    PDT_ERR_CHARS_NUM,
    PDT_ERR_DUPEDIT,
    PDT_ERR_EXTEDIT,
    PDT_ERR_FACE_SEL,
    PDT_ERR_FILEDIT,
    PDT_ERR_NON_VALID,
    PDT_ERR_NO_SEL_GEOM,
    PDT_ERR_SEL_1_EDGE,
    PDT_ERR_SEL_1_EDGEM,
    PDT_ERR_SPLITEDIT,
    PDT_ERR_BADMATHS,
    PDT_OBJ_MODE_ERROR,
    PDT_ERR_SEL_4_VERTS,
    PDT_ERR_INT_LINES,
    PDT_LAB_PLANE,
    PDT_ERR_NO_ACT_OBJ,
    PDT_ERR_VERT_MODE,
)
from .pdt_bix import add_line_to_bisection
from .pdt_etof import extend_vertex
from .pdt_xall import intersect_all

from . import pdt_exception
PDT_SelectionError = pdt_exception.SelectionError
PDT_InvalidVector = pdt_exception.InvalidVector
PDT_CommandFailure = pdt_exception.CommandFailure
PDT_ObjectModeError = pdt_exception.ObjectModeError
PDT_MathsError = pdt_exception.MathsError
PDT_IntersectionError = pdt_exception.IntersectionError
PDT_NoObjectError = pdt_exception.NoObjectError
PDT_FeatureError = pdt_exception.FeatureError


class PDT_OT_CommandReRun(Operator):
    """Repeat Current Displayed Command"""

    bl_idname = "pdt.command_rerun"
    bl_label = "Re-run Current Command"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """Repeat Current Command Line Input.

        Args:
            context: Blender bpy.context instance.

        Returns:
            Nothing.
        """
        command_run(self, context)
        return {"FINISHED"}


def command_run(self, context):
    """Run Command String as input into Command Line.

    Note:
        Uses pg.command, pg.error & many other 'pg.' variables to set PDT menu items,
        or alter functions

        Command Format; Operation(single letter) Mode(single letter) Values(up to 3 values
        separated by commas)

        Example; CD0.4,0.6,1.1 - Moves Cursor Delta XYZ = 0.4,0.6,1.1 from Current Position/Active
        Vertex/Object Origin

        Example; SP35 - Splits active Edge at 35% of separation between edge's vertices

        Valid First Letters (as 'operation' - pg.command[0])
            C = Cursor, G = Grab(move), N = New Vertex, V = Extrude Vertices Only,
            E = Extrude geometry, P = Move Pivot Point, D = Duplicate geometry, S = Split Edges

            Capitals and lower case letters are both allowed

        Valid Second Letters (as 'mode' - pg.command[1])

            A = Absolute XYZ, D = Delta XYZ, I = Distance at Angle, P = Percent
            X = X Delta, Y = Y, Delta Z, = Z Delta, O = Output (Maths Operation only)
            V = Vertex Bevel, E = Edge Bevel, I = Intersect then Bevel

            Capitals and lower case letters are both allowed

        Valid Values (pdt_command[2:])
            Only Integers and Floats, missing values are set to 0, appropriate length checks are
            performed as Values is split by commas.

            Example; CA,,3 - Cursor to Absolute, is re-interpreted as CA0,0,3

            Exception for Maths Operation, Values section is evaluated as Maths expression

            Example; madegrees(atan(3/4)) - sets PDT Angle to smallest angle of 3,4,5 Triangle;
            (36.8699 degrees)

    Args:
        context: Blender bpy.context instance.

    Returns:
        Nothing.
    """

    scene = context.scene
    pg = scene.pdt_pg
    command = pg.command.strip()

    # Check Object Type & Mode First
    obj = context.view_layer.objects.active
    if obj is not None and command[0].upper() not in {"M", "?", "HELP"}:
        if obj.mode not in {"OBJECT", "EDIT"} or obj.type not in {"MESH", "EMPTY"}:
            pg.error = PDT_OBJ_MODE_ERROR
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            raise PDT_ObjectModeError

    # Special Cases of Command.
    if command == "?" or command.lower() == "help":
        # fmt: off
        context.window_manager.popup_menu(pdt_help, title="PDT Command Line Help", icon="INFO")
        # fmt: on
        return
    if command == "":
        return
    if command.upper() == "J2V":
        join_two_vertices(context)
        return
    if command.upper() == "AD2":
        set_angle_distance_two(context)
        return
    if command.upper() == "AD3":
        set_angle_distance_three(context)
        return
    if command.upper() == "OTC":
        origin_to_cursor(context)
        return
    if command.upper() == "TAP":
        taper(context)
        return
    if command.upper() == "BIS":
        add_line_to_bisection(context)
        return
    if command.upper() == "ETF":
        extend_vertex(context)
        return
    if command.upper() == "INTALL":
        intersect_all(context)
        return
    if command.upper()[1:] == "NML":
        placement_normal(context, command.upper()[0])
        return
    if command.upper()[1:] == "CEN":
        placement_arc_centre(context, command.upper()[0])
        return
    if command.upper()[1:] == "INT":
        placement_intersect(context, command.upper()[0])
        return

    # Check Command Length
    if len(command) < 3:
        pg.error = PDT_ERR_CHARS_NUM
        context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        return

    # Check First Letter
    operation = command[0].upper()
    if operation not in {"C", "D", "E", "F", "G", "N", "M", "P", "V", "S"}:
        pg.error = PDT_ERR_BADFLETTER
        context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        return

    # Check Second Letter.
    mode = command[1].lower()
    if (
            (operation == "F" and mode not in {"v", "e", "i"})
            or (operation in {"D", "E"} and mode not in {"d", "i", "n"}) #new
            or (operation == "M" and mode not in {"a", "d", "i", "p", "o", "x", "y", "z"})
            or (operation not in {"D", "E", "F", "M"} and mode not in {"a", "d", "i", "p", "n"}) #new
        ):
        pg.error = f"'{mode}' {PDT_ERR_NON_VALID} '{operation}'"
        context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        return

    # --------------
    # Maths Operation
    if operation == "M":
        try:
            command_maths(context, mode, pg, command[2:], mode)
            return
        except PDT_MathsError:
            return

    # -----------------------------------------------------
    # Not a Maths Operation, so let's parse the command line
    try:
        pg, values, obj, obj_loc, bm, verts = command_parse(context)
    except PDT_SelectionError:
        return

    # ---------------------
    # Cursor or Pivot Point
    if operation in {"C", "P"}:
        try:
            move_cursor_pivot(context, pg, operation, mode, obj, verts, values)
        except PDT_CommandFailure:
            return

    # ------------------------
    # Move Vertices or Objects
    if operation == "G":
        try:
            move_entities(context, pg, operation, mode, obj, bm, verts, values)
        except PDT_CommandFailure:
            return

    # --------------
    # Add New Vertex
    if operation == "N":
        try:
            add_new_vertex(context, pg, operation, mode, obj, bm, verts, values)
        except PDT_CommandFailure:
            return

    # -----------
    # Split Edges
    if operation == "S":
        try:
            split_edges(context, pg, operation, mode, obj, obj_loc, bm, values)
        except PDT_CommandFailure:
            return


    # ----------------
    # Extrude Vertices
    if operation == "V":
        try:
            extrude_vertices(context, pg, operation, mode, obj, obj_loc, bm, verts, values)
        except PDT_CommandFailure:
            return

    # ----------------
    # Extrude Geometry
    if operation == "E":
        try:
            extrude_geometry(context, pg, operation, mode, obj, bm, values)
        except PDT_CommandFailure:
            return

    # ------------------
    # Duplicate Geometry
    if operation == "D":
        try:
            duplicate_geometry(context, pg, operation, mode, obj, bm, values)
        except PDT_CommandFailure:
            return

    # ---------------
    # Fillet Geometry
    if operation == "F":
        try:
            fillet_geometry(context, pg, mode, obj, bm, verts, values)
        except PDT_CommandFailure:
            return


def pdt_help(self, context):
    """Display PDT Command Line help in a pop-up.

    Args:
        context: Blender bpy.context instance

    Returns:
        Nothing.
    """
    label = self.layout.label
    label(text="Primary Letters (Available Secondary Letters):")
    label(text="")
    label(text="C: Cursor (a, d, i, p, v)")
    label(text="D: Duplicate Geometry (d, i, v)")
    label(text="E: Extrude Geometry (d, i, v)")
    label(text="F: Fillet (v, e, i)")
    label(text="G: Grab (Move) (a, d, i, p, v)")
    label(text="N: New Vertex (a, d, i, p, v)")
    label(text="M: Maths Functions (a, d, p, o, x, y, z)")
    label(text="P: Pivot Point (a, d, i, p, v)")
    label(text="V: Extrude Vertice Only (a, d, i, p, v)")
    label(text="S: Split Edges (a, d, i, p)")
    label(text="?: Quick Help")
    label(text="")
    label(text="Secondary Letters:")
    label(text="")
    label(text="- General Options:")
    label(text="a: Absolute (Global) Coordinates e.g. 1,3,2")
    label(text="d: Delta (Relative) Coordinates, e.g. 0.5,0,1.2")
    label(text="i: Directional (Polar) Coordinates e.g. 2.6,45")
    label(text="p: Percent e.g. 67.5")
    label(text="n: Work in View Normal Axis")
    label(text="")
    label(text="- Fillet Options:")
    label(text="v: Fillet Vertices")
    label(text="e: Fillet Edges")
    label(text="i: Fillet & Intersect 2 Disconnected Edges")
    label(text="- Math Options:")
    label(text="x, y, z: Send result to X, Y and Z input fields in PDT Design")
    label(text="d, a, p: Send result to Distance, Angle or Percent input field in PDT Design")
    label(text="o: Send Maths Calculation to Output")
    label(text="")
    label(text="Note that commands are case-insensitive: ED = Ed = eD = ed")
    label(text="")
    label(text="Examples:")
    label(text="")
    label(text="ed0.5,,0.6")
    label(text="'- Extrude Geometry Delta 0.5 in X, 0 in Y, 0.6 in Z")
    label(text="")
    label(text="fe0.1,4,0.5")
    label(text="'- Fillet Edges")
    label(text="'- Radius: 0.1 (float) -- the radius (or offset) of the bevel/fillet")
    label(text="'- Segments: 4 (int) -- choosing an even amount of segments gives better geometry")
    label(text="'- Profile: 0.5 (float[0.0;1.0]) -- 0.5 (default) yields a circular, convex shape")
    label(text="")
    label(text="More Information at:")
    label(text="https://github.com/Clockmender/Precision-Drawing-Tools/wiki")


def command_maths(context, mode, pg, expression, output_target):
    """Evaluates Maths Input.

    Args:
        context: Blender bpy.context instance.
        mode: The Operation Mode, e.g. a for Absolute
        pg: PDT Parameters Group - our variables
        expression: The Maths component of the command input e.g. sqrt(56)
        output_target: The output variable box on the UI

    Returns:
        Nothing.
    """

    namespace = {}
    namespace.update(vars(math))
    try:
        maths_result = eval(expression, namespace, namespace)
    except:
        pg.error = PDT_ERR_BADMATHS
        context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        raise PDT_MathsError

    decimal_places = context.preferences.addons[__package__].preferences.pdt_input_round
    if output_target == "x":
        pg.cartesian_coords.x = round(maths_result, decimal_places)
    elif output_target == "y":
        pg.cartesian_coords.y = round(maths_result, decimal_places)
    elif output_target == "z":
        pg.cartesian_coords.z = round(maths_result, decimal_places)
    elif output_target == "d":
        pg.distance = round(maths_result, decimal_places)
    elif output_target == "a":
        pg.angle = round(maths_result, decimal_places)
    elif output_target == "p":
        pg.percent = round(maths_result, decimal_places)
    else:
        # Must be "o"
        pg.maths_output = round(maths_result, decimal_places)


def command_parse(context):
    """Parse Command Input.

    Args:
        context: Blender bpy.context instance.

    Returns:
        pg: PDT Parameters Group - our variables
        values_out: The Output Values as a list of numbers
        obj: The Active Object
        obj_loc: The object's location in 3D space
        bm: The object's Bmesh
        verts: The object's selected vertices, or selected history vertices.
    """
    scene = context.scene
    pg = scene.pdt_pg
    command = pg.command.strip()
    operation = command[0].upper()
    mode = command[1].lower()
    values = command[2:].split(",")
    mode_sel = pg.select
    obj = context.view_layer.objects.active
    ind = 0
    for v in values:
        try:
            _ = float(v)
            good = True
        except ValueError:
            values[ind] = "0.0"
        ind = ind + 1
    if mode == "n":
        # View relative mode
        if pg.plane == "XZ":
            values = [0.0, values[0], 0.0]
        elif pg.plane == "YZ":
            values = [values[0], 0.0, 0.0]
        elif pg.plane == "XY":
            values = [0.0, 0.0, values[0]]
        else:
            if "-" in values[0]:
                values = [0.0, 0.0, values[0][1:]]
            else:
                values = [0.0, 0.0, f"-{values[0]}"]
    # Apply System Rounding
    decimal_places = context.preferences.addons[__package__].preferences.pdt_input_round
    values_out = [str(round(float(v), decimal_places)) for v in values]
    bm = "No Bmesh"
    obj_loc = Vector((0,0,0))
    verts = []

    if mode_sel == 'REL' and operation not in {"C", "P"}:
        pg.select = 'SEL'
        mode_sel = 'SEL'

    if mode == "a" and operation not in {"C", "P"}:
        # Place new Vertex, or Extrude Vertices by Absolute Coords.
        if mode_sel == 'REL':
            pg.select = 'SEL'
            mode_sel = 'SEL'
        if obj is not None:
            if obj.mode == "EDIT":
                bm = bmesh.from_edit_mesh(obj.data)
                obj_loc = obj.matrix_world.decompose()[0]
                verts = []
            else:
                if operation != "G":
                    pg.error = PDT_OBJ_MODE_ERROR
                    context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                    raise PDT_ObjectModeError
        else:
            pg.error = PDT_ERR_NO_ACT_OBJ
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            raise PDT_NoObjectError

    if mode_sel == 'SEL' and mode not in {"a"}:
        # All other options except Cursor or Pivot by Absolute
        # These options require no object, etc.
        bm, good = obj_check(obj, scene, operation)
        if good and obj.mode == 'EDIT':
            obj_loc = obj.matrix_world.decompose()[0]
            if len(bm.select_history) == 0 or operation == "G":
                verts = [v for v in bm.verts if v.select]
                if len(verts) == 0:
                    pg.error = PDT_ERR_NO_SEL_GEOM
                    context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                    raise PDT_SelectionError
            else:
                verts = bm.select_history

    debug(f"command: {operation}{mode}{values_out}")
    debug(f"obj: {obj}, bm: {bm}, obj_loc: {obj_loc}")

    return pg, values_out, obj, obj_loc, bm, verts


def move_cursor_pivot(context, pg, operation, mode, obj, verts, values):
    """Moves Cursor & Pivot Point.

    Args:
        context: Blender bpy.context instance.
        pg: PDT Parameters Group - our variables
        operation: The Operation e.g. Create New Vertex
        mode: The Operation Mode, e.g. a for Absolute
        obj: The Active Object
        verts: The object's selected vertices, or selected history vertices
        values: The parameters passed e.g. 1,4,3 for Cartesian Coordinates

    Returns:
        Nothing.
    """

    # Absolute/Global Coordinates, or Delta/Relative Coordinates
    if mode in {"a", "d", "n"}:
        try:
            vector_delta = vector_build(context, pg, obj, operation, values, 3)
        except:
            raise PDT_InvalidVector
    # Direction/Polar Coordinates
    elif mode == "i":
        try:
            vector_delta = vector_build(context, pg, obj, operation, values, 2)
        except:
            raise PDT_InvalidVector
    # Percent Options
    else:
        # Must be Percent
        try:
            vector_delta = vector_build(context, pg, obj, operation, values, 1)
        except:
            raise PDT_InvalidVector

    scene = context.scene
    mode_sel = pg.select
    obj_loc = Vector((0,0,0))
    if obj is not None:
        obj_loc = obj.matrix_world.decompose()[0]

    if mode == "a":
        if operation == "C":
            scene.cursor.location = vector_delta
        elif operation == "P":
            pg.pivot_loc = vector_delta
    elif mode in {"d", "i", "n"}:
        if pg.plane == "LO" and mode in  {"d", "n"}:
            vector_delta = view_coords(vector_delta.x, vector_delta.y, vector_delta.z)
        elif pg.plane == "LO" and mode == "i":
            vector_delta = view_dir(pg.distance, pg.angle)
        if mode_sel == "REL":
            if operation == "C":
                scene.cursor.location = scene.cursor.location + vector_delta
            else:
                pg.pivot_loc = pg.pivot_loc + vector_delta
        elif mode_sel == "SEL":
            if obj.mode == "EDIT":
                if operation == "C":
                    scene.cursor.location = verts[-1].co + obj_loc + vector_delta
                else:
                    pg.pivot_loc = verts[-1].co + obj_loc + vector_delta
            if obj.mode == "OBJECT":
                if operation == "C":
                    scene.cursor.location = obj_loc + vector_delta
                else:
                    pg.pivot_loc = obj_loc + vector_delta
    else:
        # Must be Percent
        if obj.mode == "EDIT":
            if operation == "C":
                scene.cursor.location = obj_loc + vector_delta
            else:
                pg.pivot_loc = obj_loc + vector_delta
        if obj.mode == "OBJECT":
            if operation == "C":
                scene.cursor.location = vector_delta
            else:
                pg.pivot_loc = vector_delta


def move_entities(context, pg, operation, mode, obj, bm, verts, values):
    """Moves Entities.

    Args:
        context: Blender bpy.context instance.
        pg: PDT Parameters Group - our variables
        operation: The Operation e.g. Create New Vertex
        mode: The Operation Mode, e.g. a for Absolute
        obj: The Active Object
        bm: The object's Bmesh
        verts: The object's selected vertices, or selected history vertices
        values: The parameters passed e.g. 1,4,3 for Cartesian Coordinates

    Returns:
        Nothing.
    """

    obj_loc = obj.matrix_world.decompose()[0]

    # Absolute/Global Coordinates
    if mode == "a":
        try:
            vector_delta = vector_build(context, pg, obj, operation, values, 3)
        except:
            raise PDT_InvalidVector
        if obj.mode == "EDIT":
            for v in [v for v in bm.verts if v.select]:
                v.co = vector_delta - obj_loc
            bmesh.ops.remove_doubles(
                bm, verts=[v for v in bm.verts if v.select], dist=0.0001
            )
        if obj.mode == "OBJECT":
            for ob in context.view_layer.objects.selected:
                ob.location = vector_delta

    elif mode in {"d", "i", "n"}:
        if mode in {"d", "n"}:
            # Delta/Relative Coordinates
            try:
                vector_delta = vector_build(context, pg, obj, operation, values, 3)
            except:
                raise PDT_InvalidVector
        else:
            # Direction/Polar Coordinates
            try:
                vector_delta = vector_build(context, pg, obj, operation, values, 2)
            except:
                raise PDT_InvalidVector

        if pg.plane == "LO" and mode in {"d", "n"}:
            vector_delta = view_coords(vector_delta.x, vector_delta.y, vector_delta.z)
        elif pg.plane == "LO" and mode == "i":
            vector_delta = view_dir(pg.distance, pg.angle)

        if obj.mode == "EDIT":
            bmesh.ops.translate(
                bm, verts=[v for v in bm.verts if v.select], vec=vector_delta
            )
        if obj.mode == "OBJECT":
            for ob in context.view_layer.objects.selected:
                ob.location = obj_loc + vector_delta
    # Percent Options Only Other Choice
    else:
        try:
            vector_delta = vector_build(context, pg, obj, operation, values, 1)
        except:
            raise PDT_InvalidVector
        if obj.mode == 'EDIT':
            verts[-1].co = vector_delta
        if obj.mode == "OBJECT":
            obj.location = vector_delta
    if obj.mode == 'EDIT':
        bmesh.update_edit_mesh(obj.data)
        bm.select_history.clear()


def add_new_vertex(context, pg, operation, mode, obj, bm, verts, values):
    """Add New Vertex.

    Args:
        context: Blender bpy.context instance.
        pg, operation, mode, obj, bm, verts, values

    Returns:
        Nothing.
    """

    obj_loc = obj.matrix_world.decompose()[0]

    if not obj.mode == "EDIT":
        pg.error = PDT_ERR_ADDVEDIT
        context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        raise PDT_SelectionError
    if mode not in {"a"}:
        if not isinstance(verts[0], bmesh.types.BMVert):
            pg.error = PDT_ERR_VERT_MODE
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            raise PDT_FeatureError
    # Absolute/Global Coordinates
    if mode == "a":
        try:
            vector_delta = vector_build(context, pg, obj, operation, values, 3)
        except:
            raise PDT_InvalidVector
        new_vertex = bm.verts.new(vector_delta - obj_loc)
    # Delta/Relative Coordinates
    elif mode in  {"d", "n"}:
        try:
            vector_delta = vector_build(context, pg, obj, operation, values, 3)
        except:
            raise PDT_InvalidVector
        if pg.plane == "LO":
            vector_delta = view_coords(vector_delta.x, vector_delta.y, vector_delta.z)
        new_vertex = bm.verts.new(verts[-1].co + vector_delta)
    # Direction/Polar Coordinates
    elif mode == "i":
        try:
            vector_delta = vector_build(context, pg, obj, operation, values, 2)
        except:
            raise PDT_InvalidVector
        if pg.plane == "LO":
            vector_delta = view_dir(pg.distance, pg.angle)
        new_vertex = bm.verts.new(verts[-1].co + vector_delta)
    # Percent Options Only Other Choice
    else:
        try:
            vector_delta = vector_build(context, pg, obj, operation, values, 1)
        except:
            raise PDT_InvalidVector
        new_vertex = bm.verts.new(vector_delta)

    for v in [v for v in bm.verts if v.select]:
        v.select_set(False)
    new_vertex.select_set(True)
    bmesh.update_edit_mesh(obj.data)
    bm.select_history.clear()


def split_edges(context, pg, operation, mode, obj, obj_loc, bm, values):
    """Split Edges.

    Args:
        context: Blender bpy.context instance.
        pg: PDT Parameters Group - our variables
        operation: The Operation e.g. Create New Vertex
        mode: The Operation Mode, e.g. a for Absolute
        obj: The Active Object
        obj_loc: The object's location in 3D space
        bm: The object's Bmesh
        verts: The object's selected vertices, or selected history vertices
        values: The parameters passed e.g. 1,4,3 for Cartesian Coordinates

    Returns:
        Nothing.
    """

    if not obj.mode == "EDIT":
        pg.error = PDT_ERR_SPLITEDIT
        context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        return
    # Absolute/Global Coordinates
    if mode == "a":
        try:
            vector_delta = vector_build(context, pg, obj, operation, values, 3)
        except:
            raise PDT_InvalidVector
        edges = [e for e in bm.edges if e.select]
        if len(edges) != 1:
            pg.error = f"{PDT_ERR_SEL_1_EDGE} {len(edges)})"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
        geom = bmesh.ops.subdivide_edges(bm, edges=edges, cuts=1)
        new_verts = [v for v in geom["geom_split"] if isinstance(v, bmesh.types.BMVert)]
        new_vertex = new_verts[0]
        new_vertex.co = vector_delta - obj_loc
    # Delta/Relative Coordinates
    elif mode == "d":
        try:
            vector_delta = vector_build(context, pg, obj, operation, values, 3)
        except:
            raise PDT_InvalidVector
        edges = [e for e in bm.edges if e.select]
        faces = [f for f in bm.faces if f.select]
        if len(faces) != 0:
            pg.error = PDT_ERR_FACE_SEL
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
        if len(edges) < 1:
            pg.error = f"{PDT_ERR_SEL_1_EDGEM} {len(edges)})"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
        geom = bmesh.ops.subdivide_edges(bm, edges=edges, cuts=1)
        new_verts = [v for v in geom["geom_split"] if isinstance(v, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, verts=new_verts, vec=vector_delta)
    # Directional/Polar Coordinates
    elif mode == "i":
        try:
            vector_delta = vector_build(context, pg, obj, operation, values, 2)
        except:
            raise PDT_InvalidVector
        edges = [e for e in bm.edges if e.select]
        faces = [f for f in bm.faces if f.select]
        if len(faces) != 0:
            pg.error = PDT_ERR_FACE_SEL
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
        if len(edges) < 1:
            pg.error = f"{PDT_ERR_SEL_1_EDGEM} {len(edges)})"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
        geom = bmesh.ops.subdivide_edges(bm, edges=edges, cuts=1)
        new_verts = [v for v in geom["geom_split"] if isinstance(v, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, verts=new_verts, vec=vector_delta)
    # Percent Options
    elif mode == "p":
        try:
            vector_delta = vector_build(context, pg, obj, operation, values, 1)
        except:
            raise PDT_InvalidVector
        edges = [e for e in bm.edges if e.select]
        faces = [f for f in bm.faces if f.select]
        if len(faces) != 0:
            pg.error = PDT_ERR_FACE_SEL
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
        if len(edges) != 1:
            pg.error = f"{PDT_ERR_SEL_1_EDGEM} {len(edges)})"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
        geom = bmesh.ops.subdivide_edges(bm, edges=edges, cuts=1)
        new_verts = [v for v in geom["geom_split"] if isinstance(v, bmesh.types.BMVert)]
        new_vertex = new_verts[0]
        new_vertex.co = vector_delta

    for v in [v for v in bm.verts if v.select]:
        v.select_set(False)
    for v in new_verts:
        v.select_set(False)
    bmesh.update_edit_mesh(obj.data)
    bm.select_history.clear()


def extrude_vertices(context, pg, operation, mode, obj, obj_loc, bm, verts, values):
    """Extrude Vertices.

    Args:
        context: Blender bpy.context instance.
        pg: PDT Parameters Group - our variables
        operation: The Operation e.g. Create New Vertex
        mode: The Operation Mode, e.g. a for Absolute
        obj: The Active Object
        obj_loc: The object's location in 3D space
        bm: The object's Bmesh
        verts: The object's selected vertices, or selected history vertices
        values: The parameters passed e.g. 1,4,3 for Cartesian Coordinates

    Returns:
        Nothing.
    """

    if not obj.mode == "EDIT":
        pg.error = PDT_ERR_EXTEDIT
        context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        return
    # Absolute/Global Coordinates
    if mode == "a":
        try:
            vector_delta = vector_build(context, pg, obj, operation, values, 3)
        except:
            raise PDT_InvalidVector
        new_vertex = bm.verts.new(vector_delta - obj_loc)
        verts = [v for v in bm.verts if v.select].copy()
        for v in verts:
            bm.edges.new([v, new_vertex])
            v.select_set(False)
        new_vertex.select_set(True)
        bmesh.ops.remove_doubles(
            bm, verts=[v for v in bm.verts if v.select], dist=0.0001
        )
    # Delta/Relative Coordinates
    elif mode in {"d", "n"}:
        try:
            vector_delta = vector_build(context, pg, obj, operation, values, 3)
        except:
            raise PDT_InvalidVector
        if pg.plane == "LO":
            vector_delta = view_coords(vector_delta.x, vector_delta.y, vector_delta.z)
        for v in verts:
            new_vertex = bm.verts.new(v.co)
            new_vertex.co = new_vertex.co + vector_delta
            bm.edges.new([v, new_vertex])
            v.select_set(False)
            new_vertex.select_set(True)
    # Direction/Polar Coordinates
    elif mode == "i":
        try:
            vector_delta = vector_build(context, pg, obj, operation, values, 2)
        except:
            raise PDT_InvalidVector
        if pg.plane == "LO":
            vector_delta = view_dir(pg.distance, pg.angle)
        for v in verts:
            new_vertex = bm.verts.new(v.co)
            new_vertex.co = new_vertex.co + vector_delta
            bm.edges.new([v, new_vertex])
            v.select_set(False)
            new_vertex.select_set(True)
    # Percent Options
    elif mode == "p":
        extend_all  = pg.extend
        try:
            vector_delta = vector_build(context, pg, obj, operation, values, 1)
        except:
            raise PDT_InvalidVector
        verts = [v for v in bm.verts if v.select].copy()
        new_vertex = bm.verts.new(vector_delta)
        if extend_all:
            for v in [v for v in bm.verts if v.select]:
                bm.edges.new([v, new_vertex])
                v.select_set(False)
        else:
            bm.edges.new([verts[-1], new_vertex])
        new_vertex.select_set(True)

    bmesh.update_edit_mesh(obj.data)


def extrude_geometry(context, pg, operation, mode, obj, bm, values):
    """Extrude Geometry.

    Args:
        context: Blender bpy.context instance.
        pg: PDT Parameters Group - our variables
        operation: The Operation e.g. Create New Vertex
        mode: The Operation Mode, e.g. a for Absolute
        obj: The Active Object
        bm: The object's Bmesh
        values: The parameters passed e.g. 1,4,3 for Cartesian Coordinates

    Returns:
        Nothing.
    """

    if not obj.mode == "EDIT":
        pg.error = PDT_ERR_EXTEDIT
        context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        return
    # Delta/Relative Coordinates
    if mode in {"d", "n"}:
        try:
            vector_delta = vector_build(context, pg, obj, operation, values, 3)
        except:
            raise PDT_InvalidVector
    # Direction/Polar Coordinates
    elif mode == "i":
        try:
            vector_delta = vector_build(context, pg, obj, operation, values, 2)
        except:
            raise PDT_InvalidVector

    ret = bmesh.ops.extrude_face_region(
        bm,
        geom=(
            [f for f in bm.faces if f.select]
            + [e for e in bm.edges if e.select]
            + [v for v in bm.verts if v.select]
        ),
        use_select_history=True,
    )
    geom_extr = ret["geom"]
    verts_extr = [v for v in geom_extr if isinstance(v, bmesh.types.BMVert)]
    edges_extr = [e for e in geom_extr if isinstance(e, bmesh.types.BMEdge)]
    faces_extr = [f for f in geom_extr if isinstance(f, bmesh.types.BMFace)]
    del ret

    if pg.plane == "LO" and mode in {"d", "n"}:
        vector_delta = view_coords(vector_delta.x, vector_delta.y, vector_delta.z)
    elif pg.plane == "LO" and mode == "i":
        vector_delta = view_dir(pg.distance, pg.angle)

    bmesh.ops.translate(bm, verts=verts_extr, vec=vector_delta)
    update_sel(bm, verts_extr, edges_extr, faces_extr)
    bmesh.update_edit_mesh(obj.data)
    bm.select_history.clear()


def duplicate_geometry(context, pg, operation, mode, obj, bm, values):
    """Duplicate Geometry.

    Args:
        context: Blender bpy.context instance.
        pg: PDT Parameters Group - our variables
        operation: The Operation e.g. Create New Vertex
        mode: The Operation Mode, e.g. a for Absolute
        obj: The Active Object
        bm: The object's Bmesh
        values: The parameters passed e.g. 1,4,3 for Cartesian Coordinates

    Returns:
        Nothing.
    """

    if not obj.mode == "EDIT":
        pg.error = PDT_ERR_DUPEDIT
        context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        return
    # Delta/Relative Coordinates
    if mode in {"d", "n"}:
        try:
            vector_delta = vector_build(context, pg, obj, operation, values, 3)
        except:
            raise PDT_InvalidVector
    # Direction/Polar Coordinates
    elif mode == "i":
        try:
            vector_delta = vector_build(context, pg, obj, operation, values, 2)
        except:
            raise PDT_InvalidVector

    ret = bmesh.ops.duplicate(
        bm,
        geom=(
            [f for f in bm.faces if f.select]
            + [e for e in bm.edges if e.select]
            + [v for v in bm.verts if v.select]
        ),
        use_select_history=True,
    )
    geom_dupe = ret["geom"]
    verts_dupe = [v for v in geom_dupe if isinstance(v, bmesh.types.BMVert)]
    edges_dupe = [e for e in geom_dupe if isinstance(e, bmesh.types.BMEdge)]
    faces_dupe = [f for f in geom_dupe if isinstance(f, bmesh.types.BMFace)]
    del ret

    if pg.plane == "LO" and mode in  {"d", "n"}:
        vector_delta = view_coords(vector_delta.x, vector_delta.y, vector_delta.z)
    elif pg.plane == "LO" and mode == "i":
        vector_delta = view_dir(pg.distance, pg.angle)

    bmesh.ops.translate(bm, verts=verts_dupe, vec=vector_delta)
    update_sel(bm, verts_dupe, edges_dupe, faces_dupe)
    bmesh.update_edit_mesh(obj.data)


def fillet_geometry(context, pg, mode, obj, bm, verts, values):
    """Fillet Geometry.

    Args:
        context: Blender bpy.context instance.
        pg: PDT Parameters Group - our variables
        operation: The Operation e.g. Create New Vertex
        mode: The Operation Mode, e.g. a for Absolute
        obj: The Active Object
        bm: The object's Bmesh
        verts: The object's selected vertices, or selected history vertices
        values: The parameters passed e.g. 1,4,3 for Cartesian Coordinates

    Returns:
        Nothing.
    """

    if not obj.mode == "EDIT":
        pg.error = PDT_ERR_FILEDIT
        context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        return
    if mode in {"i", "v"}:
        affect = 'VERTICES'
    else:
        # Must be "e"
        affect = 'EDGES'
    # Note that passing an empty parameter results in that parameter being seen as "0"
    # _offset <= 0 is ignored since a bevel/fillet radius must be > 0 to make sense
    _offset = float(values[0])
    # Force _segments to an integer (bug fix T95442)
    _segments = int(float(values[1]))
    if _segments < 1:
        _segments = 1   # This is a single, flat segment (ignores profile)
    _profile = float(values[2])
    if _profile < 0.0 or _profile > 1.0:
        _profile = 0.5  # This is a circular profile
    if mode == "i":
        # Fillet & Intersect Two Edges
        # Always use Current Selection
        verts = [v for v in bm.verts if v.select]
        edges = [e for e in bm.edges if e.select]
        if len(edges) == 2 and len(verts) == 4:
            plane = pg.plane
            v_active = edges[0].verts[0]
            v_other = edges[0].verts[1]
            v_last = edges[1].verts[0]
            v_first = edges[1].verts[1]
            vector_delta, done = intersection(v_active.co,
                                              v_other.co,
                                              v_last.co,
                                              v_first.co,
                                              plane
                                              )
            if not done:
                pg.error = f"{PDT_ERR_INT_LINES} {plane}  {PDT_LAB_PLANE}"
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                raise PDT_IntersectionError
            if (v_active.co - vector_delta).length < (v_other.co - vector_delta).length:
                v_active.co = vector_delta
                v_other.select_set(False)
            else:
                v_other.co = vector_delta
                v_active.select_set(False)
            if (v_last.co - vector_delta).length < (v_first.co - vector_delta).length:
                v_last.co = vector_delta
                v_first.select_set(False)
            else:
                v_first.co = vector_delta
                v_last.select_set(False)
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
        else:
            pg.error = f"{PDT_ERR_SEL_4_VERTS} {len(verts)} Vert(s), {len(edges)} Edge(s))"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            raise PDT_SelectionError

    bpy.ops.mesh.bevel(
        offset_type="OFFSET",
        offset=_offset,
        segments=_segments,
        profile=_profile,
        affect=affect
    )
