# Copyright 2018-2019 The glTF-Blender-IO authors.
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

import json
import bpy
from mathutils import Matrix

from ..com.gltf2_blender_conversion import loc_gltf_to_blender, quaternion_gltf_to_blender, scale_to_matrix
from ...io.imp.gltf2_io_binary import BinaryData
from .gltf2_blender_animation_utils import simulate_stash, make_fcurve


class BlenderBoneAnim():
    """Blender Bone Animation."""
    def __new__(cls, *args, **kwargs):
        raise RuntimeError("%s should not be instantiated" % cls)

    @staticmethod
    def parse_translation_channel(gltf, node, obj, bone, channel, animation):
        """Manage Location animation."""
        blender_path = "pose.bones[" + json.dumps(bone.name) + "].location"
        group_name = bone.name

        keys = BinaryData.get_data_from_accessor(gltf, animation.samplers[channel.sampler].input)
        values = BinaryData.get_data_from_accessor(gltf, animation.samplers[channel.sampler].output)
        inv_bind_matrix = node.blender_bone_matrix.to_quaternion().to_matrix().to_4x4().inverted() \
            @ Matrix.Translation(node.blender_bone_matrix.to_translation()).inverted()

        if animation.samplers[channel.sampler].interpolation == "CUBICSPLINE":
            # TODO manage tangent?
            translation_keyframes = (
                loc_gltf_to_blender(values[idx * 3 + 1])
                for idx in range(0, len(keys))
            )
        else:
            translation_keyframes = (loc_gltf_to_blender(vals) for vals in values)
        if node.parent is None:
            parent_mat = Matrix()
        else:
            if not gltf.data.nodes[node.parent].is_joint:
                parent_mat = Matrix()
            else:
                parent_mat = gltf.data.nodes[node.parent].blender_bone_matrix

        # Pose is in object (armature) space and it's value if the offset from the bind pose
        # (which is also in object space)
        # Scale is not taken into account
        final_translations = [
            inv_bind_matrix @ (parent_mat @ Matrix.Translation(translation_keyframe)).to_translation()
            for translation_keyframe in translation_keyframes
        ]

        BlenderBoneAnim.fill_fcurves(
            obj.animation_data.action,
            keys,
            final_translations,
            group_name,
            blender_path,
            animation.samplers[channel.sampler].interpolation
        )

    @staticmethod
    def parse_rotation_channel(gltf, node, obj, bone, channel, animation):
        """Manage rotation animation."""
        blender_path = "pose.bones[" + json.dumps(bone.name) + "].rotation_quaternion"
        group_name = bone.name

        keys = BinaryData.get_data_from_accessor(gltf, animation.samplers[channel.sampler].input)
        values = BinaryData.get_data_from_accessor(gltf, animation.samplers[channel.sampler].output)
        bind_rotation = node.blender_bone_matrix.to_quaternion()

        if animation.samplers[channel.sampler].interpolation == "CUBICSPLINE":
            # TODO manage tangent?
            quat_keyframes = [
                quaternion_gltf_to_blender(values[idx * 3 + 1])
                for idx in range(0, len(keys))
            ]
        else:
            quat_keyframes = [quaternion_gltf_to_blender(vals) for vals in values]


        if node.parent is None:
            final_rots = [
                bind_rotation.inverted() @ quat_keyframe
                for quat_keyframe in quat_keyframes
            ]
        else:
            if not gltf.data.nodes[node.parent].is_joint:
                parent_mat = Matrix()
            else:
                parent_mat = gltf.data.nodes[node.parent].blender_bone_matrix

            if parent_mat != parent_mat.inverted():
                final_rots = [
                    bind_rotation.rotation_difference(
                        (parent_mat @ quat_keyframe.to_matrix().to_4x4()).to_quaternion()
                    )
                    for quat_keyframe in quat_keyframes
                ]
            else:
                final_rots = [
                    bind_rotation.rotation_difference(quat_keyframe)
                    for quat_keyframe in quat_keyframes
                ]

        # Manage antipodal quaternions
        for i in range(1, len(final_rots)):
            if final_rots[i].dot(final_rots[i-1]) < 0:
                final_rots[i] = -final_rots[i]

        BlenderBoneAnim.fill_fcurves(
            obj.animation_data.action,
            keys,
            final_rots,
            group_name,
            blender_path,
            animation.samplers[channel.sampler].interpolation
        )

    @staticmethod
    def parse_scale_channel(gltf, node, obj, bone, channel, animation):
        """Manage scaling animation."""
        blender_path = "pose.bones[" + json.dumps(bone.name) + "].scale"
        group_name = bone.name

        keys = BinaryData.get_data_from_accessor(gltf, animation.samplers[channel.sampler].input)
        values = BinaryData.get_data_from_accessor(gltf, animation.samplers[channel.sampler].output)
        bind_scale = scale_to_matrix(node.blender_bone_matrix.to_scale())

        if animation.samplers[channel.sampler].interpolation == "CUBICSPLINE":
            # TODO manage tangent?
            scale_mats = (
                scale_to_matrix(loc_gltf_to_blender(values[idx * 3 + 1]))
                for idx in range(0, len(keys))
            )
        else:
            scale_mats = (scale_to_matrix(loc_gltf_to_blender(vals)) for vals in values)
        if node.parent is None:
            final_scales = [
                (bind_scale.inverted() @ scale_mat).to_scale()
                for scale_mat in scale_mats
            ]
        else:
            if not gltf.data.nodes[node.parent].is_joint:
                parent_mat = Matrix()
            else:
                parent_mat = gltf.data.nodes[node.parent].blender_bone_matrix

            final_scales = [
                (bind_scale.inverted() @ scale_to_matrix(parent_mat.to_scale()) @ scale_mat).to_scale()
                for scale_mat in scale_mats
            ]

        BlenderBoneAnim.fill_fcurves(
            obj.animation_data.action,
            keys,
            final_scales,
            group_name,
            blender_path,
            animation.samplers[channel.sampler].interpolation
        )

    @staticmethod
    def fill_fcurves(action, keys, values, group_name, blender_path, interpolation):
        """Create FCurves from the keyframe-value pairs (one per component)."""
        fps = bpy.context.scene.render.fps

        coords = [0] * (2 * len(keys))
        coords[::2] = (key[0] * fps for key in keys)

        for i in range(0, len(values[0])):
            coords[1::2] = (vals[i] for vals in values)
            make_fcurve(
                action,
                coords,
                data_path=blender_path,
                index=i,
                group_name=group_name,
                interpolation=interpolation,
            )

    @staticmethod
    def anim(gltf, anim_idx, node_idx):
        """Manage animation."""
        node = gltf.data.nodes[node_idx]
        blender_armature_name = gltf.data.skins[node.skin_id].blender_armature_name
        obj = bpy.data.objects[blender_armature_name]
        bone = obj.pose.bones[node.blender_bone_name]

        if anim_idx not in node.animations.keys():
            return

        animation = gltf.data.animations[anim_idx]

        action = gltf.arma_cache.get(blender_armature_name)
        if not action:
            name = animation.track_name + "_" + obj.name
            action = bpy.data.actions.new(name)
            gltf.needs_stash.append((obj, animation.track_name, action))
            gltf.arma_cache[blender_armature_name] = action

        if not obj.animation_data:
            obj.animation_data_create()
        obj.animation_data.action = action

        for channel_idx in node.animations[anim_idx]:
            channel = animation.channels[channel_idx]

            if channel.target.path == "translation":
                BlenderBoneAnim.parse_translation_channel(gltf, node, obj, bone, channel, animation)

            elif channel.target.path == "rotation":
                BlenderBoneAnim.parse_rotation_channel(gltf, node, obj, bone, channel, animation)

            elif channel.target.path == "scale":
                BlenderBoneAnim.parse_scale_channel(gltf, node, obj, bone, channel, animation)

