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
# Contributed to by: meta-androcto, JayDez, sim88, sam, lijenstina, mkb, wisaac, CoDEmanX #


import bpy
from bpy.types import (
        Operator,
        Menu,
        )
from bpy.props import (
        BoolProperty,
        StringProperty,
        )

from .object_menus import *


# ********** Edit Curve **********
class VIEW3D_MT_Edit_Curve(Menu):
    bl_label = "Curve"

    def draw(self, context):
        layout = self.layout

        toolsettings = context.tool_settings

        layout.operator_menu_enum("curve.spline_type_set", "type")
        layout.menu("VIEW3D_MT_mirror")
        layout.operator("curve.make_segment")
        layout.menu("VIEW3D_MT_edit_curve_segments")
        layout.separator()

        layout.operator("curve.duplicate_move")
        layout.operator("curve.split")
        layout.operator("curve.separate")
        layout.operator("curve.cyclic_toggle")
        layout.operator("curve.spin")
        layout.separator()

        layout.menu("VIEW3D_MT_edit_curve_showhide")
        layout.menu("VIEW3D_MT_edit_curve_clean")
        layout.separator()

#        layout.prop_menu_enum(toolsettings, "proportional_edit",
#                              icon="PROP_CON")
        layout.prop_menu_enum(toolsettings, "proportional_edit_falloff",
                              icon="SMOOTHCURVE")


# List The Classes #

classes = (
    VIEW3D_MT_Edit_Curve,
)


# Register Classes & Hotkeys #
def register():
    for cls in classes:
        bpy.utils.register_class(cls)


# Unregister Classes & Hotkeys #
def unregister():

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
