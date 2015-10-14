#!/usr/bin/python3
# To change this template, choose Tools | Templates
# and open the template in the editor.
#  ***** GPL LICENSE BLOCK *****
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#  All rights reserved.
#  ***** GPL LICENSE BLOCK *****

bl_info = {
    "name": "Import: Sound to Animation",
    "author": "Vlassius",
    "version": (0, 70),
    "blender": (2, 64, 0),
    "location": "Select a object > Object tab > Import Movement From Wav File",
    "description": "Extract movement from sound file. "
        "See the Object Panel at the end.",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
        "Scripts/Import-Export/Import_Movement_From_Audio_File",
    "tracker_url": "https://developer.blender.org/T23565",
    "category": "Import-Export"}

"""
-- Extract movement from sound file, to help in animation - import script --<br>

- NOTES:
- This script takes a wav file and get sound "movement" to help you in sync the movement to words in the wave file. <br>
- Supported Audio: .wav (wave) 8 bits and 16 bits - mono and multichanel file<br>
- At least Blender 2.64.9 is necessary to run this program.
- Curitiba - Brasil


-v 0.70Beta-
    Included: SmartRender - Render just the frames that has changes
    Included: Options to check SmartRender for Blender Internal Render Engine:LocRotScale, Material, Transp, Mirror
    Included: User can Cancel all functions with CANCEL button- Extensive Code and flux change (bugs expected)
    Included: User can Cancel all functions with ESC
    Inclused: User friendly messages into UI while running (its no more necessary to look at terminal window to most users)
    Cleanup:  Non Stardard Chars in coments
    To Do:    Decrease overhead of timer loops
    To Do:    Try to implement Smart Render for Cycles

-v 0.60Beta-
    Included: Option to use just the beat from the audio sound
    Included: Option to exclude the beat from the audio sound
    Included: More or less sensibility options when using the beat
    Included: Audio Channel Select option

-v 0.50Beta-
    Included: Auto Adjust Audio Sensity option
    Included: 8 bits .wav file support
    Recalibrated: Manual audio sense 1
    Cosmetic: Many changes in panel and terminal window info
    Corrected: Tracker_url
    Corrected: a few bytes in Memory Leaks
    work around: memory leak in function: bpy.ops.transform.rotate
    work around: memory leak in function: bpy.ops.anim.keyframe_insert

-v 0.22Beta-
    Included:
    Camera Rotation
    Empty Location-Rotation-Scale

-v 0.21Beta-
    Changed just the meta informations like version and wiki page.

-v 0.20 Beta-
    New Panel

-v 0.1.5 Beta-
    Change in API-> Properties
    Included the button "Get FPS from Scene" due to a problem to get it in the start
    Return to Frame 1 after import
    Filter .wav type file (by batFINGER)

-v 0.1.4 Beta-
    If choose negative in rotation, auto check the rotation negative to Bones
    change in register()  unregister():

-v 0.1.3 Beta-
    File Cleanup
    Change to bl_info.
    Cosmetic Changes.
    Minor change in API in how to define buttons.
    Adjust in otimization.

-v 0.1.2 Beta
change in API- Update function bpy.ops.anim.keyframe_insert_menu

-v 0.1.1 Beta
change in API- Update property of  window_manager.fileselect_add

-v 0.1.0 Beta
new - Added support to LAMP object
new - improved flow to import
new - check the type of object before show options
bug - option max. and min. values
change- Updated scene properties for changes in property API.
        See http://lists.blender.org/pipermail/bf-committers/2010-September/028654.html
new flow: 1) Process the sound file    2) Show Button to import key frames

- v0.0.4 ALPHA
new - Added destructive optimizer option - LostLestSignificativeDigit lost/total -> 10/255 default
new - Visual Graph to samples
new - Option to just process audio file and do not import - this is to help adjust the audio values
new - Get and show automatically the FPS (in proper field) information taking the information from scene
bug- Display sensitivity +1
bug - Corrected location of the script in description

- v0.0.3
Main change: Corrected to work INSIDE dir /install/linux2/2.53/scripts/addons
Corrected position of label "Rotation Negative"
Added correct way to deal with paths in Python os.path.join - os.path.normpath

- v0.0.2
Corrected initial error (Register() function)
Corrected some labels R. S. L.
Turned off "object field" for now
Changed target default to Z location

- v0.0.1
Initial version

Credit to:
Vlassius

- http://vlassius.com.br
- vlassius@vlassius.com.br
- Curitiba - Brasil

"""

import bpy
from bpy.props import *
#from io_utils import ImportHelper
import wave

#para deixar global
def _Interna_Globals(BytesDadosTotProcess, context):
    global array
    global arrayAutoSense

    array= bytearray(BytesDadosTotProcess)  # cria array
    arrayAutoSense= bytearray((BytesDadosTotProcess)*2)  # cria array para AutoAudioSense
    context.scene.imp_sound_to_anim.bArrayCriado=True

#
#==================================================================================================
# BLENDER UI Panel
#==================================================================================================
#
class VIEW3D_PT_CustomMenuPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_label = "Import Movement From Wav File"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        b=bpy.context.active_object.type=='EMPTY' or bpy.context.active_object.type=='ARMATURE' or \
                                                            bpy.context.active_object.type=='MESH' or \
                                                            bpy.context.active_object.type=='CAMERA' or \
                                                            bpy.context.active_object.type=='LAMP'
        if not b:
            row=layout.row()
            row.label(text="The Selected Object is: type \"" + bpy.context.active_object.type + \
                                                                    "\", and it is not supported.")
            row=layout.row()
            row.label(text="Supported Object are Type: Armature, Mesh, Camera and Lamp")
            row=layout.row()
        else:
            #print(context.scene.imp_sound_to_anim.bTypeImport)
            if context.scene.imp_sound_to_anim.bTypeImport == 0:
                #mount panel to Direct animation
                row=layout.row()
                layout.operator("import.sound_animation_botao_udirect")

            # monta as telas quando está rodando
            elif context.scene.imp_sound_to_anim.Working!="":   #its running
                row=layout.row()
                row=layout.row()

                if context.scene.imp_sound_to_anim.Working== "CheckSmartRender":
                    #context.scene.imp_sound_to_anim.Info_check_smartrender=
                    row=layout.row()
                    row.label(text="Checking for Smart Render...")
                    row=layout.row()
                    row.label(text=context.scene.imp_sound_to_anim.Info_check_smartrender)
                    row=layout.row()

                elif context.scene.imp_sound_to_anim.Working== "SmartRender":
                    #context.scene.imp_sound_to_anim.Info_check_smartrender=
                    row=layout.row()
                    row.label(text="Processing Smart Render...")
                    row=layout.row()
                    row.label(text=context.scene.imp_sound_to_anim.Info_check_smartrender)
                    row=layout.row()

                elif context.scene.imp_sound_to_anim.Working== "ProcessaSom":
                    #context.scene.imp_sound_to_anim.Info_Import=
                    row=layout.row()
                    row.label(text="Processing Sound File...")
                    row=layout.row()
                    row.label(text=context.scene.imp_sound_to_anim.Info_Import)

                elif context.scene.imp_sound_to_anim.Working== "wavimport":
                    #context.scene.imp_sound_to_anim.Info_Import=
                    row=layout.row()
                    row.label(text="Importing Keys...")
                    row=layout.row()
                    row.label(text=context.scene.imp_sound_to_anim.Info_Import)
                    row=layout.row()

                # botao cancel
                layout.operator(OBJECT_OT_Botao_Cancel.bl_idname)
                row=layout.row()

            elif context.scene.imp_sound_to_anim.bTypeImport == 1:
                row=layout.row()
                row.label(text="1)Click button \"Process Wav\",")
                row=layout.row()
                row.label(text="2)Click Button \"Import Key Frames\",")
                row=layout.row()
                row.label(text="Run the animation (alt A) and Enjoy!")
                row=layout.row()
                row.prop(context.scene.imp_sound_to_anim,"action_auto_audio_sense")
                row=layout.row()
                if context.scene.imp_sound_to_anim.action_auto_audio_sense == 0:   # se auto audio sense desligado
                    row.prop(context.scene.imp_sound_to_anim,"audio_sense")
                    row=layout.row()

                else: #somente se autosense ligado
                    if context.scene.imp_sound_to_anim.remove_beat == 0 :
                        row.prop(context.scene.imp_sound_to_anim,"use_just_beat")

                    if context.scene.imp_sound_to_anim.use_just_beat == 0:
                        row.prop(context.scene.imp_sound_to_anim,"remove_beat")

                    if context.scene.imp_sound_to_anim.use_just_beat or context.scene.imp_sound_to_anim.remove_beat:
                        if not context.scene.imp_sound_to_anim.beat_less_sensible and not context.scene.imp_sound_to_anim.beat_more_sensible:
                            row=layout.row()
                        if context.scene.imp_sound_to_anim.beat_less_sensible ==0:
                            row.prop(context.scene.imp_sound_to_anim,"beat_more_sensible")

                        if context.scene.imp_sound_to_anim.beat_more_sensible ==0:
                            row.prop(context.scene.imp_sound_to_anim,"beat_less_sensible")

                row=layout.row()
                row.prop(context.scene.imp_sound_to_anim,"action_per_second")
                row=layout.row()
                row.prop(context.scene.imp_sound_to_anim,"action_escale")

                #row=layout.row()
                row.label(text="Result from 0 to " + str(round(255/context.scene.imp_sound_to_anim.action_escale,4)) + "")

                row=layout.row()
                row.label(text="Property to Change:")
                row.prop(context.scene.imp_sound_to_anim,"import_type")

                #coluna
                row=layout.row()
                row.prop(context.scene.imp_sound_to_anim,"import_where1")
                row.prop(context.scene.imp_sound_to_anim,"import_where2")
                row.prop(context.scene.imp_sound_to_anim,"import_where3")

                row=layout.row()
                row.label(text='Optional Configurations:')
                row=layout.row()

                row.prop(context.scene.imp_sound_to_anim,"frames_per_second")
                row=layout.row()
                #coluna
                column= layout.column()
                split=column.split(percentage=0.5)
                col=split.column()

                row=col.row()
                row.prop(context.scene.imp_sound_to_anim,"frames_initial")

                row=col.row()
                row.prop(context.scene.imp_sound_to_anim,"action_min_value")

                col=split.column()

                row=col.row()
                row.prop(context.scene.imp_sound_to_anim,"optimization_destructive")

                row=col.row()
                row.prop(context.scene.imp_sound_to_anim,"action_max_value")

                row=layout.row()

                row.prop(context.scene.imp_sound_to_anim,"action_offset_x")
                row.prop(context.scene.imp_sound_to_anim,"action_offset_y")
                row.prop(context.scene.imp_sound_to_anim,"action_offset_z")

                row=layout.row()
                row.prop(context.scene.imp_sound_to_anim,"audio_channel_select")
                row.prop(context.scene.imp_sound_to_anim,"action_valor_igual")

                #operator button
                #OBJECT_OT_Botao_Go => Botao_GO
                row=layout.row()
                layout.operator(OBJECT_OT_Botao_Go.bl_idname)

                row=layout.row()
                row.label(text=context.scene.imp_sound_to_anim.Info_Import)

                # preciso garantir a existencia do array porque o Blender salva no arquivo como existente sem o array existir
                try:
                    array
                except NameError:
                    nada=0 #dummy
                else:
                    if context.scene.imp_sound_to_anim.bArrayCriado:
                        layout.operator(OBJECT_OT_Botao_Import.bl_idname)
                        row=layout.row()

                #Layout SmartRender, somente para Blender_render
                if bpy.context.scene.render.engine == "BLENDER_RENDER":
                    row=layout.row()
                    row.label(text="----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")
                    row=layout.row()
                    if context.scene.imp_sound_to_anim.Info_check_smartrender!= "":
                        row=layout.row()
                        row.label(text=context.scene.imp_sound_to_anim.Info_check_smartrender)

                    row=layout.row()
                    row.operator(OBJECT_OT_Botao_Check_SmartRender.bl_idname)
                    if context.scene.imp_sound_to_anim.Info_check_smartrender!= "":
                        row.operator(OBJECT_OT_Botao_SmartRender.bl_idname)

                    row=layout.row()
                    row.prop(context.scene.imp_sound_to_anim,"check_smartrender_loc_rot_sc")
                    row.prop(context.scene.imp_sound_to_anim,"check_smartrender_material_basic")
                    row=layout.row()
                    row.prop(context.scene.imp_sound_to_anim,"check_smartrender_material_transparence")
                    row.prop(context.scene.imp_sound_to_anim,"check_smartrender_material_mirror")

            #-----------------------------
            #Use Driver
            #-----------------------------
            if context.scene.imp_sound_to_anim.bTypeImport == 2:

                row=layout.row()
                row.prop(context.scene.imp_sound_to_anim,"audio_sense")
                row=layout.row()
                row.prop(context.scene.imp_sound_to_anim,"frames_per_second")
                row=layout.row()
                row.prop(context.scene.imp_sound_to_anim,"action_per_second")
                row=layout.row()
                layout.operator(ImportWavFile.bl_idname)


#
#==================================================================================================
# BLENDER UI PropertyGroup
#==================================================================================================
#
class ImpSoundtoAnim(bpy.types.PropertyGroup):

        #Array created
        bArrayCriado = IntProperty(name="",
            description="Avisa que rodou process de som",
            default=0)

        #Script Running
        Working = StringProperty(name="",
            description="Script esta trabalhando",
            maxlen= 1024,
            default="")

        #Nome do objeto
        Info_Import = StringProperty(name="",
            description="Info about Import",
            maxlen= 1024,
            default= "")#this set the initial text

        #Mensagem Smart Render
        Info_check_smartrender = StringProperty(name="",
            description="Smart Render Message",
            maxlen= 1024,
            default= "")#this set the initial text

        #iAudioSensib=0    #sensibilidade volume do audio 0 a 5. Quanto maior, mais sensibilidade
        audio_sense = IntProperty(name="Audio Sens",
            description="Audio Sensibility.",
            min=1,
            max=6,
            step=1,
            default= 1)

        #iFramesPorSeg=15  #Frames por segundo para key frame
        #fps= (bpy.types.Scene) bpy.context.scene.render.fps
        frames_per_second = IntProperty(name="#Frames/s",
            description="Frames you want per second. Better match your set up in Blender scene.",
            min=1,
            max=120,
            step=1)

        #iMovPorSeg=1      #Sensibilidade de movimento. 3= 3 movimentos por segundo
        action_per_second = IntProperty(name="Act/s",
            description="Actions per second. From 1 to #Frames/s",
            min=1,
            max=120,
            step=1,
            default= 4)#this set the initial text

        #iDivScala=200
        #scala do valor do movimento. [se =1 - 0 a 255 ] [se=255 - 0,00000 a 1,00000] [se=1000 - 0 a 0.255]
        action_escale = IntProperty(name="Scale",
            description="Scale the result values. See the text at right side of the field",
            min=1,
            max=99999,
            step=100,
            default= 100)#this set the initial text

        #iMaxValue=255
        action_max_value = IntProperty(name="Clip Max",
            description="Set the max value (clip higher values).",
            min=1,
            max=255,
            step=1,
            default= 255)#this set the initial text

        #iMinValue=0
        action_min_value = IntProperty(name="Clip Min",
            description="Set the min value. (clip lower values)",
            min=0,
            max=255,
            step=1,
            default= 0)#this set the initial text

        #iStartFrame=0#
        frames_initial = IntProperty(name="Frame Ini",
            description="Where to start to put the computed values.",
            min=0,
            max=999999999,
            step=1,
            default= 0)

        audio_channel_select = IntProperty(name="Audio Channel",
            description="Choose the audio channel to use",
            min=1,
            max=10,
            step=1,
            default= 1)

        action_offset_x = FloatProperty(name="XOffset",
            description="Offset X Values",
            min=-999999,
            max=999999,
            step=1,
            default= 0)

        action_offset_y = FloatProperty(name="YOffset",
            description="Offset Y Values",
            min=-999999,
            max=999999,
            step=1,
            default= 0)

        action_offset_z = FloatProperty(name="ZOffset",
            description="Offset Z Values",
            min=-999999,
            max=999999,
            step=1,
            default= 0)

        import_type= EnumProperty(items=(('imp_t_Scale', "Scale", "Apply to Scale"),
                                         ('imp_t_Rotation', "Rotation", "Apply to Rotation"),
                                         ('imp_t_Location', "Location", "Apply to Location")
                                        ),
                                 name="",
                                 description= "Property to Import Values",
                                 default='imp_t_Location')

        import_where1= EnumProperty(items=(('imp_w_-z', "-z", "Apply to -z"),
                                          ('imp_w_-y', "-y", "Apply to -y"),
                                          ('imp_w_-x', "-x", "Apply to -x"),
                                          ('imp_w_z', "z", "Apply to z"),
                                          ('imp_w_y', "y", "Apply to y"),
                                          ('imp_w_x', "x", "Apply to x")
                                        ),
                                 name="",
                                 description= "Where to Import",
                                 default='imp_w_z')

        import_where2= EnumProperty(items=(('imp_w_none', "None", ""),
                                          ('imp_w_-z', "-z", "Apply to -z"),
                                          ('imp_w_-y', "-y", "Apply to -y"),
                                          ('imp_w_-x', "-x", "Apply to -x"),
                                          ('imp_w_z', "z", "Apply to z"),
                                          ('imp_w_y', "y", "Apply to y"),
                                          ('imp_w_x', "x", "Apply to x")
                                        ),
                                 name="",
                                 description= "Where to Import",
                                 default='imp_w_none')

        import_where3= EnumProperty(items=(('imp_w_none', "None", ""),
                                          ('imp_w_-z', "-z", "Apply to -z"),
                                          ('imp_w_-y', "-y", "Apply to -y"),
                                          ('imp_w_-x', "-x", "Apply to -x"),
                                          ('imp_w_z', "z", "Apply to z"),
                                          ('imp_w_y', "y", "Apply to y"),
                                          ('imp_w_x', "x", "Apply to x")
                                        ),
                                 name="",
                                 description= "Where to Import",
                                 default='imp_w_none')


        #========== Propriedades boolean  =============#

        #  INVERTIDO!!!  bNaoValorIgual=True    # nao deixa repetir valores     INVERTIDO!!!
        action_valor_igual = BoolProperty(name="Hard Transition",
            description="Use to movements like a mouth, to a arm movement, maybe you will not use this.",
            default=1)

        action_auto_audio_sense = BoolProperty(name="Auto Audio Sensitivity",
            description="Try to discover best audio scale. ",
            default=1)

        use_just_beat=BoolProperty(name="Just Use The Beat",
            description="Try to use just the beat to extract movement.",
            default=0)

        remove_beat=BoolProperty(name="Remove The Beat",
            description="Try to remove the beat to extract movement.",
            default=0)

        beat_more_sensible=BoolProperty(name="More Sensible",
            description="Try To be more sensible about the beat.",
            default=0)

        beat_less_sensible=BoolProperty(name="Less Sensible",
            description="Try to be less sensible about the beat.",
            default=0)

        check_smartrender_loc_rot_sc=BoolProperty(name="Loc Rot Scale",
            description="Find changes in Location, Rotation and Scale Frame by Frame.",
            default=1)

        check_smartrender_material_basic=BoolProperty(name="Basic Material",
            description="Find changes in basic material settings Frame by Frame.",
            default=1)

        check_smartrender_material_transparence=BoolProperty(name="Material Transparence",
            description="Find changes in material transparence settings Frame by Frame.",
            default=0)

        check_smartrender_material_mirror=BoolProperty(name="Material Mirror",
            description="Find changes in material mirror settings Frame by Frame.",
            default=0)

        timer_reset_func=BoolProperty(name="Reset Counters",
            description="Reset Counters after stop",
            default=0)

        cancel_button_hit=BoolProperty(name="Cancel Hit",
            description="Cancel Hit",
            default=0)

        #  Optimization
        optimization_destructive = IntProperty(name="Optimization",
            description="Hi value = Hi optimization -> Hi loss of information.",
            min=0,
            max=254,
            step=10,
            default= 10)

        # import as driver or direct   NOT IN USE!!
        # not defined
        # Direct=1
        # Driver=2
        bTypeImport = IntProperty(name="",
            description="Import Direct or Driver",
            default=0)

        # globais do dialog open wave
        filter_glob = StringProperty(default="*.wav", options={'HIDDEN'})
        path =        StringProperty(name="File Path", description="Filepath used for importing the WAV file", \
                                                                                        maxlen= 1024, default= "")
        filename =    StringProperty(name="File Name", description="Name of the file")
        directory =   StringProperty(name="Directory", description="Directory of the file")

from bpy.props import *

def WavFileImport(self, context):
    self.layout.operator(ImportWavFile.bl_idname, text="Import a wav file", icon='PLUGIN')


#
#==================================================================================================
# Use Direct
#==================================================================================================
#
class OBJECT_OT_Botao_uDirect(bpy.types.Operator):
    '''Import as Direct Animation'''
    bl_idname = "import.sound_animation_botao_udirect"
    bl_label = "Direct to a Property"

    def execute(self, context):
        context.scene.imp_sound_to_anim.bTypeImport= 1
        if context.scene.imp_sound_to_anim.frames_per_second == 0:
             context.scene.imp_sound_to_anim.frames_per_second= bpy.context.scene.render.fps
        return{'FINISHED'}

    def invoke(self, context, event):
        self.execute(context)
        return {'FINISHED'}

#
#==================================================================================================
# Button - Import
#==================================================================================================
#
class OBJECT_OT_Botao_Import(bpy.types.Operator):
    '''Import Key Frames to Blender'''
    bl_idname = "import.sound_animation_botao_import"
    bl_label = "Import Key Frames"

    RunFrom=0
    iSumImportFrames=0
    iSumOptimizerP1=0
    iSumOptimizerP2=0
    iSumOptimizerP3=0

    def wavimport(context, loop):
        obi=OBJECT_OT_Botao_Import

        # para de entrar no timer
        context.scene.imp_sound_to_anim.Working=""
        #reseta contadores caso seja pedido
        if context.scene.imp_sound_to_anim.timer_reset_func:
            obi.RunFrom=0
            obi.iSumOptimizerP1=0
            obi.iSumOptimizerP2=0
            obi.iSumOptimizerP3=0
            obi.iSumImportFrames=0
            context.scene.imp_sound_to_anim.timer_reset_func=False

        #limita o loop se estiver no fim
        tot=len(array)-1
        if obi.RunFrom+loop > tot:
            loop= tot - obi.RunFrom

        #scala do valor do movimento. [se =1 - 0 a 255 ] [se=255 - 0,00000 a 1,00000] [se=1000 - 0 a 0.255]
        iDivScala= int(context.scene.imp_sound_to_anim.action_escale)

        # nao deixa repetir valores
        bNaoValorIgual=True
        if context.scene.imp_sound_to_anim.action_valor_igual: bNaoValorIgual= False

        # inicia no inicio pedido pelo usuario mais ponteiro RunFrom
        iStartFrame= int(context.scene.imp_sound_to_anim.frames_initial) + obi.RunFrom

        iMaxValue= context.scene.imp_sound_to_anim.action_max_value
        iMinValue= context.scene.imp_sound_to_anim.action_min_value

        bEscala=bRotacao=bEixo=False
        if context.scene.imp_sound_to_anim.import_type=='imp_t_Scale':
            bEscala=True;

        if context.scene.imp_sound_to_anim.import_type=='imp_t_Rotation':
            bRotacao=True;

        if context.scene.imp_sound_to_anim.import_type=='imp_t_Location':
            bEixo=True;

        # atencao, nao eh boolean
        iEixoXneg= iEixoYneg= iEixoZneg=1
        # atencao, nao eh boolean
        iRotationNeg=1
        # atencao, nao eh boolean
        iEscalaYneg= iEscalaZneg= iEscalaXneg=1
        bEixoX=bEixoY=bEixoZ=bEscalaX=bEscalaY=bEscalaZ=bRotationX=bRotationY=bRotationZ=False

        # LOCAL 1
        if context.scene.imp_sound_to_anim.import_where1== 'imp_w_x':
            bEixoX=True
            bEscalaX=True
            bRotationX=True

        if context.scene.imp_sound_to_anim.import_where1== 'imp_w_y':
            bEixoY=True
            bEscalaY=True
            bRotationY=True

        if context.scene.imp_sound_to_anim.import_where1== 'imp_w_z':
            bEixoZ=True
            bEscalaZ=True
            bRotationZ=True

        if context.scene.imp_sound_to_anim.import_where1== 'imp_w_-x':
            bEixoX=True
            bEscalaX=True
            bRotationX=True
            iEixoXneg=-1
            iEscalaXneg=-1
            iRotationNeg=-1

        if context.scene.imp_sound_to_anim.import_where1== 'imp_w_-y':
            bEixoY=True
            bEscalaY=True
            bRotationY=True
            iEixoYneg=-1
            iRotationNeg=-1
            iEscalaYneg=-1

        if context.scene.imp_sound_to_anim.import_where1== 'imp_w_-z':
            bEixoZ=True
            bEscalaZ=True
            bRotationZ=True
            iEixoZneg=-1
            iRotationNeg=-1
            iEscalaZneg=-1


        # LOCAL 2
        if context.scene.imp_sound_to_anim.import_where2== 'imp_w_x':
            bEixoX=True
            bEscalaX=True
            bRotationX=True

        if context.scene.imp_sound_to_anim.import_where2== 'imp_w_y':
            bEixoY=True
            bEscalaY=True
            bRotationY=True

        if context.scene.imp_sound_to_anim.import_where2== 'imp_w_z':
            bEixoZ=True
            bEscalaZ=True
            bRotationZ=True

        if context.scene.imp_sound_to_anim.import_where2== 'imp_w_-x':
            bEixoX=True
            bEscalaX=True
            bRotationX=True
            iEixoXneg=-1
            iEscalaXneg=-1
            iRotationNeg=-1

        if context.scene.imp_sound_to_anim.import_where2== 'imp_w_-y':
            bEixoY=True
            bEscalaY=True
            bRotationY=True
            iEixoYneg=-1
            iRotationNeg=-1
            iEscalaYneg=-1

        if context.scene.imp_sound_to_anim.import_where2== 'imp_w_-z':
            bEixoZ=True
            bEscalaZ=True
            bRotationZ=True
            iEixoZneg=-1
            iRotationNeg=-1
            iEscalaZneg=-1


        # LOCAL 3
        if context.scene.imp_sound_to_anim.import_where3== 'imp_w_x':
            bEixoX=True
            bEscalaX=True
            bRotationX=True

        if context.scene.imp_sound_to_anim.import_where3== 'imp_w_y':
            bEixoY=True
            bEscalaY=True
            bRotationY=True

        if context.scene.imp_sound_to_anim.import_where3== 'imp_w_z':
            bEixoZ=True
            bEscalaZ=True
            bRotationZ=True

        if context.scene.imp_sound_to_anim.import_where3== 'imp_w_-x':
            bEixoX=True
            bEscalaX=True
            bRotationX=True
            iEixoXneg=-1
            iEscalaXneg=-1
            iRotationNeg=-1

        if context.scene.imp_sound_to_anim.import_where3== 'imp_w_-y':
            bEixoY=True
            bEscalaY=True
            bRotationY=True
            iEixoYneg=-1
            iRotationNeg=-1
            iEscalaYneg=-1

        if context.scene.imp_sound_to_anim.import_where3== 'imp_w_-z':
            bEixoZ=True
            bEscalaZ=True
            bRotationZ=True
            iEixoZneg=-1
            iRotationNeg=-1
            iEscalaZneg=-1

        iMinBaseX=iMinScaleBaseX=context.scene.imp_sound_to_anim.action_offset_x
        iMinBaseY=iMinScaleBaseY=context.scene.imp_sound_to_anim.action_offset_y
        iMinBaseZ=iMinScaleBaseZ=context.scene.imp_sound_to_anim.action_offset_z

        #escala inicia com 1 e nao com zero
        iRotationAxisBaseX=context.scene.imp_sound_to_anim.action_offset_x  +1
        iRotationAxisBaseY=context.scene.imp_sound_to_anim.action_offset_y  +1
        iRotationAxisBaseZ=context.scene.imp_sound_to_anim.action_offset_z  +1

        #Added destructive optimizer option - LostLestSignificativeDigit lost/total
        iDestructiveOptimizer=context.scene.imp_sound_to_anim.optimization_destructive

        #limita ou nao o valor - velocidade
        bLimitValue=False

        if iMinValue<0: iMinValue=0
        if iMaxValue>255: iMaxValue=255
        if iMinValue>255: iMinValue=255
        if iMaxValue<0: iMaxValue=0
        if iMinValue!= 0: bLimitValue= True
        if iMaxValue!= 255: bLimitValue= True

        if obi.RunFrom==0:
            print('')
            print("================================================================")
            from time import strftime
            print(strftime("Start Import:  %H:%M:%S"))
            print("================================================================")
            print('')

        ilocationXAnt=0
        ilocationYAnt=0
        ilocationZAnt=0
        iscaleXAnt=0
        iscaleYAnt=0
        iscaleZAnt=0
        iRotateValAnt=0

        # variavel global _Interna_Globals
        if context.scene.imp_sound_to_anim.bArrayCriado:
            for i in range(loop):
                ival=array[i+obi.RunFrom]/iDivScala
                #valor pequeno demais, vai dar zero na hora de aplicar
                if ival < 0.001:
                     array[i+obi.RunFrom]=0
                     ival=0

                # to increase performance and legibility
                arrayI= array[i+obi.RunFrom]
                arrayIP1= array[i+1+obi.RunFrom]
                arrayIL1= array[i-1+obi.RunFrom]

                # opcao de NAO colocar valores iguais sequenciais
                if i>0 and bNaoValorIgual and arrayIL1== arrayI:
                    print("Importing Blender Frame: "+str(i+obi.RunFrom+1)+"\tof "+str(len(array)-1) + \
                                                                            "\t(skipped by optimizer)")
                    obi.iSumOptimizerP3+=1
                else:
                    # otimizacao - nao preciso mais que 2 valores iguais.
                    # pular key frame intermediario - Ex b, a, -, -, -, a
                    # tambem otimiza pelo otimizador com perda
                    # valor atual == anterior e posterior -> pula
                    if i>0 and i< len(array)-1 and abs(arrayI - arrayIL1)<=iDestructiveOptimizer and \
                                                        abs(arrayI - arrayIP1)<=iDestructiveOptimizer:
                            print("Importing Blender Frame: "+str(i+obi.RunFrom+1)+"\tof "+str(len(array)-1) + \
                                                                                    "\t(skipped by optimizer)")
                            if iDestructiveOptimizer>0 and arrayI != arrayIL1 or arrayI != arrayIP1:
                                obi.iSumOptimizerP1+=1
                            else: obi.iSumOptimizerP2+=1
                    else:
                            if bLimitValue:
                                if arrayI > iMaxValue: array[i+obi.RunFrom]=iMaxValue
                                if arrayI < iMinValue: array[i+obi.RunFrom]=iMinValue

                            ival=array[i+obi.RunFrom]/iDivScala
                            #passa para float com somente 3 digitos caso seja float
                            m_ival=ival*1000
                            if int(m_ival) != m_ival:
                                ival= int(m_ival)
                                ival = ival /1000

                            bpy.context.scene.frame_current = i+iStartFrame

                            #precisa fazer objeto ativo
                            if bpy.context.active_object.type=='MESH' or bpy.context.active_object.type=='CAMERA' or \
                                                                            bpy.context.active_object.type=='EMPTY':
                                if bEixo:
                                    if bEixoX: bpy.context.active_object.location.x = ival*iEixoXneg+iMinBaseX
                                    if bEixoY: bpy.context.active_object.location.y = ival*iEixoYneg+iMinBaseY
                                    if bEixoZ: bpy.context.active_object.location.z = ival*iEixoZneg+iMinBaseZ

                                if bEscala:
                                    if bEscalaX: bpy.context.active_object.scale.x = ival*iEscalaXneg+iMinScaleBaseX
                                    if bEscalaY: bpy.context.active_object.scale.y = ival*iEscalaYneg+iMinScaleBaseY
                                    if bEscalaZ: bpy.context.active_object.scale.z = ival*iEscalaZneg+iMinScaleBaseZ

                            # 'ARMATURE' or ('MESH' and bRotacao) or ('CAMERA' and bRotacao) or 'LAMP' or 'EMPTY' and bRotacao)
                            if bpy.context.active_object.type=='ARMATURE' or (bpy.context.active_object.type=='MESH' and bRotacao) or \
                                                                            (bpy.context.active_object.type=='CAMERA' and bRotacao) or \
                                                                            bpy.context.active_object.type=='LAMP' or \
                                                                            (bpy.context.active_object.type=='EMPTY' and bRotacao):

                                    #===========  BONE ===========#
                                    if bpy.context.active_object.type=='ARMATURE':   #precisa ser objeto ativo. Nao achei como passar para editmode
                                        if bpy.context.mode!= 'POSE':    #posemode
                                            bpy.ops.object.posemode_toggle()

                                    #============= ALL ===========#
                                    if bEixo:
                                        if ilocationXAnt!=0 or ilocationYAnt!=0 or ilocationZAnt!=0:

                                            bpy.ops.transform.translate(value=(ilocationXAnt*-1,                ilocationYAnt*-1, \
                                                                                ilocationZAnt*-1),               constraint_axis=(bEixoX, bEixoY,bEixoZ), \
                                                                                constraint_orientation='GLOBAL', mirror=False, \
                                                                                proportional='DISABLED',         proportional_edit_falloff='SMOOTH', \
                                                                                proportional_size=1,             snap=False, \
                                                                                snap_target='CLOSEST',           snap_point=(0, 0, 0), \
                                                                                snap_align=False,               snap_normal=(0, 0, 0), \
                                                                                release_confirm=False)

                                        ilocationX=ilocationY=ilocationZ=0
                                        if bEixoX: ilocationX = ival*iEixoXneg+iMinBaseX
                                        if bEixoY: ilocationY = ival*iEixoYneg+iMinBaseY
                                        if bEixoZ: ilocationZ = ival*iEixoZneg+iMinBaseZ

                                        bpy.ops.transform.translate(value=(ilocationX,                       ilocationY, \
                                                                            ilocationZ),                      constraint_axis=(bEixoX, bEixoY,bEixoZ), \
                                                                            constraint_orientation='GLOBAL',  mirror=False, \
                                                                            proportional='DISABLED',          proportional_edit_falloff='SMOOTH', \
                                                                            proportional_size=1,              snap=False, \
                                                                            snap_target='CLOSEST',            snap_point=(0, 0, 0), snap_align=False, \
                                                                            snap_normal=(0, 0, 0),           release_confirm=False)
                                        ilocationXAnt= ilocationX
                                        ilocationYAnt= ilocationY
                                        ilocationZAnt= ilocationZ

                                    if bEscala:
                                        if iscaleXAnt!=0 or iscaleYAnt!=0 or iscaleZAnt!=0:
                                            tmpscaleXAnt=0
                                            tmpscaleYAnt=0
                                            tmpscaleZAnt=0
                                            if iscaleXAnt: tmpscaleXAnt=1/iscaleXAnt
                                            if iscaleYAnt: tmpscaleYAnt=1/iscaleYAnt
                                            if iscaleZAnt: tmpscaleZAnt=1/iscaleZAnt

                                            bpy.ops.transform.resize(value=(tmpscaleXAnt,                    tmpscaleYAnt, \
                                                                            tmpscaleZAnt ),                   constraint_axis=(False, False, False), \
                                                                            constraint_orientation='GLOBAL',  mirror=False, \
                                                                            proportional='DISABLED',          proportional_edit_falloff='SMOOTH', \
                                                                            proportional_size=1, snap=False, snap_target='CLOSEST', \
                                                                            snap_point=(0, 0, 0),             snap_align=False, \
                                                                            snap_normal=(0, 0, 0),            release_confirm=False)

                                        iscaleX=iscaleY=iscaleZ=0
                                        if bEscalaX: iscaleX = ival*iEscalaXneg+iMinScaleBaseX
                                        if bEscalaY: iscaleY = ival*iEscalaYneg+iMinScaleBaseY
                                        if bEscalaZ: iscaleZ = ival*iEscalaZneg+iMinScaleBaseZ

                                        bpy.ops.transform.resize(value=(iscaleX,                        iscaleY, \
                                                                        iscaleZ),                        constraint_axis=(False, False, False), \
                                                                        constraint_orientation='GLOBAL', mirror=False, \
                                                                        proportional='DISABLED',         proportional_edit_falloff='SMOOTH', \
                                                                        proportional_size=1,             snap=False, \
                                                                        snap_target='CLOSEST',           snap_point=(0, 0, 0), \
                                                                        snap_align=False,               snap_normal=(0, 0, 0), \
                                                                        release_confirm=False)
                                        iscaleXAnt= iscaleX
                                        iscaleYAnt= iscaleY
                                        iscaleZAnt= iscaleZ

                                    if bRotacao:
                                        if iRotateValAnt!=0:
                                            bpy.context.active_object.rotation_euler= ((iRotateValAnt*-1)+    iRotationAxisBaseX) *bRotationX , \
                                                                                        ((iRotateValAnt*-1)+  iRotationAxisBaseY) *bRotationY , \
                                                                                        ((iRotateValAnt*-1)+  iRotationAxisBaseZ) *bRotationZ

                                        bpy.context.active_object.rotation_euler= ((ival*iRotationNeg)+   iRotationAxisBaseX) * bRotationX, \
                                                                                    ((ival*iRotationNeg)+ iRotationAxisBaseY)  * bRotationY, \
                                                                                    ((ival*iRotationNeg)+ iRotationAxisBaseZ)  * bRotationZ
                                        iRotateValAnt= ival*iRotationNeg

                            ob = bpy.context.active_object

                            if bEixo:
                                ob.keyframe_insert(data_path="location")

                            if bRotacao:
                                ob.keyframe_insert(data_path="rotation_euler")

                            if bEscala:
                                ob.keyframe_insert(data_path="scale")

                            print("Importing Blender Frame: "+str(i+obi.RunFrom+1)+"\tof "+str(len(array)-1) + "\tValue: "+ str(ival))

                            obi.iSumImportFrames+=1
                    # Fim do ELSE otimizador
                # Fim bNaoValorIgual

            if obi.RunFrom>= tot:
                bpy.context.scene.frame_current = 1
                context.scene.imp_sound_to_anim.Info_Import="Done. Imported " + str(obi.iSumImportFrames) + " Frames"
                from time import strftime
                print('')
                print("================================================================")
                print("Imported: " +str(obi.iSumImportFrames) + " Key Frames")
                print("Optimizer Pass 1 prepared to optimize: " +str(obi.iSumOptimizerP1) + " blocks of Frames")
                print("Optimizer Pass 2 has optimized: " +str(obi.iSumOptimizerP2) + " Frames")
                print("Optimizer Pass 3 has optimized: " +str(obi.iSumOptimizerP3) + " Frames")
                print("Optimizer has optimized: " +str(obi.iSumOptimizerP1 + obi.iSumOptimizerP2 + obi.iSumOptimizerP3) + " Frames")
                print(strftime("End Import:  %H:%M:%S - by Vlassius"))
                print("================================================================")
                print('')
                obi.RunFrom=0
                obi.iSumImportFrames=0
                obi.iSumOptimizerP1=0
                obi.iSumOptimizerP2=0
                obi.iSumOptimizerP3=0
                return obi.RunFrom
            else:
                obi.RunFrom+= loop
                context.scene.imp_sound_to_anim.Info_Import="Processing Frame " + str(obi.RunFrom+loop) + \
                                                                            " of " + str(tot-1) + " Frames"
                return obi.RunFrom


    def execute(self, context):
        #wavimport(context)
        #return{'FINISHED'}
        context.scene.imp_sound_to_anim.Working= "wavimport"
        bpy.ops.wm.modal_timer_operator()

    def invoke(self, context, event):
        self.execute(context)
        return {'FINISHED'}



#
#==================================================================================================
# Button - Sound Process
#==================================================================================================
#
class OBJECT_OT_Botao_Go(bpy.types.Operator):
    ''''''
    bl_idname = "import.sound_animation_botao_go"
    # change in API
    bl_description = "Process a .wav file, take movement from the sound and import to the scene as Key"
    bl_label = "Process Wav"

    filter_glob = StringProperty(default="*.wav", options={'HIDDEN'})
    path = StringProperty(name="File Path", description="Filepath used for importing the WAV file", \
                                                                            maxlen= 1024, default= "")
    filename = StringProperty(name="File Name", description="Name of the file")
    directory = StringProperty(name="Directory", description="Directory of the file")

    RunFrom=0
    Wave_read=0
    MaxAudio=0


    def SoundConv(File, DivSens, Sensibil, Resol, context, bAutoSense, bRemoveBeat, bUseBeat, bMoreSensible, \
                                                                            bLessSensible, AudioChannel, loop):
        obg= OBJECT_OT_Botao_Go
        #reseta contadores caso seja pedido
        if context.scene.imp_sound_to_anim.timer_reset_func:
            obc.RunFrom=0
            Wave_read=0
            MaxAudio=0
            context.scene.imp_sound_to_anim.timer_reset_func=False

        #abre arquivo se primeira rodada
        if obg.RunFrom==0:
            try:
                obg.Wave_read= wave.open(File, 'rb')
            except IOError as e:
                print("File Open Error: ", e)
                return False

        NumCh=      obg.Wave_read.getnchannels()
        SampW=      obg.Wave_read.getsampwidth() # 8, 16, 24 32 bits
        FrameR=     obg.Wave_read.getframerate()
        NumFr=      obg.Wave_read.getnframes()
        ChkCompr=   obg.Wave_read.getcomptype()

        if ChkCompr != "NONE":
            print('Sorry, this compressed Format is NOT Supported ', ChkCompr)
            context.scene.imp_sound_to_anim.Info_Import= "Sorry, this compressed Format is NOT Supported "
            return False

        if SampW > 2:
            context.scene.imp_sound_to_anim.Info_Import= "Sorry, supported .wav files 8 and 16 bits only"
            print('Sorry, supported .wav files 8 and 16 bits only')
            return False

        context.scene.imp_sound_to_anim.Info_Import=""

        # controla numero do canal
        if AudioChannel > NumCh:
            if obg.RunFrom==0:
                print("Channel number " + str(AudioChannel) + " is selected but this audio file has just " + \
                                                            str(NumCh) + " channels, so selecting channel " \
                                                                                            + str(NumCh) + "!")
            AudioChannel = NumCh

        # apenas para por na tela
        tmpAudioChannel= AudioChannel

        #used in index sum to find the channe, adjust to first byte sample index
        AudioChannel -= 1

        # se dois canais, AudioChannel=4 porque sao 4 bytes
        if SampW ==2:  AudioChannel*=2

        # usado para achar contorno da onda - achando picos
        # numero de audio frames para cada video frame
        BytesResol= int(FrameR/Resol)

        # com 8 bits/S - razao Sample/s por resolucao
        # tamanho do array
        BytesDadosTotProcess= NumFr // BytesResol

        if obg.RunFrom==0:   # primeira rodada
            # inicia array
            _Interna_Globals(BytesDadosTotProcess, context)
            print('')
            print("================================================================")
            from time import strftime
            print(strftime("Go!  %H:%M:%S"))
            print("================================================================")
            print('')
            print('Total Audio Time: \t ' + str(NumFr//FrameR) + 's (' + str(NumFr//FrameR//60) + 'min)')
            print('Total # Interactions: \t', BytesDadosTotProcess)
            print('Total Audio Frames: \t', NumFr)
            print('Frames/s: \t\t ' + str(FrameR))
            print('# Chanels in File: \t', NumCh)
            print('Channel to use:\t\t', tmpAudioChannel)
            print('Bit/Sample/Chanel: \t ' + str(SampW*8))
            print('# Frames/Act: \t\t', DivSens)

            if bAutoSense==0:
                print('Audio Sensitivity: \t', Sensibil+1)
            else:
                print('Using Auto Audio Sentivity. This is pass 1 of 2.')

            print('')
            print ("Sample->[value]\tAudio Frame #   \t\t[Graph Value]")

        if obg.RunFrom==0 and bAutoSense!=0:
            Sensibil=0  # if auto sense, Sensibil must be zero here
            obg.MaxAudio=0  # valor maximo de audio encontrado

        # verifica limite total do audio
        looptot= int(BytesDadosTotProcess // DivSens)
        if obg.RunFrom+loop > looptot:
            loop= looptot-obg.RunFrom

        j=0  # usado de indice
        # laco total leitura bytes
        # armazena dado de pico
        for jj in range(loop):
            # caso de 2 canais (esterio)
            # uso apenas 2 bytes em 16 bits, ie, apenas canal esquerdo
            # [0] e [1] para CH L
            # [2] e [3] para CH R   and so on
            # mono:1 byte to 8 bits, 2 bytes to 16 bits
            # sterio: 2 byte to 8 bits, 4 bytes to 16 bits
            ValorPico=0
            # leio o numero de frames de audio para cada frame de video, valor em torno de 1000
            for i in range(BytesResol):
                #loop exterior copia DivSens frames a cada frame calculado
                frame = obg.Wave_read.readframes(DivSens)

                if len(frame)==0: break

                if bAutoSense==0:    # AutoAudioSense Desligado
                    if SampW ==1:
                        if Sensibil ==5:
                            frame0= frame[AudioChannel] << 6 & 255

                        elif Sensibil ==4:
                            frame0= frame[AudioChannel] << 5 & 255

                        elif Sensibil ==3:
                            frame0= frame[AudioChannel] << 4 & 255

                        elif Sensibil ==2:
                            frame0= frame[AudioChannel] << 3 & 255

                        elif Sensibil ==1:
                            frame0= frame[AudioChannel] << 2 & 255

                        elif Sensibil ==0:
                            frame0= frame[AudioChannel]

                        if frame0> ValorPico:
                            ValorPico= frame0

                    if SampW ==2:   # frame[0] baixa       frame[1] ALTA BIT 1 TEM SINAL!
                        if frame[1+AudioChannel] <127:    # se bit1 =0, usa o valor - se bit1=1 quer dizer numero negativo
                            if Sensibil ==0:
                                frame0= frame[1+AudioChannel]

                            elif Sensibil ==4:
                                frame0= ((frame[AudioChannel] & 0b11111100) >> 2) | ((frame[1+AudioChannel] & 0b00000011) << 6)

                            elif Sensibil ==3:
                                frame0= ((frame[AudioChannel] & 0b11110000) >> 4) | ((frame[1+AudioChannel] & 0b00001111) << 4)

                            elif Sensibil ==2:
                                frame0= ((frame[AudioChannel] & 0b11100000) >> 5) | ((frame[1+AudioChannel] & 0b00011111) << 3)

                            elif Sensibil ==1:
                                frame0= ((frame[AudioChannel] & 0b11000000) >> 6) | ((frame[1+AudioChannel] & 0b00111111) << 2)

                            elif Sensibil ==5:
                                frame0=frame[AudioChannel]

                            if frame0 > ValorPico:
                                ValorPico= frame0

                else:   # AutoAudioSense Ligado
                    if SampW ==1:
                        if frame[AudioChannel]> obg.MaxAudio:
                            obg.MaxAudio = frame[AudioChannel]

                        if frame[AudioChannel]> ValorPico:
                            ValorPico=frame[AudioChannel]

                    if SampW ==2:
                        if frame[1+AudioChannel] < 127:
                            tmpValorPico= frame[1+AudioChannel] << 8
                            tmpValorPico+=  frame[AudioChannel]

                            if tmpValorPico > obg.MaxAudio:
                                obg.MaxAudio = tmpValorPico

                            if tmpValorPico > ValorPico:
                                ValorPico= tmpValorPico

            if bAutoSense==0:    #autoaudiosense desligado
                # repito o valor de frames por actions (OTIMIZAR)
                for ii in range(DivSens):
                    array[j+obg.RunFrom]=ValorPico  # valor de pico encontrado
                    j +=1           # incrementa indice prox local
            else:
                idx=obg.RunFrom*2 # porque sao dois bytes
                arrayAutoSense[j+idx]= (ValorPico & 0b0000000011111111) #copia valores baixos
                arrayAutoSense[j+1+idx]= (ValorPico & 0b1111111100000000) >> 8   #copia valores altos
                j+=2

            if bAutoSense==0:    #autoaudiosense desligado
                igraph= ValorPico//10
            else:
                if SampW ==2:
                    igraph= ValorPico//1261

                else:
                    igraph= ValorPico//10

            stgraph="["
            for iii in range(igraph):
                stgraph+="+"

            for iiii in range(26-igraph):
                stgraph+=" "
            stgraph+="]"

            print ("Sample-> " + str(ValorPico) + "\tAudio Frame #  " + str(jj+obg.RunFrom) + " of " + str(looptot-1) + "\t"+ stgraph)

        # acabou primeira fase roda toda de uma vez
        if obg.RunFrom+loop == looptot:
            if bAutoSense==1:
                print("")
                print("================================================================")
                print('Calculating Auto Audio Sentivity, pass 2 of 2.')
                print("================================================================")

                # caso usar batida, procurar por valores proximos do maximo e zerar restante.
                # caso retirar batida, zerar valores proximos do maximo
                UseMinim=0
                UseMax=0

                if bUseBeat==1:
                    print("Trying to use just the beat.")
                    UseMinim= obg.MaxAudio*0.8
                    if bMoreSensible:
                        UseMinim= obg.MaxAudio*0.7
                    elif bLessSensible:
                        UseMinim= obg.MaxAudio*0.9

                if bRemoveBeat==1:
                    print("Trying to exclude the beat.")
                    UseMax= obg.MaxAudio*0.7
                    if bMoreSensible:
                        UseMax= obg.MaxAudio*0.8
                    elif bLessSensible:
                        UseMax= obg.MaxAudio*0.7

                print("")
                # para transformar 15 bits em 8 calibrando valor maximo -> fazer regra de 3
                # obg.MaxAudio -> 255
                # outros valores => valor calibrado= (255 * Valor) / obg.MaxAudio
                scale= 255/obg.MaxAudio

                j=0
                jj=0
                print ("Sample->[value]\tAudio Frame #    \t\t[Graph Value]")

                for i in range(BytesDadosTotProcess // DivSens):

                    ValorOriginal= arrayAutoSense[j+1] << 8
                    ValorOriginal+= arrayAutoSense[j]

                    if bUseBeat==1:
                        if ValorOriginal < UseMinim:
                            ValorOriginal = 0

                    elif bRemoveBeat==1:
                        if ValorOriginal > UseMax:
                            ValorOriginal = 0

                    ValorOriginal= ((round(ValorOriginal * scale)) & 0b11111111)    #aplica a escala

                    for ii in range(DivSens):
                        array[jj] = ValorOriginal
                        jj += 1   # se autoaudiosense, o array tem dois bytes para cada valor

                    j+=2
                    igraph= round(array[jj-1]/10)
                    stgraph="["
                    for iii in range(igraph):
                        stgraph+="+"

                    for iiii in range(26-igraph):
                        stgraph+=" "
                    stgraph+="]"
                    print ("Sample-> " + str(array[jj-1]) + "\tAudio Frame #  " + str(i) + " of " + str(looptot-1) + "\t"+ stgraph)

                #limpa array tmp
                del arrayAutoSense[:]

            # mensagens finais
            context.scene.imp_sound_to_anim.Info_Import= "Click \"Import Key frames\" to begin import" #this set the initial text

            print("================================================================")
            from time import strftime
            print(strftime("End Process:  %H:%M:%S"))
            print("================================================================")

            try:
                obg.Wave_read.close()
            except:
                print('File Close Error')

            obg.RunFrom=0
            return obg.RunFrom   # acabou tudo

        else:#ainda nao acabou o arquivo todo if RunFrom+loop = looptot:
            context.scene.imp_sound_to_anim.Info_Import="Processing " + str(obg.RunFrom) + " of " + str(looptot) +" Audio Frames"
            # force update info text in UI
            bpy.context.scene.frame_current= bpy.context.scene.frame_current
            obg.RunFrom+=loop
            return obg.RunFrom




    def ProcessaSom(context, loop):
        obg= OBJECT_OT_Botao_Go
        # para de entrar o timer
        context.scene.imp_sound_to_anim.Working=""
        #reseta contadores caso seja pedido
        if context.scene.imp_sound_to_anim.timer_reset_func:
            obg.RunFrom=0
            context.scene.imp_sound_to_anim.timer_reset_func=False

        import os
        f= os.path.join(context.scene.imp_sound_to_anim.directory, context.scene.imp_sound_to_anim.filename)
        f= os.path.normpath(f)

        if obg.RunFrom==0:
            print ("")
            print ("")
            print ("Selected file = ",f)
        checktype = f.split('\\')[-1].split('.')[1]
        if checktype.upper() != 'WAV':
            print ("ERROR!! Selected file = ", f)
            print ("ERROR!! Its not a .wav file")
            return

        #sensibilidade volume do audio 0 a 5. Quanto maior, mais sensibilidade
        iAudioSensib= int(context.scene.imp_sound_to_anim.audio_sense)-1
        if iAudioSensib <0: iAudioSensib=0
        elif iAudioSensib>5: iAudioSensib=5

        #act/s nao pode se maior que frames/s
        if context.scene.imp_sound_to_anim.action_per_second > context.scene.imp_sound_to_anim.frames_per_second:
            context.scene.imp_sound_to_anim.action_per_second = context.scene.imp_sound_to_anim.frames_per_second

        #Frames por segundo para key frame
        iFramesPorSeg= int(context.scene.imp_sound_to_anim.frames_per_second)

        #Sensibilidade de movimento. 3= 3 movimentos por segundo
        iMovPorSeg= int(context.scene.imp_sound_to_anim.action_per_second)

        #iDivMovPorSeg Padrao - taxa 4/s ou a cada 0,25s  => iFramesPorSeg/iDivMovPorSeg= ~0.25
        for i in range(iFramesPorSeg):
            iDivMovPorSeg=iFramesPorSeg/(i+1)
            if iFramesPorSeg/iDivMovPorSeg >=iMovPorSeg:
                break

        bRemoveBeat=    context.scene.imp_sound_to_anim.remove_beat
        bUseBeat=       context.scene.imp_sound_to_anim.use_just_beat
        bLessSensible=  context.scene.imp_sound_to_anim.beat_less_sensible
        bMoreSensible=  context.scene.imp_sound_to_anim.beat_more_sensible
        AudioChannel=   context.scene.imp_sound_to_anim.audio_channel_select

        # chama funcao de converter som, retorna preenchendo _Interna_Globals.array
        index= OBJECT_OT_Botao_Go.SoundConv(f, int(iDivMovPorSeg), iAudioSensib, iFramesPorSeg, context, \
                                    context.scene.imp_sound_to_anim.action_auto_audio_sense, bRemoveBeat, \
                                    bUseBeat, bMoreSensible, bLessSensible, AudioChannel, loop)
        return index


    def execute(self, context):

        # copia dados dialof open wave
        context.scene.imp_sound_to_anim.filter_glob= self.filter_glob
        context.scene.imp_sound_to_anim.path = self.path
        context.scene.imp_sound_to_anim.filename = self.filename
        context.scene.imp_sound_to_anim.directory = self.directory

        context.scene.imp_sound_to_anim.Working= "ProcessaSom"
        bpy.ops.wm.modal_timer_operator()
        #ProcessaSom(context)
        return{'FINISHED'}

    def invoke(self, context, event):
        #need to set a path so so we can get the file name and path
        wm = context.window_manager
        wm.fileselect_add(self)

        return {'RUNNING_MODAL'}


#
#==================================================================================================
# Button - Check Smart Render
#==================================================================================================
#
class OBJECT_OT_Botao_Check_SmartRender(bpy.types.Operator):
    '''Check for Reduction'''
    bl_idname = "import.sound_animation_botao_check_smartrender"
    bl_label = "Check Smart Render"

    RunFrom=0
    Frames_Renderizar=0
    Frames_Pular=0

    def CheckSmartRender(context, loop):
        obc= OBJECT_OT_Botao_Check_SmartRender

        #reseta contadores caso seja pedido
        if context.scene.imp_sound_to_anim.timer_reset_func:
            obc.RunFrom=0
            obc.Frames_Pular=0
            obc.Frames_Renderizar=0
            context.scene.imp_sound_to_anim.timer_reset_func=False

        if obc.RunFrom==0:
            if loop !=1: # loop==1 quando estou chamando de dentro da funcao render
                print("")
                print("================================================================")
                print('Running Check Smart Render...')

        #garante ao menos locrotscale ligado
        if context.scene.imp_sound_to_anim.check_smartrender_loc_rot_sc==False and \
                        context.scene.imp_sound_to_anim.check_smartrender_material_basic==False and \
                        context.scene.imp_sound_to_anim.check_smartrender_material_transparence==False and \
                        context.scene.imp_sound_to_anim.check_smartrender_material_mirror==False:
            context.scene.imp_sound_to_anim.check_smartrender_loc_rot_sc=True

        chkLocRotSc=  context.scene.imp_sound_to_anim.check_smartrender_loc_rot_sc
        chkMatBas=    context.scene.imp_sound_to_anim.check_smartrender_material_basic
        chkMatTransp= context.scene.imp_sound_to_anim.check_smartrender_material_transparence
        chkMatMirror= context.scene.imp_sound_to_anim.check_smartrender_material_mirror

        ToRender=[]
        origloop=loop
        from copy import copy
        RunMax= bpy.context.scene.frame_end - bpy.context.scene.frame_start+1
        if obc.RunFrom+loop > RunMax:
            loop= RunMax-obc.RunFrom
            if loop<=0:   #acabou
                if origloop !=1: # loop==1 quando estou chamando de dentro da funcao render
                    print("")
                    print("Frames to copy: " + str(obc.Frames_Pular) + " Frames to really render= " + str(obc.Frames_Renderizar))
                    print("================================================================")
                    print("")
                obc.RunFrom=0
                obc.Frames_Pular=0
                obc.Frames_Renderizar=0
                return (ToRender, obc.RunFrom)

        #move para o primeiro frame a renderizar
        #RunFrom inicia em zero - frames inicia em 1
        bpy.context.scene.frame_current = obc.RunFrom+bpy.context.scene.frame_start

        for k in range(loop):
            if obc.RunFrom==0 and k==0: #primeiro sempre renderiza
                ToRender.append(bpy.context.scene.frame_current)
                obc.Frames_Renderizar+=1
                bpy.context.scene.frame_set(bpy.context.scene.frame_current + 1)
            else:
                if origloop !=1: # loop==1 quando estou chamando de dentro da funcao render
                    import sys
                    sys.stdout.write("\rChecking Frame "+str(bpy.context.scene.frame_current) + "  ")
                    sys.stdout.flush()
                #buffer de todos os objetos
                a=[]
                for obj in bpy.data.objects:
                    if chkLocRotSc:
                        # loc rot scale
                        a.append(copy(obj.location))
                        a.append(copy(obj.rotation_euler))
                        a.append(copy(obj.scale))
                    if hasattr(obj.data, 'materials') and obj.data.materials.keys()!=[] :
                        if bpy.context.scene.render.engine == "BLENDER_RENDER":
                            #pega somente primeiro material sempre
                            if chkMatBas:
                                # cores
                                a.append(copy(obj.data.materials[0].type))
                                a.append(copy(obj.data.materials[0].emit))
                                a.append(copy(obj.data.materials[0].diffuse_color))
                                a.append(copy(obj.data.materials[0].diffuse_intensity))
                                a.append(copy(obj.data.materials[0].specular_intensity))
                                a.append(copy(obj.data.materials[0].specular_color))
                                a.append(copy(obj.data.materials[0].alpha))
                                a.append(copy(obj.data.materials[0].diffuse_shader))
                                a.append(copy(obj.data.materials[0].specular_shader))
                                a.append(copy(obj.data.materials[0].specular_hardness))

                            if chkMatTransp:
                                # transp
                                a.append(copy(obj.data.materials[0].transparency_method))
                                a.append(copy(obj.data.materials[0].specular_alpha))
                                a.append(copy(obj.data.materials[0].raytrace_transparency.fresnel))
                                a.append(copy(obj.data.materials[0].raytrace_transparency.ior))
                                a.append(copy(obj.data.materials[0].raytrace_transparency.filter))
                                a.append(copy(obj.data.materials[0].raytrace_transparency.depth))
                                a.append(copy(obj.data.materials[0].translucency))
                                a.append(copy(obj.data.materials[0].specular_alpha))

                            if chkMatMirror:
                                #mirror
                                a.append(copy(obj.data.materials[0].raytrace_mirror.reflect_factor))
                                a.append(copy(obj.data.materials[0].raytrace_mirror.fresnel))
                                a.append(copy(obj.data.materials[0].raytrace_mirror.fresnel_factor))
                                a.append(copy(obj.data.materials[0].mirror_color))
                                a.append(copy(obj.data.materials[0].raytrace_mirror.depth))
                                a.append(copy(obj.data.materials[0].raytrace_mirror.gloss_factor))

                # tenho todos os objetos em a[]
                # incrementar um frame e checar se eh igual
                bpy.context.scene.frame_set(bpy.context.scene.frame_current + 1)

                j=0
                dif=0
                for obj in bpy.data.objects:
                    if chkLocRotSc:
                        if a[j]!= obj.location or a[j+1]!= obj.rotation_euler or a[j+2]!= obj.scale:
                            dif=1
                            #break
                        j+=3

                    if hasattr(obj.data, 'materials') and obj.data.materials.keys()!=[] :
                        if bpy.context.scene.render.engine == "BLENDER_RENDER":
                            if chkMatBas:
                                # cores
                                if a[j]!= obj.data.materials[0].type or   a[j+1]!= obj.data.materials[0].emit or \
                                                                            a[j+2]!= obj.data.materials[0].diffuse_color or \
                                                                            a[j+3]!= obj.data.materials[0].diffuse_intensity or \
                                                                            a[j+4]!= obj.data.materials[0].specular_intensity or \
                                                                            a[j+5]!= obj.data.materials[0].specular_color or \
                                                                            a[j+6]!= obj.data.materials[0].alpha or \
                                                                            a[j+7]!= obj.data.materials[0].diffuse_shader or \
                                                                            a[j+8]!= obj.data.materials[0].specular_shader or \
                                                                            a[j+9]!= obj.data.materials[0].specular_hardness:
                                    dif=1
                                    print("mat")
                                    j+= 10  # ajusta ponteiro j
                                    if chkMatTransp: j+=8
                                    if chkMatMirror: j+=6
                                    break
                                j+=10

                            if chkMatTransp:
                                #transp
                                if a[j]!= obj.data.materials[0].transparency_method or    a[j+1]!= obj.data.materials[0].specular_alpha or \
                                                                                            a[j+2]!= obj.data.materials[0].raytrace_transparency.fresnel or \
                                                                                            a[j+3]!= obj.data.materials[0].raytrace_transparency.ior or \
                                                                                            a[j+4]!= obj.data.materials[0].raytrace_transparency.filter or \
                                                                                            a[j+5]!= obj.data.materials[0].raytrace_transparency.depth or \
                                                                                            a[j+6]!= obj.data.materials[0].translucency or \
                                                                                            a[j+7]!= obj.data.materials[0].specular_alpha:
                                    dif=1
                                    j+= 8     # ajusta ponteiro j
                                    if chkMatMirror: j+=6

                                    break
                                j+=8

                            if chkMatMirror:
                                #mirror
                                if a[j]!= obj.data.materials[0].raytrace_mirror.reflect_factor or a[j+1]!= obj.data.materials[0].raytrace_mirror.fresnel or \
                                                                                                    a[j+2]!= obj.data.materials[0].raytrace_mirror.fresnel_factor or \
                                                                                                    a[j+3]!= obj.data.materials[0].mirror_color or \
                                                                                                    a[j+4]!= obj.data.materials[0].raytrace_mirror.depth or \
                                                                                                    a[j+5]!= obj.data.materials[0].raytrace_mirror.gloss_factor:
                                    dif=1
                                    j+= 6     # ajusta ponteiro j
                                    break
                                j+=6
                # finaliza
                if dif==0:
                    obc.Frames_Pular+=1
                else:
                    obc.Frames_Renderizar+=1
                    ToRender.append(bpy.context.scene.frame_current)

                del a
        # para nao sair do index - nunca chega nesse frame
        ToRender.append(bpy.context.scene.frame_end+1)

        if obc.RunFrom+loop < RunMax:
            context.scene.imp_sound_to_anim.Info_check_smartrender= "["+str(obc.RunFrom+loop) + "/" + \
                                        str(RunMax) + "] Frames to Render= " + str(obc.Frames_Renderizar) + \
                                        " -> Reduction " + str(round((obc.Frames_Pular/RunMax)*100,1)) + "%"
        else:
            context.scene.imp_sound_to_anim.Info_check_smartrender= "Frames to Render= " + str(obc.Frames_Renderizar) + \
                                                    " -> Reduction " + str(round((obc.Frames_Pular/RunMax)*100,1)) + "%"

        #incrementa indice
        obc.RunFrom+= loop
        return (ToRender, obc.RunFrom)

    def execute(self, context):
        context.scene.imp_sound_to_anim.Working= "CheckSmartRender"
        #context.scene.imp_sound_to_anim.timer_reset_func=True
        bpy.ops.wm.modal_timer_operator()
        #CheckSmartRender(context)
        return{'FINISHED'}

    def invoke(self, context, event):
        self.execute(context)
        return {'FINISHED'}


#
#==================================================================================================
# Button - Smart Render
#==================================================================================================
#
class OBJECT_OT_Botao_SmartRender(bpy.types.Operator):
    '''Render Only Modified Frames and Copy the Others'''
    bl_idname = "import.sound_animation_smart_render"
    bl_label = "Smart Render"

    BaseRenderToCopy=0

    def SmartRender(context):
        obs=OBJECT_OT_Botao_SmartRender

        index=0
        pad=4
        #calcula zero pad
        if bpy.context.scene.frame_end //1000000 > 0:  #default 999999 1000000//1000000=1
            pad=7
        elif bpy.context.scene.frame_end //100000 > 0:  #default 99999 100000//100000=1
            pad=6
        elif bpy.context.scene.frame_end //10000 > 0:  #default 9999 10000//10000=1
            pad=5

        #bpy.data.images['Render Result'].file_format ='PNG'
        bpy.context.scene.render.image_settings.file_format = 'PNG'

        #info dos arquivos
        path= bpy.context.scene.render.filepath

        import shutil

        tot=bpy.context.scene.frame_end - bpy.context.scene.frame_start+1
        i=0
        # checa apenas 1 frame    o indice é interno em ChackSmartRender
        r= OBJECT_OT_Botao_Check_SmartRender.CheckSmartRender(context, 1)
        ToRender= r[0] # tem numero do frame se for para renderizar
        index= r[1]

        #copia frame atual  #se o frame ja não foi renderizado
        if (obs.BaseRenderToCopy!=(index+bpy.context.scene.frame_start-1)) and index > 1:   #index!=1 and index !=0:
            print("Copying: " + str(obs.BaseRenderToCopy) + "-> " + str(index+bpy.context.scene.frame_start-1) + \
                                "  To " + path + str(index+bpy.context.scene.frame_start-1).zfill(pad)  + ".png")
            shutil.copy2(path + str(obs.BaseRenderToCopy).zfill(pad)  + ".png", path + \
                        str(index+bpy.context.scene.frame_start-1).zfill(pad)  + ".png")

        if ToRender.__len__()>1:   #renderizar 1 item em ToRender nao renderiza, (sempre vem com no minimo 1)
            if index==1:
                print("================================================================")
                from time import strftime
                print(strftime("Running Smart Render:  %H:%M:%S"))
                print("================================================================")
                BaseRenderToCopy=0

            if ToRender[0] <= bpy.context.scene.frame_end:
                #renderiza proximo frame
                print("Rendering-> " + str(ToRender[0]))
                obs.BaseRenderToCopy= ToRender[0]
                bpy.ops.render.render(animation=False, write_still=False)
                bpy.data.images['Render Result'].save_render(filepath=path + str(ToRender[0]).zfill(pad)  + ".png")
                i+=1

        if index==tot:
            print("================================================================")
            from time import strftime
            print(strftime("Finish Render:  %H:%M:%S"))
            print("================================================================")
            print(".")

        if index==tot+1:
            obs.BaseRenderToCopy=0
            return 0

        return index


    def execute(self, context):
        # se for CYCLES, nao funciona com timer, preciso rodar direto
        context.scene.imp_sound_to_anim.Working= "SmartRender"
        bpy.ops.wm.modal_timer_operator()
        #SmartRender(context)
        return{'FINISHED'}

    def invoke(self, context, event):
        self.execute(context)
        return {'FINISHED'}



#
#==================================================================================================
# Button - Cancel
#==================================================================================================
#
class OBJECT_OT_Botao_Cancel(bpy.types.Operator):
    '''Cancel Actual Operation'''
    bl_idname = "import.sound_animation_botao_cancel"
    bl_label = "CANCEL"

    def execute(self, context):
        context.scene.imp_sound_to_anim.cancel_button_hit=True
        return{'FINISHED'}

    def invoke(self, context, event):
        self.execute(context)
        return {'FINISHED'}


#
#==================================================================================================
#     TIMER - controla a execucao das funcoes
#           Responsavel por rodar em partes usando o timer e possibilitando
#           o cancelamento e textos informativos
#==================================================================================================
#
class ModalTimerOperator(bpy.types.Operator):
    """Internal Script Control"""
    bl_idname = "wm.modal_timer_operator"
    bl_label = "Internal Script Control"

    _timer = None
    Running= False

    def CheckRunStop(self, context, func, index):
        # forca update do UI
        bpy.context.scene.frame_set(bpy.context.scene.frame_current)
        if index!=0:
            #configura timer para a funcao
            context.scene.imp_sound_to_anim.Working= func
            self.Running=True
            return {'PASS_THROUGH'}
        else: # posso desligar o timer e modal
            if self._timer!= None:
                context.window_manager.event_timer_remove(self._timer)
                self._timer= None
            return {'FINISHED'}


    def modal(self, context, event):
        if event.type == 'ESC'and self.Running:
            print("-- ESC Pressed --")
            self.cancel(context)
            context.scene.imp_sound_to_anim.Working=""
            self.Running=False
            #reseta contadores
            context.scene.imp_sound_to_anim.timer_reset_func=True
            # forca update do UI
            bpy.context.scene.frame_set(bpy.context.scene.frame_current)
            return {'CANCELLED'}

        if event.type == 'TIMER':
            #print("timer")
            #CheckSmartRender
            if context.scene.imp_sound_to_anim.Working== "CheckSmartRender":
                self.parar(context)
                #5= frames para rodar antes de voltar    [1]= indice de posicao atual
                index= OBJECT_OT_Botao_Check_SmartRender.CheckSmartRender(context, 5)[1]
                return self.CheckRunStop(context, "CheckSmartRender", index)

            #SmartRender
            elif context.scene.imp_sound_to_anim.Working== "SmartRender":
                self.parar(context)
                #render/copia 1 e volta     index>=0 indice posicao atual
                index= OBJECT_OT_Botao_SmartRender.SmartRender(context)
                return self.CheckRunStop(context, "SmartRender", index)

            #ProcessaSom
            elif context.scene.imp_sound_to_anim.Working== "ProcessaSom":
                self.parar(context)
                # loop = numero de frames de audio    index=0 se terminou ou >0 se não acabou
                index= OBJECT_OT_Botao_Go.ProcessaSom(context, 50)
                return self.CheckRunStop(context, "ProcessaSom", index)

            #wavimport(context)
            elif context.scene.imp_sound_to_anim.Working== "wavimport":
                self.parar(context)
                # 5= numero de frames to import por timer
                index=OBJECT_OT_Botao_Import.wavimport(context, 50)
                return self.CheckRunStop(context, "wavimport", index)

            #passa por aqui quando as funcoes estao sendo executadas mas
            #configuradas para nao entrar porque  context.scene.imp_sound_to_anim.Working== ""
            return {'PASS_THROUGH'}

        # reseta e para tudo botao CANCEL pressionado
        if context.scene.imp_sound_to_anim.cancel_button_hit==True:
            context.scene.imp_sound_to_anim.Working=""
            #pede reset contadores
            context.scene.imp_sound_to_anim.timer_reset_func=True
            if self._timer!= None:
                context.window_manager.event_timer_remove(self._timer)
                self._timer= None
            print("-- Cancel Pressed --")
            context.scene.imp_sound_to_anim.cancel_button_hit=False
            return {'FINISHED'}

        #print("modal")

        # se o timer esta ativado, continua, (senao termina).
        # desligar a chamada ao modal se caso chegar aqui (nao deveria)
        if self._timer!= None:
            return{'PASS_THROUGH'}
        else:
            return {'FINISHED'}

    def execute(self, context):
        if self._timer==None:
            self._timer = context.window_manager.event_timer_add(0.2, context.window)
            context.window_manager.modal_handler_add(self)
        #para deixar rodar sem deligar o timer
        context.scene.imp_sound_to_anim.timer_desligar=False
        self.Running=True
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        if self._timer!= None:
            context.window_manager.event_timer_remove(self._timer)
        self._timer= None

    def parar(self, context):
        if self.Running:
            context.scene.imp_sound_to_anim.Working=""
            self.Running=False



#
#==================================================================================================
#     Register - Unregister - MAIN
#==================================================================================================
#
def register():
    bpy.utils.register_module(__name__)
    bpy.types.Scene.imp_sound_to_anim = PointerProperty(type=ImpSoundtoAnim, name="Import: Sound to Animation", description="Extract movement from sound file. See the Object Panel at the end.")
    bpy.types.INFO_MT_file_import.append(WavFileImport)

def unregister():

    try:
        bpy.utils.unregister_module(__name__)
    except:
        pass

    try:
        bpy.types.INFO_MT_file_import.remove(WavFileImport)
    except:
        pass



if __name__ == "__main__":
    register()




