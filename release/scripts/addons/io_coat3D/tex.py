# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****

import bpy
import os
import re
import json

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


def UVTiling(objekti, texturelist):
    """ Checks what materials are linked into UV """

    objekti.coat3D.applink_scale = objekti.scale
    final_material_indexs = []
    uvtiles_index = []

    for poly in objekti.data.polygons:
        if (poly.material_index not in final_material_indexs):
            final_material_indexs.append(poly.material_index)
            loop_index = poly.loop_indices[0]
            uvtiles_index.append([poly.material_index, objekti.data.uv_layers.active.data[loop_index].uv[0]])
        if (len(final_material_indexs) == len(objekti.material_slots)):
            break
    print(final_material_indexs)

    for texture_info in texturelist:
        name = texture_info[0]
        final_name = name[1:]
        tiling_number = int(final_name)
        for list_tiles in uvtiles_index:
            if(list_tiles[1] >= (tiling_number - 1) and list_tiles[1] <= tiling_number ):
                texture_info[0] = objekti.material_slots[list_tiles[0]].material.name


    print('uvtiles_index', uvtiles_index)
    return texturelist


def readtexturefolder(objekti, mat_list, texturelist, is_new): #read textures from texture file

    create_nodes = False

    if texturelist[0][0] == '1001':
        print('This is UVTiling')
        texturelist = UVTiling(objekti, texturelist)
    print('texturelist:', texturelist)

    for index_mat in objekti.material_slots:

        texcoat = {}
        texcoat['color'] = []
        texcoat['ao'] = []
        texcoat['rough'] = []
        texcoat['metalness'] = []
        texcoat['nmap'] = []
        texcoat['emissive'] = []
        texcoat['emissive_power'] = []
        texcoat['displacement'] = []

        create_group_node = False
        for texture_info in texturelist:
            if texture_info[0] == index_mat.name:
                if texture_info[2] == 'color' or texture_info[2] == 'diffuse':
                    texcoat['color'].append(texture_info[3])
                    create_nodes = True
                elif texture_info[2] == 'metalness' or texture_info[2] == 'specular' or texture_info[2] == 'reflection':
                    texcoat['metalness'].append(texture_info[3])
                    create_nodes = True
                elif texture_info[2] == 'rough' or texture_info[2] == 'roughness':
                    texcoat['rough'].append(texture_info[3])
                    create_nodes = True
                elif texture_info[2] == 'nmap' or texture_info[2] == 'normalmap' or texture_info[2] == 'normal_map'  or texture_info[2] == 'normal':
                    texcoat['nmap'].append(texture_info[3])
                    create_nodes = True
                elif texture_info[2] == 'emissive':
                    texcoat['emissive'].append(texture_info[3])
                    create_nodes = True
                elif texture_info[2] == 'emissive_power':
                    texcoat['emissive_power'].append(texture_info[3])
                    create_nodes = True
                elif texture_info[2] == 'ao':
                    texcoat['ao'].append(texture_info[3])
                    create_nodes = True
                elif texture_info[2].startswith('displacement'):
                    texcoat['displacement'].append(texture_info[3])
                    create_nodes = True
                create_group_node = True
        if(create_nodes):
            coat3D = bpy.context.scene.coat3D
            path3b_n = coat3D.exchangedir
            path3b_n += ('%slast_saved_3b_file.txt' % (os.sep))

            if (os.path.isfile(path3b_n)):
                export_file = open(path3b_n)
                for line in export_file:
                    objekti.coat3D.applink_3b_path = line
                export_file.close()
                coat3D.remove_path = True
            createnodes(index_mat, texcoat, create_group_node)


def checkmaterial(mat_list, objekti): #check how many materials object has
    mat_list = []

    for obj_mate in objekti.material_slots:
        if(obj_mate.material.use_nodes == False):
            obj_mate.material.use_nodes = True


def createnodes(active_mat,texcoat, create_group_node): # Cretes new nodes and link textures into them
    bring_color = True # Meaning of these is to check if we can only update textures or do we need to create new nodes
    bring_metalness = True
    bring_roughness = True
    bring_normal = True
    bring_displacement = True
    bring_emissive = True
    bring_AO = True

    coat3D = bpy.context.scene.coat3D
    coatMat = active_mat.material

    if(coatMat.use_nodes == False):
        coatMat.use_nodes = True
    act_material = coatMat.node_tree
    main_material = coatMat.node_tree
    applink_group_node = False
    #ensimmaiseksi kaydaan kaikki image nodet lapi ja tarkistetaan onko nimi 3DC alkunen jos on niin reload

    for node in coatMat.node_tree.nodes:
        if (node.type == 'OUTPUT_MATERIAL'):
            out_mat = node
            break

    for node in act_material.nodes:
        if(node.name == '3DC_Applink' and node.type == 'GROUP'):
            applink_group_node = True
            act_material = node.node_tree
            group_tree = node.node_tree
            applink_tree = node
            break

    print('TeXture UPDATE happens')
    for node in act_material.nodes:
        if(node.type == 'TEX_IMAGE'):
            if(node.name == '3DC_color'):
                bring_color = False
                node.image.reload()
            elif(node.name == '3DC_metalness'):
                bring_metalness = False
                node.image.reload()
            elif(node.name == '3DC_rough'):
                bring_roughness = False
                node.image.reload()
            elif(node.name == '3DC_nmap'):
                bring_normal = False
                node.image.reload()
            elif(node.name == '3DC_displacement'):
                bring_displacement = False
                node.image.reload()
            elif (node.name == '3DC_emissive'):
                bring_emissive = False
                node.image.reload()
            elif (node.name == '3DC_AO'):
                bring_AO = False
                node.image.reload()

    #seuraavaksi lahdemme rakentamaan node tree. Lahdetaan Material Outputista rakentaa
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
            group_tree.outputs.new("NodeSocketColor", "Displacement")
            group_tree.outputs.new("NodeSocketColor", "Emissive")
            group_tree.outputs.new("NodeSocketColor", "Emissive Power")
            group_tree.outputs.new("NodeSocketColor", "AO")
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
                    emission_shader.location = 40, -330
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
        json_address = os.path.dirname(bpy.app.binary_path) + os.sep + '2.80' + os.sep + 'scripts' + os.sep + 'addons' + os.sep + 'io_coat3D' + os.sep + 'data.json'
        with open(json_address, encoding='utf-8') as data_file:
            data = json.loads(data_file.read())

        if(out_mat.inputs['Surface'].is_linked == True):
            if(bring_color == True and texcoat['color'] != []):
                CreateTextureLine(data['color'], act_material, main_mat, texcoat, coat3D, notegroup, main_material, applink_tree)

            if(bring_metalness == True and texcoat['metalness'] != []):
                CreateTextureLine(data['metalness'], act_material, main_mat, texcoat, coat3D, notegroup, main_material, applink_tree)

            if(bring_roughness == True and texcoat['rough'] != []):
                CreateTextureLine(data['rough'], act_material, main_mat, texcoat, coat3D, notegroup, main_material, applink_tree)

            if(bring_normal == True and texcoat['nmap'] != []):
                CreateTextureLine(data['nmap'], act_material, main_mat, texcoat, coat3D, notegroup, main_material, applink_tree)

            if (bring_normal == True and texcoat['emissive'] != []):
                CreateTextureLine(data['emissive'], act_material, main_mat, texcoat, coat3D, notegroup, main_material, applink_tree)


            ''' DISPLACEMENT '''

            if (bring_displacement == True and texcoat['displacement'] != []):
                node = act_material.nodes.new('ShaderNodeTexImage')
                node.name = '3DC_displacement'
                node.label = 'Displacement'
                # input_color = main_mat.inputs.find('Roughness') Blender 2.8 Does not support Displacement yet.
                if (texcoat['displacement']):
                    node.image = bpy.data.images.load(texcoat['displacement'][0])
                    node.color_space = 'NONE'

                if (coat3D.createnodes):
                    '''
                    curvenode = act_material.nodes.new('ShaderNodeRGBCurve')
                    curvenode.name = '3DC_RGBCurve'
                    huenode = act_material.nodes.new('ShaderNodeHueSaturation')
                    huenode.name = '3DC_HueSaturation'
                    rampnode = act_material.nodes.new('ShaderNodeValToRGB')
                    rampnode.name = '3DC_ColorRamp'
    
                    act_material.links.new(node.outputs[0], curvenode.inputs[1])
                    act_material.links.new(curvenode.outputs[0], rampnode.inputs[0])
                    act_material.links.new(rampnode.outputs[0], huenode.inputs[4])
                    '''
                    act_material.links.new(node.outputs[0], notegroup.inputs[4])

                    #if (main_mat.type == 'BSDF_PRINCIPLED'):
                        #main_material.links.new(applink_tree.outputs[2], main_mat.inputs[input_color])
                    node.location = -276, -579

                else:
                    node.location = -550, 0
                    act_material.links.new(node.outputs[0], notegroup.inputs[4])

def CreateTextureLine(type, act_material, main_mat, texcoat, coat3D, notegroup, main_material, applink_tree):

    node = act_material.nodes.new('ShaderNodeTexImage')

    if type['name'] == 'nmap':
        normal_node = act_material.nodes.new('ShaderNodeNormalMap')
        node.location = -650, -500
        normal_node.location = -350, -350
        normal_node.name = '3DC_normalnode'

    node.name = '3DC_' + type['name']
    node.label = type['name']

    for input_index in type['find_input']:
        input_color = main_mat.inputs.find(input_index)
        if(input_color != -1):
            break

    node.image = bpy.data.images.load(texcoat[type['name']][0])
    if(type['colorspace'] == 'noncolor'):
        node.color_space = 'NONE'

    if (coat3D.createnodes):
        if(type['name'] == 'nmap'):
            act_material.links.new(node.outputs[0], normal_node.inputs[1])
            if(input_color != -1):
                act_material.links.new(normal_node.outputs[0], main_mat.inputs[input_color])

            act_material.links.new(normal_node.outputs[0], notegroup.inputs[type['input']])
            if (main_mat.inputs[input_color].name == 'Normal' and input_color != -1):
                main_material.links.new(applink_tree.outputs[type['input']], main_mat.inputs[input_color])
        else:

            huenode = createExtraNodes(act_material, node, type)

            act_material.links.new(huenode.outputs[0], notegroup.inputs[type['input']])
            if (main_mat.type != 'MIX_SHADER' and input_color != -1):
                main_material.links.new(applink_tree.outputs[type['input']], main_mat.inputs[input_color])
            else:
                location = main_mat.location
                #applink_tree.location = main_mat.location[0], main_mat.location[1] + 200

            if(type['name'] == 'emissive'):
                for material in main_material.nodes:
                    if(material.name == '3DC_Emission'):
                        main_material.links.new(applink_tree.outputs[type['input']], material.inputs[0])
                        break


    else:
        node.location = type['node_location'][0], type['node_location'][1]
        act_material.links.new(node.outputs[0], notegroup.inputs[type['input']])
        if (input_color != -1):
            main_material.links.new(applink_tree.outputs[type['input']], main_mat.inputs[input_color])


def createExtraNodes(act_material, node, type):

    curvenode = act_material.nodes.new('ShaderNodeRGBCurve')
    curvenode.name = '3DC_RGBCurve'
    huenode = act_material.nodes.new('ShaderNodeHueSaturation')
    huenode.name = '3DC_HueSaturation'
    print('tieto:', type)
    print('ttoto: ', type['rampnode'])
    if(type['rampnode'] == 'yes'):
        rampnode = act_material.nodes.new('ShaderNodeValToRGB')
        rampnode.name = '3DC_ColorRamp'

    if (type['rampnode'] == 'yes'):
        act_material.links.new(node.outputs[0], curvenode.inputs[1])
        act_material.links.new(curvenode.outputs[0], rampnode.inputs[0])
        act_material.links.new(rampnode.outputs[0], huenode.inputs[4])
    else:
        act_material.links.new(node.outputs[0], curvenode.inputs[1])
        act_material.links.new(curvenode.outputs[0], huenode.inputs[4])

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

    return huenode

def matlab(objekti,mat_list,texturelist,is_new):

    ''' FBX Materials: remove all nodes and create princibles node'''
    if(is_new):
        RemoveFbxNodes(objekti)

    '''Main Loop for Texture Update'''
    #checkmaterial(mat_list, objekti)
    readtexturefolder(objekti,mat_list,texturelist,is_new)

    return('FINISHED')
