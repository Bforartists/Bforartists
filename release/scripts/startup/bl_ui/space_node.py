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

# <pep8 compliant>
import bpy
from bpy.types import Header, Menu, Panel
from blf import gettext as _


class NODE_HT_header(Header):
    bl_space_type = 'NODE_EDITOR'

    def draw(self, context):
        layout = self.layout

        snode = context.space_data
        snode_id = snode.id
        id_from = snode.id_from

        row = layout.row(align=True)
        row.template_header()

        if context.area.show_menus:
            row.menu("NODE_MT_view")
            row.menu("NODE_MT_select")
            row.menu("NODE_MT_add")
            row.menu("NODE_MT_node")

        layout.prop(snode, "tree_type", text="", expand=True)

        if snode.tree_type == 'SHADER':
            row.prop(snode, "shader_type", text="", expand=True)

            if snode.shader_type == 'OBJECT':
                if id_from:
                    layout.template_ID(id_from, "active_material", new="material.new")
                if snode_id:
                    layout.prop(snode_id, "use_nodes")

        elif snode.tree_type == 'TEXTURE':
            layout.prop(snode, "texture_type", text="", expand=True)

            if id_from:
                if snode.texture_type == 'BRUSH':
                    layout.template_ID(id_from, "texture", new="texture.new")
                else:
                    layout.template_ID(id_from, "active_texture", new="texture.new")
            if snode_id:
                layout.prop(snode_id, "use_nodes")

        elif snode.tree_type == 'COMPOSITING':
            layout.prop(snode_id, "use_nodes")
            layout.prop(snode_id.render, "use_free_unused_nodes", text=_("Free Unused"))
            layout.prop(snode, "show_backdrop")
            if snode.show_backdrop:
                row = layout.row(align=True)
                row.prop(snode, "backdrop_channels", text="", expand=True)
            layout.prop(snode, "use_auto_render")

        layout.separator()

        layout.template_running_jobs()


class NODE_MT_view(Menu):
    bl_label = "View"

    def draw(self, context):
        layout = self.layout

        layout.operator("node.properties", icon='MENU_PANEL')
        layout.separator()

        layout.operator("view2d.zoom_in")
        layout.operator("view2d.zoom_out")

        layout.separator()

        layout.operator("node.view_all")

        if context.space_data.show_backdrop:
            layout.separator()

            layout.operator("node.backimage_move", text=_("Backdrop move"))
            layout.operator("node.backimage_zoom", text=_("Backdrop zoom in")).factor = 1.2
            layout.operator("node.backimage_zoom", text=_("Backdrop zoom out")).factor = 0.833

        layout.separator()

        layout.operator("screen.area_dupli")
        layout.operator("screen.screen_full_area")


class NODE_MT_select(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout

        layout.operator("node.select_border")

        layout.separator()
        layout.operator("node.select_all")
        layout.operator("node.select_linked_from")
        layout.operator("node.select_linked_to")
        layout.operator("node.select_same_type")
        layout.operator("node.select_same_type_next")
        layout.operator("node.select_same_type_prev")


class NODE_MT_node(Menu):
    bl_label = "Node"

    def draw(self, context):
        layout = self.layout

        layout.operator("transform.translate")
        layout.operator("transform.rotate")
        layout.operator("transform.resize")

        layout.separator()

        layout.operator("node.duplicate_move")
        layout.operator("node.delete")
        layout.operator("node.delete_reconnect")

        layout.separator()
        layout.operator("node.link_make")
        layout.operator("node.link_make", text=_("Make and Replace Links")).replace = True
        layout.operator("node.links_cut")

        layout.separator()
        layout.operator("node.group_edit")
        layout.operator("node.group_ungroup")
        layout.operator("node.group_make")

        layout.separator()

        layout.operator("node.hide_toggle")
        layout.operator("node.mute_toggle")
        layout.operator("node.preview_toggle")
        layout.operator("node.hide_socket_toggle")

        layout.separator()

        layout.operator("node.show_cyclic_dependencies")
        layout.operator("node.read_renderlayers")
        layout.operator("node.read_fullsamplelayers")


# Node Backdrop options
class NODE_PT_properties(Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_label = "Backdrop"

    @classmethod
    def poll(cls, context):
        snode = context.space_data
        return snode.tree_type == 'COMPOSITING'

    def draw_header(self, context):
        snode = context.space_data
        self.layout.prop(snode, "show_backdrop", text="")

    def draw(self, context):
        layout = self.layout

        snode = context.space_data
        layout.active = snode.show_backdrop
        layout.prop(snode, "backdrop_channels", text="")
        layout.prop(snode, "backdrop_zoom", text=_("Zoom"))

        col = layout.column(align=True)
        col.label(text=_("Offset:"))
        col.prop(snode, "backdrop_x", text="X")
        col.prop(snode, "backdrop_y", text="Y")
        col.operator("node.backimage_move", text=_("Move"))

if __name__ == "__main__":  # only for live edit.
    bpy.utils.register_module(__name__)
