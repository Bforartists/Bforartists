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
    "name": "BFA - Classic Modifier Menu",
    "author": "Quackers",
    "description": "Addon for restoring the pre-4.0 style of the 'Add Modifiers' menu in the Properties Editor\nAdditionally adds extra UX to the add menus.",
    "blender": (4, 0, 0),
    "version" : (1, 1, 0),
    "location": "Properties",
    "category": "Interface",
}

from . import operators, ui, keymaps, prefs 
modules = (operators, ui, keymaps, prefs,)


def register():
    for module in modules:
        module.register()


def unregister():
    for module in modules:
        module.unregister()


if __name__ == "__main__":
    register()
