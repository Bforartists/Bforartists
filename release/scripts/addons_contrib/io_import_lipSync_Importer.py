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
    "name": "LipSync Importer & Blinker",
    "author": "Yousef Harfoush - bat3a)",
    "version": (0, 5, 2),
    "blender": (2, 70, 0),
    "location": "3D window > Tool Shelf",
    "description": "Plots Moho (Papagayo, Jlipsync, Yolo) file "
                   "to frames and adds automatic blinking",
    "warning": "",
    "wiki_url": "https://wiki.blender.org/index.php?title=Extensions:2.6/Py/"
                "Scripts/Import-Export/Lipsync Importer",
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
    "category": "Import-Export"}


import bpy
import re
from random import random
from bpy.props import (
        EnumProperty,
        IntProperty,
        FloatProperty,
        StringProperty,
        PointerProperty,
        )

global lastPhoneme
lastPhoneme = "nothing"


# add blinking
def blinker():

    scn = bpy.context.scene

    if scn.regMenuTypes.enumBlinkTypes == '0':
        modifier = 0
    elif scn.regMenuTypes.enumBlinkTypes == '1':
        modifier = scn.regMenuTypes.blinkMod

    # creating keys with blinkNm count
    for y in range(scn.regMenuTypes.blinkNm):
        frame = y * scn.regMenuTypes.blinkSp + int(random() * modifier)
        createShapekey('blink', frame)


# -- code contributed by dalai felinto adds armature support modified by me --

bone_keys = {
    "AI": ('location', 0),
    "E": ('location', 1),
    "FV": ('location', 2),
    "L": ('rotation_euler', 0),
    "MBP": ('rotation_euler', 1),
    "O": ('rotation_euler', 2),
    "U": ('scale', 0),
    "WQ": ('scale', 1),
    "etc": ('scale', 2),
    "rest": ('ik_stretch', -1)
}


def lipsyncerBone():
    # reading imported file & creating keys
    scene = bpy.context.scene
    bone = bpy.context.active_pose_bone

    resetBoneScale(bone)

    f = open(scene.regMenuTypes.fpath)  # importing file
    f.readline()           # reading the 1st line that we don"t need

    for line in f:
        # removing new lines
        lsta = re.split("\n+", line)

        # building a list of frames & shapes indexes
        lst = re.split(":? ", lsta[0])  # making a list of a frame & number
        frame = int(lst[0])

        for key, attribute in bone_keys.items():
            if lst[1] == key:
                createBoneKeys(key, bone, attribute, frame)


def resetBoneScale(bone):
    # set the attributes used by papagayo to 0.0
    for attribute, index in bone_keys.values():
        if index != -1:
            # bone.location[0] = 0.0
            exec("bone.%s[%d] = %f" % (attribute, index, 0.0))
        else:
            exec("bone.%s = %f" % (attribute, 0.0))


def addBoneKey(bone, data_path, index=-1, value=None, frame=0, group=""):
    # set a value and keyframe for the bone
    # it assumes the 'bone' variable was defined before
    # and it's the current selected bone
    frame = bpy.context.scene.frame_current
    if value is not None:
        if index != -1:
            # bone.location[0] = 0.0
            exec("bone.%s[%d] = %f" % (data_path, index, value))
        else:
            exec("bone.%s = %f" % (data_path, value))

    # bone.keyframe_insert("location", 0, 10.0, "Lipsync")
    exec('bone.keyframe_insert("%s", %d, %f, "%s")' % (data_path, index, frame, group))


# creating keys with offset and eases for a phonem @ the Skframe
def createBoneKeys(phoneme, bone, attribute, frame):
    global lastPhoneme

    scene = bpy.context.scene

    offst = scene.regMenuTypes.offset     # offset value
    skVlu = scene.regMenuTypes.skscale    # shape key value

    # in case of Papagayo format
    if scene.regMenuTypes.enumFileTypes == '0':
        frmIn = scene.regMenuTypes.easeIn     # ease in value
        frmOut = scene.regMenuTypes.easeOut   # ease out value
        hldIn = scene.regMenuTypes.holdGap    # holding time value

    # in case of Jlipsync format or Yolo
    elif scene.regMenuTypes.enumFileTypes == '1':
        frmIn = 1
        frmOut = 1
        hldIn = 0

    # inserting the In key only when phonem change or when blinking
    if lastPhoneme != phoneme or eval(scene.regMenuTypes.enumModeTypes) == 1:
        addBoneKey(bone, attribute[0], attribute[1], 0.0, offst + frame - frmIn, "Lipsync")

    addBoneKey(bone, attribute[0], attribute[1], skVlu, offst + frame, "Lipsync")
    addBoneKey(bone, attribute[0], attribute[1], skVlu, offst + frame + hldIn, "Lipsync")
    addBoneKey(bone, attribute[0], attribute[1], 0.0, offst + frame + hldIn + frmOut, "Lipsync")

    lastPhoneme = phoneme


# -------------------------------------------------------------------------------

# reading imported file & creating keys
def lipsyncer():

    obj = bpy.context.object
    scn = bpy.context.scene

    f = open(bpy.path.abspath(scn.regMenuTypes.fpath))  # importing file
    f.readline()         # reading the 1st line that we don"t need

    for line in f:

        # removing new lines
        lsta = re.split("\n+", line)

        # building a list of frames & shapes indexes
        lst = re.split(":? ", lsta[0])  # making a list of a frame & number
        frame = int(lst[0])

        for key in obj.data.shape_keys.key_blocks:
            if lst[1] == key.name:
                createShapekey(key.name, frame)


# creating keys with offset and eases for a phonem @ the frame
def createShapekey(phoneme, frame):

    global lastPhoneme

    scn = bpy.context.scene
    obj = bpy.context.object
    objSK = obj.data.shape_keys

    offst = scn.regMenuTypes.offset     # offset value
    skVlu = scn.regMenuTypes.skscale    # shape key value

    # in case of Papagayo format
    if scn.regMenuTypes.enumFileTypes == '0':
        frmIn = scn.regMenuTypes.easeIn     # ease in value
        frmOut = scn.regMenuTypes.easeOut   # ease out value
        hldIn = scn.regMenuTypes.holdGap    # holding time value

    # in case of Jlipsync format or Yolo
    elif scn.regMenuTypes.enumFileTypes == '1':
        frmIn = 1
        frmOut = 1
        hldIn = 0

    # inserting the In key only when phonem change or when blinking
    if lastPhoneme != phoneme or eval(scn.regMenuTypes.enumModeTypes) == 1:
        objSK.key_blocks[phoneme].value = 0.0
        objSK.key_blocks[phoneme].keyframe_insert(
            "value", -1, offst + frame - frmIn, "Lipsync"
            )

    objSK.key_blocks[phoneme].value = skVlu
    objSK.key_blocks[phoneme].keyframe_insert(
            "value", -1, offst + frame, "Lipsync"
            )
    objSK.key_blocks[phoneme].value = skVlu
    objSK.key_blocks[phoneme].keyframe_insert(
            "value", -1, offst + frame + hldIn, "Lipsync"
            )
    objSK.key_blocks[phoneme].value = 0.0
    objSK.key_blocks[phoneme].keyframe_insert(
            "value", -1, offst + frame + hldIn + frmOut, "Lipsync"
            )
    lastPhoneme = phoneme


# lipsyncer operation start
class btn_lipsyncer(bpy.types.Operator):
    bl_idname = 'lipsync.go'
    bl_label = 'Start Processing'
    bl_description = 'Plots the voice file keys to timeline'

    def execute(self, context):

        scn = context.scene
        obj = context.active_object

        # testing if object is valid
        if obj is not None:
            if obj.type == "MESH":
                if obj.data.shape_keys is not None:
                    if scn.regMenuTypes.fpath != '':
                        lipsyncer()
                    else:
                        print("select a Moho file")
                else:
                    print("No shape keys")

            elif obj.type == "ARMATURE":
                if 1:  # XXX add prop test
                    if scn.regMenuTypes.fpath != '':
                        lipsyncerBone()
                    else:
                        print("select a Moho file")
                else:
                    print("Create Pose properties")
            else:
                print("Object is not a mesh ot bone")
        else:
            print("Select object")

        return {'FINISHED'}


# blinker operation start
class btn_blinker(bpy.types.Operator):
    bl_idname = 'blink.go'
    bl_label = 'Start Processing'
    bl_description = 'Add blinks at random or specifice frames'

    def execute(self, context):

        obj = context.object

        # testing if object is valid
        if obj is not None:
            if obj.type == "MESH":
                if obj.data.shape_keys is not None:
                    for key in obj.data.shape_keys.key_blocks:
                        if key.name == 'blink':
                            blinker()
                            # return
                else:
                    print("No shape keys")
            else:
                print("Object is not a mesh ot bone")
        else:
            print("Select object")

        return {'FINISHED'}


# defining custom enumeratos
class menuTypes(bpy.types.PropertyGroup):

    enumFileTypes = EnumProperty(
            items=(('0', 'Papagayo', ''),
                    ('1', 'Jlipsync Or Yolo', '')
                    # ('2', 'Retarget', '')
                    ),
            name='Choose FileType',
            default='0'
            )
    enumBlinkTypes = EnumProperty(
            items=(('0', 'Specific', ''),
                    ('1', 'Random', '')),
            name='Choose BlinkType',
            default='0'
            )
    enumModeTypes = EnumProperty(
            items=(('0', 'Lipsyncer', ''),
                   ('1', 'Blinker', '')),
            name='Choose Mode',
            default='0'
            )

    fpath = StringProperty(
            name="Import File ",
            description="Select your voice file",
            subtype="FILE_PATH"
            )
    skscale = FloatProperty(
            description="Smoothing shape key values",
            min=0.1, max=1.0,
            default=0.8
            )
    offset = IntProperty(
            description="Offset your frames",
            default=0
            )
    easeIn = IntProperty(
            description="Smoothing In curve",
            min=1, default=3
            )
    easeOut = IntProperty(
            description="Smoothing Out curve",
            min=1,
            default=3
            )
    holdGap = IntProperty(
            description="Holding for slow keys",
            min=0,
            default=0
            )
    blinkSp = IntProperty(
            description="Space between blinks",
            min=1,
            default=100
            )
    blinkNm = IntProperty(
            description="Number of blinks",
            min=1,
            default=10
            )
    blinkMod = IntProperty(
            description="Randomzing keyframe placment",
            min=1,
            default=10
            )


# drawing the user interface
class LipSyncBoneUI(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Phonemes"
    bl_category = 'Animation'

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        bone = bpy.context.active_pose_bone

        # showing the current object type
        if bone:  # and if scn.regMenuTypes.enumModeTypes == '0':
            col.prop(bone, "location", index=0, text="AI")
            col.prop(bone, "location", index=1, text="E")
            col.prop(bone, "location", index=2, text="FV")

            if bpy.context.scene.unit_settings.system_rotation == 'RADIANS':
                col.prop(bone, "rotation_euler", index=0, text="L")
                col.prop(bone, "rotation_euler", index=1, text="MBP")
                col.prop(bone, "rotation_euler", index=2, text="O")
            else:
                row = col.row()
                row.prop(bone, "rotation_euler", index=0, text="L")
                row.label(text=str("%4.2f" % (bone.rotation_euler.x)))

                row = col.row()
                row.prop(bone, "rotation_euler", index=1, text="MBP")
                row.label(text=str("%4.2f" % (bone.rotation_euler.y)))

                row = col.row()
                row.prop(bone, "rotation_euler", index=2, text="O")
                row.label(text=str("%4.2f" % (bone.rotation_euler.z)))

            col.prop(bone, "scale", index=0, text="U")
            col.prop(bone, "scale", index=1, text="WQ")
            col.prop(bone, "scale", index=2, text="etc")
        else:
            layout.label(text="No good bone is selected")


# drawing the user interface
class LipSyncUI(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOL_PROPS"
    bl_label = "LipSync Importer & Blinker"

    def draw(self, context):
        obj = bpy.context.active_object
        scn = bpy.context.scene

        layout = self.layout
        col = layout.column()

        # showing the current object type
        if obj is not None:
            if obj.type == "MESH":
                split = col.split(align=True)
                split.label(text="The active object is: ", icon="OBJECT_DATA")
                split.label(obj.name, icon="EDITMODE_HLT")

            elif obj.type == "ARMATURE":  # bone needs to be selected
                if obj.mode == "POSE":    # mode needs to be pose
                    split = col.split(align=True)
                    split.label(text="The active object is: ", icon="ARMATURE_DATA")
                    split.label(obj.name, icon="EDITMODE_HLT")
                else:
                    col.label(text="You need to select Pose mode!", icon="OBJECT_DATA")
            else:
                col.label(text="The active object is not a Mesh or Armature!", icon="OBJECT_DATA")
        else:
            layout.label(text="No object is selected", icon="OBJECT_DATA")

        col.row().prop(scn.regMenuTypes, 'enumModeTypes')
        col.separator()

        # the lipsyncer panel
        if scn.regMenuTypes.enumModeTypes == '0':
            # choose the file format
            col.row().prop(scn.regMenuTypes, 'enumFileTypes', text=' ', expand=True)

            # Papagayo panel
            if scn.regMenuTypes.enumFileTypes == '0':
                col.prop(scn.regMenuTypes, "fpath")

                split = col.split(align=True)
                split.label("Key Value :")
                split.prop(scn.regMenuTypes, "skscale")

                split = col.split(align=True)
                split.label("Frame Offset :")
                split.prop(scn.regMenuTypes, "offset")

                split = col.split(align=True)
                split.prop(scn.regMenuTypes, "easeIn", "Ease In")
                split.prop(scn.regMenuTypes, "holdGap", "Hold Gap")
                split.prop(scn.regMenuTypes, "easeOut", "Ease Out")

                col.operator('lipsync.go', text='Plot Keys to the Timeline')

            # Jlipsync & Yolo panel
            elif scn.regMenuTypes.enumFileTypes == '1':
                col.prop(scn.regMenuTypes, "fpath")
                split = col.split(align=True)
                split.label("Key Value :")
                split.prop(scn.regMenuTypes, "skscale")

                split = col.split(align=True)
                split.label("Frame Offset :")
                split.prop(scn.regMenuTypes, "offset")

                col.operator('lipsync.go', text='Plot Keys to the Timeline')

        # the blinker panel
        elif scn.regMenuTypes.enumModeTypes == '1':
            # choose blink type
            col.row().prop(scn.regMenuTypes, 'enumBlinkTypes', text=' ', expand=True)

            # specific panel
            if scn.regMenuTypes.enumBlinkTypes == '0':
                split = col.split(align=True)
                split.label("Key Value :")
                split.prop(scn.regMenuTypes, "skscale")

                split = col.split(align=True)
                split.label("Frame Offset :")
                split.prop(scn.regMenuTypes, "offset")

                split = col.split(align=True)
                split.prop(scn.regMenuTypes, "easeIn", "Ease In")
                split.prop(scn.regMenuTypes, "holdGap", "Hold Gap")
                split.prop(scn.regMenuTypes, "easeOut", "Ease Out")
                col.prop(scn.regMenuTypes, "blinkSp", "Spacing")
                col.prop(scn.regMenuTypes, "blinkNm", "Times")
                col.operator('blink.go', text='Add Keys to the Timeline')

            # Random panel
            elif scn.regMenuTypes.enumBlinkTypes == '1':
                split = col.split(align=True)
                split.label("Key Value :")
                split.prop(scn.regMenuTypes, "skscale")

                split = col.split(align=True)
                split.label("Frame Start :")
                split.prop(scn.regMenuTypes, "offset")

                split = col.split(align=True)
                split.prop(scn.regMenuTypes, "easeIn", "Ease In")
                split.prop(scn.regMenuTypes, "holdGap", "Hold Gap")
                split.prop(scn.regMenuTypes, "easeOut", "Ease Out")

                split = col.split(align=True)
                split.prop(scn.regMenuTypes, "blinkSp", "Spacing")
                split.prop(scn.regMenuTypes, "blinkMod", "Random Modifier")
                col.prop(scn.regMenuTypes, "blinkNm", "Times")
                col.operator('blink.go', text='Add Keys to the Timeline')


# registering the script
def register():
    bpy.utils.register_module(__name__)
    bpy.types.Scene.regMenuTypes = PointerProperty(type=menuTypes)


def unregister():
    bpy.utils.unregister_module(__name__)
    del bpy.types.Scene.regMenuTypes


if __name__ == "__main__":
    register()
