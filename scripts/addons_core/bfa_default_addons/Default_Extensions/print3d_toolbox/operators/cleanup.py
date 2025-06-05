# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2013-2022 Campbell Barton
# SPDX-FileContributor: Mikhail Rachinskiy


import math

import bmesh
import bpy
from bpy.app.translations import pgettext_tip as tip_
from bpy.props import FloatProperty, IntProperty
from bpy.types import Operator


class MESH_OT_clean_distorted(Operator):
    bl_idname = "mesh.print3d_clean_distorted"
    bl_label = "3D Print Clean Distorted"
    bl_description = "Tessellate distorted faces"
    bl_options = {"REGISTER", "UNDO"}

    angle: FloatProperty(
        name="Angle",
        description="Limit for checking distorted faces",
        subtype="ANGLE",
        default=math.radians(45.0),
        min=0.0,
        max=math.radians(180.0),
        step=100,
    )

    def execute(self, context):
        from .. import lib

        obj = context.active_object
        bm = lib.bmesh_from_object(obj)
        bm.normal_update()
        elems_triangulate = [ele for ele in bm.faces if lib.face_is_distorted(ele, self.angle)]

        if elems_triangulate:
            bmesh.ops.triangulate(bm, faces=elems_triangulate)
            lib.bmesh_to_object(obj, bm)

        self.report({"INFO"}, tip_("Triangulated {} faces").format(len(elems_triangulate)))

        return {"FINISHED"}

    def invoke(self, context, event):
        self.angle = context.scene.print_3d.angle_distort

        wm = context.window_manager
        wm.invoke_props_popup(self, event)
        return self.execute(context)


class MESH_OT_clean_non_manifold(Operator):
    bl_idname = "mesh.print3d_clean_non_manifold"
    bl_label = "3D Print Clean Non-Manifold"
    bl_description = "Cleanup problems, like holes, non-manifold vertices and inverted normals"
    bl_options = {"REGISTER", "UNDO"}

    threshold: FloatProperty(
        name="Merge Distance",
        description="Minimum distance between elements to merge",
        default=0.0001,
        precision=4,
        step=0.01,
        min=0.0
    )
    sides: IntProperty(
        name="Sides",
        description="Number of sides in hole required to fill (zero fills all holes)",
    )

    def execute(self, context):
        # TODO bow-tie quads

        self.context = context
        mode_orig = context.mode

        self.setup_environment()
        bm_key_orig = self.elem_count(context)

        self.delete_loose()
        self.delete_interior()
        self.remove_doubles(self.threshold)
        self.dissolve_degenerate(self.threshold)
        self.fix_non_manifold(context, self.sides)  # may take a while
        self.make_normals_consistently_outwards()

        bm_key = self.elem_count(context)

        if mode_orig != "EDIT_MESH":
            bpy.ops.object.mode_set(mode="OBJECT")

        verts = bm_key[0] - bm_key_orig[0]
        edges = bm_key[1] - bm_key_orig[1]
        faces = bm_key[2] - bm_key_orig[2]

        self.report({"INFO"}, tip_("Modified: {:+} vertices, {:+} edges, {:+} faces").format(verts, edges, faces))

        return {"FINISHED"}

    @staticmethod
    def elem_count(context):
        bm = bmesh.from_edit_mesh(context.edit_object.data)
        return len(bm.verts), len(bm.edges), len(bm.faces)

    @staticmethod
    def setup_environment():
        """set the mode as edit, select mode as vertices, and reveal hidden vertices"""
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_mode(type="VERT")
        bpy.ops.mesh.reveal()

    @staticmethod
    def remove_doubles(threshold):
        """remove duplicate vertices"""
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.remove_doubles(threshold=threshold)

    @staticmethod
    def delete_loose():
        """delete loose vertices/edges/faces"""
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.delete_loose(use_verts=True, use_edges=True, use_faces=True)

    @staticmethod
    def delete_interior():
        """delete interior faces"""
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.mesh.select_interior_faces()
        bpy.ops.mesh.delete(type="FACE")

    @staticmethod
    def dissolve_degenerate(threshold):
        """dissolve zero area faces and zero length edges"""
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.dissolve_degenerate(threshold=threshold)

    @staticmethod
    def make_normals_consistently_outwards():
        """have all normals face outwards"""
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.normals_make_consistent()

    @classmethod
    def fix_non_manifold(cls, context, sides):
        """naive iterate-until-no-more approach for fixing manifolds"""
        total_non_manifold = cls.count_non_manifold_verts(context)

        if not total_non_manifold:
            return

        bm_states = set()
        bm_key = cls.elem_count(context)
        bm_states.add(bm_key)

        while True:
            cls.fill_non_manifold(sides)
            cls.delete_newly_generated_non_manifold_verts()

            bm_key = cls.elem_count(context)
            if bm_key in bm_states:
                break
            else:
                bm_states.add(bm_key)

    @staticmethod
    def select_non_manifold_verts(
        use_wire=False,
        use_boundary=False,
        use_multi_face=False,
        use_non_contiguous=False,
        use_verts=False,
    ):
        """select non-manifold vertices"""
        bpy.ops.mesh.select_non_manifold(
            extend=False,
            use_wire=use_wire,
            use_boundary=use_boundary,
            use_multi_face=use_multi_face,
            use_non_contiguous=use_non_contiguous,
            use_verts=use_verts,
        )

    @classmethod
    def count_non_manifold_verts(cls, context):
        """return a set of coordinates of non-manifold vertices"""
        cls.select_non_manifold_verts(use_wire=True, use_boundary=True, use_verts=True)

        bm = bmesh.from_edit_mesh(context.edit_object.data)
        return sum((1 for v in bm.verts if v.select))

    @classmethod
    def fill_non_manifold(cls, sides):
        """fill in any remnant non-manifolds"""
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.fill_holes(sides=sides)

    @classmethod
    def delete_newly_generated_non_manifold_verts(cls):
        """delete any newly generated vertices from the filling repair"""
        cls.select_non_manifold_verts(use_wire=True, use_verts=True)
        bpy.ops.mesh.delete(type="VERT")
