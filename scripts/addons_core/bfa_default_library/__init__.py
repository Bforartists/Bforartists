# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
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

# -----------------------------------------------------------------------------
# ! IMPORTANT! READ THIS WHEN SETTING UP THE LIBRARY
# This is a work in progress, and many assets, categories, thumbnails and more are subject to change.
# Use at own risk. 
# -----------------------------------------------------------------------------

import bpy
import os

from bpy.types import (
    AddonPreferences,
    Context,
    Preferences,
    UILayout,
)

from pathlib import Path
from os import path as p

bl_info = {
    "name": "Default Asset Library",
    "author": "Draise (@trinumedia)",
    "version": (1, 0, 2),
    "blender": (3, 6, 0),
    "location": "Asset Browser>Default Library",
    "description": "Adds a default library with complementary assets that you can use from the Asset Browser Editor",
    "warning": "This is the second iteration of the default asset library. Expect changes. Use at own risk.",
    "doc_url": "https://github.com/Bforartists/Manual",
    "tracker_url": "https://github.com/Bforartists/Bforartists",
    # Please go to https://github.com/BlenderDefender/implement_addon_updater to implement support for automatic library updates:
    "endpoint_url": "",
    "support": "OFFICIAL",
    "category": "Bforartists",
}

# Configure the display name and sub-folder of your Library here:
LIB_NAME = "Default Library"

# Running code, don't change if not necessary!
# -----------------------------------------------------------------------------

# # safe_bl_idname = re.sub("\s", "_", re.sub("[^\w\s]", "", LIB_NAME)).lower()


class LIBADDON_APT_preferences(AddonPreferences):
    bl_idname = __package__

    def draw(self, context: Context):
        layout: UILayout = self.layout

        # Display addon inormation: Library name and Version.
        addon_version = bl_info['version']

        layout.label(
            text=f"{LIB_NAME} - Version {'.'.join(map(str, addon_version))}")
        layout.label(
            text="To access these defualt assets, switch to the Assets workspace or Asset Browser editor,")
        layout.label(
            text="Go to the Current Library drop down and switch to the Default Library.")
        layout.label(
            text="You will now see new categories, assets and more. Enjoy!")


def get_lib_path_index(prefs: Preferences):
    """Get the index of the library name or path for configuring them in the operator."""
    for index, lib in enumerate(prefs.filepaths.asset_libraries):
        if lib.path == p.dirname(__file__) or lib.name == LIB_NAME:
            return index
    return -1


def register_library():
    """Register the library in Blender, as long as the addon is enabled."""

    prefs = bpy.context.preferences

    index = get_lib_path_index(prefs)

    path = p.dirname(__file__)
    sub_folder = LIB_NAME

    full_path = os.path.join(path, sub_folder)

    # In case the library doesn't exist in the preferences, create it.
    if index == -1:
        bpy.ops.preferences.asset_library_add(
            directory=full_path)
        index = get_lib_path_index(prefs)

    # Set the correct name and path of the library to avoid issues because of wrong paths.
    prefs.filepaths.asset_libraries[index].name = LIB_NAME
    prefs.filepaths.asset_libraries[index].path = full_path
    return


def unregister_library():
    """Remove the library from Bforartists, as soon as the addon is disabled."""
    prefs = bpy.context.preferences

    index = get_lib_path_index(prefs)

    if index == -1:
        return

    bpy.ops.preferences.asset_library_remove(index=index)
    print("Unregistered library")

classes = (
    LIBADDON_APT_preferences,
)

#Registers the library when you load the addon.
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.app.timers.register(register_library, first_interval=0.1)

#Unregisters the library when you unload the addon.
def unregister():
    unregister_library()

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    try:
        bpy.app.timers.unregister(register_library)
    except Exception:
        pass
