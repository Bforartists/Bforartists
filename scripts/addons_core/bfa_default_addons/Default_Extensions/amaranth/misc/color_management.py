# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
Color Management Presets

Save your Color Management options as presets, for easy re-use.

It will pretty much every option in the Color Management panel, such as
the look, color settings, and so on. Except the curve points (have to
figure out how to do that nicely), good news is that in Blender 2.69+ you
can now copy/paste curves.
"""

import bpy
from bl_operators.presets import AddPresetBase


class AMTH_SCENE_MT_color_management_presets(bpy.types.Menu):

    """List of Color Management presets"""
    bl_label = "Color Management Presets"
    preset_subdir = "color"
    preset_operator = "script.execute_preset"
    draw = bpy.types.Menu.draw_preset


class AMTH_AddPresetColorManagement(AddPresetBase, bpy.types.Operator):

    """Add or remove a Color Management preset"""
    bl_idname = "scene.color_management_preset_add"
    bl_label = "Add Color Management Preset"
    preset_menu = "AMTH_SCENE_MT_color_management_presets"

    preset_defines = [
        "scene = bpy.context.scene",
    ]

    preset_values = [
        "scene.view_settings.view_transform",
        "scene.display_settings.display_device",
        "scene.view_settings.exposure",
        "scene.view_settings.gamma",
        "scene.view_settings.look",
        "scene.view_settings.use_curve_mapping",
        "scene.sequencer_colorspace_settings.name",
    ]

    preset_subdir = "color"


def ui_color_management_presets(self, context):

    layout = self.layout

    row = layout.row(align=True)
    row.menu("AMTH_SCENE_MT_color_management_presets",
             text=bpy.types.AMTH_SCENE_MT_color_management_presets.bl_label)
    row.operator("scene.color_management_preset_add", text="", icon="ZOOM_IN")
    row.operator("scene.color_management_preset_add",
                 text="", icon="ZOOM_OUT").remove_active = True
    layout.separator()


def register():
    bpy.utils.register_class(AMTH_AddPresetColorManagement)
    bpy.utils.register_class(AMTH_SCENE_MT_color_management_presets)
    bpy.types.RENDER_PT_color_management.prepend(ui_color_management_presets)


def unregister():
    bpy.utils.unregister_class(AMTH_AddPresetColorManagement)
    bpy.utils.unregister_class(AMTH_SCENE_MT_color_management_presets)
    bpy.types.RENDER_PT_color_management.remove(ui_color_management_presets)
