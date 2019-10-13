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

import bpy
from mathutils import Vector

from ..com.gltf2_blender_conversion import loc_gltf_to_blender, quaternion_gltf_to_blender, scale_gltf_to_blender
from ..com.gltf2_blender_conversion import correction_rotation
from ...io.imp.gltf2_io_binary import BinaryData
from .gltf2_blender_animation_utils import simulate_stash, make_fcurve


class BlenderNodeAnim():
    """Blender Object Animation."""
    def __new__(cls, *args, **kwargs):
        raise RuntimeError("%s should not be instantiated" % cls)

    @staticmethod
    def anim(gltf, anim_idx, node_idx):
        """Manage animation."""
        node = gltf.data.nodes[node_idx]
        obj = bpy.data.objects[node.blender_object]
        fps = bpy.context.scene.render.fps

        animation = gltf.data.animations[anim_idx]

        if anim_idx not in node.animations.keys():
            return

        for channel_idx in node.animations[anim_idx]:
            channel = animation.channels[channel_idx]
            if channel.target.path in ['translation', 'rotation', 'scale']:
                break
        else:
            return

        name = animation.track_name + "_" + obj.name
        action = bpy.data.actions.new(name)
        gltf.needs_stash.append((obj, animation.track_name, action))

        if not obj.animation_data:
            obj.animation_data_create()
        obj.animation_data.action = action

        for channel_idx in node.animations[anim_idx]:
            channel = animation.channels[channel_idx]

            keys = BinaryData.get_data_from_accessor(gltf, animation.samplers[channel.sampler].input)
            values = BinaryData.get_data_from_accessor(gltf, animation.samplers[channel.sampler].output)

            if channel.target.path not in ['translation', 'rotation', 'scale']:
                continue

            # There is an animation on object
            # We can't remove Yup2Zup object
            gltf.animation_object = True

            if animation.samplers[channel.sampler].interpolation == "CUBICSPLINE":
                # TODO manage tangent?
                values = [values[idx * 3 + 1] for idx in range(0, len(keys))]

            if channel.target.path == "translation":
                blender_path = "location"
                group_name = "Location"
                num_components = 3
                values = [loc_gltf_to_blender(vals) for vals in values]

            elif channel.target.path == "rotation":
                blender_path = "rotation_quaternion"
                group_name = "Rotation"
                num_components = 4
                if node.correction_needed is True:
                    values = [
                        (quaternion_gltf_to_blender(vals).to_matrix().to_4x4() @ correction_rotation()).to_quaternion()
                        for vals in values
                    ]
                else:
                    values = [quaternion_gltf_to_blender(vals) for vals in values]


                # Manage antipodal quaternions
                for i in range(1, len(values)):
                    if values[i].dot(values[i-1]) < 0:
                        values[i] = -values[i]

            elif channel.target.path == "scale":
                blender_path = "scale"
                group_name = "Scale"
                num_components = 3
                values = [scale_gltf_to_blender(vals) for vals in values]

            coords = [0] * (2 * len(keys))
            coords[::2] = (key[0] * fps for key in keys)

            for i in range(0, num_components):
                coords[1::2] = (vals[i] for vals in values)
                make_fcurve(
                    action,
                    coords,
                    data_path=blender_path,
                    index=i,
                    group_name=group_name,
                    interpolation=animation.samplers[channel.sampler].interpolation,
                )

