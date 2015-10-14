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
# testscreenings, Alejandro Omar Chocano Vasquez, Jimmy Hazevoet, meta-androcto #

bl_info = {
    "name": "Extra Objects",
    "author": "Multiple Authors",
    "version": (0, 1),
    "blender": (2, 63, 0),
    "location": "View3D > Add > Curve > Extra Objects",
    "description": "Add extra curve object types",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/Curve/Curve_Objects",
    "category": "Add Curve"}

if "bpy" in locals():
    import imp
    imp.reload(add_curve_aceous_galore)
    imp.reload(add_curve_spirals)
    imp.reload(add_curve_torus_knots)

else:
    from . import add_curve_aceous_galore
    from . import add_curve_spirals
    from . import add_curve_torus_knots

import bpy

class INFO_MT_curve_extras_add(bpy.types.Menu):
    # Define the "Extras" menu
    bl_idname = "curve_extra_objects_add"
    bl_label = "Extra Objects"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("mesh.curveaceous_galore",
            text="Curves Galore!")
        layout.operator("curve.spirals",
            text="Spirals")
        layout.operator("curve.torus_knot_plus",
            text="Torus Knot Plus")
# Define "Extras" menu
def menu_func(self, context):
    self.layout.operator("mesh.curveaceous_galore",
            text="Curves Galore!")
    self.layout.operator("curve.torus_knot_plus",
            text="Torus Knot Plus")
    self.layout.operator("curve.spirals",
            text="Spirals")

def register():
    bpy.utils.register_module(__name__)

    # Add "Extras" menu to the "Add Curve" menu
    bpy.types.INFO_MT_curve_add.append(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)

    # Remove "Extras" menu from the "Add Curve" menu.
    bpy.types.INFO_MT_curve_add.remove(menu_func)

if __name__ == "__main__":
    register()
