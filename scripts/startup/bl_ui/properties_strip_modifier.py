# SPDX-FileCopyrightText: 2009-2023 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy # BFA

from bpy.types import (
    Menu,
    Operator,
    Panel,
)

from bl_ui.generic_column_menu import InvokeMenuOperator


class StripModButtonsPanel:
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "strip_modifier"

    @classmethod
    def poll(cls, context):
        return context.active_strip is not None


# BFA - Modifier Assets
class SEQUENCER_MT_modifier_add_assets(Menu):
    bl_label = "Assets"
    bl_description = "Add a modifier nodegroup to the strip"
    bl_options = {'SEARCH_ON_KEY_PRESS'}

    def draw(self, context):
        layout = self.layout

        if layout.operator_context == 'EXEC_REGION_WIN':
            layout.operator_context = 'INVOKE_REGION_WIN'
            layout.operator(
                "wm.search_single_menu", text="Search...", icon="VIEWZOOM"
            ).menu_idname = self.bl_idname
            layout.separator()

        layout.operator_context = 'EXEC_REGION_WIN'
        layout.menu_contents("SEQUENCER_MT_modifier_add_root_catalogs")


# BFA - Modifier Assets
class SEQUENCER_OT_add_asset_modifier_menu(InvokeMenuOperator, Operator):
    bl_idname = "sequencer.add_asset_modifier_menu"
    bl_label = "Add Asset Modifier"
    bl_description = "Add a modifier nodegroup to the strip"
    menu_id = "SEQUENCER_MT_modifier_add_assets"
    space_type = 'PROPERTIES'
    space_context = 'STRIP_MODIFIER'


class STRIP_PT_modifiers(StripModButtonsPanel, Panel):
    bl_label = "Modifiers"
    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        row = layout.row()
        row.operator("wm.call_menu", text="Add Modifier", icon='ADD').name = "SEQUENCER_MT_modifier_add"

        # BFA - Modifier Assets
        row.operator("sequencer.add_asset_modifier_menu", icon='ADD')

        # BFA - adde and expose the copy to selected to the stack consistently, and make it intuitive when selected strips are more than 1.
        copy_row = row.row()
        copy_row.enabled = len(bpy.context.selected_strips) > 1
        copy_row.operator("sequencer.strip_modifier_copy", text="", icon="COPYDOWN")

        layout.template_strip_modifiers()


classes = (
    STRIP_PT_modifiers,
    SEQUENCER_MT_modifier_add_assets,  # BFA
    SEQUENCER_OT_add_asset_modifier_menu,  # BFA
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
