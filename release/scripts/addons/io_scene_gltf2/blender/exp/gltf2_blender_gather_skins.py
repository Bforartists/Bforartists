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

import mathutils
from . import gltf2_blender_export_keys
from io_scene_gltf2.blender.exp.gltf2_blender_gather_cache import cached
from io_scene_gltf2.io.com import gltf2_io
from io_scene_gltf2.io.exp import gltf2_io_binary_data
from io_scene_gltf2.io.com import gltf2_io_constants
from io_scene_gltf2.blender.exp import gltf2_blender_gather_accessors
from io_scene_gltf2.blender.exp import gltf2_blender_gather_joints
from io_scene_gltf2.blender.com import gltf2_blender_math


@cached
def gather_skin(blender_object, mesh_object, export_settings):
    """
    Gather armatures, bones etc into a glTF2 skin object.

    :param blender_object: the object which may contain a skin
    :param mesh_object: the mesh object to be deformed
    :param export_settings:
    :return: a glTF2 skin object
    """
    if not __filter_skin(blender_object, export_settings):
        return None

    return gltf2_io.Skin(
        extensions=__gather_extensions(blender_object, export_settings),
        extras=__gather_extras(blender_object, export_settings),
        inverse_bind_matrices=__gather_inverse_bind_matrices(blender_object, mesh_object, export_settings),
        joints=__gather_joints(blender_object, export_settings),
        name=__gather_name(blender_object, export_settings),
        skeleton=__gather_skeleton(blender_object, export_settings)
    )


def __filter_skin(blender_object, export_settings):
    if not export_settings[gltf2_blender_export_keys.SKINS]:
        return False
    if blender_object.type != 'ARMATURE' or len(blender_object.pose.bones) == 0:
        return False

    return True


def __gather_extensions(blender_object, export_settings):
    return None


def __gather_extras(blender_object, export_settings):
    return None

def __gather_inverse_bind_matrices(blender_object, mesh_object, export_settings):
    axis_basis_change = mathutils.Matrix.Identity(4)
    if export_settings[gltf2_blender_export_keys.YUP]:
        axis_basis_change = mathutils.Matrix(
            ((1.0, 0.0, 0.0, 0.0), (0.0, 0.0, 1.0, 0.0), (0.0, -1.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)))

    # build the hierarchy of nodes out of the bones
    root_bones = []
    for blender_bone in blender_object.pose.bones:
        if not blender_bone.parent:
            root_bones.append(blender_bone)

    matrices = []

    # traverse the matrices in the same order as the joints and compute the inverse bind matrix
    def __collect_matrices(bone):
        matrix_world = gltf2_blender_math.multiply(blender_object.matrix_world, mesh_object.matrix_world.inverted())
        inverse_bind_matrix = gltf2_blender_math.multiply(
            axis_basis_change,
            gltf2_blender_math.multiply(
                matrix_world,
                bone.bone.matrix_local
            )
        ).inverted()
        matrices.append(inverse_bind_matrix)

        for child in bone.children:
            __collect_matrices(child)

    # start with the "root" bones and recurse into children, in the same ordering as the how joints are gathered
    for root_bone in root_bones:
        __collect_matrices(root_bone)

    # flatten the matrices
    inverse_matrices = []
    for matrix in matrices:
        for column in range(0, 4):
            for row in range(0, 4):
                inverse_matrices.append(matrix[row][column])

    binary_data = gltf2_io_binary_data.BinaryData.from_list(inverse_matrices, gltf2_io_constants.ComponentType.Float)
    return gltf2_blender_gather_accessors.gather_accessor(
        binary_data,
        gltf2_io_constants.ComponentType.Float,
        len(inverse_matrices) // gltf2_io_constants.DataType.num_elements(gltf2_io_constants.DataType.Mat4),
        None,
        None,
        gltf2_io_constants.DataType.Mat4,
        export_settings
    )


def __gather_joints(blender_object, export_settings):
    root_joints = []
    # build the hierarchy of nodes out of the bones
    for blender_bone in blender_object.pose.bones:
        if not blender_bone.parent:
            root_joints.append(gltf2_blender_gather_joints.gather_joint(blender_bone, export_settings))

    # joints is a flat list containing all nodes belonging to the skin
    joints = []

    def __collect_joints(node):
        joints.append(node)
        for child in node.children:
            __collect_joints(child)
    for joint in root_joints:
        __collect_joints(joint)

    return joints


def __gather_name(blender_object, export_settings):
    return blender_object.name


def __gather_skeleton(blender_object, export_settings):
    # In the future support the result of https://github.com/KhronosGroup/glTF/pull/1195
    return None  # gltf2_blender_gather_nodes.gather_node(blender_object, export_settings)

