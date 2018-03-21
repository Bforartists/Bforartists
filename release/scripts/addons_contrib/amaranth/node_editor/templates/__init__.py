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
