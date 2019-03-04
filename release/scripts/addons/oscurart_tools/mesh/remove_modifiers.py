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


def funcRemoveModifiers(self,context):
    for ob in bpy.context.selected_objects:
        if ob.type == "MESH":
            for mod in ob.modifiers:
                ob.modifiers.remove(mod)

class RemoveModifiers(bpy.types.Operator):
    """Remove all mesh modifiers"""
    bl_idname = "mesh.remove_modifiers"
    bl_label = "Remove Modifiers"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (context.view_layer.objects.active is not None and
                context.view_layer.objects.active.type == 'MESH')


    def execute(self, context):
        funcRemoveModifiers(self,context)
        return {'FINISHED'}



