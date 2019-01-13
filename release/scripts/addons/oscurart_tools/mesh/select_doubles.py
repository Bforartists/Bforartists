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



def SelDoubles(self, context, distance):
    obj = bpy.context.object
    me = obj.data
    bm = bmesh.from_edit_mesh(me)
    double = bmesh.ops.find_doubles(bm, verts=bm.verts, dist=distance)

    bpy.ops.mesh.select_all(action = 'DESELECT')

    for vertice in double['targetmap']:
        vertice.select = True

    # Switch to vertex select
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')

    # Show the updates in the viewport
    bmesh.update_edit_mesh(me, False)

class SelectDoubles(Operator):
    """Selects duplicated vertex without merge them"""
    bl_idname = "mesh.select_doubles"
    bl_label = "Select Doubles"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (context.view_layer.objects.active is not None and
                context.view_layer.objects.active.type == 'MESH' and
                context.view_layer.objects.active.mode == "EDIT")

    distance : bpy.props.FloatProperty(
        default=.0001,
        name="Distance")

    def execute(self, context):
        SelDoubles(self, context,self.distance)
        return {'FINISHED'}



