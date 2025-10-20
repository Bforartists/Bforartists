# SPDX-FileCopyrightText: 2009-2023 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

from bpy.types import (
    Panel,
)


class StripModButtonsPanel:
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "strip_modifier"

    @classmethod
    def poll(cls, context):
        return context.active_strip is not None


class STRIP_PT_modifiers(StripModButtonsPanel, Panel):
    bl_label = "Modifiers"
    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        strip = context.active_strip
        if strip.type == 'SOUND':
            sound = strip.sound
        else:
            sound = None

        if sound is None:
            row = layout.row()  # BFA - float left
            row.use_property_split = False
            row.prop(strip, "use_linear_modifiers")
            row.prop_decorator(strip, "use_linear_modifiers")

        row = layout.row()
        row.operator("wm.call_menu", text="Add Modifier", icon='ADD').name = "SEQUENCER_MT_modifier_add"
        row.operator("sequencer.strip_modifier_copy", text="", icon="COPYDOWN") # BFA - expose consistently

        layout.template_strip_modifiers()


classes = (
    STRIP_PT_modifiers,
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
