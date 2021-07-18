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

from typing import List, Tuple

import bpy

addon_keymaps: List[Tuple[bpy.types.KeyMap, bpy.types.KeyMapItem]] = []


def register() -> None:
    wm = bpy.context.window_manager
    if wm.keyconfigs.addon is None:
        # This happens when Blender is running in the background.
        return

    km = wm.keyconfigs.addon.keymaps.new(name="File Browser Main", space_type="FILE_BROWSER")

    # DblClick to apply pose.
    kmi = km.keymap_items.new("poselib.apply_pose_asset_for_keymap", "LEFTMOUSE", "DOUBLE_CLICK")
    addon_keymaps.append((km, kmi))


def unregister() -> None:
    # Clear shortcuts from the keymap.
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
