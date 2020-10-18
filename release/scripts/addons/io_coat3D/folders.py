import bpy
import os

def InitFolders():

    platform = os.sys.platform
    coat3D = bpy.context.scene.coat3D

    #    Global variable foundExchangeFolder (True / False) guides these steps
    # 1. Read Exchange_folder.txt, if not success ->
    # 2. Try to find exchange folder from system hard drive, if not success -->
    # 3. Leave foundExchangeFolder = False 

    # 1. #################################################################

    if(platform == 'win32' or platform == 'darwin'):
        exchangeFile = os.path.expanduser("~") + os.sep + 'Documents' + os.sep + '3DC2Blender' + os.sep + 'Exchange_folder.txt'
    else:
        exchangeFile = os.path.expanduser("~") + os.sep + '3DC2Blender' + os.sep + 'Exchange_folder.txt'
    if(os.path.isfile(exchangeFile)):
        folderPath = ''

        folderPathh = open(exchangeFile)
        for line in folderPathh:
            folderPath = line
            break
        folderPathh.close()

        if(os.path.isdir(os.path.abspath(folderPath)) and folderPath.rfind('Exchange') >= 0):
            coat3D.exchangeFolder = folderPath
            return True, coat3D.exchangeFolder
    else:
        os.makedirs(os.path.dirname(exchangeFile))


    # 2. #################################################################

    if(platform == 'win32' or platform == 'darwin'):
        exchangeFolder = os.path.expanduser("~") + os.sep + 'Documents' + os.sep + 'Applinks' + os.sep + '3D-Coat' + os.sep +'Exchange'
    else:
        exchangeFolder = os.path.expanduser("~") + os.sep + '3D-CoatV4' + os.sep + 'Exchange'
        if not(os.path.isdir(exchangeFolder)):
            exchangeFolder = os.path.expanduser("~") + os.sep + '3D-CoatV3' + os.sep + 'Exchange'
    if(os.path.isdir(exchangeFolder)):
        coat3D.exchangeFolder = exchangeFolder
        
        Blender_folder = ("%s%sBlender"%(exchangeFolder,os.sep))

        if(not(os.path.isdir(Blender_folder))):
            os.makedirs(Blender_folder)
            Blender_folder1 = os.path.join(Blender_folder,"run.txt")
            file = open(Blender_folder1, "w")
            file.close()

            Blender_folder2 = os.path.join(Blender_folder, "extension.txt")
            file = open(Blender_folder2, "w")
            file.write("fbx")
            file.close()

            Blender_folder3 = os.path.join(Blender_folder, "preset.txt")
            file = open(Blender_folder3, "w")
            file.write("Blender Cycles")
            file.close()
        
        file = open(exchangeFile, "w")
        file.write("%s"%(os.path.abspath(coat3D.exchangeFolder)))
        file.close()

        return True, coat3D.exchangeFolder

    return False, ''


def updateExchangeFile(newPath):

    platform = os.sys.platform
    
    if(platform == 'win32' or platform == 'darwin'):
        exchangeFile = os.path.expanduser("~") + os.sep + 'Documents' + os.sep + '3DC2Blender' + os.sep + 'Exchange_folder.txt'
    else:
        exchangeFile = os.path.expanduser("~") + os.sep + '3DC2Blender' + os.sep + 'Exchange_folder.txt'
    if(os.path.isfile(exchangeFile)):
        folderPath = ''
    
    if(os.path.isfile(exchangeFile)):
        file = open(exchangeFile, "w")
        file.write("%s"%(newPath))
        file.close()

def set_working_folders():

    platform = os.sys.platform
    coat3D = bpy.context.scene.coat3D

    if(platform == 'win32' or platform == 'darwin'):
        if (coat3D.defaultfolder != '' and os.path.isdir(coat3D.defaultfolder)):
            return coat3D.defaultfolder
        else:
            folder_objects = os.path.expanduser("~") + os.sep + 'Documents' + os.sep + '3DC2Blender' + os.sep + 'ApplinkObjects'
            if(not(os.path.isdir(folder_objects))):
                os.makedirs(folder_objects)
    else:
        if (coat3D.defaultfolder != '' and os.path.isdir(coat3D.defaultfolder)):
            return coat3D.defaultfolder
        else:
            folder_objects = os.path.expanduser("~") + os.sep + '3DC2Blender' + os.sep + 'ApplinkObjects'
            if(not(os.path.isdir(folder_objects))):
                os.makedirs(folder_objects)

    return folder_objects
