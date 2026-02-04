# SPDX-FileCopyrightText: 2009-2023 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy  # BFA
from bpy.types import Header, Menu, Panel
from bpy.app.translations import contexts as i18n_contexts
from bl_ui.space_dopesheet import (
    DopesheetFilterPopoverBase,
    DopesheetActionPanelBase,
    dopesheet_filter,
)
from bl_ui.space_time import playback_controls

################################ Switch between the editors ##########################################

# The blank button, we don't want to switch to the editor in which we are already.


class ANIM_OT_switch_editors_in_nla(bpy.types.Operator):
    """You are in the Nonlinear Animation Editor"""  # blender will use this as a tooltip for menu items and buttons.

    bl_idname = "wm.switch_editor_in_nla"  # unique identifier for buttons and menu items to reference.
    bl_label = "Nonlinear Animation Editor"  # display name in the interface.
    bl_options = {'INTERNAL'}  # use internal so it can not be searchable

    def execute(self, context):  # Blank button, we don't execute anything here.
        return {"FINISHED"}


##########################################


class NLA_HT_header(Header):
    bl_space_type = 'NLA_EDITOR'

    def draw(self, context):
        self.draw_editor_type_menu(context)
        layout = self.layout

        st = context.space_data
        scene = context.scene

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        # Switch between the editors

        # bfa - The tabs to switch between the four animation editors. The classes are in space_dopesheet.py
        row = layout.row(align=True)

        row.operator("wm.switch_editor_to_dopesheet", text="", icon="ACTION")
        row.operator("wm.switch_editor_to_graph", text="", icon="GRAPH")
        row.operator("wm.switch_editor_to_driver", text="", icon="DRIVER")
        row.operator("wm.switch_editor_in_nla", text="", icon="NLA_ACTIVE")

        # tweak strip actions

        row = layout.row(align=True)

        if addon_prefs.nla_tweak_isolate_action:
            if scene.is_nla_tweakmode:
                row.active_default = True
                row.operator(
                    "nla.tweakmode_exit", text="Tweak", icon="ACTION_TWEAK_SOLO"
                ).isolate_action = True
                row.separator()
                row.label(icon="CHECKBOX_HLT", text="Isolate")
            else:
                row.operator(
                    "nla.tweakmode_enter", text="Tweak", icon="ACTION_TWEAK_SOLO"
                ).isolate_action = True
                row.separator()
                row.prop(addon_prefs, "nla_tweak_isolate_action")

        else:
            if scene.is_nla_tweakmode:
                row.active_default = True
                row.operator("nla.tweakmode_exit", text="Tweak", icon="ACTION_TWEAK")
                row.separator()
                row.label(icon="CHECKBOX_DEHLT", text="Isolate")
            else:
                row.operator(
                    "nla.tweakmode_enter", text="Tweak", icon="ACTION_TWEAK"
                ).use_upper_stack_evaluation = True
                row.separator()
                row.prop(addon_prefs, "nla_tweak_isolate_action")

        ##########################

        NLA_MT_editor_menus.draw_collapsible(context, layout)

        layout.separator_spacer()

        dopesheet_filter(layout, context)

        row = layout.row()

        row.popover(panel="NLA_PT_filters", text="", icon="FILTER")

        row = layout.row(align=True)
        tool_settings = context.tool_settings
        row.prop(tool_settings, "use_snap_anim", text="")
        sub = row.row(align=True)
        sub.popover(
            panel="NLA_PT_snapping",
            text="",
        )

        row = layout.row(align=True)
        row.popover(panel="NLA_PT_view_view_options", text="Options")  # BFA - moved to end


class NLA_HT_playback_controls(Header):
    bl_space_type = 'NLA_EDITOR'
    bl_region_type = 'FOOTER'

    def draw(self, context):
        layout = self.layout

        playback_controls(layout, context)


class NLA_PT_snapping(Panel):
    bl_space_type = 'NLA_EDITOR'
    bl_region_type = 'HEADER'
    bl_label = "Snapping"

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.label(text="Snap To")
        tool_settings = context.tool_settings
        col.prop(tool_settings, "snap_anim_element", expand=True)
        if tool_settings.snap_anim_element != "MARKER":
            col.prop(tool_settings, "use_snap_time_absolute")


class NLA_PT_filters(DopesheetFilterPopoverBase, Panel):
    bl_space_type = 'NLA_EDITOR'
    bl_region_type = 'HEADER'
    bl_label = "Filters"

    def draw(self, context):
        layout = self.layout

        # bfa - we have the props in the header already
        # DopesheetFilterPopoverBase.draw_generic_filters(context, layout)
        # layout.separator()
        DopesheetFilterPopoverBase.draw_search_filters(context, layout)
        layout.separator()
        DopesheetFilterPopoverBase.draw_standard_filters(context, layout)


class NLA_PT_action(DopesheetActionPanelBase, Panel):
    bl_space_type = 'NLA_EDITOR'
    bl_category = "Strip"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        strip = context.active_nla_strip
        return strip and strip.type == "CLIP" and strip.action

    def draw(self, context):
        action = context.active_nla_strip.action
        self.draw_generic_panel(context, self.layout, action)


class NLA_MT_editor_menus(Menu):
    bl_idname = "NLA_MT_editor_menus"
    bl_label = ""

    def draw(self, context):
        st = context.space_data
        layout = self.layout
        layout.menu("SCREEN_MT_user_menu", text="Quick")  # Quick favourites menu
        layout.menu("NLA_MT_view")
        layout.menu("NLA_MT_select")
        if st.show_markers:
            layout.menu("NLA_MT_marker")
        layout.menu("NLA_MT_add")
        layout.menu("NLA_MT_tracks")
        layout.menu("NLA_MT_strips")


class NLA_MT_view(Menu):
    bl_label = "View"

    def draw(self, context):
        layout = self.layout

        st = context.space_data

        layout.prop(st, "show_region_channels")  # bfa - channels
        layout.prop(st, "show_region_ui")
        layout.prop(st, "show_region_hud")
        layout.prop(st, "show_region_footer", text="Playback Controls")
        layout.separator()

        layout.operator("anim.previewrange_set", icon="BORDER_RECT")
        layout.operator("anim.previewrange_clear", icon="CLEAR")
        layout.operator("nla.previewrange_set", icon="BORDER_RECT")
        if context.scene.use_preview_range:
            layout.operator("anim.scene_range_frame", text="Frame Preview Range", icon='FRAME_PREVIEW_RANGE')
        else:
            layout.operator("anim.scene_range_frame", text="Frame Scene Range", icon='FRAME_SCENE_RANGE')
        layout.separator()

        layout.operator("view2d.zoom_in", text="Zoom In", icon="ZOOM_IN")
        layout.operator("view2d.zoom_out", text="Zoom Out", icon="ZOOM_OUT")
        layout.operator("view2d.zoom_border", icon="ZOOM_BORDER")

        layout.separator()

        layout.operator("nla.view_all", icon="VIEWALL")
        layout.operator("nla.view_selected", icon="VIEW_SELECTED")
        layout.operator("nla.view_frame", icon="VIEW_FRAME")

        layout.separator()

        layout.menu("NLA_MT_view_pie_menus")
        layout.menu("INFO_MT_area")

# BFA - menu


class NLA_MT_view_pie_menus(Menu):
    bl_label = "Pie Menus"

    def draw(self, _context):
        layout = self.layout

        layout.operator("wm.call_menu_pie", text="Region Toggle", icon="MENU_PANEL").name = "WM_MT_region_toggle_pie"
        layout.operator(
            "wm.call_menu_pie", text="Snap", icon="MENU_PANEL"
        ).name = "NLA_MT_snap_pie"
        layout.operator(
            "wm.call_menu_pie", text="View", icon="MENU_PANEL"
        ).name = "NLA_MT_view_pie"

# BFA - menu


class NLA_PT_view_view_options(Panel):
    bl_label = "View Options"
    bl_space_type = 'NLA_EDITOR'
    bl_region_type = 'HEADER'
    bl_category = "View"

    def draw(self, context):
        layout = self.layout

        st = context.space_data
        tool_settings = context.tool_settings

        col = layout.column(align=True)

        col.prop(st, "use_realtime_update")
        col.prop(st, "show_seconds")
        col.prop(st, "show_locked_time")
        col.separator()

        col.prop(st, "show_strip_curves")

        col.separator()
        col.prop(st, "show_markers")
        col.prop(st, "show_local_markers")
        col.prop(tool_settings, "lock_markers")


class NLA_MT_select(Menu):
    bl_label = "Select"

    def draw(self, _context):
        layout = self.layout

        layout.operator(
            "nla.select_all", text="All", icon="SELECT_ALL"
        ).action = "SELECT"
        layout.operator(
            "nla.select_all", text="None", icon="SELECT_NONE"
        ).action = "DESELECT"
        layout.operator(
            "nla.select_all", text="Invert", icon="INVERSE"
        ).action = "INVERT"

        layout.separator()
        layout.operator("nla.select_box", icon="BORDER_RECT").axis_range = False
        layout.operator(
            "nla.select_box", text="Box Select (Axis Range)", icon="BORDER_RECT"
        ).axis_range = True

        layout.separator()
        props = layout.operator(
            "nla.select_leftright",
            text="Before Current Frame",
            icon="BEFORE_CURRENT_FRAME",
        )
        props.extend = False
        props.mode = "LEFT"
        props = layout.operator(
            "nla.select_leftright",
            text="After Current Frame",
            icon="BEFORE_CURRENT_FRAME",
        )
        props.extend = False
        props.mode = "RIGHT"


class NLA_MT_marker(Menu):
    bl_label = "Marker"

    def draw(self, context):
        layout = self.layout

        from bl_ui.space_time import marker_menu_generic
        marker_menu_generic(layout, context)


class NLA_MT_marker_select(Menu):
    bl_label = "Select"

    def draw(self, _context):
        layout = self.layout

        layout.operator(
            "marker.select_all", text="All", icon="SELECT_ALL"
        ).action = "SELECT"
        layout.operator(
            "marker.select_all", text="None", icon="SELECT_NONE"
        ).action = "DESELECT"
        layout.operator(
            "marker.select_all", text="Invert", icon="INVERSE"
        ).action = "INVERT"

        layout.separator()

        layout.operator(
            "marker.select_leftright",
            text="Before Current Frame",
            icon="BEFORE_CURRENT_FRAME",
        ).mode = "LEFT"
        layout.operator(
            "marker.select_leftright",
            text="After Current Frame",
            icon="AFTER_CURRENT_FRAME",
        ).mode = "RIGHT"


class NLA_MT_add(Menu):
    bl_label = "Add"
    bl_translation_context = i18n_contexts.operator_default

    def draw(self, _context):
        layout = self.layout

        layout.operator("nla.actionclip_add", text="Action")
        layout.operator("nla.transition_add", text="Transition")
        layout.operator("nla.soundclip_add", text="Sound")

        layout.separator()
        layout.operator("nla.selected_objects_add", text="Selected Objects")


class NLA_MT_tracks(Menu):
    bl_label = "Track"
    bl_translation_context = i18n_contexts.id_action

    def draw(self, _context):
        layout = self.layout

        layout.operator("nla.tracks_delete", text="Delete", icon='DELETE')

        layout.separator()

        layout.operator_menu_enum("anim.channels_move", "direction", text="Track Ordering")

        layout.separator()

        layout.operator("anim.channels_clean_empty", icon="CLEAN_CHANNELS")


class NLA_MT_strips(Menu):
    bl_label = "Strip"

    def draw(self, context):
        layout = self.layout

        scene = context.scene

        layout.menu("NLA_MT_strips_transform", text="Transform")
        layout.operator_menu_enum("nla.snap", "type", text="Snap")

        layout.separator()

        layout.operator("nla.bake", text="Bake Action", icon="BAKE_ACTION")
        layout.operator(
            "nla.duplicate", text="Duplicate", icon="DUPLICATE"
        ).linked = False
        layout.operator(
            "nla.duplicate", text="Linked Duplicate", icon="DUPLICATE"
        ).linked = True
        layout.operator("nla.split", icon="SPLIT")
        props = layout.operator("wm.call_panel", text="Rename", icon="RENAME")
        props.name = "TOPBAR_PT_name"
        props.keep_open = False
        layout.operator("nla.delete", icon="DELETE")
        layout.operator("nla.tracks_delete", icon="DELETE")

        layout.separator()

        layout.operator("nla.mute_toggle", icon="MUTE_IPO_ON")

        layout.separator()

        layout.operator("nla.apply_scale", icon="APPLYSCALE")
        layout.operator("nla.clear_scale", icon="CLEARSCALE")
        layout.operator("nla.action_sync_length", icon="SYNC").active = False

        layout.separator()

        layout.operator("nla.make_single_user", icon="MAKE_SINGLE_USER")

        layout.separator()

        layout.operator("nla.swap", icon="SWAP")
        layout.operator("nla.move_up", icon="MOVE_UP")
        layout.operator("nla.move_down", icon="MOVE_DOWN")

        layout.separator()

        layout.operator("anim.channels_clean_empty", icon="CLEAN_CHANNELS")

        if not scene.is_nla_tweakmode:
            layout.separator()
            layout.operator(
                "nla.tweakmode_enter",
                text="Tweak Action (Lower Stack)",
                icon="ACTION_TWEAK",
            ).use_upper_stack_evaluation = False

# BFA - menu


class NLA_MT_add(Menu):
    bl_label = "Add"
    bl_translation_context = i18n_contexts.operator_default

    def draw(self, _context):
        layout = self.layout

        layout.operator("nla.actionclip_add", icon="ADD_STRIP")
        layout.operator("nla.transition_add", icon="TRANSITION")
        layout.operator("nla.soundclip_add", icon="SOUND")

        layout.separator()
        layout.operator("nla.meta_add", icon="ADD_METASTRIP")
        layout.operator("nla.meta_remove", icon="REMOVE_METASTRIP")

        layout.separator()
        layout.operator("nla.tracks_add", icon="ADD_TRACK").above_selected = False
        layout.operator(
            "nla.tracks_add", text="Add Tracks Above Selected", icon="ADD_TRACK_ABOVE"
        ).above_selected = True

        layout.separator()
        layout.operator(
            "nla.selected_objects_add", text="Selected Objects", icon="ADD_SELECTED"
        )

# BFA - menu


class NLA_MT_strips_transform(Menu):
    bl_label = "Transform"

    def draw(self, _context):
        layout = self.layout

        layout.operator("transform.translate", text="Grab/Move", icon="TRANSFORM_MOVE")
        layout.operator(
            "transform.transform", text="Extend", icon="SHRINK_FATTEN"
        ).mode = "TIME_EXTEND"
        layout.operator(
            "transform.transform", text="Scale", icon="TRANSFORM_SCALE"
        ).mode = "TIME_SCALE"

        # BFA - moved up to top level
        # layout.separator()
        # layout.operator("nla.swap", text="Swap")

        # layout.separator()
        # layout.operator("nla.move_up", text="Move Up")
        # layout.operator("nla.move_down", text="Move Down")


class NLA_MT_snap_pie(Menu):
    bl_label = "Snap"

    def draw(self, _context):
        layout = self.layout
        pie = layout.menu_pie()

        pie.operator(
            "nla.snap", text="Selection to Current Frame", icon="SNAP_CURRENTFRAME"
        ).type = 'CFRA'
        pie.operator(
            "nla.snap", text="Selection to Nearest Frame", icon="SNAP_NEARESTFRAME"
        ).type = 'NEAREST_FRAME'
        pie.operator(
            "nla.snap", text="Selection to Nearest Second", icon="SNAP_NEARESTSECOND"
        ).type = 'NEAREST_SECOND'
        pie.operator(
            "nla.snap", text="Selection to Nearest Marker", icon="SNAP_NEARESTMARKER"
        ).type = 'NEAREST_MARKER'


class NLA_MT_view_pie(Menu):
    bl_label = "View"

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()

        pie.operator("nla.view_all", icon="VIEWALL")
        pie.operator("nla.view_selected", icon="VIEW_SELECTED")
        pie.operator("nla.view_frame", icon="VIEW_FRAME")
        if context.scene.use_preview_range:
            pie.operator("anim.scene_range_frame", text="Frame Preview Range")
        else:
            pie.operator("anim.scene_range_frame", text="Frame Scene Range")


class NLA_MT_context_menu(Menu):
    bl_label = "NLA"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        if scene.is_nla_tweakmode:
            layout.operator(
                "nla.tweakmode_exit",
                text="Stop Tweaking Isolated Action",
                icon="ACTION_TWEAK_SOLO",
            ).isolate_action = True
            layout.operator(
                "nla.tweakmode_exit", text="Stop Tweaking Action", icon="ACTION_TWEAK"
            )
        else:
            layout.operator(
                "nla.tweakmode_enter",
                text="Tweak Isolated Action",
                icon="ACTION_TWEAK_SOLO",
            ).isolate_action = True
            layout.operator(
                "nla.tweakmode_enter",
                text="Tweak Action (Full Stack)",
                icon="ACTION_TWEAK",
            ).use_upper_stack_evaluation = True
            layout.operator(
                "nla.tweakmode_enter",
                text="Tweak Action (Lower Stack)",
                icon="ACTION_TWEAK",
            ).use_upper_stack_evaluation = False

        layout.separator()

        props = layout.operator("wm.call_panel", text="Rename", icon="RENAME")
        props.name = "TOPBAR_PT_name"
        props.keep_open = False
        layout.operator("nla.duplicate_move", text="Duplicate", icon="DUPLICATE")
        layout.operator(
            "nla.duplicate_linked_move", text="Linked Duplicate", icon="DUPLICATE"
        )

        layout.separator()

        layout.operator("nla.split", icon="SPLIT")
        layout.operator("nla.delete", icon="DELETE")

        layout.separator()

        layout.operator("nla.meta_add", icon="ADD_METASTRIP")
        layout.operator("nla.meta_remove", icon="REMOVE_METASTRIP")

        layout.separator()

        layout.operator("nla.swap", icon="SWAP")

        layout.separator()

        layout.operator_menu_enum("nla.snap", "type", text="Snap")


class NLA_MT_channel_context_menu(Menu):
    bl_label = "NLA Tracks"

    def draw(self, _context):
        layout = self.layout

        layout.operator_menu_enum("anim.channels_move", "direction", text="Track Ordering")

        layout.separator()

        layout.operator("nla.tracks_add", text="Add Track").above_selected = False
        layout.operator("nla.tracks_add", text="Add Track Above Selected").above_selected = True
        layout.separator()
        layout.operator("nla.tracks_delete")
        layout.operator("anim.channels_clean_empty", icon="CLEAN_CHANNELS")


classes = (
    ANIM_OT_switch_editors_in_nla,  # BFA - menu
    NLA_HT_header,
    NLA_HT_playback_controls,
    NLA_MT_editor_menus,
    NLA_MT_view,
    NLA_MT_view_pie_menus,  # BFA - menu
    NLA_PT_view_view_options,  # BFA - menu
    NLA_MT_select,
    NLA_MT_marker,
    NLA_MT_marker_select,
    NLA_MT_add,
    NLA_MT_tracks,
    NLA_MT_strips,
    NLA_MT_strips_transform,
    NLA_MT_snap_pie,
    NLA_MT_view_pie,
    NLA_MT_context_menu,
    NLA_MT_channel_context_menu,
    NLA_PT_filters,
    NLA_PT_action,
    NLA_PT_snapping,
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
