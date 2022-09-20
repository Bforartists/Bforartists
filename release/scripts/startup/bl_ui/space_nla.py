# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.types import Header, Menu, Panel
from bpy.app.translations import contexts as i18n_contexts
from bl_ui.space_dopesheet import (
    DopesheetFilterPopoverBase,
    DopesheetActionPanelBase,
    dopesheet_filter,
)

################################ Switch between the editors ##########################################

# The blank button, we don't want to switch to the editor in which we are already.


class ANIM_OT_switch_editors_in_nla(bpy.types.Operator):
    """You are in Nonlinear Animation Editor"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "wm.switch_editor_in_nla"        # unique identifier for buttons and menu items to reference.
    bl_label = "Nonlinear Animation Editor"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # Blank button, we don't execute anything here.
        return {'FINISHED'}

##########################################


class NLA_HT_header(Header):
    bl_space_type = 'NLA_EDITOR'

    def draw(self, context):
        layout = self.layout

        st = context.space_data
        scene = context.scene

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        ALL_MT_editormenu.draw_hidden(context, layout)  # bfa - show hide the editormenu

        # Switch between the editors

        # bfa - The tabs to switch between the four animation editors. The classes are in space_dopesheet.py
        row = layout.row(align=True)

        row.operator("wm.switch_editor_to_dopesheet", text="", icon='ACTION')
        row.operator("wm.switch_editor_to_graph", text="", icon='GRAPH')
        row.operator("wm.switch_editor_to_driver", text="", icon='DRIVER')
        row.operator("wm.switch_editor_in_nla", text="", icon='NLA_ACTIVE')

        # tweak strip actions

        row = layout.row(align=True)

        if addon_prefs.nla_tweak_isolate_action:

            if scene.is_nla_tweakmode:
                row.active_default = True
                row.operator("nla.tweakmode_exit", text="Tweak", icon="ACTION_TWEAK_SOLO").isolate_action = True
                row.label(icon="CHECKBOX_HLT", text="Isolate")
            else:
                row.operator("nla.tweakmode_enter", text="Tweak", icon="ACTION_TWEAK_SOLO").isolate_action = True
                row.prop(addon_prefs, "nla_tweak_isolate_action")

        else:

            if scene.is_nla_tweakmode:
                row.active_default = True
                row.operator("nla.tweakmode_exit", text="Tweak", icon="ACTION_TWEAK")
                row.label(icon="CHECKBOX_DEHLT", text="Isolate")
            else:
                row.operator(
                    "nla.tweakmode_enter",
                    text="Tweak",
                    icon="ACTION_TWEAK").use_upper_stack_evaluation = False
                row.prop(addon_prefs, "nla_tweak_isolate_action")

        ##########################

        NLA_MT_editor_menus.draw_collapsible(context, layout)

        layout.separator_spacer()

        dopesheet_filter(layout, context)

        row = layout.row()

        row.popover(panel="NLA_PT_filters", text="", icon='FILTER')
        row.prop(st, "auto_snap", text="")
        row.popover(panel="NLA_PT_view_view_options", text="Options")


# bfa - show hide the editormenu
class ALL_MT_editormenu(Menu):
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):

        row = layout.row(align=True)
        row.template_header()  # editor type menus


class NLA_PT_filters(DopesheetFilterPopoverBase, Panel):
    bl_space_type = 'NLA_EDITOR'
    bl_region_type = 'HEADER'
    bl_label = "Filters"

    def draw(self, context):
        layout = self.layout

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
        return strip and strip.type == 'CLIP' and strip.action

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
        layout.menu("NLA_MT_edit")
        layout.menu("NLA_MT_add")


class NLA_MT_view(Menu):
    bl_label = "View"

    def draw(self, context):
        layout = self.layout

        st = context.space_data

        layout.prop(st, "show_region_channels")  # bfa - channels
        layout.prop(st, "show_region_ui")
        layout.prop(st, "show_region_hud")

        layout.separator()

        layout.operator("anim.previewrange_set", icon='BORDER_RECT')
        layout.operator("anim.previewrange_clear", icon="CLEAR")
        layout.operator("nla.previewrange_set", icon='BORDER_RECT')

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


class NLA_MT_view_pie_menus(Menu):
    bl_label = "Pie menus"

    def draw(self, _context):
        layout = self.layout

        layout.operator("wm.call_menu_pie", text="Snap", icon="MENU_PANEL").name = 'NLA_MT_snap_pie'
        layout.operator("wm.call_menu_pie", text="View", icon="MENU_PANEL").name = 'NLA_MT_view_pie'


class NLA_PT_view_view_options(Panel):
    bl_label = "View Options"
    bl_space_type = 'NLA_EDITOR'
    bl_region_type = 'HEADER'
    bl_category = 'View'

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

        layout.operator("nla.select_all", text="All", icon='SELECT_ALL').action = 'SELECT'
        layout.operator("nla.select_all", text="None", icon='SELECT_NONE').action = 'DESELECT'
        layout.operator("nla.select_all", text="Invert", icon='INVERSE').action = 'INVERT'

        layout.separator()
        layout.operator("nla.select_box", icon='BORDER_RECT').axis_range = False
        layout.operator("nla.select_box", text="Box Select (Axis Range)", icon='BORDER_RECT').axis_range = True

        layout.separator()
        props = layout.operator("nla.select_leftright", text="Before Current Frame", icon="BEFORE_CURRENT_FRAME")
        props.extend = False
        props.mode = 'LEFT'
        props = layout.operator("nla.select_leftright", text="After Current Frame", icon="BEFORE_CURRENT_FRAME")
        props.extend = False
        props.mode = 'RIGHT'


class NLA_MT_marker(Menu):
    bl_label = "Marker"

    def draw(self, context):
        layout = self.layout

        from bl_ui.space_time import marker_menu_generic
        marker_menu_generic(layout, context)


class NLA_MT_marker_select(Menu):
    bl_label = 'Select'

    def draw(self, _context):
        layout = self.layout

        layout.operator("marker.select_all", text="All", icon='SELECT_ALL').action = 'SELECT'
        layout.operator("marker.select_all", text="None", icon='SELECT_NONE').action = 'DESELECT'
        layout.operator("marker.select_all", text="Invert", icon='INVERSE').action = 'INVERT'

        layout.separator()

        layout.operator(
            "marker.select_leftright",
            text="Before Current Frame",
            icon="BEFORE_CURRENT_FRAME").mode = 'LEFT'
        layout.operator(
            "marker.select_leftright",
            text="After Current Frame",
            icon="AFTER_CURRENT_FRAME").mode = 'RIGHT'


class NLA_MT_edit(Menu):
    bl_label = "Edit"

    def draw(self, context):
        layout = self.layout

        scene = context.scene

        layout.menu("NLA_MT_edit_transform", text="Transform")

        layout.operator_menu_enum("nla.snap", "type", text="Snap")

        layout.separator()
        layout.operator("nla.bake", text="Bake Action", icon="BAKE_ACTION")
        layout.operator("nla.duplicate", text="Duplicate", icon="DUPLICATE").linked = False
        layout.operator("nla.duplicate", text="Linked Duplicate", icon="DUPLICATE").linked = True
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

        # TODO: this really belongs more in a "channel" (or better, "track") menu
        layout.separator()
        layout.operator_menu_enum("anim.channels_move", "direction", text="Track Ordering")
        layout.operator("anim.channels_clean_empty", icon="CLEAN_CHANNELS")

        layout.separator()

        layout.operator("nla.tweakmode_enter", text="Tweak (Full Stack)",
                        icon="ACTION_TWEAK").use_upper_stack_evaluation = True


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
            "nla.tracks_add",
            text="Add Tracks Above Selected",
            icon="ADD_TRACK_ABOVE").above_selected = True

        layout.separator()
        layout.operator("nla.selected_objects_add", icon="ADD_SELECTED")


class NLA_MT_edit_transform(Menu):
    bl_label = "Transform"

    def draw(self, _context):
        layout = self.layout

        layout.operator("transform.translate", text="Grab/Move", icon="TRANSFORM_MOVE")
        layout.operator("transform.transform", text="Extend", icon="SHRINK_FATTEN").mode = 'TIME_EXTEND'
        layout.operator("transform.transform", text="Scale", icon="TRANSFORM_SCALE").mode = 'TIME_SCALE'


class NLA_MT_snap_pie(Menu):
    bl_label = "Snap"

    def draw(self, _context):
        layout = self.layout
        pie = layout.menu_pie()

        pie.operator("nla.snap", text="Selection to Current Frame", icon="SNAP_CURRENTFRAME").type = 'CFRA'
        pie.operator("nla.snap", text="Selection to Nearest Frame", icon="SNAP_NEARESTFRAME").type = 'NEAREST_FRAME'
        pie.operator("nla.snap", text="Selection to Nearest Second", icon="SNAP_NEARESTSECOND").type = 'NEAREST_SECOND'
        pie.operator("nla.snap", text="Selection to Nearest Marker", icon="SNAP_NEARESTMARKER").type = 'NEAREST_MARKER'


class NLA_MT_view_pie(Menu):
    bl_label = "View"

    def draw(self, _context):
        layout = self.layout

        pie = layout.menu_pie()
        pie.operator("nla.view_all")
        pie.operator("nla.view_selected", icon='ZOOM_SELECTED')
        pie.operator("nla.view_frame")


class NLA_MT_context_menu(Menu):
    bl_label = "NLA Context Menu"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        if scene.is_nla_tweakmode:
            layout.operator(
                "nla.tweakmode_exit",
                text="Stop Editing Stashed Action",
                icon="ACTION_TWEAK_SOLO").isolate_action = True
            layout.operator("nla.tweakmode_exit", text="Stop Tweaking Strip Actions", icon="ACTION_TWEAK")
        else:
            layout.operator(
                "nla.tweakmode_enter",
                text="Start Editing Stashed Action",
                icon="ACTION_TWEAK_SOLO").isolate_action = True
            layout.operator("nla.tweakmode_enter",
                            text="Start Tweaking Strip Actions (Full Stack)",
                            icon="ACTION_TWEAK").use_upper_stack_evaluation = True
            layout.operator("nla.tweakmode_enter",
                            text="Start Tweaking Strip Actions (Lower Stack)",
                            icon="ACTION_TWEAK").use_upper_stack_evaluation = False

        layout.separator()

        props = layout.operator("wm.call_panel", text="Rename", icon="RENAME")
        props.name = "TOPBAR_PT_name"
        props.keep_open = False
        layout.operator("nla.duplicate", text="Duplicate", icon="DUPLICATE").linked = False
        layout.operator("nla.duplicate", text="Linked Duplicate", icon="DUPLICATE").linked = True

        layout.separator()

        layout.operator("nla.split", icon="SPLIT")
        layout.operator("nla.delete", icon="DELETE")

        layout.separator()

        layout.operator("nla.swap", icon="SWAP")

        layout.separator()

        layout.operator_menu_enum("nla.snap", "type", text="Snap")


class NLA_MT_channel_context_menu(Menu):
    bl_label = "NLA Channel Context Menu"

    def draw(self, _context):
        layout = self.layout

        layout.operator_menu_enum("anim.channels_move", "direction", text="Track Ordering...")
        layout.operator("anim.channels_clean_empty", icon="CLEAN_CHANNELS")


classes = (
    ANIM_OT_switch_editors_in_nla,
    ALL_MT_editormenu,
    NLA_HT_header,
    NLA_MT_edit,
    NLA_MT_editor_menus,
    NLA_MT_view,
    NLA_MT_view_pie_menus,
    NLA_PT_view_view_options,
    NLA_MT_select,
    NLA_MT_marker,
    NLA_MT_marker_select,
    NLA_MT_add,
    NLA_MT_edit_transform,
    NLA_MT_snap_pie,
    NLA_MT_view_pie,
    NLA_MT_context_menu,
    NLA_MT_channel_context_menu,
    NLA_PT_filters,
    NLA_PT_action,
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
