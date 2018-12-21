### BEGIN GPL LICENSE BLOCK #####
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

# <pep8 compliant>

bl_info = {
    "name": "Cacharanth",
    "author": "Pablo Vazquez, Lukas Toenne",
    "version": (0, 2),
    "blender": (2, 7, 3),
    "location": "View3D > Cacharanth (Tab)",
    "description": "Import and Export Caches",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
    "category": "Import-Export",
    }

import bpy
from cacharanth import ui, meshcache

def register():
    ui.register()
    meshcache.register()

def unregister():
    ui.unregister()
    meshcache.unregister()

if __name__ == "__main__":
    register()
