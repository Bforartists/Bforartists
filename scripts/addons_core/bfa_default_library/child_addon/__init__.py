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
Default Asset Library Child Module
This is a module that contains all operators, panels, handlers, and wizards.
It's loaded directly by the parent addon, not as a separate addon.

This file should be empty or contain minimal code since the parent addon
handles all module loading and registration.
"""

import bpy

# -----------------------------------------------------------------------------
# Shared Utilities
# -----------------------------------------------------------------------------

def is_bforartists():
    """
    Check if running in Bforartists (vs standard Blender).

    Returns True if running in Bforartists, False if running in Blender.
    This is determined by checking for Bforartists-specific UI elements.
    """
    return "OUTLINER_MT_view" in dir(bpy.types)


def get_icon(bforartists_icon, blender_fallback="INFO"):
    """
    Get the appropriate icon based on whether running in Bforartists or Blender.

    Args:
        bforartists_icon: Icon name to use in Bforartists
        blender_fallback: Icon name to use in standard Blender (default: "INFO")

    Returns:
        The appropriate icon name string.
    """
    return bforartists_icon if is_bforartists() else blender_fallback


# No registration here - handled by parent addon
# This file exists so Python recognizes this as a package

# Placeholder functions that do nothing - actual registration is handled by parent
def register():
    """Placeholder - registration handled by parent addon."""
    pass
    
def unregister():
    """Placeholder - unregistration handled by parent addon."""
    pass