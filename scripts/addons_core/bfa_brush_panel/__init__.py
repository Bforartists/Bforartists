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

bl_info = {
    "name": "Brush Panel",
    "author": "Iyad Ahmed (@cgonfire), Draise (@trinumedia)",
    "version": (0, 0, 12),
    "blender": (3, 1, 0),
    "location": "3D View > Tools",
    "description": "Official BFA add-on to display brushes in a top-level panel",
    "doc_url": "https://github.com/Bforartists/Manual",
    "tracker_url": "https://github.com/Bforartists/Bforartists",
    "support": "OFFICIAL",
    "category": "Bforartists",
}

## INFO ##
# This add-on adds top-level brush presets into a new toolshelf tab and brush panels you can collapse, pin or use.
# The panels update depending on how many brush presets you have per brush group.
# The buttons also highlight when activated, and the list updates when you create and remove brushes.
# The iconography also updates to custom icons when they are defined by the user.
# The panel also is responsive with the standard 1,2,3 and text row format defined by Bforartists.
# In use cases, this has already proven a huge time saver when weighting rigs - very intuitive.

## UPDATES ##
# -added icons to the GP using an attribute check and new library - Draise


import sys

from bpy.utils import register_submodule_factory

submodule_names = [
    "operators",
    "icon_system",
    "weight_paint",
    "vertex_paint",
    "texture_paint",
    "texture_paint_image_editor",
    "sculpt",
    "gp",
]

register, unregister = register_submodule_factory(__name__, submodule_names)
