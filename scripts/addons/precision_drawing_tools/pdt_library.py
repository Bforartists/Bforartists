# SPDX-FileCopyrightText: 2019-2022 Alan Odom (Clockmender)
# SPDX-FileCopyrightText: 2019-2022 Rune Morling (ermo)
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.types import Operator
from mathutils import Vector
from pathlib import Path
from .pdt_functions import debug, oops
from .pdt_msg_strings import PDT_ERR_NO_LIBRARY, PDT_ERR_OBJECTMODE


class PDT_OT_LibShow(Operator):
    """Show Library File Details"""

    bl_idname = "pdt.lib_show"
    bl_label = "Show Library Details"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """Shows Location Of PDT Library File.

        Args:
            context: Blender bpy.context instance.

        Returns:
            Status Set.
        """

        scene = context.scene
        pg = scene.pdt_pg
        file_path = pg.pdt_library_path
        pg.error = str(Path(file_path))
        debug("PDT Parts Library:")
        debug(f"{pg.error}")
        bpy.context.window_manager.popup_menu(
            oops, title="Information - Parts Library File", icon="INFO"
        )
        return {"FINISHED"}


class PDT_OT_Append(Operator):
    """Append from Library at cursor Location"""

    bl_idname = "pdt.append"
    bl_label = "Append"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """Appends Objects from PDT Library file.

        Note:
            Appended Objects are placed at Cursor Location.
            Uses pg.lib_objects, pg.lib_collections & pg.lib_materials

        Args:
            context: Blender bpy.context instance.

        Returns:
            Status Set.
        """

        scene = context.scene
        pg = scene.pdt_pg
        obj = context.view_layer.objects.active
        if obj is not None:
            if obj.mode != "OBJECT":
                error_message = PDT_ERR_OBJECTMODE
                self.report({"ERROR"}, error_message)
                return {"FINISHED"}

        obj_names = [o.name for o in context.view_layer.objects].copy()
        file_path = pg.pdt_library_path
        path = Path(file_path)

        if path.is_file() and str(path).endswith(".blend"):
            if pg.lib_mode == "OBJECTS":
                bpy.ops.wm.append(
                    filepath=str(path),
                    directory=str(path) + "/Object",
                    filename=pg.lib_objects,
                )
                for obj in context.view_layer.objects:
                    if obj.name not in obj_names:
                        obj.select_set(False)
                        obj.location = Vector(
                            (
                                scene.cursor.location.x,
                                scene.cursor.location.y,
                                scene.cursor.location.z,
                            )
                        )
                return {"FINISHED"}
            if pg.lib_mode == "COLLECTIONS":
                bpy.ops.wm.append(
                    filepath=str(path),
                    directory=str(path) + "/Collection",
                    filename=pg.lib_collections,
                )
                for obj in context.view_layer.objects:
                    if obj.name not in obj_names:
                        obj.select_set(False)
                        obj.location = Vector(
                            (
                                scene.cursor.location.x,
                                scene.cursor.location.y,
                                scene.cursor.location.z,
                            )
                        )
                return {"FINISHED"}
            if pg.lib_mode == "MATERIALS":
                bpy.ops.wm.append(
                    filepath=str(path),
                    directory=str(path) + "/Material",
                    filename=pg.lib_materials,
                )
                return {"FINISHED"}

        error_message = PDT_ERR_NO_LIBRARY
        self.report({"ERROR"}, error_message)
        return {"FINISHED"}


class PDT_OT_Link(Operator):
    """Link from Library at Object's Origin"""

    bl_idname = "pdt.link"
    bl_label = "Link"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """Links Objects from PDT Library file.

        Note:
            Linked Objects are placed at Cursor Location
            Uses pg.lib_objects, pg.lib_collections & pg.lib_materials

        Args:
            context: Blender bpy.context instance.

        Returns:
            Status Set.
        """

        scene = context.scene
        pg = scene.pdt_pg
        obj = context.view_layer.objects.active
        if obj is not None:
            if obj.mode != "OBJECT":
                error_message = PDT_ERR_OBJECTMODE
                self.report({"ERROR"}, error_message)
                return {"FINISHED"}

        file_path = pg.pdt_library_path
        path = Path(file_path)

        if path.is_file() and str(path).endswith(".blend"):
            if pg.lib_mode == "OBJECTS":
                bpy.ops.wm.link(
                    filepath=str(path),
                    directory=str(path) + "/Object",
                    filename=pg.lib_objects,
                )
                for obj in context.view_layer.objects:
                    obj.select_set(False)
                return {"FINISHED"}
            if pg.lib_mode == "COLLECTIONS":
                bpy.ops.wm.link(
                    filepath=str(path),
                    directory=str(path) + "/Collection",
                    filename=pg.lib_collections,
                )
                for obj in context.view_layer.objects:
                    obj.select_set(False)
                return {"FINISHED"}
            if pg.lib_mode == "MATERIALS":
                bpy.ops.wm.link(
                    filepath=str(path),
                    directory=str(path) + "/Material",
                    filename=pg.lib_materials,
                )
                return {"FINISHED"}

        error_message = PDT_ERR_NO_LIBRARY
        self.report({"ERROR"}, error_message)
        return {"FINISHED"}
