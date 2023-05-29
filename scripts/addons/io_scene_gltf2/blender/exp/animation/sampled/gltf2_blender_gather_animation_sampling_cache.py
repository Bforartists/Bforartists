# SPDX-License-Identifier: Apache-2.0
# Copyright 2018-2022 The glTF-Blender-IO authors.

import mathutils
import bpy
import typing
from .....blender.com.gltf2_blender_data_path import get_sk_exported
from ...gltf2_blender_gather_cache import datacache
from ...gltf2_blender_gather_tree import VExportNode
from ..gltf2_blender_gather_drivers import get_sk_drivers

# Warning : If you change some parameter here, need to be changed in cache system
@datacache
def get_cache_data(path: str,
                      blender_obj_uuid: str,
                      bone: typing.Optional[str],
                      action_name: str,
                      current_frame: int,
                      step: int,
                      export_settings,
                      only_gather_provided=False
                    ):

    data = {}

    min_, max_ = get_range(blender_obj_uuid, action_name, export_settings)

    if only_gather_provided:
        obj_uuids = [blender_obj_uuid]
    else:
        obj_uuids = [uid for (uid, n) in export_settings['vtree'].nodes.items() if n.blender_type not in [VExportNode.BONE]]

    frame = min_
    while frame <= max_:
        bpy.context.scene.frame_set(int(frame))

        for obj_uuid in obj_uuids:
            blender_obj = export_settings['vtree'].nodes[obj_uuid].blender_object

            # TODO: we may want to avoid looping on all objects, but an accurate filter must be found

            # calculate local matrix
            if export_settings['vtree'].nodes[obj_uuid].parent_uuid is None:
                parent_mat = mathutils.Matrix.Identity(4).freeze()
            else:
                if export_settings['vtree'].nodes[export_settings['vtree'].nodes[obj_uuid].parent_uuid].blender_type not in [VExportNode.BONE]:
                    parent_mat = export_settings['vtree'].nodes[export_settings['vtree'].nodes[obj_uuid].parent_uuid].blender_object.matrix_world
                else:
                    # Object animated is parented to a bone
                    blender_bone = export_settings['vtree'].nodes[export_settings['vtree'].nodes[obj_uuid].parent_bone_uuid].blender_bone
                    armature_object = export_settings['vtree'].nodes[export_settings['vtree'].nodes[export_settings['vtree'].nodes[obj_uuid].parent_bone_uuid].armature].blender_object
                    axis_basis_change = mathutils.Matrix(
                        ((1.0, 0.0, 0.0, 0.0), (0.0, 0.0, 1.0, 0.0), (0.0, -1.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)))

                    parent_mat = armature_object.matrix_world @ blender_bone.matrix @ axis_basis_change

            #For object inside collection (at root), matrix world is already expressed regarding collection parent
            if export_settings['vtree'].nodes[obj_uuid].parent_uuid is not None and export_settings['vtree'].nodes[export_settings['vtree'].nodes[obj_uuid].parent_uuid].blender_type == VExportNode.COLLECTION:
                parent_mat = mathutils.Matrix.Identity(4).freeze()

            mat = parent_mat.inverted_safe() @ blender_obj.matrix_world

            if obj_uuid not in data.keys():
                data[obj_uuid] = {}

            if blender_obj.animation_data and blender_obj.animation_data.action \
                    and export_settings['gltf_animation_mode'] in ["ACTIVE_ACTIONS", "ACTIONS"]:
                if blender_obj.animation_data.action.name not in data[obj_uuid].keys():
                    data[obj_uuid][blender_obj.animation_data.action.name] = {}
                    data[obj_uuid][blender_obj.animation_data.action.name]['matrix'] = {}
                    data[obj_uuid][blender_obj.animation_data.action.name]['matrix'][None] = {}
                data[obj_uuid][blender_obj.animation_data.action.name]['matrix'][None][frame] = mat
            elif export_settings['gltf_animation_mode'] in ["NLA_TRACKS"]:
                if action_name not in data[obj_uuid].keys():
                    data[obj_uuid][action_name] = {}
                    data[obj_uuid][action_name]['matrix'] = {}
                    data[obj_uuid][action_name]['matrix'][None] = {}
                data[obj_uuid][action_name]['matrix'][None][frame] = mat
            else:
                # case of baking object.
                # There is no animation, so use uuid of object as key
                if obj_uuid not in data[obj_uuid].keys():
                    data[obj_uuid][obj_uuid] = {}
                    data[obj_uuid][obj_uuid]['matrix'] = {}
                    data[obj_uuid][obj_uuid]['matrix'][None] = {}
                data[obj_uuid][obj_uuid]['matrix'][None][frame] = mat

            # Store data for all bones, if object is an armature
            if blender_obj.type == "ARMATURE":
                bones = export_settings['vtree'].get_all_bones(obj_uuid)
                if blender_obj.animation_data and blender_obj.animation_data.action \
                        and export_settings['gltf_animation_mode'] in ["ACTIVE_ACTIONS", "ACTIONS"]:
                    if 'bone' not in data[obj_uuid][blender_obj.animation_data.action.name].keys():
                        data[obj_uuid][blender_obj.animation_data.action.name]['bone'] = {}
                elif blender_obj.animation_data \
                        and export_settings['gltf_animation_mode'] in ["NLA_TRACKS"]:
                    if 'bone' not in data[obj_uuid][action_name].keys():
                        data[obj_uuid][action_name]['bone'] = {}
                else:
                    if 'bone' not in data[obj_uuid][obj_uuid].keys():
                        data[obj_uuid][obj_uuid]['bone'] = {}

                for bone_uuid in bones:
                    blender_bone = export_settings['vtree'].nodes[bone_uuid].blender_bone

                    if export_settings['vtree'].nodes[bone_uuid].parent_uuid is not None and export_settings['vtree'].nodes[export_settings['vtree'].nodes[bone_uuid].parent_uuid].blender_type == VExportNode.BONE:
                        blender_bone_parent = export_settings['vtree'].nodes[export_settings['vtree'].nodes[bone_uuid].parent_uuid].blender_bone
                        rest_mat = blender_bone_parent.bone.matrix_local.inverted_safe() @ blender_bone.bone.matrix_local
                        matrix = rest_mat.inverted_safe() @ blender_bone_parent.matrix.inverted_safe() @ blender_bone.matrix
                    else:
                        if blender_bone.parent is None:
                            matrix = blender_bone.bone.matrix_local.inverted_safe() @ blender_bone.matrix
                        else:
                            # Bone has a parent, but in export, after filter, is at root of armature
                            matrix = blender_bone.matrix.copy()

                    if blender_obj.animation_data and blender_obj.animation_data.action \
                            and export_settings['gltf_animation_mode'] in ["ACTIVE_ACTIONS", "ACTIONS"]:
                        if blender_bone.name not in data[obj_uuid][blender_obj.animation_data.action.name]['bone'].keys():
                            data[obj_uuid][blender_obj.animation_data.action.name]['bone'][blender_bone.name] = {}
                        data[obj_uuid][blender_obj.animation_data.action.name]['bone'][blender_bone.name][frame] = matrix
                    elif blender_obj.animation_data \
                            and export_settings['gltf_animation_mode'] in ["NLA_TRACKS"]:
                        if blender_bone.name not in data[obj_uuid][action_name]['bone'].keys():
                            data[obj_uuid][action_name]['bone'][blender_bone.name] = {}
                        data[obj_uuid][action_name]['bone'][blender_bone.name][frame] = matrix
                    else:
                        # case of baking object.
                        # There is no animation, so use uuid of object as key
                        if blender_bone.name not in data[obj_uuid][obj_uuid]['bone'].keys():
                            data[obj_uuid][obj_uuid]['bone'][blender_bone.name] = {}
                        data[obj_uuid][obj_uuid]['bone'][blender_bone.name][frame] = matrix


            # Check SK animation here, as we are caching data
            # This will avoid to have to do it again when exporting SK animation
            if export_settings['gltf_morph_anim'] and blender_obj.type == "MESH" \
            and blender_obj.data is not None \
            and blender_obj.data.shape_keys is not None \
            and blender_obj.data.shape_keys.animation_data is not None \
            and blender_obj.data.shape_keys.animation_data.action is not None \
            and export_settings['gltf_animation_mode'] in ["ACTIVE_ACTIONS", "ACTIONS"]:

                if blender_obj.data.shape_keys.animation_data.action.name not in data[obj_uuid].keys():
                    data[obj_uuid][blender_obj.data.shape_keys.animation_data.action.name] = {}
                    data[obj_uuid][blender_obj.data.shape_keys.animation_data.action.name]['sk'] = {}
                    data[obj_uuid][blender_obj.data.shape_keys.animation_data.action.name]['sk'][None] = {}
                data[obj_uuid][blender_obj.data.shape_keys.animation_data.action.name]['sk'][None][frame] = [k.value for k in get_sk_exported(blender_obj.data.shape_keys.key_blocks)]

            elif export_settings['gltf_morph_anim'] and blender_obj.type == "MESH" \
            and blender_obj.data is not None \
            and blender_obj.data.shape_keys is not None \
            and blender_obj.data.shape_keys.animation_data is not None \
            and export_settings['gltf_animation_mode'] in ["NLA_TRACKS"]:

                if action_name not in data[obj_uuid].keys():
                    data[obj_uuid][action_name] = {}
                    data[obj_uuid][action_name]['sk'] = {}
                    data[obj_uuid][action_name]['sk'][None] = {}
                if 'sk' not in data[obj_uuid][action_name].keys():
                    data[obj_uuid][action_name]['sk'] = {}
                    data[obj_uuid][action_name]['sk'][None] = {}
                data[obj_uuid][action_name]['sk'][None][frame] = [k.value for k in get_sk_exported(blender_obj.data.shape_keys.key_blocks)]



            elif export_settings['gltf_morph_anim'] and blender_obj.type == "MESH" \
                    and blender_obj.data is not None \
                    and blender_obj.data.shape_keys is not None:
                if obj_uuid not in data[obj_uuid].keys():
                    data[obj_uuid][obj_uuid] = {}
                    data[obj_uuid][obj_uuid]['sk'] = {}
                    data[obj_uuid][obj_uuid]['sk'][None] = {}
                elif 'sk' not in data[obj_uuid][obj_uuid].keys():
                    data[obj_uuid][obj_uuid]['sk'] = {}
                    data[obj_uuid][obj_uuid]['sk'][None] = {}
                data[obj_uuid][obj_uuid]['sk'][None][frame] = [k.value for k in get_sk_exported(blender_obj.data.shape_keys.key_blocks)]

            # caching driver sk meshes
            # This will avoid to have to do it again when exporting SK animation
            if blender_obj.type == "ARMATURE":
                sk_drivers = get_sk_drivers(obj_uuid, export_settings)
                for dr_obj in sk_drivers:
                    driver_object = export_settings['vtree'].nodes[dr_obj].blender_object
                    if dr_obj not in data.keys():
                        data[dr_obj] = {}
                    if blender_obj.animation_data and blender_obj.animation_data.action \
                            and export_settings['gltf_animation_mode'] in ["ACTIVE_ACTIONS", "ACTIONS"]:
                        if obj_uuid + "_" + blender_obj.animation_data.action.name not in data[dr_obj]: # Using uuid of armature + armature animation name as animation name
                            data[dr_obj][obj_uuid + "_" + blender_obj.animation_data.action.name] = {}
                            data[dr_obj][obj_uuid + "_" + blender_obj.animation_data.action.name]['sk'] = {}
                            data[dr_obj][obj_uuid + "_" + blender_obj.animation_data.action.name]['sk'][None] = {}
                        data[dr_obj][obj_uuid + "_" + blender_obj.animation_data.action.name]['sk'][None][frame] = [k.value for k in get_sk_exported(driver_object.data.shape_keys.key_blocks)]
                    if blender_obj.animation_data \
                            and export_settings['gltf_animation_mode'] in ["NLA_TRACKS"]:
                        if obj_uuid + "_" + action_name not in data[dr_obj]:
                            data[dr_obj][obj_uuid + "_" + action_name] = {}
                            data[dr_obj][obj_uuid + "_" + action_name]['sk'] = {}
                            data[dr_obj][obj_uuid + "_" + action_name]['sk'][None] = {}
                        data[dr_obj][obj_uuid + "_" + action_name]['sk'][None][frame] = [k.value for k in get_sk_exported(driver_object.data.shape_keys.key_blocks)]
                    else:
                        if obj_uuid + "_" + obj_uuid not in data[dr_obj]:
                            data[dr_obj][obj_uuid + "_" + obj_uuid] = {}
                            data[dr_obj][obj_uuid + "_" + obj_uuid]['sk'] = {}
                            data[dr_obj][obj_uuid + "_" + obj_uuid]['sk'][None] = {}
                        data[dr_obj][obj_uuid + "_" + obj_uuid]['sk'][None][frame] = [k.value for k in get_sk_exported(driver_object.data.shape_keys.key_blocks)]

        frame += step
    return data

# For perf, we may be more precise, and get a list of ranges to be exported that include all needed frames
def get_range(obj_uuid, key, export_settings):
    if export_settings['gltf_animation_mode'] in ["NLA_TRACKS"]:
        return export_settings['ranges'][obj_uuid][key]['start'], export_settings['ranges'][obj_uuid][key]['end']
    else:
        min_ = None
        max_ = None
        for obj in export_settings['ranges'].keys():
            for anim in export_settings['ranges'][obj].keys():
                if min_ is None or min_ > export_settings['ranges'][obj][anim]['start']:
                    min_ = export_settings['ranges'][obj][anim]['start']
                if max_ is None or max_ < export_settings['ranges'][obj][anim]['end']:
                    max_ = export_settings['ranges'][obj][anim]['end']
    return min_, max_
