# Copyright 2016 Jake Dube
#
# ##### BEGIN GPL LICENSE BLOCK ######
# This file is part of MeshTools.
#
# MeshTools is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# MeshTools is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with MeshTools.  If not, see <http://www.gnu.org/licenses/>.
# ##### END GPL LICENSE BLOCK #####


import bpy
from bpy.types import Panel, Operator, PropertyGroup, Scene
from bpy.utils import register_class, unregister_class
from bpy.props import FloatProperty, PointerProperty


bl_info = {
    "name": "Mesh Tools - Bforartists version",
    "author": "Jake Dube, Reiner Prokein",
    "version": (1, 1, 2),
    "blender": (2, 90, 0),
    "location": "Edit Mode > Mesh menu > Transform > Set Dimensions",
    "description": "Sets dimensions for selected vertices in world coordinates.",
    "category": "Mesh"}


def calc_bounds():
    """Calculates the bounding box for selected vertices. Requires applied scale to work correctly. """
    # for some reason we must change into object mode for the calculations
    mode = bpy.context.object.mode
    bpy.ops.object.mode_set(mode='OBJECT')

    mesh = bpy.context.object.data
    verts = [v for v in mesh.vertices if v.select]
	#bfa - check for selected vertices
    if True in [x.select for x in bpy.context.object.data.vertices]:

        # [+x, -x, +y, -y, +z, -z]
        v = verts[0].co
        bounds = [v.x, v.x, v.y, v.y, v.z, v.z]

        for v in verts:
            if bounds[0] < v.co.x:
                bounds[0] = v.co.x
            if bounds[1] > v.co.x:
                bounds[1] = v.co.x
            if bounds[2] < v.co.y:
                bounds[2] = v.co.y
            if bounds[3] > v.co.y:
                bounds[3] = v.co.y
            if bounds[4] < v.co.z:
                bounds[4] = v.co.z
            if bounds[5] > v.co.z:
                bounds[5] = v.co.z

        bpy.ops.object.mode_set(mode=mode)

        return bounds


def safe_divide(a, b):
    if b != 0:
        return a / b
    return 1


class ED_OT_SetDimensions(Operator):
    bl_label = "Set Dimensions"
    bl_idname = "mesh_tools_addon.set_dimensions"
    bl_description = "Sets dimensions of selected vertices"
    bl_options = {'REGISTER', 'UNDO'}
    bl_context = "editmode"

    new_x : FloatProperty(name="X", min=0, default=1, unit='LENGTH')
    new_y : FloatProperty(name="Y", min=0, default=1, unit='LENGTH')
    new_z : FloatProperty(name="Z", min=0, default=1, unit='LENGTH')

    def invoke(self, context, event):
        bounds = calc_bounds()
	# bfa - added if else. The else is when nothing is selected
        if bounds is not None:
            self.new_x = bounds[0] - bounds[1]
            self.new_y = bounds[2] - bounds[3]
            self.new_z = bounds[4] - bounds[5]
            return {'FINISHED'}
        else:
            self.report({'INFO'},"No geometry selected" ) # bfa - display an info message that there is no geometry selected.
            bpy.ops.object.mode_set(mode='EDIT')
            return {'FINISHED'}

    def execute(self, context):
        bounds = calc_bounds()
        bpy.ops.object.mode_set(mode='EDIT')
        x = safe_divide(self.new_x, (bounds[0] - bounds[1]))
        y = safe_divide(self.new_y, (bounds[2] - bounds[3]))
        z = safe_divide(self.new_z, (bounds[4] - bounds[5]))
        bpy.ops.transform.resize(value=(x, y, z))

        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.label(text = "New dimensions:")
        box.prop(self, "new_x")
        box.prop(self, "new_y")
        box.prop(self, "new_z")


def add_button(self, context):

    if context.mode in {'EDIT_MESH'}:
        self.layout.operator(ED_OT_SetDimensions.bl_idname, icon="PLUGIN")

classes = (
    ED_OT_SetDimensions,
)

def register():
    from bpy.utils import register_class
    for cls in classes:
       register_class(cls)
    bpy.types.VIEW3D_MT_transform.append(add_button)
    bpy.types.VIEW3D_PT_objecttab_transform.append(add_button)


def unregister():
    from bpy.utils import unregister_class
    for cls in classes:
       unregister_class(cls)
    bpy.types.VIEW3D_MT_transform.remove(add_button)
    bpy.types.VIEW3D_PT_objecttab_transform.remove(add_button)


if __name__ == "__main__":
    register()

