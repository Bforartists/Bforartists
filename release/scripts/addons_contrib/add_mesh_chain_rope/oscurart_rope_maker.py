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
    "name": "Oscurart Rope Maker",
    "author": "Oscurart",
    "version": (1,1),
    "blender": (2, 56, 0),
    "location": "Add > Curve > Oscurart Rope",
    "description": "Create ropes",
    "warning": "",
    "wiki_url": "oscurart.blogspot.com",
    "tracker_url": "",
    "category": "Object"}



import bpy, math





def makeRope (context, DISTPOS, curvaResU, radius, FE, CUERDAS, stResU,DIAMETRO):

    # CREO DATA , OBJETO Y LO CONECTO A LA ESCENA
    crv= bpy.data.curves.new("CurvaCable", "CURVE")
    obCable=bpy.data.objects.new("Cable",crv)
    bpy.context.scene.objects.link(obCable)

    # SETEO ATRIBUTOS
    crv.dimensions = "3D"
    crv.resolution_u = 10
    crv.resolution_v = 10
    crv.twist_mode = "MINIMUM"

    # LISTA DE COMPONENTES
    coordenadas= [
        (0,radius,0,radius),
        (radius,0,0,radius),
        (0,-radius,0,radius),
        (-radius,0,0,radius)
    ]



    # CREO EL SPLINE
    spline=crv.splines.new("NURBS")
    lencoord= len(coordenadas)
    #print("lencoord--> :"+str(lencoord))
    rango=range(lencoord)
    spline.points.add(lencoord-1)
    for punto in rango:
        spline.points[punto].co = coordenadas[punto]
        #print(punto)


    # MODIFICACIONES DE DATA
    spline.use_cyclic_u = True
    spline.resolution_u = curvaResU
    spline.order_u = 3
    spline.use_endpoint_u = True


    ## ==CREO CADENAS==

    ## DIVIDO EL RADIO POR LA CANTIDAD DE LINEAS Y SETEO UNA LISTA

    GRADOS=[]
    VALORPORPARTE=[]
    DIVISION=360/CUERDAS
    TAJADA=0

    for parte in range(0,CUERDAS):
        GRADOS.append(TAJADA)
        TAJADA+=DIVISION



    for GRAD in GRADOS:


        # VARIABLES
        FC=0
        VARLISTVER=[]

        VARANGLEY=0
        VARANGLEZ=90
        VARPOSX=0
        EDGEINDEX=0
        # DEFINO EL PESO PARA LAS COORDENADAS
        WEIGHT = 1

        while FC < FE:
            ## CREA 3 CADENAS EN 0 90 Y 180 GRADOS
            VARLISTVER.append((VARPOSX, math.sin(math.radians(GRAD))/(1/DIAMETRO) , math.sin(math.radians(GRAD+90))/(1/DIAMETRO),WEIGHT))

            GRAD += 30
            FC += 1
            VARPOSX += DISTPOS



        # CREO DATA , OBJETO Y LO CONECTO A LA ESCENA
        crv= bpy.data.curves.new("curvaData", "CURVE")
        ob=bpy.data.objects.new("Curva",crv)
        bpy.context.scene.objects.link(ob)

        # SETEO ATRIBUTOS
        crv.dimensions = "3D"
        crv.resolution_u = 10
        crv.resolution_v = 10
        crv.twist_mode = "MINIMUM"

        # LISTA DE COMPONENTES
        coordenadas= VARLISTVER



        # CREO EL SPLINE
        spline=crv.splines.new("NURBS")
        lencoord= len(coordenadas)
        #print("lencoord--> :"+str(lencoord))
        rango=range(lencoord)
        spline.points.add(lencoord-1)
        for punto in rango:
            spline.points[punto].co = coordenadas[punto]
            #print(punto)


        # MODIFICACIONES DE DATA
        spline.use_cyclic_u = False
        spline.resolution_u = stResU
        spline.order_u = 3
        spline.use_endpoint_u = True

        ob.data.bevel_object= bpy.data.objects["Cable"]

        #print(VARLISTVER)

#---------------
from bpy.props import *

class OBJECT_OT_add_object(bpy.types.Operator):
    bl_idname="curve.primitive_osc_rope_add"
    bl_label="Oscurart Rope"
    bl_options={'REGISTER','UNDO'}

    strands = IntProperty (name="Strands", default=5 , min=1, max=1000, step=1)
    diameter = FloatProperty (name="Diameter", default=1 , min=0, max=1000)
    distPos= FloatProperty (name="Stretch", default=1 , min=0.01, max=100.0)
    vertices= IntProperty (name="Length", default=10 , min=0, max=1000, step=1)
    distResU= IntProperty (name="Resolution V", default=5 , min=1, max=1000, step=1)
    stResU= IntProperty (name="Resolution U", default=5 , min=1, max=1000, step=1)
    radio= FloatProperty (name="Radius", default=1 , min=0, max=1000)

    def execute(self, context):
        makeRope(context,
            self.distPos,self.distResU,self.radio,self.vertices,self.strands, self.stResU,self.diameter)
        return {'FINISHED'}

# Registration

def oscRopeButton(self, context):
    self.layout.operator(
        OBJECT_OT_add_object.bl_idname,
        text="Oscurart Rope",
        icon="PLUGIN")


def register():
    bpy.utils.register_class(OBJECT_OT_add_object)
    bpy.types.INFO_MT_curve_add.append(oscRopeButton)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_add_object)
    bpy.types.INFO_MT_curve_add.remove(oscRopeButton)


if __name__ == '__main__':
    register()
