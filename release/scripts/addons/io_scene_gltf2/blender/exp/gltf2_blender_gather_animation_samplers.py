# SPDX-License-Identifier: Apache-2.0
# Copyright 2018-2021 The glTF-Blender-IO authors.


import typing
from io_scene_gltf2.blender.exp.gltf2_blender_gather_tree import VExportNode

import bpy
import mathutils
from io_scene_gltf2.blender.com import gltf2_blender_math
from io_scene_gltf2.blender.com.gltf2_blender_data_path import get_target_property_name, get_target_object_path
from io_scene_gltf2.blender.exp import gltf2_blender_gather_animation_sampler_keyframes
from io_scene_gltf2.blender.exp.gltf2_blender_gather_cache import cached
from io_scene_gltf2.blender.exp import gltf2_blender_gather_accessors
from io_scene_gltf2.blender.exp import gltf2_blender_get
from io_scene_gltf2.io.com import gltf2_io
from io_scene_gltf2.io.com import gltf2_io_constants
from io_scene_gltf2.io.exp import gltf2_io_binary_data
from . import gltf2_blender_export_keys
from io_scene_gltf2.io.exp.gltf2_io_user_extensions import export_user_extensions


@cached
def gather_animation_sampler(channels: typing.Tuple[bpy.types.FCurve],
                             obj_uuid: str,
                             bake_bone: typing.Union[str, None],
                             bake_channel: typing.Union[str, None],
                             bake_range_start,
                             bake_range_end,
                             force_range: bool,
                             action_name: str,
                             driver_obj_uuid,
                             node_channel_is_animated: bool,
                             need_rotation_correction,
                             export_settings
                             ) -> gltf2_io.AnimationSampler:

    blender_object = export_settings['vtree'].nodes[obj_uuid].blender_object
    is_armature = True if blender_object.type == "ARMATURE" else False
    blender_object_if_armature = blender_object if is_armature is True else None
    if is_armature is True and driver_obj_uuid is None:
        if bake_bone is None:
            pose_bone_if_armature = gltf2_blender_get.get_object_from_datapath(blender_object_if_armature,
                                                                               channels[0].data_path)
        else:
            pose_bone_if_armature = blender_object.pose.bones[bake_bone]
    else:
        pose_bone_if_armature = None
    non_keyed_values = __gather_non_keyed_values(channels, blender_object,
                                                 blender_object_if_armature, pose_bone_if_armature,
                                                 bake_channel,
                                                 driver_obj_uuid,
                                                 export_settings)
    if blender_object.parent is not None:
        matrix_parent_inverse = blender_object.matrix_parent_inverse.copy().freeze()
    else:
        matrix_parent_inverse = mathutils.Matrix.Identity(4).freeze()

    input = __gather_input(channels, obj_uuid, is_armature, non_keyed_values,
                         bake_bone, bake_channel, bake_range_start, bake_range_end, force_range, action_name, driver_obj_uuid, node_channel_is_animated, export_settings)

    if input is None:
        # After check, no need to animate this node for this channel
        return None

    sampler = gltf2_io.AnimationSampler(
        extensions=__gather_extensions(channels, blender_object_if_armature, export_settings, bake_bone, bake_channel),
        extras=__gather_extras(channels, blender_object_if_armature, export_settings, bake_bone, bake_channel),
        input=input,
        interpolation=__gather_interpolation(channels, blender_object_if_armature, export_settings, bake_bone, bake_channel),
        output=__gather_output(channels,
                               matrix_parent_inverse,
                               obj_uuid,
                               is_armature,
                               non_keyed_values,
                               bake_bone,
                               bake_channel,
                               bake_range_start,
                               bake_range_end,
                               force_range,
                               action_name,
                               driver_obj_uuid,
                               node_channel_is_animated,
                               need_rotation_correction,
                               export_settings)
    )

    export_user_extensions('gather_animation_sampler_hook',
                            export_settings,
                            sampler,
                            channels,
                            blender_object,
                            bake_bone,
                            bake_channel,
                            bake_range_start,
                            bake_range_end,
                            action_name)

    return sampler

def __gather_non_keyed_values(channels: typing.Tuple[bpy.types.FCurve],
                              blender_object: bpy.types.Object,
                              blender_object_if_armature: typing.Optional[bpy.types.Object],
                              pose_bone_if_armature: typing.Optional[bpy.types.PoseBone],
                              bake_channel: typing.Union[str, None],
                              driver_obj_uuid,
                              export_settings
                              ) ->  typing.Tuple[typing.Optional[float]]:

    non_keyed_values = []

    driver_obj = export_settings['vtree'].nodes[driver_obj_uuid].blender_object if driver_obj_uuid is not None else None
    obj = blender_object if driver_obj is None else driver_obj

    # Note: channels has some None items only for SK if some SK are not animated
    if None not in channels:
        # classic case for object TRS or bone TRS
        # Or if all morph target are animated

        if driver_obj is not None:
            # driver of SK
            return tuple([None] * len(channels))

        if bake_channel is None:
            target = channels[0].data_path.split('.')[-1]
        else:
            target = bake_channel
        if target == "value":
            # All morph targets are animated
            return tuple([None] * len(channels))

        indices = [c.array_index for c in channels]
        indices.sort()
        length = {
            "delta_location": 3,
            "delta_rotation_euler": 3,
            "location": 3,
            "rotation_axis_angle": 4,
            "rotation_euler": 3,
            "rotation_quaternion": 4,
            "scale": 3,
            "value": len(channels)
        }.get(target)

        if length is None:
            # This is not a known target
            return ()

        for i in range(0, length):
            if bake_channel is not None:
                non_keyed_values.append({
                    "delta_location" : obj.delta_location,
                    "delta_rotation_euler" : obj.delta_rotation_euler,
                    "location" : obj.location,
                    "rotation_axis_angle" : obj.rotation_axis_angle,
                    "rotation_euler" : obj.rotation_euler,
                    "rotation_quaternion" : obj.rotation_quaternion,
                    "scale" : obj.scale
                }[target][i])
            elif i in indices:
                non_keyed_values.append(None)
            else:
                if blender_object_if_armature is None:
                    non_keyed_values.append({
                        "delta_location" : obj.delta_location,
                        "delta_rotation_euler" : obj.delta_rotation_euler,
                        "location" : obj.location,
                        "rotation_axis_angle" : obj.rotation_axis_angle,
                        "rotation_euler" : obj.rotation_euler,
                        "rotation_quaternion" : obj.rotation_quaternion,
                        "scale" : obj.scale
                    }[target][i])
                else:
                     # TODO, this is not working if the action is not active (NLA case for example)
                     trans, rot, scale = pose_bone_if_armature.matrix_basis.decompose()
                     non_keyed_values.append({
                        "location": trans,
                        "rotation_axis_angle": rot,
                        "rotation_euler": rot,
                        "rotation_quaternion": rot,
                        "scale": scale
                        }[target][i])

        return tuple(non_keyed_values)

    else:
        # We are in case of morph target, where all targets are not animated
        # So channels has some None items
        first_channel = [c for c in channels if c is not None][0]
        object_path = get_target_object_path(first_channel.data_path)
        if object_path:
            shapekeys_idx = {}
            cpt_sk = 0
            for sk in obj.data.shape_keys.key_blocks:
                if sk == sk.relative_key:
                    continue
                if sk.mute is True:
                    continue
                shapekeys_idx[cpt_sk] = sk.name
                cpt_sk += 1

        for idx_c, channel in enumerate(channels):
            if channel is None:
                non_keyed_values.append(obj.data.shape_keys.key_blocks[shapekeys_idx[idx_c]].value)
            else:
                non_keyed_values.append(None)

        return tuple(non_keyed_values)

def __gather_extensions(channels: typing.Tuple[bpy.types.FCurve],
                        blender_object_if_armature: typing.Optional[bpy.types.Object],
                        export_settings,
                        bake_bone: typing.Union[str, None],
                        bake_channel: typing.Union[str, None]
                        ) -> typing.Any:
    return None


def __gather_extras(channels: typing.Tuple[bpy.types.FCurve],
                    blender_object_if_armature: typing.Optional[bpy.types.Object],
                    export_settings,
                    bake_bone: typing.Union[str, None],
                    bake_channel: typing.Union[str, None]
                    ) -> typing.Any:
    return None

@cached
def __gather_input(channels: typing.Tuple[bpy.types.FCurve],
                   blender_obj_uuid: str,
                   is_armature: bool,
                   non_keyed_values: typing.Tuple[typing.Optional[float]],
                   bake_bone: typing.Union[str, None],
                   bake_channel: typing.Union[str, None],
                   bake_range_start,
                   bake_range_end,
                   force_range: bool,
                   action_name,
                   driver_obj_uuid,
                   node_channel_is_animated: bool,
                   export_settings
                   ) -> gltf2_io.Accessor:
    """Gather the key time codes."""
    keyframes, is_baked = gltf2_blender_gather_animation_sampler_keyframes.gather_keyframes(blender_obj_uuid,
                                                                                  is_armature,
                                                                                  channels,
                                                                                  non_keyed_values,
                                                                                  bake_bone,
                                                                                  bake_channel,
                                                                                  bake_range_start,
                                                                                  bake_range_end,
                                                                                  force_range,
                                                                                  action_name,
                                                                                  driver_obj_uuid,
                                                                                  node_channel_is_animated,
                                                                                  export_settings)
    if keyframes is None:
        # After check, no need to animation this node
        return None
    times = [k.seconds for k in keyframes]

    return gltf2_blender_gather_accessors.gather_accessor(
        gltf2_io_binary_data.BinaryData.from_list(times, gltf2_io_constants.ComponentType.Float),
        gltf2_io_constants.ComponentType.Float,
        len(times),
        tuple([max(times)]),
        tuple([min(times)]),
        gltf2_io_constants.DataType.Scalar,
        export_settings
    )


def __gather_interpolation(channels: typing.Tuple[bpy.types.FCurve],
                           blender_object_if_armature: typing.Optional[bpy.types.Object],
                           export_settings,
                           bake_bone: typing.Union[str, None],
                           bake_channel: typing.Union[str, None]
                           ) -> str:

    # Note: channels has some None items only for SK if some SK are not animated

    if gltf2_blender_gather_animation_sampler_keyframes.needs_baking(blender_object_if_armature,
                                                                     channels,
                                                                     export_settings):
        if bake_bone is not None:
            # TODO: check if the bone was animated with CONSTANT
            return 'LINEAR'
        else:
            if len(channels) != 0: # channels can be empty when baking object (non animated selected object)
                max_keyframes = max([len(ch.keyframe_points) for ch in channels if ch is not None])
                # If only single keyframe revert to STEP
                if max_keyframes < 2:
                    return 'STEP'

                # If all keyframes are CONSTANT, we can use STEP.
                if all(all(k.interpolation == 'CONSTANT' for k in c.keyframe_points) for c in channels if c is not None):
                    return 'STEP'

            # Otherwise, sampled keyframes use LINEAR interpolation.
            return 'LINEAR'

    # Non-sampled keyframes implies that all keys are of the same type, and that the
    # type is supported by glTF (because we checked in needs_baking).
    blender_keyframe = [c for c in channels if c is not None][0].keyframe_points[0]

    # Select the interpolation method.
    return {
        "BEZIER": "CUBICSPLINE",
        "LINEAR": "LINEAR",
        "CONSTANT": "STEP"
    }[blender_keyframe.interpolation]


@cached
def __gather_output(channels: typing.Tuple[bpy.types.FCurve],
                    parent_inverse,
                    blender_obj_uuid: str,
                    is_armature: bool,
                    non_keyed_values: typing.Tuple[typing.Optional[float]],
                    bake_bone: typing.Union[str, None],
                    bake_channel: typing.Union[str, None],
                    bake_range_start,
                    bake_range_end,
                    force_range: bool,
                    action_name,
                    driver_obj,
                    node_channel_is_animated: bool,
                    need_rotation_correction: bool,
                    export_settings
                    ) -> gltf2_io.Accessor:
    """Gather the data of the keyframes."""
    keyframes, is_baked = gltf2_blender_gather_animation_sampler_keyframes.gather_keyframes(blender_obj_uuid,
                                                                                  is_armature,
                                                                                  channels,
                                                                                  non_keyed_values,
                                                                                  bake_bone,
                                                                                  bake_channel,
                                                                                  bake_range_start,
                                                                                  bake_range_end,
                                                                                  force_range,
                                                                                  action_name,
                                                                                  driver_obj,
                                                                                  node_channel_is_animated,
                                                                                  export_settings)

    if is_baked is True:
        parent_inverse = mathutils.Matrix.Identity(4).freeze()

    blender_object_if_armature = export_settings['vtree'].nodes[blender_obj_uuid].blender_object if is_armature is True else None

    if bake_bone is not None:
        target_datapath = "pose.bones['" + bake_bone + "']." + bake_channel
    else:
        if len(channels) != 0: # channels can be empty when baking object (non animated selected object)
            target_datapath = [c for c in channels if c is not None][0].data_path
        else:
            target_datapath = bake_channel

    is_yup = export_settings[gltf2_blender_export_keys.YUP]

    # bone animations need to be handled differently as they are in a different coordinate system
    if bake_bone is None:
        object_path = get_target_object_path(target_datapath)
    else:
        object_path = None

    # If driver_obj is set, this is a shapekey animation
    if driver_obj is not None:
        is_armature_animation = False
    else:
        is_armature_animation = bake_bone is not None or (blender_object_if_armature is not None and object_path != "")

    if is_armature_animation:
        if bake_bone is None:
            bone = gltf2_blender_get.get_object_from_datapath(blender_object_if_armature, object_path)
        else:
            bone = blender_object_if_armature.pose.bones[bake_bone]
        if isinstance(bone, bpy.types.PoseBone):
            if bone.parent is None:
                # bone at root of armature
                axis_basis_change = mathutils.Matrix.Identity(4)
                if export_settings[gltf2_blender_export_keys.YUP]:
                    axis_basis_change = mathutils.Matrix(
                        ((1.0, 0.0, 0.0, 0.0),
                         (0.0, 0.0, 1.0, 0.0),
                         (0.0, -1.0, 0.0, 0.0),
                         (0.0, 0.0, 0.0, 1.0)))
                correction_matrix_local = axis_basis_change @ bone.bone.matrix_local
            else:
                # Bone is not at root of armature
                # There are 2 cases :
                parent_uuid = export_settings['vtree'].nodes[export_settings['vtree'].nodes[blender_obj_uuid].bones[bone.name]].parent_uuid
                if parent_uuid is not None and export_settings['vtree'].nodes[parent_uuid].blender_type == VExportNode.BONE:
                    # export bone is not at root of armature neither
                    blender_bone_parent = export_settings['vtree'].nodes[parent_uuid].blender_bone
                    correction_matrix_local = (
                        blender_bone_parent.bone.matrix_local.inverted_safe() @
                        bone.bone.matrix_local
                    )
                else:
                    # exported bone (after filter) is at root of armature
                    axis_basis_change = mathutils.Matrix.Identity(4)
                    if export_settings[gltf2_blender_export_keys.YUP]:
                        axis_basis_change = mathutils.Matrix(
                            ((1.0, 0.0, 0.0, 0.0),
                            (0.0, 0.0, 1.0, 0.0),
                            (0.0, -1.0, 0.0, 0.0),
                            (0.0, 0.0, 0.0, 1.0)))
                    correction_matrix_local = axis_basis_change

            transform = correction_matrix_local
        else:
            transform = mathutils.Matrix.Identity(4)
    else:
        transform = parent_inverse

    values = []
    fps = bpy.context.scene.render.fps
    for keyframe in keyframes:
        # Transform the data and build gltf control points
        value = gltf2_blender_math.transform(keyframe.value, target_datapath, transform, need_rotation_correction)
        if is_yup and not is_armature_animation:
            value = gltf2_blender_math.swizzle_yup(value, target_datapath)
        keyframe_value = gltf2_blender_math.mathutils_to_gltf(value)

        if keyframe.in_tangent is not None:
            # we can directly transform the tangent as it currently is represented by a control point
            in_tangent = gltf2_blender_math.transform(keyframe.in_tangent, target_datapath, transform, need_rotation_correction)
            if is_yup and blender_object_if_armature is None:
                in_tangent = gltf2_blender_math.swizzle_yup(in_tangent, target_datapath)
            # the tangent in glTF is relative to the keyframe value and uses seconds
            if not isinstance(value, list):
                in_tangent = fps * (in_tangent - value)
            else:
                in_tangent = [fps * (in_tangent[i] - value[i]) for i in range(len(value))]
            keyframe_value = gltf2_blender_math.mathutils_to_gltf(in_tangent) + keyframe_value  # append

        if keyframe.out_tangent is not None:
            # we can directly transform the tangent as it currently is represented by a control point
            out_tangent = gltf2_blender_math.transform(keyframe.out_tangent, target_datapath, transform, need_rotation_correction)
            if is_yup and blender_object_if_armature is None:
                out_tangent = gltf2_blender_math.swizzle_yup(out_tangent, target_datapath)
            # the tangent in glTF is relative to the keyframe value and uses seconds
            if not isinstance(value, list):
                out_tangent = fps * (out_tangent - value)
            else:
                out_tangent = [fps * (out_tangent[i] - value[i]) for i in range(len(value))]
            keyframe_value = keyframe_value + gltf2_blender_math.mathutils_to_gltf(out_tangent)  # append

        values += keyframe_value

    # store the keyframe data in a binary buffer
    component_type = gltf2_io_constants.ComponentType.Float
    if get_target_property_name(target_datapath) == "value":
        # channels with 'weight' targets must have scalar accessors
        data_type = gltf2_io_constants.DataType.Scalar
    else:
        data_type = gltf2_io_constants.DataType.vec_type_from_num(len(keyframes[0].value))

    return gltf2_io.Accessor(
        buffer_view=gltf2_io_binary_data.BinaryData.from_list(values, component_type),
        byte_offset=None,
        component_type=component_type,
        count=len(values) // gltf2_io_constants.DataType.num_elements(data_type),
        extensions=None,
        extras=None,
        max=None,
        min=None,
        name=None,
        normalized=None,
        sparse=None,
        type=data_type
    )
