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
import shutil
import glob
import sys

from bpy.utils import register_submodule_factory
from bpy.types import AddonPreferences, Context, Preferences, UILayout
from pathlib import Path
from os import path as p

# Import utility functions
from . import utility

# -----------------------------------------------------------------------------
# CONFIGURATION - Edit these variables for each addon instance
# -----------------------------------------------------------------------------

# Addon identification - MUST BE UNIQUE for each compiled addon
ADDON_UNIQUE_ID = "default_asset_library_1_2_5"  # Change to match your addon name and version
ADDON_DISPLAY_NAME = "Default Asset Library"     # Change to match your addon's display name
ADDON_VERSION = (1, 2, 5)                   # Change to match your addon's version

# Library configuration - Only include libraries that exist in your packaged addon
CENTRAL_LIB_SUBFOLDERS = [
    "Default Library",
    "Geometry Nodes Library",
    "Shader Nodes Library",
    "Compositor Nodes Library"]  # Only include libraries that exist

# Library display names (for reference - do not change these)
LIB_NAME = "Default Library"
GEO_NAME = "Geometry Nodes Library"
SHADER_NAME = "Shader Nodes Library"
COMP_NAME = "Compositor Nodes Library"

# -----------------------------------------------------------------------------

# Central library base path will be determined at runtime


def get_central_library_base():
    """Get the central library path at runtime with debug output."""
    path = utility.get_central_library_path()
    # print(f"🛠️ Central library base path resolved to: {path}")
    # print(f"🛠️ Current file location: {__file__}")
    return path


CENTRAL_LIBRARY_BASE = None  # Will be set during registration

# This is for built in core addons, but won't show as an extension
bl_info = {
    "name": "Default Asset Library",
    "author": "Draise",
    "version": (1, 2, 5),
    "blender": (4, 4, 3),
    "location": "Asset Browser>Default Library",
    "description": "Adds a default library with complementary assets that you can use from the Asset Browser Editor",
    "warning": "This is the third iteration of the default asset library. Expect changes. Use at own risk.",
    "doc_url": "https://github.com/Bforartists/Manual",
    "tracker_url": "https://github.com/Bforartists/Bforartists",
    # Please go to https://github.com/BlenderDefender/implement_addon_updater
    # to implement support for automatic library updates:
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
            text="Go to the left library selector drop down and select:")
        layout.label(
            text="'Default Library', 'Geometry Nodes Library', 'Shader Nodes Library', or 'Compositor Nodes Library'.")
        layout.label(
            text="You will now see assets from the selected Bforartists library. Enjoy!")

        # Show central library info
        box = layout.box()
        box.label(text="Central Library Information", icon='LIBRARY_DATA_DIRECT')

        path = utility.get_central_library_path()

        box.label(text=f"Location: {path}")
        box.label(text=f"Active Addons: {utility.get_active_addons_count(path)}")


def get_lib_path_index(prefs: Preferences, library_name: str, library_path: str):
    """Get the index of the library name or path for configuring them in the operator."""
    for index, lib in enumerate(prefs.filepaths.asset_libraries):
        if lib.path == library_path or lib.name == library_name:
            return index
    return -1


def register_library():
    """Register each library subfolder as a separate library in Blender preferences."""
    prefs = bpy.context.preferences

    # Get central library path at runtime
    central_base = get_central_library_base()

    # Debug output
    # print(f"🔧 Registering Multiple Asset Libraries...")
    # print(f"   Source path: {p.dirname(__file__)}")
    # print(f"   Central base: {central_base}")
    # print(f"   Libraries to register: {CENTRAL_LIB_SUBFOLDERS}")

    # Check if source directories exist and filter to only existing ones
    existing_libraries = []
    for lib_name in CENTRAL_LIB_SUBFOLDERS:
        source_dir = p.join(p.dirname(__file__), lib_name)
        if p.exists(source_dir):
            # print(f"   ✅ Source directory exists: {source_dir}")
            existing_libraries.append(lib_name)
        else:
            pass
            # print(f"   ⚠ Source directory missing (skipping): {source_dir}")

            # print(f"   Libraries to process: {existing_libraries}")

            # Use unique addon info for proper tracking
    addon_info = {
        'name': ADDON_DISPLAY_NAME,
        'version': ADDON_VERSION,
        'unique_id': ADDON_UNIQUE_ID
    }

    # Add this addon to central library and copy assets (only existing libraries)
    utility.add_addon_to_central_library(addon_info, existing_libraries, p.dirname(__file__), central_base)

    # Register each subfolder as a separate library in Blender preferences
    registered_count = 0
    for lib_name in existing_libraries:
        library_path = p.join(central_base, lib_name)

        # Check if this specific library already exists in preferences
        lib_index = -1
        for i, lib in enumerate(prefs.filepaths.asset_libraries):
            if lib.path == library_path:
                lib_index = i
                break

        if lib_index == -1:
            # Library doesn't exist, create it
            try:
                bpy.ops.preferences.asset_library_add(directory=library_path)

                # Find the newly created library and set its name and import method
                for i, lib in enumerate(prefs.filepaths.asset_libraries):
                    if lib.path == library_path:
                        lib.name = lib_name
                        # Set import method to APPEND (1) instead of default PACKED (0)
                        lib.import_method = 'APPEND'
                        # print(f"   ✅ Registered library: {lib_name} -> {library_path} (Import Method: Append)")
                        registered_count += 1
                        break
            except Exception as e:
                print(f"   ❌ Could not register library {lib_name}: {e}")
        else:
            # Library already exists, update the name and ensure append mode
            lib_ref = prefs.filepaths.asset_libraries[lib_index]
            lib_ref.name = lib_name
            # Ensure import method is set to APPEND
            lib_ref.import_method = 'APPEND'
            # print(f"   ⏩ Library already registered: {lib_name} -> {library_path} (Import Method: Append)")
            registered_count += 1

    # print(f"   ✅ Successfully registered {registered_count} libraries")


def unregister_library():
    """Remove individual libraries if no other addons are using them."""
    try:
        # Get central library path at runtime
        central_base = get_central_library_base()

        # Use unique addon info for proper tracking
        addon_info = {
            'name': ADDON_DISPLAY_NAME,
            'version': ADDON_VERSION,
            'unique_id': ADDON_UNIQUE_ID
        }

        # Remove this addon from central library tracking
        utility.remove_addon_from_central_library(addon_info, central_base)

        # Check if no other addons are using the central library
        active_addons = utility.get_active_addons_count(central_base)
        # print(f"Active addons remaining: {active_addons}")

        if active_addons == 0:
            # No other addons using any libraries, so clean up completely
            try:
                prefs = bpy.context.preferences
                # Remove all libraries that match our subfolders
                for lib_name in CENTRAL_LIB_SUBFOLDERS:
                    lib_path = p.join(central_base, lib_name)
                    lib_index = get_lib_path_index(prefs, lib_name, lib_path)
                    if lib_index != -1:
                        try:
                            bpy.ops.preferences.asset_library_remove(index=lib_index)
                            # print(f"✓ Removed library from preferences: {lib_name}")
                        except Exception as e:
                            print(f"⚠ Could not remove library {lib_name} from preferences: {e}")
            except Exception as e:
                print(f"⚠ Could not access preferences during unregistration: {e}")
            
            # Force cleanup of central library files (remove everything)
            try:
                utility.cleanup_central_library(central_base)
                # print("✓ Central library files cleaned up")
            except Exception as e:
                print(f"⚠ Could not cleanup central library files: {e}")
        else:
            pass
            # Other addons are still using libraries, keep individual libraries registered
            print(f"✓ {active_addons} addon(s) still using central library, keeping individual libraries registered")
            
    except Exception as e:
        print(f"⚠ Error during library unregistration: {e}")
        print("⚠ Library cleanup may be incomplete")


def register_all_libraries():
    """Register the central asset library."""
    # print("🔄 register_all_libraries() called")
    register_library()


def unregister_all_libraries():
    """Unregister the central asset library if needed."""
    unregister_library()


# -----------------------------------------------------------------------------
# Main Registration
# -----------------------------------------------------------------------------

classes = (
    LIBADDON_APT_preferences,
)

# Define all submodules including the new operators and wizards modules
submodule_names = [
    "ui",              # User interface and menus
    "panels",          # Main panels
    "ops",             # Main operations
    "operators",       # All operator classes (geometry, compositor, shader)
    "wizards",         # Wizards
]
# Note: "utility" is NOT a submodule - it's just imported functions

# Get the register/unregister functions from the factory
register_submodules, unregister_submodules = register_submodule_factory(__name__, submodule_names)


def register():
    """Register the complete addon"""
    # print("=== BFA Default Library Addon Registration Started ===")

    # Register preferences class
    for cls in classes:
        bpy.utils.register_class(cls)

    # Register all submodules
    register_submodules()

    # Register asset libraries - try immediate registration first
    # Use load_post handler for reliable library registration
    # This ensures registration happens after Blender is fully loaded
    bpy.app.handlers.load_post.append(delayed_library_registration)
    # print("✓ Load post handler registered for delayed library setup")

    # Also try immediate registration in case we're already loaded
    try:
        register_all_libraries()
        # print(f"✓ Immediate Default Library registration successful")
    except Exception as e:
        print(f"⚠ Immediate registration failed (normal during startup): {e}")

        # print("=== BFA Default Library Addon Registration Completed ===")


def delayed_library_registration(scene):
    """Callback for load_post handler to register libraries after Blender loads."""
    # print("🔄 Delayed library registration triggered by load_post handler")
    try:
        register_all_libraries()
        # print(f"✓ Delayed Default Library registration successful")

        # Remove ourselves from the handler to avoid multiple registrations
        if delayed_library_registration in bpy.app.handlers.load_post:
            bpy.app.handlers.load_post.remove(delayed_library_registration)
            # print("✓ Removed load_post handler after successful registration")

    except Exception as e:
        print(f"⚠ Delayed Library registration failed: {e}")

def unregister():
    """Unregister the complete addon"""
    # print("=== BFA Default Library Addon Unregistration Started ===")

    # Try to remove load_post handler first to prevent any delayed calls
    try:
        if delayed_library_registration in bpy.app.handlers.load_post:
            bpy.app.handlers.load_post.remove(delayed_library_registration)
            # print("✓ Removed load_post handler")
    except Exception as e:
        print(f"⚠ Could not remove load_post handler: {e}")
    
    # Unregister all libraries (with error handling)
    try:
        unregister_all_libraries()
    except Exception as e:
        print(f"⚠ Error during library unregistration: {e}")

    try:
        # Force refresh of asset catalogs to remove our entries to avoid a hard crash
        bpy.ops.asset.library_refresh()
    except:
        pass

    # Unregister preferences class with error handling
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception as e:
            print(f"⚠ Could not unregister class {cls}: {e}")

            # Unregister timer if exists
    try:
        bpy.app.timers.unregister(register_all_libraries)
    except Exception:
        pass

    # Unregister all submodules with error handling
    try:
        unregister_submodules()
        # print("✓ Submodules unregistered")
    except Exception as e:
        print(f"⚠ Error during submodule unregistration: {e}")
    
    #print("=== BFA Default Library Addon Unregistration Completed ===")
