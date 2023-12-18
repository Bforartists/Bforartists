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

from bfa_3Dsequencer import (
    #editorial, #BFA - temporariliy removed
    #keymaps, #BFA - temporariliy removed
    preferences,
    #render, #BFA - temporariliy removed
    sequence,
    #shared_collections, #BFA - temporariliy removed
    shot,
    sync,
)


bl_info = {
    "name": "BFA - 3D Sequencer",
    "author": "The SPA Studios, Znight, Draise",
    "description": "Toolset for a 3D sequencer scene workflow to switch scenes/cameras with a sequencer timeline.",
    "blender": (4, 0, 2),
    "version": (1, 0, 1),
    "location": "",
    "warning": "",
    "category": "Sequencer",
}


packages = (
    sync,
    shot,
    sequence,
    #render, #BFA - temporariliy removed
    #editorial, #BFA - temporariliy removed
    #shared_collections, #BFA - temporariliy removed
    preferences,
    #keymaps, #BFA - temporariliy removed
)


def register():
    for package in packages:
        package.register()


def unregister():
    for package in packages:
        package.unregister()
