# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Split Solidify",
    "author": "zmj100, updated by zeffii to BMesh",
    "version": (0, 1, 2),
    "blender": (2, 80, 0),
    "location": "View3D > Tool Shelf",
    "description": "",
    "warning": "",
    "doc_url": "",
    "category": "Mesh",
}

import bpy
import bmesh
from bpy.types import Operator
from bpy.props import (
        EnumProperty,
        FloatProperty,
        BoolProperty,
        )
import random
from math import cos


# define the functions
def solidify_split(self, list_0):

    loc_random = self.loc_random
    random_dist = self.random_dist
    distance = self.distance
    thickness = self.thickness
    normal_extr = self.normal_extr

    bm = self.bm

    for fi in list_0:
        bm.faces.ensure_lookup_table()
        f = bm.faces[fi]
        list_1 = []
        list_2 = []

        if loc_random:
            d = random_dist * random.randrange(0, 10)
        elif not loc_random:
            d = distance

        # add new vertices
        for vi in f.verts:
            bm.verts.ensure_lookup_table()
            v = bm.verts[vi.index]

            if normal_extr == 'opt0':
                p1 = (v.co).copy() + ((f.normal).copy() * d)                # out
                p2 = (v.co).copy() + ((f.normal).copy() * (d - thickness))  # in
            elif normal_extr == 'opt1':
                ang = ((v.normal).copy()).angle((f.normal).copy())
                h = thickness / cos(ang)
                p1 = (v.co).copy() + ((f.normal).copy() * d)
                p2 = p1 + (-h * (f.normal).copy())

            v1 = bm.verts.new(p1)
            v2 = bm.verts.new(p2)
            v1.select = False
            v2.select = False
            list_1.append(v1)
            list_2.append(v2)

        # add new faces, allows faces with more than 4 verts
        n = len(list_1)

        k = bm.faces.new(list_1)
        k.select = False
        for i in range(n):
            j = (i + 1) % n
            vseq = list_1[i], list_2[i], list_2[j], list_1[j]
            k = bm.faces.new(vseq)
            k.select = False

        list_2.reverse()
        k = bm.faces.new(list_2)
        k.select = False
    bpy.ops.mesh.normals_make_consistent(inside=False)

    bmesh.update_edit_mesh(self.me, loop_triangles=True)


class MESH_OT_split_solidify(Operator):
    bl_idname = "mesh.split_solidify"
    bl_label = "Split Solidify"
    bl_description = "Split and Solidify selected Faces"
    bl_options = {"REGISTER", "UNDO"}

    distance: FloatProperty(
            name="",
            description="Distance of the splitted Faces to the original geometry",
            default=0.4,
            min=-100.0, max=100.0,
            step=1,
            precision=3
            )
    thickness: FloatProperty(
            name="",
            description="Thickness of the splitted Faces",
            default=0.04,
            min=-100.0, max=100.0,
            step=1,
            precision=3
            )
    random_dist: FloatProperty(
            name="",
            description="Randomization factor of the splitted Faces' location",
            default=0.06,
            min=-10.0, max=10.0,
            step=1,
            precision=3
            )
    loc_random: BoolProperty(
            name="Random",
            description="Randomize the locations of splitted faces",
            default=False
            )
    del_original: BoolProperty(
            name="Delete original faces",
            default=True
            )
    normal_extr: EnumProperty(
            items=(('opt0', "Face", "Solidify along Face Normals"),
                   ('opt1', "Vertex", "Solidify along Vertex Normals")),
            name="Normal",
            default='opt0'
           )

    def draw(self, context):
        layout = self.layout
        layout.label(text="Normal:")
        layout.prop(self, "normal_extr", expand=True)
        layout.prop(self, "loc_random")

        if not self.loc_random:
            layout.label(text="Distance:")
            layout.prop(self, "distance")
        elif self.loc_random:
            layout.label(text="Random distance:")
            layout.prop(self, "random_dist")

        layout.label(text="Thickness:")
        layout.prop(self, "thickness")
        layout.prop(self, "del_original")

    def execute(self, context):
        obj = bpy.context.active_object
        self.me = obj.data
        self.bm = bmesh.from_edit_mesh(self.me)
        self.me.update()

        list_0 = [f.index for f in self.bm.faces if f.select]

        if len(list_0) == 0:
            self.report({'WARNING'},
                        "No suitable selection found. Operation cancelled")

            return {'CANCELLED'}

        elif len(list_0) != 0:
            solidify_split(self, list_0)
            context.tool_settings.mesh_select_mode = (True, True, True)
            if self.del_original:
                bpy.ops.mesh.delete(type='FACE')
            else:
                pass

        return {'FINISHED'}


def register():
    bpy.utils.register_class(MESH_OT_split_solidify)


def unregister():
    bpy.utils.unregister_class(MESH_OT_split_solidify)


if __name__ == "__main__":
    register()
