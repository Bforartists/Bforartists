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

from . import ops

from bpy.utils import register_submodule_factory

from bpy.types import (
    AddonPreferences,
    Context,
    Preferences,
    UILayout,
)

from pathlib import Path
from os import path as p

####### SCRIPT TO PACK (run from Powershell) #######
# cd "[PATH TO ADDON CONTENTS]"
# blender --command extension build
#
# This will pack the addon contents into a zip file like this for extensions
#
# my_extension-0.0.1.zip
# ├─ __init__.py
# ├─ blender_manifest.toml
# └─ (..

bl_info = {
    "name": "Default Asset Library",
    "author": "Draise",
    "version": (1, 2, 1),
    "blender": (4, 4, 3),
    "location": "Asset Browser>Default Library",
    "description": "Adds a default library with complementary assets that you can use from the Asset Browser Editor",
    "warning": "This is the third iteration of the default asset library. Expect changes. Use at own risk.",
    "doc_url": "https://github.com/Bforartists/Manual",
    "tracker_url": "https://github.com/Bforartists/Bforartists",
    # Please go to https://github.com/BlenderDefender/implement_addon_updater to implement support for automatic library updates:
    "endpoint_url": "",
    "category": "Import-Export"
}
# Configure the display name and sub-folder of your Library here:
LIB_NAME = "Default Library"
GEO_NAME = "Geometry Nodes Library"
SHADER_NAME = "Shader Nodes Library"
COMP_NAME = "Compositor Nodes Library"

# Running code, don't change if not necessary!
# -----------------------------------------------------------------------------

# # safe_bl_idname = re.sub("\s", "_", re.sub("[^\w\s]", "", LIB_NAME)).lower()


class LIBADDON_APT_preferences(AddonPreferences):
    bl_idname = __package__

    def draw(self, context: Context):
        layout: UILayout = self.layout

        layout.label(
            text="Instructions",
            icon="INFO")

        layout.label(
            text="To access these default assets, switch to the Asset Browser editor,")
        layout.label(
            text="Go to the left library selector drop down and switch to the Smart Primitives Library.")
        layout.label(
            text="You will now see new your assets. Enjoy!")


def get_lib_path_index(prefs: Preferences, library_name: str):
    """Get the index of the library name or path for configuring them in the operator."""
    for index, lib in enumerate(prefs.filepaths.asset_libraries):
        if lib.path == p.dirname(__file__) or lib.name == library_name:
            return index
    return -1


def register_library(library_name: str):
    """Register a library in Blender, as long as the addon is enabled."""
    prefs = bpy.context.preferences
    index = get_lib_path_index(prefs, library_name)
    path = p.dirname(__file__)
    sub_folder = library_name
    full_path = os.path.join(path, sub_folder)

    # In case the library doesn't exist in the preferences, create it.
    if index == -1:
        bpy.ops.preferences.asset_library_add(directory=full_path)
        index = get_lib_path_index(prefs, library_name)

    # Set the correct name and path of the library to avoid issues because of wrong paths.
    prefs.filepaths.asset_libraries[index].name = library_name
    prefs.filepaths.asset_libraries[index].path = full_path


def unregister_library(library_name: str):
    """Remove a library from Bforartists, as soon as the addon is disabled."""
    prefs = bpy.context.preferences
    index = get_lib_path_index(prefs, library_name)

    if index == -1:
        return

    bpy.ops.preferences.asset_library_remove(index=index)
    #print(f"Unregistered library: {library_name}")


def register_all_libraries():
    """Register both the default and geometry nodes libraries."""
    register_library(LIB_NAME)
    register_library(GEO_NAME)
    register_library(SHADER_NAME)
    register_library(COMP_NAME)


def unregister_all_libraries():
    """Unregister both the default and geometry nodes libraries."""
    unregister_library(LIB_NAME)
    unregister_library(GEO_NAME)
    unregister_library(SHADER_NAME)
    unregister_library(COMP_NAME)

classes = (
    LIBADDON_APT_preferences,
)

submodule_names = [
    "ui",
    "ops",
    "handlers_collections",
]

# Get the register/unregister functions from the factory
register_submodules, unregister_submodules = register_submodule_factory(__name__, submodule_names)

# Registers the library when you load the addon.
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    register_submodules()

    # Register both libraries using the timer
    bpy.app.timers.register(register_all_libraries, first_interval=0.1)

# Unregisters the library when you unload the addon.
def unregister():
    # Unregister both libraries
    unregister_all_libraries()

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    try:
        bpy.app.timers.unregister(register_all_libraries)
    except Exception:
        pass

    unregister_submodules()
