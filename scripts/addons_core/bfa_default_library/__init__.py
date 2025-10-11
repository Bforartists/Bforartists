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
# Default Asset Library Addon
# A comprehensive asset library system with smart primitives and wizard operations
# -----------------------------------------------------------------------------

import bpy
import os

from bpy.utils import register_submodule_factory
from bpy.types import AddonPreferences, Context, Preferences, UILayout
from pathlib import Path
from os import path as p

# Configure the display names and sub-folders of your Libraries here:
LIB_NAME = "Default Library"
GEO_NAME = "Geometry Nodes Library"
SHADER_NAME = "Shader Nodes Library"
COMP_NAME = "Compositor Nodes Library"

bl_info = {
    "name": "Default Asset Library",
    "author": "Draise",
    "version": (1, 2, 2),
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

# -----------------------------------------------------------------------------
# Preferences and Library Management
# -----------------------------------------------------------------------------

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


def register_all_libraries():
    """Register all asset libraries."""
    register_library(LIB_NAME)
    register_library(GEO_NAME)
    register_library(SHADER_NAME)
    register_library(COMP_NAME)


def unregister_all_libraries():
    """Unregister all asset libraries."""
    unregister_library(LIB_NAME)
    unregister_library(GEO_NAME)
    unregister_library(SHADER_NAME)
    unregister_library(COMP_NAME)


# -----------------------------------------------------------------------------
# Main Registration
# -----------------------------------------------------------------------------

classes = (
    LIBADDON_APT_preferences,
)

# Define all submodules including the new operators and wizards modules
submodule_names = [
    "ui",              # User interface and menus
    "ops",             # Main operations and panels
    "operators",       # All operator classes (geometry, compositor, shader)
    "wizards",         # Wizard operations and handlers
]

# Get the register/unregister functions from the factory
register_submodules, unregister_submodules = register_submodule_factory(__name__, submodule_names)

def register():
    """Register the complete addon"""
    # Register preferences class
    for cls in classes:
        bpy.utils.register_class(cls)

    # Register all submodules
    register_submodules()

    # Register asset libraries using timer
    bpy.app.timers.register(register_all_libraries, first_interval=0.1)

def unregister():
    """Unregister the complete addon"""
    # Unregister all libraries
    unregister_all_libraries()

    # Unregister preferences class
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    # Unregister timer if exists
    try:
        bpy.app.timers.unregister(register_all_libraries)
    except Exception:
        pass

    # Unregister all submodules
    unregister_submodules()
