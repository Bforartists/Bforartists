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

class switch_editors_in_graph(bpy.types.Operator):
    """You are in Graph editor"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "wm.switch_editor_in_graph"        # unique identifier for buttons and menu items to reference.
    bl_label = "Graph Editor"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.


##########################################################################


class GRAPH_HT_header(Header):
    bl_space_type = 'GRAPH_EDITOR'

    def draw(self, context):
        from bl_ui.space_dopesheet import dopesheet_filter

        layout = self.layout
        toolsettings = context.tool_settings

        st = context.space_data

        ALL_MT_editormenu.draw_hidden(context, layout) # bfa - show hide the editormenu

        # bfa - The tabs to switch between the four animation editors. The classes are in space_time.py
        row = layout.row(align=True)
        row.operator("wm.switch_editor_to_timeline", text="", icon='TIME')
        row.operator("wm.switch_editor_in_graph", text="", icon='GRAPH_ACTIVE')
        row.operator("wm.switch_editor_to_dopesheet", text="", icon='ACTION')     
        row.operator("wm.switch_editor_to_nla", text="", icon='NLA')

        GRAPH_MT_editor_menus.draw_collapsible(context, layout)

        layout.prop(st, "mode", text="")

        dopesheet_filter(layout, context)

        row = layout.row(align=True)
        row.prop(st, "use_normalization", icon='NORMALIZE_FCURVES', text="Normalize", toggle=True)
        sub = row.row(align=True)
        sub.active = st.use_normalization
        sub.prop(st, "use_auto_normalization", icon='FILE_REFRESH', text="", toggle=True)

        row = layout.row(align=True)

        row.prop(toolsettings, "use_proportional_fcurve",
                 text="", icon_only=True)
        if toolsettings.use_proportional_fcurve:
            row.prop(toolsettings, "proportional_edit_falloff",
                     text="", icon_only=True)

        layout.prop(st, "auto_snap", text="")
        layout.prop(st, "pivot_point", icon_only=True)

        row = layout.row(align=True)
        if st.has_ghost_curves:
            row.operator("graph.ghost_curves_clear", text="", icon='GHOST_DISABLED')
        else:
            row.operator("graph.ghost_curves_create", text="", icon='GHOST_ENABLED')

# bfa - show hide the editormenu
class ALL_MT_editormenu(Menu):
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):

        row = layout.row(align=True)
        row.template_header() # editor type menus

class GRAPH_MT_editor_menus(Menu):
    bl_idname = "GRAPH_MT_editor_menus"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):
        layout.menu("GRAPH_MT_view")
        layout.menu("GRAPH_MT_select")
        layout.menu("GRAPH_MT_marker")
        layout.menu("GRAPH_MT_channel")
        layout.menu("GRAPH_MT_key")


class GRAPH_MT_view(Menu):
    bl_label = "View"

    def draw(self, context):
        layout = self.layout

        st = context.space_data

        layout.operator("graph.properties", icon='MENU_PANEL')
        layout.separator()

        layout.prop(st, "use_realtime_update")
        layout.prop(st, "show_frame_indicator")
        layout.prop(st, "show_cursor")
        layout.prop(st, "show_sliders")
        layout.prop(st, "show_group_colors")
        layout.prop(st, "use_auto_merge_keyframes")

        layout.separator()
        layout.prop(st, "use_beauty_drawing")

        layout.separator()

        layout.prop(st, "show_handles")

        layout.prop(st, "use_only_selected_curves_handles")
        layout.prop(st, "use_only_selected_keyframe_handles")

        layout.prop(st, "show_seconds")
        layout.prop(st, "show_locked_time")

        layout.separator()
        layout.operator("anim.previewrange_set", icon='BORDER_RECT')
        layout.operator("anim.previewrange_clear", icon = "CLEAR")
        layout.operator("graph.previewrange_set", icon='BORDER_RECT')

        layout.separator()
        layout.operator("graph.view_all", icon = "VIEWALL")
        layout.operator("graph.view_selected", icon = "VIEW_SELECTED")
        layout.operator("graph.view_frame", icon = "VIEW_FRAME" )

        layout.separator()
        layout.operator("screen.area_dupli", icon = "NEW_WINDOW")
        layout.operator("screen.toggle_maximized_area", text="Toggle Maximize Area", icon = "MAXIMIZE_AREA") # bfa - the separated tooltip. Class is in space_text.py
        layout.operator("screen.screen_full_area", text="Toggle Fullscreen Area", icon = "FULLSCREEN_AREA").use_hide_panels = True


class GRAPH_MT_select(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout
     
        props = layout.operator("graph.select_border", icon='BORDER_RECT')
        props.axis_range = False
        props.include_handles = False
        props = layout.operator("graph.select_border", text="Border Axis Range", icon='BORDER_RECT')
        props.axis_range = True
        props.include_handles = False
        props = layout.operator("graph.select_border", text="Border (Include Handles)", icon='BORDER_RECT')
        props.axis_range = False
        props.include_handles = True
        props = layout.operator("graph.select_border", text="Border (Axis + Handles)", icon='BORDER_RECT')
        props.axis_range = False
        props.include_handles = True
        layout.operator("graph.select_circle", icon = 'CIRCLE_SELECT')
        
        layout.separator()
        
        layout.operator("graph.select_all_toggle", text = "(De)Select All", icon='SELECT_ALL').invert = False
        layout.operator("graph.select_all_toggle", text="Inverse", icon = 'INVERSE').invert = True     

        layout.separator()
        
        layout.operator("graph.select_column", text="Columns on Selected Keys", icon = "COLUMNS_KEYS").mode = 'KEYS'
        layout.operator("graph.select_column", text="Column on Current Frame", icon = "COLUMN_CURRENT_FRAME").mode = 'CFRA'

        layout.operator("graph.select_column", text="Columns on Selected Markers", icon = "COLUMNS_MARKERS").mode = 'MARKERS_COLUMN'
        layout.operator("graph.select_column", text="Between Selected Markers", icon = "BETWEEN_MARKERS").mode = 'MARKERS_BETWEEN'
        
        layout.separator()

        layout.operator("graph.select_linked",text = "Linked", icon = "CONNECTED")   

        layout.separator()
        
        props = layout.operator("graph.select_leftright", text="Before Current Frame", icon = "BEFORE_CURRENT_FRAME")
        props.extend = False
        props.mode = 'LEFT'
        props = layout.operator("graph.select_leftright", text="After Current Frame", icon = "AFTER_CURRENT_FRAME")
        props.extend = False
        props.mode = 'RIGHT'

        layout.separator()

        layout.operator("graph.select_more",text = "More", icon = "SELECTMORE")
        layout.operator("graph.select_less",text = "Less", icon = "SELECTLESS")



class GRAPH_MT_marker(Menu):
    bl_label = "Marker"

    def draw(self, context):
        layout = self.layout

        from bl_ui.space_time import marker_menu_generic
        marker_menu_generic(layout)

        # TODO: pose markers for action edit mode only?


# Workaround to separate the tooltips for Toggle Maximize Area
class GRAPH_MT_channel_hide_unselected_curves(bpy.types.Operator):
    """Hide unselected Curves\nHide unselected Curves from Graph Editor """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "graph.hide_unselected_curves"        # unique identifier for buttons and menu items to reference.
    bl_label = "Hide Unselected Curves"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.graph.hide(unselected = True)
        return {'FINISHED'}  

class GRAPH_MT_channel(Menu):
    bl_label = "Channel"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_CHANNELS'

        layout.operator("anim.channels_delete")

        layout.separator()
        layout.operator("anim.channels_group")
        layout.operator("anim.channels_ungroup")

        layout.separator()
        layout.operator_menu_enum("anim.channels_setting_toggle", "type")
        layout.operator_menu_enum("anim.channels_setting_enable", "type")
        layout.operator_menu_enum("anim.channels_setting_disable", "type")

        layout.separator()
        layout.operator("anim.channels_editable_toggle")
        layout.operator_menu_enum("graph.extrapolation_type", "type", text="Extrapolation Mode")

        layout.separator()
        layout.operator("graph.hide", text="Hide Selected Curves").unselected = False
        layout.operator("graph.hide_unselected_curves", text="Hide Unselected Curves")
        layout.operator("graph.reveal")

        layout.separator()
        layout.operator("anim.channels_expand")
        layout.operator("anim.channels_collapse")

        layout.separator()
        layout.operator_menu_enum("anim.channels_move", "direction", text="Move...")

        layout.separator()
        layout.operator("anim.channels_fcurves_enable")


class GRAPH_MT_key(Menu):
    bl_label = "Key"

    def draw(self, context):
        layout = self.layout

        layout.menu("GRAPH_MT_key_transform", text="Transform")

        layout.operator_menu_enum("graph.snap", "type", text="Snap")
        layout.operator_menu_enum("graph.mirror", "type", text="Mirror")

        layout.separator()
        layout.operator_menu_enum("graph.keyframe_insert", "type")
        layout.operator_menu_enum("graph.fmodifier_add", "type")
        layout.operator("graph.sound_bake")

        layout.separator()
        layout.operator("graph.frame_jump")

        layout.separator()
        layout.operator("graph.duplicate_move")
        layout.operator("graph.delete")

        layout.separator()
        layout.operator_menu_enum("graph.handle_type", "type", text="Handle Type")
        layout.operator_menu_enum("graph.interpolation_type", "type", text="Interpolation Mode")
        layout.operator_menu_enum("graph.easing_type", "type", text="Easing Type")

        layout.separator()
        layout.operator("graph.clean").channels = False
        layout.operator("graph.clean", text="Clean Channels").channels = True
        layout.operator("graph.smooth")
        layout.operator("graph.sample")
        layout.operator("graph.bake")

        layout.separator()
        layout.operator("graph.copy", text="Copy Keyframes", icon='COPYDOWN')
        layout.operator("graph.paste", text="Paste Keyframes", icon='PASTEDOWN')
        layout.operator("graph.paste", text="Paste Flipped", icon='PASTEFLIPDOWN').flipped = True

        layout.separator()
        layout.operator("graph.euler_filter", text="Discontinuity (Euler) Filter")


class GRAPH_MT_key_transform(Menu):
    bl_label = "Transform"

    def draw(self, context):
        layout = self.layout

        layout.operator("transform.translate", text="Grab/Move")
        layout.operator("transform.transform", text="Extend").mode = 'TIME_EXTEND'
        layout.operator("transform.rotate", text="Rotate")
        layout.operator("transform.resize", text="Scale")


class GRAPH_MT_delete(Menu):
    bl_label = "Delete"

    def draw(self, context):
        layout = self.layout

        layout.operator("graph.delete")

        layout.separator()

        layout.operator("graph.clean").channels = False
        layout.operator("graph.clean", text="Clean Channels").channels = True

classes = (
    switch_editors_in_graph,
    GRAPH_HT_header,
    ALL_MT_editormenu,
    GRAPH_MT_editor_menus,
    GRAPH_MT_view,
    GRAPH_MT_select,
    GRAPH_MT_marker,
    GRAPH_MT_channel_hide_unselected_curves,
    GRAPH_MT_channel,
    GRAPH_MT_key,
    GRAPH_MT_key_transform,
    GRAPH_MT_delete,
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
