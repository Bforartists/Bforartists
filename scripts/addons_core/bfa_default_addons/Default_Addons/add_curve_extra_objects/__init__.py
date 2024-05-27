# SPDX-FileCopyrightText: 2012-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Extra Objects",
    "author": "Multiple Authors",
    "version": (0, 1, 5),
    "blender": (2, 93, 0),
    "location": "View3D > Add > Curve > Extra Objects",
    "description": "Add extra curve object types",
    "warning": "",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/add_curve/extra_objects.html",
    "category": "Add Curve",
}

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

import bpy
from bpy.types import (
        Menu,
        AddonPreferences,
        )
from bpy.props import (
        StringProperty,
        BoolProperty,
        )


def convert_old_presets(data_path, msg_data_path, old_preset_subdir,
                        new_preset_subdir, fixdic={}, ext=".py"):
    """
    convert old presets
    """

    def convert_presets(self, context):
        if not getattr(self, data_path, False):
            return None
        import os

        target_path = os.path.join("presets", old_preset_subdir)
        target_path = bpy.utils.user_resource('SCRIPTS', path=target_path)

        # created an anytype op to run against preset
        op = type('', (), {})()

        files = [f for f in os.listdir(target_path) if f.endswith(ext)]
        if not files:
            print("No old presets in %s" % target_path)
            setattr(self, msg_data_path, "No old presets")
            return None

        new_target_path = os.path.join("presets", new_preset_subdir)
        new_target_path = bpy.utils.user_resource('SCRIPTS', path=new_target_path, create=True)
        for f in files:
            file = open(os.path.join(target_path, f))
            for line in file:
                if line.startswith("op."):
                    exec(line)
            file.close()
            for key, items in fixdic.items():
                if hasattr(op, key) and isinstance(getattr(op, key), int):
                    setattr(op, key, items[getattr(op, key)])
            # create a new one
            new_file_path = os.path.join(new_target_path, f)
            if os.path.isfile(new_file_path):
                # do nothing
                print("Preset %s already exists, passing..." % f)
                continue
            file_preset = open(new_file_path, 'w')
            file_preset.write("import bpy\n")
            file_preset.write("op = bpy.context.active_operator\n")

            for prop, value in vars(op).items():
                if isinstance(value, str):
                    file_preset.write("op.%s = '%s'\n" % (prop, str(value)))
                else:
                    file_preset.write("op.%s = %s\n" % (prop, str(value)))
            file_preset.close()
            print("Writing new preset to %s" % new_file_path)

        setattr(self, msg_data_path, "Converted %d old presets" % len(files))
        return None

    return convert_presets


# Addons Preferences

class CurveExtraObjectsAddonPreferences(AddonPreferences):
    bl_idname = __name__

    spiral_fixdic = {
            "spiral_type": ['ARCH', 'ARCH', 'LOG', 'SPHERE', 'TORUS'],
            "curve_type": ['POLY', 'NURBS'],
            "spiral_direction": ['COUNTER_CLOCKWISE', 'CLOCKWISE']
            }
    update_spiral_presets_msg : StringProperty(
            default="Nothing to do"
            )
    update_spiral_presets : BoolProperty(
            name="Update Old Presets",
            description="Update presets to reflect data changes",
            default=False,
            update=convert_old_presets(
                    "update_spiral_presets",  # this props name
                    "update_spiral_presets_msg",  # message prop
                    "operator/curve.spirals",
                    "curve_extras/curve.spirals",
                    fixdic=spiral_fixdic
                    )
            )
    show_menu_list : BoolProperty(
            name="Menu List",
            description="Show/Hide the Add Menu items",
            default=False
            )

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text="Spirals:")

        if self.update_spiral_presets:
            box.label(text=self.update_spiral_presets_msg, icon="FILE_TICK")
        else:
            box.prop(self, "update_spiral_presets")

        icon_1 = "TRIA_RIGHT" if not self.show_menu_list else "TRIA_DOWN"
        box = layout.box()
        box.prop(self, "show_menu_list", emboss=False, icon=icon_1)

        if self.show_menu_list:
            box.label(text="Items located in the Add Menu > Curve (default shortcut Ctrl + A):",
                      icon="LAYER_USED")
            box.label(text="2D Objects:", icon="LAYER_ACTIVE")
            box.label(text="Angle, Arc, Circle, Distance, Ellipse, Line, Point, Polygon,",
                      icon="LAYER_USED")
            box.label(text="Polygon ab, Rectangle, Rhomb, Sector, Segment, Trapezoid",
                      icon="LAYER_USED")
            box.label(text="Curve Profiles:", icon="LAYER_ACTIVE")
            box.label(text="Arc, Arrow, Cogwheel, Cycloid, Flower, Helix (3D),",
                      icon="LAYER_USED")
            box.label(text="Noise (3D), Nsided, Profile, Rectangle, Splat, Star",
                      icon="LAYER_USED")
            box.label(text="Curve Spirals:", icon="LAYER_ACTIVE")
            box.label(text="Archemedian, Logarithmic, Spheric, Torus",
                      icon="LAYER_USED")
            box.label(text="Knots:", icon="LAYER_ACTIVE")
            box.label(text="Torus Knots Plus, Celtic Links, Braid Knot",
                      icon="LAYER_USED")
            box.label(text="SpiroFit, Bounce Spline, Catenary", icon="LAYER_USED")
            box.label(text="Curly Curve", icon="LAYER_ACTIVE")
            box.label(text="Bevel/Taper:", icon="LAYER_ACTIVE")
            box.label(text="Add Curve as Bevel, Add Curve as Taper",
                      icon="LAYER_USED")
            box.label(text="Simple Curve:", icon="LAYER_ACTIVE")
            box.label(text="Available if the Active Object is a Curve was created with 2D Objects",
                     icon="LAYER_USED")

            box.label(text="Items located in the Add Menu > Surface (default shortcut Ctrl + A):",
                      icon="LAYER_USED")
            box.label(text="Wedge, Cone, Star, Plane",
                      icon="LAYER_ACTIVE")


class INFO_MT_curve_knots_add(Menu):
    # Define the "Extras" menu
    bl_idname = "INFO_MT_curve_knots_add"
    bl_label = "Plants"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.operator("curve.torus_knot_plus", text="Torus Knot Plus")
        layout.operator("curve.celtic_links", text="Celtic Links")
        layout.operator("curve.add_braid", text="Braid Knot")
        layout.operator("object.add_spirofit_spline", icon="FORCE_MAGNETIC")
        layout.operator("object.add_bounce_spline", icon="FORCE_HARMONIC")
        layout.operator("object.add_catenary_curve", icon="FORCE_CURVE")


# Define "Extras" menus
def menu_func(self, context):
    layout = self.layout

    layout.operator_menu_enum("curve.curveaceous_galore", "ProfileType", icon='CURVE_DATA')
    layout.operator_menu_enum("curve.spirals", "spiral_type", icon='FORCE_VORTEX')
    layout.separator()
    layout.operator("curve.curlycurve", text="Curly Curve", icon='GP_ONLY_SELECTED')
    if context.mode != 'OBJECT':
        # fix in D2142 will allow to work in EDIT_CURVE
        return None
    layout.separator()
    layout.menu(INFO_MT_curve_knots_add.bl_idname, text="Knots", icon='CURVE_DATA')
    layout.separator()
    layout.operator("curve.bevelcurve")
    layout.operator("curve.tapercurve")
    layout.operator("curve.simple")

def menu_surface(self, context):
    self.layout.separator()
    if context.mode == 'EDIT_SURFACE':
        self.layout.operator("curve.smooth_x_times", text="Special Smooth", icon="MOD_CURVE")
    elif context.mode == 'OBJECT':
        self.layout.operator("object.add_surface_wedge", text="Wedge", icon="SURFACE_DATA")
        self.layout.operator("object.add_surface_cone", text="Cone", icon="SURFACE_DATA")
        self.layout.operator("object.add_surface_star", text="Star", icon="SURFACE_DATA")
        self.layout.operator("object.add_surface_plane", text="Plane", icon="SURFACE_DATA")

# Register
classes = [
    CurveExtraObjectsAddonPreferences,
    INFO_MT_curve_knots_add
]

def register():
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


def unregister():
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

if __name__ == "__main__":
    register()
