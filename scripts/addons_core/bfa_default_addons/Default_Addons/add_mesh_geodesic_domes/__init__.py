# SPDX-FileCopyrightText: 2010-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

# Contributed to by PKHG, Meta Androcto, Noctumsolis, Lijenstina,
# Spivak Vladimir (cwolf3d)
# Origunally an addon by Andy Houston

bl_info = {
    "name": "Geodesic Domes",
    "author": "Andy Houston",
    "version": (0, 3, 6),
    "blender": (2, 80, 0),
    "location": "View3D > Add > Mesh",
    "description": "Create geodesic dome type objects.",
    "warning": "",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/add_mesh/geodesic_domes.html",
    "category": "Add Mesh",
}

if "bpy" in locals():
    import importlib
    importlib.reload(add_shape_geodesic)
    importlib.reload(forms_271)
    importlib.reload(geodesic_classes_271)
    importlib.reload(third_domes_panel_271)
    importlib.reload(vefm_271)

else:
    from . import add_shape_geodesic
    from . import forms_271
    from . import geodesic_classes_271
    from . import third_domes_panel_271
    from . import vefm_271

import bpy

def Geodesic_contex_menu(self, context):
    bl_label = 'Change'

    obj = context.object
    layout = self.layout

    if obj.data is not None and 'GeodesicDome' in obj.data.keys():
        props = layout.operator("mesh.generate_geodesic_dome", text="Change Geodesic Dome")
        props.change = True
        for prm in third_domes_panel_271.GeodesicDomeParameters():
            setattr(props, prm, obj.data[prm])
        layout.separator()

# Define "Extras" menu
def menu_func(self, context):
    lay_out = self.layout
    lay_out.operator_context = 'INVOKE_REGION_WIN'

    lay_out.separator()
    oper = lay_out.operator("mesh.generate_geodesic_dome",
                    text="Geodesic Dome", icon="MESH_ICOSPHERE")
    oper.change = False

# Register
classes = [
    add_shape_geodesic.add_pose_shape_fast,
    third_domes_panel_271.GenerateGeodesicDome,
    third_domes_panel_271.DialogOperator,
]

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    # Add "Extras" menu to the "Add Mesh" menu
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)
    bpy.types.VIEW3D_MT_object_context_menu.prepend(Geodesic_contex_menu)


def unregister():
    # Remove "Extras" menu from the "Add Mesh" menu.
    bpy.types.VIEW3D_MT_object_context_menu.remove(Geodesic_contex_menu)
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)

    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

if __name__ == "__main__":
    register()
