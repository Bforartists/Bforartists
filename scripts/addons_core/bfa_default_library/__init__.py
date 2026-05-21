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
# Modular Asset Library Addon - Parent Container
# -----------------------------------------------------------------------------

import bpy
import os
import shutil
import sys
import json
from pathlib import Path

from bpy.types import Preferences
from os import path as p

# Import utility functions
from . import utility

# Import UI module (preferences panel) - imported after functions are defined
# to avoid circular imports. See register() function.

# -----------------------------------------------------------------------------
# CONFIGURATION - Edit these variables for each modular addon instance
# -----------------------------------------------------------------------------

# Parent addon info - this is the container/library manager
bl_info = {
    "name": "Default Asset Library",
    "author": "Andres (Draise) Stephens, Ereaser45-Studios, Iyad Ahmed, Juan Carlos Aragon",
    "version": (1, 3, 3),
    "blender": (5, 0, 1),
    "location": "Asset Browser>Default Library",
    "description": "Adds a modular default asset library and addon with wizards and complementary operators",
    "warning": "Expect changes. Use at own risk. Append mode is recommended.",
    "doc_url": "https://github.com/Bforartists/Manual",
    "tracker_url": "https://github.com/Bforartists/Bforartists",
    "endpoint_url": "",
    "category": "Import-Export"
}

# Addon identification - MUST BE UNIQUE for each compiled parent addon
# TO DO: Update the version in the bl_info above as well for consistency
PARENT_ADDON_UNIQUE_ID = "default_asset_library"
PARENT_ADDON_DISPLAY_NAME = "Default Asset Library"
PARENT_ADDON_VERSION = (1, 3, 3)

# Child addon info - this is the functional addon
# The UNIQUE_ID is VERSION-INDEPENDENT (no version baked in) so it stays stable
CHILD_ADDON_UNIQUE_ID = "default_asset_library_functions"
CHILD_ADDON_DISPLAY_NAME = "Default Asset Library Functions"

# SINGLE SOURCE OF TRUTH: Read version from the bundled child_addon manifest.
# CHILD_ADDON_VERSION is set dynamically by _read_bundled_child_version() below.
# Fallback if the manifest cannot be read (should never happen in a packaged addon).
CHILD_ADDON_VERSION = (1, 0, 0)

# -----------------------------------------------------------------------------
# Version Comparison Utilities
# -----------------------------------------------------------------------------

def parse_version_string(version_str):
    """
    Parse a version string into a tuple of integers.
    
    Args:
        version_str: Version string like "1.0.2" or "1.2"
    
    Returns:
        Tuple of integers, e.g., (1, 0, 2) or (1, 2, 0)
    """
    try:
        # Split by dots and convert to integers
        parts = version_str.strip().split('.')
        version_tuple = tuple(int(part) for part in parts)
        
        # Ensure we have at least 3 parts (major, minor, patch)
        while len(version_tuple) < 3:
            version_tuple = version_tuple + (0,)
            
        return version_tuple
    except (ValueError, AttributeError):
        # If parsing fails, return (0, 0, 0)
        return (0, 0, 0)


def compare_versions(version_a, version_b):
    """
    Compare two version tuples.
    
    Args:
        version_a: First version tuple (e.g., (1, 0, 1))
        version_b: Second version tuple (e.g., (1, 0, 2))
    
    Returns:
        -1 if version_a < version_b
         0 if version_a == version_b
         1 if version_a > version_b
    """
    # Compare major, minor, patch in order
    for a, b in zip(version_a, version_b):
        if a < b:
            return -1
        elif a > b:
            return 1
    return 0


def is_version_newer(installed_version, parent_version):
    """
    Check if the installed version is newer than the parent version.
    
    Args:
        installed_version: Version tuple of installed child addon
        parent_version: Version tuple from parent addon
    
    Returns:
        True if installed_version is newer than parent_version
    """
    return compare_versions(installed_version, parent_version) > 0


def is_version_older(installed_version, parent_version):
    """
    Check if the installed version is older than the parent version.
    
    Args:
        installed_version: Version tuple of installed child addon
        parent_version: Version tuple from parent addon
    
    Returns:
        True if installed_version is older than parent_version
    """
    return compare_versions(installed_version, parent_version) < 0


def get_installed_child_addon_version():
    """
    Get the version of the installed child addon from its manifest file.
    
    Returns:
        Version tuple if found, None if not installed or manifest not found
    """
    child_addon_dir = get_child_addon_path()
    manifest_file = p.join(child_addon_dir, "blender_manifest.toml")
    
    if not p.exists(manifest_file):
        return None
    
    try:
        # Simple TOML parsing for version string
        with open(manifest_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Look for version line in the manifest
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('version ='):
                # Extract version string, handling quotes
                version_str = line.split('=', 1)[1].strip().strip('"\'')
                return parse_version_string(version_str)
    except Exception as e:
        print(f"⚠ Error reading child addon manifest: {e}")
        
    return None


def _read_bundled_child_version():
    """Read the child addon version from the BUNDLED manifest (the one we ship).

    This is the single source of truth.  The installed copy's manifest may
    be stale, so we ALWAYS consult the version that came with *this* parent.

    Returns a tuple like (1, 0, 5) or None on failure.
    """
    parent_dir = p.dirname(__file__)
    bundled_manifest = p.join(parent_dir, "child_addon", "blender_manifest.toml")
    if not p.exists(bundled_manifest):
        return None
    try:
        with open(bundled_manifest, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith("version ="):
                    version_str = stripped.split("=", 1)[1].strip().strip("\"'")
                    return parse_version_string(version_str)
    except Exception:
        pass
    return None


# -----------------------------------------------------------------------------
# Blender Version Detection and Compatibility
# -----------------------------------------------------------------------------

def get_blender_version_info():
    """
    Get comprehensive Blender version information with human-readable labels.
    
    Returns:
        dict: Version information including:
            - version_tuple: (major, minor, patch) tuple
            - version_string: "X.Y.Z" format
            - version_category: Human-readable category name
            - compatibility_level: Internal compatibility level
            - features: Dict of supported features
    """
    try:
        version = bpy.app.version
        version_tuple = (version[0], version[1], version[2] if len(version) > 2 else 0)
        version_string = f"{version[0]}.{version[1]}.{version[2] if len(version) > 2 else 0}"
        
        # Determine version category and compatibility level
        if version_tuple >= (5, 2, 0):
            category = "Blender 5.2+ Modern"
            compatibility_level = "modern"
            features = {
                "asset_library_type_param": True,
                "geometry_nodes_interface_panels": True,
                "modifier_property_access": "interface_based",
                "remote_asset_libraries": True
            }
        elif version_tuple >= (5, 1, 0):
            category = "Blender 5.1+ Enhanced"
            compatibility_level = "enhanced"
            features = {
                "asset_library_type_param": False,  # 5.1.x operator doesn't actually accept 'type' parameter
                "geometry_nodes_interface_panels": True,
                "modifier_property_access": "interface_based",
                "remote_asset_libraries": False
            }
        elif version_tuple >= (5, 0, 0):
            category = "Blender 5.0 Legacy"
            compatibility_level = "legacy"
            features = {
                "asset_library_type_param": False,
                "geometry_nodes_interface_panels": False,
                "modifier_property_access": "direct_access",
                "remote_asset_libraries": False
            }
        else:
            category = "Blender 4.x or Earlier (Unsupported)"
            compatibility_level = "unsupported"
            features = {
                "asset_library_type_param": False,
                "geometry_nodes_interface_panels": False,
                "modifier_property_access": "unknown",
                "remote_asset_libraries": False
            }
        
        return {
            "version_tuple": version_tuple,
            "version_string": version_string,
            "version_category": category,
            "compatibility_level": compatibility_level,
            "features": features
        }
    except Exception as e:
        # Fallback if version detection fails
        return {
            "version_tuple": (0, 0, 0),
            "version_string": "Unknown",
            "version_category": "Unknown Version",
            "compatibility_level": "unknown",
            "features": {
                "asset_library_type_param": False,
                "geometry_nodes_interface_panels": False,
                "modifier_property_access": "unknown",
                "remote_asset_libraries": False
            },
            "error": str(e)
        }


def is_blender_version_supported():
    """
    Check if the current Blender version is supported by this addon.
    
    Returns:
        tuple: (is_supported: bool, reason: str)
    """
    version_info = get_blender_version_info()
    
    if version_info["compatibility_level"] == "unsupported":
        return False, f"Unsupported Blender version: {version_info['version_string']}. This addon requires Blender 5.0 or later."
    
    return True, f"Supported: {version_info['version_category']} ({version_info['version_string']})"


def get_version_compatibility_warnings():
    """
    Get list of compatibility warnings for the current Blender version.
    
    Returns:
        list: List of warning strings, empty if no warnings
    """
    version_info = get_blender_version_info()
    warnings = []
    
    if version_info["compatibility_level"] == "legacy":
        warnings.append("Running on Blender 5.0 - some advanced features may not work correctly")
    
    if not version_info["features"]["asset_library_type_param"]:
        warnings.append("Asset library registration may require manual configuration")
    
    if version_info["features"]["modifier_property_access"] == "unknown":
        warnings.append("Modifier property access patterns may be unreliable")
    
    return warnings


def get_addon_module_name():
    """Return the addon module name used in Blender preferences."""
    return p.basename(p.dirname(__file__))


def is_debug_asset_library_registration_enabled():
    """Return whether the addon preferences debug toggle is enabled."""
    try:
        addon = bpy.context.preferences.addons.get(get_addon_module_name())
        if addon and hasattr(addon, "preferences"):
            return getattr(addon.preferences, "debug_asset_registration", False)
    except Exception:
        pass
    return False


def debug_log(message: str):
    """Print debug messages only when the debug preference is enabled."""
    if is_debug_asset_library_registration_enabled():
        print(message)


def log_version_info():
    """Log comprehensive version information for debugging."""
    version_info = get_blender_version_info()
    
    # DEBUG: Print detailed version info for troubleshooting
    #print("=== Blender Version Detection ===")
    #print(f"Version: {version_info['version_string']}")
    #print(f"Category: {version_info['version_category']}")
    #print(f"Compatibility Level: {version_info['compatibility_level']}")
    #print(f"Features: {version_info['features']}")
    
    supported, reason = is_blender_version_supported()
    #print(f"Supported: {supported} - {reason}")
    
    warnings = get_version_compatibility_warnings()
    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"  ⚠ {warning}")
    else:
        #print("No compatibility warnings")
        pass
    #print("==================================")


# Library configuration - Only include libraries that exist in your packaged addon
CENTRAL_LIB_SUBFOLDERS = [
    "Default Library",
    "Geometry Nodes Library",
    "Shader Nodes Library",
    "Compositor Nodes Library"]  # Only include libraries that exist

# Child addon submodules to manage (single source of truth)
# Note: "operators" is a package with its own submodules, handled separately in loadingollama run qwen2.5-coder
CHILD_ADDON_SUBMODULES = [
    "panels",
    "wizards",
    "wizard_handlers",
    "wizard_operators",
    "ops",
    "ui",
]

# All child addon modules including the operators package (for cleanup/detection)
CHILD_ADDON_ALL_MODULES = ["operators"] + CHILD_ADDON_SUBMODULES

# -----------------------------------------------------------------------------

# Central library base path will be determined at runtime
def get_central_library_base():
    """Get the central library path at runtime."""
    path = utility.get_central_library_path()
    return path


def get_child_addon_path():
    """Get the path where child addons should be stored in Bforartists extensions."""
    # Use the utility function that now correctly points to extensions/user_default
    return utility.get_child_addon_path("modular_child_addons")


def ensure_child_addon_directory():
    """Ensure the child addon directory exists."""
    child_addon_dir = get_child_addon_path()
    os.makedirs(child_addon_dir, exist_ok=True)
    return child_addon_dir


def copy_child_addon_to_user_prefs():
    """Copy the child addon files to user preferences directory."""
    parent_addon_dir = p.dirname(__file__)
    child_addon_src = p.join(parent_addon_dir, "child_addon")
    child_addon_dst = get_child_addon_path()

    if not p.exists(child_addon_src):
        #print(f"⚠ Child addon source directory not found: {child_addon_src}")
        return False

    try:
        # First, remove destination directory if it exists (for clean reinstall)
        if p.exists(child_addon_dst):
            #print(f"🔄 Removing existing child addon directory: {child_addon_dst}")
            shutil.rmtree(child_addon_dst)

        # Create destination directory
        os.makedirs(child_addon_dst, exist_ok=True)

        # Copy all files from child_addon directory (not just Python files)
        for root, dirs, files in os.walk(child_addon_src):
            # Get relative path for destination
            rel_path = os.path.relpath(root, child_addon_src)
            dest_dir = os.path.join(child_addon_dst, rel_path)

            # Create destination directory
            os.makedirs(dest_dir, exist_ok=True)

            # Copy all files (only Python files)
            for file in files:
                if file.endswith('.py'):
                    src_file = os.path.join(root, file)
                    dest_file = os.path.join(dest_dir, file)
                    shutil.copy2(src_file, dest_file)
                    #print(f"  ✓ Copied Python: {file}")
                elif file.endswith('.toml'):
                    # Copy manifest files to avoid empty manifest warnings
                    src_file = os.path.join(root, file)
                    dest_file = os.path.join(dest_dir, file)
                    shutil.copy2(src_file, dest_file)
                    #print(f"  ✓ Copied manifest: {file}")
                else:
                    # Copy other files (if any)
                    src_file = os.path.join(root, file)
                    dest_file = os.path.join(dest_dir, file)
                    shutil.copy2(src_file, dest_file)
                    #print(f"  ✓ Copied: {file}")

        #print(f"✅ Child addon copied to: {child_addon_dst}")

        # Verify the copy worked - check for Python files and manifest
        init_file = p.join(child_addon_dst, "__init__.py")
        manifest_file = p.join(child_addon_dst, "blender_manifest.toml")

        if p.exists(init_file):
            # Double-check that manifest file was copied
            if not p.exists(manifest_file):
                # Try to copy from source again
                source_manifest = p.join(child_addon_src, "blender_manifest.toml")
                if p.exists(source_manifest):
                    shutil.copy2(source_manifest, manifest_file)
                    #print(f"✓ Re-copied manifest from source: {source_manifest}")
                else:
                    # Create a minimal blender_manifest.toml if missing
                    with open(manifest_file, 'w') as f:
                        f.write('''[build-system]
                                requires = ["setuptools"]
                                build-backend = "setuptools.build_meta"

                                [project]
                                name = "default_asset_library_functions"
                                version = "1.0.1"
                                ''')
                    #print(f"✓ Created minimal blender_manifest.toml")
            #print(f"✅ Verification: __init__.py present")
            return True
        else:
            #print(f"❌ Verification failed: __init__.py missing")
            return False

    except Exception as e:
        print(f"⚠ Error copying child addon: {e}")
        # Debug:
        #import traceback  
        #traceback.print_exc()
        return False


def activate_child_addon():
    """
    "Activate" the child addon by loading its functionality directly.
    This doesn't actually activate it as a separate addon in preferences.
    """
    #print("🔄 Loading child addon functionality...")

    # Ensure child addon is installed first
    if not ensure_child_addon_installed():
        #print("❌ Failed to install child addon files")
        return False

    # Load the child addon functionality
    if load_child_addon_functionality():
        # Add this parent to tracking (since we're manually loading)
        add_parent_to_child_tracking()
        #print("✅ Child addon functionality loaded and tracking updated")
        return True
    else:
        #print("❌ Failed to load child addon functionality")
        return False


def deactivate_child_addon():
    """Deactivate the child addon by unloading its functionality."""
    #print("🔄 Unloading child addon functionality...")

    # First check if other parents would still be active after we remove
    tracking_data = get_child_addon_tracking_data()
    other_parents_active = len([p for p in tracking_data["active_parents"] if p != PARENT_ADDON_UNIQUE_ID])

    # Try to unload (will return True if already unloaded or if other parents are active)
    if unload_child_addon_functionality(force=False):
        # Remove this parent from tracking (since we're manually unloading)
        remove_parent_from_child_tracking()
        if other_parents_active > 0:
            #print(f"✅ Child addon functionality kept loaded for {other_parents_active} other parent(s)")
            pass
        else:
            #print("✅ Child addon functionality unloaded and tracking updated")
            pass
        return True
    else:
        #print("❌ Failed to unload child addon functionality")
        return False


def remove_child_addon_from_user_prefs():
    """Remove the child addon files from user preferences."""
    child_addon_dir = get_child_addon_path()

    if p.exists(child_addon_dir):
        try:
            shutil.rmtree(child_addon_dir)
            #print(f"✅ Child addon files removed from: {child_addon_dir}")
            return True
        except Exception as e:
            print(f"⚠ Error removing child addon files: {e}")
            return False
    else:
        #print(f"✓ Child addon directory not found: {child_addon_dir}")
        return True


def is_child_addon_installed():
    """Check if child addon is installed in user preferences."""
    child_addon_dir = get_child_addon_path()
    child_addon_init = p.join(child_addon_dir, "__init__.py")
    return p.exists(child_addon_init)


def is_child_addon_active():
    """
    Check if child addon functionality is loaded.

    We check both:
    1. The tracking data (which should be accurate if everyone follows the protocol)
    2. sys.modules (as a fallback if tracking data is wrong)
    """
    # First check tracking data (primary source of truth)
    tracking_data = get_child_addon_tracking_data()
    if tracking_data["is_functionality_loaded"]:
        return True

    # Fallback: Check sys.modules
    child_addon_name = "modular_child_addons"

    # Check if any of the child addon modules are loaded
    module_prefixes = [
        f"{child_addon_name}.",
        "child_addon.",
    ]

    for module_name in sys.modules:
        for prefix in module_prefixes:
            if module_name.startswith(prefix):
                # Found a module from our child addon
                #print(f"⚠ Child addon module found in sys.modules but tracking says not loaded: {module_name}")
                return True

    # Also check for direct module names (use centralized constant)
    for module in CHILD_ADDON_ALL_MODULES:
        if module in sys.modules:
            # Check if it's from our child addon
            module_obj = sys.modules[module]
            if hasattr(module_obj, '__file__'):
                filepath = module_obj.__file__
                if filepath and 'modular_child_addons' in filepath:
                    #print(f"⚠ Child addon module found in sys.modules but tracking says not loaded: {module}")
                    return True

    return False


def is_child_addon_enabled_for_this_parent():
    """
    Check if child addon functionality is enabled for THIS specific parent.
    This is different from is_child_addon_active() which checks if functionality
    is loaded globally.
    """
    tracking_data = get_child_addon_tracking_data()
    return PARENT_ADDON_UNIQUE_ID in tracking_data["active_parents"]


def get_child_addon_tracking_data():
    """Get child addon tracking data to manage multiple parent addons."""
    central_base = get_central_library_base()

    # Create child addon tracking file path
    tracking_file = p.join(central_base, "child_addon_tracking.json")

    # Default tracking data
    default_data = {
        "active_parents": [],  # List of parent addon IDs that are using the child addon
        "last_activated_by": None,  # Last parent addon that activated the child addon
        "is_functionality_loaded": False  # Whether child addon functionality is currently loaded
    }

    # Try to read existing tracking data
    try:
        if p.exists(central_base) and p.exists(tracking_file):
            with open(tracking_file, 'r') as f:
                tracking_data = json.load(f)
                
                # Validate and fix tracking data
                if not isinstance(tracking_data.get("active_parents"), list):
                    tracking_data["active_parents"] = []
                if not isinstance(tracking_data.get("is_functionality_loaded"), bool):
                    tracking_data["is_functionality_loaded"] = False
                    
                return tracking_data
    except json.JSONDecodeError as e:
        print(f"⚠ Child addon tracking file is invalid JSON: {e}. Using default data.")
        return default_data
    except Exception as e:
        print(f"⚠ Error reading child addon tracking: {e}")
        return default_data

    return default_data

def reconcile_tracking_with_actual_state():
    """Check if the tracking data matches the actual module state."""
    tracking_data = get_child_addon_tracking_data()
    
    # Check if modules are actually loaded - look for any modules in our package
    actual_loaded = any(
        name.startswith("modular_child_addons") 
        for name in sys.modules.keys()
    )
    
    # If there's a mismatch, correct the tracking data
    if tracking_data["is_functionality_loaded"] != actual_loaded:
        #print(f"⚠ Reconciling tracking data: tracking says {'loaded' if tracking_data['is_functionality_loaded'] else 'not loaded'}, but actual state is {'loaded' if actual_loaded else 'not loaded'}")
        tracking_data["is_functionality_loaded"] = actual_loaded
        save_child_addon_tracking_data(tracking_data)
    
    # Make sure tracking data is properly updated in memory
    return tracking_data

def save_child_addon_tracking_data(tracking_data):
    """Save child addon tracking data."""
    central_base = get_central_library_base()
    tracking_file = p.join(central_base, "child_addon_tracking.json")

    try:
        # Ensure the directory exists before trying to write
        os.makedirs(central_base, exist_ok=True)

        with open(tracking_file, 'w') as f:
            json.dump(tracking_data, f, indent=2)
        return True
    except Exception as e:
        print(f"⚠ Error saving child addon tracking: {e}")
        return False


def add_parent_to_child_tracking():
    """Add this parent addon to the child addon tracking."""
    tracking_data = get_child_addon_tracking_data()
    parent_addon_id = PARENT_ADDON_UNIQUE_ID

    if parent_addon_id not in tracking_data["active_parents"]:
        tracking_data["active_parents"].append(parent_addon_id)
        #print(f"✓ Added parent {PARENT_ADDON_DISPLAY_NAME} to child addon tracking")
        save_child_addon_tracking_data(tracking_data)

    return tracking_data


def remove_parent_from_child_tracking():
    """Remove this parent addon from the child addon tracking."""
    tracking_data = get_child_addon_tracking_data()
    parent_addon_id = PARENT_ADDON_UNIQUE_ID

    if parent_addon_id in tracking_data["active_parents"]:
        tracking_data["active_parents"].remove(parent_addon_id)
        #print(f"✓ Removed parent {PARENT_ADDON_DISPLAY_NAME} from child addon tracking")
        save_child_addon_tracking_data(tracking_data)

    return tracking_data


def should_keep_child_addon_active():
    """Check if child addon should remain active based on active parents."""
    tracking_data = get_child_addon_tracking_data()
    return len(tracking_data["active_parents"]) > 0


def ensure_child_addon_installed():
    """
    Ensure child addon files are copied to extensions folder, but don't try to activate it.
    
    This function checks the version of the installed child addon and updates it
    if the parent addon has a newer version.
    """
    child_addon_dir = get_child_addon_path()
    
    # Check if child addon is already installed
    child_init_file = p.join(child_addon_dir, "__init__.py")
    manifest_file = p.join(child_addon_dir, "blender_manifest.toml")
    
    is_installed = p.exists(child_init_file) and p.exists(manifest_file)
    
    if is_installed:
        # Get installed version
        installed_version = get_installed_child_addon_version()
        
        if installed_version is not None:
            # Compare with parent version
            if is_version_newer(installed_version, CHILD_ADDON_VERSION):
                # Installed version is NEWER than parent version
                # This shouldn't normally happen, but we should keep the newer version
                #print(f"✓ Child addon already installed (version {'.'.join(map(str, installed_version))}) is NEWER than parent version ({'.'.join(map(str, CHILD_ADDON_VERSION))}) - keeping installed version")
                return True
            elif is_version_older(installed_version, CHILD_ADDON_VERSION):
                # Installed version is OLDER than parent version - update it
                #print(f"🔄 Child addon version {'.'.join(map(str, installed_version))} is OLDER than parent version {'.'.join(map(str, CHILD_ADDON_VERSION))} - updating...")
                if copy_child_addon_to_user_prefs():
                    #print(f"✅ Child addon updated to version {'.'.join(map(str, CHILD_ADDON_VERSION))}")
                    return True
                else:
                    #print(f"❌ Failed to update child addon")
                    return False
            else:
                # Versions are equal
                #print(f"✓ Child addon already installed with matching version {'.'.join(map(str, installed_version))}")
                return True
        else:
            # Could not read version, assume it needs update
            #print(f"⚠ Could not read installed child addon version - updating...")
            if copy_child_addon_to_user_prefs():
                #print(f"✅ Child addon updated")
                return True
            else:
                #print(f"❌ Failed to update child addon")
                return False
    else:
        # Not installed at all
        #print("📦 Installing child addon files...")
        if copy_child_addon_to_user_prefs():
            #print(f"✅ Child addon files installed to: {child_addon_dir}")
            return True
        else:
            #print(f"❌ Failed to install child addon files")
            return False


def _ensure_child_version_updated():
    """Guarantee that the installed child addon matches our bundled version.

    1. Compare the installed version vs the bundled (source-of-truth) version.
    2. If the installed version is OLDER (or missing), force-unload all
       child modules, copy the new files, clear sys.modules cache, then
       reload from scratch.
    3. Returns True if the installed files are now up to date.
    """
    bundled_version = CHILD_ADDON_VERSION  # already set by _read_bundled_child_version in register()
    installed_version = get_installed_child_addon_version()

    # If installed version is same or newer, nothing to do.
    if installed_version is not None and not is_version_older(installed_version, bundled_version):
        return True

    # --- VERSION MISMATCH or MISSING: update the files ---
    # 1. Force-unload any currently loaded child modules (they represent the OLD version)
    unload_child_addon_functionality(force=True)

    # 2. Copy new files from the bundled child_addon/ directory
    if not copy_child_addon_to_user_prefs():
        print("⚠ Failed to copy updated child addon files")
        return False

    # 3. Wipe stale modules from sys.modules so fresh imports happen
    _nuke_child_modules_from_sys()

    return True


def _nuke_child_modules_from_sys():
    """Remove ALL modular_child_addons modules from sys.modules.

    After a file update, old .pyc caches and previously-imported modules
    must be purged so that importlib re-executes the new source files.
    Also handles legacy underscore-style module names for compatibility.
    """
    package_name = "modular_child_addons"
    to_delete = [name for name in sys.modules
                 if name == package_name
                 or name.startswith(package_name + ".")
                 or name.startswith(package_name + "_")]
    for name in to_delete:
        try:
            del sys.modules[name]
        except KeyError:
            pass


def load_child_addon_functionality():
    """Load and register child addon functionality directly.

    Detects version changes: if the installed child addon files are OLDER
    than the bundled version, the old modules are force-unloaded, new files
    are copied, and the updated modules are loaded fresh.
    """
    try:
        _ensure_child_version_updated()

        # First check if functionality is already loaded
        tracking_data = get_child_addon_tracking_data()
        if tracking_data["is_functionality_loaded"]:
            #print("✓ Child addon functionality already loaded")

            # Still add this parent to tracking even if already loaded
            if PARENT_ADDON_UNIQUE_ID not in tracking_data["active_parents"]:
                tracking_data["active_parents"].append(PARENT_ADDON_UNIQUE_ID)
                tracking_data["last_activated_by"] = PARENT_ADDON_UNIQUE_ID
                save_child_addon_tracking_data(tracking_data)
                #print(f"✓ Added {PARENT_ADDON_DISPLAY_NAME} to active parents")

            return True

        # Get child addon path
        child_addon_dir = get_child_addon_path()

        # Check if child addon is installed
        child_init_file = p.join(child_addon_dir, "__init__.py")
        if not p.exists(child_init_file):
            #print(f"⚠ Child addon not found: {child_init_file}")
            # Try to install it
            if not ensure_child_addon_installed():
                #print(f"❌ Could not install child addon")
                return False

        #print("🔄 Loading child addon functionality...")

        # We need to load the child addon as a proper package
        # The child addon is in a directory like: .../modular_child_addons/
        # We'll add the parent directory to sys.path and import it as a package

        # Get the parent directory (where modular_child_addons folder is located)
        parent_dir = p.dirname(child_addon_dir)
        package_name = p.basename(child_addon_dir)  # Should be "modular_child_addons"

        # Save original sys.path
        original_sys_path = sys.path.copy()

        try:
            # Add parent directory to sys.path if not already there
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)

            # Now import the child addon as a package
            import importlib

            # Import the main package (this will load __init__.py)
            try:
                child_package = importlib.import_module(package_name)
                #print(f"✓ Imported child addon package: {package_name}")
            except ImportError as e:
                print(f"⚠ Failed to import child addon package: {e}")
                return False

            # Now import the submodules (use centralized constant)
            loaded_modules = {}

            for submodule_name in CHILD_ADDON_SUBMODULES:
                try:
                    full_name = f"{package_name}.{submodule_name}"
                    module = importlib.import_module(full_name)
                    loaded_modules[submodule_name] = module
                    #print(f"✓ Loaded module: {submodule_name}")
                except ImportError as e:
                    print(f"⚠ Failed to import module {submodule_name}: {e}")

            # Load operators subpackage
            operators_module = None
            try:
                operators_module = importlib.import_module(f"{package_name}.operators")
                #print(f"✓ Loaded operators subpackage")
            except ImportError as e:
                print(f"⚠ Failed to import operators subpackage: {e}")

            # Register all modules that have a register function
            # Register operators first (if it has a register function at the package level)
            if operators_module and hasattr(operators_module, 'register'):
                try:
                    operators_module.register()
                    #print(f"✓ Registered operators subpackage")
                except Exception as e:
                    print(f"⚠ Failed to register operators subpackage: {e}")

            # Register other modules
            for module_name, module in loaded_modules.items():
                if hasattr(module, 'register'):
                    try:
                        module.register()
                        #print(f"✓ Registered module: {module_name}")
                    except Exception as e:
                        print(f"⚠ Failed to register module {module_name}: {e}")

            # Update tracking data
            tracking_data = get_child_addon_tracking_data()
            tracking_data["is_functionality_loaded"] = True
            if PARENT_ADDON_UNIQUE_ID not in tracking_data["active_parents"]:
                tracking_data["active_parents"].append(PARENT_ADDON_UNIQUE_ID)
            tracking_data["last_activated_by"] = PARENT_ADDON_UNIQUE_ID
            save_child_addon_tracking_data(tracking_data)

            #print("✅ Child addon functionality loaded and registered")
            return True

        finally:
            # Restore original sys.path
            sys.path = original_sys_path

    except Exception as e:
        print(f"❌ Error loading child addon functionality: {e}")
        import traceback
        traceback.print_exc()
        return False

def unload_child_addon_functionality(force=False):
    """Unload and unregister child addon functionality."""
    try:
        # First reconcile tracking data with actual state
        tracking_data = reconcile_tracking_with_actual_state()
        

        # Check if we should keep child addon active
        if not force and should_keep_child_addon_active():
            #print(f"⚠ Not unloading child addon - other parent addons still active")
            return True

        # We need to look for the modules we loaded in sys.modules
        # With our new approach, modules can be loaded as:
        # 1. "modular_child_addons" (package)
        # 2. "modular_child_addons.panels" (module in package)
        # 3. "modular_child_addons_panels" (old style, for compatibility)
        import sys

        # Use centralized module list
        operator_submodules = ["geometry_nodes", "compositor", "shader"]

        all_module_names = []

        # Add package-style module names (new approach)
        package_name = "modular_child_addons"
        all_module_names.append(package_name)  # Main package

        # Add dot-notation module names
        for name in CHILD_ADDON_ALL_MODULES:
            all_module_names.append(f"{package_name}.{name}")

        # Add operator submodules
        all_module_names.append(f"{package_name}.operators")
        for name in operator_submodules:
            all_module_names.append(f"{package_name}.operators.{name}")

        # Add underscore-style module names (old approach, for compatibility)
        for name in CHILD_ADDON_ALL_MODULES:
            all_module_names.append(f"{package_name}_{name}")

        # Add operator submodules with underscores
        for name in operator_submodules:
            all_module_names.append(f"{package_name}_operators_{name}")

        # Also check for the original module names (without prefix) as fallback
        for name in CHILD_ADDON_ALL_MODULES:
            all_module_names.append(name)

        unregistered_count = 0
        modules_unregistered = []

        # Use a set to track already processed modules to avoid duplicates
        processed_modules = set()
        
        # We'll unregister in a specific order to prevent duplicate unregistration
        # 1. Unregister submodules first (operators, ui, etc.)
        # 2. Unregister top-level modules
        # 3. Unregister the main package
        unregister_order = [
            # Submodules
            *[f"modular_child_addons.operators.{name}" for name in operator_submodules],
            "modular_child_addons.operators",
            *[f"modular_child_addons.{name}" for name in CHILD_ADDON_SUBMODULES],
            
            # Top-level modules
            "modular_child_addons_operators_geometry_nodes",
            "modular_child_addons_operators_compositor",
            "modular_child_addons_operators_shader",
            *[f"modular_child_addons_{name}" for name in CHILD_ADDON_SUBMODULES],
            "modular_child_addons_operators",
            
            # Main package
            "modular_child_addons"
        ]
        
        # Add any other modules that might have been missed
        unregister_order += [name for name in all_module_names if name not in unregister_order]
        
        # First pass: unregister modules in the specific order
        for module_name in unregister_order:
            if module_name in sys.modules:
                module = sys.modules[module_name]
                try:
                    # Skip if already unregistered
                    if module_name in processed_modules:
                        continue
                        
                    processed_modules.add(module_name)
                    
                    # Check if the module has a registered unregister function
                    if hasattr(module, 'unregister') and callable(module.unregister):
                        module.unregister()
                        unregistered_count += 1
                        modules_unregistered.append(module_name)
                        #print(f"✓ Unregistered {module_name}")
                    else:
                        #print(f"⚠ Module {module_name} doesn't have callable unregister function")
                        pass
                except Exception as e:
                    # Silence specific known-safe errors
                    if "already unregistered" not in str(e) and "missing bl_rna" not in str(e):
                        print(f"⚠ Failed to unregister {module_name}: {e}")
                        pass
                    else:
                        # Mark as unregistered even if we got an error
                        if module_name not in modules_unregistered:
                            modules_unregistered.append(module_name)

        # Second pass: remove from sys.modules in reverse order
        for module_name in reversed(unregister_order):
            if module_name in sys.modules:
                try:
                    # Skip if already removed
                    if module_name not in sys.modules:
                        continue
                        
                    del sys.modules[module_name]
                    #print(f"✓ Removed from sys.modules: {module_name}")
                except KeyError:
                    pass  # Already removed
                except Exception as e:
                    print(f"⚠ Error removing {module_name} from sys.modules: {e}")


        # Also clean up the main package if it exists
        if package_name in sys.modules:
            # Only process if not already unregistered
            if package_name not in modules_unregistered:
                try:
                    module = sys.modules[package_name]
                    
                    # Try to unregister if it has the method
                    if hasattr(module, 'unregister') and callable(module.unregister):
                        try:
                            module.unregister()
                            #print(f"✓ Unregistered package: {package_name}")
                            unregistered_count += 1
                            modules_unregistered.append(package_name)
                        except Exception as e:
                            print(f"⚠ Failed to unregister package {package_name}: {e}")
                    
                    # Always remove from sys.modules
                    del sys.modules[package_name]
                    #print(f"✓ Removed package from sys.modules: {package_name}")
                except KeyError:
                    pass
                except Exception as e:
                    print(f"⚠ Error cleaning up package {package_name}: {e}")
                    pass

        if unregistered_count > 0:
            # Update tracking data
            tracking_data = get_child_addon_tracking_data()
            tracking_data["is_functionality_loaded"] = False
            tracking_data["last_activated_by"] = None
            save_child_addon_tracking_data(tracking_data)

            #print(f"✅ Child addon functionality unloaded ({unregistered_count} modules)")
            return True
        else:
            #print("⚠ No child addon modules found to unregister")

            # Still update tracking data since we're unloading
            tracking_data = get_child_addon_tracking_data()
            tracking_data["is_functionality_loaded"] = False
            tracking_data["last_activated_by"] = None
            save_child_addon_tracking_data(tracking_data)

            return True

    except Exception as e:
        print(f"⚠ Error unloading child addon functionality: {e}")
        import traceback
        traceback.print_exc()
        return False


# -----------------------------------------------------------------------------
# Library Management Functions (Similar to original but simplified)
# -----------------------------------------------------------------------------

def normalize_library_path(library_path: str):
    """Normalize an asset library path for reliable comparison across OS and Blender versions."""
    try:
        return p.normcase(p.normpath(library_path))
    except Exception:
        return library_path


def get_lib_path_index(prefs: Preferences, library_name: str, library_path: str):
    """Get the index of the library name or path for configuring them in the operator."""
    normalized_target = normalize_library_path(library_path)
    for index, lib in enumerate(prefs.filepaths.asset_libraries):
        if lib.name == library_name:
            return index
        if normalize_library_path(getattr(lib, 'path', '')) == normalized_target:
            return index
    return -1


def create_asset_library_in_preferences(prefs: Preferences, library_name: str, library_path: str, version_info: dict):
    """Create or re-add an asset library in preferences with Blender version fallbacks."""
    library_path = p.abspath(library_path)
    lib_index = get_lib_path_index(prefs, library_name, library_path)
    if lib_index != -1:
        return lib_index

    # Attempt direct collection creation first, which is more reliable in 5.1.x.
    try:
        asset_libraries = prefs.filepaths.asset_libraries
        if hasattr(asset_libraries, "add"):
            lib = asset_libraries.add()
            lib.name = library_name
        elif hasattr(asset_libraries, "new"):
            lib = asset_libraries.new(name=library_name)  # name must be keyword argument in 5.1.x
        else:
            raise AttributeError("User asset library collection has no add/new method")

        lib.path = library_path
        lib.import_method = 'APPEND'
        debug_log(f"✓ Directly created asset library '{library_name}'")

        lib_index = get_lib_path_index(prefs, library_name, library_path)
        if lib_index != -1:
            return lib_index

        debug_log(f"⚠ Direct creation created library but lookup failed for '{library_name}'")
        for index, current_lib in enumerate(prefs.filepaths.asset_libraries):
            debug_log(f"   Asset library {index}: name='{getattr(current_lib, 'name', '')}', path='{getattr(current_lib, 'path', '')}'")
    except Exception as e:
        print(f"⚠ Direct asset library creation failed for '{library_name}': {e}")

    # Fallback: try the Blender operator with EXEC_DEFAULT to avoid the popup confirm.
    # For 5.1.x, the operator might not accept 'type' parameter despite version detection
    try:
        # Check if we should use type parameter - but 5.1.x might not support it
        if version_info["features"]["asset_library_type_param"] and version_info["version_tuple"] >= (5, 2, 0):
            bpy.ops.preferences.asset_library_add('EXEC_DEFAULT', directory=library_path, type='LOCAL')
            debug_log(f"✓ Asset library operator executed '{library_name}' with type='LOCAL'")
        else:
            bpy.ops.preferences.asset_library_add('EXEC_DEFAULT', directory=library_path)
            debug_log(f"✓ Asset library operator executed '{library_name}'")
    except Exception as e:
        print(f"⚠ Operator asset library creation failed for '{library_name}' with EXEC_DEFAULT: {e}")

    lib_index = get_lib_path_index(prefs, library_name, library_path)
    if lib_index != -1:
        lib = prefs.filepaths.asset_libraries[lib_index]
        lib.name = library_name
        lib.import_method = 'APPEND'
        return lib_index

    print(f"❌ Could not create asset library '{library_name}' after direct and operator fallback")
    print(f"   Preferences asset_libraries count: {len(prefs.filepaths.asset_libraries)}")
    for index, current_lib in enumerate(prefs.filepaths.asset_libraries):
        print(f"   Asset library {index}: name='{getattr(current_lib, 'name', '')}', path='{getattr(current_lib, 'path', '')}'")
    return -1


def cleanup_existing_libraries(prefs, central_base):
    """
    Clean up any libraries with our names that don't have the correct path.
    Remove duplicates (.001, .002 suffixes) and update wrong paths.
    Returns list of library names that need to be created.
    """
    # This is a simplified version - in production you'd want the full logic
    libraries_to_create = []

    # Check which libraries already exist with correct paths
    for lib_name in CENTRAL_LIB_SUBFOLDERS:
        library_path = p.join(central_base, lib_name)
        lib_index = get_lib_path_index(prefs, lib_name, library_path)

        if lib_index == -1:
            # Library doesn't exist
            libraries_to_create.append(lib_name)
        else:
            # Library exists - verify it has correct path
            lib = prefs.filepaths.asset_libraries[lib_index]
            if lib.path != library_path:
                # Update path
                lib.path = library_path
                #print(f"✓ Updated library path: {lib_name}")

    return libraries_to_create


def register_library(force_reregister=False):
    """Register each library subfolder as a separate library in Blender preferences."""
    prefs = bpy.context.preferences

    # Get central library path at runtime
    central_base = get_central_library_base()

    # Use parent addon info for tracking
    parent_addon_info = {
        'name': PARENT_ADDON_DISPLAY_NAME,
        'version': PARENT_ADDON_VERSION,
        'unique_id': PARENT_ADDON_UNIQUE_ID
    }

    # Check if already tracked
    addon_id = utility.get_addon_identifier(parent_addon_info)
    tracking_data = utility.read_addon_tracking(central_base)
    already_tracked = addon_id in tracking_data

    # Determine if we need to force-copy assets (version upgrade)
    needs_asset_update = False
    if already_tracked:
        tracked_version = tracking_data[addon_id].get('version', None)
        if tracked_version is not None:
            tracked_version_tuple = tuple(tracked_version)
            if is_version_older(tracked_version_tuple, PARENT_ADDON_VERSION):
                #print(f"🔄 Parent addon version upgraded from {tracked_version_tuple} to {PARENT_ADDON_VERSION} - updating assets...")
                needs_asset_update = True
        else:
            # No version tracked, assume update needed
            needs_asset_update = True

    if force_reregister and already_tracked:
        #print(f"🔄 Forcing re-registration of tracked parent addon: {addon_id}")
        del tracking_data[addon_id]
        utility.write_addon_tracking(central_base, tracking_data)
        already_tracked = False
        needs_asset_update = True

    # Smart cleanup - update existing libraries to correct paths
    libraries_to_create = cleanup_existing_libraries(prefs, central_base)

    # Check if source directories exist
    existing_libraries = []
    for lib_name in CENTRAL_LIB_SUBFOLDERS:
        source_dir = p.join(p.dirname(__file__), lib_name)
        if p.exists(source_dir):
            existing_libraries.append(lib_name)

    # Add this parent addon to central library and copy assets
    # Use force_copy=True when version has changed to overwrite existing blend files
    utility.add_addon_to_central_library(
        parent_addon_info, existing_libraries, p.dirname(__file__), central_base,
        force_copy=needs_asset_update
    )

    # Create libraries that don't exist yet
    registered_count = 0
    for lib_name in existing_libraries:
        library_path = p.join(central_base, lib_name)

        if lib_name in libraries_to_create:
            # Library doesn't exist, create it
            version_info = get_blender_version_info()
            lib_index = create_asset_library_in_preferences(prefs, lib_name, library_path, version_info)
            if lib_index != -1:
                registered_count += 1
            else:
                print(f"❌ Could not create library {lib_name} after fallback")
                print(f"   Debug: Blender version {version_info['version_string']} ({version_info['version_category']})")
                print(f"   Debug: Asset library type param supported: {version_info['features']['asset_library_type_param']}")
        else:
            # Library already exists - ensure correct settings
            lib_index = get_lib_path_index(prefs, lib_name, library_path)
            if lib_index != -1:
                lib = prefs.filepaths.asset_libraries[lib_index]
                lib.name = lib_name
                lib.import_method = 'APPEND'
                registered_count += 1

    #print(f"✅ Successfully registered {registered_count} libraries")
    return registered_count


def unregister_library(full_cleanup=False):
    """
    Remove individual libraries while maintaining tracking unless doing full cleanup.
    """
    #print("🔄 Unregistering asset libraries...")
    
    try:
        central_base = get_central_library_base()
        parent_addon_info = {
            'name': PARENT_ADDON_DISPLAY_NAME,
            'version': PARENT_ADDON_VERSION,
            'unique_id': PARENT_ADDON_UNIQUE_ID
        }

        # Always maintain tracking unless explicitly doing full cleanup
        if full_cleanup:
            utility.remove_addon_from_central_library(parent_addon_info, central_base, cleanup_mode='force')
        else:
            # Update library presence without removing tracking
            utility.update_addon_in_central_library(parent_addon_info, [], central_base, p.dirname(__file__))

            # Check which libraries are still used by other addons
            tracking_data = utility.read_addon_tracking(central_base)
            used_libraries = set()
            for addon_data in tracking_data.values():
                used_libraries.update(addon_data.get('libraries', []))

            # Remove libraries that are no longer used
            try:
                prefs = bpy.context.preferences
                for lib_name in CENTRAL_LIB_SUBFOLDERS:
                    if lib_name not in used_libraries:
                        lib_path = p.join(central_base, lib_name)
                        lib_index = get_lib_path_index(prefs, lib_name, lib_path)
                        if lib_index != -1:
                            bpy.ops.preferences.asset_library_remove(index=lib_index)
                            print(f"✓ Removed unused library: {lib_name}")
            except Exception as e:
                print(f"⚠ Could not remove unused libraries from preferences: {e}")


        # Check if no other addons are using the central library
        active_addons = utility.get_active_addons_count(central_base)

        if active_addons == 0:
            # No other addons using any libraries, clean up
            #print("🔄 Cleaning up libraries...")

            try:
                prefs = bpy.context.preferences
                for lib_name in CENTRAL_LIB_SUBFOLDERS:
                    lib_path = p.join(central_base, lib_name)
                    lib_index = get_lib_path_index(prefs, lib_name, lib_path)
                    if lib_index != -1:
                        bpy.ops.preferences.asset_library_remove(index=lib_index)
                        #print(f"✓ Removed library: {lib_name}")
            except Exception as e:
                print(f"⚠ Could not access preferences during uninstallation: {e}")

            # Clean up central library files
            try:
                utility.cleanup_central_library(central_base)
                #print("✓ Cleaned up central library files")
            except Exception as e:
                print(f"⚠ Could not cleanup central library files: {e}")

        else:
            #print(f"✓ {active_addons} addon(s) still using central library, keeping libraries registered")
            pass


    except Exception as e:
        print(f"⚠ Error during library unregistration: {e}")


def fully_uninstall_library():
    """Forcefully remove all libraries (for manual cleanup if needed)."""
    #print("🗑️  Addon library cleanup initiated...")

    try:
        central_base = get_central_library_base()

        # Remove parent addon from tracking
        parent_addon_info = {
            'name': PARENT_ADDON_DISPLAY_NAME,
            'version': PARENT_ADDON_VERSION,
            'unique_id': PARENT_ADDON_UNIQUE_ID
        }
        utility.remove_addon_from_central_library(parent_addon_info, central_base, cleanup_mode='force')

        # Remove libraries from preferences
        try:
            prefs = bpy.context.preferences
            for lib_name in CENTRAL_LIB_SUBFOLDERS:
                lib_path = p.join(central_base, lib_name)
                lib_index = get_lib_path_index(prefs, lib_name, lib_path)
                if lib_index != -1:
                    bpy.ops.preferences.asset_library_remove(index=lib_index)
        except Exception as e:
            print(f"⚠ Could not access preferences during forced cleanup: {e}")

        # Force cleanup of central library files
        try:
            utility.cleanup_central_library(central_base)
        except Exception as e:
            print(f"⚠ Could not cleanup central library files: {e}")

        #print("✅ Addon library cleanup complete")

    except Exception as e:
        print(f"⚠ Error during addon library cleanup: {e}")
        pass


def register_all_libraries():
    """Register the central asset library."""
    #print("🔄 register_all_libraries() called")
    register_library()

    # Try to refresh the asset browser UI
    try:
        bpy.ops.asset.library_refresh()
    except Exception:
        #print(f"Asset refresh skipped")
        pass


def unregister_all_libraries():
    """Unregister the central asset library if needed."""
    unregister_library()

    # Try to refresh the asset browser UI
    try:
        bpy.ops.asset.library_refresh()
    except Exception:
        #print(f"Asset refresh skipped")
        pass



# -----------------------------------------------------------------------------
# Main Registration
# -----------------------------------------------------------------------------

# Flag to track if libraries have been registered
_library_refresh_done = False


def delayed_setup():
    """Delayed setup called by timer."""
    global _library_refresh_done

    if _library_refresh_done:
        return None  # Don't repeat timer

    try:
        # Step 1: Register libraries (this will add us to central library tracking)
        register_all_libraries()

        # Step 2: Ensure child addon files are installed
        ensure_child_addon_installed()

        # Step 3: Load child addon functionality by default on first run
        # On subsequent runs, only load if user hasn't explicitly disabled it
        tracking_data = get_child_addon_tracking_data()

        # Check if this is the first time this parent is running
        # (i.e., not in active_parents list yet)
        is_first_run = PARENT_ADDON_UNIQUE_ID not in tracking_data["active_parents"]

        if is_first_run:
            # First time this parent is running - enable child addon by default
            #print("🔄 First run detected - enabling child addon functionality by default")

            # Add this parent to active parents
            tracking_data["active_parents"].append(PARENT_ADDON_UNIQUE_ID)
            tracking_data["last_activated_by"] = PARENT_ADDON_UNIQUE_ID
            save_child_addon_tracking_data(tracking_data)

            # Load child addon functionality
            if load_child_addon_functionality():
                #print("✅ Child addon functionality loaded (first run)")
                pass
            else:
                #print("⚠ Could not load child addon functionality, but continuing...")
                pass
        else:
            # Not first run - respect user's choice
            if PARENT_ADDON_UNIQUE_ID in tracking_data["active_parents"]:
                #print("🔄 Auto-loading child addon functionality (user previously enabled it)")

                if not tracking_data["is_functionality_loaded"]:
                    # Load child addon functionality if not already loaded
                    if load_child_addon_functionality():
                        #print("✅ Child addon functionality loaded")
                        pass
                    else:
                        #print("⚠ Could not load child addon functionality, but continuing...")
                        pass
                else:
                    #print("✓ Child addon functionality already loaded")
                    pass
            else:
                #print("ℹ Child addon functionality not auto-loaded (user disabled it)")
                pass

        # Step 4: Try to refresh asset browser
        try:
            bpy.ops.asset.library_refresh()
        except:
            pass

        _library_refresh_done = True
        #print("✅ Parent addon setup complete")
        #print(f"📚 Child addon tracking: {len(tracking_data['active_parents'])} active parent(s)")

        return None  # Don't repeat timer

    except Exception as e:
        print(f"⚠ Delayed setup failed: {e}")
        import traceback
        traceback.print_exc()
        return 2.0  # Try again in 2 seconds


def register():
    """Register the parent addon."""
    global _library_refresh_done, CHILD_ADDON_VERSION
    _library_refresh_done = False

    # --- Single source of truth: read child version from bundled manifest ---
    bundled_ver = _read_bundled_child_version()
    if bundled_ver is not None:
        CHILD_ADDON_VERSION = bundled_ver
    # -----------------------------------------------------------------------

    # Log version information for debugging and compatibility
    log_version_info()
    
    # Check version compatibility
    supported, reason = is_blender_version_supported()
    if not supported:
        print(f"⚠ {reason}")
        # Continue anyway but log the issue
    
    # Log any compatibility warnings
    warnings = get_version_compatibility_warnings()
    if warnings:
        print("Compatibility Warnings:")
        for warning in warnings:
            print(f"  ⚠ {warning}")

    # First reconcile tracking data with actual state
    reconcile_tracking_with_actual_state()

    # Import and register UI module (preferences panel and operators)
    from . import ui
    ui.register()

    # First check if child addon is already installed
    child_addon_dir = get_child_addon_path()
    child_init_file = p.join(child_addon_dir, "__init__.py")
    
    # Only install child addon if not already installed
    if not p.exists(child_init_file):
        # Add delayed setup timer to install child addon and set up libraries
        bpy.app.timers.register(delayed_setup, first_interval=0.5)
        #print("🔄 Child addon not found - scheduling installation")
    else:
        #print("✓ Child addon already installed - skipping copy")
        # Still need to set up libraries and load functionality
        bpy.app.timers.register(delayed_setup, first_interval=0.5)

    #print("✅ Parent addon registered (library manager)")
    
    # Only run delayed setup if we're in Blender (not during background mode)
    if not bpy.app.background:
        # Add delayed setup timer
        bpy.app.timers.register(delayed_setup, first_interval=0.5)
    else:
        #print("ℹ Running in background mode - skipping delayed setup")
        pass

def unregister():
    """Unregister the parent addon - called when Blender exits or addon is disabled."""
    global _library_refresh_done
    _library_refresh_done = True

    # Remove timer
    try:
        if bpy.app.timers.is_registered(delayed_setup):
            bpy.app.timers.unregister(delayed_setup)
    except:
        pass

    # Get current tracking data before modification
    tracking_data = get_child_addon_tracking_data()
    
    # Check if this is a permanent uninstall or just session closure
    is_permanent_uninstall = not bpy.context.preferences.addons.get(__name__, False)
    
    if is_permanent_uninstall:
        #print("🔧 Permanent uninstallation detected - cleaning up child addon...")
        # Remove from tracking and unload
        tracking_data = remove_parent_from_child_tracking()
        if len(tracking_data["active_parents"]) == 0:
            unload_child_addon_functionality(force=True)
            # Clean up files only if uninstalling
            remove_child_addon_from_user_prefs()
    else:
        #print("🔧 Session closure detected - keeping child addon available...")
        # Only remove from active parents but keep functionality loaded
        tracking_data["active_parents"] = [p for p in tracking_data["active_parents"] if p != PARENT_ADDON_UNIQUE_ID]
        save_child_addon_tracking_data(tracking_data)
        #print(f"🔄 {len(tracking_data['active_parents'])} other parent(s) still active - keeping child addon loaded")

    # Only clean up libraries if permanently uninstalling
    if is_permanent_uninstall:
        #print("🔄 Unregistering libraries...")
        unregister_library()
    else:
        #print("ℹ Keeping libraries registered between sessions")
        pass
    
    # Update central library tracking only if uninstalling
    if is_permanent_uninstall:
        try:
            central_base = get_central_library_base()
            parent_addon_info = {
                'name': PARENT_ADDON_DISPLAY_NAME,
                'version': PARENT_ADDON_VERSION,
                'unique_id': PARENT_ADDON_UNIQUE_ID
            }
            addon_id = utility.get_addon_identifier(parent_addon_info)
            library_tracking_data = utility.read_addon_tracking(central_base)

            if addon_id in library_tracking_data:
                #print(f"🔄 Removing {PARENT_ADDON_DISPLAY_NAME} from central library tracking")
                del library_tracking_data[addon_id]
                utility.write_addon_tracking(central_base, library_tracking_data)
                #print(f"📚 Updated library status: {len(library_tracking_data)} addon(s) remaining")
                
        except Exception as e:
            print(f"⚠ Error updating central library tracking: {e}")
            pass

    # Never remove child addon files during unregister - they are persistent
    #print("ℹ Keeping child addon files for next session")

    # Unregister UI module (MUST be last to avoid issues with operators still being referenced)
    try:
        from . import ui
        ui.unregister()
        #print("✓ Unregistered UI module")
    except Exception as e:
        print(f"⚠ Failed to unregister UI module: {e}")

    #print("✅ Parent addon fully unregistered")