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
# Contributed to by
# SAYproductions, meta-androcto, jambay, brikbot#

bl_info = {
    "name": "Building Objects",
    "author": "Multiple Authors",
    "version": (0, 2),
    "blender": (2, 71, 0),
    "location": "View3D > Add > Mesh > Cad Objects",
    "description": "Add building object types",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "https://developer.blender.org/T32711",
    "category": "Add Mesh"}


if "bpy" in locals():
    import imp
    imp.reload(add_mesh_balcony)
    imp.reload(add_mesh_sove)
    imp.reload(add_mesh_window)
    imp.reload(add_mesh_beam_builder)
    imp.reload(Wallfactory)
    imp.reload(stairbuilder)

else:
    from . import add_mesh_balcony
    from . import add_mesh_sove
    from . import add_mesh_window
    from . import add_mesh_beam_builder
    from . import Wallfactory
    from . import stairbuilder

import bpy


class INFO_MT_mesh_objects_add(bpy.types.Menu):
    # Define the "mesh objects" menu
    bl_idname = "INFO_MT_cad_objects_add"
    bl_label = "Building Objects"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.menu("INFO_MT_mesh_beambuilder_add",
            text="Beam Builder")
        layout.operator("mesh.add_say3d_balcony",
            text="Balcony")
        layout.operator("mesh.add_say3d_sove",
            text="Sove")
        layout.operator("mesh.add_say3d_pencere2",
            text="Window")
        layout.operator("mesh.wall_add",
            text="Wall Factory")
        layout.operator("mesh.stairs",
            text="Stair Builder")


# Register all operators and panels

# Define "Extras" menu
def menu_func(self, context):
    self.layout.menu("INFO_MT_cad_objects_add", icon="PLUGIN")


def register():
    bpy.utils.register_module(__name__)

    # Add "Extras" menu to the "Add Mesh" menu
    bpy.types.INFO_MT_mesh_add.append(menu_func)


def unregister():
    bpy.utils.unregister_module(__name__)

    # Remove "Extras" menu from the "Add Mesh" menu.
    bpy.types.INFO_MT_mesh_add.remove(menu_func)

if __name__ == "__main__":
    register()
