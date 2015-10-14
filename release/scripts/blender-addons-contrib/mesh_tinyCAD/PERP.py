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
import mathutils
import math
from mathutils import Vector


def cut_visible_by_perpendicular(self):

    obj = bpy.context.object
    me = obj.data
    bm = bmesh.from_edit_mesh(me)

    if hasattr(bm.verts, "ensure_lookup_table"):
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()    
        bm.faces.ensure_lookup_table()

    verts = [v for v in bm.verts if (v.select and not v.hide)]

    if not len(verts) == 2:
        msg = "select two vertices"
        self.report({"WARNING"}, msg)
        return {'CANCELLED'}

    v1, v2 = [v.co for v in verts]
    print('vectors found:\n', v1, '\n', v2)

    mid_vec = v1.lerp(v2, 0.5)
    plane_no = v2 - mid_vec
    plane_co = mid_vec
    dist = 0.0001

    # hidden geometry will not be affected.
    visible_geom = [g for g in bm.faces[:]
                    + bm.verts[:] + bm.edges[:] if not g.hide]

    bmesh.ops.bisect_plane(
        bm,
        geom=visible_geom,
        dist=dist,
        plane_co=plane_co, plane_no=plane_no,
        use_snap_center=False,
        clear_outer=False,
        clear_inner=False)

    bmesh.update_edit_mesh(me, True)


class CutOnPerpendicular(bpy.types.Operator):

    bl_idname = 'mesh.cutonperp'
    bl_label = 'perp cutline for verts'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        return all([obj is not None, obj.type == 'MESH', obj.mode == 'EDIT'])

    def execute(self, context):
        cut_visible_by_perpendicular(self)
        return {'FINISHED'}
