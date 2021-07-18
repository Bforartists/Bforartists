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
Pose Library based on the Asset Browser.
"""

bl_info = {
    "name": "Pose Library",
    "description": "Pose Library based on the Asset Browser.",
    "author": "Sybren A. Stüvel",
    "version": (2, 0),
    "blender": (3, 0, 0),
    "warning": "In heavily development, things may change",
    "location": "Asset Browser -> Animations, and 3D Viewport -> Animation panel",
    # "doc_url": "{BLENDER_MANUAL_URL}/addons/animation/pose_library.html",
    "support": "OFFICIAL",
    "category": "Animation",
}

from typing import List, Tuple

_need_reload = "operators" in locals()
from . import gui, keymaps, macros, operators, conversion

if _need_reload:
    import importlib

    gui = importlib.reload(gui)
    keymaps = importlib.reload(keymaps)
    macros = importlib.reload(macros)
    operators = importlib.reload(operators)
    conversion = importlib.reload(conversion)

import bpy

addon_keymaps: List[Tuple[bpy.types.KeyMap, bpy.types.KeyMapItem]] = []


def register() -> None:
    bpy.types.WindowManager.poselib_flipped = bpy.props.BoolProperty(
        name="Flip Pose",
        default=False,
    )
    bpy.types.WindowManager.poselib_previous_action = bpy.props.PointerProperty(type=bpy.types.Action)

    operators.register()
    macros.register()
    keymaps.register()
    gui.register()


def unregister() -> None:
    gui.unregister()
    keymaps.unregister()
    macros.unregister()
    operators.unregister()

    try:
        del bpy.types.WindowManager.poselib_flipped
    except AttributeError:
        pass
    try:
        del bpy.types.WindowManager.poselib_previous_action
    except AttributeError:
        pass
