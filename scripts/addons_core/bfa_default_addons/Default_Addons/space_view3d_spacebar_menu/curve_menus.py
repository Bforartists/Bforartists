# SPDX-FileCopyrightText: 2019-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

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
