# mesh_normalsmooth_7.py Copyright (C) 2010, Dolf Veenvliet
#
# Relaxes selected vertices while retaining the shape as much as possible
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****

bl_info = {
    "name": "Normal Smooth",
    "author": "Dolf Veenvliet",
    "version": (7,),
    "blender": (2, 63, 0),
    "location": "View3D > Specials > Normal Smooth ",
    "description": "Smooth the vertex position based on the normals",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "https://developer.blender.org/T32587",
    "category": "Mesh"}

"""
Usage:

Launch from "W-menu" or from "Mesh -> Vertices -> Normal Smooth"

Additional links:
    Author Site: http://www.macouno.com
    e-mail: dolf {at} macouno {dot} com
"""

import bpy, mathutils, math
from bpy.props import IntProperty

## Rotate one vector (vec1) towards another (vec2)
## (rad = ammount of degrees to rotate in radians)
def RotVtoV(vec1, vec2, rad):
    cross = vec1.cross(vec2)
    mat = mathutils.Matrix.Rotation(rad, 3, cross)
    return (mat * vec1)


# Find the new coordinate for this verticle
def smoothVert(v1, v1in, me):

    v1co = v1.co
    v1no = v1.normal

    # List of verts not to check (don't check against yourself)
    chk = [v1in]
    newCo = []

    # Make sure there's faces, otherwise we do nothing
    if len(me.polygons):

        # Check every face
        for f in me.polygons:

            # Only check faces that this vert is in
            if v1in in f.vertices:

                # Loop through all the verts in the face
                for v2in in f.vertices:

                    # Make sure you check every vert only once
                    if not v2in in chk:

                        chk.append(v2in)

                        v2 = me.vertices[v2in]

                        v2co = v2.co

                        # Get the vector from one vert to the other
                        vTov = v2co - v1co

                        vLen = vTov.length

                        # Use half the distance (actually 0.514 seems to be the specific nr to multiply by... just by experience)
                        vLen *= 0.514

                        # Get the normal rotated 90 degrees (pi * 0.5 = 90 degrees in radians) towards the original vert
                        vNor = RotVtoV(v2.normal, vTov.normalized(), (math.pi * 0.5))

                        # Make the vector the correct length
                        vNor = vNor.normalized() * vLen

                        # Add the vector to the vert position to get the correct coord
                        vNor = v2co + vNor

                        newCo.append(vNor)

    # Calculate the new coord only if there's a result
    if len(newCo):

        nC = mathutils.Vector()

        # Add all the new coordinates together
        for c in newCo:
            nC = nC + c

        # Divide the resulting vector by the total to get the average
        nC = nC / len(newCo)

    # If there's no result, just return the original coord
    else:
        nC = v1co

    return nC


# Base function
def normal_smooth(context):

    ob = context.active_object

    bpy.ops.object.mode_set(mode='OBJECT')

    vNew = {}
    me = ob.data

    # loop through all verts
    for v1 in me.vertices:

        # only smooth selected verts
        if v1.select:

            v1in = v1.index

            # Get the new coords for this vert
            vNew[v1in] = smoothVert(v1, v1in, me)

    # Only if they're anything new, can we apply anything
    if len(vNew):

        # Get the indexes for all verts to adapt
        for k in vNew.keys():

            # Set the vert's new coords
            me.vertices[k].co = vNew[k]

    bpy.ops.object.mode_set(mode='EDIT')

class nsmooth_help(bpy.types.Operator):
	bl_idname = 'help.normal_smooth'
	bl_label = ''

	def draw(self, context):
		layout = self.layout
		layout.label('To use:')
		layout.label('Select A vertex or group of verts.')
		layout.label('Smooth the vertex position based on the normals')


	def execute(self, context):
		return {'FINISHED'}

	def invoke(self, context, event):
		return context.window_manager.invoke_popup(self, width = 300)

class NormalSmooth(bpy.types.Operator):
    """Smoothes verticle position based on vertex normals"""
    bl_idname = 'normal.smooth'
    bl_label = 'Normal Smooth'
    bl_options = {'REGISTER', 'UNDO'}


    iterations = IntProperty(name="Smoothing iterations",
                default=1, min=0, max=100, soft_min=0, soft_max=10)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH')

    def execute(self, context):
        for i in range(0,self.iterations):
            normal_smooth(context)
        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(NormalSmooth.bl_idname, text="Normal Smooth")


def register():
    bpy.utils.register_module(__name__)

    bpy.types.VIEW3D_MT_edit_mesh_specials.append(menu_func)
    bpy.types.VIEW3D_MT_edit_mesh_vertices.append(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.VIEW3D_MT_edit_mesh_specials.remove(menu_func)
    bpy.types.VIEW3D_MT_edit_mesh_vertices.remove(menu_func)

if __name__ == "__main__":
    register()
