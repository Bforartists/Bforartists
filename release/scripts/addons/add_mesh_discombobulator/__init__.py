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
# Contributed to by: Chichiri, Jace Priester #
# codemanx, blender dev team, Lijenstina, Spivak Vladimir (cwolf3d) #
# Originally by Evan J. Rosky (syrux)

bl_info = {
    "name": "Discombobulator",
    "author": "Evan J. Rosky (syrux)",
    "version": (0, 1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Add > Mesh",
    "description": "Add Discombobulator",
    "warning": "",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/add_mesh/discombobulator.html",
    "category": "Add Mesh",
}

# Note: Blocks has to be loaded before the WallFactory or the script
#       will not work properly after (F8) reload

if "bpy" in locals():
    import importlib
    importlib.reload(mesh_discombobulator)
else:
    from . import mesh_discombobulator

import bpy
from bpy.types import (
                Menu,
                PropertyGroup,
                )
from bpy.props import (
                PointerProperty,
                )

# Register all operators and panels

# Define "Extras" menu
def menu_func(self, context):
    layout = self.layout
    layout.operator_context = 'INVOKE_REGION_WIN'

    layout.separator()
    layout.operator("discombobulate.ops",
                    text="Discombobulator", icon="MOD_BUILD")


# Properties
class DISCProps(PropertyGroup):
    DISC_doodads = []

# Register
classes = (
    mesh_discombobulator.discombobulator,
    mesh_discombobulator.discombobulator_dodads_list,
    mesh_discombobulator.discombob_help,
    mesh_discombobulator.VIEW3D_OT_tools_discombobulate,
    mesh_discombobulator.chooseDoodad,
    mesh_discombobulator.unchooseDoodad,
    DISCProps
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.discombobulator = PointerProperty(type=DISCProps)
    # Add "Extras" menu to the "Add Mesh" menu
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)


def unregister():
    # Remove "Extras" menu from the "Add Mesh" menu.
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)

    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

    del bpy.types.Scene.discombobulator

if __name__ == "__main__":
    register()
