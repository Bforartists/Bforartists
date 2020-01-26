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
#
# -----------------------------------------------------------------------
# Author: Alan Odom (Clockmender), Rune Morling (ermo) Copyright (c) 2019
# -----------------------------------------------------------------------
#
import bpy
import bmesh
from bpy.types import Operator
from mathutils import Vector
import math
from .pdt_functions import (
    debug,
    disAng,
    getPercent,
    intersection,
    objCheck,
    oops,
    updateSel,
)
from .pdt_msg_strings import (
    PDT_ERR_ADDVEDIT,
    PDT_ERR_BAD1VALS,
    PDT_ERR_BAD2VALS,
    PDT_ERR_BAD3VALS,
    PDT_ERR_BADCOORDL,
    PDT_ERR_BADFLETTER,
    PDT_ERR_BADMATHS,
    PDT_ERR_BADSLETTER,
    PDT_ERR_CHARS_NUM,
    PDT_ERR_DUPEDIT,
    PDT_ERR_EXTEDIT,
    PDT_ERR_FACE_SEL,
    PDT_ERR_FILEDIT,
    PDT_ERR_NOCOMMAS,
    PDT_ERR_NON_VALID,
    PDT_ERR_NO_ACT_OBJ,
    PDT_ERR_NO_SEL_GEOM,
    PDT_ERR_SEL_1_EDGE,
    PDT_ERR_SEL_1_EDGEM,
    PDT_ERR_SEL_1_VERT,
    PDT_ERR_SPLITEDIT
)


def pdt_help(self, context):
    """Display PDT Command Line help in a pop-up."""
    label = self.layout.label
    label(text="Primary Letters (Available Secondary Letters):")
    label(text="")
    label(text="C: Cursor (a, d, i, p)")
    label(text="D: Duplicate Geometry (d, i)")
    label(text="E: Extrude Geometry (d, i)")
    label(text="F: Fillet (v, e)")
    label(text="G: Grab (Move) (a, d, i, p)")
    label(text="N: New Vertex (a, d, i, p)")
    label(text="M: Maths Functions (x, y, z, d, a, p)")
    label(text="P: Pivot Point (a, d, i, p)")
    label(text="V: Extrude Vertice Only (a, d, i, p)")
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

class PDT_OT_CommandReRun(Operator):
    """Repeat Current Displayed Command."""

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

    Args:
        context: Blender bpy.context instance.

    Note:
        Uses pg.command, pg.error & many other 'pg.' variables to set PDT menu items,
        or alter functions

        Command Format; Operation(single letter) Mode(single letter) Values(up to 3 values
        separated by commas)

        Example; CD0.4,0.6,1.1 - Moves Cursor Delta XYZ = 0.4,0.6,1.1 from Current Position/Active
        Vertex/Object Origin

        Example; SP35 - Splits active Edge at 35% of separation between edge's vertices

        Valid First Letters (as 'oper' - pg.command[0])
            C = Cursor, G = Grab(move), N = New Vertex, V = Extrude Vertices Only,
            E = Extrude geometry, P = Move Pivot Point, D = Duplicate geometry, S = Split Edges

            Capitals and lower case letters are both allowed

        Valid Second Letters (as 'mode' - pg.command[1])

            A = Absolute XYZ, D = Delta XYZ, I = Distance at Angle, P = Percent
            X = X Delta, Y = Y, Delta Z, = Z Delta, O = Output (Maths Operation only)
            V = Vertex Bevel, E = Edge Bevel

            Capitals and lower case letters are both allowed

        Valid Values (pdt_command[2:])
            Only Integers and Floats, missing values are set to 0, appropriate length checks are
            performed as Values is split by commas.

            Example; CA,,3 - Cursor to Absolute, is re-interpreted as CA0,0,3

            Exception for Maths Operation, Values section is evaluated as Maths command

            Example; madegrees(atan(3/4)) - sets PDT Angle to smallest angle of 3,4,5 Triangle;
            (36.8699 degrees)

    Returns:
        Nothing.
    """

    scene = context.scene
    pg = scene.pdt_pg
    cmd = pg.command.strip()

    if cmd == "?" or cmd.lower() == "help":
        # fmt: off
        context.window_manager.popup_menu(pdt_help, title="PDT Command Line Help", icon="INFO")
        # fmt: on
        return
    elif cmd == "":
        return
    elif len(cmd) < 3:
        pg.error = PDT_ERR_CHARS_NUM
        context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        return
    oper = cmd[0].upper()
    if oper not in {"C", "D", "E", "F", "G", "N", "M", "P", "V", "S"}:
        pg.error = PDT_ERR_BADFLETTER
        context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        return
    mode = cmd[1].lower()
    if mode not in {"a", "d", "e", "g", "i", "o", "p", "v", "x", "y", "z"}:
        pg.error = PDT_ERR_BADSLETTER
        context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        return

    # --------------
    # Math Operation
    if oper == "M":
        if mode not in {"x", "y", "z", "d", "a", "p", "o"}:
            pg.error = f"{mode} {PDT_ERR_NON_VALID} Maths)"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
        exp = cmd[2:]
        namespace = {}
        namespace.update(vars(math))
        try:
            num = eval(exp, namespace, namespace)
        except ValueError:
            pg.error = PDT_ERR_BADMATHS
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
        if mode == "x":
            pg.cartesian_coords.x = num
        elif mode == "y":
            pg.cartesian_coords.y = num
        elif mode == "z":
            pg.cartesian_coords.z = num
        elif mode == "d":
            pg.distance = num
        elif mode == "a":
            pg.angle = num
        elif mode == "p":
            pg.percent = num
        elif mode == "o":
            pg.maths_output = num
        return
    # "o"/"x"/"y"/"z" modes are only legal for Math Operation
    else:
        if mode in {"o", "x", "y", "z"}:
            pg.error = PDT_ERR_BADCOORDL
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return

    # -----------------------------------------------------
    # Not a Math Operation, so let's parse the command line
    vals = cmd[2:].split(",")
    ind = 0
    for r in vals:
        try:
            _ = float(r)
            good = True
        except ValueError:
            vals[ind] = "0"
        ind = ind + 1
    mode_s = pg.select
    flip_a = pg.flip_angle
    flip_p = pg.flip_percent
    ext_a = pg.extend
    plane = pg.plane
    obj = context.view_layer.objects.active
    #FIXME: What does call this imply in terms of invariants?
    #       There's a lot of places in the code where we rely on bm not being None...
    bm, good = objCheck(obj, scene, oper)
    obj_loc = None
    if good:
        obj_loc = obj.matrix_world.decompose()[0]
    debug(f"cmd: {cmd}")
    debug(f"obj: {obj}, bm: {bm}, obj_loc: {obj_loc}")

    # static set variable for use in recurring comparisons
    adip = {"a", "d", "i", "p"}

    # ---------------------
    # Cursor or Pivot Point
    if oper in {"C", "P"}:
        if mode not in adip:
            pg.error = f"'{mode}' {PDT_ERR_NON_VALID} '{oper}'"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
        if mode in {"d","i"}:
            if len(bm.select_history) == 0:
                if len(bm.verts) == 0:
                    pg.error = PDT_ERR_NO_SEL_GEOM
                    context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                    return
                else:
                    verts = bm.verts
            else:
                verts = bm.select_history
        # Absolute/Global Coordinates
        if mode == "a":
            if len(vals) != 3:
                pg.error = PDT_ERR_BAD3VALS
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return
            vector_delta = Vector((float(vals[0]), float(vals[1]), float(vals[2])))
            if oper == "C":
                scene.cursor.location = vector_delta
            else:
                pg.pivot_loc = vector_delta
        # Delta/Relative Coordinates
        elif mode == "d":
            if len(vals) != 3:
                pg.error = PDT_ERR_BAD3VALS
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return
            vector_delta = Vector((float(vals[0]), float(vals[1]), float(vals[2])))
            if mode_s == "REL":
                if oper == "C":
                    scene.cursor.location = scene.cursor.location + vector_delta
                else:
                    pg.pivot_loc = pg.pivot_loc + vector_delta
            elif mode_s == "SEL":
                if obj.mode == "EDIT":
                    if oper == "C":
                        scene.cursor.location = (
                            verts[-1].co + obj_loc + vector_delta
                        )
                    else:
                        pg.pivot_loc = verts[-1].co + obj_loc + vector_delta
                elif obj.mode == "OBJECT":
                    if oper == "C":
                        scene.cursor.location = obj_loc + vector_delta
                    else:
                        pg.pivot_loc = obj_loc + vector_delta
        # Direction/Polar Coordinates
        elif mode == "i":
            if len(vals) != 2:
                pg.error = PDT_ERR_BAD2VALS
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return
            vector_delta = disAng(vals, flip_a, plane, scene)
            if mode_s == "REL":
                if oper == "C":
                    scene.cursor.location = scene.cursor.location + vector_delta
                else:
                    pg.pivot_loc = pg.pivot_loc + vector_delta
            elif mode_s == "SEL":
                if obj.mode == "EDIT":
                    if oper == "C":
                        scene.cursor.location = (
                            verts[-1].co + obj_loc + vector_delta
                        )
                    else:
                        pg.pivot_loc = verts[-1].co + obj_loc + vector_delta
                elif obj.mode == "OBJECT":
                    if oper == "C":
                        scene.cursor.location = obj_loc + vector_delta
                    else:
                        pg.pivot_loc = obj_loc + vector_delta
        # Percent Options
        elif mode == "p":
            if len(vals) != 1:
                pg.error = PDT_ERR_BAD1VALS
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return
            vector_delta = getPercent(obj, flip_p, float(vals[0]), oper, scene)
            if vector_delta is None:
                return
            if obj.mode == "EDIT":
                if oper == "C":
                    scene.cursor.location = obj_loc + vector_delta
                else:
                    pg.pivot_loc = obj_loc + vector_delta
            elif obj.mode == "OBJECT":
                if oper == "C":
                    scene.cursor.location = vector_delta
                else:
                    pg.pivot_loc = vector_delta
        return

    # ------------------------
    # Move Vertices or Objects
    elif oper == "G":
        if mode not in adip:
            pg.error = f"'{mode}' {PDT_ERR_NON_VALID} '{oper}'"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
        # Absolute/Global Coordinates
        if mode == "a":
            if len(vals) != 3:
                pg.error = PDT_ERR_BAD3VALS
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return
            vector_delta = Vector((float(vals[0]), float(vals[1]), float(vals[2])))
            if obj.mode == "EDIT":
                verts = [v for v in bm.verts if v.select]
                if len(verts) == 0:
                    pg.error = PDT_ERR_NO_SEL_GEOM
                    context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                    return
                for v in verts:
                    v.co = vector_delta - obj_loc
                bmesh.ops.remove_doubles(
                    bm, verts=[v for v in bm.verts if v.select], dist=0.0001
                )
                bmesh.update_edit_mesh(obj.data)
                bm.select_history.clear()
            elif obj.mode == "OBJECT":
                for ob in context.view_layer.objects.selected:
                    ob.location = vector_delta
        # Delta/Relative Coordinates
        elif mode == "d":
            if len(vals) != 3:
                pg.error = PDT_ERR_BAD3VALS
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return
            vector_delta = Vector((float(vals[0]), float(vals[1]), float(vals[2])))
            if obj.mode == "EDIT":
                # FIXME: Show error popup if nothing is selected?
                bmesh.ops.translate(
                    bm, verts=[v for v in bm.verts if v.select], vec=vector_delta
                )
                bmesh.update_edit_mesh(obj.data)
                bm.select_history.clear()
            elif obj.mode == "OBJECT":
                for ob in context.view_layer.objects.selected:
                    ob.location = obj_loc + vector_delta
        # Direction/Polar Coordinates
        elif mode == "i":
            if len(vals) != 2:
                pg.error = PDT_ERR_BAD2VALS
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return
            vector_delta = disAng(vals, flip_a, plane, scene)
            if obj.mode == "EDIT":
                verts = [v for v in bm.verts if v.select]
                if len(verts) == 0:
                    pg.error = PDT_ERR_NO_SEL_GEOM
                    context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                    return
                bmesh.ops.translate(bm, verts=verts, vec=vector_delta)
                bmesh.update_edit_mesh(obj.data)
                bm.select_history.clear()
            elif obj.mode == "OBJECT":
                for ob in context.view_layer.objects.selected:
                    ob.location = ob.location + vector_delta
        # Percent Options
        elif mode == "p":
            if obj.mode == "OBJECT":
                if len(vals) != 1:
                    pg.error = PDT_ERR_BAD1VALS
                    context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                    return
                vector_delta = getPercent(obj, flip_p, float(vals[0]), oper, scene)
                if vector_delta is None:
                    return
                ob.location = vector_delta
        return

    # --------------
    # Add New Vertex
    elif oper == "N":
        if mode not in adip:
            pg.error = f"'{mode}' {PDT_ERR_NON_VALID} '{oper}'"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
        if not obj.mode == "EDIT":
            pg.error = PDT_ERR_ADDVEDIT
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
        if mode in {"d","i"}:
            if len(bm.select_history) == 0:
                if len(bm.verts) == 0:
                    pg.error = PDT_ERR_NO_SEL_GEOM
                    context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                    return
                else:
                    verts = bm.verts
            else:
                verts = bm.select_history
        # Absolute/Global Coordinates
        if mode == "a":
            if len(vals) != 3:
                pg.error = PDT_ERR_BAD3VALS
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return
            vector_delta = Vector((float(vals[0]), float(vals[1]), float(vals[2])))
            vNew = vector_delta - obj_loc
            nVert = bm.verts.new(vNew)
            for v in [v for v in bm.verts if v.select]:
                v.select_set(False)
            nVert.select_set(True)
            bmesh.update_edit_mesh(obj.data)
            bm.select_history.clear()
        # Delta/Relative Coordinates
        elif mode == "d":
            if len(vals) != 3:
                pg.error = PDT_ERR_BAD3VALS
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return
            vector_delta = Vector((float(vals[0]), float(vals[1]), float(vals[2])))
            vNew = verts[-1].co + vector_delta
            nVert = bm.verts.new(vNew)
            for v in [v for v in bm.verts if v.select]:
                v.select_set(False)
            nVert.select_set(True)
            bmesh.update_edit_mesh(obj.data)
            bm.select_history.clear()
        # Direction/Polar Coordinates
        elif mode == "i":
            if len(vals) != 2:
                pg.error = PDT_ERR_BAD2VALS
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return
            vector_delta = disAng(vals, flip_a, plane, scene)
            vNew = verts[-1].co + vector_delta
            nVert = bm.verts.new(vNew)
            for v in [v for v in bm.verts if v.select]:
                v.select_set(False)
            nVert.select_set(True)
            bmesh.update_edit_mesh(obj.data)
            bm.select_history.clear()
        # Percent Options
        elif mode == "p":
            if len(vals) != 1:
                pg.error = PDT_ERR_BAD1VALS
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return
            vector_delta = getPercent(obj, flip_p, float(vals[0]), oper, scene)
            vNew = vector_delta
            nVert = bm.verts.new(vNew)
            for v in [v for v in bm.verts if v.select]:
                v.select_set(False)
            nVert.select_set(True)
            bmesh.update_edit_mesh(obj.data)
            bm.select_history.clear()
        return

    # -----------
    # Split Edges
    elif oper == "S":
        if mode not in adip:
            pg.error = f"'{mode}' {PDT_ERR_NON_VALID} '{oper}'"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
        if not obj.mode == "EDIT":
            pg.error = PDT_ERR_SPLITEDIT
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
        # Absolute/Global Coordinates
        if mode == "a":
            if len(vals) != 3:
                pg.error = PDT_ERR_BAD3VALS
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return
            vector_delta = Vector((float(vals[0]), float(vals[1]), float(vals[2])))
            edges = [e for e in bm.edges if e.select]
            if len(edges) != 1:
                pg.error = f"{PDT_ERR_SEL_1_EDGE} {len(edges)})"
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return
            geom = bmesh.ops.subdivide_edges(bm, edges=edges, cuts=1)
            new_verts = [v for v in geom["geom_split"] if isinstance(v, bmesh.types.BMVert)]
            nVert = new_verts[0]
            nVert.co = vector_delta - obj_loc
            for v in [v for v in bm.verts if v.select]:
                v.select_set(False)
            nVert.select_set(True)
            bmesh.update_edit_mesh(obj.data)
            bm.select_history.clear()
        # Delta/Relative Coordinates
        elif mode == "d":
            if len(vals) != 3:
                pg.error = PDT_ERR_BAD3VALS
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return
            vector_delta = Vector((float(vals[0]), float(vals[1]), float(vals[2])))
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
            for v in [v for v in bm.verts if v.select]:
                v.select_set(False)
            for v in new_verts:
                v.select_set(False)
            bmesh.ops.translate(bm, verts=new_verts, vec=vector_delta)
            for v in [v for v in bm.verts if v.select]:
                v.select_set(False)
            for v in new_verts:
                v.select_set(False)
            bmesh.update_edit_mesh(obj.data)
            bm.select_history.clear()
        # Directional/Polar Coordinates
        elif mode == "i":
            if len(vals) != 2:
                pg.error = PDT_ERR_BAD2VALS
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return
            vector_delta = disAng(vals, flip_a, plane, scene)
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
            for v in [v for v in bm.verts if v.select]:
                v.select_set(False)
            for v in new_verts:
                v.select_set(False)
            bmesh.update_edit_mesh(obj.data)
            bm.select_history.clear()
        # Percent Options
        elif mode == "p":
            if len(vals) != 1:
                pg.error = PDT_ERR_BAD1VALS
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return
            vector_delta = getPercent(obj, flip_p, float(vals[0]), oper, scene)
            if vector_delta is None:
                return
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
            nVert = new_verts[0]
            nVert.co = vector_delta
            for v in [v for v in bm.verts if v.select]:
                v.select_set(False)
            nVert.select_set(True)
            bmesh.update_edit_mesh(obj.data)
            bm.select_history.clear()
        return

    # ----------------
    # Extrude Vertices
    elif oper == "V":
        if mode not in adip:
            pg.error = f"'{mode}' {PDT_ERR_NON_VALID} '{oper}'"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
        if not obj.mode == "EDIT":
            pg.error = PDT_ERR_EXTEDIT
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
        # Absolute/Global Coordinates
        if mode == "a":
            if len(vals) != 3:
                pg.error = PDT_ERR_BAD3VALS
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return
            vector_delta = Vector((float(vals[0]), float(vals[1]), float(vals[2])))
            vNew = vector_delta - obj_loc
            nVert = bm.verts.new(vNew)
            for v in [v for v in bm.verts if v.select]:
                bm.edges.new([v, nVert])
                v.select_set(False)
            nVert.select_set(True)
            bmesh.ops.remove_doubles(
                bm, verts=[v for v in bm.verts if v.select], dist=0.0001
            )
            bmesh.update_edit_mesh(obj.data)
            bm.select_history.clear()
        # Delta/Relative Coordinates
        elif mode == "d":
            if len(vals) != 3:
                pg.error = PDT_ERR_BAD3VALS
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return
            vector_delta = Vector((float(vals[0]), float(vals[1]), float(vals[2])))
            verts = [v for v in bm.verts if v.select]
            if len(verts) == 0:
                pg.error = PDT_ERR_NO_SEL_GEOM
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return
            for v in verts:
                nVert = bm.verts.new(v.co)
                nVert.co = nVert.co + vector_delta
                bm.edges.new([v, nVert])
                v.select_set(False)
                nVert.select_set(True)
            bmesh.update_edit_mesh(obj.data)
            bm.select_history.clear()
        # Direction/Polar Coordinates
        elif mode == "i":
            if len(vals) != 2:
                pg.error = PDT_ERR_BAD2VALS
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return
            vector_delta = disAng(vals, flip_a, plane, scene)
            verts = [v for v in bm.verts if v.select]
            if len(verts) == 0:
                pg.error = PDT_ERR_NO_SEL_GEOM
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return
            for v in verts:
                nVert = bm.verts.new(v.co)
                nVert.co = nVert.co + vector_delta
                bm.edges.new([v, nVert])
                v.select_set(False)
                nVert.select_set(True)
            bmesh.update_edit_mesh(obj.data)
            bm.select_history.clear()
        # Percent Options
        elif mode == "p":
            vector_delta = getPercent(obj, flip_p, float(vals[0]), oper, scene)
            verts = [v for v in bm.verts if v.select].copy()
            if len(verts) == 0:
                pg.error = PDT_ERR_NO_SEL_GEOM
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return
            nVert = bm.verts.new(vector_delta)
            if ext_a:
                for v in [v for v in bm.verts if v.select]:
                    bm.edges.new([v, nVert])
                    v.select_set(False)
            else:
                bm.edges.new([verts[-1], nVert])
            nVert.select_set(True)
            bmesh.update_edit_mesh(obj.data)
            bm.select_history.clear()
        return

    # ----------------
    # Extrude Geometry
    elif oper == "E":
        if mode not in {"d", "i"}:
            pg.error = f"'{mode}' {PDT_ERR_NON_VALID} '{oper}'"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
        if not obj.mode == "EDIT":
            pg.error = PDT_ERR_EXTEDIT
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
        # Delta/Relative Coordinates
        if mode == "d":
            if len(vals) != 3:
                pg.error = PDT_ERR_BAD3VALS
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return
            vector_delta = Vector((float(vals[0]), float(vals[1]), float(vals[2])))
            verts = [v for v in bm.verts if v.select]
            if len(verts) == 0:
                pg.error = PDT_ERR_NO_SEL_GEOM
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return
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
            bmesh.ops.translate(bm, verts=verts_extr, vec=vector_delta)
            updateSel(bm, verts_extr, edges_extr, faces_extr)
            bmesh.update_edit_mesh(obj.data)
            bm.select_history.clear()
        # Direction/Polar Coordinates
        elif mode == "i":
            if len(vals) != 2:
                pg.error = PDT_ERR_BAD2VALS
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return
            vector_delta = disAng(vals, flip_a, plane, scene)
            verts = [v for v in bm.verts if v.select]
            if len(verts) == 0:
                pg.error = PDT_ERR_NO_SEL_GEOM
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return
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
            bmesh.ops.translate(bm, verts=verts_extr, vec=vector_delta)
            updateSel(bm, verts_extr, edges_extr, faces_extr)
            bmesh.update_edit_mesh(obj.data)
            bm.select_history.clear()
        return

    # ------------------
    # Duplicate Geometry
    elif oper == "D":
        if mode not in {"d", "i"}:
            pg.error = f"'{mode}' {PDT_ERR_NON_VALID} '{oper}'"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
        if not obj.mode == "EDIT":
            pg.error = PDT_ERR_DUPEDIT
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
        # Delta/Relative Coordinates
        if mode == "d":
            if len(vals) != 3:
                pg.error = PDT_ERR_BAD3VALS
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return
            vector_delta = Vector((float(vals[0]), float(vals[1]), float(vals[2])))
            verts = [v for v in bm.verts if v.select]
            if len(verts) == 0:
                pg.error = PDT_ERR_NO_SEL_GEOM
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return
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
            bmesh.ops.translate(bm, verts=verts_dupe, vec=vector_delta)
            updateSel(bm, verts_dupe, edges_dupe, faces_dupe)
            bmesh.update_edit_mesh(obj.data)
            bm.select_history.clear()
        # Direction/Polar Coordinates
        elif mode == "i":
            if len(vals) != 2:
                pg.error = PDT_ERR_BAD2VALS
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return
            vector_delta = disAng(vals, flip_a, plane, scene)
            verts = [v for v in bm.verts if v.select]
            if len(verts) == 0:
                pg.error = PDT_ERR_NO_SEL_GEOM
                context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return
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
            bmesh.ops.translate(bm, verts=verts_dupe, vec=vector_delta)
            updateSel(bm, verts_dupe, edges_dupe, faces_dupe)
            bmesh.update_edit_mesh(obj.data)
            bm.select_history.clear()
        return

    # ---------------
    # Fillet Geometry
    elif oper == "F":
        if mode not in {"v", "e", "i"}:
            pg.error = f"'{mode}' {PDT_ERR_NON_VALID} '{oper}'"
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
        if obj is None:
            pg.error = PDT_ERR_NO_ACT_OBJ
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
        if not obj.mode == "EDIT":
            pg.error = PDT_ERR_FILEDIT
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
        if len(vals) != 3:
            pg.error = PDT_ERR_BAD3VALS
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
        if mode in {"i", "v"}:
            vert_bool = True
        elif mode == "e":
            vert_bool = False
        verts = [v for v in bm.verts if v.select]
        if len(verts) == 0:
            pg.error = PDT_ERR_SEL_1_VERT
            context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
        # Note that passing an empty parameter results in that parameter being seen as "0"
        # _offset <= 0 is ignored since a bevel/fillet radius must be > 0 to make sense
        _offset = float(vals[0])
        _segments = int(vals[1])
        if _segments < 1:
            _segments = 1   # This is a single, flat segment (ignores profile)
        _profile = float(vals[2])
        if _profile < 0.0 or _profile > 1.0:
            _profile = 0.5  # This is a circular profile
        if mode == "i":
            # Fillet & Intersect Two Edges
            edges = [e for e in bm.edges if e.select]
            if len(edges) == 2 and len(verts) == 4:
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
                    errmsg = f"{PDT_ERR_INT_LINES} {plane}  {PDT_LAB_PLANE}"
                    self.report({"ERROR"}, errmsg)
                    return {"FINISHED"}
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
        bpy.ops.mesh.bevel(
            offset_type="OFFSET",
            offset=_offset,
            segments=_segments,
            profile=_profile,
            vertex_only=vert_bool
        )
        return
