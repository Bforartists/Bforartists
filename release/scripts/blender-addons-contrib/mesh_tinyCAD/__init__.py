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

bl_info = {
    "name": "tinyCAD Mesh tools",
    "author": "zeffii (aka Dealga McArdle)",
    "version": (1, 0, 7),
    "blender": (2, 7, 3),
    "category": "Mesh",
    "location": "View3D > EditMode > (w) Specials",
    "wiki_url": "",
    "tracker_url": ""
}

## implemented lookup table for bmesh changes in 2.73

if "bpy" in locals():
    import imp

import bpy
from mesh_tinyCAD.VTX import AutoVTX
from mesh_tinyCAD.V2X import Vert2Intersection
# from mesh_tinyCAD.EXM import ExtendEdgesMulti
from mesh_tinyCAD.XALL import IntersectAllEdges
from mesh_tinyCAD.BIX import LineOnBisection
from mesh_tinyCAD.PERP import CutOnPerpendicular
from mesh_tinyCAD.CCEN import CircleCenter


vtx_classes = (
    [AutoVTX, "tinyCAD autoVTX"],
    [Vert2Intersection, "tinyCAD V2X"],
    [IntersectAllEdges, "tinyCAD XALL"],
    # [ExtendEdgesMulti, "tinyCAD EXM"],      # this is buggy
    [LineOnBisection, "tinyCAD BIX"],
    [CutOnPerpendicular, "tinyCAD PERP CUT"],
    [CircleCenter, "tC Circle Center"]
)


class VIEW3D_MT_edit_mesh_tinycad(bpy.types.Menu):
    bl_label = "TinyCAD"

    def draw(self, context):
        for i, text in vtx_classes:
            self.layout.operator(i.bl_idname, text=text)


def menu_func(self, context):
    self.layout.menu("VIEW3D_MT_edit_mesh_tinycad")
    self.layout.separator()


def register():
    for i, _ in vtx_classes:
        bpy.utils.register_class(i)
    bpy.utils.register_class(VIEW3D_MT_edit_mesh_tinycad)
    bpy.types.VIEW3D_MT_edit_mesh_specials.prepend(menu_func)


def unregister():
    for i, _ in vtx_classes:
        bpy.utils.unregister_class(i)
    bpy.utils.unregister_class(VIEW3D_MT_edit_mesh_tinycad)
    bpy.types.VIEW3D_MT_edit_mesh_specials.remove(menu_func)
