# SPDX-License-Identifier: Apache-2.0
# Copyright 2018-2021 The glTF-Blender-IO authors.

import bpy
import typing
from mathutils import Matrix
from ....blender.com.gltf2_blender_data_path import get_sk_exported
from ....io.com import gltf2_io
from ....io.exp.gltf2_io_user_extensions import export_user_extensions
from ....io.com.gltf2_io_debug import print_console
from ..gltf2_blender_gather_tree import VExportNode
from .sampled.armature.gltf2_blender_gather_armature_action_sampled import gather_action_armature_sampled
from .sampled.object.gltf2_blender_gather_object_action_sampled import gather_action_object_sampled
from .sampled.shapekeys.gltf2_blender_gather_sk_channels import gather_sampled_sk_channel
from .gltf2_blender_gather_drivers import get_sk_drivers

def link_samplers(animation: gltf2_io.Animation, export_settings):
    """
    Move animation samplers to their own list and store their indices at their previous locations.

    After gathering, samplers are stored in the channels properties of the animation and need to be moved
    to their own list while storing an index into this list at the position where they previously were.
    This behaviour is similar to that of the glTFExporter that traverses all nodes
    :param animation:
    :param export_settings:
    :return:
    """
    # TODO: move this to some util module and update gltf2 exporter also
    T = typing.TypeVar('T')

    def __append_unique_and_get_index(l: typing.List[T], item: T):
        if item in l:
            return l.index(item)
        else:
            index = len(l)
            l.append(item)
            return index

    for i, channel in enumerate(animation.channels):
        animation.channels[i].sampler = __append_unique_and_get_index(animation.samplers, channel.sampler)


def reset_bone_matrix(blender_object, export_settings) -> None:
    if export_settings['gltf_export_reset_pose_bones'] is False:
        return

    # Only for armatures
    if blender_object.type != "ARMATURE":
        return

    # Remove current action if any
    if blender_object.animation_data and blender_object.animation_data.action:
        blender_object.animation_data.action = None

    # Resetting bones TRS to avoid to keep not keyed value on a future action set
    for bone in blender_object.pose.bones:
        bone.matrix_basis = Matrix()

def reset_sk_data(blender_object, blender_actions, export_settings) -> None:
    # Using NLA for SK is not so common
    # Reset to 0.0 will happen here only if there are at least 2 tracks to export
    if export_settings['gltf_export_reset_sk_data'] is False:
        return

    if len([i for i in blender_actions if i[2] == "SHAPEKEY"]) <= 1:
        return

    if blender_object.type != "MESH":
        return

    # Reset
    for sk in get_sk_exported(blender_object.data.shape_keys.key_blocks):
        sk.value = 0.0


def add_slide_data(start_frame, obj_uuid: int, key: str, export_settings):

    if obj_uuid not in export_settings['slide'].keys():
        export_settings['slide'][obj_uuid] = {}
    export_settings['slide'][obj_uuid][key] = start_frame
    # Add slide info for driver sk too
    obj_drivers = get_sk_drivers(obj_uuid, export_settings)
    for obj_dr in obj_drivers:
        if obj_dr not in export_settings['slide'].keys():
            export_settings['slide'][obj_dr] = {}
        export_settings['slide'][obj_dr][obj_uuid + "_" + key] = start_frame

def merge_tracks_perform(merged_tracks, animations, export_settings):
    to_delete_idx = []
    for merged_anim_track in merged_tracks.keys():
        if len(merged_tracks[merged_anim_track]) < 2:

            # There is only 1 animation in the track
            # If name of the track is not a default name, use this name for action
            if len(merged_tracks[merged_anim_track]) != 0:
                animations[merged_tracks[merged_anim_track][0]].name = merged_anim_track

            continue

        base_animation_idx = None
        offset_sampler = 0

        for idx, anim_idx in enumerate(merged_tracks[merged_anim_track]):
            if idx == 0:
                base_animation_idx = anim_idx
                animations[anim_idx].name = merged_anim_track
                already_animated = []
                for channel in animations[anim_idx].channels:
                    already_animated.append((channel.target.node, channel.target.path))
                continue

            to_delete_idx.append(anim_idx)

            # Merging extensions
            # Provide a hook to handle extension merging since there is no way to know author intent
            export_user_extensions('merge_animation_extensions_hook', export_settings, animations[anim_idx], animations[base_animation_idx])

            # Merging extras
            # Warning, some values can be overwritten if present in multiple merged animations
            if animations[anim_idx].extras is not None:
                for k in animations[anim_idx].extras.keys():
                    if animations[base_animation_idx].extras is None:
                        animations[base_animation_idx].extras = {}
                    animations[base_animation_idx].extras[k] = animations[anim_idx].extras[k]

            offset_sampler = len(animations[base_animation_idx].samplers)
            for sampler in animations[anim_idx].samplers:
                animations[base_animation_idx].samplers.append(sampler)

            for channel in animations[anim_idx].channels:
                if (channel.target.node, channel.target.path) in already_animated:
                    print_console("WARNING", "Some strips have same channel animation ({}), on node {} !".format(channel.target.path, channel.target.node.name))
                    continue
                animations[base_animation_idx].channels.append(channel)
                animations[base_animation_idx].channels[-1].sampler = animations[base_animation_idx].channels[-1].sampler + offset_sampler
                already_animated.append((channel.target.node, channel.target.path))

    new_animations = []
    if len(to_delete_idx) != 0:
        for idx, animation in enumerate(animations):
            if idx in to_delete_idx:
                continue
            new_animations.append(animation)
    else:
        new_animations = animations

    return new_animations

def bake_animation(obj_uuid: str, animation_key: str, export_settings, mode=None):

    # if there is no animation in file => no need to bake
    if len(bpy.data.actions) == 0:
        return None

    blender_object = export_settings['vtree'].nodes[obj_uuid].blender_object

    # No TRS animation are found for this object.
    # But we may need to bake
    # (Only when force sampling is ON)
    # If force sampling is OFF, can lead to inconsistent export anyway
    if (export_settings['gltf_bake_animation'] is True \
            or export_settings['gltf_animation_mode'] == "NLA_TRACKS") \
            and blender_object.type != "ARMATURE" and export_settings['gltf_force_sampling'] is True:
        animation = None
        # We also have to check if this is a skinned mesh, because we don't have to force animation baking on this case
        # (skinned meshes TRS must be ignored, says glTF specification)
        if export_settings['vtree'].nodes[obj_uuid].skin is None:
            if mode is None or mode == "OBJECT":
                animation = gather_action_object_sampled(obj_uuid, None, animation_key, export_settings)


        # Need to bake sk only if not linked to a driver sk by parent armature
        # In case of NLA track export, no baking of SK
        if export_settings['gltf_morph_anim'] \
                and blender_object.type == "MESH" \
                and blender_object.data is not None \
                and blender_object.data.shape_keys is not None:

            ignore_sk = False
            if export_settings['vtree'].nodes[obj_uuid].parent_uuid is not None \
                    and export_settings['vtree'].nodes[export_settings['vtree'].nodes[obj_uuid].parent_uuid].blender_type == VExportNode.ARMATURE:
                obj_drivers = get_sk_drivers(export_settings['vtree'].nodes[obj_uuid].parent_uuid, export_settings)
                if obj_uuid in obj_drivers:
                    ignore_sk = True

            if mode == "OBJECT":
                ignore_sk = True

            if ignore_sk is False:
                channel = gather_sampled_sk_channel(obj_uuid, animation_key, export_settings)
                if channel is not None:
                    if animation is None:
                        animation = gltf2_io.Animation(
                                channels=[channel],
                                extensions=None, # as other animations
                                extras=None, # Because there is no animation to get extras from
                                name=blender_object.name, # Use object name as animation name
                                samplers=[]
                            )
                    else:
                        animation.channels.append(channel)

        if animation is not None and animation.channels:
            link_samplers(animation, export_settings)
            return animation

    elif (export_settings['gltf_bake_animation'] is True \
            or export_settings['gltf_animation_mode'] == "NLA_TRACKS") \
            and blender_object.type == "ARMATURE" \
            and mode is None or mode == "OBJECT":
        # We need to bake all bones. Because some bone can have some constraints linking to
        # some other armature bones, for example

        animation = gather_action_armature_sampled(obj_uuid, None, animation_key, export_settings)
        link_samplers(animation, export_settings)
        if animation is not None:
            return animation
    return None
