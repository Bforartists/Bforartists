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
Pose Library - Conversion of old pose libraries.
"""

from typing import Optional
from collections.abc import Collection

if "pose_creation" not in locals():
    from . import pose_creation
else:
    import importlib

    pose_creation = importlib.reload(pose_creation)

import bpy
from bpy.types import (
    Action,
    TimelineMarker,
)


def convert_old_poselib(old_poselib: Action) -> Collection[Action]:
    """Convert an old-style pose library to a set of pose Actions.

    Old pose libraries were one Action with multiple pose markers. Each pose
    marker will be converted to an Action by itself and marked as asset.
    """

    pose_assets = [
        action
        for marker in old_poselib.pose_markers
        if (action := convert_old_pose(old_poselib, marker))
    ]

    # Mark all Actions as assets in one go. Ideally this would be done on an
    # appropriate frame in the scene (to set up things like the background
    # colour), but the old-style poselib doesn't contain such information. All
    # we can do is just render on the current frame.
    bpy.ops.asset.mark({'selected_ids': pose_assets})

    return pose_assets


def convert_old_pose(old_poselib: Action, marker: TimelineMarker) -> Optional[Action]:
    """Convert an old-style pose library pose to a pose action."""

    frame: int = marker.frame
    action: Optional[Action] = None

    for fcurve in old_poselib.fcurves:
        key = pose_creation.find_keyframe(fcurve, frame)
        if not key:
            continue

        if action is None:
            action = bpy.data.actions.new(marker.name)

        pose_creation.create_single_key_fcurve(action, fcurve, key)

    return action
