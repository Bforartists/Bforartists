# SPDX-FileCopyrightText: 2018-2021 The glTF-Blender-IO authors
#
# SPDX-License-Identifier: Apache-2.0

import bpy

def get_animation_target(action_group: bpy.types.ActionGroup):
    return action_group.channels[0].data_path.split('.')[-1]


def get_object_from_datapath(blender_object, data_path: str):
    if "." in data_path:
        # gives us: ('modifiers["Subsurf"]', 'levels')
        path_prop, path_attr = data_path.rsplit(".", 1)

        # same as: prop = obj.modifiers["Subsurf"]
        if path_attr in ["rotation", "scale", "location",
                         "rotation_axis_angle", "rotation_euler", "rotation_quaternion"]:
            prop = blender_object.path_resolve(path_prop)
        else:
            prop = blender_object.path_resolve(data_path)
    else:
        prop = blender_object
        # single attribute such as name, location... etc
        # path_attr = data_path

    return prop
