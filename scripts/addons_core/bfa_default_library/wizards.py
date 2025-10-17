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
# Wizard Main Module
# Main entry point that imports and registers all wizard components
# -----------------------------------------------------------------------------

import bpy

# Import wizard components
from . import wizard_operators
from . import wizard_handlers

def register():
    """Register all wizard components"""
    wizard_operators.register()
    wizard_handlers.register()

def unregister():
    """Unregister all wizard components"""
    wizard_handlers.unregister()
    wizard_operators.unregister()

if __name__ == "__main__":
    register()
