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

bl_info = {
    "name": "Make Thread Mesh",
    "author": "Oscurart",
    "version": (1, 0),
    "blender": (2, 59, 0),
    "location": "Add > Mesh > Thread",
    "description": "Make a thread.",
    "warning": "",
    "wiki_url": "http://oscurart.blogspot.com",
    "tracker_url": "",
    "category": "Object"}


import math
import bpy


def func_osc_screw(self, STRETCH,TURNS,DIAMETER,RESOLUTION):
    # DATA PARA EL MESH
    me = bpy.data.meshes.new("threadData")
    obj = bpy.data.objects.new("Thread", me)
    bpy.context.scene.objects.link(obj)

    # VARIABLES
    vertexlist=[]
    facelist=[]
    facereset=0
    CANTDIV=360/RESOLUTION
    ESPACIODIV=STRETCH/(TURNS+2+RESOLUTION)

    # PARA CADA VERTICE EN EL RANGO DESDE CERO A LENGTH
    for vertice in range(0,TURNS+2+RESOLUTION):
        # SUMA EN LA LISTA UN VERTICE
        vertexlist.append((math.sin(math.radians(vertice*CANTDIV))*DIAMETER,vertice*ESPACIODIV,math.cos(math.radians(vertice*CANTDIV))*DIAMETER))
        if vertice > RESOLUTION:
            facelist.append((vertice-(RESOLUTION),vertice-((RESOLUTION)+1),vertice-1,vertice))

    # CONECTO OBJETO
    me.from_pydata(vertexlist,[],facelist)
    me.update()



class oscMakeScrew (bpy.types.Operator):

    bl_idname = "mesh.primitive_thread_oscurart"
    bl_label = "Add Mesh Thread"
    bl_description = "Create a Thread"
    bl_options = {'REGISTER', 'UNDO'}

    resolution = bpy.props.IntProperty (name="Resolution",default=10,min=3,max=1000)
    stretch = bpy.props.FloatProperty (name="Stretch",default=1,min=0.000001,max=1000)
    turns = bpy.props.IntProperty (name="Turns Steps",default=19,min=0)
    diameter = bpy.props.FloatProperty (name="Diameter",default=1,min=0,max=1000)



    def execute(self, context):
        func_osc_screw(self, self.stretch,self.turns,self.diameter,self.resolution)
        return {'FINISHED'}


# Registration

def add_screw_list(self, context):
    self.layout.operator(
        "mesh.primitive_thread_oscurart",
        text="Thread",
        icon="PLUGIN")

def register():
    bpy.types.INFO_MT_mesh_add.append(add_screw_list)
    bpy.utils.register_class(oscMakeScrew)


def unregister():
    bpy.types.INFO_MT_mesh_add.remove(add_screw_list)
    bpy.utils.unregister_class(oscMakeScrew)


if __name__ == '__main__':
    register()

