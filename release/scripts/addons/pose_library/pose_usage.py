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
Pose Library - usage functions.
"""

from typing import Set
import re
import bpy

from bpy.types import (
    Action,
    Object,
)


def select_bones(arm_object: Object, action: Action, *, select: bool, flipped: bool) -> None:
    pose_bone_re = re.compile(r'pose.bones\["([^"]+)"\]')
    pose = arm_object.pose

    seen_bone_names: Set[str] = set()

    for fcurve in action.fcurves:
        data_path: str = fcurve.data_path
        match = pose_bone_re.match(data_path)
        if not match:
            continue

        bone_name = match.group(1)

        if bone_name in seen_bone_names:
            continue
        seen_bone_names.add(bone_name)

        if flipped:
            bone_name = bpy.utils.flip_name(bone_name)

        try:
            pose_bone = pose.bones[bone_name]
        except KeyError:
            continue

        pose_bone.bone.select = select


if __name__ == '__main__':
    import doctest

    print(f"Test result: {doctest.testmod()}")
