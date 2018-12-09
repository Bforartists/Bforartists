#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
"""
Symmetry Tools: Find Asymmetric + Make Symmetric (by Sergey Sharybin)

Our character wasn’t completely symmetric in some parts where it was
supposed to, this could be by moving vertices by mistake or just reasons.
To fix this in a fast way, Sergey coded this two super useful tools:

* Find Asymmetric:
Selects vertices that don’t have the same position on the opposite side.

* Make Symmetric:
Move selected vertices to match the position of those on the other side.

This tools may not apply on every single model out there, but I tried it
in many different characters and it worked. So probably better use it on
those models that were already symmetric at some point, modeled with a
mirror modifier or so.
Search (spacebar) for "Find Asymmetric", and "Make Symmetric""Settings".

> Developed during Caminandes Open Movie Project
"""

import bpy
import bmesh
from mathutils import Vector


class AMTH_MESH_OT_find_asymmetric(bpy.types.Operator):

    """
    Find asymmetric vertices
    """

    bl_idname = "mesh.find_asymmetric"
    bl_label = "Find Asymmetric"
    bl_options = {"UNDO", "REGISTER"}

    @classmethod
    def poll(cls, context):
        object = context.object
        if object:
            return object.mode == "EDIT" and object.type == "MESH"
        return False

    def execute(self, context):
        threshold = 1e-6

        object = context.object
        bm = bmesh.from_edit_mesh(object.data)

        # Deselect all the vertices
        for v in bm.verts:
            v.select = False

        for v1 in bm.verts:
            if abs(v1.co[0]) < threshold:
                continue

            mirror_found = False
            for v2 in bm.verts:
                if v1 == v2:
                    continue
                if v1.co[0] * v2.co[0] > 0.0:
                    continue

                mirror_coord = Vector(v2.co)
                mirror_coord[0] *= -1
                if (mirror_coord - v1.co).length_squared < threshold:
                    mirror_found = True
                    break
            if not mirror_found:
                v1.select = True

        bm.select_flush_mode()

        bmesh.update_edit_mesh(object.data)

        return {"FINISHED"}


class AMTH_MESH_OT_make_symmetric(bpy.types.Operator):

    """
    Make symmetric
    """

    bl_idname = "mesh.make_symmetric"
    bl_label = "Make Symmetric"
    bl_options = {"UNDO", "REGISTER"}

    @classmethod
    def poll(cls, context):
        object = context.object
        if object:
            return object.mode == "EDIT" and object.type == "MESH"
        return False

    def execute(self, context):
        threshold = 1e-6

        object = context.object
        bm = bmesh.from_edit_mesh(object.data)

        for v1 in bm.verts:
            if v1.co[0] < threshold:
                continue
            if not v1.select:
                continue

            closest_vert = None
            closest_distance = -1
            for v2 in bm.verts:
                if v1 == v2:
                    continue
                if v2.co[0] > threshold:
                    continue
                if not v2.select:
                    continue

                mirror_coord = Vector(v2.co)
                mirror_coord[0] *= -1
                distance = (mirror_coord - v1.co).length_squared
                if closest_vert is None or distance < closest_distance:
                    closest_distance = distance
                    closest_vert = v2

            if closest_vert:
                closest_vert.select = False
                closest_vert.co = Vector(v1.co)
                closest_vert.co[0] *= -1
            v1.select = False

        for v1 in bm.verts:
            if v1.select:
                closest_vert = None
                closest_distance = -1
                for v2 in bm.verts:
                    if v1 != v2:
                        mirror_coord = Vector(v2.co)
                        mirror_coord[0] *= -1
                        distance = (mirror_coord - v1.co).length_squared
                        if closest_vert is None or distance < closest_distance:
                            closest_distance = distance
                            closest_vert = v2
                if closest_vert:
                    v1.select = False
                    v1.co = Vector(closest_vert.co)
                    v1.co[0] *= -1

        bm.select_flush_mode()
        bmesh.update_edit_mesh(object.data)

        return {"FINISHED"}


def register():
    bpy.utils.register_class(AMTH_MESH_OT_find_asymmetric)
    bpy.utils.register_class(AMTH_MESH_OT_make_symmetric)


def unregister():
    bpy.utils.unregister_class(AMTH_MESH_OT_find_asymmetric)
    bpy.utils.unregister_class(AMTH_MESH_OT_make_symmetric)
