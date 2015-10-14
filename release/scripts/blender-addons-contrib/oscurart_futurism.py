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
    "name": "Futurism",
    "author": "Oscurart",
    "version": (1, 2),
    "blender": (2, 63, 0),
    "location": "Object > Futurism",
    "description": "Adds a new Mesh Object",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
        "Scripts/Object/Oscurart_Futurism",
    "tracker_url": "https://developer.blender.org/T31911",
    "category": "Add Mesh"}


import bpy

def object_osc_futurism (self, context,STEP, HOLD):
    ACTOBJ=bpy.context.active_object # OBJETO ACTIVO
    FS=bpy.context.scene.frame_start # FRAME START
    FE=bpy.context.scene.frame_end # FRAME END
    OBJLIST=[] # LISTA PARA OBJETOS ????
    FC=FS # FRAME CURRENT
    OBJNUMBER=1 # SUFIJO DE NUMERO PARA OBJETOS
    STEPINC=0 # NUMERO PARA EVALUAR LOS PASOS
    bpy.context.scene.frame_set(FS)  # SETEO EL FRAME CURRENT
    OBACT = bpy.context.active_object # SETEO EL OBJETO ACTIVO

    ## CREO EMPTY
    bpy.ops.object.add()
    bpy.context.active_object.name = "FuturismContainer"
    EMPTY = bpy.context.active_object

    # SUMO PARAMETERS AL EMPTY
    EMPTY["FUTURISM_HOLDIN"] = 0
    EMPTY["FUTURISM_HOLDOUT"] = 0

    bpy.context.scene.objects.active = OBACT  # RECUPERO OBJETO ACTIVO

    for OBJETO in range((FE+1)-FS):
        if STEPINC == STEP:
            # CREO UN MESH A PARTIR DE OBJETO
            MESH=ACTOBJ.to_mesh(bpy.context.scene, True, 'PREVIEW')
            # CREO OBJETO
            OBJECT=bpy.data.objects.new(ACTOBJ.name[:3]+str(FC), MESH)
            # CONECTO A LA ESCENA
            bpy.context.scene.objects.link(OBJECT)
            # SETEO FRAME CURRENT
            bpy.context.scene.frame_set(FC)
            # MARCO EXPRESIONES PARA VIEW
            OBJECT.driver_add("hide")
            OBJECT.animation_data.drivers[0].driver.variables.new()
            OBJECT.animation_data.drivers[0].driver.variables.new()
            OBJECT.animation_data.drivers[0].driver.variables.new()
            OBJECT.animation_data.drivers[0].driver.expression= "False if frame >= %s+var_001 and frame <= %s+var_002 else True" % (str(FC),str(FC+HOLD))
            OBJECT.animation_data.drivers[0].driver.variables[0].targets[0].id_type = 'SCENE'
            OBJECT.animation_data.drivers[0].driver.variables[0].targets[0].id= bpy.context.scene
            OBJECT.animation_data.drivers[0].driver.variables[0].targets[0].data_path = "current_frame"
            OBJECT.animation_data.drivers[0].driver.variables[1].targets[0].id_type = 'OBJECT'
            OBJECT.animation_data.drivers[0].driver.variables[1].targets[0].id= EMPTY
            OBJECT.animation_data.drivers[0].driver.variables[1].targets[0].data_path = '["FUTURISM_HOLDIN"]'
            OBJECT.animation_data.drivers[0].driver.variables[2].targets[0].id_type = 'OBJECT'
            OBJECT.animation_data.drivers[0].driver.variables[2].targets[0].id= EMPTY
            OBJECT.animation_data.drivers[0].driver.variables[2].targets[0].data_path = '["FUTURISM_HOLDOUT"]'

            # MARCO EXPRESIONES PARA RENDER
            OBJECT.driver_add("hide_render")
            OBJECT.animation_data.drivers[1].driver.variables.new()
            OBJECT.animation_data.drivers[1].driver.variables.new()
            OBJECT.animation_data.drivers[1].driver.variables.new()
            OBJECT.animation_data.drivers[1].driver.expression= "False if frame >= %s+5 and frame <= %s else True" % (str(FC),str(FC+HOLD))
            OBJECT.animation_data.drivers[1].driver.variables[0].targets[0].id_type = 'SCENE'
            OBJECT.animation_data.drivers[1].driver.variables[0].targets[0].id= bpy.context.scene
            OBJECT.animation_data.drivers[1].driver.variables[0].targets[0].data_path = "current_frame"
            OBJECT.animation_data.drivers[1].driver.variables[1].targets[0].id_type = 'OBJECT'
            OBJECT.animation_data.drivers[1].driver.variables[1].targets[0].id= EMPTY
            OBJECT.animation_data.drivers[1].driver.variables[1].targets[0].data_path = '["FUTURISM_HOLDIN"]'
            OBJECT.animation_data.drivers[1].driver.variables[2].targets[0].id_type = 'OBJECT'
            OBJECT.animation_data.drivers[1].driver.variables[2].targets[0].id= EMPTY
            OBJECT.animation_data.drivers[1].driver.variables[2].targets[0].data_path = '["FUTURISM_HOLDOUT"]'
            # RESETEO STEPINC
            STEPINC=0
            # COPIAMOS S R T
            OBJECT.matrix_world=ACTOBJ.matrix_world
            #EMPARENTO
            OBJECT.parent=EMPTY
        # AVANZO STEP Y FRAME
        FC+=1
        STEPINC+=1

# CLASE PARA OPERADOR
class Oscurart_futurism (bpy.types.Operator):
    bl_idname = "object.duplicate_futurism"
    bl_label = "Duplicate Futurism"
    bl_description = "Duplicate object per frame"
    bl_options = {'REGISTER', 'UNDO'}

    scale = bpy.props.IntProperty(name='Step',default=1, min=1, max=1000)

    hold = bpy.props.IntProperty(name='Hold', default=0, min=0)

    @classmethod
    def poll(cls, context):
        return(bpy.context.active_object.type == "MESH" )

    def execute(self, context):
        object_osc_futurism(self, context, self.scale, self.hold)

        return {'FINISHED'}


# Registration

def add_osc_futurism_button(self, context):
    self.layout.operator(
        Oscurart_futurism.bl_idname,
        text="Futurism",
        icon="PLUGIN")


def register():
    bpy.utils.register_class(Oscurart_futurism)
    bpy.types.VIEW3D_MT_object.append(add_osc_futurism_button)


def unregister():
    bpy.utils.unregister_class(Oscurart_futurism)
    bpy.types.VIEW3D_MT_object.remove(add_osc_futurism_button)


if __name__ == '__main__':
    register()
