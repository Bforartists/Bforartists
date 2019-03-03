# ##### BEGIN GPL LICENSE BLOCK #####
#
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
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>


import bpy
import bmesh
from random import uniform

def vertexColorMask(self,context):
    obj = bpy.context.active_object
    mesh= obj.data
    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
    bpy.ops.mesh.select_all(action="DESELECT")
    bm = bmesh.from_edit_mesh(mesh)
    bm.faces.ensure_lookup_table()
    islands = []
    faces = bm.faces
    try:
        color_layer = bm.loops.layers.color["RGBMask"]
    except:
        color_layer = bm.loops.layers.color.new("RGBMask")
    while faces:
        faces[0].select_set(True)
        bpy.ops.mesh.select_linked()
        islands.append([f for f in faces if f.select])
        bpy.ops.mesh.hide(unselected=False)
        faces = [f for f in bm.faces if not f.hide]
    bpy.ops.mesh.reveal()
    for island in islands:
        color = (uniform(0,1),uniform(0,1),uniform(0,1),1)
        for face in island:
            for loop in face.loops:
                loop[color_layer] = color
    bpy.ops.object.mode_set(mode="VERTEX_PAINT")
    
    
class createVCMask(bpy.types.Operator):
    bl_idname = "mesh.vertex_color_mask"
    bl_label = "Vertex Color Mask"
    bl_description = ("Create a Vertex Color Mask")
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None

    def execute(self, context):
        vertexColorMask(self, context)
        return {'FINISHED'}



