# SPDX-License-Identifier: GPL-2.0-or-later

# <pep8 compliant>

import bpy
from bpy.types import Panel
from bpy.app.translations import pgettext_iface as iface_
from bpy.app.translations import contexts as i18n_contexts
from bl_ui.utils import PresetPanel
from bl_ui.properties_grease_pencil_common import (
    AnnotationDataPanel,
)
from bl_ui.space_toolsystem_common import (
    ToolActivePanelHelper,
)
from bl_ui.properties_material import (
    EEVEE_MATERIAL_PT_settings,
    MATERIAL_PT_viewport
)
from bl_ui.properties_world import (
    WORLD_PT_viewport_display
)
from bl_ui.properties_data_light import (
    DATA_PT_light,
    DATA_PT_EEVEE_light,
)

class toolshelf_calculate(Panel):

    @staticmethod
    def ts_width(layout, region, scale_y):

        # Currently this just checks the width,
        # we could have different layouts as preferences too.
        system = bpy.context.preferences.system
        view2d = region.view2d
        view2d_scale = (
            view2d.region_to_view(1.0, 0.0)[0] -
            view2d.region_to_view(0.0, 0.0)[0]
        )
        width_scale = region.width * view2d_scale / system.ui_scale

        # how many rows. 4 is text buttons.

        if width_scale > 160.0:
            column_count = 4
        elif width_scale > 130.0:
            column_count = 3
        elif width_scale > 90:
            column_count = 2
        else:
            column_count = 1

        return column_count


class NODE_PT_transform(toolshelf_calculate, Panel):
    bl_label = "Transform"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "Node"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

     # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        #view = context.space_data
        #overlay = view.overlay
        #return overlay.show_toolshelf_tabs == True and sima.mode == 'UV'
        return addon_prefs.node_show_toolshelf_tabs

    def draw(self, context):
        layout = self.layout

        column_count = self.ts_width(layout, context.region, scale_y= 1.75)

        obj = context.object

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("transform.translate", icon = "TRANSFORM_MOVE").release_confirm = True
            col.operator("transform.rotate", icon = "TRANSFORM_ROTATE")
            col.operator("transform.resize",  icon = "TRANSFORM_SCALE")

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("transform.translate", text = "", icon = "TRANSFORM_MOVE").release_confirm = True
                row.operator("transform.rotate", text = "", icon = "TRANSFORM_ROTATE")
                row.operator("transform.resize", text = "",  icon = "TRANSFORM_SCALE")

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("transform.translate", text = "", icon = "TRANSFORM_MOVE").release_confirm = True
                row.operator("transform.rotate", text = "", icon = "TRANSFORM_ROTATE")
                row = col.row(align=True)
                row.operator("transform.resize", text = "",  icon = "TRANSFORM_SCALE")

            elif column_count == 1:

                col.operator("transform.translate", text = "", icon = "TRANSFORM_MOVE").release_confirm = True
                col.operator("transform.rotate", text = "", icon = "TRANSFORM_ROTATE")
                col.operator("transform.resize", text = "",  icon = "TRANSFORM_SCALE")


class NODE_PT_links(toolshelf_calculate, Panel):
    bl_label = "Links"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "Node"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

     # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        #view = context.space_data
        #overlay = view.overlay
        #return overlay.show_toolshelf_tabs == True and sima.mode == 'UV'
        return addon_prefs.node_show_toolshelf_tabs

    def draw(self, context):
        layout = self.layout

        column_count = self.ts_width(layout, context.region, scale_y= 1.75)

        obj = context.object

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("node.link_make", icon = "LINK_DATA").replace = False
            col.operator("node.link_make", text="Make and Replace Links", icon = "LINK_REPLACE").replace = True
            col.operator("node.links_detach", icon = "DETACH_LINKS")
            col.operator("node.move_detach_links", text = "Detach Links Move", icon = "DETACH_LINKS_MOVE")
            col.operator("node.links_mute", icon = "MUTE_IPO_ON")

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("node.link_make", text="", icon = "LINK_DATA").replace = False
                row.operator("node.link_make", text="", icon = "LINK_REPLACE").replace = True
                row.operator("node.links_detach", text="", icon = "DETACH_LINKS")

                row = col.row(align=True)
                row.operator("node.move_detach_links", text = "", icon = "DETACH_LINKS_MOVE")
                row.operator("node.links_mute", text="", icon = "MUTE_IPO_ON")

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("node.link_make", text="", icon = "LINK_DATA").replace = False
                row.operator("node.link_make", text="", icon = "LINK_REPLACE").replace = True

                row = col.row(align=True)
                row.operator("node.links_detach", text="", icon = "DETACH_LINKS")
                row.operator("node.move_detach_links", text = "", icon = "DETACH_LINKS_MOVE")

                row = col.row(align=True)
                row.operator("node.links_mute", text="", icon = "MUTE_IPO_ON")

            elif column_count == 1:

                col.operator("node.link_make", text="", icon = "LINK_DATA").replace = False
                col.operator("node.link_make", text="", icon = "LINK_REPLACE").replace = True
                col.operator("node.links_detach", text="", icon = "DETACH_LINKS")
                col.operator("node.move_detach_links", text = "", icon = "DETACH_LINKS_MOVE")
                col.operator("node.links_mute", text="", icon = "MUTE_IPO_ON")


class NODE_PT_separate(toolshelf_calculate, Panel):
    bl_label = "Separate"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "Node"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

     # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        #view = context.space_data
        #overlay = view.overlay
        #return overlay.show_toolshelf_tabs == True and sima.mode == 'UV'
        return addon_prefs.node_show_toolshelf_tabs

    def draw(self, context):
        layout = self.layout

        column_count = self.ts_width(layout, context.region, scale_y= 1.75)

        obj = context.object

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("node.group_separate", text = "Copy", icon = "SEPARATE_COPY").type = 'COPY'
            col.operator("node.group_separate", text = "Move", icon = "SEPARATE").type = 'MOVE'

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("node.group_separate", text = "", icon = "SEPARATE_COPY").type = 'COPY'
                row.operator("node.group_separate", text = "", icon = "SEPARATE").type = 'MOVE'

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("node.group_separate", text = "", icon = "SEPARATE_COPY").type = 'COPY'
                row.operator("node.group_separate", text = "", icon = "SEPARATE").type = 'MOVE'

            elif column_count == 1:

                col.operator("node.group_separate", text = "", icon = "SEPARATE_COPY").type = 'COPY'
                col.operator("node.group_separate", text = "", icon = "SEPARATE").type = 'MOVE'


class NODE_PT_node_tools(toolshelf_calculate, Panel):
    bl_label = "Frame Tools"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "Node"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

     # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        #view = context.space_data
        #overlay = view.overlay
        #return overlay.show_toolshelf_tabs == True and sima.mode == 'UV'
        return addon_prefs.node_show_toolshelf_tabs

    def draw(self, context):
        layout = self.layout

        column_count = self.ts_width(layout, context.region, scale_y= 1.75)

        obj = context.object

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("node.join", text="Join in New Frame", icon = "JOIN")
            col.operator("node.detach", text="Remove from Frame", icon = "DELETE")
            col.operator("node.parent_set", text = "Frame Make Parent", icon = "PARENT_SET")

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("node.join", text="", icon = "JOIN")
                row.operator("node.detach", text="", icon = "DELETE")
                row.operator("node.parent_set", text = "", icon = "PARENT_SET")

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("node.join", text="", icon = "JOIN")
                row.operator("node.detach", text="", icon = "DELETE")

                row = col.row(align=True)
                row.operator("node.parent_set", text = "", icon = "PARENT_SET")

            elif column_count == 1:

                col.operator("node.join", text="", icon = "JOIN")
                col.operator("node.detach", text="", icon = "DELETE")
                col.operator("node.parent_set", text = "", icon = "PARENT_SET")


classes = (
    NODE_PT_transform,
    NODE_PT_links,
    NODE_PT_separate,
    NODE_PT_node_tools,
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
