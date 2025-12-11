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
import json
import shutil
import glob
from pathlib import Path
from os import path as p


def get_addon_identifier(addon_info):
    """Get a unique identifier for an addon instance."""
    # Use unique_id if provided, otherwise fall back to name+version
    if 'unique_id' in addon_info:
        return addon_info['unique_id']
    return f"{addon_info['name']}_{addon_info['version'][0]}.{addon_info['version'][1]}.{addon_info['version'][2]}"


def get_central_library_path():
    """Get the central library base path - same level as addon folder."""
    try:
        # Get the addon directory (where this utility.py file is located)
        addon_dir = p.dirname(__file__)
        # Get the parent directory of the addon (where addon folder resides)
        parent_dir = p.dirname(addon_dir)
        # Create central library in the same parent directory
        return p.join(parent_dir, "bfa_central_asset_library")
    except:
        # Fallback to user's documents folder if above fails
        return p.join(p.expanduser("~"), "BFA_Central_Asset_Library")


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
    
    print(f"   📦 Adding {addon_info['name']} to central library...")
    print(f"      Addon path: {addon_path}")
    print(f"      Central path: {central_lib_base}")
    print(f"      Library folders: {library_folders}")
    
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
            print(f"      ⚠ Source directory missing: {source_dir}")
            continue

        print(f"      Copying from: {source_dir}")
        print(f"      Copying to: {target_dir}")

        os.makedirs(target_dir, exist_ok=True)

        # Copy all blend files and catalog files
        for pattern in ['*.blend', '*.blend?', 'blender_assets.cats.txt']:
            src_files = glob.glob(p.join(source_dir, pattern))
            print(f"      Found {len(src_files)} files matching {pattern}")

            for src_file in src_files:
                filename = p.basename(src_file)
                dest_file = p.join(target_dir, filename)
                relative_dest_path = p.relpath(dest_file, central_lib_base)

                # Only copy if source is newer or destination doesn't exist
                if not p.exists(dest_file) or p.getmtime(src_file) > p.getmtime(dest_file):
                    shutil.copy2(src_file, dest_file)
                    print(f"      ✅ Copied {filename} to central library")
                    files_copied += 1
                    files_copied_by_addon.append(relative_dest_path)
                else:
                    print(f"      ⏩ Skipped {filename} (already up to date)")
                    # Still track the file if it already exists and we would have copied it
                    if p.exists(dest_file):
                        files_copied_by_addon.append(relative_dest_path)
    
    print(f"      Total files copied: {files_copied}")
    print(f"      Files tracked for this addon: {len(files_copied_by_addon)}")
    
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
        print(f"      ✅ Added to tracking: {addon_id}")
    else:
        # Update existing entry with current file list
        tracking_data[addon_id]['files'] = files_copied_by_addon
        tracking_data[addon_id]['libraries'] = library_folders.copy()
        write_addon_tracking(central_lib_base, tracking_data)
        print(f"      ⏩ Updated tracking: {addon_id}")
    
    return central_lib_base


def remove_addon_from_central_library(addon_info, central_lib_base=None):
    """Remove an addon's tracking entry and clean up its files if not used by others."""
    if central_lib_base is None:
        central_lib_base = get_central_library_path()
    tracking_data = read_addon_tracking(central_lib_base)
    addon_id = get_addon_identifier(addon_info)

    if addon_id in tracking_data:
        # Get the files that this addon is responsible for
        addon_files = tracking_data[addon_id].get('files', [])
        print(f"   📤 Removing addon {addon_id} with {len(addon_files)} tracked files")
        
        # Remove the addon from tracking
        del tracking_data[addon_id]
        write_addon_tracking(central_lib_base, tracking_data)
        
        # Remove files that only this addon was using
        if addon_files:
            removed_files = remove_orphaned_files(central_lib_base, tracking_data, addon_files)
            print(f"   🗑️ Removed {removed_files} orphaned files")
        
        # Clean up if library is empty
        cleanup_central_library(central_lib_base, tracking_data)


def cleanup_central_library(central_lib_base, tracking_data=None):
    """Clean up the central library if no addons are using it."""
    if tracking_data is None:
        tracking_data = read_addon_tracking(central_lib_base)

    if len(tracking_data) == 0:
        try:
            if p.exists(central_lib_base):
                # Force delete entire central library directory and all contents
                shutil.rmtree(central_lib_base)
                print(f"🗑️ Force removed central library: {central_lib_base}")
        except OSError as e:
            print(f"⚠ Warning: Could not cleanup central library: {e}")


def get_active_addons_count(central_lib_base=None):
    """Get the number of addons currently registered in the central library."""
    if central_lib_base is None:
        central_lib_base = get_central_library_path()
    tracking_data = read_addon_tracking(central_lib_base)
    return len(tracking_data)


def is_central_library_registered(prefs, central_lib_base=None):
    """Check if the central library is already registered."""
    if central_lib_base is None:
        central_lib_base = get_central_library_path()

    for lib in prefs.filepaths.asset_libraries:
        if lib.path == central_lib_base:
            return True
    return False


def get_central_library_index(prefs, central_lib_base=None):
    """Get the index of the central library in preferences."""
    if central_lib_base is None:
        central_lib_base = get_central_library_path()
    
    for index, lib in enumerate(prefs.filepaths.asset_libraries):
        if lib.path == central_lib_base:
            return index
    return -1


def remove_orphaned_files(central_lib_base, tracking_data, files_to_check):
    """Remove files that are not used by any other addons, but keep catalog files."""
    removed_count = 0
    
    # Get all files that are still used by other addons
    all_used_files = set()
    for addon_id, addon_data in tracking_data.items():
        all_used_files.update(addon_data.get('files', []))

    # Remove files that are no longer used by any addon (except catalog files)
    for file_path in files_to_check:
        full_file_path = p.join(central_lib_base, file_path)
        
        # Skip catalog files - keep them until the entire central library is removed
        if file_path.endswith('blender_assets.cats.txt'):
            print(f"      💾 Keeping catalog file: {file_path}")
            continue
            
        if file_path not in all_used_files and p.exists(full_file_path):
            try:
                os.remove(full_file_path)
                removed_count += 1
                print(f"      🗑️ Removed orphaned file: {file_path}")

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
                                print(f"      🗑️ Removed catalog file from empty directory: {catalog_file}")

                            os.rmdir(parent_dir)
                            print(f"      🗂️ Removed empty directory: {p.relpath(parent_dir, central_lib_base)}")
                            parent_dir = p.dirname(parent_dir)
                        else:
                            break
                    except OSError:
                        break

            except OSError as e:
                print(f"      ⚠ Could not remove file {file_path}: {e}")
    
    return removed_count


# Dummy register/unregister functions to prevent errors if accidentally called as submodule
def register():
    """Dummy register function - utility is not a Blender submodule."""
    pass

def unregister():
    """Dummy unregister function - utility is not a Blender submodule."""
    pass
