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
        "name": "Power User Tools",
        "description": "Additional set of user experience tools and operators to assist with every day use for the power user.",
        "author": "Draise (@trinumedia)",
        "version": (0, 2, 1),
        "blender": (4, 00, 0),
        "location": "Varios consistent locations for the power user - customize as you need! ",
        "warning": "This is a Bforartists exclusive addon for the time being", # used for warning icon and text in add-ons panel
        "doc_url": "https://github.com/Bforartists/Manual",
        "tracker_url": "https://github.com/Bforartists/Bforartists",
        "support": "OFFICIAL",
        "category": "Bforartists"
        }


import sys

from bpy.utils import register_submodule_factory

from . import prefs
from . import properties
from . import toolshelf
from . import ui
from . import ops

submodule_names = [
    "prefs",
    "properties",
    "toolshelf",
    "ui",
    "ops",
]

register, unregister = register_submodule_factory(__name__, submodule_names)
