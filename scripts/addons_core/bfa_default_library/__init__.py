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
from .ui import LIBADDON_APT_preferences


# -----------------------------------------------------------------------------
# CONFIGURATION - Edit these variables for each addon instance
# -----------------------------------------------------------------------------

# This is for built-in core addons, but won't show as an extension.
# Copy this info to the Extension manifest file if packaging as an extension
bl_info = {
    "name": "Default Asset Library",
    "author": "Andres (Draise) Stephens, Ereaser45-Studios, Iyad Ahmed, Juan Carlos Aragon",
    "version": (1, 2, 6),
    "blender": (4, 4, 3),
    "location": "Asset Browser>Default Library",
    "description": "Adds a default library with complementary assets that you can use from the Asset Browser Editor or Asset Shelves",
    "warning": "Expect changes. Use at own risk. Append mode is recommended.",
    "doc_url": "https://github.com/Bforartists/Manual",
    "tracker_url": "https://github.com/Bforartists/Bforartists",
    # Please go to https://github.com/BlenderDefender/implement_addon_updater
    # to implement support for automatic library updates:
    "endpoint_url": "",
    "category": "Import-Export"
}

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

def get_lib_path_index(prefs: Preferences, library_name: str, library_path: str):
    """Get the index of the library name or path for configuring them in the operator."""
    for index, lib in enumerate(prefs.filepaths.asset_libraries):
        if lib.path == library_path or lib.name == library_name:
            return index
    return -1

def find_and_cleanup_libraries(prefs, central_base):
    """
    Find all libraries with our names and clean up duplicates/wrong paths.
    Returns a list of library names that need to be created.
    """
    # Track which library names we need to create
    libraries_to_create = set(CENTRAL_LIB_SUBFOLDERS)
    
    # Track all libraries we find with our names
    found_libraries = []
    
    # First pass: Collect all libraries with our names (including .001, .002 suffixes)
    for i, lib in enumerate(prefs.filepaths.asset_libraries):
        for lib_name in CENTRAL_LIB_SUBFOLDERS:
            # Check if library name matches (including .001, .002 suffixes)
            if lib.name == lib_name or lib.name.startswith(f"{lib_name}."):
                found_libraries.append({
                    'index': i,
                    'original_index': i,  # Store original index for later reference
                    'name': lib.name,
                    'clean_name': lib_name,  # The base name without .001 suffix
                    'path': lib.path,
                    'correct_path': p.join(central_base, lib_name)
                })
                break
    
    # If no libraries found, we need to create all of them
    if not found_libraries:
        return list(libraries_to_create)
    
    # Group libraries by clean name (e.g., group "Default Library" and "Default Library.001")
    libraries_by_name = {}
    for lib in found_libraries:
        clean_name = lib['clean_name']
        if clean_name not in libraries_by_name:
            libraries_by_name[clean_name] = []
        libraries_by_name[clean_name].append(lib)
    
    # For each library name, determine which one(s) to keep and which to remove
    libraries_to_remove = []
    
    for clean_name, lib_list in libraries_by_name.items():
        # Sort libraries: first by if they have the correct path, then by name (prefer no suffix)
        lib_list.sort(key=lambda x: (
            x['path'] != x['correct_path'],  # Wrong path first
            x['name'] != clean_name,  # Suffixed names second
            x['name']  # Alphabetical as tiebreaker
        ))
        
        # Check if any library has the correct path
        correct_library = None
        for lib in lib_list:
            if lib['path'] == lib['correct_path']:
                correct_library = lib
                break
        
        if correct_library:
            # We have at least one library with the correct path
            # Remove all other libraries with this name (including .001, .002 suffixes)
            for lib in lib_list:
                if lib['index'] != correct_library['original_index']:
                    libraries_to_remove.append(lib['index'])
            
            # This library doesn't need to be created
            if clean_name in libraries_to_create:
                libraries_to_create.remove(clean_name)
        else:
            # No library has the correct path
            # Keep the first one (will be updated later) and remove all others
            if lib_list:
                # The first one after sorting will be updated
                library_to_update = lib_list[0]
                # Remove all others (if there are multiple)
                for lib in lib_list[1:]:
                    libraries_to_remove.append(lib['index'])
    
    # Remove duplicate libraries in reverse order to maintain correct indices
    for index in sorted(set(libraries_to_remove), reverse=True):
        try:
            bpy.ops.preferences.asset_library_remove(index=index)
            # print(f"   🗑️ Removed duplicate library at index {index}")
        except Exception as e:
            print(f"   ⚠ Could not remove library at index {index}: {e}")
    
    # Now update any remaining libraries that don't have the correct path
    for i, lib in enumerate(prefs.filepaths.asset_libraries):
        for lib_name in CENTRAL_LIB_SUBFOLDERS:
            if lib.name == lib_name or lib.name.startswith(f"{lib_name}."):
                correct_path = p.join(central_base, lib_name)
                if lib.path != correct_path:
                    # This library needs to be updated
                    try:
                        # Remove and re-add with correct path
                        bpy.ops.preferences.asset_library_remove(index=i)
                        bpy.ops.preferences.asset_library_add(directory=correct_path)
                        
                        # Find the new library and set its name
                        for j, new_lib in enumerate(prefs.filepaths.asset_libraries):
                            if new_lib.path == correct_path:
                                new_lib.name = lib_name
                                new_lib.import_method = 'APPEND'
                                # print(f"   🔄 Updated library {lib_name} from {lib.path} to {correct_path}")
                                break
                        
                        # This library doesn't need to be created
                        if lib_name in libraries_to_create:
                            libraries_to_create.remove(lib_name)
                    except Exception as e:
                        print(f"   ⚠ Could not update library {lib_name}: {e}")
                else:
                    # Library already has correct path
                    if lib_name in libraries_to_create:
                        libraries_to_create.remove(lib_name)
                break
    
    return list(libraries_to_create)

def cleanup_existing_libraries(prefs, central_base):
    """
    Clean up any libraries with our names that don't have the correct path.
    Remove duplicates (.001, .002 suffixes) and update wrong paths.
    Returns list of library names that need to be created.
    """
    return find_and_cleanup_libraries(prefs, central_base)


def register_library(force_reregister=False):
    """Register each library subfolder as a separate library in Blender preferences.
    
    Args:
        force_reregister: If True, will force recreation of libraries even if already tracked
    """
    prefs = bpy.context.preferences

    # Get central library path at runtime (now in user preferences folder)
    central_base = get_central_library_base()

    # Debug output
    # print(f"🔧 Registering Multiple Asset Libraries...")
    # print(f"   Source path: {p.dirname(__file__)}")
    # print(f"   Central base (user prefs): {central_base}")
    # print(f"   Libraries to register: {CENTRAL_LIB_SUBFOLDERS}")

    # Step 1: Check if we're already tracked in the central library
    # This prevents re-copying files every time Bforartists starts
    addon_info = {
        'name': ADDON_DISPLAY_NAME,
        'version': ADDON_VERSION,
        'unique_id': ADDON_UNIQUE_ID
    }
    
    addon_id = utility.get_addon_identifier(addon_info)
    tracking_data = utility.read_addon_tracking(central_base)
    
    already_tracked = addon_id in tracking_data
    
    # Force re-register handling
    if force_reregister and already_tracked:
        print(f"   🔄 Forcing re-registration of tracked addon: {addon_id}")
        # Temporarily remove from tracking to force recreation
        del tracking_data[addon_id]
        utility.save_addon_tracking(central_base, tracking_data)
        already_tracked = False
    
    # Step 2: Smart cleanup - update existing libraries to correct paths
    # and get list of libraries that need to be created
    libraries_to_create = cleanup_existing_libraries(prefs, central_base)

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

    # Step 3: Add this addon to central library and copy assets
    # We always copy assets when registering libraries (even if already tracked)
    # This ensures files are present when user clicks "Re-add Libraries"
    # print(f"   📦 Adding addon to central library and copying assets...")
    utility.add_addon_to_central_library(addon_info, existing_libraries, p.dirname(__file__), central_base)

    # Step 4: Create libraries that don't exist yet
    registered_count = 0
    for lib_name in existing_libraries:
        library_path = p.join(central_base, lib_name)
        
        # Only create libraries that are in the libraries_to_create list
        # (libraries that were updated in cleanup are already done)
        if lib_name in libraries_to_create:
            # Library doesn't exist, create it
            try:
                bpy.ops.preferences.asset_library_add(directory=library_path)

                # Find the newly created library and set its name and import method
                for i, lib in enumerate(prefs.filepaths.asset_libraries):
                    if lib.path == library_path:
                        lib.name = lib_name
                        # Set import method to APPEND (1) instead of default PACKED (0)
                        lib.import_method = 'APPEND'
                        # print(f"   ✅ Created new library: {lib_name} -> {library_path} (Import Method: Append)")
                        registered_count += 1
                        break
            except Exception as e:
                print(f"   ❌ Could not create library {lib_name}: {e}")
        else:
            # Library already exists (was either already correct or was updated in cleanup)
            # Just ensure it has the correct name and import method
            lib_index = -1
            for i, lib in enumerate(prefs.filepaths.asset_libraries):
                if lib.path == library_path:
                    lib_index = i
                    break
            
            if lib_index != -1:
                lib_ref = prefs.filepaths.asset_libraries[lib_index]
                lib_ref.name = lib_name
                lib_ref.import_method = 'APPEND'
                # print(f"   ✓ Library already correctly set up: {lib_name} -> {library_path}")
                registered_count += 1

    # print(f"   ✅ Successfully registered {registered_count} libraries")


def unregister_library():
    """
    Remove individual libraries if no other addons are using them.
    Note: This is called when the addon is being uninstalled/disabled by the user.
    """
    try:
        # Get central library path at runtime
        central_base = get_central_library_base()

        # Use unique addon info for proper tracking
        addon_info = {
            'name': ADDON_DISPLAY_NAME,
            'version': ADDON_VERSION,
            'unique_id': ADDON_UNIQUE_ID
        }

        # Remove this addon from central library tracking with force cleanup
        # This ensures files are cleaned up when addon is disabled/uninstalled
        utility.remove_addon_from_central_library(addon_info, central_base, cleanup_mode='force')

        # Check if no other addons are using the central library
        active_addons = utility.get_active_addons_count(central_base)
        # print(f"Active addons remaining: {active_addons}")

        if active_addons == 0:
            # No other addons using any libraries, so we can clean up
            print("🔄 Cleaning up libraries (addon is being uninstalled)...")
            
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
            
            # Clean up central library files
            try:
                utility.cleanup_central_library(central_base)
                # print("✓ Central library files cleaned up")
            except Exception as e:
                print(f"⚠ Could not cleanup central library files: {e}")
        else:
            # Other addons are still using libraries, keep individual libraries registered
            print(f"✓ {active_addons} addon(s) still using central library, keeping libraries registered for other addons")
            
    except Exception as e:
        print(f"⚠ Error during library unregistration: {e}")
        print("⚠ Library cleanup may be incomplete")


def fully_uninstall_library():
    """
    Forcefully remove all libraries (for manual cleanup if needed).
    This should only be called when the user explicitly wants to remove everything.
    """
    print("🗑️  Addon library cleanup initiated...")
    
    try:
        # Get central library path at runtime
        central_base = get_central_library_base()
        
        # First, remove this addon from tracking with force cleanup
        # This ensures files are cleaned up
        addon_info = {
            'name': ADDON_DISPLAY_NAME,
            'version': ADDON_VERSION,
            'unique_id': ADDON_UNIQUE_ID
        }
        utility.remove_addon_from_central_library(addon_info, central_base, cleanup_mode='force')
        
        # Remove libraries from preferences
        try:
            prefs = bpy.context.preferences
            for lib_name in CENTRAL_LIB_SUBFOLDERS:
                lib_path = p.join(central_base, lib_name)
                lib_index = get_lib_path_index(prefs, lib_name, lib_path)
                if lib_index != -1:
                    try:
                        bpy.ops.preferences.asset_library_remove(index=lib_index)
                        print(f"✓ Removed library from preferences: {lib_name}")
                    except Exception as e:
                        print(f"⚠ Could not remove library {lib_name} from preferences: {e}")
        except Exception as e:
            print(f"⚠ Could not access preferences during forced cleanup: {e}")
        
        # Force cleanup of central library files (in case tracking removal didn't clean everything)
        try:
            utility.cleanup_central_library(central_base)
            print("✓ Central library files cleaned up, no more Library Addons using the central library...")
        except Exception as e:
            print(f"⚠ Could not cleanup central library files: {e}")
        
        print("✅ Addon library cleanup complete")
        
    except Exception as e:
        print(f"⚠ Error during addon library cleanup: {e}")


def register_all_libraries():
    """Register the central asset library and force refresh."""
    # print("🔄 register_all_libraries() called")
    register_library()
    
    # Force refresh the asset browser UI
    try:
        bpy.ops.asset.library_refresh()
        
        # Force redraw of all UI areas
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                area.tag_redraw()
    except Exception as e:
        #print(f"⚠ Could not refresh asset libraries: {e}")
        pass


def unregister_all_libraries():
    """Unregister the central asset library if needed."""
    unregister_library()


# -----------------------------------------------------------------------------
# Library Operators
# -----------------------------------------------------------------------------

class LIBADDON_OT_cleanup_libraries(bpy.types.Operator):
    """Remove all Default Library asset libraries from preferences (manual cleanup)"""
    bl_idname = "preferences.libaddon_cleanup_libraries"
    bl_label = "Remove Libraries"
    bl_description = "Remove all Default Library asset libraries from Blender preferences"
    bl_options = {'REGISTER', 'INTERNAL'}
    
    def execute(self, context):
        # Call the forced cleanup function
        fully_uninstall_library()
        self.report({'INFO'}, "Default Library asset libraries removed from preferences")
        return {'FINISHED'}


class LIBADDON_OT_readd_libraries(bpy.types.Operator):
    """Re-add all Default Library asset libraries to preferences"""
    bl_idname = "preferences.libaddon_readd_libraries"
    bl_label = "Re-add Libraries"
    bl_description = "Re-add all Default Library asset libraries to Blender preferences"
    bl_options = {'REGISTER', 'INTERNAL'}
    
    def execute(self, context):
        # Call the registration function to re-add libraries with force flag
        register_library(force_reregister=True)
        
        # Force refresh of asset browser
        try:
            bpy.ops.asset.library_refresh()
        except:
            pass
        
        self.report({'INFO'}, "Default Library asset libraries re-added to preferences")
        return {'FINISHED'}

# -----------------------------------------------------------------------------
# Main Registration
# -----------------------------------------------------------------------------

classes = (
    LIBADDON_APT_preferences,
    LIBADDON_OT_cleanup_libraries,
    LIBADDON_OT_readd_libraries,
)

# Define all submodules including the new operators and wizards modules
submodule_names = [
    "ui",              # User interface and menus
    "panels",          # Main panels
    "ops",             # Main operations
    "wizards",         # Wizards
]

# Get the register/unregister functions from the factory
register_submodules, unregister_submodules = register_submodule_factory(__name__, submodule_names)


# Flag to track if we've already done a refresh to avoid multiple refreshes
_library_refresh_done = False

def refresh_asset_libraries():
    """
    Refresh asset libraries with multiple fallback approaches for maximum reliability.
    Returns True if any refresh method succeeded or if refresh has already been done.
    """
    global _library_refresh_done
    
    # If we've already successfully refreshed, don't do it again
    if _library_refresh_done:
        return True
    
    refresh_success = False
    
    # Method 1: Try to find an asset browser area and use it for context override
    try:
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'FILE_BROWSER':
                    # Check if this is actually an asset browser
                    for space in area.spaces:
                        if space.type == 'FILE_BROWSER' and hasattr(space, 'browse_mode') and space.browse_mode == 'ASSETS':
                            # Create proper context override with all required elements
                            override = bpy.context.copy()
                            override['window'] = window
                            override['screen'] = window.screen
                            override['area'] = area
                            override['space_data'] = space
                            override['region'] = area.regions[-1]  # Use the main region
                            
                            # Try with the full context override
                            bpy.ops.asset.library_refresh(override)
                            refresh_success = True
                            break
    except Exception:
        pass
    
    # Method 2: Try global operator with no context override
    if not refresh_success:
        try:
            bpy.ops.asset.library_refresh()
            refresh_success = True
        except Exception:
            pass
    
    # Method 3: Alternative approach - force a re-registration of libraries
    if not refresh_success:
        try:
            # Re-register all libraries manually (recreate entries)
            prefs = bpy.context.preferences
            
            # First get existing library paths
            existing_libs = {}
            for lib in prefs.filepaths.asset_libraries:
                existing_libs[lib.path] = lib.name
                
            # Register our libraries again to ensure they exist
            register_library()
            refresh_success = True
        except Exception:
            pass
    
    # Always force UI redraw regardless of refresh success
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            area.tag_redraw()
    
    # Mark that we've done a refresh if successful
    if refresh_success:
        _library_refresh_done = True
    
    return refresh_success

def register_all_libraries_and_refresh():
    """Register libraries and force a refresh of the asset browser."""
    try:
        # First, register all libraries
        register_all_libraries()
        
        # Then try to refresh with our robust method
        refresh_success = refresh_asset_libraries()
        
        if refresh_success:
            # print("✓ Timer-based library registration and refresh complete")
            pass
        else:
            # Schedule one more refresh attempt after a short delay if needed
            # This is the only additional attempt we'll make
            if not _library_refresh_done:
                bpy.app.timers.register(lambda: refresh_asset_libraries(), first_interval=1.0)
        
        return None  # Don't repeat the timer
    except Exception as e:
        print(f"⚠ Timer-based library registration failed: {e}")
        return None  # Don't repeat the timer


def register():
    """Register the complete addon"""
    global _library_refresh_done
    _library_refresh_done = False
    
    # Register main classes with duplicate handling
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except ValueError as e:
            # Operator already registered (by another addon version)
            if "already registered" in str(e):
                # This is expected and OK
                pass
            else:
                print(f"⚠ Error registering {cls.__name__}: {e}")
    
    # Register operators modules
    try:
        from .operators import register as register_operators
        register_operators()
        #print(f"✓ Registered operators")
        
        from .ops import register as register_ops
        register_ops()
        #print(f"✓ Registered ops")
    except Exception as e:
        print(f"⚠ Error registering operators: {e}")
    
    # Register remaining submodules with central registry
    for module_name in submodule_names:
        try:
            # Import the module dynamically
            module = __import__(f"{__name__}.{module_name}", fromlist=["register"])
            
            # Call its register function with the registry ID
            if hasattr(module, "register"):
                module.register()  # Don't pass registry ID, let modules handle registration
                #print(f"✓ Registered module {module_name}")
        except Exception as e:
            print(f"⚠ Error registering module {module_name}: {e}")

    # Simplified library registration to avoid multiple refreshes
    # Use a single timer-based approach with coordinated timing
    
    # Safely check if we're in startup or mid-session
    is_startup = False
    try:
        # Try multiple methods to detect startup vs active session
        if hasattr(bpy.data, 'filepath'):
            is_startup = not bool(bpy.data.filepath)
        else:
            # For Bforartists or if filepath attribute doesn't exist
            # Check if there are any scenes loaded or if we're in initial state
            is_startup = len(bpy.data.scenes) <= 1 and not bpy.context.screen
    except:
        # If any check fails, assume startup for safety
        is_startup = True
    
    if not is_startup:
        # File is loaded, we're in an active session
        try:
            register_all_libraries()
            # print("✓ Immediate library registration (mid-session)")
        except Exception as e:
            print(f"⚠ Immediate registration failed: {e}")
    else:
        # During startup, use a single timer to avoid multiple registrations
        if not bpy.app.timers.is_registered(register_all_libraries_and_refresh):
            bpy.app.timers.register(register_all_libraries_and_refresh, first_interval=0.5)


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
    """Unregister the complete addon - but KEEP libraries AND tracking data!"""
    global _library_refresh_done
    _library_refresh_done = True  # Set to True to prevent any further refreshes during unregister
    
    # Try to remove load_post handler first to prevent any delayed calls
    try:
        if delayed_library_registration in bpy.app.handlers.load_post:
            bpy.app.handlers.load_post.remove(delayed_library_registration)
    except Exception as e:
        print(f"⚠ Could not remove load_post handler: {e}")
    
    # Remove all timers to prevent any future executions
    try:
        if bpy.app.timers.is_registered(register_all_libraries_and_refresh):
            bpy.app.timers.unregister(register_all_libraries_and_refresh)
    except Exception:
        pass
        
    try:
        if bpy.app.timers.is_registered(register_all_libraries):
            bpy.app.timers.unregister(register_all_libraries)
    except Exception:
        pass

    # IMPORTANT: First unregister main classes to prevent double-unregistration
    # Many main classes are also registered by submodules and don't need double handling
    unregistered_count = 0
    for cls in reversed(classes):
        try:
            # Check if the class has bl_rna and if the associated Struct is registered
            if hasattr(cls, 'bl_rna'):
                # Get the actual Struct from the bl_rna
                struct_ptr = getattr(bpy.types, cls.__name__, None)
                if struct_ptr and hasattr(struct_ptr, 'is_registered') and struct_ptr.is_registered:
                    bpy.utils.unregister_class(cls)
                    #print(f"✓ Unregistered class {cls.__name__}")
                    
                    increment_counter()
                else:
                    # Class was never registered or already unregistered
                    # Don't print warning for classes that are expected to be unregistered by submodules
                    if cls.__name__ not in ["LIBADDON_OT_cleanup_libraries", "LIBADDON_OT_readd_libraries", "LIBADDON_APT_preferences"]:
                        print(f"⚠ Class {cls.__name__} was not registered, skipping unregister")
            else:
                # Class doesn't have bl_rna, try to unregister anyway with protection
                try:
                    bpy.utils.unregister_class(cls)
                    #print(f"✓ Unregistered class {cls.__name__}")
                    
                    increment_counter()
                except RuntimeError as e:
                    if "not registered" in str(e):
                        # Don't print warning for classes that are expected to be unregistered by submodules
                        if cls.__name__ not in ["LIBADDON_OT_cleanup_libraries", "LIBADDON_OT_readd_libraries", "LIBADDON_APT_preferences"]:
                            print(f"⚠ Class {cls.__name__} was not registered, skipping unregister")
                    else:
                        raise
        except RuntimeError as e:
            if "not registered" in str(e):
                # Don't print warning for classes that are expected to be unregistered by submodules
                if cls.__name__ not in ["LIBADDON_OT_cleanup_libraries", "LIBADDON_OT_readd_libraries", "LIBADDON_APT_preferences"]:
                    print(f"⚠ Class {cls.__name__} was not registered, skipping unregister")
            else:
                print(f"⚠ RuntimeError unregistering {cls.__name__}: {e}")
        except ValueError as e:
            if "missing bl_rna" in str(e):
                # Don't print warning for classes that are expected to be unregistered by submodules
                if cls.__name__ not in ["LIBADDON_OT_cleanup_libraries", "LIBADDON_OT_readd_libraries", "LIBADDON_APT_preferences"]:
                    print(f"⚠ Class {cls.__name__} has missing bl_rna, skipping unregister")
            else:
                print(f"⚠ ValueError unregistering {cls.__name__}: {e}")
        except Exception as e:
            print(f"⚠ Unexpected error unregistering {cls.__name__}: {e}")

    # IMPORTANT: We DO NOT remove tracking data when Bforartists closes!
    # This allows the addon to remember it was active when Bforartists restarts.
    # 
    # When Bforartists closes, we keep everything as-is:
    # 1. Libraries remain registered in preferences
    # 2. Tracking data remains intact
    # 3. Next time Bforartists starts, the addon knows it was previously active
    
    # Just print status, don't remove anything
    try:
        # Get central library path at runtime
        central_base = get_central_library_base()
        
        # Check how many addons are still tracked
        active_addons = utility.get_active_addons_count(central_base)
        #print(f"📚 Library status: {active_addons} addon(s) tracked in central library")
        #print(f"📚 Addon unregistered - libraries and tracking preserved for next session")
    except Exception as e:
        print(f"⚠ Error checking library status: {e}")
        print("📚 Libraries and tracking preserved for next session")
    
    # Unregister remaining submodules with central registry
    for module_name in reversed(submodule_names):
        try:
            # Import the module dynamically
            module = __import__(f"{__name__}.{module_name}", fromlist=["unregister"])
            
            # Call its unregister function with the registry ID
            if hasattr(module, "unregister"):
                module.unregister()  # Don't pass registry ID
                #print(f"✓ Unregistered module {module_name}")
        except Exception as e:
            print(f"⚠ Error unregistering module {module_name}: {e}")
