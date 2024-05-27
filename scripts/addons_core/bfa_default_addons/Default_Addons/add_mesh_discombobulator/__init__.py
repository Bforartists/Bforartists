# SPDX-FileCopyrightText: 2010-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

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
