# SPDX-FileCopyrightText: 2010-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "3D-Coat Applink",
    "author": "Kalle-Samuli Riihikoski (haikalle)",
    "version": (4, 9, 34),
    "blender": (2, 80, 0),
    "location": "Scene > 3D-Coat Applink",
    "description": "Transfer data between 3D-Coat/Blender",
    "warning": "",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/import_export/coat3D.html",
    "category": "Import-Export",
}

if "bpy" in locals():
    import importlib
    importlib.reload(tex)
else:
    from . import tex
from bpy.app.handlers import persistent

from io_coat3D import tex
from io_coat3D import texVR
from io_coat3D import folders

import os
import platform
import ntpath
import re
import shutil
import pathlib
import stat


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
only_one_time = True
global_exchange_folder = ''
foundExchangeFolder = True
saved_exchange_folder = ''
liveUpdate = True
mTime = 0

@persistent
def every_3_seconds():

    global global_exchange_folder
    global liveUpdate
    global mTime
    global only_one_time

    if(only_one_time):
        only_one_time = False
        folders.loadExchangeFolder()


    try:
        coat3D = bpy.context.scene.coat3D

        Export_folder  = coat3D.exchangeFolder
        Export_folder += ('%sexport.txt' % (os.sep))

        if (os.path.isfile(Export_folder) and mTime != os.path.getmtime(Export_folder)):

            for objekti in bpy.data.objects:
                if(objekti.coat3D.applink_mesh):
                    tex.updatetextures(objekti)

            mTime = os.path.getmtime(Export_folder)

    except:
        pass

    return 3.0

@persistent
def load_handler(dummy):
    bpy.app.timers.register(every_3_seconds)

def removeFile(exportfile):
    if (os.path.isfile(exportfile)):
        os.remove(exportfile)


def folder_size(path):

    folder_size_max = int(bpy.context.scene.coat3D.folder_size)

    if(bpy.context.scene.coat3D.defaultfolder == ''):
        tosi = True
        while tosi:
            list_of_files = []
            for file in os.listdir(path):
                list_of_files.append(path + os.sep + file)

            if len(list_of_files) >= folder_size_max:
                oldest_file = min(list_of_files, key=os.path.getctime)
                os.remove(os.path.abspath(oldest_file))
            else:
                tosi = False

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

def updatemesh(objekti, proxy, texturelist):
    # Vertex colors
    if(len(proxy.data.vertex_colors) > 0):
        bring_vertex_map = True
    else:
        bring_vertex_map = False

    if(bring_vertex_map):
        if(len(objekti.data.vertex_colors) > 0):
            for vertex_map in objekti.data.vertex_colors:
                if vertex_map.name == 'Col':
                    copy_data = True
                    vertex_map_copy = vertex_map
                    break
                else:
                    copy_data = False
        else:
            copy_data = False

        if(copy_data):
            for poly in objekti.data.polygons:
                for loop_index in poly.loop_indices:
                    vertex_map_copy.data[loop_index].color = proxy.data.vertex_colors[0].data[loop_index].color
        else:
            objekti.data.vertex_colors.new()
            vertex_map_copy = objekti.data.vertex_colors[-1]
            for poly in objekti.data.polygons:
                for loop_index in poly.loop_indices:
                    vertex_map_copy.data[loop_index].color = proxy.data.vertex_colors[0].data[loop_index].color

    # UV -Sets
    udim_textures = False
    if(texturelist != []):
        if(texturelist[0][0].startswith('100')):
            udim_textures =True

    proxy.select_set(True)
    objekti.select_set(True)

    uv_count = len(proxy.data.uv_layers)
    index = 0
    while(index < uv_count and len(proxy.data.polygons) == len(objekti.data.polygons)):
        for poly in proxy.data.polygons:
            for indi in poly.loop_indices:
                if(proxy.data.uv_layers[index].data[indi].uv[0] != 0 and proxy.data.uv_layers[index].data[indi].uv[1] != 0):

                    if(udim_textures):
                        udim = proxy.data.uv_layers[index].name
                        udim_index = int(udim[2:]) - 1

                    objekti.data.uv_layers[0].data[indi].uv[0] = proxy.data.uv_layers[index].data[indi].uv[0]
                    objekti.data.uv_layers[0].data[indi].uv[1] = proxy.data.uv_layers[index].data[indi].uv[1]

        index = index + 1

    # Mesh Copy
    if(proxy.name.startswith('RetopoGroup')):
        objekti.data = proxy.data
    else:
        for ind, v in enumerate(objekti.data.vertices):
            v.co = proxy.data.vertices[ind].co

class SCENE_OT_getback(bpy.types.Operator):
    bl_idname = "getback.pilgway_3d_coat"
    bl_label = "Export your custom property"
    bl_description = "Export your custom property"
    bl_options = {'UNDO'}

    def invoke(self, context, event):

        global global_exchange_folder
        path_ex = ''

        Export_folder  = global_exchange_folder
        Blender_folder = os.path.join(Export_folder, 'Blender')

        BlenderFolder = Blender_folder
        ExportFolder = Export_folder

        Blender_folder += ('%sexport.txt' % (os.sep))
        Export_folder += ('%sexport.txt' % (os.sep))

        if (bpy.app.background == False):
            if os.path.isfile(Export_folder):

                print('BLENDER -> 3DC -> BLENDER WORKFLLOW')
                DeleteExtra3DC()
                workflow1(ExportFolder)
                removeFile(Export_folder)
                removeFile(Blender_folder)

            elif os.path.isfile(Blender_folder):

                print('3DC -> BLENDER WORKFLLOW')
                DeleteExtra3DC()
                workflow2(BlenderFolder)
                removeFile(Blender_folder)

        return {'FINISHED'}

class SCENE_OT_savenew(bpy.types.Operator):
    bl_idname = "save_new_export.pilgway_3d_coat"
    bl_label = "Export your custom property"
    bl_description = "Export your custom property"
    bl_options = {'UNDO'}

    def invoke(self, context, event):

        coat3D = bpy.context.scene.coat3D
        platform = os.sys.platform

        if(platform == 'win32' or platform == 'darwin'):
            exchangeFile = os.path.expanduser("~") + os.sep + 'Documents' + os.sep + '3DC2Blender' + os.sep + 'Exchange_folder.txt'
        else:
            exchangeFile = os.path.expanduser("~") + os.sep + '3DC2Blender' + os.sep + 'Exchange_folder.txt'
        if(os.path.isfile(exchangeFile)):
            folderPath = ''

        if(os.path.isfile(exchangeFile)):
            file = open(exchangeFile, "w")
            file.write("%s"%(coat3D.exchangeFolder))
            file.close()

        return {'FINISHED'}


class SCENE_OT_folder(bpy.types.Operator):
    bl_idname = "update_exchange_folder.pilgway_3d_coat"
    bl_label = "Export your custom property"
    bl_description = "Export your custom property"
    bl_options = {'UNDO'}

    def invoke(self, context, event):
        global foundExchangeFolder
        coat3D = bpy.context.scene.coat3D
        if(os.path.isdir(coat3D.exchangeFolder)):
            foundExchangeFolder= True
            folders.updateExchangeFile(coat3D.exchangeFolder)

        return {'FINISHED'}

class SCENE_OT_opencoat(bpy.types.Operator):
    bl_idname = "open_3dcoat.pilgway_3d_coat"
    bl_label = "Export your custom property"
    bl_description = "Export your custom property"
    bl_options = {'UNDO'}

    def invoke(self, context, event):

        coat3D = bpy.context.selected_objects[0].coat3D.applink_3b_path
        platform = os.sys.platform
        if (platform == 'win32' or platform == 'darwin'):
            importfile = bpy.context.scene.coat3D.exchangeFolder
            importfile += ('%simport.txt' % (os.sep))
            file = open(importfile, "w")
            file.write("%s" % (coat3D))
            file.write("\n%s" % (coat3D))
            file.write("\n[3B]")
            file.close()
        else:
            importfile = bpy.context.scene.coat3D.exchangeFolder
            importfile += ('%simport.txt' % (os.sep))
            file = open(importfile, "w")
            file.write("%s" % (coat3D))
            file.write("\n%s" % (coat3D))
            file.write("\n[3B]")
            file.close()

        return {'FINISHED'}

def scaleParents():
    save = []
    names =[]

    for objekti in bpy.context.selected_objects:
        temp = objekti
        while (temp.parent is not None and temp.parent.name not in names):
            save.append([temp.parent,(temp.parent.scale[0],temp.parent.scale[1],temp.parent.scale[2])])
            names.append(temp.parent)
            temp = temp.parent

    for name in names:
        name.scale = (1,1,1)

    return save

def scaleBackParents(save):

    for data in save:
        data[0].scale = data[1]

def deleteNodes(type):

    deletelist = []
    deleteimages = []
    deletegroup =[]
    delete_images = bpy.context.scene.coat3D.delete_images

    if type == 'Material':
        if(len(bpy.context.selected_objects) == 1):
            material = bpy.context.selected_objects[0].active_material
            if(material.use_nodes):
                for node in material.node_tree.nodes:
                    if(node.name.startswith('3DC')):
                        if (node.type == 'GROUP'):
                            deletegroup.append(node.node_tree.name)
                        deletelist.append(node.name)
                        if node.type == 'TEX_IMAGE' and delete_images == True:
                            deleteimages.append(node.image.name)
                if deletelist:
                    for node in deletelist:
                        material.node_tree.nodes.remove(material.node_tree.nodes[node])
                if deleteimages:
                    for image in deleteimages:
                        bpy.data.images.remove(bpy.data.images[image])

    elif type == 'Object':
        if (len(bpy.context.selected_objects) > 0):
            for objekti in bpy.context.selected_objects:
                for material in objekti.material_slots:
                    if (material.material.use_nodes):
                        for node in material.material.node_tree.nodes:
                            if (node.name.startswith('3DC')):
                                if(node.type == 'GROUP'):
                                    deletegroup.append(node.node_tree.name)
                                deletelist.append(node.name)
                                if node.type == 'TEX_IMAGE' and delete_images == True:
                                    deleteimages.append(node.image.name)
                    if deletelist:
                        for node in deletelist:
                            material.material.node_tree.nodes.remove(material.material.node_tree.nodes[node])
                            deletelist = []

                    if deleteimages:
                        for image in deleteimages:
                            bpy.data.images.remove(bpy.data.images[image])
                            deleteimages = []

    elif type == 'Collection':
        for collection_object in bpy.context.view_layer.active_layer_collection.collection.all_objects:
            if(collection_object.type == 'MESH'):
                for material in collection_object.material_slots:
                    if (material.material.use_nodes):
                        for node in material.material.node_tree.nodes:
                            if (node.name.startswith('3DC')):
                                if (node.type == 'GROUP'):
                                    deletegroup.append(node.node_tree.name)
                                deletelist.append(node.name)
                                if node.type == 'TEX_IMAGE' and delete_images == True:
                                    deleteimages.append(node.image.name)

                    if deletelist:
                        for node in deletelist:
                            material.material.node_tree.nodes.remove(material.material.node_tree.nodes[node])
                            deletelist = []

                    if deleteimages:
                        for image in deleteimages:
                            bpy.data.images.remove(bpy.data.images[image])
                            deleteimages = []

    elif type == 'Scene':
        for collection in bpy.data.collections:
            for collection_object in collection.all_objects:
                if (collection_object.type == 'MESH'):
                    for material in collection_object.material_slots:
                        if (material.material.use_nodes):
                            for node in material.material.node_tree.nodes:
                                if (node.name.startswith('3DC')):
                                    if (node.type == 'GROUP'):
                                        deletegroup.append(node.node_tree.name)

                                    deletelist.append(node.name)
                                    if node.type == 'TEX_IMAGE' and delete_images == True:
                                        deleteimages.append(node.image.name)
                        if deletelist:
                            for node in deletelist:
                                material.material.node_tree.nodes.remove(material.material.node_tree.nodes[node])
                                deletelist = []

                        if deleteimages:
                            for image in deleteimages:
                                bpy.data.images.remove(bpy.data.images[image])
                                deleteimages = []

        if(deletelist):
            for node in deletelist:
                bpy.data.node_groups.remove(bpy.data.node_groups[node])

        for image in bpy.data.images:
            if (image.name.startswith('3DC') and image.name[6] == '_'):
                deleteimages.append(image.name)


    if(deletegroup):
        for node in deletegroup:
            bpy.data.node_groups.remove(bpy.data.node_groups[node])

    if deleteimages:
        for image in deleteimages:
            bpy.data.images.remove(bpy.data.images[image])


def delete_materials_from_end(keep_materials_count, objekti):
    #bpy.context.object.active_material_index = 0
    index_t = 0
    while (index_t < keep_materials_count):
        temp_len = len(objekti.material_slots)-1
        bpy.context.object.active_material_index = temp_len
        bpy.ops.object.material_slot_remove()
        index_t +=1

''' DELETE NODES BUTTONS'''

class SCENE_OT_delete_material_nodes(bpy.types.Operator):
    bl_idname = "delete_material_nodes.pilgway_3d_coat"
    bl_label = "Delete material nodes"
    bl_description = "Delete material nodes"
    bl_options = {'UNDO'}

    def invoke(self, context, event):
        type = bpy.context.scene.coat3D.deleteMode = 'Material'
        deleteNodes(type)
        return {'FINISHED'}

class SCENE_OT_delete_object_nodes(bpy.types.Operator):
    bl_idname = "delete_object_nodes.pilgway_3d_coat"
    bl_label = "Delete material nodes"
    bl_description = "Delete material nodes"
    bl_options = {'UNDO'}

    def invoke(self, context, event):
        type = bpy.context.scene.coat3D.deleteMode = 'Object'
        deleteNodes(type)
        return {'FINISHED'}

class SCENE_OT_delete_collection_nodes(bpy.types.Operator):
    bl_idname = "delete_collection_nodes.pilgway_3d_coat"
    bl_label = "Delete material nodes"
    bl_description = "Delete material nodes"
    bl_options = {'UNDO'}

    def invoke(self, context, event):
        type = bpy.context.scene.coat3D.deleteMode = 'Collection'
        deleteNodes(type)
        return {'FINISHED'}

class SCENE_OT_delete_scene_nodes(bpy.types.Operator):
    bl_idname = "delete_scene_nodes.pilgway_3d_coat"
    bl_label = "Delete material nodes"
    bl_description = "Delete material nodes"
    bl_options = {'UNDO'}

    def invoke(self, context, event):
        type = bpy.context.scene.coat3D.deleteMode = 'Scene'
        deleteNodes(type)
        return {'FINISHED'}


''' TRANSFER AND UPDATE BUTTONS'''

class SCENE_OT_export(bpy.types.Operator):
    bl_idname = "export_applink.pilgway_3d_coat"
    bl_label = "Export your custom property"
    bl_description = "Export your custom property"
    bl_options = {'UNDO'}

    def invoke(self, context, event):
        bpy.ops.export_applink.pilgway_3d_coat()

        return {'FINISHED'}

    def execute(self, context):
        global foundExchangeFolder
        global global_exchange_folder
        global run_background_update
        run_background_update = False

        foundExchangeFolder, global_exchange_folder = folders.InitFolders()

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
                    if(len(objec.data.uv_layers) == 0):
                        objec.data.uv_layers.new(name='UVMap', do_init = False)

                    export_ok = True
            if (export_ok == False):
                return {'FINISHED'}

        scaled_objects = scaleParents()

        activeobj = bpy.context.active_object.name
        checkname = ''
        coa = bpy.context.active_object.coat3D

        p = pathlib.Path(coat3D.exchangeFolder)
        kokeilu = coat3D.exchangeFolder[:-9]
        Blender_folder2 = ("%s%sExchange" % (kokeilu, os.sep))
        Blender_folder2 += ('%sexport.txt' % (os.sep))

        if (os.path.isfile(Blender_folder2)):
            os.remove(Blender_folder2)

        if (not os.path.isdir(coat3D.exchangeFolder)):
            coat3D.exchange_found = False
            return {'FINISHED'}

        folder_objects = folders.set_working_folders()
        folder_size(folder_objects)

        importfile = coat3D.exchangeFolder
        texturefile = coat3D.exchangeFolder
        importfile += ('%simport.txt'%(os.sep))
        texturefile += ('%stextures.txt'%(os.sep))

        looking = True
        object_index = 0
        active_render =  bpy.context.scene.render.engine

        if(coat3D.type == 'autopo'):
            checkname = folder_objects + os.sep
            checkname = ("%sretopo.fbx" % (checkname))

        elif(coat3D.type == 'update'):
            checkname = bpy.context.selected_objects[0].coat3D.applink_address

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
            if objekti.type == 'MESH':
                objekti.name = '__' + objekti.name
                if(objekti.material_slots.keys() == []):
                    newmat = bpy.data.materials.new('Material')
                    newmat.use_nodes = True
                    objekti.data.materials.append(newmat)
                    matindex += 1
                objekti.coat3D.applink_name = objekti.name
        mod_mat_list = {}


        bake_location = folder_objects + os.sep + 'Bake'
        if (os.path.isdir(bake_location)):
            shutil.rmtree(bake_location)
            os.makedirs(bake_location)
        else:
            os.makedirs(bake_location)

        # BAKING #

        temp_string = ''
        for objekti in bpy.context.selected_objects:
            if objekti.type == 'MESH':
                mod_mat_list[objekti.name] = []
                objekti.coat3D.applink_scale = objekti.scale
                objekti.coat3D.retopo = False

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

                    bake_list = []
                    if(coat3D.bake_diffuse):
                        bake_list.append(['DIFFUSE', '$LOADTEX'])
                    if (coat3D.bake_ao):
                        bake_list.append(['AO', '$ExternalAO'])
                    if (coat3D.bake_normal):
                        bake_list.append(['NORMAL', '$LOADLOPOLYTANG'])
                    if (coat3D.bake_roughness):
                        bake_list.append(['ROUGHNESS', '$LOADROUGHNESS'])

                    if(coat3D.bake_resolution == 'res_64'):
                        res_size = 64
                    elif (coat3D.bake_resolution == 'res_128'):
                        res_size = 128
                    elif (coat3D.bake_resolution == 'res_256'):
                        res_size = 256
                    elif (coat3D.bake_resolution == 'res_512'):
                        res_size = 512
                    elif (coat3D.bake_resolution == 'res_1024'):
                        res_size = 1024
                    elif (coat3D.bake_resolution == 'res_2048'):
                        res_size = 2048
                    elif (coat3D.bake_resolution == 'res_4096'):
                        res_size = 4096
                    elif (coat3D.bake_resolution == 'res_8192'):
                        res_size = 8192

                    if(len(bake_list) > 0):
                        index_bake_tex = 0
                        while(index_bake_tex < len(bake_list)):
                            bake_index = 0
                            for bake_mat_index in final_material_indexs:
                                bake_node = objekti.material_slots[bake_mat_index].material.node_tree.nodes.new('ShaderNodeTexImage')
                                bake_node.name = 'ApplinkBake' + str(bake_index)
                                bpy.ops.image.new(name=bake_node.name, width=res_size, height=res_size)
                                bake_node.image = bpy.data.images[bake_node.name]
                                objekti.material_slots[bake_mat_index].material.node_tree.nodes.active = bake_node

                                bake_index += 1
                            if(bpy.context.scene.render.engine != 'CYCLES'):
                                bpy.context.scene.render.engine = 'CYCLES'
                            bpy.context.scene.render.bake.use_pass_direct = False
                            bpy.context.scene.render.bake.use_pass_indirect = False
                            bpy.context.scene.render.bake.use_pass_color = True

                            bpy.ops.object.bake(type=bake_list[index_bake_tex][0], margin=1, width=res_size, height=res_size)

                            bake_index = 0
                            for bake_mat_index in final_material_indexs:
                                bake_image = 'ApplinkBake' + str(bake_index)
                                bpy.data.images[bake_image].filepath_raw = bake_location + os.sep + objekti.name + '_' + bake_image + '_' + bake_list[index_bake_tex][0] + ".png"
                                image_bake_name =  bpy.data.images[bake_image].filepath_raw
                                tie = image_bake_name.split(os.sep)
                                toi = ''
                                for sana in tie:
                                    toi += sana
                                    toi += "/"
                                final_bake_name = toi[:-1]
                                bpy.data.images[bake_image].save()
                                temp_string += '''\n[script ImportTexture("''' + bake_list[index_bake_tex][1] + '''","''' + objekti.material_slots[bake_mat_index].material.name + '''","''' +  final_bake_name + '''");]'''

                                bake_index += 1

                            for material in objekti.material_slots:
                                if material.material.use_nodes == True:
                                    for node in material.material.node_tree.nodes:
                                        if (node.name.startswith('ApplinkBake') == True):
                                            material.material.node_tree.nodes.remove(node)

                            for image in bpy.data.images:
                                if (image.name.startswith('ApplinkBake') == True):
                                    bpy.data.images.remove(image)

                            index_bake_tex += 1

        #BAKING ENDS

        #bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
        if(len(bpy.context.selected_objects) > 1 and coat3D.type != 'vox'):
            bpy.ops.object.transforms_to_deltas(mode='ROT')

        if(coat3D.type == 'autopo'):
            coat3D.bring_retopo = True
            coat3D.bring_retopo_path = checkname
            bpy.ops.export_scene.fbx(filepath=checkname, global_scale = 1, use_selection=True, use_mesh_modifiers=coat3D.exportmod, axis_forward='-Z', axis_up='Y')

        elif (coat3D.type == 'vox'):
            coat3D.bring_retopo = False
            bpy.ops.export_scene.fbx(filepath=coa.applink_address, global_scale = 0.01, use_selection=True,
                                     use_mesh_modifiers=coat3D.exportmod, axis_forward='-Z', axis_up='Y')

        else:
            coat3D.bring_retopo = False
            bpy.ops.export_scene.fbx(filepath=coa.applink_address,global_scale = 0.01, use_selection=True, use_mesh_modifiers=coat3D.exportmod, axis_forward='-Z', axis_up='Y')

        file = open(importfile, "w")
        file.write("%s"%(checkname))
        file.write("\n%s"%(checkname))
        file.write("\n[%s]"%(coat3D.type))
        if(coat3D.type == 'ppp' or coat3D.type == 'mv' or coat3D.type == 'ptex'):
            file.write("\n[export_preset Blender Cycles]")
            file.write(temp_string)

        file.close()
        for idx, objekti in enumerate(bpy.context.selected_objects):
            if objekti.type == 'MESH':
                objekti.name = objekti.name[2:]
                if(len(bpy.context.selected_objects) == 1):
                    objekti.coat3D.applink_onlyone = True
                objekti.coat3D.type = coat3D.type
                objekti.coat3D.applink_mesh = True
                objekti.coat3D.obj_mat = ''
                objekti.coat3D.applink_index = ("3DC%.3d" % (object_index))

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
                    if(mat_list == '__' + objekti.name):
                        for ind, mat in enumerate(mod_mat_list[mat_list]):
                            objekti.material_slots[mod_mat_list[mat_list][ind][0]].material = mod_mat_list[mat_list][ind][1]

        scaleBackParents(scaled_objects)
        bpy.context.scene.render.engine = active_render
        return {'FINISHED'}


def DeleteExtra3DC():

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

    image_del_list = []
    for image in bpy.data.images:
        if (image.name.startswith('3DC')):
            if image.users == 0:
                image_del_list.append(image.name)

    if (image_del_list != []):
        for image in image_del_list:
            bpy.data.images.remove(bpy.data.images[image])

def new_ref_function(new_applink_address, nimi):

    create_collection = True
    for collection in bpy.data.collections:
        if collection.name == 'Applink_Objects':
            create_collection = False

    if create_collection:
        bpy.data.collections.new('Applink_Objects')

    coll_items = bpy.context.scene.collection.children.items()

    add_applink_collection = True
    for coll in coll_items:
        if coll[0] == 'Applink_Objects':
            add_applink_collection = False

    if add_applink_collection:
        bpy.context.scene.collection.children.link(bpy.data.collections['Applink_Objects'])

    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Applink_Objects']

    old_objects = bpy.data.objects.keys()
    object_list = []


    bpy.ops.import_scene.fbx(filepath=new_applink_address, global_scale = 0.01,axis_forward='X', axis_up='Y',use_custom_normals=False)
    new_objects = bpy.data.objects.keys()
    diff_objects = [i for i in new_objects if i not in old_objects]
    texturelist = []

    for diff_object in diff_objects:

        refmesh = bpy.data.objects[nimi]
        copymesh = bpy.data.objects[nimi].copy()

        copymesh.data = bpy.data.objects[diff_object].data
        copymesh.coat3D.applink_name = bpy.data.objects[diff_object].data.name
        copymesh.coat3D.applink_address = refmesh.coat3D.applink_address
        ne_name = bpy.data.objects[diff_object].data.name

        copymesh.coat3D.type = 'ppp'
        copymesh.coat3D.retopo = True

        bpy.data.collections['Applink_Objects'].objects.link(copymesh)

        bpy.data.objects.remove(bpy.data.objects[diff_object])
        bpy.ops.object.select_all(action='DESELECT')
        copymesh.select_set(True)
        copymesh.delta_rotation_euler[0] = 1.5708
        copymesh.name = ne_name

        normal_node = copymesh.material_slots[0].material.node_tree.nodes['Normal Map']
        copymesh.material_slots[0].material.node_tree.nodes.remove(normal_node)
        copymesh.material_slots[0].material.node_tree.nodes['Principled BSDF'].inputs['Metallic'].default_value = 0
        copymesh.material_slots[0].material.node_tree.nodes['Principled BSDF'].inputs['Specular'].default_value = 0.5


    refmesh.coat3D.applink_name = ''
    refmesh.coat3D.applink_address = ''
    refmesh.coat3D.type = ''
    copymesh.scale = (1,1,1)
    copymesh.coat3D.applink_scale = (1,1,1)
    copymesh.location = (0,0,0)
    copymesh.rotation_euler = (0,0,0)


def blender_3DC_blender(texturelist, file_applink_address):

    coat3D = bpy.context.scene.coat3D

    old_materials = bpy.data.materials.keys()
    old_objects = bpy.data.objects.keys()
    cache_base = bpy.data.objects.keys()

    object_list = []
    import_list = []
    import_type = []

    for objekti in bpy.data.objects:
        if objekti.type == 'MESH' and objekti.coat3D.applink_address == file_applink_address:
            obj_coat = objekti.coat3D

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
        for idx, list in enumerate(import_list):

            bpy.ops.import_scene.fbx(filepath=list, global_scale = 0.01,axis_forward='X',use_custom_normals=False)
            cache_objects = bpy.data.objects.keys()
            cache_objects = [i for i in cache_objects if i not in cache_base]
            for cache_object in cache_objects:

                bpy.data.objects[cache_object].coat3D.type = import_type[idx]
                bpy.data.objects[cache_object].coat3D.applink_address = list
                cache_base.append(cache_object)

        bpy.ops.object.select_all(action='DESELECT')
        new_materials = bpy.data.materials.keys()
        new_objects = bpy.data.objects.keys()


        diff_mat = [i for i in new_materials if i not in old_materials]
        diff_objects = [i for i in new_objects if i not in old_objects]

        for mark_mesh in diff_objects:
            bpy.data.objects[mark_mesh].data.coat3D.name = '3DC'

        for c_index in diff_mat:
            bpy.data.materials.remove(bpy.data.materials[c_index])

    '''The main Applink Object Loop'''

    for oname in object_list:

        objekti = bpy.data.objects[oname]
        if(objekti.coat3D.applink_mesh == True):

            path3b_n = coat3D.exchangeFolder
            path3b_n += ('%slast_saved_3b_file.txt' % (os.sep))

            if(objekti.coat3D.import_mesh and coat3D.importmesh == True):

                objekti.coat3D.import_mesh = False
                objekti.select_set(True)

                use_smooth = objekti.data.polygons[0].use_smooth
                found_obj = False

                '''Changes objects mesh into proxy mesh'''
                if(objekti.coat3D.type != 'ref'):

                    for proxy_objects in diff_objects:
                        if(objekti.coat3D.retopo == False):
                            if (proxy_objects == objekti.coat3D.applink_name):
                                obj_proxy = bpy.data.objects[proxy_objects]
                                obj_proxy.coat3D.delete_proxy_mesh = True
                                found_obj = True
                        else:
                            if (proxy_objects == objekti.coat3D.applink_name + '.001'):
                                obj_proxy = bpy.data.objects[proxy_objects]
                                obj_proxy.coat3D.delete_proxy_mesh = True
                                found_obj = True


                mat_list = []
                if (objekti.material_slots):
                    for obj_mat in objekti.material_slots:
                        mat_list.append(obj_mat.material)

                if(found_obj == True):
                    exportfile = coat3D.exchangeFolder
                    path3b_n = coat3D.exchangeFolder
                    path3b_n += ('%slast_saved_3b_file.txt' % (os.sep))
                    exportfile += ('%sBlender' % (os.sep))
                    exportfile += ('%sexport.txt'%(os.sep))
                    if(os.path.isfile(exportfile)):
                        export_file = open(exportfile)
                        export_file.close()
                        os.remove(exportfile)
                    if(os.path.isfile(path3b_n)):

                        mesh_time = os.path.getmtime(objekti.coat3D.applink_address)
                        b_time = os.path.getmtime(path3b_n)
                        if (abs(mesh_time - b_time) < 240):
                            export_file = open(path3b_n)
                            for line in export_file:
                                objekti.coat3D.applink_3b_path = line
                                head, tail = os.path.split(line)
                                just_3b_name = tail
                                objekti.coat3D.applink_3b_just_name = just_3b_name
                            export_file.close()
                            coat3D.remove_path = True

                    bpy.ops.object.select_all(action='DESELECT')
                    obj_proxy.select_set(True)

                    bpy.ops.object.select_all(action='TOGGLE')

                    if objekti.coat3D.applink_firsttime == True and objekti.coat3D.type == 'vox':
                        objekti.select_set(True)
                        objekti.scale = (0.01, 0.01, 0.01)
                        objekti.rotation_euler[0] = 1.5708
                        objekti.rotation_euler[2] = 1.5708
                        bpy.ops.object.transforms_to_deltas(mode='ROT')
                        bpy.ops.object.transforms_to_deltas(mode='SCALE')
                        objekti.coat3D.applink_firsttime = False
                        objekti.select_set(False)

                    elif objekti.coat3D.applink_firsttime == True:
                        objekti.scale = (objekti.scale[0]/objekti.coat3D.applink_scale[0],objekti.scale[1]/objekti.coat3D.applink_scale[1],objekti.scale[2]/objekti.coat3D.applink_scale[2])
                        #bpy.ops.object.transforms_to_deltas(mode='SCALE')
                        if(objekti.coat3D.applink_onlyone == False):
                            objekti.rotation_euler = (0,0,0)
                        objekti.coat3D.applink_firsttime = False

                    if(coat3D.importlevel):
                        obj_proxy.select = True
                        obj_proxy.modifiers.new(name='temp',type='MULTIRES')
                        objekti.select = True
                        bpy.ops.object.multires_reshape(modifier=multires_name)
                        bpy.ops.object.select_all(action='TOGGLE')
                    else:

                        bpy.context.view_layer.objects.active = obj_proxy
                        keep_materials_count = len(obj_proxy.material_slots) - len(objekti.material_slots)

                        #delete_materials_from_end(keep_materials_count, obj_proxy)


                        updatemesh(objekti,obj_proxy, texturelist)
                        bpy.context.view_layer.objects.active = objekti



                    #it is important to get the object translated correctly

                    objekti.select_set(True)

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
                    if(objekti.coat3D.retopo == False):
                        tex.matlab(objekti,mat_list,texturelist,is_new)
                objekti.select_set(False)
            else:
                mat_list = []
                if (objekti.material_slots):
                    for obj_mat in objekti.material_slots:
                        mat_list.append(obj_mat.material)

                if (coat3D.importtextures):
                    is_new = False
                    if(objekti.coat3D.retopo == False):
                        tex.matlab(objekti,mat_list,texturelist, is_new)
                objekti.select_set(False)

    if(coat3D.remove_path == True):
        if(os.path.isfile(path3b_n)):
            os.remove(path3b_n)
        coat3D.remove_path = False

    bpy.ops.object.select_all(action='DESELECT')
    if(import_list):

        for del_obj in diff_objects:

            if(bpy.context.collection.all_objects[del_obj].coat3D.type == 'vox' and bpy.context.collection.all_objects[del_obj].coat3D.delete_proxy_mesh == False):
                bpy.context.collection.all_objects[del_obj].select_set(True)
                objekti = bpy.context.collection.all_objects[del_obj]
                #bpy.ops.object.transforms_to_deltas(mode='ROT')
                objekti.scale = (1, 1, 1)
                bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')

                objekti.data.coat3D.name = '3DC'

                objekti.coat3D.objecttime = str(os.path.getmtime(objekti.coat3D.applink_address))
                objekti.coat3D.applink_name = objekti.name
                objekti.coat3D.applink_mesh = True
                objekti.coat3D.import_mesh = False

                #bpy.ops.object.transforms_to_deltas(mode='SCALE')
                objekti.coat3D.applink_firsttime = False
                bpy.context.collection.all_objects[del_obj].select_set(False)

            else:
                bpy.context.collection.all_objects[del_obj].select_set(True)
                bpy.data.objects.remove(bpy.data.objects[del_obj])

    if (coat3D.bring_retopo or coat3D.bring_retopo_path):
        if(os.path.isfile(coat3D.bring_retopo_path)):
            bpy.ops.import_scene.fbx(filepath=coat3D.bring_retopo_path, global_scale=1, axis_forward='X', use_custom_normals=False)
            os.remove(coat3D.bring_retopo_path)

    kokeilu = coat3D.exchangeFolder[:-9]
    Blender_folder2 = ("%s%sExchange" % (kokeilu, os.sep))
    Blender_folder2 += ('%sexport.txt' % (os.sep))
    if (os.path.isfile(Blender_folder2)):
        os.remove(Blender_folder2)

def blender_3DC(texturelist, new_applink_address):

    bpy.ops.object.select_all(action='DESELECT')
    for old_obj in bpy.context.collection.objects:
        old_obj.coat3D.applink_old = True

    coat3D = bpy.context.scene.coat3D
    Blender_folder = ("%s%sBlender"%(coat3D.exchangeFolder,os.sep))
    Blender_export = Blender_folder
    path3b_now = coat3D.exchangeFolder + os.sep
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

    create_collection = True
    for collection in bpy.data.collections:
        if collection.name == 'Applink_Objects':
            create_collection = False

    if create_collection:
        bpy.data.collections.new('Applink_Objects')

    coll_items = bpy.context.scene.collection.children.items()

    add_applink_collection = True
    for coll in coll_items:
        if coll[0] == 'Applink_Objects':
            add_applink_collection = False

    if add_applink_collection:
        bpy.context.scene.collection.children.link(bpy.data.collections['Applink_Objects'])

    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Applink_Objects']

    old_materials = bpy.data.materials.keys()
    old_objects = bpy.data.objects.keys()

    bpy.ops.import_scene.fbx(filepath=new_applink_address, global_scale = 1, axis_forward='-Z', axis_up='Y')

    new_materials = bpy.data.materials.keys()
    new_objects = bpy.data.objects.keys()

    diff_mat = [i for i in new_materials if i not in old_materials]
    diff_objects = [i for i in new_objects if i not in old_objects]


    for mark_mesh in diff_mat:
        bpy.data.materials[mark_mesh].coat3D.name = '3DC'
        bpy.data.materials[mark_mesh].use_fake_user = True
    laskuri = 0
    index = 0

    facture_object = False

    for c_index in diff_objects:
        bpy.data.objects[c_index].data.coat3D.name = '3DC'
        laskuri += 1
        if(laskuri == 2 and c_index == ('vt_' + diff_objects[0])):
            facture_object = True
            print('Facture object founded!!')

    #bpy.ops.object.transforms_to_deltas(mode='SCALE')
    bpy.ops.object.select_all(action='DESELECT')
    for new_obj in bpy.context.collection.objects:

        if(new_obj.coat3D.applink_old == False):
            new_obj.select_set(True)
            new_obj.coat3D.applink_firsttime = False
            new_obj.select_set(False)
            new_obj.coat3D.type = 'ppp'
            new_obj.coat3D.applink_address = new_applink_address
            new_obj.coat3D.applink_mesh = True
            new_obj.coat3D.objecttime = str(os.path.getmtime(new_obj.coat3D.applink_address))

            new_obj.coat3D.applink_name = new_obj.name
            index = index + 1

            bpy.context.view_layer.objects.active = new_obj

            new_obj.coat3D.applink_export = True

            if (os.path.isfile(osoite_3b)):
                mesh_time = os.path.getmtime(new_obj.coat3D.applink_address)
                b_time = os.path.getmtime(osoite_3b)
                if (abs(mesh_time-b_time) < 240):
                    new_obj.coat3D.applink_3b_path = osoite_3b
                    new_obj.coat3D.applink_3b_just_name = just_3b_name

            mat_list.append(new_obj.material_slots[0].material)
            is_new = True

            if(facture_object):
                texVR.matlab(new_obj, mat_list, texturelist, is_new)
                new_obj.scale = (0.01, 0.01, 0.01)
            else:
                tex.matlab(new_obj, mat_list, texturelist, is_new)

            mat_list.pop()

    for new_obj in bpy.context.collection.objects:
        if(new_obj.coat3D.applink_old == False):
            new_obj.coat3D.applink_old = True

    kokeilu = coat3D.exchangeFolder[:-10]
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


def workflow1(ExportFolder):

    coat3D = bpy.context.scene.coat3D

    texturelist = make_texture_list(ExportFolder)

    for texturepath in texturelist:
        for image in bpy.data.images:
            if(image.filepath == texturepath[3] and image.users == 0):
                bpy.data.images.remove(image)

    path3b_now = coat3D.exchangeFolder

    path3b_now += ('last_saved_3b_file.txt')
    new_applink_address = 'False'
    new_object = False
    new_ref_object = False

    exportfile3 = coat3D.exchangeFolder
    exportfile3 += ('%sexport.txt' % (os.sep))

    if(os.path.isfile(exportfile3)):

        obj_pathh = open(exportfile3)

        for line in obj_pathh:
            new_applink_address = line
            break
        obj_pathh.close()
        for scene_objects in bpy.context.collection.all_objects:
            if(scene_objects.type == 'MESH'):
                if(scene_objects.coat3D.applink_address == new_applink_address and scene_objects.coat3D.type == 'ref'):
                    scene_objects.coat3D.type == ''
                    new_ref_object = True
                    nimi = scene_objects.name




    exportfile = coat3D.exchangeFolder
    exportfile += ('%sBlender' % (os.sep))
    exportfile += ('%sexport.txt' % (os.sep))
    if (os.path.isfile(exportfile)):
        os.remove(exportfile)

    if(new_ref_object):

        new_ref_function(new_applink_address, nimi)

    else:
        blender_3DC_blender(texturelist, new_applink_address)

def workflow2(BlenderFolder):

    coat3D = bpy.context.scene.coat3D

    texturelist = make_texture_list(BlenderFolder)

    for texturepath in texturelist:
        for image in bpy.data.images:
            if(image.filepath == texturepath[3] and image.users == 0):
                bpy.data.images.remove(image)

    kokeilu = coat3D.exchangeFolder

    Blender_export = os.path.join(kokeilu, 'Blender')

    path3b_now = coat3D.exchangeFolder

    path3b_now += ('last_saved_3b_file.txt')
    Blender_export += ('%sexport.txt'%(os.sep))
    new_applink_address = 'False'
    new_object = False
    new_ref_object = False

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

    exportfile = coat3D.exchangeFolder
    exportfile += ('%sBlender' % (os.sep))
    exportfile += ('%sexport.txt' % (os.sep))
    if (os.path.isfile(exportfile)):
        os.remove(exportfile)

    if(new_ref_object):

        new_ref_function(new_applink_address, nimi)

    else:

        blender_3DC(texturelist, new_applink_address)

from bpy import *
from mathutils import Vector, Matrix

class SCENE_PT_Main(bpy.types.Panel):
    bl_label = "3D-Coat Applink"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = '3D-Coat'

    @classmethod
    def poll(cls, context):
        if bpy.context.mode == 'OBJECT':
            return True
        else:
            return False

    def draw(self, context):
        layout = self.layout
        coat3D = bpy.context.scene.coat3D
        global foundExchangeFolder

        if(foundExchangeFolder == False):
            row = layout.row()
            row.label(text="Applink didn't find your 3d-Coat/Exchange folder.")
            row = layout.row()
            row.label(text="Please select it before using Applink.")
            row = layout.row()
            row.prop(coat3D,"exchangeFolder",text="")
            row = layout.row()
            row.operator("update_exchange_folder.pilgway_3d_coat", text="Apply folder")

        else:
            #Here you add your GUI
            row = layout.row()
            row.prop(coat3D,"type",text = "")
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=False, even_rows=False, align=True)

            row = layout.row()

            row.operator("export_applink.pilgway_3d_coat", text="Send")
            row.operator("getback.pilgway_3d_coat", text="GetBack")


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

class MaterialButtonsPanel():
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"

class SCENE_PT_Material(MaterialButtonsPanel,bpy.types.Panel):
    bl_label = "3D-Coat Applink"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"

    def draw(self, context):
        pass

class SCENE_PT_Material_Import(MaterialButtonsPanel, bpy.types.Panel):
    bl_label = "Import Textures:"
    bl_parent_id = "SCENE_PT_Material"
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        coat3D = bpy.context.active_object.active_material

        layout.active = True

        flow = layout.grid_flow(row_major=True, columns=0, even_columns=False, even_rows=False, align=True)

        col = flow.column()
        col.prop(coat3D, "coat3D_diffuse", text="Diffuse")
        col.prop(coat3D, "coat3D_metalness", text="Metalness")
        col.prop(coat3D, "coat3D_roughness", text="Roughness")
        col.prop(coat3D, "coat3D_ao", text="AO")
        col = flow.column()
        col.prop(coat3D, "coat3D_normal", text="NormalMap")
        col.prop(coat3D, "coat3D_displacement", text="Displacement")
        col.prop(coat3D, "coat3D_emissive", text="Emissive")
        col.prop(coat3D, "coat3D_alpha", text="Alpha")



class SCENE_PT_Settings_Update(ObjectButtonsPanel, bpy.types.Panel):
    bl_label = "Update"
    bl_parent_id = "SCENE_PT_Settings"
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        coat3D = bpy.context.scene.coat3D

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

class SCENE_PT_Bake_Settings(ObjectButtonsPanel, bpy.types.Panel):
    bl_label = "Bake"
    bl_parent_id = "SCENE_PT_Settings"
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        coat3D = bpy.context.scene.coat3D

        layout.active = True

        flow = layout.grid_flow(row_major=True, columns=0, even_columns=False, even_rows=False, align=True)

        col = flow.column()
        col.prop(coat3D, "bake_resolution", text="Resolution")
        col = flow.column()
        col.prop(coat3D, "bake_diffuse", text="Diffuse")
        col = flow.column()
        col.prop(coat3D, "bake_ao", text="AO")
        col = flow.column()
        col.prop(coat3D, "bake_normal", text="Normal")
        col = flow.column()
        col.prop(coat3D, "bake_roughness", text="Roughness")

class SCENE_PT_Settings_Folders(ObjectButtonsPanel, bpy.types.Panel):
    bl_label = "Folders"
    bl_parent_id = "SCENE_PT_Settings"
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        coat3D = bpy.context.scene.coat3D

        layout.active = True

        flow = layout.grid_flow(row_major=True, columns=0, even_columns=False, even_rows=False, align=True)

        col = flow.column()
        col.prop(coat3D, "exchangeFolder", text="Exchange folder")
        col.operator("save_new_export.pilgway_3d_coat", text="Save new Exchange folder")

        col = flow.column()
        col.prop(coat3D, "defaultfolder", text="Object/Texture folder")

        col = flow.column()
        col.prop(coat3D, "folder_size", text="Max count in Applink folder")

class SCENE_PT_Settings_DeleteNodes(ObjectButtonsPanel, bpy.types.Panel):
    bl_label = "Delete 3DC nodes from selected..."
    bl_parent_id = "SCENE_PT_Settings"
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        coat3D = bpy.context.scene.coat3D

        layout.active = True

        flow = layout.grid_flow(row_major=True, columns=0, even_columns=False, even_rows=False, align=True)

        col = flow.column()
        col.operator("delete_material_nodes.pilgway_3d_coat", text="Material")

        col.operator("delete_object_nodes.pilgway_3d_coat", text="Object(s)")

        col = flow.column()
        col.operator("delete_collection_nodes.pilgway_3d_coat", text="Collection")

        col.operator("delete_scene_nodes.pilgway_3d_coat", text="Scene")

        col = flow.column()
        col.prop(coat3D, "delete_images", text="Delete nodes images")




# 3D-Coat Dynamic Menu
class VIEW3D_MT_Coat_Dynamic_Menu(bpy.types.Menu):
    bl_label = "3D-Coat Applink Menu"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_WIN'

        ob = context
        if ob.mode == 'OBJECT':
            if(len(context.selected_objects) > 0):
                layout.operator("import_applink.pilgway_3d_coat",
                                text="Update Scene")
                layout.separator()

                layout.operator("export_applink.pilgway_3d_coat",
                                text="Transfer to 3D-Coat")
                layout.separator()

                if(context.selected_objects[0].coat3D.applink_3b_path != ''):
                    layout.operator("open_3dcoat.pilgway_3d_coat",
                                    text="Open " +context.selected_objects[0].coat3D.applink_3b_just_name)
                    layout.separator()

            else:
                layout.operator("import_applink.pilgway_3d_coat",
                                text="Update Scene")
                layout.separator()

            if (len(context.selected_objects) > 0):
                layout.operator("delete_material_nodes.pilgway_3d_coat",
                                text="Delete 3D-Coat nodes from active material")

                layout.operator("delete_object_nodes.pilgway_3d_coat",
                                text="Delete 3D-Coat nodes from selected objects")

            layout.operator("delete_collection_nodes.pilgway_3d_coat",
                            text="Delete 3D-Coat nodes from active collection")

            layout.operator("delete_scene_nodes.pilgway_3d_coat",
                            text="Delete all 3D-Coat nodes")
            layout.separator()



class ObjectCoat3D(PropertyGroup):

    obj_mat: StringProperty(
        name="Object_Path",
        default=''
    )
    applink_address: StringProperty(
        name="Object_Applink_address"
    )
    applink_index: StringProperty(
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
    retopo: BoolProperty(
        name="Retopo object",
        description="Retopo object",
        default=False
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

class SceneCoat3D(PropertyGroup):
    defaultfolder: StringProperty(
        name="FilePath",
        subtype="DIR_PATH",
    )
    deleteMode: StringProperty(
        name="FilePath",
        subtype="DIR_PATH",
        default=''
    )
    coat3D_exe: StringProperty(
        name="FilePath",
        subtype="FILE_PATH",
    )
    exchangeFolder: StringProperty(
        name="FilePath",
        subtype="DIR_PATH"
    )
    bring_retopo: BoolProperty(
        name="Import window",
        description="Allows to skip import dialog",
        default=False
    )
    foundExchangeFolder: BoolProperty(
        name="found Exchange Folder",
        description="found Exchange folder",
        default=False
    )
    delete_images: BoolProperty(
        name="Import window",
        description="Allows to skip import dialog",
        default=True
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
        default=True
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
               ("update", "Update mesh/uvs", ""),
               ),
        default="ppp"
    )
    bake_resolution: EnumProperty(
        name="Bake Resolution",
        description="Bake resolution",
        items=(("res_64", "64 x 64", ""),
               ("res_128", "128 x 128", ""),
               ("res_256", "256 x 256", ""),
               ("res_512", "512 x 512", ""),
               ("res_1024", "1024 x 1024", ""),
               ("res_2048", "2048 x 2048", ""),
               ("res_4096", "4096 x 4096", ""),
               ("res_8192", "8192 x 8192", ""),
               ),
        default="res_1024"
    )
    folder_size: EnumProperty(
        name="Applink folder size",
        description="Applink folder size",
        items=(("10", "10", ""),
               ("100", "100", ""),
               ("500", "500", ""),
               ("1000", "1000", ""),
               ("5000", "5000", ""),
               ("10000", "10000", ""),
               ),
        default="500"
    )
    bake_textures: BoolProperty(
        name="Bake all textures",
        description="Add Modifiers and export",
        default=False
    )
    bake_diffuse: BoolProperty(
        name="Bake diffuse texture",
        description="Add Modifiers and export",
        default=False
    )
    bake_ao: BoolProperty(
        name="Bake AO texture",
        description="Add Modifiers and export",
        default=False
    )
    bake_roughness: BoolProperty(
        name="Bake roughness texture",
        description="Add Modifiers and export",
        default=False
    )
    bake_metalness: BoolProperty(
        name="Bake metalness texture",
        description="Add Modifiers and export",
        default=False
    )
    bake_emissive: BoolProperty(
        name="Bake emissive texture",
        description="Add Modifiers and export",
        default=False
    )
    bake_normal: BoolProperty(
        name="Bake normal texture",
        description="Add Modifiers and export",
        default=False
    )
    bake_displacement: BoolProperty(
        name="Bake displacement",
        description="Add Modifiers and export",
        default=False
    )

class MeshCoat3D(PropertyGroup):
    applink_address: StringProperty(
        name="ApplinkAddress",
        # subtype="APPLINK_ADDRESS",
    )

class MaterialCoat3D(PropertyGroup):
    name: StringProperty(
        name="ApplinkAddress",
        # subtype="APPLINK_ADDRESS",
        default=''
    )
    bring_diffuse: BoolProperty(
        name="Import diffuse texture",
        description="Import diffuse texture",
        default=True
    )
    bring_metalness: BoolProperty(
        name="Import diffuse texture",
        description="Import diffuse texture",
        default=True
    )
    bring_roughness: BoolProperty(
        name="Import diffuse texture",
        description="Import diffuse texture",
        default=True
    )
    bring_normal: BoolProperty(
        name="Import diffuse texture",
        description="Import diffuse texture",
        default=True
    )
    bring_displacement: BoolProperty(
        name="Import diffuse texture",
        description="Import diffuse texture",
        default=True
    )
    bring_emissive: BoolProperty(
        name="Import diffuse texture",
        description="Import diffuse texture",
        default=True
    )
    bring_gloss: BoolProperty(
        name="Import diffuse texture",
        description="Import diffuse texture",
        default=True
    )

classes = (
    SCENE_PT_Main,
    SCENE_PT_Settings,
    SCENE_PT_Material,
    SCENE_PT_Settings_Update,
    SCENE_PT_Bake_Settings,
    SCENE_PT_Settings_DeleteNodes,
    SCENE_PT_Settings_Folders,
    SCENE_PT_Material_Import,
    SCENE_OT_folder,
    SCENE_OT_opencoat,
    SCENE_OT_export,
    SCENE_OT_getback,
    SCENE_OT_savenew,
    SCENE_OT_delete_material_nodes,
    SCENE_OT_delete_object_nodes,
    SCENE_OT_delete_collection_nodes,
    SCENE_OT_delete_scene_nodes,
    VIEW3D_MT_Coat_Dynamic_Menu,
    ObjectCoat3D,
    SceneCoat3D,
    MeshCoat3D,
    MaterialCoat3D,
    )

def register():

    bpy.types.Material.coat3D_diffuse = BoolProperty(
        name="Import diffuse texture",
        description="Import diffuse texture",
        default=True
    )
    bpy.types.Material.coat3D_roughness = BoolProperty(
        name="Import diffuse texture",
        description="Import diffuse texture",
        default=True
    )
    bpy.types.Material.coat3D_metalness = BoolProperty(
        name="Import diffuse texture",
        description="Import diffuse texture",
        default=True
    )
    bpy.types.Material.coat3D_normal = BoolProperty(
        name="Import diffuse texture",
        description="Import diffuse texture",
        default=True
    )
    bpy.types.Material.coat3D_displacement = BoolProperty(
        name="Import diffuse texture",
        description="Import diffuse texture",
        default=True
    )
    bpy.types.Material.coat3D_emissive = BoolProperty(
        name="Import diffuse texture",
        description="Import diffuse texture",
        default=True
    )
    bpy.types.Material.coat3D_ao = BoolProperty(
        name="Import diffuse texture",
        description="Import diffuse texture",
        default=True
    )
    bpy.types.Material.coat3D_alpha = BoolProperty(
        name="Import alpha texture",
        description="Import alpha texture",
        default=True
    )
    bpy.types.Material.coat3D_gloss = BoolProperty(
        name="Import alpha texture",
        description="Import alpha texture",
        default=True
    )




    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Object.coat3D = PointerProperty(type=ObjectCoat3D)
    bpy.types.Scene.coat3D = PointerProperty(type=SceneCoat3D)
    bpy.types.Mesh.coat3D = PointerProperty(type=MeshCoat3D)
    bpy.types.Material.coat3D = PointerProperty(type=MaterialCoat3D)
    bpy.app.handlers.load_post.append(load_handler)

    kc = bpy.context.window_manager.keyconfigs.addon

    if kc:
        km = kc.keymaps.new(name="3D View", space_type="VIEW_3D")
        kmi = km.keymap_items.new('wm.call_menu', 'Q', 'PRESS', shift=True)
        kmi.properties.name = "VIEW3D_MT_Coat_Dynamic_Menu"

def unregister():

    import bpy
    from bpy.utils import unregister_class

    del bpy.types.Object.coat3D
    del bpy.types.Scene.coat3D
    del bpy.types.Material.coat3D
    bpy.types.Material.coat3D_diffuse
    bpy.types.Material.coat3D_metalness
    bpy.types.Material.coat3D_roughness
    bpy.types.Material.coat3D_normal
    bpy.types.Material.coat3D_displacement
    bpy.types.Material.coat3D_emissive
    bpy.types.Material.coat3D_alpha

    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        km = kc.keymaps.get('3D View')
        for kmi in km.keymap_items:
            if kmi.idname == 'wm.call_menu':
                if kmi.properties.name == "VIEW3D_MT_Coat_Dynamic_Menu":
                    km.keymap_items.remove(kmi)

    for cls in reversed(classes):
        unregister_class(cls)
