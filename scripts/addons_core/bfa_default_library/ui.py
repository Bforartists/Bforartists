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
UI Module - Parent Addon Preferences Panel
Contains the addon preferences panel and related operators.
"""

import bpy
from os import path as p
from bpy.types import AddonPreferences

# Import configuration and functions from parent module
from . import (
    PARENT_ADDON_DISPLAY_NAME,
    PARENT_ADDON_VERSION,
    PARENT_ADDON_UNIQUE_ID,
    CENTRAL_LIB_SUBFOLDERS,
    is_child_addon_active,
    get_lib_path_index,
    get_central_library_base,
)
from . import utility


# -----------------------------------------------------------------------------
# Library Operators for Preferences Panel
# -----------------------------------------------------------------------------

class LIBADDON_OT_cleanup_libraries(bpy.types.Operator):
    """Remove all Default Library asset libraries from preferences (manual cleanup)"""
    bl_idname = "preferences.libaddon_cleanup_libraries"
    bl_label = "Remove Libraries"
    bl_description = "Remove all Default Library asset libraries from preferences"
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        prefs = context.preferences
        central_base = get_central_library_base()

        # Simply remove the libraries from prefs by path/name
        removed = 0
        for lib_name in CENTRAL_LIB_SUBFOLDERS:
            lib_path = p.join(central_base, lib_name)
            lib_index = get_lib_path_index(prefs, lib_name, lib_path)
            if lib_index != -1:
                try:
                    bpy.ops.preferences.asset_library_remove(index=lib_index)
                    removed += 1
                except Exception as e:
                    print(f"⚠ Could not remove library '{lib_name}': {e}")

        self.report({'INFO'}, f"Removed {removed} libraries from preferences")
        return {'FINISHED'}


class LIBADDON_OT_readd_libraries(bpy.types.Operator):
    """Re-add / update all Default Library asset libraries to preferences"""
    bl_idname = "preferences.libaddon_readd_libraries"
    bl_label = "Re-add / Update Libraries"
    bl_description = "Re-add all Default Library asset libraries to preferences and update assets"
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        prefs = context.preferences
        central_base = get_central_library_base()
        parent_addon_dir = p.dirname(__file__)

        parent_addon_info = {
            'name': PARENT_ADDON_DISPLAY_NAME,
            'version': PARENT_ADDON_VERSION,
            'unique_id': PARENT_ADDON_UNIQUE_ID
        }

        # Step 1: Remove all existing libraries from prefs (clean slate)
        for lib_name in CENTRAL_LIB_SUBFOLDERS:
            lib_path = p.join(central_base, lib_name)
            lib_index = get_lib_path_index(prefs, lib_name, lib_path)
            if lib_index != -1:
                try:
                    bpy.ops.preferences.asset_library_remove(index=lib_index)
                except Exception:
                    pass

        # Step 2: Clean tracking for this addon so add_addon_to_central_library creates fresh
        addon_id = utility.get_addon_identifier(parent_addon_info)
        tracking_data = utility.read_addon_tracking(central_base)
        if addon_id in tracking_data:
            del tracking_data[addon_id]
            utility.write_addon_tracking(central_base, tracking_data)

        # Step 3: Check which source libraries exist
        existing_libraries = []
        for lib_name in CENTRAL_LIB_SUBFOLDERS:
            source_dir = p.join(parent_addon_dir, lib_name)
            if p.exists(source_dir):
                existing_libraries.append(lib_name)

        # Step 4: Force-copy assets and update tracking
        utility.add_addon_to_central_library(
            parent_addon_info, existing_libraries, parent_addon_dir, central_base,
            force_copy=True
        )

        # Step 5: Create all libraries in prefs
        registered_count = 0
        for lib_name in existing_libraries:
            library_path = p.join(central_base, lib_name)
            try:
                if bpy.app.version >= (5, 1, 0):
                    bpy.ops.preferences.asset_library_add(directory=library_path, type='LOCAL')
                else:
                    bpy.ops.preferences.asset_library_add(directory=library_path)

                # Find the newly created library and configure it
                for lib in prefs.filepaths.asset_libraries:
                    if lib.path == library_path:
                        lib.name = lib_name
                        lib.import_method = 'APPEND'
                        registered_count += 1
                        break
            except Exception as e:
                print(f"⚠ Could not create library '{lib_name}': {e}")

        # Step 6: Refresh asset browser
        try:
            bpy.ops.asset.library_refresh()
        except Exception:
            pass

        self.report({'INFO'}, f"{registered_count} libraries re-added and assets updated")
        return {'FINISHED'}


# -----------------------------------------------------------------------------
# Parent Addon Preferences Panel
# -----------------------------------------------------------------------------

class LIBADDON_APT_preferences(AddonPreferences):
    """Parent addon preferences panel in user preferences"""
    bl_idname = __package__  # Uses the package name (bfa_default_library)

    def draw(self, context):
        layout = self.layout

        # Header
        box = layout.box()
        box.label(text=f"{PARENT_ADDON_DISPLAY_NAME}", icon='ASSET_MANAGER')
        box.label(text=f"Version: {PARENT_ADDON_VERSION[0]}.{PARENT_ADDON_VERSION[1]}.{PARENT_ADDON_VERSION[2]}")

        # Status
        box.separator()
        row = box.row()
        if is_child_addon_active():
            row.label(text="Status: Active", icon='CHECKMARK')
        else:
            row.label(text="Status: Inactive", icon='X')

        # Library management
        box.separator()
        box.label(text="Library Management:")

        row = box.row(align=True)
        row.operator("preferences.libaddon_readd_libraries",
                    text="Re-add Libraries",
                    icon='FILE_REFRESH')

        row.operator("preferences.libaddon_cleanup_libraries",
                    text="Remove Libraries",
                    icon='TRASH')


# -----------------------------------------------------------------------------
# Classes to register
# -----------------------------------------------------------------------------

classes = (
    LIBADDON_APT_preferences,
    LIBADDON_OT_cleanup_libraries,
    LIBADDON_OT_readd_libraries,
)


def register():
    """Register UI classes."""
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except ValueError as e:
            if "already registered" not in str(e):
                print(f"⚠ Error registering {cls.__name__}: {e}")


def unregister():
    """Unregister UI classes."""
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception as e:
            if "not registered" not in str(e) and "missing bl_rna" not in str(e):
                print(f"⚠ Error unregistering class {cls.__name__}: {e}")
