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
from mathutils import Matrix

from ..com.gltf2_blender_conversion import loc_gltf_to_blender, quaternion_gltf_to_blender, scale_to_matrix
from ...io.imp.gltf2_io_binary import BinaryData


class BlenderBoneAnim():
    """Blender Bone Animation."""
    def __new__(cls, *args, **kwargs):
        raise RuntimeError("%s should not be instantiated" % cls)

    @staticmethod
    def set_interpolation(interpolation, kf):
        """Set interpolation."""
        if interpolation == "LINEAR":
            kf.interpolation = 'LINEAR'
        elif interpolation == "STEP":
            kf.interpolation = 'CONSTANT'
        elif interpolation == "CUBICSPLINE":
            kf.interpolation = 'BEZIER'
        else:
            kf.interpolation = 'BEZIER'

    @staticmethod
    def parse_translation_channel(gltf, node, obj, bone, channel, animation):
        """Manage Location animation."""
        fps = bpy.context.scene.render.fps
        blender_path = "location"

        keys = BinaryData.get_data_from_accessor(gltf, animation.samplers[channel.sampler].input)
        values = BinaryData.get_data_from_accessor(gltf, animation.samplers[channel.sampler].output)
        inv_bind_matrix = node.blender_bone_matrix.to_quaternion().to_matrix().to_4x4().inverted() \
            @ Matrix.Translation(node.blender_bone_matrix.to_translation()).inverted()

        for idx, key in enumerate(keys):
            if animation.samplers[channel.sampler].interpolation == "CUBICSPLINE":
                # TODO manage tangent?
                translation_keyframe = loc_gltf_to_blender(values[idx * 3 + 1])
            else:
                translation_keyframe = loc_gltf_to_blender(values[idx])
            if not node.parent:
                parent_mat = Matrix()
            else:
                if not gltf.data.nodes[node.parent].is_joint:
                    parent_mat = Matrix()
                else:
                    parent_mat = gltf.data.nodes[node.parent].blender_bone_matrix

            # Pose is in object (armature) space and it's value if the offset from the bind pose
            # (which is also in object space)
            # Scale is not taken into account
            final_trans = (parent_mat @ Matrix.Translation(translation_keyframe)).to_translation()
            bone.location = inv_bind_matrix @ final_trans
            bone.keyframe_insert(blender_path, frame=key[0] * fps, group="location")

        for fcurve in [curve for curve in obj.animation_data.action.fcurves if curve.group.name == "location"]:
            for kf in fcurve.keyframe_points:
                BlenderBoneAnim.set_interpolation(animation.samplers[channel.sampler].interpolation, kf)

    @staticmethod
    def parse_rotation_channel(gltf, node, obj, bone, channel, animation):
        """Manage rotation animation."""
        # Note: some operations lead to issue with quaternions. Converting to matrix and then back to quaternions breaks
        # quaternion continuity
        # (see antipodal quaternions). Blender interpolates between two antipodal quaternions, which causes glitches in
        # animation.
        # Converting to euler and then back to quaternion is a dirty fix preventing this issue in animation, until a
        # better solution is found
        # This fix is skipped when parent matrix is identity
        fps = bpy.context.scene.render.fps
        blender_path = "rotation_quaternion"

        keys = BinaryData.get_data_from_accessor(gltf, animation.samplers[channel.sampler].input)
        values = BinaryData.get_data_from_accessor(gltf, animation.samplers[channel.sampler].output)
        bind_rotation = node.blender_bone_matrix.to_quaternion()

        for idx, key in enumerate(keys):
            if animation.samplers[channel.sampler].interpolation == "CUBICSPLINE":
                # TODO manage tangent?
                quat_keyframe = quaternion_gltf_to_blender(values[idx * 3 + 1])
            else:
                quat_keyframe = quaternion_gltf_to_blender(values[idx])
            if not node.parent:
                bone.rotation_quaternion = bind_rotation.inverted() @ quat_keyframe
            else:
                if not gltf.data.nodes[node.parent].is_joint:
                    parent_mat = Matrix()
                else:
                    parent_mat = gltf.data.nodes[node.parent].blender_bone_matrix

                if parent_mat != parent_mat.inverted():
                    final_rot = (parent_mat @ quat_keyframe.to_matrix().to_4x4()).to_quaternion()
                    bone.rotation_quaternion = bind_rotation.rotation_difference(final_rot).to_euler().to_quaternion()
                else:
                    bone.rotation_quaternion = \
                        bind_rotation.rotation_difference(quat_keyframe).to_euler().to_quaternion()

            bone.keyframe_insert(blender_path, frame=key[0] * fps, group='rotation')

        for fcurve in [curve for curve in obj.animation_data.action.fcurves if curve.group.name == "rotation"]:
            for kf in fcurve.keyframe_points:
                BlenderBoneAnim.set_interpolation(animation.samplers[channel.sampler].interpolation, kf)

    @staticmethod
    def parse_scale_channel(gltf, node, obj, bone, channel, animation):
        """Manage scaling animation."""
        fps = bpy.context.scene.render.fps
        blender_path = "scale"

        keys = BinaryData.get_data_from_accessor(gltf, animation.samplers[channel.sampler].input)
        values = BinaryData.get_data_from_accessor(gltf, animation.samplers[channel.sampler].output)
        bind_scale = scale_to_matrix(node.blender_bone_matrix.to_scale())

        for idx, key in enumerate(keys):
            if animation.samplers[channel.sampler].interpolation == "CUBICSPLINE":
                # TODO manage tangent?
                scale_mat = scale_to_matrix(loc_gltf_to_blender(values[idx * 3 + 1]))
            else:
                scale_mat = scale_to_matrix(loc_gltf_to_blender(values[idx]))
            if not node.parent:
                bone.scale = (bind_scale.inverted() @ scale_mat).to_scale()
            else:
                if not gltf.data.nodes[node.parent].is_joint:
                    parent_mat = Matrix()
                else:
                    parent_mat = gltf.data.nodes[node.parent].blender_bone_matrix

                bone.scale = (
                    bind_scale.inverted() @ scale_to_matrix(parent_mat.to_scale()) @ scale_mat
                ).to_scale()

            bone.keyframe_insert(blender_path, frame=key[0] * fps, group='scale')

        for fcurve in [curve for curve in obj.animation_data.action.fcurves if curve.group.name == "scale"]:
            for kf in fcurve.keyframe_points:
                BlenderBoneAnim.set_interpolation(animation.samplers[channel.sampler].interpolation, kf)

    @staticmethod
    def anim(gltf, anim_idx, node_idx):
        """Manage animation."""
        node = gltf.data.nodes[node_idx]
        obj = bpy.data.objects[gltf.data.skins[node.skin_id].blender_armature_name]
        bone = obj.pose.bones[node.blender_bone_name]

        if anim_idx not in node.animations.keys():
            return

        animation = gltf.data.animations[anim_idx]

        if animation.name:
            name = animation.name + "_" + obj.name
        else:
            name = "Animation_" + str(anim_idx) + "_" + obj.name
        if name not in bpy.data.actions:
            action = bpy.data.actions.new(name)
        else:
            action = bpy.data.actions[name]
            # Check if this action has some users.
            # If no user (only 1 indeed), that means that this action must be deleted
            # (is an action from a deleted object)
            if action.users == 1:
                bpy.data.actions.remove(action)
                action = bpy.data.actions.new(name)
        if not obj.animation_data:
            obj.animation_data_create()
        obj.animation_data.action = bpy.data.actions[action.name]

        for channel_idx in node.animations[anim_idx]:
            channel = animation.channels[channel_idx]

            if channel.target.path == "translation":
                BlenderBoneAnim.parse_translation_channel(gltf, node, obj, bone, channel, animation)

            elif channel.target.path == "rotation":
                BlenderBoneAnim.parse_rotation_channel(gltf, node, obj, bone, channel, animation)

            elif channel.target.path == "scale":
                BlenderBoneAnim.parse_scale_channel(gltf, node, obj, bone, channel, animation)

