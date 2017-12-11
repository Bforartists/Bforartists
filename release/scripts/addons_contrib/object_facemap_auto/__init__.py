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

# <pep8 compliant>

bl_info = {
    "name": "Auto Face Map Widgets",
    "author": "Campbell Barton",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D",
    "description": "Use face-maps in the 3D view when rigged meshes are selected.",
    "warning": "This is currently a proof of concept.",
    "wiki_url": "",
    "category": "Rigging",
}

submodules = (
    "auto_fmap_widgets",
    "auto_fmap_ops",
)

# reload at runtime, for development.
USE_RELOAD = True
USE_VERBOSE = False

from bpy.utils import register_submodule_factory

register, unregister = register_submodule_factory(__name__, submodules)

if __name__ == "__main__":
    register()
