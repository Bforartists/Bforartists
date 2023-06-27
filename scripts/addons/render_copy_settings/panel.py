# SPDX-FileCopyrightText: 2011-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from . import presets
from . import data as data_types


class RENDER_UL_copy_settings(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        #assert(isinstance(item, (data_types.RenderCopySettingsScene, data_types.RenderCopySettingsDataSetting)))
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if isinstance(item, data_types.RenderCopySettingsDataSetting):
                layout.label(text=item.name, icon_value=icon)
                layout.prop(item, "copy", text="")
            else: #elif isinstance(item, data_types.RenderCopySettingsDataScene):
                layout.prop(item, "allowed", text=item.name, toggle=True)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            if isinstance(item, data_types.RenderCopySettingsDataSetting):
                layout.label(text=item.name, icon_value=icon)
                layout.prop(item, "copy", text="")
            else: #elif isinstance(item, data_types.RenderCopySettingsDataScene):
                layout.prop(item, "allowed", text=item.name, toggle=True)


class RENDER_PT_copy_settings(bpy.types.Panel):
    bl_label = "Copy Settings"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {'BLENDER_RENDER'}

    def draw(self, context):
        layout = self.layout
        cp_sett = context.scene.render_copy_settings

        layout.operator("scene.render_copy_settings", text="Copy Render Settings")

        split = layout.split(factor=0.75)
        split.template_list("RENDER_UL_copy_settings", "settings", cp_sett, "affected_settings",
                            cp_sett, "affected_settings_idx", rows=5)

        col = split.column()
        all_set = {sett.strid for sett in cp_sett.affected_settings if sett.copy}
        for p in presets.presets:
            label = ""
            if p.elements & all_set == p.elements:
                label = "Clear {}".format(p.ui_name)
            else:
                label = "Set {}".format(p.ui_name)
            col.operator("scene.render_copy_settings_preset", text=label).presets = {p.rna_enum[0]}

        layout.prop(cp_sett, "filter_scene")
        if len(cp_sett.allowed_scenes):
            layout.label(text="Affected Scenes:")
            layout.template_list("RENDER_UL_copy_settings", "scenes", cp_sett, "allowed_scenes",
#                                 cp_sett, "allowed_scenes_idx", rows=6, type='GRID')
                                 cp_sett, "allowed_scenes_idx", rows=6) # XXX Grid is not nice currently...
        else:
            layout.label(text="No Affectable Scenes!", icon="ERROR")


classes = (
    RENDER_UL_copy_settings,
    RENDER_PT_copy_settings,
)
