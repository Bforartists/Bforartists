﻿# ##### BEGIN GPL LICENSE BLOCK #####
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
from bpy.types import Header, Menu

################################ Switch between the editors ##########################################

# Editor types: 
# ('VIEW_3D', 'TIMELINE', 'GRAPH_EDITOR', 'DOPESHEET_EDITOR', 'NLA_EDITOR', 'IMAGE_EDITOR', 
# 'CLIP_EDITOR', 'TEXT_EDITOR', 'NODE_EDITOR', 'PROPERTIES', 'OUTLINER', 'USER_PREFERENCES', 'INFO', 'FILE_BROWSE)

class switch_editors_to_properties(bpy.types.Operator):
    """Switch to Properties editor"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "wm.switch_editor_to_properties"        # unique identifier for buttons and menu items to reference.
    bl_label = "Switch to Properties Editor"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.wm.context_set_enum(data_path="area.type", value="PROPERTIES")
        return {'FINISHED'}

class switch_editors_to_outliner(bpy.types.Operator):
    """Switch to Outliner Editor"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "wm.switch_editor_to_outliner"        # unique identifier for buttons and menu items to reference.
    bl_label = "Switch to Outliner Editor"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.wm.context_set_enum(data_path="area.type", value="OUTLINER")
        return {'FINISHED'} 

################################ Switch between the editors ##########################################

class switch_editors_in_outliner(bpy.types.Operator):
    """You are in Outliner Editor"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "wm.switch_editor_in_outliner"        # unique identifier for buttons and menu items to reference.
    bl_label = "Outliner Editor"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.


class OUTLINER_HT_header(Header):
    bl_space_type = 'OUTLINER'

    def draw(self, context):
        layout = self.layout

        space = context.space_data
        scene = context.scene
        ks = context.scene.keying_sets.active

        ALL_MT_editormenu.draw_hidden(context, layout) # bfa - show hide the editormenu

        # bfa - The tabs to switch between the four animation editors. The classes are here above
        row = layout.row(align=True)
        row.operator("wm.switch_editor_in_outliner", text="", icon='OOPS_ACTIVE')
        row.operator("wm.switch_editor_to_properties", text="", icon='BUTS')

        OUTLINER_MT_editor_menus.draw_collapsible(context, layout)

        layout.prop(space, "display_mode", text="")

        layout.prop(space, "filter_text", icon='VIEWZOOM', text="")

        layout.separator()

        if space.display_mode == 'DATABLOCKS':
            row = layout.row(align=True)
            row.operator("outliner.keyingset_add_selected", icon='ZOOMIN', text="")
            row.operator("outliner.keyingset_remove_selected", icon='ZOOMOUT', text="")

            if ks:
                row = layout.row()
                row.prop_search(scene.keying_sets, "active", scene, "keying_sets", text="")

                row = layout.row(align=True)
                row.operator("anim.keyframe_insert", text="", icon='KEY_HLT')
                row.operator("anim.keyframe_delete", text="", icon='KEY_DEHLT')
            else:
                row = layout.row()
                row.label(text="No Keying Set Active")
        elif space.display_mode == 'ORPHAN_DATA':
            layout.operator("outliner.orphans_purge")

# bfa - show hide the editormenu
class ALL_MT_editormenu(Menu):
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):

        row = layout.row(align=True)
        row.template_header() # editor type menus


class OUTLINER_MT_editor_menus(Menu):
    bl_idname = "OUTLINER_MT_editor_menus"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):
        space = context.space_data

        layout.menu("OUTLINER_MT_view")

        if space.display_mode == 'DATABLOCKS':
            layout.menu("OUTLINER_MT_edit_datablocks")

# Workaround to separate the tooltips for Hide one level
class OUTLINER_MT_view_hide_one_level(bpy.types.Operator):
    """Hide one level\nCollapse all entries by one level """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "outliner.hide_one_level"        # unique identifier for buttons and menu items to reference.
    bl_label = "Hide one level"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.outliner.show_one_level(open = False)
        return {'FINISHED'}  

class OUTLINER_MT_view(Menu):
    bl_label = "View"

    def draw(self, context):
        layout = self.layout

        space = context.space_data

        layout.menu("OUTLINER_MT_search")

        if space.display_mode not in {'DATABLOCKS', 'USER_PREFERENCES', 'KEYMAPS'}:
            layout.prop(space, "use_sort_alpha")
            layout.prop(space, "show_restrict_columns")
            layout.separator()
            layout.operator("outliner.show_active", icon = "CENTER")

        layout.operator("outliner.show_one_level", text="Show One Level", icon = "HIERARCHY_DOWN")
        layout.operator("outliner.show_one_level", text="Hide One Level", icon = "HIERARCHY_UP").open = False
        layout.operator("outliner.show_hierarchy", icon = "HIERARCHY")

        layout.separator()

        layout.operator("outliner.select_border", icon='BORDER_RECT')
        layout.operator("outliner.selected_toggle", icon='SELECT_ALL')
        layout.operator("outliner.expanded_toggle", icon='INVERSE')

        layout.separator()

        layout.operator("screen.area_dupli", icon = "NEW_WINDOW")
        layout.operator("screen.toggle_maximized_area", text="Toggle Maximize Area", icon = "MAXIMIZE_AREA") # bfa - the separated tooltip. Class is in space_text.py
        layout.operator("screen.screen_full_area", icon = "FULLSCREEN_AREA").use_hide_panels = True


class OUTLINER_MT_search(Menu):
    bl_label = "Search Options"

    def draw(self, context):
        layout = self.layout

        space = context.space_data

        layout.prop(space, "use_filter_case_sensitive")
        layout.prop(space, "use_filter_complete")


class OUTLINER_MT_edit_datablocks(Menu):
    bl_label = "Edit"

    def draw(self, context):
        layout = self.layout

        layout.operator("outliner.keyingset_add_selected")
        layout.operator("outliner.keyingset_remove_selected")

        layout.separator()

        layout.operator("outliner.drivers_add_selected")
        layout.operator("outliner.drivers_delete_selected")


classes = (
    switch_editors_to_properties,
    switch_editors_to_outliner,
    switch_editors_in_outliner,
    OUTLINER_HT_header,
    ALL_MT_editormenu,
    OUTLINER_MT_editor_menus,
    OUTLINER_MT_view_hide_one_level,
    OUTLINER_MT_view,
    OUTLINER_MT_search,
    OUTLINER_MT_edit_datablocks,
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
