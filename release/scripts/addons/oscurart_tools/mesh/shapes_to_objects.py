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
from bpy.types import Operator
from bpy.props import (
            BoolProperty,
            FloatProperty,
            )
import math



class ShapeToObjects(Operator):
    """It creates a new object for every shapekey in the selected object, ideal to export to other 3D software Apps"""
    bl_idname = "object.shape_key_to_objects_osc"
    bl_label = "Shapes To Objects"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (context.view_layer.objects.active is not None and
                context.view_layer.objects.active.type in
                {'MESH', 'SURFACE', 'CURVE'})

    def execute(self, context):
        OBJACT = bpy.context.view_layer.objects.active
        has_keys = hasattr(getattr(OBJACT.data, "shape_keys", None), "key_blocks")
        if has_keys:
            for SHAPE in OBJACT.data.shape_keys.key_blocks[:]:
                print(SHAPE.name)
                bpy.ops.object.shape_key_clear()
                SHAPE.value = 1
                mesh = OBJACT.to_mesh(bpy.context.depsgraph, True, calc_undeformed=False)
                object = bpy.data.objects.new(SHAPE.name, mesh)
                bpy.context.scene.collection.objects.link(object)
        else:
            self.report({'INFO'}, message="Active object doesn't have shape keys")
            return {'CANCELLED'}

        return {'FINISHED'}
