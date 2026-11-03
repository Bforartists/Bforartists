# SPDX-FileCopyrightText: 2012-2025 Blender Foundation
#
# SPDX-License-Identifier: GPL-3.0-or-later

if "bpy" in locals():
    import importlib
    importlib.reload(add_curve_aceous_galore)
    importlib.reload(add_curve_spirals)
    importlib.reload(add_curve_torus_knots)
    importlib.reload(add_surface_plane_cone)
    importlib.reload(add_curve_curly)
    importlib.reload(beveltaper_curve)
    importlib.reload(add_curve_celtic_links)
    importlib.reload(add_curve_braid)
    importlib.reload(add_curve_simple)
    importlib.reload(add_curve_spirofit_bouncespline)
    importlib.reload(preferences)

else:
    from . import add_curve_aceous_galore
    from . import add_curve_spirals
    from . import add_curve_torus_knots
    from . import add_surface_plane_cone
    from . import add_curve_curly
    from . import beveltaper_curve
    from . import add_curve_celtic_links
    from . import add_curve_braid
    from . import add_curve_simple
    from . import add_curve_spirofit_bouncespline
    from . import preferences

import bpy
from bpy.types import Menu


class INFO_MT_curve_simple_add(Menu):
    bl_idname = "INFO_MT_curve_simple_add"
    bl_label = "Simple"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        add_curve_simple.menu(self, context)


class INFO_MT_curve_knots_add(Menu):
    # Define the "Extras" menu
    bl_idname = "INFO_MT_curve_knots_add"
    bl_label = "Plants"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.operator("curve.torus_knot_plus", text="Torus Knot Plus")
        layout.operator("curve.add_braid", text="Braid Knot")
        layout.operator("curve.celtic_links", text="Celtic Links")
        layout.operator("object.add_spirofit_spline", icon="FORCE_MAGNETIC")
        layout.operator("object.add_bounce_spline", icon="FORCE_HARMONIC")
        layout.operator("object.add_catenary_curve", icon="FORCE_CURVE")


# Define "Extras" menus
def menu_func(self, context):
    prefs = bpy.context.preferences.addons[__package__].preferences
    layout = self.layout

    layout.separator()
    if prefs.show_curly:
        layout.operator("curve.curlycurve", text="Curly", icon='GP_ONLY_SELECTED')
    if prefs.show_simple:
        layout.menu(INFO_MT_curve_simple_add.bl_idname, text='Simple', icon='CURVE_NCIRCLE')
    if prefs.show_profiles:
        layout.operator_menu_enum("curve.curveaceous_galore", "ProfileType", text='Profiles', icon='SURFACE_NCURVE')
    if prefs.show_spirals:
        layout.operator_menu_enum("curve.spirals", "spiral_type", text='Spirals', icon='FORCE_VORTEX')
    if context.mode != 'OBJECT':
        # fix in D2142 will allow to work in EDIT_CURVE
        return None
    if prefs.show_knots:
        layout.menu(INFO_MT_curve_knots_add.bl_idname, text="Knots", icon='FORCE_MAGNETIC')
    if prefs.show_bevel or prefs.show_taper:
        layout.separator()
    if prefs.show_bevel:
        layout.operator("curve.bevelcurve", icon='MOD_CURVE')
    if prefs.show_taper:
        layout.operator("curve.tapercurve", icon='MOD_CURVE')

def menu_surface(self, context):
    prefs = bpy.context.preferences.addons[__package__].preferences
    layout = self.layout

    if prefs.show_wedge or prefs.show_cone or prefs.show_star or prefs.show_plane:
        layout.separator()
    if context.mode == 'EDIT_SURFACE':
        layout.operator("curve.smooth_x_times", text="Special Smooth", icon="MOD_CURVE")
    elif context.mode == 'OBJECT':
        if prefs.show_wedge:
            layout.operator("object.add_surface_wedge", text="Wedge", icon="SURFACE_DATA")
        if prefs.show_cone:
            layout.operator("object.add_surface_cone", text="Cone", icon="SURFACE_DATA")
        if prefs.show_star:
            layout.operator("object.add_surface_star", text="Star", icon="SURFACE_DATA")
        if prefs.show_plane:
            layout.operator("object.add_surface_plane", text="Plane", icon="SURFACE_DATA")

# Register
classes = [
    preferences.CurveExtraObjectsAddonPreferences,
    INFO_MT_curve_knots_add,
    INFO_MT_curve_simple_add
]

def register():
    import os

    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    add_curve_simple.register()
    add_curve_spirals.register()
    add_curve_aceous_galore.register()
    add_curve_torus_knots.register()
    add_curve_braid.register()
    add_curve_celtic_links.register()
    add_curve_curly.register()
    add_curve_spirofit_bouncespline.register()
    add_surface_plane_cone.register()
    beveltaper_curve.register()

    # Add "Extras" menu to the "Add Curve" menu
    bpy.types.VIEW3D_MT_curve_add.append(menu_func)
    # Add "Extras" menu to the "Add Surface" menu
    bpy.types.VIEW3D_MT_surface_add.append(menu_surface)

    # Presets
    if register_preset_path := getattr(bpy.utils, "register_preset_path", None):
        register_preset_path(os.path.join(os.path.dirname(__file__)))


def unregister():
    import os

    # Remove "Extras" menu from the "Add Curve" menu.
    bpy.types.VIEW3D_MT_curve_add.remove(menu_func)
    # Remove "Extras" menu from the "Add Surface" menu.
    bpy.types.VIEW3D_MT_surface_add.remove(menu_surface)

    add_surface_plane_cone.unregister()
    add_curve_spirofit_bouncespline.unregister()
    add_curve_curly.unregister()
    add_curve_celtic_links.unregister()
    add_curve_braid.unregister()
    add_curve_torus_knots.unregister()
    add_curve_aceous_galore.unregister()
    add_curve_spirals.unregister()
    add_curve_simple.unregister()
    beveltaper_curve.unregister()

    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

    # Presets
    if unregister_preset_path := getattr(bpy.utils, "unregister_preset_path", None):
        unregister_preset_path(os.path.join(os.path.dirname(__file__)))

if __name__ == "__main__":
    register()
