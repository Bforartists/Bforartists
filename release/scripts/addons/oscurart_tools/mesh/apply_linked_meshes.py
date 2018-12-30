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



def applyLRTEx(self, context):
    actObj = bpy.context.active_object
    actObjMatrixWorld = actObj.matrix_world.copy()
    bpy.ops.object.select_linked(extend=False, type="OBDATA")
    linkedObjects = bpy.context.selected_objects
    linkedObjects.remove(actObj)

    for vert in actObj.data.vertices:
        vert.co = actObjMatrixWorld @ vert.co
        actObj.location = (0,0,0)
        actObj.rotation_euler = (0,0,0)
        actObj.scale = (1,1,1)

    for ob in linkedObjects:     
        ob.matrix_world = ob.matrix_world @ actObj.matrix_world.inverted()


class ApplyLRT(bpy.types.Operator):
    """Apply LRT with linked mesh data"""
    bl_idname = "mesh.apply_linked_meshes"
    bl_label = "Apply LRT with linked meshes"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (context.view_layer.objects.active is not None and
                context.view_layer.objects.active.type == 'MESH')

    def execute(self, context):
        applyLRTEx(self, context)
        return {'FINISHED'}
    
  



