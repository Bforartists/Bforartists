# SPDX-FileCopyrightText: 2016-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later


import bpy
import bmesh
from mathutils import geometry


def add_vertex_to_intersection():

    obj = bpy.context.object
    me = obj.data
    bm = bmesh.from_edit_mesh(me)

    edges = [e for e in bm.edges if e.select]

    if len(edges) == 2:
        [[v1, v2], [v3, v4]] = [[v.co for v in e.verts] for e in edges]

        iv = geometry.intersect_line_line(v1, v2, v3, v4)
        if iv:
            iv = (iv[0] + iv[1]) / 2
            bm.verts.new(iv)

            bm.verts.ensure_lookup_table()

            bm.verts[-1].select = True
            bmesh.update_edit_mesh(me)


class TCVert2Intersection(bpy.types.Operator):
    '''Add a vertex at the intersection (projected or real) of two selected edges'''
    bl_idname = 'tinycad.vertintersect'
    bl_label = 'V2X vertex to intersection'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == 'MESH' and obj.mode == 'EDIT'

    def execute(self, context):
        add_vertex_to_intersection()
        return {'FINISHED'}
