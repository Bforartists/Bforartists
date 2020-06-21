# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
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
    "name": "Add Camera Rigs",
    "author": "Wayne Dixon, Brian Raschko, Kris Wittig, Damien Picard, Flavio Perez",
    "version": (1, 4, 4),
    "blender": (2, 80, 0),
    "location": "View3D > Add > Camera > Dolly or Crane Rig",
    "description": "Adds a Camera Rig with UI",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/camera/camera_rigs.html",
    "tracker_url": "https://github.com/waylow/add_camera_rigs/issues",
    "category": "Camera",
}

import bpy
import os

from . import build_rigs
from . import operators
from . import ui_panels
from . import prefs
from . import composition_guides_menu

# =========================================================================
# Registration:
# =========================================================================

def register():
    build_rigs.register()
    operators.register()
    ui_panels.register()
    prefs.register()
    composition_guides_menu.register()


def unregister():
    build_rigs.unregister()
    operators.unregister()
    ui_panels.unregister()
    prefs.unregister()
    composition_guides_menu.unregister()


if __name__ == "__main__":
    register()
