# SPDX-FileCopyrightText: 2010-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
import os
import re
import json
from io_coat3D import updateimage

def find_index(objekti):

    luku = 0
    for tex in objekti.active_material.texture_slots:
        if(not(hasattr(tex,'texture'))):
            break
        luku = luku +1
    return luku


def RemoveFbxNodes(objekti):
    Node_Tree = objekti.active_material.node_tree
    for node in Node_Tree.nodes:
        if node.type != 'OUTPUT_MATERIAL':
            Node_Tree.nodes.remove(node)
        else:
            output = node
            output.location = 340,400
    Prin_mat = Node_Tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    Prin_mat.location = 13, 375

    Node_Tree.links.new(Prin_mat.outputs[0], output.inputs[0])


def updatetextures(objekti): # Update 3DC textures

    for index_mat in objekti.material_slots:

        for node in index_mat.material.node_tree.nodes:
            if (node.type == 'TEX_IMAGE'):
                if (node.name == '3DC_color' or node.name == '3DC_metalness' or node.name == '3DC_rough' or node.name == '3DC_nmap'
                or node.name == '3DC_displacement' or node.name == '3DC_emissive' or node.name == '3DC_AO' or node.name == '3DC_alpha'):
                    try:
                        node.image.reload()
                    except:
                        pass

    for index_node_group in bpy.data.node_groups:

        for node in index_node_group.nodes:
            if (node.type == 'TEX_IMAGE'):
                if (node.name == '3DC_color' or node.name == '3DC_metalness' or node.name == '3DC_rough' or node.name == '3DC_nmap'
                or node.name == '3DC_displacement' or node.name == '3DC_emissive' or node.name == '3DC_AO' or node.name == '3DC_alpha'):
                    try:
                        node.image.reload()
                    except:
                        pass

def testi(objekti, texture_info, index_mat_name, uv_MODE_mat, mat_index):
    if uv_MODE_mat == 'UV':

        uv_set_founded = False
        for uvset in objekti.data.uv_layers:

            if(uvset.name == texture_info):
                uv_set_founded = True

                break

        if(uv_set_founded):
            for uv_poly in objekti.data.uv_layers[texture_info].id_data.polygons:
                if(mat_index == uv_poly.material_index):
                    return True
        else:
            return False

    elif uv_MODE_mat == 'MAT':
        return (texture_info == index_mat_name)

def readtexturefolder(objekti, mat_list, texturelist, is_new, udim_textures, udim_len): #read textures from texture file

    # Let's check are we UVSet or MATERIAL mode
    create_nodes = False
    for ind, index_mat in enumerate(objekti.material_slots):

        texcoat = {}
        texcoat['color'] = []
        texcoat['ao'] = []
        texcoat['rough'] = []
        texcoat['metalness'] = []
        texcoat['nmap'] = []
        texcoat['emissive'] = []
        texcoat['emissive_power'] = []
        texcoat['displacement'] = []
        texcoat['alpha'] = []

        create_group_node = False
        if(udim_textures == False):
            for slot_index, texture_info in enumerate(texturelist):

                uv_MODE_mat = 'MAT'
                for index, layer in enumerate(objekti.data.uv_layers):
                    if(layer.name == texturelist[slot_index][0]):
                        uv_MODE_mat = 'UV'
                        break


                if(testi(objekti, texturelist[slot_index][0], index_mat.name, uv_MODE_mat, ind)) :
                    if (os.path.isfile(texture_info[3])):
                        if texture_info[2] == 'color' or texture_info[2] == 'diffuse':
                            if(index_mat.material.coat3D_diffuse):

                                texcoat['color'].append(texture_info[3])
                                create_nodes = True
                            else:
                                os.remove(texture_info[3])

                        elif texture_info[2] == 'metalness' or texture_info[2] == 'specular' or texture_info[2] == 'reflection':
                            if (index_mat.material.coat3D_metalness):
                                texcoat['metalness'].append(texture_info[3])
                                create_nodes = True
                            else:
                                os.remove(texture_info[3])

                        elif texture_info[2] == 'rough' or texture_info[2] == 'roughness':
                            if (index_mat.material.coat3D_roughness):
                                texcoat['rough'].append(texture_info[3])
                                create_nodes = True
                            else:
                                os.remove(texture_info[3])

                        elif texture_info[2] == 'nmap' or texture_info[2] == 'normalmap' or texture_info[2] == 'normal_map'  or texture_info[2] == 'normal':
                            if (index_mat.material.coat3D_normal):
                                texcoat['nmap'].append(texture_info[3])
                                create_nodes = True
                            else:
                                os.remove(texture_info[3])

                        elif texture_info[2] == 'emissive':
                            if (index_mat.material.coat3D_emissive):
                                texcoat['emissive'].append(texture_info[3])
                                create_nodes = True
                            else:
                                os.remove(texture_info[3])

                        elif texture_info[2] == 'emissive_power':
                            if (index_mat.material.coat3D_emissive):
                                texcoat['emissive_power'].append(texture_info[3])
                                create_nodes = True
                            else:
                                os.remove(texture_info[3])

                        elif texture_info[2] == 'ao':
                            if (index_mat.material.coat3D_ao):
                                texcoat['ao'].append(texture_info[3])
                                create_nodes = True
                            else:
                                os.remove(texture_info[3])

                        elif texture_info[2].startswith('displacement'):
                            if (index_mat.material.coat3D_displacement):
                                texcoat['displacement'].append(texture_info[3])
                                create_nodes = True
                            else:
                                os.remove(texture_info[3])

                        elif texture_info[2] == 'alpha' or texture_info[2] == 'opacity':
                            if (index_mat.material.coat3D_alpha):
                                texcoat['alpha'].append(texture_info[3])
                                create_nodes = True
                            else:
                                os.remove(texture_info[3])

                        create_group_node = True


        else:
            for texture_info in texturelist:
                if (os.path.isfile(texture_info[3])):
                    if texture_info[2] == 'color' or texture_info[2] == 'diffuse':
                        if texcoat['color'] == [] and texture_info[1] == '1001':
                            texcoat['color'].append(texture_info[3])
                            create_nodes = True
                    elif texture_info[2] == 'metalness' or texture_info[2] == 'specular' or texture_info[
                        2] == 'reflection':
                        if texcoat['metalness'] == [] and texture_info[1] == '1001':
                            texcoat['metalness'].append(texture_info[3])
                            create_nodes = True
                    elif texture_info[2] == 'rough' or texture_info[2] == 'roughness':
                        if texcoat['rough'] == [] and texture_info[1] == '1001':
                            texcoat['rough'].append(texture_info[3])
                            create_nodes = True
                    elif texture_info[2] == 'nmap' or texture_info[2] == 'normalmap' or texture_info[
                        2] == 'normal_map' or texture_info[2] == 'normal':
                        if texcoat['nmap'] == [] and texture_info[1] == '1001':
                            texcoat['nmap'].append(texture_info[3])
                            create_nodes = True
                    elif texture_info[2] == 'emissive':
                        if texcoat['emissive'] == [] and texture_info[1] == '1001':
                            texcoat['emissive'].append(texture_info[3])
                            create_nodes = True
                    elif texture_info[2] == 'emissive_power':
                        if texcoat['emissive_power'] == [] and texture_info[1] == '1001':
                            texcoat['emissive_power'].append(texture_info[3])
                            create_nodes = True
                    elif texture_info[2] == 'ao':
                        if texcoat['ao'] == [] and texture_info[1] == '1001':
                            texcoat['ao'].append(texture_info[3])
                            create_nodes = True
                    elif texture_info[2].startswith('displacement'):
                        if texcoat['displacement'] == [] and texture_info[1] == '1001':
                            texcoat['displacement'].append(texture_info[3])
                            create_nodes = True
                    if texture_info[2] == 'alpha' or texture_info[2] == 'opacity':
                        if texcoat['alpha'] == [] and texture_info[1] == '1001':
                            texcoat['alpha'].append(texture_info[3])
                            create_nodes = True
                    create_group_node = True

        if(create_nodes):
            coat3D = bpy.context.scene.coat3D
            path3b_n = coat3D.exchangeFolder
            path3b_n += ('%slast_saved_3b_file.txt' % (os.sep))

            if (os.path.isfile(path3b_n)):
                export_file = open(path3b_n)
                for line in export_file:
                    objekti.coat3D.applink_3b_path = line
                export_file.close()
                coat3D.remove_path = True
            createnodes(index_mat, texcoat, create_group_node, objekti, ind, is_new, udim_textures, udim_len)

def createnodes(active_mat,texcoat, create_group_node, objekti, ind, is_new, udim_textures, udim_len): # Creates new nodes and link textures into them
    bring_color = True # Meaning of these is to check if we can only update textures or do we need to create new nodes
    bring_metalness = True
    bring_roughness = True
    bring_normal = True
    bring_displacement = True
    bring_emissive = True
    bring_AO = True
    bring_alpha = True

    active_mat.material.show_transparent_back = False # HACK FOR BLENDER BUG

    coat3D = bpy.context.scene.coat3D
    coatMat = active_mat.material

    coatMat.blend_method = 'BLEND'

    if(coatMat.use_nodes == False):
        coatMat.use_nodes = True
    act_material = coatMat.node_tree
    main_material = coatMat.node_tree
    applink_group_node = False

    # First go through all image nodes and let's check if it starts with 3DC and reload if needed

    for node in coatMat.node_tree.nodes:
        if (node.type == 'OUTPUT_MATERIAL'):
            out_mat = node
            break

    for node in act_material.nodes:
        if(node.name == '3DC_Applink' and node.type == 'GROUP'):
            applink_group_node = True
            act_material = node.node_tree
            applink_tree = node
            break


    for node in act_material.nodes:
        if (node.type != 'GROUP'):
            if (node.type != 'GROUP_OUTPUT'):
                if (node.type == 'TEX_IMAGE'):
                    if (node.name == '3DC_color'):
                        bring_color = False
                        updateimage.update(texcoat, 'color', node, udim_textures, udim_len)
                    elif (node.name == '3DC_metalness'):
                        bring_metalness = False
                        updateimage.update(texcoat, 'metalness', node, udim_textures, udim_len)
                    elif (node.name == '3DC_rough'):
                        bring_roughness = False
                        updateimage.update(texcoat, 'rough', node, udim_textures, udim_len)
                    elif (node.name == '3DC_nmap'):
                        bring_normal = False
                        updateimage.update(texcoat, 'nmap', node, udim_textures, udim_len)
                    elif (node.name == '3DC_displacement'):
                        bring_displacement = False
                        updateimage.update(texcoat, 'displacement', node, udim_textures, udim_len)
                    elif (node.name == '3DC_emissive'):
                        bring_emissive = False
                        updateimage.update(texcoat, 'emissive', node, udim_textures, udim_len)
                    elif (node.name == '3DC_AO'):
                        bring_AO = False
                        updateimage.update(texcoat, 'ao', node, udim_textures, udim_len)
                    elif (node.name == '3DC_alpha'):
                        bring_alpha = False
                        updateimage.update(texcoat, 'alpha', node, udim_textures, udim_len)


        elif (node.type == 'GROUP' and node.name.startswith('3DC_')):
            if (node.name == '3DC_color'):
                bring_color = False
            elif (node.name == '3DC_metalness'):
                bring_metalness = False
            elif (node.name == '3DC_rough'):
                bring_roughness = False
            elif (node.name == '3DC_nmap'):
                bring_normal = False
            elif (node.name == '3DC_displacement'):
                bring_displacement = False
            elif (node.name == '3DC_emissive'):
                bring_emissive = False
            elif (node.name == '3DC_AO'):
                bring_AO = False
            elif (node.name == '3DC_alpha'):
                bring_alpha = False

    #Let's start to build new node tree. Let's start linking with Material Output

    if(create_group_node):
        if(applink_group_node == False):
            main_mat2 = out_mat.inputs['Surface'].links[0].from_node
            for input_ind in main_mat2.inputs:
                if(input_ind.is_linked):
                    main_mat3 = input_ind.links[0].from_node
                    if(main_mat3.type == 'BSDF_PRINCIPLED'):
                        main_mat = main_mat3

            group_tree = bpy.data.node_groups.new( type="ShaderNodeTree", name="3DC_Applink")
            group_tree.outputs.new("NodeSocketColor", "Color")
            group_tree.outputs.new("NodeSocketColor", "Metallic")
            group_tree.outputs.new("NodeSocketColor", "Roughness")
            group_tree.outputs.new("NodeSocketVector", "Normal map")
            group_tree.outputs.new("NodeSocketColor", "Emissive")
            group_tree.outputs.new("NodeSocketColor", "Displacement")
            group_tree.outputs.new("NodeSocketColor", "Emissive Power")
            group_tree.outputs.new("NodeSocketColor", "AO")
            group_tree.outputs.new("NodeSocketColor", "Alpha")
            applink_tree = act_material.nodes.new('ShaderNodeGroup')
            applink_tree.name = '3DC_Applink'
            applink_tree.node_tree = group_tree
            applink_tree.location = -400, -100
            act_material = group_tree
            notegroup = act_material.nodes.new('NodeGroupOutput')
            notegroup.location = 220, -260

            if(texcoat['emissive'] != []):
                from_output = out_mat.inputs['Surface'].links[0].from_node
                if(from_output.type == 'BSDF_PRINCIPLED'):
                    add_shader = main_material.nodes.new('ShaderNodeAddShader')
                    emission_shader = main_material.nodes.new('ShaderNodeEmission')

                    emission_shader.name = '3DC_Emission'

                    add_shader.location = 420, 110
                    emission_shader.location = 70, -330
                    out_mat.location = 670, 130

                    main_material.links.new(from_output.outputs[0], add_shader.inputs[0])
                    main_material.links.new(add_shader.outputs[0], out_mat.inputs[0])
                    main_material.links.new(emission_shader.outputs[0], add_shader.inputs[1])
                    main_mat = from_output
            else:
                main_mat = out_mat.inputs['Surface'].links[0].from_node

        else:
            main_mat = out_mat.inputs['Surface'].links[0].from_node
            index = 0
            for node in coatMat.node_tree.nodes:
                if (node.type == 'GROUP' and node.name =='3DC_Applink'):
                    for in_node in node.node_tree.nodes:
                        if(in_node.type == 'GROUP_OUTPUT'):
                            notegroup = in_node
                            index = 1
                            break
                if(index == 1):
                    break

        # READ DATA.JSON FILE
        platform = os.sys.platform

        if(platform == 'darwin'):
            json_address = os.path.dirname(bpy.app.binary_path) + os.sep + str(bpy.app.version[0]) + '.' + str(bpy.app.version[1]) + os.sep + 'scripts' + os.sep + 'addons' + os.sep + 'io_coat3D' + os.sep + 'data.json'
            json_address = json_address.replace('MacOS', 'Resources')

        else:
            json_address = os.path.dirname(bpy.app.binary_path) + os.sep + str(bpy.app.version[0]) + '.' + str(bpy.app.version[1]) + os.sep + 'scripts' + os.sep + 'addons' + os.sep + 'io_coat3D' + os.sep + 'data.json'


        with open(json_address, encoding='utf-8') as data_file:
            data = json.loads(data_file.read())

        if(out_mat.inputs['Surface'].is_linked == True):
            if(bring_color == True and texcoat['color'] != []):
                CreateTextureLine(data['color'], act_material, main_mat, texcoat, coat3D, notegroup,
                                  main_material, applink_tree, out_mat, coatMat, objekti, ind, is_new, udim_textures, udim_len)

            if(bring_metalness == True and texcoat['metalness'] != []):
                CreateTextureLine(data['metalness'], act_material, main_mat, texcoat, coat3D, notegroup,
                                  main_material, applink_tree, out_mat, coatMat, objekti, ind, is_new, udim_textures, udim_len)

            if(bring_roughness == True and texcoat['rough'] != []):
                CreateTextureLine(data['rough'], act_material, main_mat, texcoat, coat3D, notegroup,
                                  main_material, applink_tree, out_mat, coatMat, objekti, ind, is_new, udim_textures, udim_len)

            if(bring_normal == True and texcoat['nmap'] != []):
                CreateTextureLine(data['nmap'], act_material, main_mat, texcoat, coat3D, notegroup,
                                  main_material, applink_tree, out_mat, coatMat, objekti, ind, is_new, udim_textures, udim_len)

            if (bring_emissive == True and texcoat['emissive'] != []):
                CreateTextureLine(data['emissive'], act_material, main_mat, texcoat, coat3D, notegroup,
                                  main_material, applink_tree, out_mat, coatMat, objekti, ind, is_new, udim_textures, udim_len)

            if (bring_displacement == True and texcoat['displacement'] != []):
                CreateTextureLine(data['displacement'], act_material, main_mat, texcoat, coat3D, notegroup,
                                  main_material, applink_tree, out_mat, coatMat, objekti, ind, is_new, udim_textures, udim_len)
            if (bring_alpha == True and texcoat['alpha'] != []):
                CreateTextureLine(data['alpha'], act_material, main_mat, texcoat, coat3D, notegroup,
                                  main_material, applink_tree, out_mat, coatMat, objekti, ind, is_new, udim_textures, udim_len)


def CreateTextureLine(type, act_material, main_mat, texcoat, coat3D, notegroup, main_material, applink_tree, out_mat, coatMat, objekti, ind, is_new, udim_textures, udim_len):

    node = act_material.nodes.new('ShaderNodeTexImage')
    uv_node = act_material.nodes.new('ShaderNodeUVMap')
    if (is_new):
        uv_node.uv_map = objekti.data.uv_layers[ind].name
    else:
        uv_node.uv_map = objekti.data.uv_layers[0].name
    act_material.links.new(uv_node.outputs[0], node.inputs[0])
    uv_node.use_custom_color = True
    uv_node.color = (type['node_color'][0], type['node_color'][1], type['node_color'][2])

    node.use_custom_color = True
    node.color = (type['node_color'][0],type['node_color'][1],type['node_color'][2])


    if type['name'] == 'nmap':
        normal_node = act_material.nodes.new('ShaderNodeNormalMap')
        normal_node.use_custom_color = True
        normal_node.color = (type['node_color'][0], type['node_color'][1], type['node_color'][2])

        node.location = -671, -510
        uv_node.location = -750, -600
        normal_node.location = -350, -350
        normal_node.name = '3DC_normalnode'

    elif type['name'] == 'displacement':
        disp_node = main_material.nodes.new('ShaderNodeDisplacement')

        node.location = -630, -1160
        disp_node.location = 90, -460
        disp_node.inputs[2].default_value = 0.1
        disp_node.name = '3DC_dispnode'

    node.name = '3DC_' + type['name']
    node.label = type['name']

    if (type['name'] != 'displacement'):
        for input_index in type['find_input']:
            input_color = main_mat.inputs.find(input_index)
            if(input_color != -1):
                break

    load_image = True

    for image in bpy.data.images:

        if(os.path.normpath(texcoat[type['name']][0]) == os.path.normpath(image.filepath)):

            load_image = False
            node.image = image

            if(udim_textures):
                node.image.source = 'TILED'
                for udim_index in udim_len:
                    if (udim_index != 1001):
                        node.image.tiles.new(udim_index)

            node.image.reload()

            break

    if (load_image):

        node.image = bpy.data.images.load(os.path.normpath(texcoat[type['name']][0]))

        if(udim_textures):
            node.image.source = 'TILED'

        for udim_index in udim_len:
            if (udim_index != 1001):
                node.image.tiles.new(udim_index)


    if node.image and type['colorspace'] == 'noncolor':
        node.image.colorspace_settings.is_data = True

    if (coat3D.createnodes):

        if(type['name'] == 'nmap'):
            act_material.links.new(node.outputs[0], normal_node.inputs[1])
            if(input_color != -1):
                act_material.links.new(normal_node.outputs[0], main_mat.inputs[input_color])

            act_material.links.new(normal_node.outputs[0], notegroup.inputs[type['input']])
            if (main_mat.inputs[input_color].name == 'Normal' and input_color != -1):
                main_material.links.new(applink_tree.outputs[type['input']], main_mat.inputs[input_color])

        elif (type['name'] == 'displacement'):

            rampnode = act_material.nodes.new('ShaderNodeValToRGB')
            rampnode.name = '3DC_ColorRamp'
            rampnode.use_custom_color = True
            rampnode.color = (type['node_color'][0], type['node_color'][1], type['node_color'][2])
            rampnode.location = -270, -956

            act_material.links.new(node.outputs[0], rampnode.inputs[0])
            act_material.links.new(rampnode.outputs[0], notegroup.inputs[5])

            main_material.links.new(applink_tree.outputs[5], disp_node.inputs[0])
            main_material.links.new(disp_node.outputs[0], out_mat.inputs[2])
            coatMat.cycles.displacement_method = 'BOTH'

        else:
            if (texcoat['alpha'] != []):
                if (type['name'] == 'alpha'):
                    act_material.links.new(node.outputs[1], notegroup.inputs[8])
            else:
                if (type['name'] == 'color'):
                    act_material.links.new(node.outputs[1], notegroup.inputs[8])
            if(type['name'] != 'alpha'):
                huenode = createExtraNodes(act_material, node, type)
            else:
                huenode = node
                huenode.location = -100, -800

            if(type['name'] != 'alpha'):
                act_material.links.new(huenode.outputs[0], notegroup.inputs[type['input']])
            if (main_mat.type != 'MIX_SHADER' and input_color != -1):
                main_material.links.new(applink_tree.outputs[type['input']], main_mat.inputs[input_color])
                if(type['name'] == 'color'): #Alpha connection into Principled shader
                    main_material.links.new(applink_tree.outputs['Alpha'], main_mat.inputs['Alpha'])

            else:
                location = main_mat.location
                #applink_tree.location = main_mat.location[0], main_mat.location[1] + 200

            if(type['name'] == 'emissive'):
                for material in main_material.nodes:
                    if(material.name == '3DC_Emission'):
                        main_material.links.new(applink_tree.outputs[type['input']], material.inputs[0])
                        break

        uv_node.location = node.location
        uv_node.location[0] -= 300
        uv_node.location[1] -= 200

    else:
        node.location = type['node_location'][0], type['node_location'][1]
        if (tile_list == []):
            uv_node.location = node.location
            uv_node.location[0] -= 300
        act_material.links.new(node.outputs[0], notegroup.inputs[type['input']])
        if (input_color != -1):
            main_material.links.new(applink_tree.outputs[type['input']], main_mat.inputs[input_color])


def createExtraNodes(act_material, node, type):

    curvenode = act_material.nodes.new('ShaderNodeRGBCurve')
    curvenode.name = '3DC_RGBCurve'
    curvenode.use_custom_color = True
    curvenode.color = (type['node_color'][0], type['node_color'][1], type['node_color'][2])

    if(type['huenode'] == 'yes'):
        huenode = act_material.nodes.new('ShaderNodeHueSaturation')
        huenode.name = '3DC_HueSaturation'
        huenode.use_custom_color = True
        huenode.color = (type['node_color'][0], type['node_color'][1], type['node_color'][2])
    else:
        huenode = act_material.nodes.new('ShaderNodeMath')
        huenode.name = '3DC_HueSaturation'
        huenode.operation = 'MULTIPLY'
        huenode.inputs[1].default_value = 1
        huenode.use_custom_color = True
        huenode.color = (type['node_color'][0], type['node_color'][1], type['node_color'][2])


    if(type['rampnode'] == 'yes'):
        rampnode = act_material.nodes.new('ShaderNodeValToRGB')
        rampnode.name = '3DC_ColorRamp'
        rampnode.use_custom_color = True
        rampnode.color = (type['node_color'][0], type['node_color'][1], type['node_color'][2])

    if (type['rampnode'] == 'yes'):
        act_material.links.new(node.outputs[0], curvenode.inputs[1])
        act_material.links.new(curvenode.outputs[0], rampnode.inputs[0])
        if(type['huenode'] == 'yes'):
            act_material.links.new(rampnode.outputs[0], huenode.inputs[4])
        else:
            act_material.links.new(rampnode.outputs[0], huenode.inputs[0])
    else:
        act_material.links.new(node.outputs[0], curvenode.inputs[1])
        if (type['huenode'] == 'yes'):
            act_material.links.new(curvenode.outputs[0], huenode.inputs[4])
        else:
            act_material.links.new(curvenode.outputs[0], huenode.inputs[0])

    if type['name'] == 'metalness':
        node.location = -1300, 119
        curvenode.location = -1000, 113
        rampnode.location = -670, 115
        huenode.location = -345, 118

    elif type['name'] == 'rough':
        node.location = -1300, -276
        curvenode.location = -1000, -245
        rampnode.location = -670, -200
        huenode.location = -340, -100

    elif type['name'] == 'color':
        node.location = -990, 530
        curvenode.location = -660, 480
        huenode.location = -337, 335

    elif type['name'] == 'emissive':
        node.location = -1200, -900
        curvenode.location = -900, -900
        huenode.location = -340, -700

    elif type['name'] == 'alpha':
        node.location = -1200, -1200
        curvenode.location = -900, -1250
        rampnode.location = -600, -1200
        huenode.location = -300, -1200

    return huenode

def matlab(objekti,mat_list,texturelist,is_new):

    # FBX Materials: remove all nodes and create principle node

    if(is_new):
        RemoveFbxNodes(objekti)

    updatetextures(objekti)

    # Count udim tiles

    if(texturelist != []):

        udim_textures = False
        udim_count = 0
        udim_indexs = []

        if texturelist[0][0].startswith('10') and  len(texturelist[0][0]) == 4:
            udim_textures = True

            udim_target = ''
            udim_target  = texturelist[0][2]
            for texture in texturelist:
                if texture[2] == udim_target:
                    udim_indexs.append(int(texture[0]))

            udim_indexs.sort() # sort tiles list -> 1001, 1002, 1003...

        # Main loop for creating nodes

        readtexturefolder(objekti, mat_list, texturelist, is_new, udim_textures, udim_indexs)


    return('FINISHED')
