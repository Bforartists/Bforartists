# SPDX-FileCopyrightText: 2019-2022 Alan Odom (Clockmender)
# SPDX-FileCopyrightText: 2019-2022 Rune Morling (ermo)
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
import bmesh
from bpy.types import Operator, SpaceView3D
from mathutils import Vector, Matrix
from math import pi
from .pdt_functions import view_coords, draw_callback_3d
from .pdt_msg_strings import (
    PDT_CON_AREYOURSURE,
    PDT_ERR_EDIT_MODE,
    PDT_ERR_NO3DVIEW,
    PDT_ERR_NOPPLOC,
    PDT_ERR_NO_ACT_OBJ,
    PDT_ERR_NO_SEL_GEOM
)


class PDT_OT_ModalDrawOperator(bpy.types.Operator):
    """Show/Hide Pivot Point"""

    bl_idname = "pdt.modaldraw"
    bl_label = "PDT Modal Draw"
    bl_options = {"REGISTER", "UNDO"}

    _handle = None  # keep function handler

    @staticmethod
    def handle_add(self, context):
        """Draw Pivot Point Graphic if not displayed.

        Note:
            Draws 7 element Pivot Point Graphic

        Args:
            context: Blender bpy.context instance.

        Returns:
            Nothing.
        """

        if PDT_OT_ModalDrawOperator._handle is None:
            PDT_OT_ModalDrawOperator._handle = SpaceView3D.draw_handler_add(
                draw_callback_3d, (self, context), "WINDOW", "POST_VIEW"
            )
            context.window_manager.pdt_run_opengl = True

    @staticmethod
    def handle_remove(self, context):
        """Remove Pivot Point Graphic if displayed.

        Note:
            Removes 7 element Pivot Point Graphic

        Args:
            context: Blender bpy.context instance.

        Returns:
            Nothing.
        """

        if PDT_OT_ModalDrawOperator._handle is not None:
            SpaceView3D.draw_handler_remove(PDT_OT_ModalDrawOperator._handle, "WINDOW")
        PDT_OT_ModalDrawOperator._handle = None
        context.window_manager.pdt_run_opengl = False

    def execute(self, context):
        """Pivot Point Show/Hide Button Function.

        Note:
            Operational execute function for Show/Hide Pivot Point function

        Args:
            context: Blender bpy.context instance.

        Returns:
            Status Set.
        """

        if context.area.type == "VIEW_3D":
            if context.window_manager.pdt_run_opengl is False:
                self.handle_add(self, context)
                context.area.tag_redraw()
            else:
                self.handle_remove(self, context)
                context.area.tag_redraw()

            return {"FINISHED"}

        self.report({"ERROR"}, PDT_ERR_NO3DVIEW)
        return {"CANCELLED"}


class PDT_OT_ViewPlaneRotate(Operator):
    """Rotate Selected Vertices about Pivot Point in View Plane"""

    bl_idname = "pdt.viewplanerot"
    bl_label = "PDT View Rotate"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """Check Object Status.

        Args:
            context: Blender bpy.context instance.

        Returns:
            Nothing.
        """

        obj = context.object
        if obj is None:
            return False
        return all([bool(obj), obj.type == "MESH", obj.mode == "EDIT"])


    def execute(self, context):
        """Rotate Selected Vertices about Pivot Point.

        Note:
            Rotates any selected vertices about the Pivot Point
            in View Oriented coordinates, works in any view orientation.

        Args:
            context: Blender bpy.context instance.

        Note:
            Uses pg.pivot_loc, pg.pivot_ang scene variables

        Returns:
            Status Set.
        """

        scene = context.scene
        pg = scene.pdt_pg
        obj = bpy.context.view_layer.objects.active
        if obj is None:
            self.report({"ERROR"}, PDT_ERR_NO_ACT_OBJ)
            return {"FINISHED"}
        if obj.mode != "EDIT":
            error_message = f"{PDT_ERR_EDIT_MODE} {obj.mode})"
            self.report({"ERROR"}, error_message)
            return {"FINISHED"}
        bm = bmesh.from_edit_mesh(obj.data)
        v1 = Vector((0, 0, 0))
        v2 = view_coords(0, 0, 1)
        axis = (v2 - v1).normalized()
        rot = Matrix.Rotation((pg.pivot_ang * pi / 180), 4, axis)
        verts = verts = [v for v in bm.verts if v.select]
        bmesh.ops.rotate(
            bm, cent=pg.pivot_loc - obj.matrix_world.decompose()[0], matrix=rot, verts=verts
        )
        bmesh.update_edit_mesh(obj.data)
        return {"FINISHED"}


class PDT_OT_ViewPlaneScale(Operator):
    """Scale Selected Vertices about Pivot Point"""

    bl_idname = "pdt.viewscale"
    bl_label = "PDT View Scale"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """Check Object Status.

        Args:
            context: Blender bpy.context instance.

        Returns:
            Nothing.
        """

        obj = context.object
        if obj is None:
            return False
        return all([bool(obj), obj.type == "MESH", obj.mode == "EDIT"])


    def execute(self, context):
        """Scales Selected Vertices about Pivot Point.

        Note:
            Scales any selected vertices about the Pivot Point
            in View Oriented coordinates, works in any view orientation

        Args:
            context: Blender bpy.context instance.

        Note:
            Uses pg.pivot_loc, pg.pivot_scale scene variables

        Returns:
            Status Set.
        """

        scene = context.scene
        pg = scene.pdt_pg
        obj = bpy.context.view_layer.objects.active
        if obj is None:
            self.report({"ERROR"}, PDT_ERR_NO_ACT_OBJ)
            return {"FINISHED"}
        if obj.mode != "EDIT":
            error_message = f"{PDT_ERR_EDIT_MODE} {obj.mode})"
            self.report({"ERROR"}, error_message)
            return {"FINISHED"}
        bm = bmesh.from_edit_mesh(obj.data)
        verts = verts = [v for v in bm.verts if v.select]
        for v in verts:
            delta_x = (pg.pivot_loc.x - obj.matrix_world.decompose()[0].x - v.co.x) * (
                1 - pg.pivot_scale.x
            )
            delta_y = (pg.pivot_loc.y - obj.matrix_world.decompose()[0].y - v.co.y) * (
                1 - pg.pivot_scale.y
            )
            delta_z = (pg.pivot_loc.z - obj.matrix_world.decompose()[0].z - v.co.z) * (
                1 - pg.pivot_scale.z
            )
            delta_v = Vector((delta_x, delta_y, delta_z))
            v.co = v.co + delta_v
        bmesh.update_edit_mesh(obj.data)
        return {"FINISHED"}


class PDT_OT_PivotToCursor(Operator):
    """Set The Pivot Point to Cursor Location"""

    bl_idname = "pdt.pivotcursor"
    bl_label = "PDT Pivot To Cursor"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """Moves Pivot Point to Cursor Location.

        Note:
            Moves Pivot Point to Cursor Location in active scene

        Args:
            context: Blender bpy.context instance.

        Returns:
             Status Set.
        """

        scene = context.scene
        pg = scene.pdt_pg
        old_cursor_loc = scene.cursor.location.copy()
        pg.pivot_loc = scene.cursor.location
        scene.cursor.location = old_cursor_loc
        return {"FINISHED"}


class PDT_OT_CursorToPivot(Operator):
    """Set The Cursor Location to Pivot Point"""

    bl_idname = "pdt.cursorpivot"
    bl_label = "PDT Cursor To Pivot"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """Moves Cursor to Pivot Point Location.

        Note:
            Moves Cursor to Pivot Point Location in active scene

        Args:
            context: Blender bpy.context instance.

        Returns:
            Status Set.
        """

        scene = context.scene
        pg = scene.pdt_pg
        scene.cursor.location = pg.pivot_loc
        return {"FINISHED"}


class PDT_OT_PivotSelected(Operator):
    """Set Pivot Point to Selected Geometry"""

    bl_idname = "pdt.pivotselected"
    bl_label = "PDT Pivot to Selected"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """Check Object Status.

        Args:
            context: Blender bpy.context instance.

        Returns:
            Nothing.
        """

        obj = context.object
        if obj is None:
            return False
        return all([bool(obj), obj.type == "MESH", obj.mode == "EDIT"])


    def execute(self, context):
        """Moves Pivot Point centroid of Selected Geometry.

        Note:
            Moves Pivot Point centroid of Selected Geometry in active scene
            using Snap_Cursor_To_Selected, then puts cursor back to original location.

        Args:
            context: Blender bpy.context instance.

        Returns:
            Status Set.
        """

        scene = context.scene
        pg = scene.pdt_pg
        obj = bpy.context.view_layer.objects.active
        if obj is None:
            self.report({"ERROR"}, PDT_ERR_NO_ACT_OBJ)
            return {"FINISHED"}
        if obj.mode != "EDIT":
            error_message = f"{PDT_ERR_EDIT_MODE} {obj.mode})"
            self.report({"ERROR"}, error_message)
            return {"FINISHED"}
        bm = bmesh.from_edit_mesh(obj.data)
        verts = verts = [v for v in bm.verts if v.select]
        if len(verts) > 0:
            old_cursor_loc = scene.cursor.location.copy()
            bpy.ops.view3d.snap_cursor_to_selected()
            pg.pivot_loc = scene.cursor.location
            scene.cursor.location = old_cursor_loc
            return {"FINISHED"}

        self.report({"ERROR"}, PDT_ERR_NO_SEL_GEOM)
        return {"FINISHED"}


class PDT_OT_PivotOrigin(Operator):
    """Set Pivot Point at Object Origin"""

    bl_idname = "pdt.pivotorigin"
    bl_label = "PDT Pivot to Object Origin"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """Check Object Status.

        Args:
            context: Blender bpy.context instance.

        Returns:
            Nothing.
        """

        obj = context.object
        if obj is None:
            return False
        return all([bool(obj), obj.type == "MESH"])

    def execute(self, context):
        """Moves Pivot Point to Object Origin.

        Note:
            Moves Pivot Point to Object Origin in active scene

        Args:
            context: Blender bpy.context instance.

        Returns:
            Status Set.
        """

        scene = context.scene
        pg = scene.pdt_pg
        obj = bpy.context.view_layer.objects.active
        if obj is None:
            self.report({"ERROR"}, PDT_ERR_NO_ACT_OBJ)
            return {"FINISHED"}
        old_cursor_loc = scene.cursor.location.copy()
        obj_loc = obj.matrix_world.decompose()[0]
        pg.pivot_loc = obj_loc
        scene.cursor.location = old_cursor_loc
        return {"FINISHED"}


class PDT_OT_PivotWrite(Operator):
    """Write Pivot Point Location to Object"""

    bl_idname = "pdt.pivotwrite"
    bl_label = "PDT Write PP to Object?"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """Check Object Status.

        Args:
            context: Blender bpy.context instance.

        Returns:
            Nothing.
        """

        obj = context.object
        if obj is None:
            return False
        return all([bool(obj), obj.type == "MESH"])

    def execute(self, context):
        """Writes Pivot Point Location to Object's Custom Properties.

        Note:
            Writes Pivot Point Location to Object's Custom Properties
            as Vector to 'PDT_PP_LOC' - Requires Confirmation through dialogue

        Args:
            context: Blender bpy.context instance.

        Note:
            Uses pg.pivot_loc scene variable

        Returns:
            Status Set.
        """

        scene = context.scene
        pg = scene.pdt_pg
        obj = bpy.context.view_layer.objects.active
        if obj is None:
            self.report({"ERROR"}, PDT_ERR_NO_ACT_OBJ)
            return {"FINISHED"}
        obj["PDT_PP_LOC"] = pg.pivot_loc
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        row = self.layout
        row.label(text=PDT_CON_AREYOURSURE)


class PDT_OT_PivotRead(Operator):
    """Read Pivot Point Location from Object"""

    bl_idname = "pdt.pivotread"
    bl_label = "PDT Read PP"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """Check Object Status.

        Args:
            context: Blender bpy.context instance.

        Returns:
            Nothing.
        """

        obj = context.object
        if obj is None:
            return False
        return all([bool(obj), obj.type == "MESH"])

    def execute(self, context):
        """Reads Pivot Point Location from Object's Custom Properties.

        Note:
            Sets Pivot Point Location from Object's Custom Properties
            using 'PDT_PP_LOC'

        Args:
            context: Blender bpy.context instance.

        Note:
            Uses pg.pivot_loc scene variable

        Returns:
            Status Set.
        """

        scene = context.scene
        pg = scene.pdt_pg
        obj = bpy.context.view_layer.objects.active
        if obj is None:
            self.report({"ERROR"}, PDT_ERR_NO_ACT_OBJ)
            return {"FINISHED"}
        if "PDT_PP_LOC" in obj:
            pg.pivot_loc = obj["PDT_PP_LOC"]
            return {"FINISHED"}

        self.report({"ERROR"}, PDT_ERR_NOPPLOC)
        return {"FINISHED"}
