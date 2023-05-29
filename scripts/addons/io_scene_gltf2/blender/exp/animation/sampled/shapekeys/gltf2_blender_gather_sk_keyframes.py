# SPDX-License-Identifier: Apache-2.0
# Copyright 2018-2022 The glTF-Blender-IO authors.

import numpy as np
from ......blender.com.gltf2_blender_data_path import get_sk_exported
from ....gltf2_blender_gather_cache import cached
from ...gltf2_blender_gather_keyframes import Keyframe
from ..gltf2_blender_gather_animation_sampling_cache import get_cache_data


@cached
def gather_sk_sampled_keyframes(obj_uuid,
        action_name,
        export_settings):

    start_frame = export_settings['ranges'][obj_uuid][action_name]['start']
    end_frame  = export_settings['ranges'][obj_uuid][action_name]['end']

    keyframes = []

    frame = start_frame
    step = export_settings['gltf_frame_step']
    blender_obj = export_settings['vtree'].nodes[obj_uuid].blender_object
    while frame <= end_frame:
        key = Keyframe([None] * (len(get_sk_exported(blender_obj.data.shape_keys.key_blocks))), frame, 'value')
        key.value_total = get_cache_data(
            'sk',
            obj_uuid,
            None,
            action_name,
            frame,
            step,
            export_settings
        )

        keyframes.append(key)
        frame += step

    if len(keyframes) == 0:
        # For example, option CROP negative frames, but all are negatives
        return None

    # In case SK has only basis
    if any([len(k.value) == 0 for k in keyframes]):
        return None

    if not export_settings['gltf_optimize_animation']:
        return keyframes

    # For sk, if all values are the same, we keep only first and last
    cst = fcurve_is_constant(keyframes)
    return [keyframes[0], keyframes[-1]] if cst is True and len(keyframes) >= 2 else keyframes

def fcurve_is_constant(keyframes):
    return all([j < 0.0001 for j in np.ptp([[k.value[i] for i in range(len(keyframes[0].value))] for k in keyframes], axis=0)])
