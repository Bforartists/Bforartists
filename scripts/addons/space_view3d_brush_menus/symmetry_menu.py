# SPDX-FileCopyrightText: 2017-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.types import Menu
from . import utils_core


class MasterSymmetryMenu(Menu):
    bl_label = "Symmetry Options"
    bl_idname = "VIEW3D_MT_sv3_master_symmetry_menu"

    @classmethod
    def poll(self, context):
        return utils_core.get_mode() in (
                        'SCULPT',
                        'VERTEX_PAINT',
                        'WEIGHT_PAINT',
                        'TEXTURE_PAINT',
                        'PARTICLE_EDIT',
                        )

    def draw(self, context):
        layout = self.layout

        if utils_core.get_mode() == 'PARTICLE_EDIT':
            layout.row().prop(context.active_object.data, "use_mirror_x",
                              text="Mirror X", toggle=True)

        elif utils_core.get_mode() == 'TEXTURE_PAINT':
            layout.row().prop(context.active_object, "use_mesh_mirror_x",
                              text="Symmetry X", toggle=True)
            layout.row().prop(context.active_object, "use_mesh_mirror_y",
                              text="Symmetry Y", toggle=True)
            layout.row().prop(context.active_object, "use_mesh_mirror_z",
                              text="Symmetry Z", toggle=True)
        else:
            layout.row().menu(SymmetryMenu.bl_idname)
            layout.row().menu(SymmetryRadialMenu.bl_idname)

            if utils_core.get_mode() == 'SCULPT':
                layout.row().prop(context.tool_settings.sculpt, "use_symmetry_feather",
                                  toggle=True)


class SymmetryMenu(Menu):
    bl_label = "Symmetry"
    bl_idname = "VIEW3D_MT_sv3_symmetry_menu"

    def draw(self, context):
        layout = self.layout

        layout.row().label(text="Symmetry")
        layout.row().separator()

        layout.row().prop(context.active_object, "use_mesh_mirror_x",
                          text="Symmetry X", toggle=True)
        layout.row().prop(context.active_object, "use_mesh_mirror_y",
                          text="Symmetry Y", toggle=True)
        layout.row().prop(context.active_object, "use_mesh_mirror_z",
                          text="Symmetry Z", toggle=True)


class SymmetryRadialMenu(Menu):
    bl_label = "Radial"
    bl_idname = "VIEW3D_MT_sv3_symmetry_radial_menu"

    def draw(self, context):
        layout = self.layout

        layout.row().label(text="Radial")
        layout.row().separator()

        mode_tool_settings = getattr(context.tool_settings, utils_core.get_mode().lower())

        layout.column().prop(mode_tool_settings, "radial_symmetry", text="", slider=True)


classes = (
    MasterSymmetryMenu,
    SymmetryMenu,
    SymmetryRadialMenu
    )

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
