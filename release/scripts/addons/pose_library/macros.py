# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

"""
Pose Library - macros.
"""

import bpy


class POSELIB_OT_select_asset_and_select_bones(bpy.types.Macro):
    bl_idname = "poselib.select_asset_and_select_bones"
    bl_label = "Select Pose & Select Bones"


class POSELIB_OT_select_asset_and_deselect_bones(bpy.types.Macro):
    bl_idname = "poselib.select_asset_and_deselect_bones"
    bl_label = "Select Pose & Deselect Bones"


classes = (
    POSELIB_OT_select_asset_and_select_bones,
    POSELIB_OT_select_asset_and_deselect_bones,
)

_register, _unregister = bpy.utils.register_classes_factory(classes)


def register() -> None:
    _register()

    step = POSELIB_OT_select_asset_and_select_bones.define("FILE_OT_select")
    step.properties.open = False
    step.properties.deselect_all = True
    step = POSELIB_OT_select_asset_and_select_bones.define("POSELIB_OT_pose_asset_select_bones")
    step.properties.select = True

    step = POSELIB_OT_select_asset_and_deselect_bones.define("FILE_OT_select")
    step.properties.open = False
    step.properties.deselect_all = True
    step = POSELIB_OT_select_asset_and_deselect_bones.define("POSELIB_OT_pose_asset_select_bones")
    step.properties.select = False


def unregister() -> None:
    _unregister()
