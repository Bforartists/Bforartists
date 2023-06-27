# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
Node Templates - Vignette, Vector Blur

Add a set of nodes with one click, in this version I added a "Vignette"
as first example.

There is no official way to make a vignette, this is just my approach at
it. Templates: On the Compositor's header, "Template" pulldown. Or hit W.
Vignette: Adjust the size and position of the vignette with the Ellipse
Mask's X/Y and width, height values.
"""

import bpy
from amaranth.node_editor.templates.vectorblur import AMTH_NODE_OT_AddTemplateVectorBlur
from amaranth.node_editor.templates.vignette import AMTH_NODE_OT_AddTemplateVignette


KEYMAPS = list()


# Node Templates Menu
class AMTH_NODE_MT_amaranth_templates(bpy.types.Menu):
    bl_idname = 'AMTH_NODE_MT_amaranth_templates'
    bl_space_type = 'NODE_EDITOR'
    bl_label = "Templates"
    bl_description = "List of Amaranth Templates"

    def draw(self, context):
        layout = self.layout
        layout.operator(
            AMTH_NODE_OT_AddTemplateVectorBlur.bl_idname,
            text="Vector Blur",
            icon='FORCE_HARMONIC')
        layout.operator(
            AMTH_NODE_OT_AddTemplateVignette.bl_idname,
            text="Vignette",
            icon='COLOR')


def node_templates_pulldown(self, context):
    if context.space_data.tree_type == 'CompositorNodeTree':
        layout = self.layout
        row = layout.row(align=True)
        row.scale_x = 1.3
        row.menu("AMTH_NODE_MT_amaranth_templates",
                 icon="NODETREE")


def register():
    bpy.utils.register_class(AMTH_NODE_MT_amaranth_templates)
    bpy.utils.register_class(AMTH_NODE_OT_AddTemplateVignette)
    bpy.utils.register_class(AMTH_NODE_OT_AddTemplateVectorBlur)
    bpy.types.NODE_HT_header.append(node_templates_pulldown)
    kc = bpy.context.window_manager.keyconfigs.addon
    km = kc.keymaps.new(name="Node Editor", space_type="NODE_EDITOR")
    kmi = km.keymap_items.new("wm.call_menu", "W", "PRESS")
    kmi.properties.name = "AMTH_NODE_MT_amaranth_templates"
    KEYMAPS.append((km, kmi))


def unregister():
    bpy.utils.unregister_class(AMTH_NODE_MT_amaranth_templates)
    bpy.utils.unregister_class(AMTH_NODE_OT_AddTemplateVignette)
    bpy.utils.unregister_class(AMTH_NODE_OT_AddTemplateVectorBlur)
    bpy.types.NODE_HT_header.remove(node_templates_pulldown)
    for km, kmi in KEYMAPS:
        km.keymap_items.remove(kmi)
    KEYMAPS.clear()
