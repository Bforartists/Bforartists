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
    "name": "3D-Coat Applink",
    "author": "Kalle-Samuli Riihikoski (haikalle)",
    "version": (5, 0, 00),
    "blender": (2, 80, 0),
    "location": "Scene > 3D-Coat Applink",
    "description": "Transfer data between 3D-Coat/Blender",
    "warning": "",
    "wiki_url": "https://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/Import-Export/3dcoat_applink",
    "category": "3D View",
}


if "bpy" in locals():
    import importlib
    importlib.reload(coat)
    importlib.reload(tex)
else:
    from . import tex

from io_coat3D import tex
import os
import ntpath
import re

import time
import bpy
import subprocess
from bpy.types import PropertyGroup
from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatVectorProperty,
        StringProperty,
        PointerProperty,
        )


bpy.coat3D = dict()
bpy.coat3D['active_coat'] = ''
bpy.coat3D['status'] = 0

def update_exe_path():
    if (bpy.context.scene.coat3D.coat3D_exe != ''):
        importfile = bpy.context.scene.coat3D.exchangedir
        importfile += ('%scoat3D_exe.txt' % (os.sep))
        print('Filepath: ',importfile)
        file = open(importfile, "w")
        file.write("%s" % (bpy.context.scene.coat3D.coat3D_exe))
        file.close()

def folder_size(path):

    tosi = True
    while tosi:
        list_of_files = []
        for file in os.listdir(path):
            list_of_files.append(path + os.sep + file)

        if len(list_of_files) >= 400:
            oldest_file = min(list_of_files, key=os.path.getctime)
            os.remove(os.path.abspath(oldest_file))
        else:
            tosi = False

def set_exchange_folder():
    platform = os.sys.platform
    coat3D = bpy.context.scene.coat3D
    Blender_export = ""

    if(platform == 'win32'):
        exchange = os.path.expanduser("~") + os.sep + 'Documents' + os.sep + 'Applinks' + os.sep + '3D-Coat' + os.sep +'Exchange'
    else:
        exchange = os.path.expanduser("~") + os.sep + '3D-CoatV4' + os.sep + 'Exchange'
        if not(os.path.isdir(exchange)):
            exchange = os.path.expanduser("~") + os.sep + '3D-CoatV3' + os.sep + 'Exchange'
    if(not(os.path.isdir(exchange))):
        exchange = coat3D.exchangedir

    if(os.path.isdir(exchange)):
        bpy.coat3D['status'] = 1
        if(platform == 'win32'):
            exchange_path = os.path.expanduser("~") + os.sep + 'Documents' + os.sep + '3DC2Blender' + os.sep + 'Exchange_folder.txt'
            applink_folder = os.path.expanduser("~") + os.sep + 'Documents' + os.sep + '3DC2Blender'
            if(not(os.path.isdir(applink_folder))):
                os.makedirs(applink_folder)
        else:
            exchange_path = os.path.expanduser("~") + os.sep + 'Documents' + os.sep + '3DC2Blender' + os.sep + 'Exchange_folder.txt'
            applink_folder = os.path.expanduser("~") + os.sep + 'Documents' + os.sep + '3DC2Blender'
            if(not(os.path.isdir(applink_folder))):
                os.makedirs(applink_folder)
        file = open(exchange_path, "w")
        file.write("%s"%(coat3D.exchangedir))
        file.close()

    else:
        if(platform == 'win32'):
            exchange_path = os.path.expanduser("~") + os.sep + 'Documents' + os.sep + '3DC2Blender' + os.sep + 'Exchange_folder.txt'
        else:
            exchange_path = os.path.expanduser("~") + os.sep + '3DC2Blender' + os.sep + 'Exchange_folder.txt'
        if(os.path.isfile(exchange_path)):
            ex_path =''

            ex_pathh = open(exchange_path)
            for line in ex_pathh:
                ex_path = line
                break
            ex_pathh.close()

            if(os.path.isdir(ex_path) and ex_path.rfind('Exchange') >= 0):
                exchange = ex_path
                bpy.coat3D['status'] = 1
            else:
                bpy.coat3D['status'] = 0
        else:
            bpy.coat3D['status'] = 0
    if(bpy.coat3D['status'] == 1):
        Blender_folder = ("%s%sBlender"%(exchange,os.sep))
        Blender_export = Blender_folder
        path3b_now = exchange
        path3b_now += ('last_saved_3b_file.txt')
        Blender_export += ('%sexport.txt'%(os.sep))

        if(not(os.path.isdir(Blender_folder))):
            os.makedirs(Blender_folder)
            Blender_folder = os.path.join(Blender_folder,"run.txt")
            file = open(Blender_folder, "w")
            file.close()
    return exchange

def set_working_folders():
    platform = os.sys.platform
    coat3D = bpy.context.scene.coat3D

    if(platform == 'win32'):
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

def make_texture_list(texturefolder):
    texturefolder += ('%stextures.txt'%(os.sep))
    texturelist = []

    if (os.path.isfile(texturefolder)):
        texturefile = open(texturefolder)
        index = 0
        for line in texturefile:
            if line != '' and index == 0:
                line = line.rstrip('\n')
                objekti = line
                index += 1
            elif index == 1:
                line = line.rstrip('\n')
                material = line
                index += 1
            elif index == 2:
                line = line.rstrip('\n')
                type = line
                index += 1
            elif index == 3:
                line = line.rstrip('\n')
                address = line
                texturelist.append([objekti,material,type,address])
                index = 0
        texturefile.close()
    return texturelist


'''
#Updating objects MESH part ( Mesh, Vertex Groups, Vertex Colors )
'''

def updatemesh(objekti, proxy):


    #TO DO VERTEX GROUPS, gives an error with this code.

    if(objekti.vertex_groups.keys() != []):
        bpy.ops.object.select_all(action='DESELECT')
        proxy.select_set(True)
        objekti.select_set(True)
        bpy.ops.object.vertex_group_copy_to_selected()
        bpy.ops.object.select_all(action='DESELECT')

    # UV Set Copy

    proxy.select_set(True)
    objekti.select_set(True)

    if len(objekti.data.uv_layers) > 1:
        obj_uv_index =  objekti.data.uv_layers.active_index
        index = 0
        for uv_layer in objekti.data.uv_layers:
            if (uv_layer != objekti.data.uv_layers[0]):
                proxy.data.uv_layers.new(name=uv_layer.name)
                proxy.data.uv_layers.active_index = index
                objekti.data.uv_layers.active_index = index
                bpy.ops.object.join_uvs()
            index += 1
        proxy.data.uv_layers.active_index = obj_uv_index

    bpy.ops.object.select_all(action='DESELECT')

    #Mesh Copy

    proxy.select_set(True)
    obj_data = objekti.data.id_data
    objekti.data = proxy.data.id_data
    objekti.data.id_data.name = obj_data.name
    if (bpy.data.meshes[obj_data.name].users == 0):
        bpy.data.meshes.remove(obj_data)

def running():
    n=0# number of instances of the program running
    prog=[line.split() for line in subprocess.check_output("tasklist").splitlines()]
    [prog.pop(e) for e in [0,1,2]] #useless
    for task in prog:
        if str(task[0]) == "b'3D-CoatDX64C.exe'" or str(task[0]) == "b'3D-CoatGL64C.exe'":
            n+=1
            break
    if n>0:
        return True
    else:
        return False

class SCENE_OT_folder(bpy.types.Operator):
    bl_idname = "update_exchange_folder.pilgway_3d_coat"
    bl_label = "Export your custom property"
    bl_description = "Export your custom property"
    bl_options = {'UNDO'}

    def invoke(self, context, event):
        coat3D = bpy.context.scene.coat3D

        if(os.path.isdir(coat3D.exchangedir)):
            coat3D.exchange_found = True
        else:
            coat3D.exchange_found = False

        return {'FINISHED'}

class SCENE_OT_opencoat(bpy.types.Operator):
    bl_idname = "open_3dcoat.pilgway_3d_coat"
    bl_label = "Export your custom property"
    bl_description = "Export your custom property"
    bl_options = {'UNDO'}

    def invoke(self, context, event):

        update_exe_path()

        exefile = bpy.context.scene.coat3D.exchangedir
        exefile += ('%scoat3D_exe.txt' % (os.sep))
        exe_path = ''
        if (os.path.isfile(exefile)):

            ex_pathh = open(exefile)
            for line in ex_pathh:
                exe_path = line
                break
            ex_pathh.close()

        coat3D = bpy.context.selected_objects[0].coat3D.applink_3b_path
        platform = os.sys.platform
        prog_path = os.environ['PROGRAMFILES']
        if (platform == 'win32'):

            active_3dcoat = exe_path

            if running() == False:
                print('tulele tanne')
                os.popen('"' + active_3dcoat + '" ' + coat3D)
            else:
                importfile = bpy.context.scene.coat3D.exchangedir
                importfile += ('%simport.txt' % (os.sep))
                file = open(importfile, "w")
                file.write("%s" % (coat3D))
                file.write("\n%s" % (coat3D))
                file.write("\n[3B]")
                file.close()

                '''
                If not Windows Os it will only write import.txt. Auto run 3d-coat.exe is disabled.
                '''

        else:
            importfile = bpy.context.scene.coat3D.exchangedir
            importfile += ('%simport.txt' % (os.sep))
            file = open(importfile, "w")
            file.write("%s" % (coat3D))
            file.write("\n%s" % (coat3D))
            file.write("\n[3B]")
            file.close()



        return {'FINISHED'}

class SCENE_OT_export(bpy.types.Operator):
    bl_idname = "export_applink.pilgway_3d_coat"
    bl_label = "Export your custom property"
    bl_description = "Export your custom property"
    bl_options = {'UNDO'}

    def invoke(self, context, event):



        for mesh in bpy.data.meshes:
            if (mesh.users == 0 and mesh.coat3D.name == '3DC'):
                bpy.data.meshes.remove(mesh)

        for material in bpy.data.materials:
            if (material.users == 1 and material.coat3D.name == '3DC'):
                bpy.data.materials.remove(material)

        export_ok = False
        coat3D = bpy.context.scene.coat3D

        if (bpy.context.selected_objects == []):
            return {'FINISHED'}
        else:
            for objec in bpy.context.selected_objects:
                if objec.type == 'MESH':
                    export_ok = True
            if (export_ok == False):
                return {'FINISHED'}

        activeobj = bpy.context.active_object.name
        checkname = ''
        coa = bpy.context.active_object.coat3D
        coat3D.exchangedir = set_exchange_folder()

        update_exe_path()

        if (not os.path.isdir(coat3D.exchangedir)):
            coat3D.exchange_found = False
            return {'FINISHED'}


        folder_objects = set_working_folders()
        folder_size(folder_objects)

        importfile = coat3D.exchangedir
        texturefile = coat3D.exchangedir
        importfile += ('%simport.txt'%(os.sep))
        texturefile += ('%stextures.txt'%(os.sep))

        looking = True
        object_index = 0

        if(coat3D.type == 'autopo'):
            checkname = folder_objects + os.sep
            checkname = ("%sretopo.fbx" % (checkname))

        else:
            while(looking == True):
                checkname = folder_objects + os.sep + "3DC"
                checkname = ("%s%.3d.fbx"%(checkname,object_index))
                if(os.path.isfile(checkname)):
                    object_index += 1
                else:
                    looking = False
                    coa.applink_name = ("%s%.2d"%(activeobj,object_index))
                    coa.applink_address = checkname

        matindex = 0

        for objekti in bpy.context.selected_objects:
            if(objekti.material_slots.keys() == []):
                newmat = bpy.data.materials.new('Material')
                newmat.use_nodes = True
                objekti.data.materials.append(newmat)
                matindex += 1
            new_name = objekti.data.name
            name_boxs = new_name.split('.')
            if(len(name_boxs)>1):
                objekti.name = name_boxs[0] + name_boxs[1]
                nimi = name_boxs[0] + name_boxs[1]
                nimiNum = int(name_boxs[1])
                looking = False
                lyytyi = False
                while(looking == False):
                    for all_ob in bpy.data.meshes:
                        numero = ("%.3d"%(nimiNum))
                        nimi2 = name_boxs[0] + numero
                        if(all_ob.name == nimi2):
                            lyytyi = True
                            break
                        else:
                            lyytyi = False

                    if(lyytyi == True):
                        nimiNum += 1
                    else:
                        looking = True
                objekti.data.name = nimi2
                objekti.name = nimi2



            else:
                objekti.name = name_boxs[0]
                objekti.data.name = name_boxs[0]
            objekti.coat3D.applink_name = objekti.data.name
        mod_mat_list = {}
        for objekti in bpy.context.selected_objects:
            mod_mat_list[objekti.name] = []
            objekti.coat3D.applink_scale = objekti.scale

            ''' Checks what materials are linked into UV '''

            if(coat3D.type == 'ppp'):
                final_material_indexs = []
                uvtiles_index = []
                for poly in objekti.data.polygons:
                    if(poly.material_index not in final_material_indexs):
                        final_material_indexs.append(poly.material_index)
                        loop_index = poly.loop_indices[0]
                        uvtiles_index.append([poly.material_index,objekti.data.uv_layers.active.data[loop_index].uv[0]])
                    if(len(final_material_indexs) == len(objekti.material_slots)):
                        break

                material_index = 0
                if (len(final_material_indexs) != len(objekti.material_slots)):
                    for material in objekti.material_slots:
                        if material_index not in final_material_indexs:
                            temp_mat = material.material
                            material.material = objekti.material_slots[0].material
                            mod_mat_list[objekti.name].append([material_index, temp_mat])
                        material_index = material_index + 1

        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
        if(len(bpy.context.selected_objects) > 1 and coat3D.type != 'vox'):
            bpy.ops.object.transforms_to_deltas(mode='ROT')

        if(coat3D.type == 'autopo'):
            coat3D.bring_retopo = True
            coat3D.bring_retopo_path = checkname
            bpy.ops.export_scene.fbx(filepath=checkname, use_selection=True, use_mesh_modifiers=coat3D.exportmod, axis_forward='-Z', axis_up='Y')
        else:
            coat3D.bring_retopo = False
            bpy.ops.export_scene.fbx(filepath=coa.applink_address, use_selection=True, use_mesh_modifiers=coat3D.exportmod, axis_forward='-Z', axis_up='Y')

        file = open(importfile, "w")
        file.write("%s"%(checkname))
        file.write("\n%s"%(checkname))
        file.write("\n[%s]"%(coat3D.type))
        file.close()
        group_index = -1.0
        for idx, objekti in enumerate(bpy.context.selected_objects):

            if(len(bpy.context.selected_objects) == 1):
                objekti.coat3D.applink_onlyone = True
            objekti.coat3D.type = coat3D.type
            objekti.coat3D.applink_mesh = True
            objekti.coat3D.obj_mat = ''
            objekti.coat3D.applink_firsttime = True
            if(coat3D.type != 'autopo'):
                objekti.coat3D.applink_address = coa.applink_address
                objekti.coat3D.objecttime = str(os.path.getmtime(objekti.coat3D.applink_address))
            objekti.data.coat3D.name = '3DC'

            if(coat3D.type != 'vox'):
                if(objekti.material_slots.keys() != []):
                    for material in objekti.material_slots:
                        if material.material.use_nodes == True:
                            for node in material.material.node_tree.nodes:
                                if(node.name.startswith('3DC_') == True):
                                    material.material.node_tree.nodes.remove(node)


            for ind, mat_list in enumerate(mod_mat_list):
                if(mat_list == objekti.name):
                    for ind, mat in enumerate(mod_mat_list[mat_list]):
                        objekti.material_slots[mod_mat_list[mat_list][ind][0]].material = mod_mat_list[mat_list][ind][1]

        return {'FINISHED'}

class SCENE_OT_import(bpy.types.Operator):
    bl_idname = "import_applink.pilgway_3d_coat"
    bl_label = "import your custom property"
    bl_description = "import your custom property"
    bl_options = {'UNDO'}

    def invoke(self, context, event):

        update_exe_path()

        for node_group in bpy.data.node_groups:
            if(node_group.users == 0):
                bpy.data.node_groups.remove(node_group)

        for mesh in bpy.data.meshes:
            if(mesh.users == 0 and mesh.coat3D.name == '3DC'):
                bpy.data.meshes.remove(mesh)

        for material in bpy.data.materials:
            img_list = []
            if (material.users == 1 and material.coat3D.name == '3DC'):
                if material.use_nodes == True:
                    for node in material.node_tree.nodes:
                        if node.type == 'TEX_IMAGE' and node.name.startswith('3DC'):
                            img_list.append(node.image)
                if img_list != []:
                    for del_img in img_list:
                        bpy.data.images.remove(del_img)

                bpy.data.materials.remove(material)

        coat3D = bpy.context.scene.coat3D
        coat = bpy.coat3D
        coat3D.exchangedir = set_exchange_folder()


        texturelist = make_texture_list(coat3D.exchangedir)
        for texturepath in texturelist:
            for image in bpy.data.images:
                if(image.filepath == texturepath[3] and image.users == 0):
                    bpy.data.images.remove(image)


        kokeilu = coat3D.exchangedir
        Blender_folder = ("%s%sBlender"%(kokeilu,os.sep))
        Blender_export = Blender_folder
        path3b_now = coat3D.exchangedir
        path3b_now += ('last_saved_3b_file.txt')
        Blender_export += ('%sexport.txt'%(os.sep))
        new_applink_address = 'False'
        new_object = False
        print('mitas: ', Blender_export)
        if(os.path.isfile(Blender_export)):
            obj_pathh = open(Blender_export)
            new_object = True
            for line in obj_pathh:
                new_applink_address = line
                break
            obj_pathh.close()

            for scene_objects in bpy.context.collection.all_objects:
                if(scene_objects.type == 'MESH'):
                    if(scene_objects.coat3D.applink_address == new_applink_address):
                        new_object = False

        exportfile = coat3D.exchangedir
        exportfile += ('%sBlender' % (os.sep))
        exportfile += ('%sexport.txt' % (os.sep))
        if (os.path.isfile(exportfile)):
            os.remove(exportfile)

        if(new_object == False):

            '''
            #Blender -> 3DC -> Blender workflow
            #First check if objects needs to be imported, if imported it will then delete extra mat and objs.
            '''

            old_materials = bpy.data.materials.keys()
            old_objects = bpy.data.objects.keys()
            cache_base = bpy.data.objects.keys()

            object_list = []
            import_list = []
            import_type = []

            for objekti in bpy.data.objects:
                if objekti.type == 'MESH':
                    obj_coat = objekti.coat3D
                    if(obj_coat.applink_mesh == True):
                        object_list.append(objekti.name)

                        if(os.path.isfile(obj_coat.applink_address)):
                            if (obj_coat.objecttime != str(os.path.getmtime(obj_coat.applink_address))):
                                obj_coat.dime = objekti.dimensions
                                obj_coat.import_mesh = True
                                obj_coat.objecttime = str(os.path.getmtime(obj_coat.applink_address))
                                if(obj_coat.applink_address not in import_list):
                                    import_list.append(obj_coat.applink_address)
                                    import_type.append(coat3D.type)

            if(import_list or coat3D.importmesh):
                print('import_list:', import_list)
                for idx, list in enumerate(import_list):
                    bpy.ops.import_scene.fbx(filepath=list, global_scale = 1,axis_forward='X',use_custom_normals=False)
                    cache_objects = bpy.data.objects.keys()
                    cache_objects = [i for i in cache_objects if i not in cache_base]
                    for cache_object in cache_objects:
                        bpy.data.objects[cache_object].coat3D.type = import_type[idx]
                        bpy.data.objects[cache_object].coat3D.applink_address = list
                        cache_base.append(cache_object)


                bpy.ops.object.select_all(action='DESELECT')

                new_materials = bpy.data.materials.keys()
                new_objects = bpy.data.objects.keys()
                new_images = bpy.data.images.keys()


                diff_mat = [i for i in new_materials if i not in old_materials]
                diff_objects = [i for i in new_objects if i not in old_objects]

                for mark_mesh in diff_objects:
                    bpy.data.objects[mark_mesh].data.coat3D.name = '3DC'
                for c_index in diff_mat:
                    bpy.data.materials.remove(bpy.data.materials[c_index])
            '''The main Applink Object Loop'''

            remove_path = True
            for oname in object_list:
                objekti = bpy.data.objects[oname]
                if(objekti.coat3D.applink_mesh == True):
                    exportfile = coat3D.exchangedir
                    path3b_n = coat3D.exchangedir
                    path3b_n += ('%slast_saved_3b_file.txt' % (os.sep))
                    if(objekti.coat3D.import_mesh and coat3D.importmesh == True):
                        objekti.coat3D.import_mesh = False
                        objekti.select_set(True)

                        use_smooth = objekti.data.polygons[0].use_smooth

                        new_name = objekti.data.name
                        name_boxs = new_name.split('.')
                        found_obj = False

                        '''Changes objects mesh into proxy mesh'''
                        print('ONAME:',oname)
                        if(objekti.coat3D.type):
                            for proxy_objects in diff_objects:
                                print('tryis to found: ',proxy_objects)
                                if (proxy_objects.startswith(objekti.coat3D.applink_name + '.')):
                                    obj_proxy = bpy.data.objects[proxy_objects]
                                    obj_proxy.coat3D.delete_proxy_mesh = True
                                    found_obj = True

                        mat_list = []
                        if (objekti.material_slots):
                            act_mat = objekti.active_material
                            for obj_mat in objekti.material_slots:
                                mat_list.append(obj_mat.material)

                        if(found_obj == True):
                            exportfile = coat3D.exchangedir
                            path3b_n = coat3D.exchangedir
                            path3b_n += ('%slast_saved_3b_file.txt' % (os.sep))
                            exportfile += ('%sBlender' % (os.sep))
                            exportfile += ('%sexport.txt'%(os.sep))
                            if(os.path.isfile(exportfile)):
                                export_file = open(exportfile)
                                for line in export_file:
                                    if line.rfind('.3b'):
                                        coat['active_coat'] = line
                                export_file.close()
                                os.remove(exportfile)
                            if(os.path.isfile(path3b_n)):
                                export_file = open(path3b_n)
                                for line in export_file:
                                    objekti.coat3D.applink_3b_path = line
                                export_file.close()
                                coat3D.remove_path = True



                            bpy.ops.object.select_all(action='DESELECT')
                            obj_proxy.select_set(True)

                            bpy.ops.object.select_all(action='TOGGLE')

                            if objekti.coat3D.applink_firsttime == True and objekti.coat3D.type == 'vox':
                                objekti.select_set(True)

                                objekti.rotation_euler[0] = 1.5708
                                objekti.rotation_euler[2] = 1.5708
                                bpy.ops.object.transforms_to_deltas(mode='ROT')
                                objekti.scale = (0.01, 0.01, 0.01)
                                bpy.ops.object.transforms_to_deltas(mode='SCALE')
                                objekti.coat3D.applink_firsttime = False
                                objekti.select_set(False)

                            elif objekti.coat3D.applink_firsttime == True:
                                objekti.scale = (objekti.scale[0]/objekti.coat3D.applink_scale[0],objekti.scale[1]/objekti.coat3D.applink_scale[1],objekti.scale[2]/objekti.coat3D.applink_scale[2])
                                bpy.ops.object.transforms_to_deltas(mode='SCALE')
                                if(objekti.coat3D.applink_onlyone == False):
                                    objekti.rotation_euler = (0,0,0)
                                objekti.scale = (0.01,0.01,0.01)
                                objekti.coat3D.applink_firsttime = False

                            if(coat3D.importlevel):
                                obj_proxy.select = True
                                obj_proxy.modifiers.new(name='temp',type='MULTIRES')
                                objekti.select = True
                                bpy.ops.object.multires_reshape(modifier=multires_name)
                                bpy.ops.object.select_all(action='TOGGLE')
                                multires_on = False
                            else:
                                updatemesh(objekti,obj_proxy)

                            #tärkee että saadaan oikein käännettyä objekt

                            objekti.select_set(True)
                            bpy.ops.object.origin_set(type='GEOMETRY_ORIGIN')

                            objekti.data.materials.pop()
                            for mat in mat_list:
                                objekti.data.materials.append(mat)

                            if (use_smooth):
                                for data_mesh in objekti.data.polygons:
                                    data_mesh.use_smooth = True
                            else:
                                for data_mesh in objekti.data.polygons:
                                    data_mesh.use_smooth = False

                                bpy.ops.object.select_all(action='DESELECT')

                            if(coat3D.importmesh and not(os.path.isfile(objekti.coat3D.applink_address))):
                                coat3D.importmesh = False

                            objekti.select_set(True)
                        if(coat3D.importtextures):
                            is_new = False
                            tex.matlab(objekti,mat_list,texturelist,is_new)
                        objekti.select_set(False)
                    else:
                        print('JAAKO TAHAN KOHTAAN 2')
                        mat_list = []
                        if (objekti.material_slots):
                            for obj_mat in objekti.material_slots:
                                mat_list.append(obj_mat.material)

                        if (coat3D.importtextures):
                            is_new = False
                            tex.matlab(objekti,mat_list,texturelist, is_new)
                        objekti.select_set(False)

            if(coat3D.remove_path == True):
                os.remove(path3b_n)
                coat3D.remove_path = False

            bpy.ops.object.select_all(action='DESELECT')
            if(import_list):
                for del_obj in diff_objects:
                    print('diff_objects', diff_objects)

                    if(bpy.context.collection.all_objects[del_obj].coat3D.type == 'vox' and bpy.context.collection.all_objects[del_obj].coat3D.delete_proxy_mesh == False):
                        bpy.context.collection.all_objects[del_obj].select_set(True)
                        objekti = bpy.context.collection.all_objects[del_obj]
                        objekti.rotation_euler[2] = 1.5708
                        bpy.ops.object.transforms_to_deltas(mode='ROT')
                        # objekti.rotation_euler = (0, 0, 0)
                        objekti.scale = (0.02, 0.02, 0.02)
                        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')

                        objekti.data.coat3D.name = '3DC'

                        objekti.coat3D.objecttime = str(os.path.getmtime(objekti.coat3D.applink_address))
                        objekti.coat3D.applink_name = objekti.name
                        objekti.coat3D.applink_mesh = True
                        objekti.coat3D.import_mesh = False
                        bpy.ops.object.transforms_to_deltas(mode='SCALE')
                        objekti.coat3D.applink_firsttime = False
                        bpy.context.collection.all_objects[del_obj].select_set(False)

                    else:
                        bpy.context.collection.all_objects[del_obj].select_set(True)
                        bpy.ops.object.delete()

            if (coat3D.bring_retopo or coat3D.bring_retopo_path):
                if(os.path.isfile(coat3D.bring_retopo_path)):
                    bpy.ops.import_scene.fbx(filepath=coat3D.bring_retopo_path, global_scale=1, axis_forward='X', use_custom_normals=False)
                    os.remove(coat3D.bring_retopo_path)


        else:

            '''
            3DC -> Blender workflow
            '''

            for old_obj in bpy.context.collection.objects:
                old_obj.coat3D.applink_old = True

            coat3D = bpy.context.scene.coat3D
            scene = context.scene
            Blender_folder = ("%s%sBlender"%(coat3D.exchangedir,os.sep))
            Blender_export = Blender_folder
            path3b_now = coat3D.exchangedir + os.sep
            path3b_now += ('last_saved_3b_file.txt')
            Blender_export += ('%sexport.txt'%(os.sep))
            mat_list = []
            osoite_3b = ''
            if (os.path.isfile(path3b_now)):
                path3b_fil = open(path3b_now)
                for lin in path3b_fil:
                    osoite_3b = lin
                path3b_fil.close()
                head, tail = os.path.split(osoite_3b)
                just_3b_name = tail
                os.remove(path3b_now)

            old_materials = bpy.data.materials.keys()
            old_objects = bpy.data.objects.keys()

            bpy.ops.import_scene.fbx(filepath=new_applink_address, global_scale = 1, use_manual_orientation=True, axis_forward='-Z', axis_up='Y', use_custom_normals=False)

            new_materials = bpy.data.materials.keys()
            new_objects = bpy.data.objects.keys()

            diff_mat = [i for i in new_materials if i not in old_materials]
            diff_objects = [i for i in new_objects if i not in old_objects]

            for mark_mesh in diff_mat:
                bpy.data.materials[mark_mesh].coat3D.name = '3DC'
                bpy.data.materials[mark_mesh].use_fake_user = True
            laskuri = 0
            index = 0
            for c_index in diff_objects:
                bpy.data.objects[c_index].data.coat3D.name = '3DC'
                bpy.data.objects[c_index].material_slots[0].material = bpy.data.materials[diff_mat[laskuri]]
                laskuri += 1


            bpy.ops.object.select_all(action='DESELECT')
            for new_obj in bpy.context.collection.objects:

                if(new_obj.coat3D.applink_old == False):
                    new_obj.select_set(True)
                    #bpy.ops.object.origin_set(type='GEOMETRY_ORIGIN')
                    #new_obj.rotation_euler = (0, 0, 0)
                    #new_obj.scale = (0.01, 0.01, 0.01)
                    new_obj.coat3D.applink_firsttime = False
                    new_obj.select_set(False)
                    new_obj.coat3D.applink_address = new_applink_address
                    new_obj.coat3D.applink_mesh = True
                    new_obj.coat3D.objecttime = str(os.path.getmtime(new_obj.coat3D.applink_address))

                    new_obj.coat3D.applink_name = new_obj.material_slots[0].material.name
                    index = index + 1

                    new_obj.coat3D.applink_export = True
                    if(osoite_3b != ''):
                        new_obj.coat3D.applink_3b_path = osoite_3b
                        new_obj.coat3D.applink_3b_just_name = just_3b_name

                    mat_list.append(new_obj.material_slots[0].material)
                    is_new = True
                    tex.matlab(new_obj, mat_list, texturelist, is_new)
                    mat_list.pop()

            for new_obj in bpy.context.collection.objects:
                if(new_obj.coat3D.applink_old == False):
                    new_obj.coat3D.applink_old = True

            bpy.ops.object.select_all(action='SELECT')
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
            bpy.ops.object.select_all(action='DESELECT')

            kokeilu = coat3D.exchangedir[:-10]
            Blender_folder2 = ("%s%sExchange%sBlender" % (kokeilu, os.sep, os.sep))
            Blender_folder2 += ('%sexport.txt' % (os.sep))

            if (os.path.isfile(Blender_export)):
                os.remove(Blender_export)
            if (os.path.isfile(Blender_folder2)):
                os.remove(Blender_folder2)
            for material in bpy.data.materials:
                if material.use_nodes == True:
                    for node in material.node_tree.nodes:
                        if (node.name).startswith('3DC'):
                            node.location = node.location

        return {'FINISHED'}

from bpy import *
from mathutils import Vector, Matrix

class SCENE_PT_Main(bpy.types.Panel):
    bl_label = "3D-Coat Applink"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = 'View'

    @classmethod
    def poll(cls, context):
        if bpy.context.mode == 'OBJECT':
            return True
        else:
            return False

    def draw(self, context):
        layout = self.layout
        coat = bpy.coat3D
        coat3D = bpy.context.scene.coat3D
        if(bpy.context.active_object):
            coa = bpy.context.active_object.coat3D
        if(coat['status'] == 0):
            row = layout.row()
            row.label(text="Applink didn't find your 3d-Coat/Excahnge folder.")
            row = layout.row()
            row.label("Please select it before using Applink.")
            row = layout.row()
            row.prop(coat3D,"exchangedir",text="")
            row = layout.row()
            row.operator("update_exchange_folder.pilgway_3d_coat", text="Apply folder")

        else:

            #Here you add your GUI
            row = layout.row()
            row.prop(coat3D,"type",text = "")
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=False, even_rows=False, align=True)

            col = flow.column()

            col.operator("export_applink.pilgway_3d_coat", text="Transfer")
            col = flow.column()
            col.operator("import_applink.pilgway_3d_coat", text="Update")




class ObjectButtonsPanel():
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

class SCENE_PT_Settings(ObjectButtonsPanel,bpy.types.Panel):
    bl_label = "3D-Coat Applink Settings"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        pass

class SCENE_PT_Settings_Update(ObjectButtonsPanel, bpy.types.Panel):
    bl_label = "Update"
    bl_parent_id = "SCENE_PT_Settings"
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        coat3D = bpy.context.scene.coat3D

        rd = context.scene.render

        layout.active = True

        flow = layout.grid_flow(row_major=True, columns=0, even_columns=False, even_rows=False, align=True)

        col = flow.column()
        col.prop(coat3D, "importmesh", text="Update Mesh/UV")
        col = flow.column()
        col.prop(coat3D, "createnodes", text="Create Extra Nodes")
        col = flow.column()
        col.prop(coat3D, "importtextures", text="Update Textures")
        col = flow.column()
        col.prop(coat3D, "exportmod", text="Export with modifiers")

class SCENE_PT_Settings_Folders(ObjectButtonsPanel, bpy.types.Panel):
    bl_label = "Folders"
    bl_parent_id = "SCENE_PT_Settings"
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        coat3D = bpy.context.scene.coat3D

        rd = context.scene.render

        layout.active = True

        flow = layout.grid_flow(row_major=True, columns=0, even_columns=False, even_rows=False, align=True)

        col = flow.column()
        col.prop(coat3D, "exchangedir", text="Exchange folder")

        col = flow.column()
        col.prop(coat3D, "defaultfolder", text="Object/Texture folder")

        col = flow.column()
        col.prop(coat3D, "coat3D_exe", text="3D-Coat.exe")

# 3D-Coat Dynamic Menu
class VIEW3D_MT_Coat_Dynamic_Menu(bpy.types.Menu):
    bl_label = "3D-Coat Applink Menu"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_WIN'

        ob = context
        if ob.mode == 'OBJECT':
            if(len(context.selected_objects) > 0):
                layout.operator("import_applink.pilgway_3d_coat", text="Update Scene")
                layout.separator()

                layout.operator("export_applink.pilgway_3d_coat", text="Copy selected object(s) into 3D-Coat")
                layout.separator()
                if(context.selected_objects[0].coat3D.applink_3b_path != ''):
                    layout.operator("open_3dcoat.pilgway_3d_coat", text="Open .3b file" +context.selected_objects[0].coat3D.applink_3b_just_name)
                    layout.separator()

            else:
                layout.operator("import_applink.pilgway_3d_coat", text="Update Scene")
                layout.separator()



class ObjectCoat3D(PropertyGroup):

    obj_mat: StringProperty(
        name="Object_Path",
        default=''
    )
    applink_address: StringProperty(
        name="Object_Applink_address"
    )
    applink_3b_path: StringProperty(
        name="Object_3B_Path"
    )
    applink_name: StringProperty(
        name="Applink object name"
    )
    applink_3b_just_name: StringProperty(
        name="Applink object name"
    )
    applink_firsttime: BoolProperty(
        name="FirstTime",
        description="FirstTime",
        default=True
    )
    delete_proxy_mesh: BoolProperty(
        name="FirstTime",
        description="FirstTime",
        default=False
    )
    applink_onlyone: BoolProperty(
        name="FirstTime",
        description="FirstTime",
        default=False
    )
    type: StringProperty(
        name="type",
        description="shows type",
        default=''
    )
    import_mesh: BoolProperty(
        name="ImportMesh",
        description="ImportMesh",
        default=False
    )
    applink_mesh: BoolProperty(
        name="ImportMesh",
        description="ImportMesh",
        default=False
    )
    applink_old: BoolProperty(
        name="OldObject",
        description="Old Object",
        default=False
    )
    applink_export: BoolProperty(
        name="FirstTime",
        description="Object is from 3d-ocat",
        default=False
    )
    objecttime: StringProperty(
        name="ObjectTime",
        subtype="FILE_PATH"
    )
    path3b: StringProperty(
        name="3B Path",
        subtype="FILE_PATH"
    )
    dime: FloatVectorProperty(
        name="dime",
        description="Dimension"
    )
    applink_scale: FloatVectorProperty(
        name="Scale",
        description="Scale"
    )
class MaterialCoat3D(PropertyGroup):
    Nodegroup: StringProperty(
        name="NodeGroup",
    )

class SceneCoat3D(PropertyGroup):
    defaultfolder: StringProperty(
        name="FilePath",
        subtype="DIR_PATH",
    )
    coat3D_exe: StringProperty(
        name="FilePath",
        subtype="FILE_PATH",
    )
    exchangedir: StringProperty(
        name="FilePath",
        subtype="DIR_PATH"
    )
    exchangefolder: StringProperty(
        name="FilePath",
        subtype="DIR_PATH"
    )
    bring_retopo: BoolProperty(
        name="Import window",
        description="Allows to skip import dialog",
        default=False
    )
    bring_retopo_path: StringProperty(
        name="FilePath",
        subtype="DIR_PATH",
    )
    remove_path: BoolProperty(
        name="Import window",
        description="Allows to skip import dialog",
        default=False
    )
    exchange_found: BoolProperty(
        name="Exchange Found",
        description="Alert if Exchange folder is not found",
        default=True
    )
    exportfile: BoolProperty(
        name="No Import File",
        description="Add Modifiers and export",
        default=False
    )
    importmod: BoolProperty(
        name="Remove Modifiers",
        description="Import and add modifiers",
        default=False
    )
    exportmod: BoolProperty(
        name="Modifiers",
        description="Export modifiers",
        default=False
    )
    importtextures: BoolProperty(
        name="Bring Textures",
        description="Import Textures",
        default=True
    )
    createnodes: BoolProperty(
        name="Bring Textures",
        description="Import Textures",
        default=True
    )
    importlevel: BoolProperty(
        name="Multires. Level",
        description="Bring Specific Multires Level",
        default=False
    )
    importmesh: BoolProperty(
        name="Mesh",
        description="Import Mesh",
        default=False
    )

    # copy location

    loca: FloatVectorProperty(
        name="location",
        description="Location",
        subtype="XYZ",
        default=(0.0, 0.0, 0.0)
    )
    rota: FloatVectorProperty(
        name="location",
        description="Location",
        subtype="EULER",
        default=(0.0, 0.0, 0.0)
    )
    scal: FloatVectorProperty(
        name="location",
        description="Location",
        subtype="XYZ",
        default=(0.0, 0.0, 0.0)
    )
    dime: FloatVectorProperty(
        name="dimension",
        description="Dimension",
        subtype="XYZ",
        default=(0.0, 0.0, 0.0)
    )
    type: EnumProperty(
        name="Export Type",
        description="Different Export Types",
        items=(("ppp", "Per-Pixel Painting", ""),
               ("mv", "Microvertex Painting", ""),
               ("ptex", "Ptex Painting", ""),
               ("uv", "UV-Mapping", ""),
               ("ref", "Reference Mesh", ""),
               ("retopo", "Retopo mesh as new layer", ""),
               ("vox", "Mesh As Voxel Object", ""),
               ("alpha", "Mesh As New Pen Alpha", ""),
               ("prim", "Mesh As Voxel Primitive", ""),
               ("curv", "Mesh As a Curve Profile", ""),
               ("autopo", "Mesh For Auto-retopology", ""),
               ),
        default="ppp"
    )
class MeshCoat3D(PropertyGroup):
    applink_address: StringProperty(
        name="ApplinkAddress",
        subtype="APPLINK_ADDRESS",
    )
class MaterialCoat3D(PropertyGroup):
    name: StringProperty(
        name="ApplinkAddress",
        subtype="APPLINK_ADDRESS",
    )

classes = (
    #ObjectButtonsPanel,
    SCENE_PT_Main,
    SCENE_PT_Settings,
    SCENE_PT_Settings_Update,
    SCENE_PT_Settings_Folders,
    SCENE_OT_folder,
    SCENE_OT_opencoat,
    SCENE_OT_export,
    SCENE_OT_import,
    VIEW3D_MT_Coat_Dynamic_Menu,
    ObjectCoat3D,
    SceneCoat3D,
    MeshCoat3D,
    MaterialCoat3D,
    )

def register():
    bpy.coat3D = dict()
    bpy.coat3D['active_coat'] = ''
    bpy.coat3D['status'] = 1
    bpy.coat3D['kuva'] = 1

    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Object.coat3D = PointerProperty(type=ObjectCoat3D)
    bpy.types.Scene.coat3D = PointerProperty(type=SceneCoat3D)
    bpy.types.Mesh.coat3D = PointerProperty(type=MeshCoat3D)
    bpy.types.Material.coat3D = PointerProperty(type=MaterialCoat3D)

    kc = bpy.context.window_manager.keyconfigs.addon

    if kc:
        km = kc.keymaps.new(name="Object Mode")
        kmi = km.keymap_items.new('wm.call_menu', 'Q', 'PRESS', shift=True)
        kmi.properties.name = "VIEW3D_MT_Coat_Dynamic_Menu"

def unregister():

    import bpy
    from bpy.utils import unregister_class

    del bpy.types.Object.coat3D
    del bpy.types.Scene.coat3D
    del bpy.types.Mesh.coat3D
    del bpy.coat3D

    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        km = kc.keymaps.get('Object Mode')
        for kmi in km.keymap_items:
            if kmi.idname == 'wm.call_menu':
                if kmi.properties.name == "VIEW3D_MT_Coat_Dynamic_Menu":
                    km.keymap_items.remove(kmi)

    for cls in reversed(classes):
        unregister_class(cls)
