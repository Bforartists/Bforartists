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
import time

C = bpy.context
D = bpy.data


def DefOscOverlapUv(self,offset,rotate):
    me = bpy.context.object.data
    bm = bmesh.from_edit_mesh(me)
    bm.faces.ensure_lookup_table()
    faces = [face for face in bm.faces if face.select]
    uv_layer = bm.loops.layers.uv[bpy.context.object.data.uv_layers.active.name]

    faceDict = {}
    faceReverse = []
    bm.select_mode = {'FACE'}
    for face in faces:
        bpy.ops.mesh.select_all(action="DESELECT")
        face.select = True
        bpy.ops.mesh.select_mirror()
        faceDict[face.index] = [mirrorface for mirrorface in bm.faces if mirrorface.select][0].index
        faceReverse.append([mirrorface for mirrorface in bm.faces if mirrorface.select][0])



    for selFace,mirrorFace in faceDict.items():
        for loop,mirrorLoop in zip(bm.faces[selFace].loops,bm.faces[mirrorFace].loops):
            mirrorLoop.copy_from(loop)
        if offset:
            for loop,mirrorLoop in zip(bm.faces[selFace].loops,bm.faces[mirrorFace].loops):
                mirrorLoop[uv_layer].uv += Vector((1,0))


    #invierto direcciones
    bmesh.ops.reverse_uvs(bm, faces=[f for f in faceReverse])
    bmesh.ops.rotate_uvs(bm, faces=[f for f in faceReverse])
    if rotate:
        bmesh.ops.rotate_uvs(bm, faces=[f for f in faceReverse])

    bmesh.update_edit_mesh(me)


class OscOverlapUv(Operator):
    """Overlaps the uvs on one side of the model symmetry plane. """ \
    """Useful to get more detail on fixed resolution bitmaps"""
    bl_idname = "mesh.overlap_uv_faces"
    bl_label = "Overlap Uvs"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None and
                context.active_object.type == 'MESH')


    offset : BoolProperty(
            default=True,
            name="Offset"
            )
    rotate : BoolProperty(
            default=False,
            name="Rotate"
            )

    def execute(self, context):
        DefOscOverlapUv(self,self.offset,self.rotate)
        return {'FINISHED'}



