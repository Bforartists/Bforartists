# SPDX-FileCopyrightText: 2009-2023 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

from bpy.types import Header, Menu, Panel, Operator
from bpy.app.translations import (
    pgettext_iface as iface_,
    contexts as i18n_contexts,
)
from bl_ui.space_dopesheet import (
    DopesheetFilterPopoverBase,
    dopesheet_filter,
)
from bl_ui.space_time import playback_controls

# BFA - WIP - to be removed: from bl_ui.space_toolsystem_common import PlayheadSnappingPanel

# BFA - Added icons and floated properties left, also moved options to it's own menu,
# BFA - and made header menus consistent with other editors

################################ BFA - Switch between the editors ##########################################

# The blank button, we don't want to switch to the editor in which we are already.


class ANIM_OT_switch_editor_in_graph(Operator):
    """You are in the Graph Editor"""  # blender will use this as a tooltip for menu items and buttons.

    bl_idname = "wm.switch_editor_in_graph"  # unique identifier for buttons and menu items to reference.
    bl_label = "Graph Editor"  # display name in the interface.
    bl_options = {"INTERNAL"}  # use internal so it can not be searchable

    def execute(self, context):  # Blank button, we don't execute anything here.
        return {"FINISHED"}


class ANIM_OT_switch_editor_in_driver(Operator):
    """You are in the Driver Editor"""  # blender will use this as a tooltip for menu items and buttons.

    bl_idname = "wm.switch_editor_in_driver"  # unique identifier for buttons and menu items to reference.
    bl_label = "Driver Editor"  # display name in the interface.
    bl_options = {"INTERNAL"}  # use internal so it can not be searchable

    def execute(self, context):  # Blank button, we don't execute anything here.
        return {"FINISHED"}


##########################################


class GRAPH_PT_playhead_snapping(Panel):
    bl_space_type = "GRAPH_EDITOR"


def drivers_editor_footer(layout, context):
    act_fcurve = context.active_editable_fcurve
    if not act_fcurve:
        return

    act_driver = act_fcurve.driver
    if not act_driver:
        return

    layout.separator_spacer()
    layout.label(
        text=iface_("Driver: {:s} ({:s})").format(
            act_fcurve.id_data.name,
            act_fcurve.data_path,
        ),
        translate=False,
    )

    if act_driver.variables:
        layout.separator(type="LINE")
        layout.label(text=iface_("Variables: {:d}").format(len(act_driver.variables)), translate=False)

    if act_driver.type == "SCRIPTED" and act_driver.expression:
        layout.separator(type="LINE")
        layout.label(text=iface_("Expression: {:s}").format(act_driver.expression), translate=False)


class GRAPH_HT_header(Header):
    bl_space_type = "GRAPH_EDITOR"

    def draw(self, context):
        self.draw_editor_type_menu(context)

        layout = self.layout
        tool_settings = context.tool_settings

        st = context.space_data

        # Now a exposed as a sub-space type
        # layout.prop(st, "mode", text="")

        # Switch between the editors

        if context.space_data.mode == "FCURVES":
            # bfa - The tabs to switch between the four animation editors. The classes are in space_dopesheet.py
            row = layout.row(align=True)

            row.operator("wm.switch_editor_to_dopesheet", text="", icon="ACTION")
            row.operator("wm.switch_editor_in_graph", text="", icon="GRAPH_ACTIVE")
            row.operator("wm.switch_editor_to_driver", text="", icon="DRIVER")
            row.operator("wm.switch_editor_to_nla", text="", icon="NLA")

        elif context.space_data.mode == "DRIVERS":
            # bfa - The tabs to switch between the four animation editors. The classes are in space_dopesheet.py
            row = layout.row(align=True)

            row.operator("wm.switch_editor_to_dopesheet", text="", icon="ACTION")
            row.operator("wm.switch_editor_to_graph", text="", icon="GRAPH")
            row.operator("wm.switch_editor_in_driver", text="", icon="DRIVER_ACTIVE")
            row.operator("wm.switch_editor_to_nla", text="", icon="NLA")

        #############################

        GRAPH_MT_editor_menus.draw_collapsible(context, layout)

        layout.separator_spacer()

        row = layout.row(align=True)
        row.prop(st, "use_normalization", icon="NORMALIZE_FCURVES", text="", toggle=True)
        sub = row.row(align=True)
        if st.use_normalization:
            sub.prop(st, "use_auto_normalization", icon="FILE_REFRESH", text="", toggle=True)

        row = layout.row(align=True)
        if st.has_ghost_curves:
            row.operator("graph.ghost_curves_clear", text="", icon="X")
        else:
            row.operator("graph.ghost_curves_create", text="", icon="FCURVE_SNAPSHOT")

        dopesheet_filter(layout, context)

        layout.popover(panel="GRAPH_PT_filters", text="", icon="FILTER")

        if context.space_data.mode == "DRIVERS":
            row.prop(tool_settings, "use_snap_driver", text="")
            sub = row.row(align=True)
            sub.popover(
                panel="GRAPH_PT_driver_snapping",
                text="",
            )
        else:
            row.prop(tool_settings, "use_snap_anim", text="")
            sub = row.row(align=True)
            sub.popover(
                panel="GRAPH_PT_snapping",
                text="",
            )

        row = layout.row(align=True)
        row.prop(tool_settings, "use_proportional_fcurve", text="", icon_only=True)
        sub = row.row(align=True)

        if tool_settings.use_proportional_fcurve:
            sub.prop_with_popover(
                tool_settings,
                "proportional_edit_falloff",
                text="",
                icon_only=True,
                panel="GRAPH_PT_proportional_edit",
            )

        row = layout.row(align=True)

        row.prop(st, "pivot_point", icon_only=True)
        row.operator_menu_enum("graph.easing_type", "type", text="", icon="IPO_EASE_IN_OUT")
        row.operator_menu_enum("graph.handle_type", "type", text="", icon="HANDLE_AUTO")
        row.operator_menu_enum("graph.interpolation_type", "type", text="", icon="INTERPOLATE")

        row = layout.row()
        row.popover(panel="GRAPH_PT_properties_view_options", text="Options")


class GRAPH_HT_playback_controls(Header):
    bl_space_type = "GRAPH_EDITOR"
    bl_region_type = "FOOTER"

    def draw(self, context):
        layout = self.layout
        is_drivers_editor = context.space_data.mode == "DRIVERS"

        if is_drivers_editor:
            drivers_editor_footer(layout, context)
        else:
            playback_controls(layout, context)


class GRAPH_PT_proportional_edit(Panel):
    bl_space_type = "GRAPH_EDITOR"
    bl_region_type = "HEADER"
    bl_label = "Proportional Editing"
    bl_ui_units_x = 8

    def draw(self, context):
        layout = self.layout
        tool_settings = context.tool_settings
        col = layout.column()
        col.active = tool_settings.use_proportional_fcurve

        col.prop(tool_settings, "proportional_edit_falloff", expand=True)
        col.prop(tool_settings, "proportional_size")


class GRAPH_PT_filters(DopesheetFilterPopoverBase, Panel):
    bl_space_type = "GRAPH_EDITOR"
    bl_region_type = "HEADER"
    bl_label = "Filters"

    def draw(self, context):
        layout = self.layout
        st = context.space_data

        # bfa - we have the props in the header already
        # DopesheetFilterPopoverBase.draw_generic_filters(context, layout)
        # layout.separator()
        DopesheetFilterPopoverBase.draw_search_filters(context, layout)
        layout.separator()
        DopesheetFilterPopoverBase.draw_standard_filters(context, layout)

        if st.mode == "DRIVERS":
            layout.separator()
            col = layout.column(align=True)
            col.label(text="Drivers:")
            col.prop(st.dopesheet, "show_driver_fallback_as_error")


# BFA - menu
class GRAPH_PT_properties_view_options(Panel):
    bl_label = "View Options"
    bl_category = "View"
    bl_space_type = "GRAPH_EDITOR"
    bl_region_type = "HEADER"

    def draw(self, context):
        sc = context.scene
        layout = self.layout

        st = context.space_data
        tool_settings = context.tool_settings

        col = layout.column(align=True)
        col.prop(st, "use_realtime_update")
        col.prop(st, "show_seconds")
        col.prop(st, "show_locked_time")

        col = layout.column(align=True)
        col.prop(st, "show_sliders")
        col.prop(st, "use_auto_merge_keyframes")
        layout.prop(st, "use_auto_lock_translation_axis")

        col = layout.column(align=True)
        col.prop(st, "show_extrapolation")
        col.prop(st, "show_handles")
        col.prop(st, "use_only_selected_keyframe_handles")

        col = layout.column(align=True)
        if st.mode != "DRIVERS":
            col.prop(st, "show_markers")
        if context.space_data.mode != "DRIVERS":
            col.prop(tool_settings, "lock_markers")


class GRAPH_PT_snapping(Panel):
    bl_space_type = "GRAPH_EDITOR"
    bl_region_type = "HEADER"
    bl_label = "Snapping"

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.label(text="Snap To")
        tool_settings = context.tool_settings
        col.prop(tool_settings, "snap_anim_element", expand=True)
        if tool_settings.snap_anim_element != "MARKER":
            col.prop(tool_settings, "use_snap_time_absolute")


class GRAPH_PT_driver_snapping(Panel):
    bl_space_type = "GRAPH_EDITOR"
    bl_region_type = "HEADER"
    bl_label = "Snapping"

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        tool_settings = context.tool_settings
        col.prop(tool_settings, "use_snap_driver_absolute")


class GRAPH_MT_editor_menus(Menu):
    bl_idname = "GRAPH_MT_editor_menus"
    bl_label = ""

    def draw(self, context):
        st = context.space_data
        layout = self.layout
        layout.menu("SCREEN_MT_user_menu", text="Quick")  # BFA - Quick favourites menu
        layout.menu("GRAPH_MT_view")
        layout.menu("GRAPH_MT_select")
        if st.mode != "DRIVERS" and st.show_markers:
            layout.menu("GRAPH_MT_marker")
        layout.menu("GRAPH_MT_channel")
        layout.menu("GRAPH_MT_key")


class GRAPH_MT_view(Menu):
    bl_label = "View"

    def draw(self, context):
        layout = self.layout

        st = context.space_data
        layout.prop(st, "show_region_channels")  # BFA - channels
        layout.prop(st, "show_region_ui")
        layout.prop(st, "show_region_hud")
        layout.prop(st, "show_region_channels")
        if st.mode != 'DRIVERS':
            layout.prop(st, "show_region_footer", text="Playback Controls")
        layout.separator()

        layout.operator("anim.previewrange_set", icon="BORDER_RECT")
        layout.operator("anim.previewrange_clear", icon="CLEAR")
        layout.operator("graph.previewrange_set", icon="BORDER_RECT")
        if context.scene.use_preview_range:
            layout.operator(
                "anim.scene_range_frame",
                text="Frame Preview Range",
                icon="FRAME_PREVIEW_RANGE",
            )
        else:
            layout.operator(
                "anim.scene_range_frame",
                text="Frame Scene Range",
                icon="FRAME_SCENE_RANGE",
            )

        layout.separator()

        layout.operator("view2d.zoom_in", text="Zoom In", icon="ZOOM_IN")
        layout.operator("view2d.zoom_out", text="Zoom Out", icon="ZOOM_OUT")
        layout.operator("view2d.zoom_border", icon="ZOOM_BORDER")

        layout.separator()

        layout.operator("graph.view_all", icon="VIEWALL")
        layout.operator("graph.view_selected", icon="VIEW_SELECTED")
        layout.operator("graph.view_frame", icon="VIEW_FRAME")

        layout.operator("anim.view_curve_in_graph_editor", icon="VIEW_GRAPH")

        layout.separator()

        layout.menu("INFO_MT_area")
        layout.menu("GRAPH_MT_view_pie_menus")

        # Add this to show key-binding (reverse action in dope-sheet).
        layout.separator()
        props = layout.operator("wm.context_set_enum", text="Toggle Dope Sheet", icon="ACTION")
        props.data_path = "area.type"
        props.value = "DOPESHEET_EDITOR"


# BFA - menu
class GRAPH_MT_view_pie_menus(Menu):
    bl_label = "Pie Menus"

    def draw(self, _context):
        layout = self.layout

        layout.operator("wm.call_menu_pie", text="Region Toggle", icon="MENU_PANEL").name = "WM_MT_region_toggle_pie"
        layout.operator("wm.call_menu_pie", text="Pivot", icon="MENU_PANEL").name = "GRAPH_MT_pivot_pie"
        layout.operator("wm.call_menu_pie", text="Snap", icon="MENU_PANEL").name = "GRAPH_MT_snap_pie"
        layout.operator("wm.call_menu_pie", text="View", icon="MENU_PANEL").name = "GRAPH_MT_view_pie"


# BFA - menu
class GRAPH_MT_select(Menu):
    bl_label = "Select"

    def draw(self, _context):
        layout = self.layout

        layout.operator("graph.select_all", text="All", icon="SELECT_ALL").action = "SELECT"
        layout.operator("graph.select_all", text="None", icon="SELECT_NONE").action = "DESELECT"
        layout.operator("graph.select_all", text="Invert", icon="INVERSE").action = "INVERT"

        layout.separator()

        layout.operator("graph.select_box", icon="BORDER_RECT")
        props = layout.operator("graph.select_box", text="Box Select (Axis Range)", icon="BORDER_RECT")
        props.axis_range = True
        props = layout.operator("graph.select_box", text="Box Select (Include Handles)", icon="BORDER_RECT")
        props.include_handles = True
        layout.operator("graph.select_circle", icon="CIRCLE_SELECT")
        layout.operator_menu_enum("graph.select_lasso", "mode")
        # BFA - column selection moved upwards for consistency with others
        layout.separator()

        layout.operator("graph.select_column", text="Columns on Selected Keys", icon="COLUMNS_KEYS").mode = "KEYS"
        layout.operator(
            "graph.select_column",
            text="Column on Current Frame",
            icon="COLUMN_CURRENT_FRAME",
        ).mode = "CFRA"

        # BFA - just in graph editor. Drivers does not have markers. graph editor = FCURVES
        if _context.space_data.mode == "FCURVES":
            layout.operator(
                "graph.select_column",
                text="Columns on Selected Markers",
                icon="COLUMNS_MARKERS",
            ).mode = "MARKERS_COLUMN"
            layout.operator(
                "graph.select_column",
                text="Between Selected Markers",
                icon="BETWEEN_MARKERS",
            ).mode = "MARKERS_BETWEEN"

        layout.separator()
        layout.operator("graph.select_linked", text="Linked", icon="CONNECTED")

        layout.separator()

        props = layout.operator(
            "graph.select_leftright",
            text="Before Current Frame",
            icon="BEFORE_CURRENT_FRAME",
        )
        props.extend = False
        props.mode = "LEFT"
        props = layout.operator(
            "graph.select_leftright",
            text="After Current Frame",
            icon="AFTER_CURRENT_FRAME",
        )
        props.extend = False
        props.mode = "RIGHT"

        layout.separator()
        props = layout.operator("graph.select_key_handles", text="Handles", icon="SELECT_HANDLETYPE")
        props.left_handle_action = "SELECT"
        props.right_handle_action = "SELECT"
        props.key_action = "KEEP"
        props = layout.operator("graph.select_key_handles", text="Key", icon="SELECT_KEY")
        props.left_handle_action = "DESELECT"
        props.right_handle_action = "DESELECT"
        props.key_action = "SELECT"

        layout.separator()
        layout.menu("GRAPH_MT_select_more_less")


# BFA menu
class GRAPH_MT_select_more_less(Menu):
    bl_label = "More/Less"

    def draw(self, _context):
        layout = self.layout

        layout.operator("graph.select_more", text="More", icon="SELECTMORE")
        layout.operator("graph.select_less", text="Less", icon="SELECTLESS")


class GRAPH_MT_marker(Menu):
    bl_label = "Marker"

    def draw(self, context):
        layout = self.layout

        from bl_ui.space_time import marker_menu_generic

        marker_menu_generic(layout, context)

        # TODO: pose markers for action edit mode only?


class GRAPH_MT_channel(Menu):
    bl_label = "Channel"

    def draw(self, context):
        layout = self.layout
        operator_context = layout.operator_context
        layout.operator_context = "INVOKE_REGION_CHANNELS"

        layout.operator("anim.channels_delete", icon="DELETE")

        if context.space_data.mode == "DRIVERS":
            layout.operator("graph.driver_delete_invalid", icon="DELETE")

        layout.separator()

        layout.operator("anim.channels_group", icon="NEW_GROUP")
        layout.operator("anim.channels_ungroup", icon="REMOVE_FROM_ALL_GROUPS")

        layout.separator()

        layout.menu("GRAPH_MT_channel_settings_toggle")

        # BFA - Redundant operators now located in GRAPH_MT_channel_settings_toggle
        """
        layout.separator()

        layout.operator("anim.channels_setting_enable", text="Protect Channels", icon='LOCKED').type = 'PROTECT'
        layout.operator("anim.channels_setting_disable", text="Unprotect Channels", icon='UNLOCKED').type = 'PROTECT'
        layout.operator("anim.channels_editable_toggle", icon="LOCKED")
        """

        layout.separator()
        layout.menu("GRAPH_MT_channel_extrapolation")
        # To get it to display the hotkey.
        layout.operator_context = operator_context
        layout.operator_menu_enum("graph.fmodifier_add", "type", text="Add F-Curve Modifier").only_active = False
        layout.operator_context = "INVOKE_REGION_CHANNELS"

        # BFA - Redundant operators now located in GRAPH_MT_channel_settings_toggle
        """
        layout.separator()

        layout.operator("graph.keys_to_samples", icon="BAKE_CURVE")
        layout.operator("graph.samples_to_keys", icon="SAMPLE_KEYFRAMES")
        layout.operator("graph.sound_to_samples", icon="BAKE_SOUND")
        layout.operator("anim.channels_bake", icon="BAKE_ACTION")
        """

        layout.separator()

        layout.operator("graph.reveal", icon="HIDE_OFF")
        layout.operator("graph.hide", text="Hide Selected Curves", icon="HIDE_ON").unselected = False
        layout.operator("graph.hide", text="Hide Unselected Curves", icon="HIDE_UNSELECTED").unselected = True

        layout.separator()

        layout.operator("anim.channels_expand", icon="EXPANDMENU")
        layout.operator("anim.channels_collapse", icon="COLLAPSEMENU")

        layout.separator()

        layout.menu("GRAPH_MT_channel_move")

        layout.separator()

        layout.operator("anim.channels_fcurves_enable", icon="UNLOCKED")
        layout.operator(
            "graph.euler_filter",
            text="Discontinuity (Euler) Filter",
            icon="DISCONTINUE_EULER",
        )


class GRAPH_MT_channel_settings_toggle(Menu):
    bl_label = "Channel Settings"

    def draw(self, context):
        layout = self.layout

        layout.operator("anim.channels_setting_toggle", text="Toggle Protect", icon="LOCKED").type = "PROTECT"
        layout.operator("anim.channels_setting_toggle", text="Toggle Mute", icon="MUTE_IPO_ON").type = "MUTE"

        layout.separator()

        layout.operator("anim.channels_setting_disable", text="Enable Protect", icon="LOCKED").type = "PROTECT"
        layout.operator("anim.channels_setting_disable", text="Disable Protect", icon="UNLOCKED").type = "PROTECT"
        layout.operator("anim.channels_setting_disable", text="Enable Mute", icon="MUTE_IPO_OFF").type = "MUTE"
        layout.operator("anim.channels_setting_disable", text="Disable Mute", icon="MUTE_IPO_ON").type = "MUTE"


class GRAPH_MT_channel_extrapolation(Menu):
    bl_label = "Extrapolation Mode"

    def draw(self, context):
        layout = self.layout

        layout.operator(
            "graph.extrapolation_type",
            text="Constant Extrapolation",
            icon="EXTRAPOLATION_CONSTANT",
        ).type = "CONSTANT"
        layout.operator(
            "graph.extrapolation_type",
            text="Linear Extrapolation",
            icon="EXTRAPOLATION_LINEAR",
        ).type = "LINEAR"
        layout.operator(
            "graph.extrapolation_type",
            text="Make Cyclic (F-Modifier)",
            icon="EXTRAPOLATION_CYCLIC",
        ).type = "MAKE_CYCLIC"
        layout.operator(
            "graph.extrapolation_type",
            text="Clear Cyclic (F-Modifier)",
            icon="EXTRAPOLATION_CYCLIC_CLEAR",
        ).type = "CLEAR_CYCLIC"


class GRAPH_MT_channel_move(Menu):
    bl_label = "Move"

    def draw(self, context):
        layout = self.layout
        layout.operator("anim.channels_move", text="To Top", icon="MOVE_TO_TOP").direction = "TOP"
        layout.operator("anim.channels_move", text="Up", icon="MOVE_UP").direction = "UP"
        layout.operator("anim.channels_move", text="Down", icon="MOVE_DOWN").direction = "DOWN"
        layout.operator("anim.channels_move", text="To Bottom", icon="MOVE_TO_BOTTOM").direction = "BOTTOM"

        layout.separator()
        layout.operator("anim.channels_view_selected", icon="VIEW_SELECTED")


class GRAPH_MT_key_density(Menu):
    bl_label = "Density"

    def draw(self, _context):
        from _bl_ui_utils.layout import operator_context
        layout = self.layout
        layout.operator("graph.decimate", text="Decimate (Ratio)", icon="DECIMATE").mode = "RATIO"
        # Using the modal operation doesn't make sense for this variant
        # as we do not have a modal mode for it, so just execute it.
        with operator_context(layout, "EXEC_REGION_WIN"):
            layout.operator("graph.decimate", text="Decimate (Allowed Change)", icon="DECIMATE").mode = "ERROR"
        layout.operator("graph.bake_keys", icon="BAKE_ACTION")

        layout.separator()
        layout.operator("graph.clean", icon="CLEAN_KEYS").channels = False


class GRAPH_MT_key_blending(Menu):
    bl_label = "Blend"
    bl_translation_context = i18n_contexts.operator_default

    def draw(self, _context):
        layout = self.layout
        layout.operator_context = "INVOKE_DEFAULT"
        layout.operator("graph.breakdown", text="Breakdown", icon="BREAKDOWNER_POSE")
        layout.operator(
            "graph.blend_to_neighbor",
            text="Blend to Neighbor",
            icon="BLEND_TO_NEIGHBOUR",
        )
        layout.operator(
            "graph.blend_to_default",
            text="Blend to Default Value",
            icon="BLEND_TO_DEFAULT",
        )
        layout.operator("graph.ease", text="Ease", icon="IPO_EASE_IN_OUT")
        layout.operator("graph.blend_to_ease", text="Blend to Ease", icon="BLEND_TO_EASE")
        layout.operator("graph.blend_offset", text="Blend Offset", icon="BLEND_OFFSET")
        layout.operator("graph.match_slope", text="Match Slope", icon="SET_CURVE_TILT")
        layout.operator("graph.push_pull", text="Push Pull", icon="PUSH_PULL")
        layout.operator("graph.shear", text="Shear Keys", icon="SHEAR")
        layout.operator("graph.scale_average", text="Scale Average", icon="SCALE_AVERAGE")
        layout.operator("graph.scale_from_neighbor", text="Scale from Neighbor", icon="MAN_SCALE")
        layout.operator("graph.time_offset", text="Time Offset", icon="MOD_TIME")


class GRAPH_MT_key_smoothing(Menu):
    bl_label = "Smooth"
    bl_translation_context = i18n_contexts.operator_default

    def draw(self, _context):
        layout = self.layout
        layout.operator_context = "INVOKE_DEFAULT"
        layout.operator(
            "graph.gaussian_smooth",
            text="Smooth (Gaussian)",
            icon="PARTICLEBRUSH_SMOOTH",
        )
        layout.operator("graph.smooth", text="Smooth (Legacy)", icon="PARTICLEBRUSH_SMOOTH")
        layout.operator("graph.butterworth_smooth", icon="PARTICLEBRUSH_SMOOTH")


class GRAPH_MT_key(Menu):
    bl_label = "Key"

    def draw(self, _context):
        from bl_ui_utils.layout import operator_context

        layout = self.layout

        layout.menu("GRAPH_MT_key_transform", text="Transform")

        layout.menu("GRAPH_MT_key_snap")
        layout.menu("GRAPH_MT_key_mirror")

        layout.separator()

        layout.operator_menu_enum("graph.keyframe_insert", "type")

        layout.separator()

        layout.operator("graph.frame_jump", text="Jump to Selected", icon="CENTER")

        layout.separator()

        layout.operator("graph.copy", text="Copy Keyframes", icon="COPYDOWN")
        layout.operator("graph.paste", text="Paste Keyframes", icon="PASTEDOWN")
        layout.operator("graph.paste", text="Paste Flipped", icon="PASTEFLIPDOWN").flipped = True
        layout.operator("graph.duplicate_move", icon="DUPLICATE")
        layout.operator("graph.delete", icon="DELETE")

        layout.separator()

        layout.operator("graph.smooth", icon="SMOOTH_KEYFRAMES")

        # BFA - moved from Channel Settings sub-menu
        layout.separator()
        layout.operator("graph.keys_to_samples", icon="BAKE_CURVE")
        layout.operator("graph.samples_to_keys", icon="SAMPLE_KEYFRAMES")
        layout.operator("graph.sound_to_samples", icon="BAKE_SOUND")
        layout.operator("anim.channels_bake", icon="BAKE_ACTION")

        # BFA - redundant operators and menus

        layout.separator()

        layout.menu("GRAPH_MT_key_density")
        layout.menu("GRAPH_MT_key_blending")
        layout.menu("GRAPH_MT_key_smoothing")


class GRAPH_MT_key_mirror(Menu):
    bl_label = "Mirror"

    def draw(self, context):
        layout = self.layout

        layout.operator("graph.mirror", text="By Times over Current Frame", icon="MIRROR_TIME").type = "CFRA"
        layout.operator(
            "graph.mirror",
            text="By Values over Cursor Value",
            icon="MIRROR_CURSORVALUE",
        ).type = "VALUE"
        layout.operator("graph.mirror", text="By Times over Time=0", icon="MIRROR_TIME").type = "YAXIS"
        layout.operator("graph.mirror", text="By Values over Value=0", icon="MIRROR_CURSORVALUE").type = "XAXIS"
        layout.operator(
            "graph.mirror",
            text="By Times over First Selected Marker",
            icon="MIRROR_MARKER",
        ).type = "MARKER"


class GRAPH_MT_key_snap(Menu):
    bl_label = "Snap"

    def draw(self, context):
        layout = self.layout

        layout.operator("graph.snap", text="Current Frame", icon="SNAP_CURRENTFRAME").type = "CFRA"
        layout.operator("graph.snap", text="Cursor Value", icon="SNAP_CURSORVALUE").type = "VALUE"
        layout.operator("graph.snap", text="Nearest Frame", icon="SNAP_NEARESTFRAME").type = "NEAREST_FRAME"
        layout.operator("graph.snap", text="Nearest Second", icon="SNAP_NEARESTSECOND").type = "NEAREST_SECOND"
        layout.operator("graph.snap", text="Nearest Marker", icon="SNAP_NEARESTMARKER").type = "NEAREST_MARKER"
        layout.operator("graph.snap", text="Flatten Handles", icon="FLATTEN_HANDLER").type = "HORIZONTAL"
        layout.operator("graph.equalize_handles", text="Equalize Handles", icon="EQUALIZE_HANDLER").side = "BOTH"
        layout.separator()
        layout.operator("graph.frame_jump", text="Cursor to Selection", icon="JUMP_TO_KEYFRAMES")
        layout.operator(
            "graph.snap_cursor_value",
            text="Cursor Value to Selection",
            icon="VALUE_TO_SELECTION",
        )


class GRAPH_MT_key_transform(Menu):
    bl_label = "Transform"

    def draw(self, _context):
        layout = self.layout

        layout.operator("transform.translate", text="Grab/Move", icon="TRANSFORM_MOVE")
        layout.operator("transform.transform", text="Extend", icon="SHRINK_FATTEN").mode = "TIME_EXTEND"
        layout.operator("transform.rotate", text="Rotate", icon="TRANSFORM_ROTATE")
        layout.operator("transform.resize", text="Scale", icon="TRANSFORM_SCALE")


class GRAPH_MT_view_pie(Menu):
    bl_label = "View"

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()
        pie.operator("graph.view_all", icon="VIEWALL")
        pie.operator("graph.view_selected", icon="ZOOM_SELECTED")
        pie.operator("graph.view_frame", icon="VIEW_FRAME")
        if context.scene.use_preview_range:
            pie.operator("anim.scene_range_frame", text="Frame Preview Range")
        else:
            pie.operator("anim.scene_range_frame", text="Frame Scene Range")


class GRAPH_MT_delete(Menu):
    bl_label = "Delete"

    def draw(self, _context):
        layout = self.layout

        layout.operator("graph.delete", icon="DELETE")

        layout.separator()

        layout.operator("graph.clean", icon="CLEAN_KEYS").channels = False
        layout.operator("graph.clean", text="Clean Channels", icon="CLEAN_CHANNELS").channels = True


class GRAPH_MT_context_menu(Menu):
    bl_label = "F-Curve"

    def draw(self, _context):
        layout = self.layout

        layout.operator_context = "INVOKE_DEFAULT"

        layout.operator("graph.copy", text="Copy", icon="COPYDOWN")
        layout.operator("graph.paste", text="Paste", icon="PASTEDOWN")
        layout.operator("graph.paste", text="Paste Flipped", icon="PASTEFLIPDOWN").flipped = True

        layout.separator()

        layout.operator_menu_enum("graph.handle_type", "type", text="Handle Type")
        layout.operator_menu_enum("graph.interpolation_type", "type", text="Interpolation Mode")
        layout.operator_menu_enum("graph.easing_type", "type", text="Easing Mode")

        layout.separator()

        layout.operator("graph.keyframe_insert", icon="KEYFRAMES_INSERT").type = "SEL"
        layout.operator("graph.duplicate_move", icon="DUPLICATE")
        layout.operator_context = "EXEC_REGION_WIN"
        layout.operator("graph.delete", icon="DELETE")

        layout.separator()

        layout.operator_menu_enum("graph.mirror", "type", text="Mirror")
        layout.operator_menu_enum("graph.snap", "type", text="Snap")


class GRAPH_MT_pivot_pie(Menu):
    bl_label = "Pivot Point"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        pie.prop_enum(context.space_data, "pivot_point", value="BOUNDING_BOX_CENTER")
        pie.prop_enum(context.space_data, "pivot_point", value="CURSOR")
        pie.prop_enum(context.space_data, "pivot_point", value="INDIVIDUAL_ORIGINS")


class GRAPH_MT_snap_pie(Menu):
    bl_label = "Snap"

    def draw(self, _context):
        layout = self.layout
        pie = layout.menu_pie()

        pie.operator("graph.snap", text="Current Frame").type = "CFRA"
        pie.operator("graph.snap", text="Cursor Value").type = "VALUE"
        pie.operator("graph.snap", text="Nearest Frame").type = "NEAREST_FRAME"
        pie.operator("graph.snap", text="Nearest Second").type = "NEAREST_SECOND"
        pie.operator("graph.snap", text="Nearest Marker").type = "NEAREST_MARKER"
        pie.operator("graph.snap", text="Flatten Handles").type = "HORIZONTAL"
        pie.operator("graph.frame_jump", text="Cursor to Selection")
        pie.operator("graph.snap_cursor_value", text="Cursor Value to Selection")


classes = (
    ANIM_OT_switch_editor_in_graph,  # BFA - menu
    ANIM_OT_switch_editor_in_driver,  # BFA - menu
    GRAPH_HT_header,
    GRAPH_PT_properties_view_options,  # BFA - menu
    GRAPH_HT_playback_controls,
    GRAPH_PT_proportional_edit,
    GRAPH_MT_editor_menus,
    GRAPH_MT_view,
    GRAPH_MT_view_pie_menus,  # BFA - menu
    GRAPH_MT_select,
    GRAPH_MT_select_more_less,  # BFA menu
    GRAPH_MT_marker,
    GRAPH_MT_channel,
    GRAPH_MT_channel_settings_toggle,  # BFA - menu
    GRAPH_MT_channel_extrapolation,  # BFA - menu
    GRAPH_MT_channel_move,  # BFA - menu
    GRAPH_MT_key,
    GRAPH_MT_key_mirror,  # BFA - menu
    GRAPH_MT_key_density,
    GRAPH_MT_key_transform,
    GRAPH_MT_key_snap,
    GRAPH_MT_key_smoothing,
    GRAPH_MT_key_blending,
    GRAPH_MT_delete,
    GRAPH_MT_context_menu,
    GRAPH_MT_pivot_pie,
    GRAPH_MT_snap_pie,
    GRAPH_MT_view_pie,
    GRAPH_PT_filters,
    GRAPH_PT_snapping,
    GRAPH_PT_driver_snapping,
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)
