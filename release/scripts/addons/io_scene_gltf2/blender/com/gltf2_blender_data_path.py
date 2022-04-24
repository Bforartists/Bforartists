# SPDX-License-Identifier: Apache-2.0
# Copyright 2018-2021 The glTF-Blender-IO authors.


def get_target_property_name(data_path: str) -> str:
    """Retrieve target property."""
    return data_path.rsplit('.', 1)[-1]


def get_target_object_path(data_path: str) -> str:
    """Retrieve target object data path without property"""
    path_split = data_path.rsplit('.', 1)
    self_targeting = len(path_split) < 2
    if self_targeting:
        return ""
    return path_split[0]

def get_rotation_modes(target_property: str) -> str:
    """Retrieve rotation modes based on target_property"""
    if target_property == "rotation_euler":
        return True, False, ["XYZ", "XZY", "YXZ", "YZX", "ZXY", "ZYX"]
    elif target_property == "delta_rotation_euler":
        return True, True, ["XYZ", "XZY", "YXZ", "YZX", "ZXY", "ZYX"]
    elif target_property == "rotation_quaternion":
        return True, False, ["QUATERNION"]
    elif target_property == "delta_rotation_quaternion":
        return True, True, ["QUATERNION"]
    elif target_property in ["rotation_axis_angle"]:
        return True, False, ["AXIS_ANGLE"]
    else:
        return False, False, []

def is_bone_anim_channel(data_path: str) -> bool:
    return data_path[:10] == "pose.bones"