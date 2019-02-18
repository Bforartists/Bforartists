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
    "name": "Geodesic Domes2",
    "author": "Noctumsolis, PKHG, Meta Androcto, Andy Houston",
    "version": (0, 3, 3),
    "blender": (2, 80, 0),
    "location": "View3D > Add > Mesh",
    "description": "Create geodesic dome type objects.",
    "warning": "",
    "wiki_url": "https://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Modeling/Geodesic_Domes",
    "tracker_url": "",
    "category": "Add Mesh"}

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

# Define "Extras" menu
def menu_func(self, context):
    lay_out = self.layout
    lay_out.operator_context = 'INVOKE_REGION_WIN'

    lay_out.separator()
    lay_out.operator("mesh.generate_geodesic_dome",
                    text="Geodesic Dome")

# Register
classes = [
    add_shape_geodesic.add_corrective_pose_shape_fast,
    third_domes_panel_271.GenerateGeodesicDome,
    third_domes_panel_271.DialogOperator,
]

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    # Add "Extras" menu to the "Add Mesh" menu
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)


def unregister():
    # Remove "Extras" menu from the "Add Mesh" menu.
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)

    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

if __name__ == "__main__":
    register()
