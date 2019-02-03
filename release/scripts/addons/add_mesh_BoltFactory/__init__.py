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
    "name": "BoltFactory",
    "author": "Aaron Keith",
    "version": (0, 4, 0),
    "blender":  (2, 80, 0),
    "location": "View3D > Add > Mesh",
    "description": "Add a bolt or nut",
    "wiki_url": "https://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/Add_Mesh/BoltFactory",
    "category": "Add Mesh",
}


if "bpy" in locals():
    import importlib
    importlib.reload(Boltfactory)
    importlib.reload(createMesh)
else:
    from . import Boltfactory
    from . import createMesh

import bpy


# ### REGISTER ###



def register():
	Boltfactory.register()
   


def unregister():
    Boltfactory.unregister()


if __name__ == "__main__":
    register()
