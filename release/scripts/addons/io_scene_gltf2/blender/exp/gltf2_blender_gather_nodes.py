# Copyright 2018 The glTF-Blender-IO authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import bpy

from . import gltf2_blender_export_keys
from io_scene_gltf2.blender.exp.gltf2_blender_gather_cache import cached
from io_scene_gltf2.blender.exp import gltf2_blender_gather_skins
from io_scene_gltf2.blender.exp import gltf2_blender_gather_cameras
from io_scene_gltf2.blender.exp import gltf2_blender_gather_mesh
from io_scene_gltf2.blender.exp import gltf2_blender_gather_joints
from io_scene_gltf2.blender.exp import gltf2_blender_extract
from io_scene_gltf2.blender.exp import gltf2_blender_gather_lights
from io_scene_gltf2.io.com import gltf2_io
from io_scene_gltf2.io.com import gltf2_io_extensions


@cached
def gather_node(blender_object, export_settings):
    if not __filter_node(blender_object, export_settings):
        return None

    node = gltf2_io.Node(
        camera=__gather_camera(blender_object, export_settings),
        children=__gather_children(blender_object, export_settings),
        extensions=__gather_extensions(blender_object, export_settings),
        extras=__gather_extras(blender_object, export_settings),
        matrix=__gather_matrix(blender_object, export_settings),
        mesh=__gather_mesh(blender_object, export_settings),
        name=__gather_name(blender_object, export_settings),
        rotation=None,
        scale=None,
        skin=__gather_skin(blender_object, export_settings),
        translation=None,
        weights=__gather_weights(blender_object, export_settings)
    )
    node.translation, node.rotation, node.scale = __gather_trans_rot_scale(blender_object, export_settings)

    return node


def __filter_node(blender_object, export_settings):
    if blender_object.users == 0:
        return False
    if export_settings[gltf2_blender_export_keys.SELECTED] and blender_object.select_get() is False:
        return False
    if not export_settings[gltf2_blender_export_keys.LAYERS] and not blender_object.layers[0]:
        return False
    if blender_object.instance_collection is not None and not blender_object.instance_collection.layers[0]:
        return False

    return True


def __gather_camera(blender_object, export_settings):
    return gltf2_blender_gather_cameras.gather_camera(blender_object, export_settings)


def __gather_children(blender_object, export_settings):
    children = []
    # standard children
    for child_object in blender_object.children:
        node = gather_node(child_object, export_settings)
        if node is not None:
            children.append(node)
    # blender dupli objects
    if blender_object.instance_type == 'COLLECTION' and blender_object.instance_collection:
        for dupli_object in blender_object.instance_collection.objects:
            node = gather_node(dupli_object, export_settings)
            if node is not None:
                children.append(node)

    # blender bones
    if blender_object.type == "ARMATURE":
        for blender_bone in blender_object.pose.bones:
            if not blender_bone.parent:
                children.append(gltf2_blender_gather_joints.gather_joint(blender_bone, export_settings))

    return children


def __gather_extensions(blender_object, export_settings):
    extensions = {}

    if export_settings["gltf_lights"] and (blender_object.type == "LAMP" or blender_object.type == "LIGHT"):
        blender_lamp = blender_object.data
        light = gltf2_blender_gather_lights.gather_lights_punctual(
            blender_lamp,
            export_settings
        )
        if light is not None:
            light_extension = gltf2_io_extensions.ChildOfRootExtension(
                name="KHR_lights_punctual",
                path=["lights"],
                extension=light
            )
            extensions["KHR_lights_punctual"] = gltf2_io_extensions.Extension(
                name="KHR_lights_punctual",
                extension={
                    "light": light_extension
                }
            )

    return extensions if extensions else None


def __gather_extras(blender_object, export_settings):
    return None


def __gather_matrix(blender_object, export_settings):
    # return blender_object.matrix_local
    return []


def __gather_mesh(blender_object, export_settings):
    if blender_object.type == "MESH":
        # If not using vertex group, they are irrelevant for caching --> ensure that they do not trigger a cache miss
        vertex_groups = blender_object.vertex_groups
        modifiers = blender_object.modifiers
        if len(vertex_groups) == 0:
            vertex_groups = None
        if len(modifiers) == 0:
            modifiers = None

        return gltf2_blender_gather_mesh.gather_mesh(blender_object.data, vertex_groups, modifiers, export_settings)
    else:
        return None


def __gather_name(blender_object, export_settings):
    if blender_object.instance_type == 'COLLECTION' and blender_object.instance_collection:
        return "Duplication_Offset_" + blender_object.name
    return blender_object.name


def __gather_trans_rot_scale(blender_object, export_settings):
    trans, rot, sca = gltf2_blender_extract.decompose_transition(blender_object.matrix_local, 'NODE', export_settings)
    if blender_object.instance_type == 'COLLECTION' and blender_object.instance_collection:
        trans = -gltf2_blender_extract.convert_swizzle_location(
            blender_object.instance_collection.instance_offset, export_settings)
    translation, rotation, scale = (None, None, None)
    if trans[0] != 0.0 or trans[1] != 0.0 or trans[2] != 0.0:
        translation = [trans[0], trans[1], trans[2]]
    if rot[0] != 0.0 or rot[1] != 0.0 or rot[2] != 0.0 or rot[3] != 1.0:
        rotation = [rot[0], rot[1], rot[2], rot[3]]
    if sca[0] != 1.0 or sca[1] != 1.0 or sca[2] != 1.0:
        scale = [sca[0], sca[1], sca[2]]
    return translation, rotation, scale


def __gather_skin(blender_object, export_settings):
    modifiers = {m.type: m for m in blender_object.modifiers}

    if "ARMATURE" in modifiers:
        # Skins and meshes must be in the same glTF node, which is different from how blender handles armatures
        return gltf2_blender_gather_skins.gather_skin(modifiers["ARMATURE"].object, export_settings)


def __gather_weights(blender_object, export_settings):
    return None

