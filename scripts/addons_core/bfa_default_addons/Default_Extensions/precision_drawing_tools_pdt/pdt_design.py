# SPDX-FileCopyrightText: 2019-2022 Alan Odom (Clockmender)
# SPDX-FileCopyrightText: 2019-2022 Rune Morling (ermo)
#
# SPDX-License-Identifier: GPL-2.0-or-later

from bpy.types import Operator
from .pdt_msg_strings import (
    PDT_ERR_NON_VALID,
    PDT_LAB_ABS,
    PDT_LAB_DEL,
    PDT_LAB_DIR,
    PDT_LAB_INTERSECT,
    PDT_LAB_PERCENT,
)


class PDT_OT_PlacementAbs(Operator):
    """Use Absolute, or Global Placement"""

    bl_idname = "pdt.absolute"
    bl_label = "Absolute Mode"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """Manipulates Geometry, or Objects by Absolute (World) Coordinates.

        Note:
            - Reads pg.operate from Operation Mode Selector as 'operation'
            - Reads pg.cartesian_coords scene variables to:
            -- set position of Cursor      (CU)
            -- set position of Pivot Point (PP)
            -- MoVe geometry/objects       (MV)
            -- Extrude Vertices            (EV)
            -- Split Edges                 (SE)
            -- add a New Vertex            (NV)

            Invalid Options result in self.report Error.

        Args:
            context: Blender bpy.context instance.

        Returns:
            Status Set.
        """

        pg = context.scene.pdt_pg
        operation = pg.operation
        decimal_places = context.preferences.addons[__package__].preferences.pdt_input_round

        if operation == "CU":
            # Cursor
            pg.command = (
                f"ca{str(round(pg.cartesian_coords.x, decimal_places))}"
                f",{str(round(pg.cartesian_coords.y, decimal_places))}"
                f",{str(round(pg.cartesian_coords.z, decimal_places))}"
            )
        elif operation == "PP":
            # Pivot Point
            pg.command = (
                f"pa{str(round(pg.cartesian_coords.x, decimal_places))}"
                f",{str(round(pg.cartesian_coords.y, decimal_places))}"
                f",{str(round(pg.cartesian_coords.z, decimal_places))}"
            )
        elif operation == "MV":
            # Move Entities
            pg.command = (
                f"ga{str(round(pg.cartesian_coords.x, decimal_places))}"
                f",{str(round(pg.cartesian_coords.y, decimal_places))}"
                f",{str(round(pg.cartesian_coords.z, decimal_places))}"
            )
        elif operation == "SE":
            # Split Edges
            pg.command = (
                f"sa{str(round(pg.cartesian_coords.x, decimal_places))}"
                f",{str(round(pg.cartesian_coords.y, decimal_places))}"
                f",{str(round(pg.cartesian_coords.z, decimal_places))}"
            )
        elif operation == "NV":
            # New Vertex
            pg.command = (
                f"na{str(round(pg.cartesian_coords.x, decimal_places))}"
                f",{str(round(pg.cartesian_coords.y, decimal_places))}"
                f",{str(round(pg.cartesian_coords.z, decimal_places))}"
            )
        elif operation == "EV":
            # Extrude Vertices
            pg.command = (
                f"va{str(round(pg.cartesian_coords.x, decimal_places))}"
                f",{str(round(pg.cartesian_coords.y, decimal_places))}"
                f",{str(round(pg.cartesian_coords.z, decimal_places))}"
            )
        else:
            error_message = f"{operation} {PDT_ERR_NON_VALID} {PDT_LAB_ABS}"
            self.report({"ERROR"}, error_message)
        return {"FINISHED"}


class PDT_OT_PlacementDelta(Operator):
    """Use Delta, or Incremental Placement"""

    bl_idname = "pdt.delta"
    bl_label = "Delta Mode"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """Manipulates Geometry, or Objects by Delta Offset (Increment).

        Note:
            - Reads pg.operation from Operation Mode Selector as 'operation'
            - Reads pg.select, pg.plane, pg.cartesian_coords scene variables to:
            -- set position of CUrsor       (CU)
            -- set position of Pivot Point  (PP)
            -- MoVe geometry/objects        (MV)
            -- Extrude Vertices             (EV)
            -- Split Edges                  (SE)
            -- add a New Vertex             (NV)
            -- Duplicate Geometry           (DG)
            -- Extrude Geometry             (EG)

            Invalid Options result in self.report Error.

        Args:
            context: Blender bpy.context instance.

        Returns:
            Status Set.
        """

        pg = context.scene.pdt_pg
        operation = pg.operation
        decimal_places = context.preferences.addons[__package__].preferences.pdt_input_round

        if operation == "CU":
            # Cursor
            pg.command = (
                f"cd{str(round(pg.cartesian_coords.x, decimal_places))}"
                f",{str(round(pg.cartesian_coords.y, decimal_places))}"
                f",{str(round(pg.cartesian_coords.z, decimal_places))}"
            )
        elif operation == "PP":
            # Pivot Point
            pg.command = (
                f"pd{str(round(pg.cartesian_coords.x, decimal_places))}"
                f",{str(round(pg.cartesian_coords.y, decimal_places))}"
                f",{str(round(pg.cartesian_coords.z, decimal_places))}"
            )
        elif operation == "MV":
            # Move Entities
            pg.command = (
                f"gd{str(round(pg.cartesian_coords.x, decimal_places))}"
                f",{str(round(pg.cartesian_coords.y, decimal_places))}"
                f",{str(round(pg.cartesian_coords.z, decimal_places))}"
            )
        elif operation == "SE":
            # Split Edges
            pg.command = (
                f"sd{str(round(pg.cartesian_coords.x, decimal_places))}"
                f",{str(round(pg.cartesian_coords.y, decimal_places))}"
                f",{str(round(pg.cartesian_coords.z, decimal_places))}"
            )
        elif operation == "NV":
            # New Vertex
            pg.command = (
                f"nd{str(round(pg.cartesian_coords.x, decimal_places))}"
                f",{str(round(pg.cartesian_coords.y, decimal_places))}"
                f",{str(round(pg.cartesian_coords.z, decimal_places))}"
            )
        elif operation == "EV":
            # Extrude Vertices
            pg.command = (
                f"vd{str(round(pg.cartesian_coords.x, decimal_places))}"
                f",{str(round(pg.cartesian_coords.y, decimal_places))}"
                f",{str(round(pg.cartesian_coords.z, decimal_places))}"
            )
        elif operation == "DG":
            # Duplicate Entities
            pg.command = (
                f"dd{str(round(pg.cartesian_coords.x, decimal_places))}"
                f",{str(round(pg.cartesian_coords.y, decimal_places))}"
                f",{str(round(pg.cartesian_coords.z, decimal_places))}"
            )
        elif operation == "EG":
            # Extrude Geometry
            pg.command = (
                f"ed{str(round(pg.cartesian_coords.x, decimal_places))}"
                f",{str(round(pg.cartesian_coords.y, decimal_places))}"
                f",{str(round(pg.cartesian_coords.z, decimal_places))}"
            )
        else:
            error_message = f"{operation} {PDT_ERR_NON_VALID} {PDT_LAB_DEL}"
            self.report({"ERROR"}, error_message)
        return {"FINISHED"}


class PDT_OT_PlacementDis(Operator):
    """Use Directional, or Distance @ Angle Placement"""

    bl_idname = "pdt.distance"
    bl_label = "Distance@Angle Mode"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """Manipulates Geometry, or Objects by Distance at Angle (Direction).

        Note:
            - Reads pg.operation from Operation Mode Selector as 'operation'
            - Reads pg.select, pg.distance, pg.angle, pg.plane & pg.flip_angle scene variables to:
            -- set position of CUrsor       (CU)
            -- set position of Pivot Point  (PP)
            -- MoVe geometry/objects        (MV)
            -- Extrude Vertices             (EV)
            -- Split Edges                  (SE)
            -- add a New Vertex             (NV)
            -- Duplicate Geometry           (DG)
            -- Extrude Geometry             (EG)

            Invalid Options result in self.report Error.

        Args:
            context: Blender bpy.context instance.

        Returns:
            Status Set.
        """

        pg = context.scene.pdt_pg
        operation = pg.operation
        decimal_places = context.preferences.addons[__package__].preferences.pdt_input_round

        if operation == "CU":
            # Cursor
            pg.command = (
                f"ci{str(round(pg.distance, decimal_places))}"
                f",{str(round(pg.angle, decimal_places))}"
            )
        elif operation == "PP":
            # Pivot Point
            pg.command = (
                f"pi{str(round(pg.distance, decimal_places))}"
                f",{str(round(pg.angle, decimal_places))}"
            )
        elif operation == "MV":
            # Move Entities
            pg.command = (
                f"gi{str(round(pg.distance, decimal_places))}"
                f",{str(round(pg.angle, decimal_places))}"
            )
        elif operation == "SE":
            # Split Edges
            pg.command = (
                f"si{str(round(pg.distance, decimal_places))}"
                f",{str(round(pg.angle, decimal_places))}"
                )
        elif operation == "NV":
            # New Vertex
            pg.command = (
                f"ni{str(round(pg.distance, decimal_places))}"
                f",{str(round(pg.angle, decimal_places))}"
            )
        elif operation == "EV":
            # Extrude Vertices
            pg.command = (
                f"vi{str(round(pg.distance, decimal_places))}"
                f",{str(round(pg.angle, decimal_places))}"
            )
        elif operation == "DG":
            # Duplicate Geometry
            pg.command = (
                f"di{str(round(pg.distance, decimal_places))}"
                f",{str(round(pg.angle, decimal_places))}"
            )
        elif operation == "EG":
            # Extrude Geometry
            pg.command = (
                f"ei{str(round(pg.distance, decimal_places))}"
                f",{str(round(pg.angle, decimal_places))}"
            )
        else:
            error_message = f"{operation} {PDT_ERR_NON_VALID} {PDT_LAB_DIR}"
            self.report({"ERROR"}, error_message)
        return {"FINISHED"}


class PDT_OT_PlacementView(Operator):
    """Use Distance Input for View Normal Axis Operations"""

    bl_idname = "pdt.view_axis"
    bl_label = "View Normal Axis Mode"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """Manipulates Geometry, or Objects by View Normal Axis Offset (Increment).

        Note:
            - Reads pg.operation from Operation Mode Selector as 'operation'
            - Reads pg.select, pg.plane, pg.cartesian_coords scene variables to:
            -- set position of CUrsor       (CU)
            -- set position of Pivot Point  (PP)
            -- MoVe geometry/objects        (MV)
            -- Extrude Vertices             (EV)
            -- Split Edges                  (SE)
            -- add a New Vertex             (NV)
            -- Duplicate Geometry           (DG)
            -- Extrude Geometry             (EG)

            Invalid Options result in self.report Error.

        Args:
            context: Blender bpy.context instance.

        Returns:
            Status Set.
        """

        pg = context.scene.pdt_pg
        operation = pg.operation
        decimal_places = context.preferences.addons[__package__].preferences.pdt_input_round

        if operation == "CU":
            # Cursor
            pg.command = (
                f"cn{str(round(pg.distance, decimal_places))}"
            )
        elif operation == "PP":
            # Pivot Point
            pg.command = (
                f"pn{str(round(pg.distance, decimal_places))}"
            )
        elif operation == "MV":
            # Move Entities
            pg.command = (
                f"gn{str(round(pg.distance, decimal_places))}"
            )
        elif operation == "NV":
            # New Vertex
            pg.command = (
                f"nn{str(round(pg.distance, decimal_places))}"
            )
        elif operation == "EV":
            # Extrude Vertices
            pg.command = (
                f"vn{str(round(pg.distance, decimal_places))}"
            )
        elif operation == "DG":
            # Duplicate Entities
            pg.command = (
                f"dn{str(round(pg.distance, decimal_places))}"
            )
        elif operation == "EG":
            # Extrude Geometry
            pg.command = (
                f"en{str(round(pg.distance, decimal_places))}"
            )
        else:
            error_message = f"{operation} {PDT_ERR_NON_VALID} {PDT_LAB_DEL}"
            self.report({"ERROR"}, error_message)
        return {"FINISHED"}


class PDT_OT_PlacementPer(Operator):
    """Use Percentage Placement"""

    bl_idname = "pdt.percent"
    bl_label = "Percentage Mode"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """Manipulates Geometry, or Objects by Percentage between 2 points.

        Note:
            - Reads pg.operation from Operation Mode Selector as 'operation'
            - Reads pg.percent, pg.extend & pg.flip_percent scene variables to:
            -- set position of CUrsor       (CU)
            -- set position of Pivot Point  (PP)
            -- MoVe geometry/objects        (MV)
            -- Extrude Vertices             (EV)
            -- Split Edges                  (SE)
            -- add a New Vertex             (NV)

            Invalid Options result in self.report Error.

        Args:
            context: Blender bpy.context instance.

        Returns:
            Status Set.
        """

        pg = context.scene.pdt_pg
        operation = pg.operation
        decimal_places = context.preferences.addons[__package__].preferences.pdt_input_round

        if operation == "CU":
            # Cursor
            pg.command = f"cp{str(round(pg.percent, decimal_places))}"
        elif operation == "PP":
            # Pivot Point
            pg.command = f"pp{str(round(pg.percent, decimal_places))}"
        elif operation == "MV":
            # Move Entities
            pg.command = f"gp{str(round(pg.percent, decimal_places))}"
        elif operation == "SE":
            # Split Edges
            pg.command = f"sp{str(round(pg.percent, decimal_places))}"
        elif operation == "NV":
            # New Vertex
            pg.command = f"np{str(round(pg.percent, decimal_places))}"
        elif operation == "EV":
            # Extrude Vertices
            pg.command = f"vp{str(round(pg.percent, decimal_places))}"
        else:
            error_message = f"{operation} {PDT_ERR_NON_VALID} {PDT_LAB_PERCENT}"
            self.report({"ERROR"}, error_message)
        return {"FINISHED"}


class PDT_OT_PlacementNormal(Operator):
    """Use Normal, or Perpendicular Placement"""

    bl_idname = "pdt.normal"
    bl_label = "Normal Mode"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """Manipulates Geometry, or Objects by Normal Intersection between 3 points.

        Note:
            - Reads pg.operation from Operation Mode Selector as 'operation'
            - Reads pg.extend scene variable to:
            -- set position of CUrsor       (CU)
            -- set position of Pivot Point  (PP)
            -- MoVe geometry/objects        (MV)
            -- Extrude Vertices             (EV)
            -- Split Edges                  (SE)
            -- add a New Vertex             (NV)

            Invalid Options result in self.report Error.

        Args:
            context: Blender bpy.context instance.

        Returns:
            Status Set.
        """

        pg = context.scene.pdt_pg
        operation = pg.operation
        if operation == "CU":
            pg.command = f"cnml"
        elif operation == "PP":
            pg.command = f"pnml"
        elif operation == "MV":
            pg.command = f"gnml"
        elif operation == "EV":
            pg.command = f"vnml"
        elif operation == "SE":
            pg.command = f"snml"
        elif operation == "NV":
            pg.command = f"nnml"
        else:
            error_message = f"{operation} {PDT_ERR_NON_VALID} {PDT_LAB_INTERSECT}"
            self.report({"ERROR"}, error_message)
        return {"FINISHED"}


class PDT_OT_PlacementCen(Operator):
    """Use Placement at Arc Centre"""

    bl_idname = "pdt.centre"
    bl_label = "Centre Mode"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """Manipulates Geometry, or Objects to an Arc Centre defined by 3 points on an Imaginary Arc.

        Note:
            - Reads pg.operation from Operation Mode Selector as 'operation'
            -- set position of CUrsor       (CU)
            -- set position of Pivot Point  (PP)
            -- MoVe geometry/objects        (MV)
            -- Extrude Vertices             (EV)
            -- add a New vertex             (NV)

            Invalid Options result in self.report Error.

        Args:
            context: Blender bpy.context instance.

        Returns:
            Status Set.
        """

        pg = context.scene.pdt_pg
        operation = pg.operation
        if operation == "CU":
            pg.command = f"ccen"
        elif operation == "PP":
            pg.command = f"pcen"
        elif operation == "MV":
            pg.command = f"gcen"
        elif operation == "EV":
            pg.command = f"vcen"
        elif operation == "NV":
            pg.command = f"ncen"
        else:
            error_message = f"{operation} {PDT_ERR_NON_VALID} {PDT_LAB_INTERSECT}"
            self.report({"ERROR"}, error_message)
        return {"FINISHED"}


class PDT_OT_PlacementInt(Operator):
    """Use Intersection, or Convergence Placement"""

    bl_idname = "pdt.intersect"
    bl_label = "Intersect Mode"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """Manipulates Geometry, or Objects by Convergence Intersection between 4 points, or 2 Edges.

        Note:
            - Reads pg.operation from Operation Mode Selector as 'operation'
            - Reads pg.plane scene variable and operates in Working Plane to:
            -- set position of CUrsor       (CU)
            -- set position of Pivot Point  (PP)
            -- MoVe geometry/objects        (MV)
            -- Extrude Vertices             (EV)
            -- add a New vertex             (NV)

            Invalid Options result in "self.report" Error.

        Args:
            context: Blender bpy.context instance.

        Returns:
            Status Set.
        """

        pg = context.scene.pdt_pg
        operation = pg.operation
        if operation == "CU":
            pg.command = f"cint"
        elif operation == "PP":
            pg.command = f"pint"
        elif operation == "MV":
            pg.command = f"gint"
        elif operation == "EV":
            pg.command = f"vint"
        elif operation == "NV":
            pg.command = f"nint"
        else:
            error_message = f"{operation} {PDT_ERR_NON_VALID} {PDT_LAB_INTERSECT}"
            self.report({"ERROR"}, error_message)
        return {"FINISHED"}


class PDT_OT_JoinVerts(Operator):
    """Join 2 Free Vertices into an Edge"""

    bl_idname = "pdt.join"
    bl_label = "Join 2 Vertices"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        ob = context.object
        if ob is None:
            return False
        return all([bool(ob), ob.type == "MESH", ob.mode == "EDIT"])

    def execute(self, context):
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

        pg = context.scene.pdt_pg
        pg.command = f"j2v"
        return {"FINISHED"}


class PDT_OT_Fillet(Operator):
    """Fillet Edges by Vertex, Set Use Verts to False for Extruded Structure"""

    bl_idname = "pdt.fillet"
    bl_label = "Fillet"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        ob = context.object
        if ob is None:
            return False
        return all([bool(ob), ob.type == "MESH", ob.mode == "EDIT"])

    def execute(self, context):
        """Create Fillets by Vertex or by Geometry.

        Note:
            Fillets connected edges, or connected faces
        Uses:
            - pg.fillet_radius  ; Radius of fillet
            - pg.fillet_segments  ; Number of segments
            - pg.fillet_profile  ; Profile, values 0 to 1
            - pg.fillet_vertices_only ; Vertices (True), or Face/Edges
            - pg.fillet_intersect ; Intersect dges first (True), or not

        Args:
            context: Blender bpy.context instance.

        Returns:
            Status Set.
        """

        pg = context.scene.pdt_pg
        decimal_places = context.preferences.addons[__package__].preferences.pdt_input_round
        if pg.fillet_intersect:
            pg.command = (
                f"fi{str(round(pg.fillet_radius, decimal_places))}"
                f",{str(round(pg.fillet_segments, decimal_places))}"
                f",{str(round(pg.fillet_profile, decimal_places))}"
            )
        elif pg.fillet_vertices_only:
            pg.command = (
                f"fv{str(round(pg.fillet_radius, decimal_places))}"
                f",{str(round(pg.fillet_segments, decimal_places))}"
                f",{str(round(pg.fillet_profile, decimal_places))}"
            )
        else:
            pg.command = (
                f"fe{str(round(pg.fillet_radius, decimal_places))}"
                f",{str(round(pg.fillet_segments, decimal_places))}"
                f",{str(round(pg.fillet_profile, decimal_places))}"
            )
        return {"FINISHED"}


class PDT_OT_Angle2(Operator):
    """Measure Distance and Angle in Working Plane, Also sets Deltas"""

    bl_idname = "pdt.angle2"
    bl_label = "Measure 2D"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
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

        pg = context.scene.pdt_pg
        pg.command = f"ad2"
        return {"FINISHED"}


class PDT_OT_Angle3(Operator):
    """Measure Distance and Angle in 3D Space"""

    bl_idname = "pdt.angle3"
    bl_label = "Measure 3D"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
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
        pg.command = f"ad3"
        return {"FINISHED"}


class PDT_OT_Origin(Operator):
    """Move Object Origin to Cursor Location"""

    bl_idname = "pdt.origin"
    bl_label = "Move Origin"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
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

        pg = context.scene.pdt_pg
        pg.command = f"otc"
        return {"FINISHED"}


class PDT_OT_Taper(Operator):
    """Taper Vertices at Angle in Chosen Axis Mode"""

    bl_idname = "pdt.taper"
    bl_label = "Taper"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        ob = context.object
        if ob is None:
            return False
        return all([bool(ob), ob.type == "MESH", ob.mode == "EDIT"])

    def execute(self, context):
        """Taper Geometry along World Axes.

        Note:
            Similar to Blender Shear command except that it shears by angle rather than displacement.
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

        pg = context.scene.pdt_pg
        pg.command = f"tap"
        return {"FINISHED"}

#class PDT_Extrude_Modal(Operator):
#    """Extrude Modal Plane Along Normal Axis"""
#    bl_idname = "pdt.extrude_modal"
#    bl_label = "Extrude Modal Normal"
#    bl_options = {"REGISTER", "UNDO"}
