'''
BEGIN GPL LICENSE BLOCK

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software Foundation,
Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

END GPL LICENCE BLOCK
'''

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
        iv = (iv[0] + iv[1]) / 2
        bm.verts.new(iv)

        # precaution?
        if hasattr(bm.verts, "ensure_lookup_table"):
            bm.verts.ensure_lookup_table()
            # bm.edges.ensure_lookup_table()

        bm.verts[-1].select = True
        bmesh.update_edit_mesh(me)


class Vert2Intersection(bpy.types.Operator):

    bl_idname = 'mesh.vertintersect'
    bl_label = 'v2x vertex to intersection'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        return obj is not None and obj.type == 'MESH' and obj.mode == 'EDIT'

    def execute(self, context):
        add_vertex_to_intersection()
        return {'FINISHED'}
