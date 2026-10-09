# SPDX-FileCopyrightText: 2012-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.types import AddonPreferences
from bpy.props import BoolProperty


class CurveExtraObjectsAddonPreferences(AddonPreferences):
    bl_idname = __package__

    show_menu_list: BoolProperty(
            name="Menu List",
            description="Show/Hide the Add Menu items",
            default=True
            )
    
    show_curly: BoolProperty(
            name="Curly Curve",
            description="Show Curly Curve in the Curve Add menu",
            default=True
            )
    show_simple: BoolProperty(
            name="Simple Menu",
            description="Show Simple Menu in the Curve Add menu",
            default=True
            )
    show_profiles: BoolProperty(
            name="Profiles Menu",
            description="Show Simple Menu in the Curve Add menu",
            default=True
            )
    show_spirals: BoolProperty(
            name="Spirals Menu",
            description="Show Spirals Menu in the Curve Add menu",
            default=True
            )
    show_knots: BoolProperty(
            name="Knots Menu",
            description="Show Knots Menu in the Curve Add menu",
            default=True
            )
    show_bevel: BoolProperty(
            name="As Bevel",
            description="Show Add As Bevel in the Curve Add menu",
            default=True
            )
    show_taper: BoolProperty(
            name="As Taper",
            description="Show Add As Taper in the Curve Add menu",
            default=True
            )
    show_wedge: BoolProperty(
            name="Wedge",
            description="Show Wedge in the Surface Add menu",
            default=True
            )
    show_cone: BoolProperty(
            name="Cone",
            description="Show Cone in the Surface Add menu",
            default=True
            )
    show_star: BoolProperty(
            name="Star",
            description="Show Star in the Surface Add menu",
            default=True
            )
    show_plane: BoolProperty(
            name="Plane",
            description="Show Plane in the Surface Add menu",
            default=True
            )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.label(text="Filter Add Menus")

        grid = layout.grid_flow(even_columns=True, even_rows=False)

        col = grid.column(heading="Curve")
        col.prop(self, 'show_curly')
        col.prop(self, 'show_simple')
        col.prop(self, 'show_profiles')
        col.prop(self, 'show_spirals')
        col.prop(self, 'show_knots')
        col.prop(self, 'show_bevel')
        col.prop(self, 'show_taper')
        col.separator()
        
        col = grid.column(heading="Surface")
        col.prop(self, 'show_wedge')
        col.prop(self, 'show_cone')
        col.prop(self, 'show_star')
        col.prop(self, 'show_plane')
