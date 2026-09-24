# SPDX-License-Identifier: GPL-2.0-or-later

# <pep8 compliant>

import bpy
from bpy.types import Panel

from bl_ui.space_toolsystem_common import (
    Separator,
    OperatorEntry,
    draw_entries,
)


class NodeToolsystemPanel(Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "Node"

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        return view.show_toolshelf_tabs == True


class NODE_PT_transform(NodeToolsystemPanel):
    bl_label = "Transform"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        entries = [            
            OperatorEntry("transform.translate", icon="TRANSFORM_MOVE", props={"release_confirm": True}),
            OperatorEntry("transform.rotate", icon="TRANSFORM_ROTATE"),
            OperatorEntry("transform.resize",  icon="TRANSFORM_SCALE"),
        ]

        draw_entries(layout, context, entries)


class NODE_PT_links(NodeToolsystemPanel):
    bl_label = "Links"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        entries = [            
            OperatorEntry("node.link_make", icon="LINK_DATA", props={"replace" : False}),
            OperatorEntry("node.link_make", text="Make and Replace Links", icon="LINK_REPLACE", props={"replace" : True}),
            OperatorEntry("node.links_detach", icon="DETACH_LINKS"),
            OperatorEntry("node.move_detach_links", text="Detach Links Move", icon="DETACH_LINKS_MOVE"),
            OperatorEntry("node.links_mute", icon="MUTE_IPO_ON"),
        ]

        draw_entries(layout, context, entries)


class NODE_PT_separate(NodeToolsystemPanel):
    bl_label = "Separate"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        entries = [            
            OperatorEntry("node.group_separate", text="Copy", icon="SEPARATE_COPY", props={"type" : 'COPY'}),
            OperatorEntry("node.group_separate", text="Move", icon="SEPARATE", props={"type" : 'MOVE'}),
        ]

        draw_entries(layout, context, entries)


class NODE_PT_node_tools(NodeToolsystemPanel):
    bl_label = "Frame Tools"
    bl_options = {'HIDE_BG'}

    def draw(self, context):
        layout = self.layout

        entries = [            
            OperatorEntry("node.join", text="Join in New Frame", icon="NODE_FRAMEJOIN"),
            OperatorEntry("node.detach", text="Remove from Frame", icon="NODE_FRAMEREMOVE"),
            OperatorEntry("node.join_nodes", text="Join Group Inputs", icon="NODE_JOINGROUP"),
            OperatorEntry("node.join_named", icon="NODE_JOINFRAMENAMED"),
            OperatorEntry("node.parent_set", text="Frame Make Parent", icon="NODE_FRAMEPARENT"),
        ]

        draw_entries(layout, context, entries)


class NODE_PT_group(NodeToolsystemPanel):
    bl_label = "Group"
    bl_options = {'HIDE_BG'}

     # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.show_toolshelf_tabs

    def draw(self, context):
        layout = self.layout

        entries = [            
            OperatorEntry("node.group_make", icon="NODE_MAKEGROUP"),
            OperatorEntry("node.group_insert", icon="NODE_GROUPINSERT"),
            OperatorEntry("node.group_ungroup", icon="NODE_UNGROUP"),
            Separator,
            OperatorEntry("node.group_edit", icon="NODE_EDITGROUP", props={"exit" : False}),
        ]

        draw_entries(layout, context, entries)


classes = (
    NODE_PT_transform,
    NODE_PT_links,
    NODE_PT_separate,
    NODE_PT_node_tools,
    NODE_PT_group,
)


if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
