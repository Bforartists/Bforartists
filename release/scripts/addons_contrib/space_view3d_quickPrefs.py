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
    "name": "QuickPrefs",
    "author": "Sean Olson",
    "version": (2, 2),
    "blender": (2, 66, 0),
    "location": "3DView->Properties Panel (N-Key)",
    "description": "Add often changed User Preference options to Properties panel.",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/3D_interaction/QuickPrefs",
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
    "category": "3D View"}


import os

import bpy
from bpy.types import Menu, Panel
from rna_prop_ui import PropertyPanel
from bpy.app.handlers import persistent
from bpy.props import (
                       BoolProperty,
                       EnumProperty,
                       FloatProperty,
                       CollectionProperty,
                       IntProperty,
                       StringProperty,
                       PointerProperty
                       )


import bpy_extras

#Global Variables
recursive  = False
renaming   = True
lastindex  = 0
lastname   = ""
debug = 0
defaultfilepath=os.path.join(bpy.utils.script_paths(subdir="addons")[0], "quickprefpresets")


##########################################
####### Import/Export Functions ##########
##########################################

#import all grabs all files in the given directory and imports them
@persistent
def gllightpreset_importall():
    path = bpy.context.scene.quickprefs.gllightpreset_importdirectory
    directorylisting = os.listdir(path)

    for infile in directorylisting:
        if not os.path.isdir(infile):                       #check if the file is a directory
            if '.preset' in infile:                           #check that this is a .preset file
                thefile=os.path.join(path, infile)       #join the filename with the path
                gllightpreset_importsingle(thefile)     #import it!

#import single takes a given filename and imports it
def gllightpreset_importsingle(filename):

    if not os.path.isdir(filename):           #check if the file is a directory
        if '.preset' in filename:              #check to make sure this is a preset file
            readfile=open(filename, 'r')

            name=readfile.readline()
            name=name[:-1]

            illuminationString0=readfile.readline()
            illuminationString0=illuminationString0[:-1]

            if illuminationString0=="True":
                illumination0=True
            else:
                illumination0=False

            illuminationString1=readfile.readline()
            illuminationString1=illuminationString1[:-1]
            if illuminationString1=="True":
                illumination1=True
            else:
                illumination1=False

            illuminationString2=readfile.readline()
            illuminationString2=illuminationString2[:-1]
            if illuminationString2=="True":
                illumination2=True
            else:
                illumination2=False

            #convert strings to booleans

            str=readfile.readline()
            strArray=str.split()
            direction0x=strArray[0]
            direction0y=strArray[1]
            direction0z=strArray[2]

            str=readfile.readline()
            strArray=str.split()
            direction1x=strArray[0]
            direction1y=strArray[1]
            direction1z=strArray[2]

            str=readfile.readline()
            strArray=str.split()
            direction2x=strArray[0]
            direction2y=strArray[1]
            direction2z=strArray[2]

            str=readfile.readline()
            strArray=str.split()
            diffuse0r=strArray[0]
            diffuse0g=strArray[1]
            diffuse0b=strArray[2]

            str=readfile.readline()
            strArray=str.split()
            diffuse1r=strArray[0]
            diffuse1g=strArray[1]
            diffuse1b=strArray[2]

            str=readfile.readline()
            strArray=str.split()
            diffuse2r=strArray[0]
            diffuse2g=strArray[1]
            diffuse2b=strArray[2]

            str=readfile.readline()
            strArray=str.split()
            spec0r=strArray[0]
            spec0g=strArray[1]
            spec0b=strArray[2]

            str=readfile.readline()
            strArray=str.split()
            spec1r=strArray[0]
            spec1g=strArray[1]
            spec1b=strArray[2]

            str=readfile.readline()
            strArray=str.split()
            spec2r=strArray[0]
            spec2g=strArray[1]
            spec2b=strArray[2]

            #set the variables
            system=bpy.context.preferences.system
            system.solid_lights[0].use=illumination0
            system.solid_lights[1].use=illumination1
            system.solid_lights[2].use=illumination2

            system.solid_lights[0].direction = (float(direction0x), float(direction0y), float(direction0z))
            system.solid_lights[1].direction = (float(direction1x), float(direction1y), float(direction1z))
            system.solid_lights[2].direction = (float(direction2x), float(direction2y), float(direction2z))

            system.solid_lights[0].diffuse_color=(float(diffuse0r), float(diffuse0g), float(diffuse0b))
            system.solid_lights[1].diffuse_color=(float(diffuse1r), float(diffuse1g), float(diffuse1b))
            system.solid_lights[2].diffuse_color=(float(diffuse2r), float(diffuse2g), float(diffuse2b))

            system.solid_lights[0].specular_color=(float(spec0r), float(spec0g), float(spec0b))
            system.solid_lights[1].specular_color=(float(spec1r), float(spec1g), float(spec1b))
            system.solid_lights[2].specular_color=(float(spec2r), float(spec2g), float(spec2b))
            gllightpreset_add(name)
            gllightpreset_save()

#Export all exports the entire contents of your presets list to the given file
@persistent
def gllightpreset_exportall(context):
   for i in range(len(bpy.context.scene.quickprefs.gllightpreset)):
        gllightpreset_exportsingle(i, True)


def gllightpreset_exportsingle(index, multiimport):
    scn=bpy.context.scene.quickprefs
    name=scn.gllightpreset[index].name

    illuminatedBool0=scn.gllightpreset[index].illuminated0
    illuminatedBool1=scn.gllightpreset[index].illuminated1
    illuminatedBool2=scn.gllightpreset[index].illuminated2

    #illuminations
    if illuminatedBool0==True:
        illuminated0="True"
    else:
        illuminated0="False"

    if illuminatedBool1==True:
        illuminated1="True"
    else:
        illuminated1="False"

    if illuminatedBool2==True:
        illuminated2="True"
    else:
        illuminated2="False"

    #direction light0
    dirx=str(scn.gllightpreset[index].direction0[0])
    diry=str(scn.gllightpreset[index].direction0[1])
    dirz=str(scn.gllightpreset[index].direction0[2])
    direction0=dirx + " " + diry + " " + dirz + " "

    #direction light1
    dirx=str(scn.gllightpreset[index].direction1[0])
    diry=str(scn.gllightpreset[index].direction1[1])
    dirz=str(scn.gllightpreset[index].direction1[2])
    direction1=dirx + " " + diry + " " + dirz + " "

    #direction light2
    dirx=str(scn.gllightpreset[index].direction2[0])
    diry=str(scn.gllightpreset[index].direction2[1])
    dirz=str(scn.gllightpreset[index].direction2[2])
    direction2=dirx + " " + diry + " " + dirz + " "

    #diffuse light0
    difr=str(scn.gllightpreset[index].diffuse0[0])
    difg=str(scn.gllightpreset[index].diffuse0[1])
    difb=str(scn.gllightpreset[index].diffuse0[2])
    diffuse0=difr + " " + difg + " " + difb + " "

    #diffuse light1
    difr=str(scn.gllightpreset[index].diffuse1[0])
    difg=str(scn.gllightpreset[index].diffuse1[1])
    difb=str(scn.gllightpreset[index].diffuse1[2])
    diffuse1=difr + " " + difg + " " + difb + " "

    #diffuse light2
    difr=str(scn.gllightpreset[index].diffuse2[0])
    difg=str(scn.gllightpreset[index].diffuse2[1])
    difb=str(scn.gllightpreset[index].diffuse2[2])
    diffuse2=difr + " " + difg + " " + difb + " "

    #specular light 0
    specr=str(scn.gllightpreset[index].specular0[0])
    specg=str(scn.gllightpreset[index].specular0[1])
    specb=str(scn.gllightpreset[index].specular0[2])
    specular0=specr + " " + specg + " " + specb + " "

    #specular light 1
    specr=str(scn.gllightpreset[index].specular1[0])
    specg=str(scn.gllightpreset[index].specular1[1])
    specb=str(scn.gllightpreset[index].specular1[2])
    specular1=specr + " " + specg + " " + specb + " "

    #specular light 2
    specr=str(scn.gllightpreset[index].specular2[0])
    specg=str(scn.gllightpreset[index].specular2[1])
    specb=str(scn.gllightpreset[index].specular2[2])
    specular2=specr + " " + specg + " " + specb + " "

    printstring=name+"\n"
    printstring+=illuminated0 +"\n"+ illuminated1 +"\n"+ illuminated2+"\n"
    printstring+=direction0  +"\n"+ direction1 +"\n"+ direction2 +"\n"
    printstring+=diffuse0+"\n"+diffuse1 +"\n"+ diffuse2 +"\n"
    printstring+=specular0+"\n"+specular1+"\n"+specular2+"\n"

    if multiimport==True:
        filepath = scn.gllightpreset_exportdirectory
    else:
        filepath = scn.gllightpreset_exportfile

    if not os.path.exists(filepath):
        os.mkdir(filepath)
    filepath=os.path.join(filepath, (name+".preset"))
    writefile = open(filepath, 'w')
    writefile.write(printstring)

##########################################
####### General  Presets Functions #######
##########################################

def gllightpreset_addPresets():

    system=bpy.context.preferences.system

    system.solid_lights[0].use=True
    system.solid_lights[1].use=True
    system.solid_lights[2].use=True

    system.solid_lights[0].direction = (-0.8920, 0.3000, 0.8999)
    system.solid_lights[1].direction = (0.5880, 0.4600, 0.2480)
    system.solid_lights[2].direction = (0.2159, -0.3920, -0.2159)

    system.solid_lights[0].diffuse_color=(0.8000, 0.8000, 0.8000)
    system.solid_lights[1].diffuse_color=(0.4980, 0.5000, 0.6000)
    system.solid_lights[2].diffuse_color=(0.7980, 0.8379, 1.0)

    system.solid_lights[0].specular_color=(0.5, 0.5, 0.5)
    system.solid_lights[1].specular_color=(0.2000, 0.2, 0.2)
    system.solid_lights[2].specular_color=(0.0659, 0.0, 0.0)
    gllightpreset_add("(Default)")
    gllightpreset_save()

    system.solid_lights[0].use=True
    system.solid_lights[1].use=True
    system.solid_lights[2].use=True

    system.solid_lights[0].direction = (-0.3207, 0.4245, 0.8466)
    system.solid_lights[1].direction = (0.4259, -0.0555, 0.9030)
    system.solid_lights[2].direction = (-0.4485, 0.2400, -0.8609)

    system.solid_lights[0].diffuse_color=(0.4292, 0.0457, 0.0457)
    system.solid_lights[1].diffuse_color=(0.7873, 0.4424, 0.2893)
    system.solid_lights[2].diffuse_color=(0.7483, 0.7168, 0.6764)

    system.solid_lights[0].specular_color=(0.2000, 0.2000, 0.2000)
    system.solid_lights[1].specular_color=(0.0, 0.0, 0.0)
    system.solid_lights[2].specular_color=(0.0, 0.0, 0.0)
    gllightpreset_add("Orange Clay")
    gllightpreset_save()

    system.solid_lights[0].use=True
    system.solid_lights[1].use=True
    system.solid_lights[2].use=True

    system.solid_lights[0].direction=(-0.06666, 0.8222, 0.5652)
    system.solid_lights[1].direction=(-0.8555, 0.1111, 0.5056)
    system.solid_lights[2].direction=(0.9000, 0.1555, 0.4071)

    system.solid_lights[0].diffuse_color=(0.1000, 0.1000, 0.1000)
    system.solid_lights[1].diffuse_color=(1.0, 0.9734, 0.8713)
    system.solid_lights[2].diffuse_color=(0.7835, 0.9215, 1.0)

    system.solid_lights[0].specular_color=(0.0, 0.0, 0.0)
    system.solid_lights[1].specular_color=(0.0, 0.0, 0.0)
    system.solid_lights[2].specular_color=(0.0, 0.0, 0.0)
    gllightpreset_add("Softblend")
    gllightpreset_save()

    system.solid_lights[0].use = True
    system.solid_lights[1].use = True
    system.solid_lights[2].use = True

    system.solid_lights[0].direction = (0.3666, 0.2888, 0.8843)
    system.solid_lights[1].direction = (0.1111, 0.0888, 0.9898)
    system.solid_lights[2].direction = (-0.5142, 0.5142, -0.6864)

    system.solid_lights[0].diffuse_color = (0.6618, 0.5481, 0.5054)
    system.solid_lights[1].diffuse_color = (0.3672, 0.2371, 0.1752)
    system.solid_lights[2].diffuse_color = (1.0, 0.9574, 0.9058)

    system.solid_lights[0].specular_color = (0.4969, 0.4886, 0.4820)
    system.solid_lights[1].specular_color = (0.0, 0.0, 0.0)
    system.solid_lights[2].specular_color = (1.0, 1.0, 1.0)
    gllightpreset_add("Skin")
    gllightpreset_save()

    system.solid_lights[0].use = True
    system.solid_lights[1].use = False
    system.solid_lights[2].use = False

    system.solid_lights[0].direction = (0.0111, 0.4000, 0.9164)
    system.solid_lights[1].direction = (0.1111, 0.0888, 0.9898)
    system.solid_lights[2].direction = (-0.5142, 0.5142, -0.6864)

    system.solid_lights[0].diffuse_color = (1.0, 0.5912, 0.4148)
    system.solid_lights[1].diffuse_color = (0.4962, 0.4962, 0.4962)
    system.solid_lights[2].diffuse_color = (1.0, 0.9574, 0.9058)

    system.solid_lights[0].specular_color = (0.2036, 0.4206, 0.7873)
    system.solid_lights[1].specular_color = (0.0, 0.0, 0.0)
    system.solid_lights[2].specular_color = (1.0, 1.0, 1.0)
    gllightpreset_add("Candy")
    gllightpreset_save();

    system.solid_lights[0].use = True
    system.solid_lights[1].use = True
    system.solid_lights[2].use = True

    system.solid_lights[0].direction = (-0.6124, 0.6046, 0.5092)
    system.solid_lights[1].direction = (0.1627, 0.5271, 0.8340)
    system.solid_lights[2].direction = (-0.5858, 0.7811, -0.2160)

    system.solid_lights[0].diffuse_color = (0.0, 0.3564, 0.4292)
    system.solid_lights[1].diffuse_color = (0.7873, 0.0038, 0.7197)
    system.solid_lights[2].diffuse_color = (0.1994, 0.2014, 0.2330)

    system.solid_lights[0].specular_color = (0.0946, 0.0946, 0.0946)
    system.solid_lights[1].specular_color = (0.0, 0.0, 0.0)
    system.solid_lights[2].specular_color = (0.0, 0.0, 0.0)
    gllightpreset_add("Purpleboogers.com")
    gllightpreset_save();

    system.solid_lights[0].use = True
    system.solid_lights[1].use = False
    system.solid_lights[2].use = False

    system.solid_lights[0].direction = (0.0111, 0.4000, 0.9164)
    system.solid_lights[1].direction = (0.1111, 0.0888, 0.9898)
    system.solid_lights[2].direction = (-0.5142, 0.5142, -0.6864)

    system.solid_lights[0].diffuse_color = (0.8000, 0.8000, 0.8000)
    system.solid_lights[1].diffuse_color = (0.4962, 0.4962, 0.4962)
    system.solid_lights[2].diffuse_color = (1.0, 0.9574, 0.9058)

    system.solid_lights[0].specular_color = (0.4540, 0.4540, 0.4540)
    system.solid_lights[1].specular_color = (0.0, 0.0, 0.0)
    system.solid_lights[2].specular_color = (1.0, 1.0, 1.0)
    gllightpreset_add("Dark Gray")
    gllightpreset_save()

    system.solid_lights[0].use = True
    system.solid_lights[1].use = False
    system.solid_lights[2].use = False

    system.solid_lights[0].direction = (0.0333, 0.2444, 0.9690)
    system.solid_lights[1].direction = (0.1111, 0.08888, 0.9898)
    system.solid_lights[2].direction = (-0.5142, 0.5142, -0.6864)

    system.solid_lights[0].diffuse_color = (0.8000, 0.6670, 0.6020)
    system.solid_lights[1].diffuse_color = (0.4962, 0.4962, 0.4962)
    system.solid_lights[2].diffuse_color = (1.0, 0.9574, 0.9058)

    system.solid_lights[0].specular_color = (0.3281, 0.3281, 0.3281)
    system.solid_lights[1].specular_color = (0.0, 0.0, 0.0)
    system.solid_lights[2].specular_color = (1.0, 1.0, 1.0)
    gllightpreset_add("Turntable")
    gllightpreset_save()

    system.solid_lights[0].use = True
    system.solid_lights[1].use = True
    system.solid_lights[2].use = True

    system.solid_lights[0].direction = (-0.2555, 0.5444, 0.7989)
    system.solid_lights[1].direction = (0.5666, -0.7333, 0.3756)
    system.solid_lights[2].direction = (-0.5142, 0.5142, -0.6864)

    system.solid_lights[0].diffuse_color = (1.0, 0.9475, 0.3194)
    system.solid_lights[1].diffuse_color = (0.3851, 0.2978, 0.1612)
    system.solid_lights[2].diffuse_color = (1.0, 1.0, 1.0)

    system.solid_lights[0].specular_color = (0.2740, 0.2740, 0.2740)
    system.solid_lights[1].specular_color = (0.0, 0.0, 0.0)
    system.solid_lights[2].specular_color = (0.0, 0.0, 0.0)
    gllightpreset_add("Yellow Clay")
    gllightpreset_save()

##########################################
####### LightPreset Functions #######
##########################################

def gllightpreset_name(self, context):
    global recursive
    global renaming
    global lastname
    if recursive==True: return
    recursive=True

    tmp=self.name
    self.name=self.name+"@temporaryname"
    self.name=gllightpreset_checkname(tmp)
    tmp=self.name
    if renaming==True: gllightpreset_rename(lastname, tmp)
    #gllightpreset_sort()

    recursive=False

def gllightpreset_checkname(name):
    collection=bpy.context.scene.quickprefs.gllightpreset
    if name=="": name="Preset"

    if not name in collection:
        return name

    pos = name.rfind(".")
    if pos==-1:
        name=name+".001"
        pos=len(name)-4

    for i in range(1, 1000):
        nr="00"+str(i)
        tmp=name[:pos+1]+nr[len(nr)-3:]
        if not tmp in collection:
            return tmp
    return "Preset.???"

def gllightpreset_rename(old, new):
    for o in bpy.context.scene.quickprefs.objects:
        if o.get("gllightpreset", "Default")==old:
            o.gllightpreset=new

@persistent
def gllightpreset_index(self, context):
    global recursive
    if recursive==True: return
    recursive=True

    scn=bpy.context.scene.quickprefs

    if scn.gllightpreset_index > len(scn.gllightpreset)-1:
        scn.gllightpreset_index = len(scn.gllightpreset)-1

    recursive=False

def gllightpreset_add(name=""):
    global renaming
    renaming=False

    scn=bpy.context.scene.quickprefs

    entry=scn.gllightpreset.add()
    bpy.context.scene.quickprefs['gllightpreset_index']=len(scn.gllightpreset)-1
    entry.name=gllightpreset_checkname(name)

    renaming=True
    gllightpreset_save()

def gllightpreset_delete():
    scn=bpy.context.scene
    index=scn.quickprefs.gllightpreset_index
    name=scn.quickprefs.gllightpreset[index].name

    for o in scn.objects:
        if o.get("gllightpreset", "Default")==name:
            o.gllightpreset="Default"

    scn.quickprefs.gllightpreset.remove(index)


def gllightpreset_save():
    index=bpy.context.scene.quickprefs.gllightpreset_index
    name=bpy.context.scene.quickprefs.gllightpreset[index].name

    bpy.context.scene.quickprefs.gllightpreset[index].illuminated0 = bpy.context.preferences.system.solid_lights[0].use
    bpy.context.scene.quickprefs.gllightpreset[index].illuminated1 = bpy.context.preferences.system.solid_lights[1].use
    bpy.context.scene.quickprefs.gllightpreset[index].illuminated2 = bpy.context.preferences.system.solid_lights[2].use

    bpy.context.scene.quickprefs.gllightpreset[index].direction0 = bpy.context.preferences.system.solid_lights[0].direction
    bpy.context.scene.quickprefs.gllightpreset[index].direction1 = bpy.context.preferences.system.solid_lights[1].direction
    bpy.context.scene.quickprefs.gllightpreset[index].direction2 = bpy.context.preferences.system.solid_lights[2].direction

    bpy.context.scene.quickprefs.gllightpreset[index].diffuse0 = bpy.context.preferences.system.solid_lights[0].diffuse_color
    bpy.context.scene.quickprefs.gllightpreset[index].diffuse1 = bpy.context.preferences.system.solid_lights[1].diffuse_color
    bpy.context.scene.quickprefs.gllightpreset[index].diffuse2 = bpy.context.preferences.system.solid_lights[2].diffuse_color

    bpy.context.scene.quickprefs.gllightpreset[index].specular0 = bpy.context.preferences.system.solid_lights[0].specular_color
    bpy.context.scene.quickprefs.gllightpreset[index].specular1 = bpy.context.preferences.system.solid_lights[1].specular_color
    bpy.context.scene.quickprefs.gllightpreset[index].specular2 = bpy.context.preferences.system.solid_lights[2].specular_color

#select the current light
def gllightpreset_select():
    index=bpy.context.scene.quickprefs.gllightpreset_index
    name=bpy.context.scene.quickprefs.gllightpreset[index].name

    bpy.context.preferences.system.solid_lights[0].use=bpy.context.scene.quickprefs.gllightpreset[index].illuminated0
    bpy.context.preferences.system.solid_lights[1].use=bpy.context.scene.quickprefs.gllightpreset[index].illuminated1
    bpy.context.preferences.system.solid_lights[2].use=bpy.context.scene.quickprefs.gllightpreset[index].illuminated2

    bpy.context.preferences.system.solid_lights[0].direction=bpy.context.scene.quickprefs.gllightpreset[index].direction0
    bpy.context.preferences.system.solid_lights[1].direction=bpy.context.scene.quickprefs.gllightpreset[index].direction1
    bpy.context.preferences.system.solid_lights[2].direction=bpy.context.scene.quickprefs.gllightpreset[index].direction2

    bpy.context.preferences.system.solid_lights[0].diffuse_color=bpy.context.scene.quickprefs.gllightpreset[index].diffuse0
    bpy.context.preferences.system.solid_lights[1].diffuse_color=bpy.context.scene.quickprefs.gllightpreset[index].diffuse1
    bpy.context.preferences.system.solid_lights[2].diffuse_color=bpy.context.scene.quickprefs.gllightpreset[index].diffuse2

    bpy.context.preferences.system.solid_lights[0].specular_color=bpy.context.scene.quickprefs.gllightpreset[index].specular0
    bpy.context.preferences.system.solid_lights[1].specular_color=bpy.context.scene.quickprefs.gllightpreset[index].specular1
    bpy.context.preferences.system.solid_lights[2].specular_color=bpy.context.scene.quickprefs.gllightpreset[index].specular2

#sort alphabetically
def gllightpreset_sort():
    collection=bpy.context.scene.quickprefs.gllightpreset
    count=len(collection)
    for i in range(0, count):
        for j in range(i+1, count):
            if collection[i].name > collection[j].name:
                collection.move(j, i)

#Add default setting
def gllightpreset_addDefault():
    print('adding default presets')
    gllightpreset_addPresets()
    gllightpreset_sort();
    bpy.context.scene.quickprefs['gllightpreset_index']=0
    gllightpreset_select()

##########################################
####### Persistant functions##############
##########################################
#This function decides where to load presets from - The order goes: BPY>File>Defaults
#@persistent
def gllightpreset_chooseLoadLocation(context):

    filepath=bpy.context.scene.quickprefs.gllightpreset_importdirectory
    if len(bpy.context.scene.quickprefs.gllightpreset)==0:                    #is it in bpy?
          if not os.path.exists(filepath):                                                     #is it in the folder?
               print('quickprefs: loading default presets')
               gllightpreset_addDefault()                                                       #it's not, add the default
          else:                                                                                             #the folder exists
               directorylisting = os.listdir(filepath)
               if len(directorylisting)==0:                                                      #is the folder empty?
                    print('quickprefs: loading default presets')
                    gllightpreset_addDefault()                                                  #the folder is empty, add default
               else:                                                                                        #the folder is not empty
                    print('quickprefs: loading preset folder')
                    gllightpreset_loadpresets(1)                                                #go ahead and load it
    #print('quickprefs: loading from bpy')

#This function scans for changes of the index of the selected preset and updates the selection if needed
@persistent
def gllightpreset_scan(context):
    global lastindex
    if debug==0:
        if lastindex!=bpy.context.scene.quickprefs.gllightpreset_index:
            lastindex=bpy.context.scene.quickprefs.gllightpreset_index
            gllightpreset_select()

#This function loads all the presets from a given folder (stored in bpy)
@persistent
def gllightpreset_loadpresets(context):
       gllightpreset_importall()
       bpy.context.scene['gllightpreset_index']=0
       gllightpreset_select()

##########################################
####### GUI ##############################
##########################################

#This function defines the layout of the openGL lamps
def opengl_lamp_buttons(column, lamp):
    split = column.split(percentage=0.1)

    split.prop(lamp, "use", text="", icon='OUTLINER_OB_LAMP' if lamp.use else 'LAMP_DATA')

    col = split.column()
    col.active = lamp.use
    row = col.row()
    row.label(text="Diffuse:")
    row.prop(lamp, "diffuse_color", text="")
    row = col.row()
    row.label(text="Specular:")
    row.prop(lamp, "specular_color", text="")

    col = split.column()
    col.active = lamp.use
    col.prop(lamp, "direction", text="")

class gllightpreset(bpy.types.PropertyGroup):

    props=bpy.props
    name: props.StringProperty(update=gllightpreset_name)

    illuminated0: props.BoolProperty(default = True)
    illuminated1: props.BoolProperty(default = True)
    illuminated2: props.BoolProperty(default = True)

    direction0: props.FloatVectorProperty(name="",  default=(-0.8920, 0.3000, 0.8999))
    direction1: props.FloatVectorProperty(name="",  default=(0.5880, 0.4600, 0.2480))
    direction2: props.FloatVectorProperty(name="",  default=(0.2159, -0.3920, -0.2159))

    diffuse0: props.FloatVectorProperty(name="",  default=(0.8000, 0.8000, 0.8000))
    diffuse1: props.FloatVectorProperty(name="",  default=(0.4980, 0.5000, 0.6000))
    diffuse2: props.FloatVectorProperty(name="",  default=(0.7980, 0.8379, 1.0))

    specular0: props.FloatVectorProperty(name="",  default=(0.5, 0.5, 0.5))
    specular1: props.FloatVectorProperty(name="",  default=(0.2000, 0.2000, 0.2000))
    specular2: props.FloatVectorProperty(name="",  default=(0.0659, 0.0, 0.0))

    count: props.IntProperty(name="", default=0)
    count2: props.IntProperty(name="", default=0)

class SCENE_OT_gllightpreset(bpy.types.Operator):
    bl_label ="Preset Action"
    bl_idname="gllightpreset.action"

    #alias


    button:bpy.props.StringProperty(default="")

    def execute(self, context):
        scn=bpy.context.scene
        button=self.button


        if   button=="add":
            gllightpreset_add()
        elif button=="delete":
            if len(scn.quickprefs.gllightpreset)>1:
                gllightpreset_delete()
            else:
                self.report({'INFO'}, "Must have at least 1 Preset")

        elif button=="save":
            gllightpreset_save()
            self.report({'INFO'}, "Saved Preset to Blend File.")
        elif button=="sort":     gllightpreset_sort()
        elif button=="select":   gllightpreset_select()
        elif button=="export":
            gllightpreset_exportsingle(scn.quickprefs.gllightpreset_index, False)
            self.report({'INFO'}, "Exported Preset to: "+scn.quickprefs.gllightpreset_exportfile)
        elif button=="exportall":
            gllightpreset_exportall(1)
            self.report({'INFO'}, "Exported Presets to: "+scn.quickprefs.gllightpreset_exportdirectory)
        elif button=="import":
            if not os.path.isdir(scn.quickprefs.gllightpreset_importfile):
                if not scn.quickprefs.gllightpreset_importdirectory=="":
                    gllightpreset_importsingle(scn.quickprefs.gllightpreset_importfile)
                else:
                    self.report({'INFO'}, "Please choose a valid preset file")
            else:
                self.report({'INFO'}, "Please choose a valid preset file")
        elif button=="importall":
            gllightpreset_importall()
            self.report({'INFO'}, "Imported Presets from: "+scn.quickprefs.gllightpreset_importdirectory)
        elif button=="defaults":
                gllightpreset_addDefault()

        if scn.quickprefs.gllightpreset_index > len(scn.quickprefs.gllightpreset)-1:
            scn.quickprefs.gllightpreset_index = len(scn.quickprefs.gllightpreset)-1

        return {"FINISHED"}

#Panel for tools
class PANEL(bpy.types.Panel):
    bl_label = 'Quick Preferences'
    bl_space_type = 'VIEW_3D'
    bl_context = "render"
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}


    def draw(self, context):
        global lastname

        #aliases
        scn = bpy.context.scene.quickprefs
        system = context.preferences.system
        inputs = context.preferences.inputs
        edit = context.preferences.edit
        view = context.preferences.view
        layout = self.layout
        split = layout.split()

#Setup the OpenGL lights box
#Draw the Lights
        box = layout.box().column(align=False)
        box.prop(scn,'gllights')
        if scn.gllights:

            split = box.split(percentage=0.1)
            split.label()
            split.label(text="Colors:")
            split.label(text="Direction:")

            lamp = system.solid_lights[0]
            opengl_lamp_buttons(box, lamp)

            lamp = system.solid_lights[1]
            opengl_lamp_buttons(box, lamp)

            lamp = system.solid_lights[2]
            opengl_lamp_buttons(box, lamp)

            box.separator()

#Draw the selection box
            split = box.split(percentage=0.7)
            col = split.row()
			#original
            col.template_list("UI_UL_list", "gl_light_presets", scn, "gllightpreset",
                              scn, "gllightpreset_index", rows=5, maxrows=5)

#Draw the buttons
            split = split.split()
            col = split.column()
            col.operator("gllightpreset.action", icon='ADD', text="Add").button="add"
            col.operator("gllightpreset.action", icon='REMOVE', text="Delete").button="delete"
            col.operator("gllightpreset.action", icon="FILE_TICK", text="Save to Blend").button="save"
            col.operator("gllightpreset.action", icon="SORTALPHA", text="Sort").button="sort"
            col.operator("gllightpreset.action", icon="SHORTDISPLAY", text="Add Defaults").button="defaults"
            col=box.row()
            col=col.column()
#Draw the text box
            count=len(scn.gllightpreset)
            if count>0:
                entry=scn.gllightpreset[scn.gllightpreset_index]
                lastname=entry.name

                if entry.count==0:
                    col.prop(entry, "name", text="")
                if entry.count> 0:
                    col.prop(entry, "name", text="")
                if bpy.context.view_layer.objects.active != None:
                    name=bpy.context.view_layer.objects.active.get("gllightpreset", "Default")
#Draw the import/export part of the box
                col.prop(scn,'importexport')
                if scn.importexport:
                    split = box.split(percentage=0.5)
                    col = split.column()
                    col.label(text="Import Directory or File")
                    col.prop(scn, 'gllightpreset_importfile')
                    col.prop(scn, 'gllightpreset_importdirectory')
                    col.label(text="Export Directory or File")
                    col.prop(scn, 'gllightpreset_exportfile')
                    col.prop(scn, 'gllightpreset_exportdirectory')

                    split = split.split()
                    col = split.column()

                    col.label(text="")
                    col.operator("gllightpreset.action", icon="IMPORT", text="Import File").button="import"
                    col.operator("gllightpreset.action", icon="IMPORT", text="Import All").button="importall"
                    col.label(text="")
                    col.operator("gllightpreset.action", icon="EXPORT", text="Export Selection").button="export"
                    col.operator("gllightpreset.action", icon="EXPORT", text="Export All").button="exportall"


#The second box containing interface options is here
        #interface options
        box = layout.box().column(align=True)
        box.prop(scn,'interface')


        if scn.interface:
            #Orbit
            boxrow=box.row()
            boxrow.label(text="Orbit Style:")
            boxrow=box.row()
            boxrow.prop(inputs, "view_rotate_method", expand=True)

            #continuous grab
            boxrow=box.row()
            boxrow.prop(inputs, "use_mouse_continuous")

            #Color Picker
            boxrow=box.row()
            boxrow.label(text="Color Picker Type")
            boxrow=box.row()
            boxrow.row().prop(view, "color_picker_type", text="")

            #Align To
            boxrow=box.row()
            boxrow.label(text="Align New Objects To:")
            boxrow=box.row()
            boxrow.prop(edit, "object_align", text="")

##########################################
####### Registration Functions ############
##########################################
class quickprefproperties(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
            bpy.types.Scene.quickprefs = PointerProperty(
                    name="QuickPrefs Settings",
                    description="QuickPrefs render settings",
                    type=cls,
                    )
            #strings for file IO
            cls.gllightpreset_importfile = StringProperty(name = "",
                    subtype='FILE_PATH',
                    default=defaultfilepath
                    )

            cls.gllightpreset_importdirectory = StringProperty(name = "",
                    subtype='FILE_PATH',
                    default=defaultfilepath
                    )

            cls.gllightpreset_exportfile = StringProperty(name = "",
                    subtype='FILE_PATH',
                    default=defaultfilepath
                    )

            cls.gllightpreset_exportdirectory = StringProperty(
                    name = "",
                    subtype='FILE_PATH',
                    default=defaultfilepath
                    )

            cls.gllights = BoolProperty(
                    name='Lights',
                    default=True
                    )

            cls.gllightPresets = BoolProperty(
                    name='GL Light Presets',
                    default=True
                    )

            cls.interface = BoolProperty(
                    name='Interface',
                    default=True
                    )

            cls.importexport = BoolProperty(
                    name='Import/Export',
                    default=True
                    )

            cls.gllights = BoolProperty(
                    name='Lights',
                    default=True
                    )

            #important storage of stuff
            cls.gllightpreset = CollectionProperty(
                    type=gllightpreset
                    )

            cls.gllightpreset_index = IntProperty(
                    min=0,
                    default=0,
                    update=gllightpreset_index
                    )

    @classmethod
    def unregister(cls):
        del bpy.types.Scene.quickprefs

@persistent
def setup(s):
	#let the fun begin!
    gllightpreset_chooseLoadLocation(1)
    gllightpreset_scan(bpy.context)

def register():
    #aliases
    handler=bpy.app.handlers

    #register classes
    bpy.utils.register_class(PANEL)
    bpy.utils.register_class(gllightpreset)
    bpy.utils.register_class(SCENE_OT_gllightpreset)
    bpy.utils.register_class(quickprefproperties)

    #handler.scene_update_pre.append(gllightpreset_scan)
    handler.scene_update_pre.append(setup)
    #handler.load_post.append(setup)     #was crashing blender on new file load - comment for now




# unregistering and removing menus
def unregister():
    bpy.utils.unregister_class(PANEL)
    bpy.utils.unregister_class(gllightpreset)
    bpy.utils.unregister_class(SCENE_OT_gllightpreset)
    bpy.utils.unregister_class(quickprefproperties)
    bpy.app.handlers.scene_update_pre.remove(setup)

if __name__ == "__main__":
    register()
