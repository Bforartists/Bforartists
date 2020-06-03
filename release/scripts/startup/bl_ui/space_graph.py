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
from bl_ui.space_dopesheet import (
    DopesheetFilterPopoverBase,
)

################################ Switch between the editors ##########################################

# The blank button, we don't want to switch to the editor in which we are already.

class ANIM_OT_switch_editor_in_graph(bpy.types.Operator):
    """You are in Graph Editor"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "wm.switch_editor_in_graph"        # unique identifier for buttons and menu items to reference.
    bl_label = "Graph Editor"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # Blank button, we don't execute anything here.
        return {'FINISHED'}


class ANIM_OT_switch_editor_in_driver(bpy.types.Operator):
    """You are in Driver Editor"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "wm.switch_editor_in_driver"        # unique identifier for buttons and menu items to reference.
    bl_label = "Driver Editor"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # Blank button, we don't execute anything here.
        return {'FINISHED'}

##########################################


class GRAPH_HT_header(Header):
    bl_space_type = 'GRAPH_EDITOR'

    def draw(self, context):
        layout = self.layout
        tool_settings = context.tool_settings

        st = context.space_data

        ALL_MT_editormenu.draw_hidden(context, layout) # bfa - show hide the editormenu

        # Now a exposed as a sub-space type
        # layout.prop(st, "mode", text="")

        ############################ Switch between the editors

        if context.space_data.mode == 'FCURVES':

            # bfa - The tabs to switch between the four animation editors. The classes are in space_dopesheet.py
            row = layout.row(align=True)

            row.operator("wm.switch_editor_to_dopesheet", text="", icon='ACTION')
            row.operator("wm.switch_editor_in_graph", text="", icon='GRAPH_ACTIVE')
            row.operator("wm.switch_editor_to_driver", text="", icon='DRIVER')
            row.operator("wm.switch_editor_to_nla", text="", icon='NLA')

        elif context.space_data.mode == 'DRIVERS':

            # bfa - The tabs to switch between the four animation editors. The classes are in space_dopesheet.py
            row = layout.row(align=True)

            row.operator("wm.switch_editor_to_dopesheet", text="", icon='ACTION')
            row.operator("wm.switch_editor_to_graph", text="", icon='GRAPH')
            row.operator("wm.switch_editor_in_driver", text="", icon='DRIVER_ACTIVE')
            row.operator("wm.switch_editor_to_nla", text="", icon='NLA')

        #############################

        GRAPH_MT_editor_menus.draw_collapsible(context, layout)

        layout.separator_spacer()

        row = layout.row(align=True)
        row.prop(st, "use_normalization", icon='NORMALIZE_FCURVES', text="", toggle=True)
        sub = row.row(align=True)
        if st.use_normalization:
            sub.prop(st, "use_auto_normalization", icon='FILE_REFRESH', text="", toggle=True)

        row = layout.row(align=True)
        if st.has_ghost_curves:
            row.operator("graph.ghost_curves_clear", text="", icon='X')
        else:
            row.operator("graph.ghost_curves_create", text="", icon='FCURVE_SNAPSHOT')

        layout.popover(
            panel="GRAPH_PT_filters",
            text="",
            icon='FILTER',
        )

        layout.prop(st, "auto_snap", text="")

        row = layout.row(align=True)
        row.prop(tool_settings, "use_proportional_fcurve", text="", icon_only=True)
        sub = row.row(align=True)

        if tool_settings.use_proportional_fcurve:
            sub.prop(tool_settings, "proportional_edit_falloff", text="", icon_only=True)

        layout.prop(st, "pivot_point", icon_only=True)

        layout.operator_menu_enum("graph.easing_type", "type", text="", icon = "IPO_EASE_IN_OUT")
        layout.operator_menu_enum("graph.handle_type", "type", text="", icon = "HANDLE_AUTO")
        layout.operator_menu_enum("graph.interpolation_type", "type", text="", icon = "INTERPOLATE")
        layout.prop(tool_settings, "keyframe_type", text="", icon_only=True)

# bfa - show hide the editormenu
class ALL_MT_editormenu(Menu):
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):

        row = layout.row(align=True)
        row.template_header() # editor type menus

class GRAPH_PT_filters(DopesheetFilterPopoverBase, Panel):
    bl_space_type = 'GRAPH_EDITOR'
    bl_region_type = 'HEADER'
    bl_label = "Filters"

    def draw(self, context):
        layout = self.layout

        DopesheetFilterPopoverBase.draw_generic_filters(context, layout)
        layout.separator()
        DopesheetFilterPopoverBase.draw_search_filters(context, layout)
        layout.separator()
        DopesheetFilterPopoverBase.draw_standard_filters(context, layout)


class GRAPH_PT_properties_Marker_options(Panel):
    bl_label = "Marker Options"
    bl_category = "View"
    bl_space_type = 'GRAPH_EDITOR'
    bl_region_type = 'UI'

    def draw(self, context):

        layout = self.layout
        tool_settings = context.tool_settings

        layout.prop(tool_settings, "lock_markers")


class GRAPH_PT_properties_view_options(Panel):
    bl_label = "View Options"
    bl_category = "View"
    bl_space_type = 'GRAPH_EDITOR'
    bl_region_type = 'UI'

    def draw(self, context):
        sc = context.scene
        layout = self.layout

        st = context.space_data

        layout.prop(st, "use_realtime_update")
        if st.mode != 'DRIVERS':
            layout.prop(st, "show_markers")

        layout.separator()

        col = layout.column(align = True)
        col.prop(st, "show_seconds")
        col.prop(st, "show_locked_time")

        layout.separator()

        col = layout.column(align = True)
        col.prop(st, "show_sliders")
        col.prop(st, "show_group_colors")
        col.prop(st, "use_auto_merge_keyframes")
        col.prop(st, "use_beauty_drawing")

        layout.separator()

        col = layout.column(align = True)
        col.prop(st, "show_handles")
        col.prop(st, "use_only_selected_curves_handles")
        col.prop(st, "use_only_selected_keyframe_handles")


class GRAPH_MT_editor_menus(Menu):
    bl_idname = "GRAPH_MT_editor_menus"
    bl_label = ""

    def draw(self, context):
        st = context.space_data
        layout = self.layout
        layout.menu("GRAPH_MT_view")
        layout.menu("GRAPH_MT_select")
        if st.mode != 'DRIVERS' and st.show_markers:
            layout.menu("GRAPH_MT_marker")
        layout.menu("GRAPH_MT_channel")
        layout.menu("GRAPH_MT_key")


class GRAPH_MT_view(Menu):
    bl_label = "View"

    def draw(self, context):
        layout = self.layout

        st = context.space_data

        layout.prop(st, "show_region_ui")
        layout.prop(st, "show_region_hud")

        layout.separator()

        layout.operator("anim.previewrange_set", icon='BORDER_RECT')
        layout.operator("anim.previewrange_clear", icon = "CLEAR")
        layout.operator("graph.previewrange_set", icon='BORDER_RECT')

        layout.separator()

        layout.operator("view2d.zoom_in", text = "Zoom In", icon = "ZOOM_IN")
        layout.operator("view2d.zoom_out", text = "Zoom Out", icon = "ZOOM_OUT")
        layout.operator("view2d.zoom_border", icon = "ZOOM_BORDER")

        layout.separator()

        layout.operator("graph.view_all", icon = "VIEWALL")
        layout.operator("graph.view_selected", icon = "VIEW_SELECTED")
        layout.operator("graph.view_frame", icon = "VIEW_FRAME" )

        layout.separator()

        layout.menu("INFO_MT_area")


# Workaround to separate the tooltips
class GRAPH_MT_select_inverse(bpy.types.Operator):
    """Inverts the current selection """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "graph.select_all_inverse"        # unique identifier for buttons and menu items to reference.
    bl_label = "Select Inverse"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.graph.select_all(action = 'INVERT')
        return {'FINISHED'}

# Workaround to separate the tooltips
class GRAPH_MT_select_none(bpy.types.Operator):
    """Deselects everything """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "graph.select_all_none"        # unique identifier for buttons and menu items to reference.
    bl_label = "Select None"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.graph.select_all(action = 'DESELECT')
        return {'FINISHED'}


class GRAPH_MT_select(Menu):
    bl_label = "Select"

    def draw(self, _context):
        layout = self.layout

        layout.operator("graph.select_all", text="All", icon='SELECT_ALL').action = 'SELECT'
        layout.operator("graph.select_all_none", text="None", icon='SELECT_NONE') # bfa - separated tooltip
        layout.operator("graph.select_all_inverse", text="Inverse", icon='INVERSE') # bfa - separated tooltip

        layout.separator()

        props = layout.operator("graph.select_box", icon='BORDER_RECT')
        props = layout.operator("graph.select_box", text="Box Select (Axis Range)", icon='BORDER_RECT')

        layout.operator("graph.select_circle", icon = 'CIRCLE_SELECT')

        layout.separator()

        layout.operator("graph.select_column", text="Columns on Selected Keys", icon = "COLUMNS_KEYS").mode = 'KEYS'
        layout.operator("graph.select_column", text="Column on Current Frame", icon = "COLUMN_CURRENT_FRAME").mode = 'CFRA'

        layout.operator("graph.select_column", text="Columns on Selected Markers", icon = "COLUMNS_MARKERS").mode = 'MARKERS_COLUMN'
        layout.operator("graph.select_column", text="Between Selected Markers", icon = "BETWEEN_MARKERS").mode = 'MARKERS_BETWEEN'

        layout.separator()

        layout.operator("graph.select_linked", text = "Linked", icon = "CONNECTED")

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
        marker_menu_generic(layout, context)

        # TODO: pose markers for action edit mode only?

# Workaround to separate the tooltips for Toggle Maximize Area
class GRAPH_MT_channel_hide_unselected_curves(bpy.types.Operator):
    """nHide unselected Curves from Graph Editor """      # blender will use this as a tooltip for menu items and buttons.
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

        layout.operator("anim.channels_delete", icon = "DELETE")
        if context.space_data.mode == 'DRIVERS':
            layout.operator("graph.driver_delete_invalid", icon = "DELETE")

        layout.separator()

        layout.operator("anim.channels_group", icon = "NEW_GROUP")
        layout.operator("anim.channels_ungroup", icon = "REMOVE_FROM_ALL_GROUPS")

        layout.separator()

        layout.menu("GRAPH_MT_channel_settings_toggle")

        layout.separator()

        layout.operator("anim.channels_editable_toggle", icon = "LOCKED")
        layout.menu("GRAPH_MT_channel_extrapolation")

        layout.separator()

        layout.operator("graph.reveal", icon = "HIDE_OFF")
        layout.operator("graph.hide", text="Hide Selected Curves", icon = "HIDE_ON").unselected = False
        layout.operator("graph.hide_unselected_curves", text="Hide Unselected Curves", icon = "HIDE_UNSELECTED")

        layout.separator()

        layout.operator("anim.channels_expand", icon = "EXPANDMENU")
        layout.operator("anim.channels_collapse", icon = "COLLAPSEMENU")

        layout.separator()

        layout.menu("GRAPH_MT_channel_move")

        layout.separator()

        layout.operator("anim.channels_fcurves_enable", icon = "UNLOCKED")


class GRAPH_MT_channel_settings_toggle(Menu):
    bl_label = "Channel Settings"

    def draw(self, context):
        layout = self.layout

        layout.operator("anim.channels_setting_toggle", text = "Toggle Protect", icon = "LOCKED").type = 'PROTECT'
        layout.operator("anim.channels_setting_toggle", text = "Toggle Mute", icon ="MUTE_IPO_ON").type = 'MUTE'

        layout.separator()

        layout.operator("anim.channels_setting_enable", text = "Enable Protect", icon = "LOCKED").type = 'PROTECT'
        layout.operator("anim.channels_setting_enable", text = "Enable Mute", icon = "MUTE_IPO_ON").type = 'MUTE'

        layout.separator()

        layout.operator("anim.channels_setting_disable", text = "Disable Protect", icon = "LOCKED").type = 'PROTECT'
        layout.operator("anim.channels_setting_disable", text = "Disable Mute", icon = "MUTE_IPO_ON").type = 'MUTE'

class GRAPH_MT_channel_extrapolation(Menu):
    bl_label = "Extrapolation Mode"

    def draw(self, context):
        layout = self.layout

        layout.operator("graph.extrapolation_type", text = "Constant Extrapolation", icon = "EXTRAPOLATION_CONSTANT").type = 'CONSTANT'
        layout.operator("graph.extrapolation_type", text = "Linear Extrapolation", icon = "EXTRAPOLATION_LINEAR").type = 'LINEAR'
        layout.operator("graph.extrapolation_type", text = "Make Cyclic (F-Modifier)", icon = "EXTRAPOLATION_CYCLIC").type = 'MAKE_CYCLIC'
        layout.operator("graph.extrapolation_type", text = "Clear Cyclic (F-Modifier)", icon = "EXTRAPOLATION_CYCLIC_CLEAR").type = 'CLEAR_CYCLIC'


class GRAPH_MT_channel_move(Menu):
    bl_label = "Move"

    def draw(self, context):
        layout = self.layout
        layout.operator("anim.channels_move", text= "To Top", icon = "MOVE_TO_TOP").direction = 'TOP'
        layout.operator("anim.channels_move", text= "Up", icon = "MOVE_UP").direction = 'UP'
        layout.operator("anim.channels_move", text= "Down", icon = "MOVE_DOWN").direction = 'DOWN'
        layout.operator("anim.channels_move", text= "To Bottom", icon = "MOVE_TO_BOTTOM").direction = 'BOTTOM'


class GRAPH_MT_key(Menu):
    bl_label = "Key"

    def draw(self, _context):
        layout = self.layout

        layout.menu("GRAPH_MT_key_transform", text="Transform")

        layout.menu("GRAPH_MT_key_snap")
        layout.menu("GRAPH_MT_key_mirror")

        layout.separator()

        layout.operator_menu_enum("graph.keyframe_insert", "type")
        layout.operator_menu_enum("graph.fmodifier_add", "type")
        layout.operator("graph.sound_bake", icon = "BAKE_SOUND")

        layout.separator()

        layout.operator("graph.frame_jump", icon = "CENTER")

        layout.separator()

        layout.operator("graph.copy", text="Copy Keyframes", icon='COPYDOWN')
        layout.operator("graph.paste", text="Paste Keyframes", icon='PASTEDOWN')
        layout.operator("graph.paste", text="Paste Flipped", icon='PASTEFLIPDOWN').flipped = True
        layout.operator("graph.duplicate_move", icon = "DUPLICATE")
        layout.operator("graph.delete", icon = "DELETE")

        layout.separator()

        operator_context = layout.operator_context

        layout.operator("graph.decimate", text="Decimate (Ratio)", icon = "DECIMATE").mode = 'RATIO'

        # Using the modal operation doesn't make sense for this variant
        # as we do not have a modal mode for it, so just execute it.
        layout.operator_context = 'EXEC_DEFAULT'
        layout.operator("graph.decimate", text="Decimate (Allowed Change)", icon = "DECIMATE").mode = 'ERROR'
        layout.operator_context = operator_context

        layout.operator("graph.clean", icon = "CLEAN_KEYS").channels = False
        layout.operator("graph.clean", text="Clean Channels", icon = "CLEAN_CHANNELS").channels = True
        layout.operator("graph.smooth", icon = "SMOOTH_KEYFRAMES")
        layout.operator("graph.sample", icon = "SAMPLE_KEYFRAMES")
        layout.operator("graph.bake", icon = "BAKE_CURVE")

        layout.separator()

        layout.operator("graph.euler_filter", text="Discontinuity (Euler) Filter", icon = "DISCONTINUE_EULER")


class GRAPH_MT_key_mirror(Menu):
    bl_label = "Mirror"

    def draw(self, context):
        layout = self.layout

        layout.operator("graph.mirror", text="By Times over Current Frame", icon = "MIRROR_TIME").type = 'CFRA'
        layout.operator("graph.mirror", text="By Values over Cursor Value", icon = "MIRROR_CURSORVALUE").type = 'VALUE'
        layout.operator("graph.mirror", text="By Times over Time=0", icon = "MIRROR_TIME").type = 'YAXIS'
        layout.operator("graph.mirror", text="By Values over Value=0", icon = "MIRROR_CURSORVALUE").type = 'XAXIS'
        layout.operator("graph.mirror", text="By Times over First Selected Marker", icon = "MIRROR_MARKER").type = 'MARKER'


class GRAPH_MT_key_snap(Menu):
    bl_label = "Snap"

    def draw(self, context):
        layout = self.layout

        layout.operator("graph.snap", text="Current Frame", icon = "SNAP_CURRENTFRAME").type= 'CFRA'
        layout.operator("graph.snap", text="Cursor Value", icon = "SNAP_CURSORVALUE").type= 'VALUE'
        layout.operator("graph.snap", text="Nearest Frame", icon = "SNAP_NEARESTFRAME").type= 'NEAREST_FRAME'
        layout.operator("graph.snap", text="Nearest Second", icon = "SNAP_NEARESTSECOND").type= 'NEAREST_SECOND'
        layout.operator("graph.snap", text="Nearest Marker", icon = "SNAP_NEARESTMARKER").type= 'NEAREST_MARKER'
        layout.operator("graph.snap", text="Flatten Handles", icon = "FLATTEN_HANDLER").type= 'HORIZONTAL'


class GRAPH_MT_key_transform(Menu):
    bl_label = "Transform"

    def draw(self, _context):
        layout = self.layout

        layout.operator("transform.translate", text="Grab/Move", icon = "TRANSFORM_MOVE")
        layout.operator("transform.transform", text="Extend", icon = "SHRINK_FATTEN").mode = 'TIME_EXTEND'
        layout.operator("transform.rotate", text="Rotate", icon = "TRANSFORM_ROTATE")
        layout.operator("transform.resize", text="Scale", icon = "TRANSFORM_SCALE")


class GRAPH_MT_delete(Menu):
    bl_label = "Delete"

    def draw(self, _context):
        layout = self.layout

        layout.operator("graph.delete", icon = "DELETE")

        layout.separator()

        layout.operator("graph.clean").channels = False
        layout.operator("graph.clean", text="Clean Channels").channels = True


class GRAPH_MT_context_menu(Menu):
    bl_label = "F-Curve Context Menu"

    def draw(self, _context):
        layout = self.layout

        layout.operator_context = 'INVOKE_DEFAULT'

        layout.operator("graph.copy", text="Copy", icon='COPYDOWN')
        layout.operator("graph.paste", text="Paste", icon='PASTEDOWN')
        layout.operator("graph.paste", text="Paste Flipped", icon='PASTEFLIPDOWN').flipped = True

        layout.separator()

        layout.operator_menu_enum("graph.handle_type", "type", text="Handle Type")
        layout.operator_menu_enum("graph.interpolation_type", "type", text="Interpolation Mode")
        layout.operator_menu_enum("graph.easing_type", "type", text="Easing Mode")

        layout.separator()

        layout.operator("graph.keyframe_insert", icon = "KEYFRAMES_INSERT").type = 'SEL'
        layout.operator("graph.duplicate_move", icon = "DUPLICATE")
        layout.operator_context = 'EXEC_REGION_WIN'
        layout.operator("graph.delete", icon = "DELETE")

        layout.separator()

        layout.operator_menu_enum("graph.mirror", "type", text="Mirror")
        layout.operator_menu_enum("graph.snap", "type", text="Snap")


class GRAPH_MT_pivot_pie(Menu):
    bl_label = "Pivot Point"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        pie.prop_enum(context.space_data, "pivot_point", value='BOUNDING_BOX_CENTER')
        pie.prop_enum(context.space_data, "pivot_point", value='CURSOR')
        pie.prop_enum(context.space_data, "pivot_point", value='INDIVIDUAL_ORIGINS')


class GRAPH_MT_snap_pie(Menu):
    bl_label = "Snap"

    def draw(self, _context):
        layout = self.layout
        pie = layout.menu_pie()

        pie.operator("graph.snap", text="Current Frame").type = 'CFRA'
        pie.operator("graph.snap", text="Cursor Value").type = 'VALUE'
        pie.operator("graph.snap", text="Nearest Frame").type = 'NEAREST_FRAME'
        pie.operator("graph.snap", text="Nearest Second").type = 'NEAREST_SECOND'
        pie.operator("graph.snap", text="Nearest Marker").type = 'NEAREST_MARKER'
        pie.operator("graph.snap", text="Flatten Handles").type = 'HORIZONTAL'


class GRAPH_MT_channel_context_menu(Menu):
    bl_label = "F-Curve Channel Context Menu"

    def draw(self, context):
        layout = self.layout
        st = context.space_data

        layout.separator()
        layout.operator("anim.channels_setting_enable", text="Mute Channels", icon='MUTE_IPO_ON').type = 'MUTE'
        layout.operator("anim.channels_setting_disable", text="Unmute Channels", icon='MUTE_IPO_OFF').type = 'MUTE'
        layout.separator()
        layout.operator("anim.channels_setting_enable", text="Protect Channels", icon = "LOCKED").type = 'PROTECT'
        layout.operator("anim.channels_setting_disable", text="Unprotect Channels", icon = "UNLOCKED").type = 'PROTECT'

        layout.separator()
        layout.operator("anim.channels_group", icon = "NEW_GROUP")
        layout.operator("anim.channels_ungroup", icon = "REMOVE_FROM_ALL_GROUPS")

        layout.separator()
        layout.operator("anim.channels_editable_toggle", icon='RESTRICT_SELECT_ON')
        layout.operator_menu_enum("graph.extrapolation_type", "type", text="Extrapolation Mode")

        layout.separator()
        layout.operator("graph.hide", text="Hide Selected Curves", icon='HIDE_ON').unselected = False
        layout.operator("graph.hide", text="Hide Unselected Curves", icon='HIDE_UNSELECTED').unselected = True
        layout.operator("graph.reveal", icon='HIDE_OFF')

        layout.separator()
        layout.operator("anim.channels_expand", icon = "EXPANDMENU")
        layout.operator("anim.channels_collapse", icon = "COLLAPSEMENU")

        layout.separator()
        layout.operator_menu_enum("anim.channels_move", "direction", text="Move...")

        layout.separator()

        layout.operator("anim.channels_delete", icon = "DELETE")
        if st.mode == 'DRIVERS':
            layout.operator("graph.driver_delete_invalid", icon = "DELETE")


classes = (
    ANIM_OT_switch_editor_in_graph,
    ANIM_OT_switch_editor_in_driver,
    ALL_MT_editormenu,
    GRAPH_HT_header,
    GRAPH_PT_properties_Marker_options,
    GRAPH_PT_properties_view_options,
    GRAPH_MT_editor_menus,
    GRAPH_MT_view,
    GRAPH_MT_select_inverse,
    GRAPH_MT_select_none,
    GRAPH_MT_select,
    GRAPH_MT_marker,
    GRAPH_MT_channel_hide_unselected_curves,
    GRAPH_MT_channel,
    GRAPH_MT_channel_settings_toggle,
    GRAPH_MT_channel_extrapolation,
    GRAPH_MT_channel_move,
    GRAPH_MT_key,
    GRAPH_MT_key_mirror,
    GRAPH_MT_key_snap,
    GRAPH_MT_key_transform,
    GRAPH_MT_delete,
    GRAPH_MT_context_menu,
    GRAPH_MT_channel_context_menu,
    GRAPH_MT_pivot_pie,
    GRAPH_MT_snap_pie,
    GRAPH_PT_filters,
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
