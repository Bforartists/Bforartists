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
import os
import bmesh

C = bpy.context
D = bpy.data



# -------------------------- OVERLAP UV ISLANDS

def defCopyUvsIsland(self, context):
    bpy.ops.object.mode_set(mode="OBJECT")
    global obLoop
    global islandFaces
    obLoop = []
    islandFaces = []
    for poly in bpy.context.object.data.polygons:
        if poly.select:
            islandFaces.append(poly.index)
            for li in poly.loop_indices:
                obLoop.append(li)

    bpy.ops.object.mode_set(mode="EDIT")

def defPasteUvsIsland(self, uvOffset, rotateUv,context):
    bpy.ops.object.mode_set(mode="OBJECT")
    selPolys = [poly.index for poly in bpy.context.object.data.polygons if poly.select]

    for island in selPolys:
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.context.object.data.polygons[island].select = True
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_linked()
        bpy.ops.object.mode_set(mode="OBJECT")
        TobLoop = []
        TislandFaces = []
        for poly in bpy.context.object.data.polygons:
            if poly.select:
                TislandFaces.append(poly.index)
                for li in poly.loop_indices:
                    TobLoop.append(li)

        for source,target in zip(range(min(obLoop),max(obLoop)+1),range(min(TobLoop),max(TobLoop)+1)):
            bpy.context.object.data.uv_layers.active.data[target].uv = bpy.context.object.data.uv_layers.active.data[source].uv + Vector((uvOffset,0))

        bpy.ops.object.mode_set(mode="EDIT")

    if rotateUv:
        bpy.ops.object.mode_set(mode="OBJECT")
        for poly in selPolys:
            bpy.context.object.data.polygons[poly].select = True
        bpy.ops.object.mode_set(mode="EDIT")
        bm = bmesh.from_edit_mesh(bpy.context.object.data)
        bmesh.ops.reverse_uvs(bm, faces=[f for f in bm.faces if f.select])
        bmesh.ops.rotate_uvs(bm, faces=[f for f in bm.faces if f.select])
        #bmesh.update_edit_mesh(bpy.context.object.data, tessface=False, destructive=False)



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

