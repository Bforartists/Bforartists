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

        layout.operator("curve.extrude_move")
        layout.operator("curve.spin")
        layout.operator("curve.duplicate_move")
        layout.operator("curve.split")
        layout.operator("curve.separate")
        layout.operator("curve.make_segment")
        layout.operator("curve.cyclic_toggle")
        layout.separator()
        layout.operator("curve.delete", text="Delete...")
        layout.separator()
        layout.menu("VIEW3D_MT_edit_curve_segments")
#        layout.prop_menu_enum(toolsettings, "proportional_edit",
#                              icon="PROP_CON")
        layout.prop_menu_enum(toolsettings, "proportional_edit_falloff",
                              icon="SMOOTHCURVE")
        layout.menu("VIEW3D_MT_edit_curve_showhide")


class VIEW3D_MT_EditCurveCtrlpoints(Menu):
    bl_label = "Control Points"

    def draw(self, context):
        layout = self.layout

        edit_object = context.edit_object

        if edit_object.type == 'CURVE':
            layout.operator("transform.transform").mode = 'TILT'
            layout.operator("curve.tilt_clear")
            layout.operator("curve.separate")
            layout.operator_menu_enum("curve.handle_type_set", "type")
            layout.menu("VIEW3D_MT_hook")


class VIEW3D_MT_EditCurveSegments(Menu):
    bl_label = "Curve Segments"

    def draw(self, context):
        layout = self.layout
        layout.operator("curve.subdivide")
        layout.operator("curve.switch_direction")


class VIEW3D_MT_EditCurveSpecials(Menu):
    bl_label = "Specials"

    def draw(self, context):
        layout = self.layout
        layout.operator("curve.subdivide")
        layout.separator()
        layout.operator("curve.switch_direction")
        layout.operator("curve.spline_weight_set")
        layout.operator("curve.radius_set")
        layout.separator()
        layout.operator("curve.smooth")
        layout.operator("curve.smooth_weight")
        layout.operator("curve.smooth_radius")
        layout.operator("curve.smooth_tilt")


# List The Classes #

classes = (
    VIEW3D_MT_Edit_Curve,
    VIEW3D_MT_EditCurveCtrlpoints,
    VIEW3D_MT_EditCurveSegments,
    VIEW3D_MT_EditCurveSpecials,
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
