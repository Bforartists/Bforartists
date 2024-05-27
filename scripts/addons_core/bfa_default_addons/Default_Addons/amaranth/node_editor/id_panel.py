# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
Object / Material Indices Panel

When working with ID Masks in the Nodes Editor, is hard to follow track
of which objects/materials have which ID.
This adds a panel on the sidebar when an ID Mask node is selected.
The active object is highlighted between [square brackets] On the Nodes
Editor's sidebar, when an ID Mask node is selected.
"""

import bpy


class AMTH_NODE_PT_indices(bpy.types.Panel):
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_label = "Object / Material Indices"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        node = context.active_node
        return node and node.type == "ID_MASK"

    def draw(self, context):
        layout = self.layout

        objects = bpy.data.objects
        materials = bpy.data.materials
        node = context.active_node

        show_ob_id = False
        show_ma_id = False
        matching_ids = False

        if context.active_object:
            ob_act = context.active_object
        else:
            ob_act = False

        for ob in objects:
            if ob and ob.pass_index > 0:
                show_ob_id = True
        for ma in materials:
            if ma and ma.pass_index > 0:
                show_ma_id = True
        row = layout.row(align=True)
        row.prop(node, "index", text="Mask Index")
        row.prop(node, "use_matching_indices", text="Only Matching IDs")

        layout.separator()

        if not show_ob_id and not show_ma_id:
            layout.label(
                text="No objects or materials indices so far.", icon="INFO")

        if show_ob_id:
            split = layout.split()
            col = split.column()
            col.label(text="Object Name")
            split.label(text="ID Number")
            row = layout.row()
            for ob in objects:
                icon = "OUTLINER_DATA_" + ob.type
                if ob.library:
                    icon = "LIBRARY_DATA_DIRECT"
                elif ob.is_library_indirect:
                    icon = "LIBRARY_DATA_INDIRECT"

                if ob and node.use_matching_indices \
                    and ob.pass_index == node.index \
                    and ob.pass_index != 0:
                    matching_ids = True
                    row.label(
                        text="[{}]".format(ob.name)
                        if ob_act and ob.name == ob_act.name else ob.name,
                        icon=icon)
                    row.label(text="%s" % ob.pass_index)
                    row = layout.row()

                elif ob and not node.use_matching_indices \
                        and ob.pass_index > 0:

                    matching_ids = True
                    row.label(
                        text="[{}]".format(ob.name)
                        if ob_act and ob.name == ob_act.name else ob.name,
                        icon=icon)
                    row.label(text="%s" % ob.pass_index)
                    row = layout.row()

            if node.use_matching_indices and not matching_ids:
                row.label(text="No objects with ID %s" %
                          node.index, icon="INFO")

            layout.separator()

        if show_ma_id:
            split = layout.split()
            col = split.column()
            col.label(text="Material Name")
            split.label(text="ID Number")
            row = layout.row()

            for ma in materials:
                icon = "BLANK1"
                if ma.use_nodes:
                    icon = "NODETREE"
                elif ma.library:
                    icon = "LIBRARY_DATA_DIRECT"
                    if ma.is_library_indirect:
                        icon = "LIBRARY_DATA_INDIRECT"

                if ma and node.use_matching_indices \
                    and ma.pass_index == node.index \
                    and ma.pass_index != 0:
                    matching_ids = True
                    row.label(text="%s" % ma.name, icon=icon)
                    row.label(text="%s" % ma.pass_index)
                    row = layout.row()

                elif ma and not node.use_matching_indices \
                        and ma.pass_index > 0:

                    matching_ids = True
                    row.label(text="%s" % ma.name, icon=icon)
                    row.label(text="%s" % ma.pass_index)
                    row = layout.row()

            if node.use_matching_indices and not matching_ids:
                row.label(text="No materials with ID %s" %
                          node.index, icon="INFO")


def register():
    bpy.utils.register_class(AMTH_NODE_PT_indices)


def unregister():
    bpy.utils.unregister_class(AMTH_NODE_PT_indices)
