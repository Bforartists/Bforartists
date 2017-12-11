# #########################################################################
# ***** BEGIN GPL LICENSE BLOCK *****
#
# This is free software under the terms of the GNU General Public License
# you may redistribute it, and/or modify it.
#
# This code is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License (http://www.gnu.org/licenses/) for more details.
#
# ***** END GPL LICENSE BLOCK *****
'''
Create block wall "Castle" style with extended features.
'''
#
# This collection of scripts has been contributed to by many authors,
# see documentation "Credits" for details.
#
# #########################################################################

bl_info = {
    "name": "Castle",
    "description": "Create a Castle",
    "author": "See documentation Credits",
    "version": (0, 0, 4),
    "blender": (2, 75, 0),
    "location": "View3D > Add > Mesh > Castle",
    "warning": "WIP - Frequent changes for known issues and enhancements",
    "support": "TESTING",
    "wiki_url": "https://wiki.blender.org/index.php/Extensions:2.6"
                "/Py/Scripts/Add_Mesh/Castle",
    "tracker_url": "https://developer.blender.org/T45596",
    "category": "Add Mesh"
}


if "bpy" in locals():
    import importlib
    importlib.reload(Castle)
else:
    from . import Castle

import bpy
from .Castle import (
        add_castle,
        )


# Menu
def menu_func_castle(self, context):
    self.layout.operator(add_castle.bl_idname, text="Castle",
                         icon="PLUGIN")


# This is needed to prevent the module defines no classes error
classes = (
    add_castle,
    )


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.INFO_MT_mesh_add.append(menu_func_castle)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    bpy.types.INFO_MT_mesh_add.remove(menu_func_castle)


if __name__ == "__main__":
    register()
