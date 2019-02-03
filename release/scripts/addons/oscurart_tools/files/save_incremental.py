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
from bpy.types import Operator
import os


def saveBkp (self, context):
    fileFolder = os.path.dirname(bpy.data.filepath)
    versionFolder = os.path.join(fileFolder,"VERSIONS")
    
    #creo folder
    if os.path.exists(versionFolder):
        print("existe")
    else:
        os.mkdir(versionFolder)  
    
    #sin version a versionada
    if not bpy.data.filepath.count("_v"): 
        filelist = [file  for file in os.listdir(versionFolder) if file.count("_v") and not file.count("blend1")] 

        filelower = 0
        print(filelist)
        for file in filelist:
            if int(file.split(".")[0][-2:]) > filelower:
                filelower = int(file.split(".")[0][-2:])        

        savepath = "%s/VERSIONS/%s_v%02d.blend" % (os.path.dirname(bpy.data.filepath),bpy.path.basename(bpy.data.filepath).split('.')[0],filelower+1)   
        print("Copia versionada guardada.")   
        bpy.ops.wm.save_as_mainfile()
        bpy.ops.wm.save_as_mainfile(filepath=savepath, copy=True)        

    else:        
        #versionada a sin version
        if bpy.data.filepath.count("_v"):
            filename = "%s/../%s.blend" % (os.path.dirname(bpy.data.filepath),os.path.basename(bpy.data.filepath).rpartition(".")[0].rpartition("_")[0])
            print(filename)
            bpy.ops.wm.save_as_mainfile(filepath=filename, copy=True)       
        print("Copia sin version guardada.")


class saveIncrementalBackup (bpy.types.Operator):
    """Save incremental backup in versions folder"""
    bl_idname = "file.save_incremental_backup"
    bl_label = "Save Incremental Backup"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        saveBkp(self, context)
        return {'FINISHED'}
   

