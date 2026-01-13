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
from bpy.types import AddonPreferences

# Import configuration and functions from parent module
from . import (
    PARENT_ADDON_DISPLAY_NAME,
    PARENT_ADDON_VERSION,
    is_child_addon_active,
    fully_uninstall_library,
    register_library,
)


# -----------------------------------------------------------------------------
# Library Operators for Preferences Panel
# -----------------------------------------------------------------------------

class LIBADDON_OT_cleanup_libraries(bpy.types.Operator):
    """Remove all Default Library asset libraries from preferences (manual cleanup)"""
    bl_idname = "preferences.libaddon_cleanup_libraries"
    bl_label = "Remove Libraries"
    bl_description = "Remove all Default Library asset libraries from Blender preferences"
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
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
        register_library(force_reregister=True)

        try:
            bpy.ops.asset.library_refresh()
        except:
            pass

        self.report({'INFO'}, "Default Library asset libraries re-added to preferences")
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
