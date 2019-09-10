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

def defSelectFlippedUvs(self, context):
    bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    
    uvLayer = bm.loops.layers.uv.verify()
    

    for face in bm.faces:
        sum_edges = 0
        
        for i in range(3):
            uv_A = face.loops[i][uvLayer].uv
            uv_B = face.loops[(i+1)%3][uvLayer].uv
            sum_edges += uv_B.cross(uv_A)
            
        if sum_edges > 0:
            face.select_set(True)

    bmesh.update_edit_mesh(bpy.context.object.data)


class selectFlippedUvs(bpy.types.Operator):
    """Copy Uv Island"""
    bl_idname = "mesh.select_flipped_uvs"
    bl_label = "Select Flipped Uvs"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None and
                context.active_object.type == 'MESH' and
                context.active_object.mode == "EDIT")

    def execute(self, context):
        defSelectFlippedUvs(self, context)
        return {'FINISHED'}