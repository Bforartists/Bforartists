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



def SelDoubles(self, context):
    bm = bmesh.from_edit_mesh(bpy.context.object.data)

    for v in bm.verts:
        v.select = 0

    dictloc = {}

    rd = lambda x: (round(x[0], 4), round(x[1], 4), round(x[2], 4))

    for vert in bm.verts:
        dictloc.setdefault(rd(vert.co), []).append(vert.index)

    for loc, ind in dictloc.items():
        if len(ind) > 1:
            for v in ind:
                bm.verts[v].select = 1

    bpy.context.view_layer.objects.active = bpy.context.view_layer.objects.active


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

    def execute(self, context):
        SelDoubles(self, context)
        return {'FINISHED'}



