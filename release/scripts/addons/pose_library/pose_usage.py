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
            bone_name = flip_side_name(bone_name)

        try:
            pose_bone = pose.bones[bone_name]
        except KeyError:
            continue

        pose_bone.bone.select = select


_FLIP_SEPARATORS = set(". -_")

# These are single-character replacements, others are handled differently.
_FLIP_REPLACEMENTS = {
    "l": "r",
    "L": "R",
    "r": "l",
    "R": "L",
}


def flip_side_name(to_flip: str) -> str:
    """Flip left and right indicators in the name.

    Basically a Python implementation of BLI_string_flip_side_name.

    >>> flip_side_name('bone_L.004')
    'bone_R.004'
    >>> flip_side_name('left_bone')
    'right_bone'
    >>> flip_side_name('Left_bone')
    'Right_bone'
    >>> flip_side_name('LEFT_bone')
    'RIGHT_bone'
    >>> flip_side_name('some.bone-RIGHT.004')
    'some.bone-LEFT.004'
    >>> flip_side_name('some.bone-right.004')
    'some.bone-left.004'
    >>> flip_side_name('some.bone-Right.004')
    'some.bone-Left.004'
    >>> flip_side_name('some.bone-LEFT.004')
    'some.bone-RIGHT.004'
    >>> flip_side_name('some.bone-left.004')
    'some.bone-right.004'
    >>> flip_side_name('some.bone-Left.004')
    'some.bone-Right.004'
    >>> flip_side_name('.004')
    '.004'
    >>> flip_side_name('L.004')
    'R.004'
    """
    import string

    if len(to_flip) < 3:
        # we don't flip names like .R or .L
        return to_flip

    # We first check the case with a .### extension, let's find the last period.
    number = ""
    replace = to_flip
    if to_flip[-1] in string.digits:
        try:
            index = to_flip.rindex(".")
        except ValueError:
            pass
        else:
            if to_flip[index + 1] in string.digits:
                # TODO(Sybren): this doesn't handle "bone.1abc2" correctly.
                number = to_flip[index:]
                replace = to_flip[:index]

    if not replace:
        # Nothing left after the number, so no flips necessary.
        return replace + number

    if len(replace) == 1:
        replace = _FLIP_REPLACEMENTS.get(replace, replace)
        return replace + number

    # First case; separator . - _ with extensions r R l L.
    if replace[-2] in _FLIP_SEPARATORS and replace[-1] in _FLIP_REPLACEMENTS:
        replace = replace[:-1] + _FLIP_REPLACEMENTS[replace[-1]]
        return replace + number

    # Second case; beginning with r R l L, with separator after it.
    if replace[1] in _FLIP_SEPARATORS and replace[0] in _FLIP_REPLACEMENTS:
        replace = _FLIP_REPLACEMENTS[replace[0]] + replace[1:]
        return replace + number

    lower = replace.lower()
    prefix = suffix = ""
    if lower.startswith("right"):
        bit = replace[0:2]
        if bit == "Ri":
            prefix = "Left"
        elif bit == "RI":
            prefix = "LEFT"
        else:
            prefix = "left"
        replace = replace[5:]
    elif lower.startswith("left"):
        bit = replace[0:2]
        if bit == "Le":
            prefix = "Right"
        elif bit == "LE":
            prefix = "RIGHT"
        else:
            prefix = "right"
        replace = replace[4:]
    elif lower.endswith("right"):
        bit = replace[-5:-3]
        if bit == "Ri":
            suffix = "Left"
        elif bit == "RI":
            suffix = "LEFT"
        else:
            suffix = "left"
        replace = replace[:-5]
    elif lower.endswith("left"):
        bit = replace[-4:-2]
        if bit == "Le":
            suffix = "Right"
        elif bit == "LE":
            suffix = "RIGHT"
        else:
            suffix = "right"
        replace = replace[:-4]

    return prefix + replace + suffix + number


if __name__ == '__main__':
    import doctest

    print(f"Test result: {doctest.testmod()}")
