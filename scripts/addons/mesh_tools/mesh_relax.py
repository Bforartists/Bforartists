# SPDX-FileCopyrightText: 2010 Fabian Fricke
#
# SPDX-License-Identifier: GPL-2.0-or-later

# Relaxes selected vertices while retaining the shape as much as possible

bl_info = {
    "name": "Relax",
    "author": "Fabian Fricke",
    "version": (1, 2, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Edit Mode Context Menu > Relax ",
    "description": "Relax the selected verts while retaining the shape",
    "warning": "",
    "doc_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
               "Scripts/Modeling/Relax",
    "category": "Mesh",
}

"""
Usage:

Launch from "W-menu" or from "Mesh -> Vertices -> Relax"


Additional links:
    Author Site: http://frigi.designdevil.de
    e-mail: frigi.f {at} gmail {dot} com
"""


import bpy
from bpy.props import IntProperty

def relax_mesh(context):

    # deselect everything that's not related
    for obj in context.selected_objects:
        obj.select_set(False)

    # get active object
    obj = context.active_object

    # duplicate the object so it can be used for the shrinkwrap modifier
    obj.select_set(True) # make sure the object is selected!
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.duplicate()
    target = context.active_object

    # remove all other modifiers from the target
    for m in range(0, len(target.modifiers)):
        target.modifiers.remove(target.modifiers[0])

    context.view_layer.objects.active = obj

    sw = obj.modifiers.new(type='SHRINKWRAP', name='relax_target')
    sw.target = target

    # run smooth operator to relax the mesh
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.vertices_smooth(factor=0.5)
    bpy.ops.object.mode_set(mode='OBJECT')

    # apply the modifier
    bpy.ops.object.modifier_apply(modifier='relax_target')

    # delete the target object
    obj.select_set(False)
    target.select_set(True)
    bpy.ops.object.delete()

    # go back to initial state
    obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')

class Relax(bpy.types.Operator):
    """Relaxes selected vertices while retaining the shape """ \
    """as much as possible"""
    bl_idname = 'mesh.relax'
    bl_label = 'Relax'
    bl_options = {'REGISTER', 'UNDO'}

    iterations: IntProperty(name="Relax iterations",
                default=1, min=0, max=100, soft_min=0, soft_max=10)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH')

    def execute(self, context):
        for i in range(0,self.iterations):
            relax_mesh(context)
        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(Relax.bl_idname, text="Relax")


def register():
    bpy.utils.register_class(Relax)

    bpy.types.VIEW3D_MT_edit_mesh_context_menu.append(menu_func)
    bpy.types.VIEW3D_MT_edit_mesh_vertices.append(menu_func)

def unregister():
    bpy.utils.unregister_class(Relax)

    bpy.types.VIEW3D_MT_edit_mesh_context_menu.remove(menu_func)
    bpy.types.VIEW3D_MT_edit_mesh_vertices.remove(menu_func)

if __name__ == "__main__":
    register()
