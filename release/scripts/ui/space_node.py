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


class NODE_HT_header(bpy.types.Header):
    bl_space_type = 'NODE_EDITOR'

    def draw(self, context):
        layout = self.layout

        snode = context.space_data

        row = layout.row(align=True)
        row.template_header()

        if context.area.show_menus:
            sub = row.row(align=True)
            sub.menu("NODE_MT_view")
            sub.menu("NODE_MT_select")
            sub.menu("NODE_MT_add")
            sub.menu("NODE_MT_node")

        row = layout.row()
        row.prop(snode, "tree_type", text="", expand=True)

        if snode.tree_type == 'MATERIAL':
            ob = snode.id_from
            snode_id = snode.id
            if ob:
                layout.template_ID(ob, "active_material", new="material.new")
            if snode_id:
                layout.prop(snode_id, "use_nodes")

        elif snode.tree_type == 'TEXTURE':
            row.prop(snode, "texture_type", text="", expand=True)

            snode_id = snode.id
            id_from = snode.id_from
            if id_from:
                if snode.texture_type == 'BRUSH':
                    layout.template_ID(id_from, "texture", new="texture.new")
                else:
                    layout.template_ID(id_from, "active_texture", new="texture.new")
            if snode_id:
                layout.prop(snode_id, "use_nodes")

        elif snode.tree_type == 'COMPOSITING':
            scene = snode.id

            layout.prop(scene, "use_nodes")
            layout.prop(scene.render, "free_unused_nodes", text="Free Unused")
            layout.prop(snode, "show_backdrop")

        layout.separator()

        layout.template_running_jobs()


class NODE_MT_view(bpy.types.Menu):
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
            
            layout.operator("node.backimage_move",text = "Backdrop move")
            layout.operator("node.backimage_zoom",text = "Backdrop zoom in").factor = 1.2
            layout.operator("node.backimage_zoom",text = "Backdrop zoom out").factor = 0.833
        
        layout.separator()

        layout.operator("screen.area_dupli")
        layout.operator("screen.screen_full_area")


class NODE_MT_select(bpy.types.Menu):
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


class NODE_MT_node(bpy.types.Menu):
    bl_label = "Node"

    def draw(self, context):
        layout = self.layout

        layout.operator("transform.translate")
        layout.operator("transform.rotate")
        layout.operator("transform.resize")

        layout.separator()

        layout.operator("node.duplicate_move")
        layout.operator("node.delete")

        layout.separator()
        layout.operator("node.link_make")
        layout.operator("node.link_make", text="Make and Replace Links").replace = True
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

        # XXX
        # layout.operator("node.rename")

        layout.separator()

        layout.operator("node.show_cyclic_dependencies")


def register():
    pass


def unregister():
    pass

if __name__ == "__main__":
    register()
