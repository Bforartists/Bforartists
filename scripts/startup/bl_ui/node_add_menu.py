# SPDX-FileCopyrightText: 2022-2023 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.types import Menu
from bl_ui import node_add_menu
from bpy.app.translations import (
    pgettext_iface as iface_,
    contexts as i18n_contexts,
)


def add_node_type(layout, node_type, *, label=None, poll=None, search_weight=0.0):
    """Add a node type to a menu."""
    bl_rna = bpy.types.Node.bl_rna_get_subclass(node_type)
    if not label:
        label = bl_rna.name if bl_rna else iface_("Unknown")
    if poll is True or poll is None:
        translation_context = bl_rna.translation_context if bl_rna else i18n_contexts.default
        props = layout.operator("node.add_node", text=label, text_ctxt=translation_context, icon=bl_rna.icon, search_weight=search_weight)
        props.type = node_type
        props.use_transform = True
        return props


def draw_node_group_add_menu(context, layout):
    """Add items to the layout used for interacting with node groups."""
    space_node = context.space_data
    node_tree = space_node.edit_tree
    all_node_groups = context.blend_data.node_groups

    layout.operator("node.group_make", icon = "NODE_MAKEGROUP")
    layout.operator("node.group_insert", text = "Insert into Group ", icon = "NODE_GROUPINSERT")
    layout.operator("node.group_ungroup", icon = "NODE_UNGROUP")

    layout.separator()

    layout.operator("node.group_edit", text = " Toggle Edit Group", icon = "NODE_EDITGROUP").exit = False

    if node_tree in all_node_groups.values():
        layout.separator()
        add_node_type(layout, "NodeGroupInput")
        add_node_type(layout, "NodeGroupOutput")

    if node_tree:
        from nodeitems_builtins import node_tree_group_type

        groups = [
            group for group in context.blend_data.node_groups
            if (group.bl_idname == node_tree.bl_idname and
                not group.contains_tree(node_tree) and
                not group.name.startswith('.'))
        ]
        if groups:
            layout.separator()
            # BFA - used an alternate way to draw group list to have an icon, borrowed from the "space_node_toolshelf.py".
            '''
            for group in groups:
                props = add_node_type(layout, node_tree_group_type[group.bl_idname], label=group.name)
                ops = props.settings.add()
                ops.name = "node_tree"
                ops.value = "bpy.data.node_groups[%r]" % group.name
            '''

            for group in groups:
                #props = add_node_type(layout, node_tree_group_type[group.bl_idname], label=group.name)

                props = layout.operator("node.add_node", text=group.name, icon="NODETREE")
                props.use_transform = True
                props.type = node_tree_group_type[group.bl_idname]

                ops = props.settings.add()
                ops.name = "node_tree"
                ops.value = "bpy.data.node_groups[%r]" % group.name


def draw_assets_for_catalog(layout, catalog_path):
    layout.template_node_asset_menu_items(catalog_path=catalog_path)


def draw_root_assets(layout):
    layout.menu_contents("NODE_MT_node_add_root_catalogs")


def add_simulation_zone(layout, label):
    """Add simulation zone to a menu."""
    props = layout.operator("node.add_simulation_zone", text=label, text_ctxt=i18n_contexts.default, icon = "TIME") #BFA - added icon to Add Menu
    props.use_transform = True
    return props


def add_repeat_zone(layout, label):
    props = layout.operator("node.add_repeat_zone", text=label, text_ctxt=i18n_contexts.default, icon = "REPEAT") #BFA - added icon to Add Menu
    props.use_transform = True
    return props


class NODE_MT_category_layout(Menu):
    bl_idname = "NODE_MT_category_layout"
    bl_label = "Layout"

    def draw(self, _context):
        layout = self.layout
        node_add_menu.add_node_type(layout, "NodeFrame")
        node_add_menu.add_node_type(layout, "NodeReroute")

        node_add_menu.draw_assets_for_catalog(layout, self.bl_label)


classes = (
    NODE_MT_category_layout,
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
