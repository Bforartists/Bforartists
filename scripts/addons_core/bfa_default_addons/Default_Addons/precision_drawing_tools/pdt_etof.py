# SPDX-FileCopyrightText: 2016-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

#
# ----------------------------------------------------------
# Author: Zeffii
# Modified by: Alan Odom (Clockmender) & Rune Morling (ermo)
# ----------------------------------------------------------
#
#
import bpy
import bmesh
from mathutils.geometry import intersect_line_plane
from .pdt_msg_strings import (
    PDT_ERR_NOINT,
    PDT_ERR_EDOB_MODE,
    PDT_ERR_SEL_1_E_1_F,
)
from .pdt_functions import oops


def failure_message(context):
    """Warn to the user to select 1 edge and 1 face.

    Args:
         context: Blender bpy.context instance.

    Returns:
        Nothing.
    """

    pg = context.scene.pdt_pg
    pg.error = f"{PDT_ERR_SEL_1_E_1_F}"
    context.window_manager.popup_menu(oops, title="Error", icon="ERROR")


def failure_message_on_plane(context):
    """Report an informative error message in a popup.

    Args:
         context: Blender bpy.context instance.

    Returns:
        Nothing.
    """

    pg = context.scene.pdt_pg
    pg.error = f"{PDT_ERR_NOINT}"
    context.window_manager.popup_menu(oops, title="Error", icon="ERROR")

def extend_vertex(context):
    """Computes Edge Extension to Face.

    Args:
        context: Blender bpy.context instance.

    Returns:
        Nothing.
    """

    obj = bpy.context.edit_object
    pg = context.scene.pdt_pg

    if all([bool(obj), obj.type == "MESH", obj.mode == "EDIT"]):
        object_data = obj.data
        bm = bmesh.from_edit_mesh(object_data)
        verts = bm.verts
        faces = bm.faces

        planes = [f for f in faces if f.select]
        if not len(planes) == 1:
            failure_message(context)
            return

        plane = planes[0]
        plane_vert_indices = plane.verts[:]
        all_selected_vert_indices = [v for v in verts if v.select]

        plane_verts = set(plane_vert_indices)
        all_verts = set(all_selected_vert_indices)
        diff_verts = all_verts.difference(plane_verts)
        diff_verts = list(diff_verts)

        if not len(diff_verts) == 2:
            failure_message(context)
            return

        (v1_ref, v1), (v2_ref, v2) = [(i, i.co) for i in diff_verts]

        plane_co = plane.calc_center_median()
        plane_no = plane.normal

        new_co = intersect_line_plane(v1, v2, plane_co, plane_no, False)

        if new_co:
            new_vertex = verts.new(new_co)
            a_len = (v1 - new_co).length
            b_len = (v2 - new_co).length

            vertex_reference = v1_ref if (a_len < b_len) else v2_ref
            bm.edges.new([vertex_reference, new_vertex])
            bmesh.update_edit_mesh(object_data, loop_triangles=True)

        else:
            failure_message_on_plane(context)
    else:
        pg.error = f"{PDT_ERR_EDOB_MODE},{obj.mode})"
        context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        return


class PDT_OT_EdgeToFace(bpy.types.Operator):
    """Extend Selected Edge to Projected Intersection with Selected Face"""

    bl_idname = "pdt.edge_to_face"
    bl_label = "Extend Edge to Face"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """Only allow this to work if a mesh is selected in EDIT mode.

        Args:
            context: Blender bpy.context instance.

        Returns:
            Boolean.
        """

        obj = context.object
        if obj is None:
            return False
        return all([bool(obj), obj.type == "MESH", obj.mode == "EDIT"])

    def execute(self, context):
        """Extends Disconnected Edge to Intersect with Face.

        Args:
            context: Blender bpy.context instance.

        Returns:
            Status Set.
        """

        pg = context.scene.pdt_pg
        pg.command = f"etf"
        return {"FINISHED"}
