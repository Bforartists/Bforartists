# SPDX-FileCopyrightText: 2018-2023 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

from bpy.types import Panel, Menu, Operator
from bl_ui.generic_column_menu import GenericColumnMenu, fetch_op_data, InvokeMenuOperator


class ShaderFxButtonsPanel:
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "shaderfx"


class DATA_PT_shader_fx(ShaderFxButtonsPanel, Panel):
    bl_label = "Effects"
    bl_options = {'HIDE_HEADER'}

    def draw(self, _context):
        layout = self.layout
        layout.operator("object.add_gpencil_shaderfx_menu", text="Add Effect", icon='ADD')
        layout.template_shaderfx()


class OBJECT_MT_gpencil_shaderfx_add(GenericColumnMenu, Menu):
    bl_description = "Add a visual effect to the active grease pencil object"

    op_id = "object.shaderfx_add"
    OPERATOR_DATA, TRANSLATION_CONTEXT = fetch_op_data(class_name="ShaderFx")
    search_header = "Effect"

    # BFA - always show for now.
    #@classmethod
    #def poll(cls, context):
    #    ob = context.object
    #    return ob and ob.type == 'GPENCIL'

    def draw(self, _context):
        layout = self.layout.row()

        self.draw_operator_column(layout, header="Add Effect",
            types=('FX_BLUR', 'FX_COLORIZE', 'FX_FLIP', 'FX_GLOW', 'FX_PIXEL', 'FX_RIM', 'FX_SHADOW', 'FX_SWIRL', 'FX_WAVE'))


class OBJECT_OT_add_gpencil_shaderfx_menu(InvokeMenuOperator, Operator):
    bl_idname = "object.add_gpencil_shaderfx_menu"
    bl_label = "Add Grease Pencil Effect"
    bl_description = "Add a visual effect to the active grease pencil object"

    menu_id = "OBJECT_MT_gpencil_shaderfx_add"
    space_type = 'PROPERTIES'
    space_context = 'SHADERFX'


classes = (
    DATA_PT_shader_fx,
    OBJECT_MT_gpencil_shaderfx_add,
    OBJECT_OT_add_gpencil_shaderfx_menu,
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
