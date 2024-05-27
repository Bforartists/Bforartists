# SPDX-FileCopyrightText: 2019-2022 Alan Odom (Clockmender)
# SPDX-FileCopyrightText: 2019-2022 Rune Morling (ermo)
# SPDX-FileCopyrightText: 2014 Reiner Prokein (tiles)
#
# SPDX-License-Identifier: GPL-2.0-or-later

# -----------------------------------------------------------------------
# Contains code which was inspired by the "Reset 3D View"
# plugin authored by Reiner Prokein (tiles), (see #37718).
# -----------------------------------------------------------------------

import bpy
from bpy.types import Operator
from math import pi
from mathutils import Quaternion
from .pdt_functions import debug, euler_to_quaternion


class PDT_OT_ViewRot(Operator):
    """Rotate View by Absolute Coordinates."""

    bl_idname = "pdt.viewrot"
    bl_label = "Rotate View"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "View Rotation by Absolute Values"

    def execute(self, context):
        """View Rotation by Absolute Values.

        Note:
            Rotations are converted to 3x3 Quaternion Rotation Matrix.
            This is an Absolute Rotation, not an Incremental Orbit.
            Uses pg.rotation_coords scene variable

        Args:
            context: Blender bpy.context instance.

        Returns:
            Status Set.
        """

        scene = context.scene
        pg = scene.pdt_pg
        roll_value = euler_to_quaternion(
            pg.rotation_coords.x * pi / 180,
            pg.rotation_coords.y * pi / 180,
            pg.rotation_coords.z * pi / 180,
        )
        context.region_data.view_rotation = roll_value
        return {"FINISHED"}


class PDT_OT_ViewRotL(Operator):
    """Rotate View Left."""

    bl_idname = "pdt.viewleft"
    bl_label = "Rotate Left"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "View Orbit Left by Delta Value"

    def execute(self, context):
        """View Orbit Left by Delta Value.

        Note:
            Uses pg.vrotangle scene variable
            Orbits view to the left about its vertical axis

        Args:
            context: Blender bpy.context instance.

        Returns:
            Status Set.
        """

        scene = context.scene
        pg = scene.pdt_pg
        bpy.ops.view3d.view_orbit(angle=(pg.vrotangle * pi / 180), type="ORBITLEFT")
        return {"FINISHED"}


class PDT_OT_ViewRotR(Operator):
    """Rotate View Right."""

    bl_idname = "pdt.viewright"
    bl_label = "Rotate Right"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "View Orbit Right by Delta Value"

    def execute(self, context):
        """View Orbit Right by Delta Value.

        Note:
            Uses pg.vrotangle scene variable
            Orbits view to the right about its vertical axis

        Args:
            context: Blender bpy.context instance.

        Returns:
            Status Set.
        """

        scene = context.scene
        pg = scene.pdt_pg
        bpy.ops.view3d.view_orbit(angle=(pg.vrotangle * pi / 180), type="ORBITRIGHT")
        return {"FINISHED"}


class PDT_OT_ViewRotU(Operator):
    """Rotate View Up."""

    bl_idname = "pdt.viewup"
    bl_label = "Rotate Up"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "View Orbit Up by Delta Value"

    def execute(self, context):
        """View Orbit Up by Delta Value.

        Note:
            Uses pg.vrotangle scene variable
            Orbits view up about its horizontal axis

        Args:
            context: Blender bpy.context instance.

        Returns:
            Status Set.
        """

        scene = context.scene
        pg = scene.pdt_pg
        bpy.ops.view3d.view_orbit(angle=(pg.vrotangle * pi / 180), type="ORBITUP")
        return {"FINISHED"}


class PDT_OT_ViewRotD(Operator):
    """Rotate View Down."""

    bl_idname = "pdt.viewdown"
    bl_label = "Rotate Down"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "View Orbit Down by Delta Value"

    def execute(self, context):
        """View Orbit Down by Delta Value.

        Note:
            Uses pg.vrotangle scene variable
            Orbits view down about its horizontal axis

        Args:
            context: Blender bpy.context instance.

        Returns:
            Status Set.
        """

        scene = context.scene
        pg = scene.pdt_pg
        bpy.ops.view3d.view_orbit(angle=(pg.vrotangle * pi / 180), type="ORBITDOWN")
        return {"FINISHED"}


class PDT_OT_ViewRoll(Operator):
    """Roll View."""

    bl_idname = "pdt.viewroll"
    bl_label = "Roll View"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "View Roll by Delta Value"

    def execute(self, context):
        """View Roll by Delta Value.

        Note:
            Uses pg.vrotangle scene variable
            Rolls view about its normal axis

        Args:
            context: Blender bpy.context instance.

        Returns:
            Status Set.
        """

        scene = context.scene
        pg = scene.pdt_pg
        bpy.ops.view3d.view_roll(angle=(pg.vrotangle * pi / 180), type="ANGLE")
        return {"FINISHED"}


class PDT_OT_ViewIso(Operator):
    """Set View Isometric."""

    bl_idname = "pdt.viewiso"
    bl_label = "Isometric View"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Isometric View"

    def execute(self, context):
        """Set Isometric View.

        Note:
            Set view orientation to Orthographic Isometric

        Args:
            context: Blender bpy.context instance.

        Returns:
            Status Set.
        """

        # Rotate view 45 degrees about Z then 32.2644 about X
        context.region_data.view_rotation = Quaternion((0.8205, 0.4247, -0.1759, -0.3399))
        context.region_data.view_perspective = "ORTHO"
        return {"FINISHED"}


class PDT_OT_Reset3DView(Operator):
    """Reset Views to Factory Default."""

    bl_idname = "pdt.reset_3d_view"
    bl_label = "Reset 3D View"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Reset 3D View to Blender Defaults"

    def execute(self, context):
        """Reset 3D View to Blender Defaults.

        Args:
            context: Blender bpy.context instance.

        Returns:
            Status Set.
        """

        # The default view_distance to the origin when starting up Blender
        default_view_distance = 17.986562728881836
        default_view_distance = (
            bpy.data.screens["Layout"].areas[-1].spaces[0].region_3d.view_distance
        )
        # The default view_matrix when starting up Blender
        default_view_matrix = (
            (0.41, -0.4017, 0.8188, 0.0),
            (0.912, 0.1936, -0.3617, 0.0),
            (-0.0133, 0.8950, 0.4458, 0.0),
            (0.0, 0.0, -17.9866, 1.0),
        )

        view = context.region_data
        debug(f"is_orthographic_side_view: {view.is_orthographic_side_view}")
        if view.is_orthographic_side_view:
            # When the view is orthographic, reset the distance and location.
            # The rotation already fits.
            debug(f"view_distance before reset: {view.view_distance}")
            debug(f"view_location before reset: {view.view_location}")
            view.view_distance = default_view_distance
            view.view_location = (-0.0, -0.0, -0.0)
            view.update()
            debug(f"view_distance AFTER reset: {view.view_distance}")
            debug(f"view_location AFTER reset: {view.view_location}")
        else:
            # Otherwise, the view matrix needs to be reset.
            debug(f"view_matrix before reset:\n{view.view_matrix}")
            view.view_matrix = default_view_matrix
            view.view_distance = default_view_distance
            view.update()
            debug(f"view_matrix AFTER reset:\n{view.view_matrix}")

        return {"FINISHED"}
