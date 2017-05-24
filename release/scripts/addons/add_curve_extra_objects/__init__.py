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
    "blender": (2, 76, 0),
    "location": "View3D > Add > Curve > Extra Objects",
    "description": "Add extra curve object types",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/Curve/Curve_Objects",
    "category": "Add Curve"
    }

if "bpy" in locals():
    import importlib
    importlib.reload(add_curve_aceous_galore)
    importlib.reload(add_curve_spirals)
    importlib.reload(add_curve_torus_knots)
    importlib.reload(add_surface_plane_cone)

else:
    from . import add_curve_aceous_galore
    from . import add_curve_spirals
    from . import add_curve_torus_knots
    from . import add_surface_plane_cone

import bpy
from bpy.types import Menu, AddonPreferences
from bpy.props import StringProperty, IntProperty, BoolProperty

def convert_old_presets(data_path, msg_data_path, old_preset_subdir, new_preset_subdir, fixdic={}, ext=".py"):
    ''' convert old presets '''

    def convert_presets(self, context):
        if not getattr(self, data_path, False):
            return None
        import os

        target_path = os.path.join("presets", old_preset_subdir)
        target_path = bpy.utils.user_resource('SCRIPTS',
                                              target_path)

        # created an anytype op to run against preset
        op = type('', (), {})()

        files = [f for f in os.listdir(target_path) if f.endswith(ext)]
        if not files:
            print("No old presets in %s" % target_path)
            setattr(self, msg_data_path, "No old presets")
            return None

        new_target_path = os.path.join("presets", new_preset_subdir)
        new_target_path = bpy.utils.user_resource('SCRIPTS',
                                              new_target_path,
                                              create=True)
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


class CurveExtraObjectsAddonPreferences(AddonPreferences):
    bl_idname = __name__

    spiral_fixdic = {"spiral_type": ['ARCH', 'ARCH', 'LOG', 'SPHERE', 'TORUS'],
              "curve_type": ['POLY', 'NURBS'],
              "spiral_direction": ['COUNTER_CLOCKWISE', 'CLOCKWISE']
                     }
    update_spiral_presets_msg = StringProperty(default="Nothing to do")
    update_spiral_presets = BoolProperty(
            name="Update Old Presets",
            description="Update presets to reflect data changes",
            default=False,
            update=convert_old_presets("update_spiral_presets",  # this props name
                                       "update_spiral_presets_msg",  # message prop
                                       "operator/curve.spirals",
                                       "curve_extras/curve.spirals",
                                       fixdic=spiral_fixdic)
            )

    def draw(self, context):
        layout = self.layout
        layout.label(text="Spirals")
        if self.update_spiral_presets:
            layout.label(self.update_spiral_presets_msg, icon='FILE_TICK')
        else:
            layout.prop(self, "update_spiral_presets")


# TODO check if this is even used.
class INFO_MT_curve_extras_add(Menu):
    # Define the "Extras" menu
    bl_idname = "curve_extra_objects_add"
    bl_label = "Extra Objects"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator_menu_enum("mesh.curveaceous_galore",
                             "ProfileType",
                            )
        layout.operator_menu_enum("curve.spirals",
                             "spiral_type",
                             icon='FORCE_VORTEX')
        layout.operator("curve.torus_knot_plus",
            text="Torus Knot Plus")

# Define "Extras" menus
def menu_func(self, context):
    if context.mode != 'OBJECT':
        # fix in D2142 will allow to work in EDIT_CURVE
        return None
    layout = self.layout
    layout.separator()
    layout.operator_menu_enum("mesh.curveaceous_galore",
                         "ProfileType",
                        )
    layout.operator_menu_enum("curve.spirals",
                         "spiral_type",
                          icon='FORCE_VORTEX')
    layout.operator("curve.torus_knot_plus", text="Torus Knot Plus")

def menu_surface(self, context):
    layout = self.layout
    self.layout.separator()
    if context.mode == 'EDIT_SURFACE':
        self.layout.operator("curve.smooth_x_times", text="Special Smooth", icon="MOD_CURVE")
    elif context.mode == 'OBJECT':
        self.layout.operator("object.add_surface_wedge", text="Wedge", icon="MOD_CURVE")
        self.layout.operator("object.add_surface_cone", text="Cone", icon="MOD_CURVE")
        self.layout.operator("object.add_surface_star", text="Star", icon="MOD_CURVE")
        self.layout.operator("object.add_surface_plane", text="Plane", icon="MOD_CURVE")

def register():
    bpy.utils.register_module(__name__)

    # Add "Extras" menu to the "Add Curve" menu
    bpy.types.INFO_MT_curve_add.append(menu_func)
    # Add "Extras" menu to the "Add Surface" menu
    bpy.types.INFO_MT_surface_add.append(menu_surface)

def unregister():
    bpy.utils.unregister_module(__name__)

    # Remove "Extras" menu from the "Add Curve" menu.
    bpy.types.INFO_MT_curve_add.remove(menu_func)
    # Remove "Extras" menu from the "Add Surface" menu.
    bpy.types.INFO_MT_surface_add.remove(menu_surface)

if __name__ == "__main__":
    register()
