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
from bpy.props import BoolProperty
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
    get_blender_version_info,  # Add version detection
    get_version_compatibility_warnings,  # Add compatibility warnings
    create_asset_library_in_preferences,
)
from . import utility


# -----------------------------------------------------------------------------
# Library Operators for Preferences Panel
# -----------------------------------------------------------------------------

class LIBADDON_OT_cleanup_libraries(bpy.types.Operator):
    """Remove this addon's files from the central library repository."""
    bl_idname = "preferences.libaddon_cleanup_libraries"
    bl_label = "Remove Addon Files"
    bl_description = "Remove this addon's files from the central library repository. The addon can re-add them later without deactivating."
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        central_base = get_central_library_base()

        parent_addon_info = {
            'name': PARENT_ADDON_DISPLAY_NAME,
            'version': PARENT_ADDON_VERSION,
            'unique_id': PARENT_ADDON_UNIQUE_ID
        }

        removed = utility.remove_addon_files_from_central_library(parent_addon_info, central_base)

        self.report({'INFO'}, f"Removed {removed} files from central library")
        return {'FINISHED'}


class LIBADDON_OT_readd_libraries(bpy.types.Operator):
    """Re-add / update all Default Library asset libraries to preferences"""
    bl_idname = "preferences.libaddon_readd_libraries"
    bl_label = "Re-add / Update Libraries"
    bl_description = "Re-add all Default Library asset libraries to preferences and update assets. If the addon is activated, this is automatic every session."
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

        # Step 1: Refresh central library contents from source
        existing_libraries = []
        for lib_name in CENTRAL_LIB_SUBFOLDERS:
            source_dir = p.join(parent_addon_dir, lib_name)
            if p.exists(source_dir):
                existing_libraries.append(lib_name)

        utility.add_addon_to_central_library(
            parent_addon_info, existing_libraries, parent_addon_dir, central_base,
            force_copy=True
        )

        # Step 2: Re-register missing libraries in preferences only if needed
        registered_count = 0
        version_info = get_blender_version_info()
        for lib_name in existing_libraries:
            library_path = p.join(central_base, lib_name)
            lib_index = create_asset_library_in_preferences(prefs, lib_name, library_path, version_info)
            if lib_index != -1:
                registered_count += 1
            else:
                print(f"⚠ Could not create library '{lib_name}' after fallback")
                print(f"   Debug: Blender version {version_info['version_string']} ({version_info['version_category']})")

        # Step 3: Refresh asset browser
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

    debug_asset_registration: BoolProperty(
        name="Debug Asset Library Registration",
        description="Print detailed asset library registration logs during addon registration and refresh actions",
        default=False,
    )

    def draw(self, context):
        layout = self.layout

        # Header
        box = layout.box()
        box.label(text=f"{PARENT_ADDON_DISPLAY_NAME}", icon='ASSET_MANAGER')
        box.label(text=f"Version: {PARENT_ADDON_VERSION[0]}.{PARENT_ADDON_VERSION[1]}.{PARENT_ADDON_VERSION[2]}")

        # DEBUG:VERSION NOTICE - Add this section
        #version_info = get_blender_version_info()
        #warnings = get_version_compatibility_warnings()
        
        #box.separator()
        #version_box = box.box()
        #version_box.label(text="Blender Version Info", icon='INFO')
        #version_box.label(text=f"Detected: {version_info['version_category']}")
        #version_box.label(text=f"Version: {version_info['version_string']}")
        
        # DEBUG: Show compatibility warnings if any
        #if warnings:
        #    version_box.separator()
        #    version_box.label(text="Compatibility Notes:", icon='ERROR')
        #    for warning in warnings:
        #        version_box.label(text=f"• {warning}", icon='DOT')

        # Status
        box.separator()
        row = box.row()
        if is_child_addon_active():
            row.label(text="Status: Active", icon='CHECKMARK')
        else:
            row.label(text="Status: Inactive", icon='X')

        box.separator()
        box.prop(self, "debug_asset_registration")

        # Library management
        box.separator()
        box.label(text="Library Management:")

        row = box.row(align=True)
        row.operator("preferences.libaddon_readd_libraries",
                    text="Re-add Libraries",
                    icon='FILE_REFRESH')

        row.operator("preferences.libaddon_cleanup_libraries",
                    text="Remove Files",
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
