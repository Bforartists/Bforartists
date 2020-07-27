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
from mathutils import Vector
from bpy.types import Operator
from bpy.props import (
        IntProperty,
        BoolProperty,
        FloatProperty,
        EnumProperty,
        )
        
        
import bmesh

# -------------------------- OVERLAP UV ISLANDS

def defCopyUvsIsland(self, context):
    global islandSet
    islandSet = {}
    islandSet["Loop"] = []
   
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    bpy.ops.uv.select_linked()
    bm = bmesh.from_edit_mesh(bpy.context.object.data)
    uv_lay = bm.loops.layers.uv.active
    faceSel = 0
    for face in bm.faces:
        if face.select:
            faceSel +=1 
            for loop in face.loops:
                islandSet["Loop"].append(loop[uv_lay].uv.copy())     
    islandSet["Size"] = faceSel

def defPasteUvsIsland(self, uvOffset, rotateUv,context):
    bm = bmesh.from_edit_mesh(bpy.context.object.data)
    bpy.context.scene.tool_settings.use_uv_select_sync = True    
    pickedFaces = [face for face in bm.faces if face.select]
    for face in pickedFaces:
        bpy.ops.mesh.select_all(action="DESELECT")
        face.select=True
        bmesh.update_edit_mesh(bpy.context.object.data)
        bpy.ops.uv.select_linked()
        uv_lay = bm.loops.layers.uv.active      
        faceSel = 0
        for face in bm.faces:
            if face.select:
                faceSel +=1     
        i = 0        
        if faceSel == islandSet["Size"]:   
            for face in bm.faces:
                if face.select:                
                    for loop in face.loops:
                        loop[uv_lay].uv  = islandSet["Loop"][i] if uvOffset == False else islandSet["Loop"][i]+Vector((1,0))
                        i += 1 
        else:
            print("the island have a different size of geometry")   
            
        if rotateUv:
            bpy.ops.object.mode_set(mode="EDIT")
            bmesh.ops.reverse_uvs(bm, faces=[f for f in bm.faces if f.select])
            bmesh.ops.rotate_uvs(bm, faces=[f for f in bm.faces if f.select])        

class CopyUvIsland(Operator):
    """Copy Uv Island"""
    bl_idname = "mesh.uv_island_copy"
    bl_label = "Copy Uv Island"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None and
                context.active_object.type == 'MESH' and
                context.active_object.mode == "EDIT")

    def execute(self, context):
        defCopyUvsIsland(self, context)
        return {'FINISHED'}

class PasteUvIsland(Operator):
    """Paste Uv Island"""
    bl_idname = "mesh.uv_island_paste"
    bl_label = "Paste Uv Island"
    bl_options = {"REGISTER", "UNDO"}

    uvOffset : BoolProperty(
            name="Uv Offset",
            default=False
            )

    rotateUv : BoolProperty(
            name="Rotate Uv Corner",
            default=False
            )
        
    @classmethod
    def poll(cls, context):
        return (context.active_object is not None and
                context.active_object.type == 'MESH' and
                context.active_object.mode == "EDIT")

    def execute(self, context):
        defPasteUvsIsland(self, self.uvOffset, self.rotateUv, context)
        return {'FINISHED'}
