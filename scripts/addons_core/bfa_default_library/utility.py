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

"""
Utility functions for Default Library management.
Provides tools for maintaining the central library system.
"""

import bpy
import os
import sys
import json
import shutil
import glob
import time
from pathlib import Path
from os import path as p


def get_addon_identifier(addon_info):
    """Get a unique identifier for an addon instance."""
    # Use unique_id if provided, otherwise fall back to name+version
    if 'unique_id' in addon_info:
        return addon_info['unique_id']
    return f"{addon_info['name']}_{addon_info['version'][0]}.{addon_info['version'][1]}.{addon_info['version'][2]}"

def _get_user_resource_path():
    """
    Internal: Get the base user resource path for Bforartists.
    This is the single source of truth for path resolution.

    Returns the version-specific user folder (e.g., .../Bforartists/5.1/).
    """
    try:
        # Get the user resource path (already includes the version)
        return str(Path(bpy.utils.resource_path("USER")))
    except Exception as e:
        print(f"⚠ Could not get user resource path: {e}")

        # Fallback: construct the path manually based on platform
        try:
            version_str = f"{bpy.app.version[0]}.{bpy.app.version[1]}"

            if sys.platform == "win32":
                # Windows: %APPDATA%\Bforartists\Bforartists\{version}
                appdata = os.getenv('APPDATA')
                if appdata:
                    return str(Path(appdata) / "Bforartists" / "Bforartists" / version_str)
            elif sys.platform == "darwin":
                # macOS: ~/Library/Application Support/Bforartists/Bforartists/{version}
                return str(Path.home() / "Library" / "Application Support" / "Bforartists" / "Bforartists" / version_str)
            else:
                # Linux and others: ~/.config/bforartists/{version}
                return str(Path.home() / ".config" / "bforartists" / version_str)
        except Exception as e2:
            print(f"⚠ Could not construct user preferences path: {e2}")
            raise e


def get_user_preferences_path():
    """Get the main user preferences path for addon files."""
    try:
        return _get_user_resource_path()
    except Exception:
        # Default to current directory if everything fails
        return os.getcwd()


def get_bforartists_user_preferences_folder():
    """Get the Bforartists user preferences folder for asset libraries."""
    user_path = _get_user_resource_path()
    return os.path.join(user_path, "asset_libraries")


def get_bfa_extensions_path():
    """Get the Bforartists extensions path where addons should be installed."""
    user_prefs_path = get_user_preferences_path()
    extensions_path = os.path.join(user_prefs_path, "extensions", "user_default")
    # Ensure the directory exists
    os.makedirs(extensions_path, exist_ok=True)
    return extensions_path


def get_child_addon_path(child_addon_name="modular_child_addons"):
    """Get the path where child addons should be stored in Bforartists extensions."""
    extensions_path = get_bfa_extensions_path()
    child_addon_path = os.path.join(extensions_path, child_addon_name)
    return child_addon_path


def get_central_library_path():
    """Get the central library base path - use Bforartists user preferences folder."""
    user_prefs_dir = get_bforartists_user_preferences_folder()
    
    # Create the directory if it doesn't exist
    os.makedirs(user_prefs_dir, exist_ok=True)
    
    return user_prefs_dir


def read_addon_tracking(central_lib_base):
    """Read the addon tracking data from the JSON file."""
    tracking_file = p.join(central_lib_base, ".addon_tracking.json")

    if not p.exists(tracking_file):
        return {}

    try:
        with open(tracking_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def write_addon_tracking(central_lib_base, tracking_data):
    """Write the addon tracking data to the JSON file."""
    tracking_file = p.join(central_lib_base, ".addon_tracking.json")
    os.makedirs(central_lib_base, exist_ok=True)
    try:
        with open(tracking_file, 'w') as f:
            json.dump(tracking_data, f, indent=2)
    except IOError:
        print(f"Warning: Could not write addon tracking file: {tracking_file}")


def add_addon_to_central_library(addon_info, library_folders, addon_path, central_lib_base=None):
    """Add an addon's assets to the central library and update tracking."""
    if central_lib_base is None:
        central_lib_base = get_central_library_path()

    # print(f"   📦 Adding {addon_info['name']} to central library...")
    # print(f"      Addon path: {addon_path}")
    # print(f"      Central path: {central_lib_base}")
    # print(f"      Library folders: {library_folders}")

    # Read current tracking
    tracking_data = read_addon_tracking(central_lib_base)
    addon_id = get_addon_identifier(addon_info)

    # Track files copied by this addon
    files_copied_by_addon = []

    # Copy assets
    files_copied = 0
    for subfolder in library_folders:
        source_dir = p.join(addon_path, subfolder)
        target_dir = p.join(central_lib_base, subfolder)

        if not p.exists(source_dir):
            # print(f"      ⚠ Source directory missing: {source_dir}")
            continue

        # print(f"      Copying from: {source_dir}")
        # print(f"      Copying to: {target_dir}")

        os.makedirs(target_dir, exist_ok=True)

        # Copy all blend files and catalog files
        for pattern in ['*.blend', '*.blend?', 'blender_assets.cats.txt']:
            src_files = glob.glob(p.join(source_dir, pattern))
            # print(f"      Found {len(src_files)} files matching {pattern}")

            for src_file in src_files:
                filename = p.basename(src_file)
                dest_file = p.join(target_dir, filename)
                relative_dest_path = p.relpath(dest_file, central_lib_base)

                # Only copy if source is newer or destination doesn't exist
                if not p.exists(dest_file) or p.getmtime(src_file) > p.getmtime(dest_file):
                    shutil.copy2(src_file, dest_file)
                    # print(f"      ✅ Copied {filename} to central library")
                    files_copied += 1
                    files_copied_by_addon.append(relative_dest_path)
                else:
                    # print(f"      ⏩ Skipped {filename} (already up to date)")
                    # Still track the file if it already exists and we would have copied it
                    if p.exists(dest_file):
                        files_copied_by_addon.append(relative_dest_path)

    # print(f"      Total files copied: {files_copied}")
    # print(f"      Files tracked for this addon: {len(files_copied_by_addon)}")

    # Update tracking
    if addon_id not in tracking_data:
        tracking_data[addon_id] = {
            'name': addon_info['name'],
            'version': list(addon_info['version']),
            'path': addon_path,
            'libraries': library_folders.copy(),
            'files': files_copied_by_addon  # Track which files this addon is responsible for
        }
        write_addon_tracking(central_lib_base, tracking_data)
        # print(f"      ✅ Added to tracking: {addon_id}")
    else:
        # Update existing entry with current file list
        tracking_data[addon_id]['files'] = files_copied_by_addon
        tracking_data[addon_id]['libraries'] = library_folders.copy()
        write_addon_tracking(central_lib_base, tracking_data)
        # print(f"      ⏩ Updated tracking: {addon_id}")

    return central_lib_base


def update_addon_in_central_library(parent_addon_info, libraries, central_base, source_dir):
    """Update existing addon entry in central library tracking without changing activation status"""
    addon_id = get_addon_identifier(parent_addon_info)
    tracking_data = read_addon_tracking(central_base)
    
    if addon_id in tracking_data:
        # Update existing entry
        tracking_data[addon_id]["libraries"] = libraries
        tracking_data[addon_id]["version"] = parent_addon_info['version']
        tracking_data[addon_id]["timestamp"] = time.time()
        write_addon_tracking(central_base, tracking_data)
        return True
    return False


def remove_addon_from_central_library(addon_info, central_lib_base=None, cleanup_mode='normal'):
    """
    Remove an addon's tracking entry and clean up its files if not used by others.
    
    Args:
        addon_info: Dictionary with addon identification info
        central_lib_base: Path to central library (optional)
        cleanup_mode: 'normal' = standard cleanup, 'force' = force cleanup even if other addons exist
    """
    if central_lib_base is None:
        central_lib_base = get_central_library_path()
    tracking_data = read_addon_tracking(central_lib_base)
    addon_id = get_addon_identifier(addon_info)

    if addon_id in tracking_data:
        # Get the files that this addon is responsible for
        addon_files = tracking_data[addon_id].get('files', [])
        # print(f"   📤 Removing addon {addon_id} with {len(addon_files)} tracked files")

        # Remove the addon from tracking
        del tracking_data[addon_id]
        write_addon_tracking(central_lib_base, tracking_data)

        # Remove files that only this addon was using
        if addon_files:
            removed_files = remove_orphaned_files(central_lib_base, tracking_data, addon_files)
            # print(f"   🗑️ Removed {removed_files} orphaned files")

        # Clean up if library is empty or we're in force mode
        if cleanup_mode == 'force' or len(tracking_data) == 0:
            cleanup_central_library(central_lib_base, tracking_data)


def cleanup_central_library(central_lib_base, tracking_data=None):
    """
    Clean up the central library if no addons are using it.
    Also cleans up individual library folders that are empty.
    """
    if tracking_data is None:
        tracking_data = read_addon_tracking(central_lib_base)

    # If no addons are using the central library at all, remove everything
    if len(tracking_data) == 0:
        try:
            if p.exists(central_lib_base):
                # Force delete entire central library directory and all contents
                shutil.rmtree(central_lib_base)
                # print(f"🗑️ Force removed central library: {central_lib_base}")
        except OSError as e:
            print(f"⚠ Warning: Could not cleanup central library: {e}")
    else:
        # Some addons are still using the library, but we should clean up
        # individual library folders that might be empty
        try:
            if p.exists(central_lib_base):
                # Check each library folder
                for item in os.listdir(central_lib_base):
                    item_path = p.join(central_lib_base, item)
                    if p.isdir(item_path):
                        # Check if directory is empty (or only contains catalog files)
                        dir_contents = os.listdir(item_path)
                        has_content = False
                        
                        for content in dir_contents:
                            content_path = p.join(item_path, content)
                            # Check if it's a file (not a catalog file) or a non-empty directory
                            if p.isfile(content_path):
                                if not content.endswith('blender_assets.cats.txt'):
                                    has_content = True
                                    break
                            elif p.isdir(content_path):
                                # Check if subdirectory has content
                                sub_contents = os.listdir(content_path)
                                if any(not sc.endswith('blender_assets.cats.txt') for sc in sub_contents):
                                    has_content = True
                                    break
                        
                        # If directory has no content, remove it
                        if not has_content:
                            try:
                                # Remove any catalog files first
                                for catalog_file in [f for f in dir_contents if f.endswith('blender_assets.cats.txt')]:
                                    catalog_path = p.join(item_path, catalog_file)
                                    os.remove(catalog_path)
                                
                                # Remove the directory
                                shutil.rmtree(item_path)
                                # print(f"🗑️ Removed empty library folder: {item}")
                            except OSError as e:
                                print(f"⚠ Could not remove empty library folder {item}: {e}")
        except OSError as e:
            print(f"⚠ Warning: Could not cleanup individual library folders: {e}")


def get_active_addons_count(central_lib_base=None):
    """Get the number of addons currently registered in the central library."""
    if central_lib_base is None:
        central_lib_base = get_central_library_path()
    tracking_data = read_addon_tracking(central_lib_base)
    return len(tracking_data)


def remove_orphaned_files(central_lib_base, tracking_data, files_to_check):
    """
    Remove files that are not used by any other addons, but keep catalog files.
    This function is careful to only remove files that are truly orphaned.
    """
    removed_count = 0

    # Build a map of which files are used by which addons
    file_usage_map = {}
    for addon_id, addon_data in tracking_data.items():
        for file_path in addon_data.get('files', []):
            if file_path not in file_usage_map:
                file_usage_map[file_path] = []
            file_usage_map[file_path].append(addon_id)

    # Remove files that are no longer used by any addon (except catalog files)
    for file_path in files_to_check:
        full_file_path = p.join(central_lib_base, file_path)

        # Skip catalog files - keep them until the entire central library is removed
        if file_path.endswith('blender_assets.cats.txt'):
            # print(f"      💾 Keeping catalog file: {file_path}")
            continue

        # Check if this file is used by any remaining addons
        is_used_by_other_addons = file_path in file_usage_map and len(file_usage_map[file_path]) > 0
        
        if not is_used_by_other_addons and p.exists(full_file_path):
            try:
                os.remove(full_file_path)
                removed_count += 1
                # print(f"      🗑️ Removed orphaned file: {file_path}")

                # Also remove empty parent directories (if they don't contain catalog files)
                parent_dir = p.dirname(full_file_path)
                while parent_dir != central_lib_base and p.exists(parent_dir):
                    try:
                        # Check if directory is empty (ignoring catalog files)
                        dir_contents = os.listdir(parent_dir)
                        # Only remove if directory is truly empty or only contains catalog files
                        has_other_files = any(f for f in dir_contents if not f.endswith('blender_assets.cats.txt'))

                        if not has_other_files:
                            # Remove all catalog files first
                            for catalog_file in [f for f in dir_contents if f.endswith('blender_assets.cats.txt')]:
                                catalog_path = p.join(parent_dir, catalog_file)
                                os.remove(catalog_path)
                                # print(f"      🗑️ Removed catalog file from empty directory: {catalog_file}")

                            os.rmdir(parent_dir)
                            # print(f"      🗂️ Removed empty directory: {p.relpath(parent_dir, central_lib_base)}")
                            parent_dir = p.dirname(parent_dir)
                        else:
                            break
                    except OSError:
                        break

            except OSError as e:
                print(f"      ⚠ Could not remove file {file_path}: {e}")

    return removed_count


def get_child_addon_status(child_addon_name="modular_child_addons"):
    """
    Get the installation and activation status of a child addon.
    
    Returns:
        tuple: (is_installed, is_active, addon_path)
    """
    import bpy
    
    # Get the Bforartists extensions path
    child_addon_dir = get_child_addon_path(child_addon_name)
    child_init_file = os.path.join(child_addon_dir, "__init__.py")
    
    # Check if installed
    is_installed = os.path.exists(child_init_file)
    
    # Check if active - try multiple possible module names
    is_active = False
    # Try the exact name first
    if child_addon_name in bpy.context.preferences.addons:
        is_active = True
    else:
        # Also check for the module name without any path components
        module_name = child_addon_name
        if module_name in bpy.context.preferences.addons:
            is_active = True
    
    return is_installed, is_active, child_addon_dir


# Dummy register/unregister functions to prevent errors if accidentally called as submodule
def register():
    """Dummy register function - utility is not a Blender submodule."""
    pass


def unregister():
    """Dummy unregister function - utility is not a Blender submodule."""
    pass
