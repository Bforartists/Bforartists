# SPDX-FileCopyrightText: 2009-2023 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

# BFA - Added icons and floated properties left
# BFA - This document is heavily modified, so like the space_view3d.py,
# BFA - compare old Blender with new Blender then splice in changes.
# BFA - Rebase compare every now and then.

import bpy
from bpy.types import (
    Header,
    Menu,
    Panel,
)
from bpy.app.translations import (
    contexts as i18n_contexts,
    pgettext_iface as iface_,
    pgettext_rpt as rpt_,
)
from bl_ui.properties_grease_pencil_common import (
    AnnotationDataPanel,
    AnnotationOnionSkin,
)
from bl_ui.space_toolsystem_common import (
    ToolActivePanelHelper,
)

from rna_prop_ui import PropertyPanel
from bl_ui.space_time import playback_controls


def _space_view_types(st):
    view_type = st.view_type
    return (
        view_type in {"SEQUENCER", "SEQUENCER_PREVIEW"},
        view_type == "PREVIEW",
    )


def selected_strips_count(context):
    selected_strips = getattr(context, "selected_strips", None)
    if selected_strips is None:
        return 0, 0

    total_count = len(selected_strips)
    nonsound_count = sum(1 for strip in selected_strips if strip.type != "SOUND")

    return total_count, nonsound_count


def draw_color_balance(layout, color_balance):
    layout.prop(color_balance, "correction_method")

    flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=False)
    flow.use_property_split = False

    if color_balance.correction_method == "LIFT_GAMMA_GAIN":
        col = flow.column()

        box = col.box()
        split = box.split(factor=0.35)
        col = split.column(align=True)
        col.label(text="Lift")
        col.separator()
        col.separator()
        col.prop(color_balance, "lift", text="")
        col.prop(color_balance, "invert_lift", text="Invert", icon="ARROW_LEFTRIGHT")
        split.template_color_picker(color_balance, "lift", value_slider=True, cubic=True)

        col = flow.column()

        box = col.box()
        split = box.split(factor=0.35)
        col = split.column(align=True)
        col.label(text="Gamma")
        col.separator()
        col.separator()
        col.prop(color_balance, "gamma", text="")
        col.prop(color_balance, "invert_gamma", text="Invert", icon="ARROW_LEFTRIGHT")
        split.template_color_picker(color_balance, "gamma", value_slider=True, lock_luminosity=True, cubic=True)

        col = flow.column()

        box = col.box()
        split = box.split(factor=0.35)
        col = split.column(align=True)
        col.label(text="Gain")
        col.separator()
        col.separator()
        col.prop(color_balance, "gain", text="")
        col.prop(color_balance, "invert_gain", text="Invert", icon="ARROW_LEFTRIGHT")
        split.template_color_picker(color_balance, "gain", value_slider=True, lock_luminosity=True, cubic=True)

    elif color_balance.correction_method == "OFFSET_POWER_SLOPE":
        col = flow.column()

        box = col.box()
        split = box.split(factor=0.35)
        col = split.column(align=True)
        col.label(text="Offset")
        col.separator()
        col.separator()
        col.prop(color_balance, "offset", text="")
        col.prop(color_balance, "invert_offset", text="Invert", icon="ARROW_LEFTRIGHT")
        split.template_color_picker(color_balance, "offset", value_slider=True, cubic=True)

        col = flow.column()

        box = col.box()
        split = box.split(factor=0.35)
        col = split.column(align=True)
        col.label(text="Power", text_ctxt=i18n_contexts.id_movieclip)
        col.separator()
        col.separator()
        col.prop(color_balance, "power", text="")
        col.prop(color_balance, "invert_power", text="Invert", icon="ARROW_LEFTRIGHT")
        split.template_color_picker(color_balance, "power", value_slider=True, cubic=True)

        col = flow.column()

        box = col.box()
        split = box.split(factor=0.35)
        col = split.column(align=True)
        col.label(text="Slope")
        col.separator()
        col.separator()
        col.prop(color_balance, "slope", text="")
        col.prop(color_balance, "invert_slope", text="Invert", icon="ARROW_LEFTRIGHT")
        split.template_color_picker(color_balance, "slope", value_slider=True, cubic=True)


class SEQUENCER_PT_active_tool(ToolActivePanelHelper, Panel):
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Tool"


class SEQUENCER_HT_tool_header(Header):
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "TOOL_HEADER"

    def draw(self, context):
        # layout = self.layout

        self.draw_tool_settings(context)

        # TODO: options popover.

    def draw_tool_settings(self, context):
        layout = self.layout

        # Active Tool
        # -----------
        from bl_ui.space_toolsystem_common import ToolSelectPanelHelper

        # Most callers assign the `tool` & `tool_mode`, currently the result is not used.
        """
        tool = ToolSelectPanelHelper.draw_active_tool_header(context, layout)
        tool_mode = context.mode if tool is None else tool.mode
        """
        # Only draw the header.
        ToolSelectPanelHelper.draw_active_tool_header(context, layout)


class SEQUENCER_HT_header(Header):
    bl_space_type = "SEQUENCE_EDITOR"

    def draw_seq(self, layout, context):  # BFA - 3D Sequencer
        pass

    def draw(self, context):
        self.draw_editor_type_menu(context)

        layout = self.layout

        st = context.space_data
        layout.prop(st, "view_type", text="")

        SEQUENCER_MT_editor_menus.draw_collapsible(context, layout)

        layout.separator_spacer()

        scene = context.sequencer_scene
        tool_settings = scene.tool_settings if scene else None
        sequencer_tool_settings = tool_settings.sequencer_tool_settings if tool_settings else None

        layout.separator_spacer()
        row = layout.row()  # BFA - 3D Sequencer
        # Sync pinned scene button
        row.label(icon="PINNED" if context.workspace.sequencer_scene else "UNPINNED")  # BFA - 3D Sequencer

        # BFA - wip merge of new sequencer
        if st.view_type == "SEQUENCER":
            row = layout.row(align=True)
            row.template_ID(context.workspace, "sequencer_scene", new="scene.new_sequencer_scene")

        if sequencer_tool_settings and st.view_type == "PREVIEW":
            row = layout.row(align=True)  # BFA
            row.prop(sequencer_tool_settings, "pivot_point", text="", icon_only=True)  # BFA

        if sequencer_tool_settings and st.view_type in {"SEQUENCER", "SEQUENCER_PREVIEW"}:
            row = layout.row(align=True)
            row.prop(sequencer_tool_settings, "overlap_mode", text="", icon_only=True)  # BFA - icon only

        if st.view_type in {"SEQUENCER", "SEQUENCER_PREVIEW"} and tool_settings:
            row = layout.row(align=True)
            row.prop(tool_settings, "use_snap_sequencer", text="")
            sub = row.row(align=True)
            sub.popover(panel="SEQUENCER_PT_snapping", text="")  # BFA - removed title

        # layout.separator_spacer()  #BFA

        if st.view_type in {"PREVIEW", "SEQUENCER_PREVIEW"}:
            layout.prop(st, "display_mode", text="", icon_only=True)
            layout.prop(st, "preview_channels", text="", icon_only=True)

            # Gizmo toggle & popover.
            row = layout.row(align=True)
            # FIXME: place-holder icon.
            row.prop(st, "show_gizmo", text="", toggle=True, icon="GIZMO")
            sub = row.row(align=True)
            sub.active = st.show_gizmo
            sub.popover(
                panel="SEQUENCER_PT_gizmo_display",
                text="",
            )

        row = layout.row(align=True)
        row.prop(st, "show_overlays", text="", icon="OVERLAY")
        sub = row.row(align=True)
        sub.popover(panel="SEQUENCER_PT_overlay", text="")
        sub.active = st.show_overlays

        row.popover(panel="SEQUENCER_PT_view_options", text="Options")
        # BFA - moved "class SEQUENCER_MT_editor_menus" below


class SEQUENCER_HT_playback_controls(Header):
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "FOOTER"

    def draw(self, context):
        layout = self.layout

        playback_controls(layout, context)


class SEQUENCER_MT_editor_menus(Menu):
    bl_idname = "SEQUENCER_MT_editor_menus"
    bl_label = ""

    def draw(self, context):
        layout = self.layout
        st = context.space_data
        has_sequencer, _has_preview = _space_view_types(st)

        layout.menu("SCREEN_MT_user_menu", text="Quick")  # Quick favourites menu
        layout.menu("SEQUENCER_MT_view")
        layout.menu("SEQUENCER_MT_select")
        layout.menu("SEQUENCER_MT_export")

        if has_sequencer and context.sequencer_scene:
            layout.menu("SEQUENCER_MT_navigation")
            if st.show_markers:
                layout.menu("SEQUENCER_MT_marker")
            layout.menu("SEQUENCER_MT_add")

        layout.menu("SEQUENCER_MT_strip")

        if st.view_type in {"SEQUENCER", "PREVIEW"}:
            layout.menu("SEQUENCER_MT_image")

        # BFA - start
        strip = context.active_strip

        if _has_preview:
            if strip and strip.type == "TEXT":
                layout.menu("SEQUENCER_MT_strip_text")
        # BFA - end


class SEQUENCER_PT_gizmo_display(Panel):
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "HEADER"
    bl_label = "Gizmos"
    bl_ui_units_x = 8

    def draw(self, context):
        layout = self.layout

        st = context.space_data

        col = layout.column()
        col.label(text="Viewport Gizmos")
        col.separator()

        col.active = st.show_gizmo
        colsub = col.column()
        colsub.prop(st, "show_gizmo_navigate", text="Navigate")
        colsub.prop(st, "show_gizmo_tool", text="Active Tools")
        # colsub.prop(st, "show_gizmo_context", text="Active Object")  # Currently unused.


class SEQUENCER_PT_overlay(Panel):
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "HEADER"
    bl_label = "Overlays"
    bl_ui_units_x = 13

    def draw(self, _context):
        pass


class SEQUENCER_PT_preview_overlay(Panel):
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "HEADER"
    bl_parent_id = "SEQUENCER_PT_overlay"
    bl_label = "Preview Overlays"

    @classmethod
    def poll(cls, context):
        st = context.space_data
        return st.view_type in {"PREVIEW", "SEQUENCER_PREVIEW"} and context.sequencer_scene

    def draw(self, context):
        ed = context.sequencer_scene.sequence_editor
        st = context.space_data
        overlay_settings = st.preview_overlay
        layout = self.layout

        layout.active = st.show_overlays and st.display_mode == "IMAGE"

        split = layout.column().split()
        col = split.column()
        col.prop(overlay_settings, "show_image_outline")
        col.prop(ed, "show_overlay_frame", text="Frame Overlay")
        col.prop(overlay_settings, "show_metadata", text="Metadata")

        col = split.column()
        col.prop(overlay_settings, "show_cursor")
        col.prop(overlay_settings, "show_safe_areas", text="Safe Areas")
        col.prop(overlay_settings, "show_annotation", text="Annotations")


class SEQUENCER_PT_sequencer_overlay(Panel):
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "HEADER"
    bl_parent_id = "SEQUENCER_PT_overlay"
    bl_label = "Sequencer Overlays"

    @classmethod
    def poll(cls, context):
        st = context.space_data
        return st.view_type in {"SEQUENCER", "SEQUENCER_PREVIEW"}

    def draw(self, context):
        st = context.space_data
        overlay_settings = st.timeline_overlay
        layout = self.layout

        layout.active = st.show_overlays
        split = layout.column().split()

        col = split.column()
        col.prop(overlay_settings, "show_grid", text="Grid")

        col = split.column()
        col.prop(st.cache_overlay, "show_cache", text="Cache")


class SEQUENCER_PT_sequencer_overlay_strips(Panel):
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "HEADER"
    bl_parent_id = "SEQUENCER_PT_overlay"
    bl_label = "Strips"

    @classmethod
    def poll(cls, context):
        st = context.space_data
        return st.view_type in {"SEQUENCER", "SEQUENCER_PREVIEW"}

    def draw(self, context):
        st = context.space_data
        overlay_settings = st.timeline_overlay
        layout = self.layout

        layout.active = st.show_overlays
        split = layout.column().split()

        col = split.column()
        col.prop(overlay_settings, "show_strip_name", text="Name")
        col.prop(overlay_settings, "show_strip_source", text="Source")
        col.prop(overlay_settings, "show_strip_duration", text="Duration")
        col.prop(overlay_settings, "show_fcurves", text="Animation Curves")

        col = split.column()
        col.prop(overlay_settings, "show_thumbnails", text="Thumbnails")
        col.prop(overlay_settings, "show_strip_tag_color", text="Color Tags")
        col.prop(overlay_settings, "show_strip_offset", text="Offsets")
        col.prop(overlay_settings, "show_strip_retiming", text="Retiming")


class SEQUENCER_PT_sequencer_overlay_waveforms(Panel):
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "HEADER"
    bl_parent_id = "SEQUENCER_PT_overlay"
    bl_label = "Waveforms"

    @classmethod
    def poll(cls, context):
        st = context.space_data
        return st.view_type in {"SEQUENCER", "SEQUENCER_PREVIEW"}

    def draw(self, context):
        st = context.space_data
        overlay_settings = st.timeline_overlay
        layout = self.layout

        layout.active = st.show_overlays

        layout.row().prop(overlay_settings, "waveform_display_type", expand=True)

        row = layout.row()
        row.prop(overlay_settings, "waveform_display_style", expand=True)
        row.active = overlay_settings.waveform_display_type != "NO_WAVEFORMS"


# BFA - Submenu
class SEQUENCER_MT_view_cache(Menu):
    bl_label = "Cache"

    def draw(self, context):
        layout = self.layout

        ed = context.equencer_scenesequence_editor
        layout.prop(ed, "show_cache")
        layout.separator()

        cache_settings = context.space_data.cache_overlay

        col = layout.column()

        show_developer_ui = context.preferences.view.show_developer_ui
        col.prop(cache_settings, "show_cache_final_out", text="Final")
        if show_developer_ui:
            col.prop(cache_settings, "show_cache_raw", text="Raw")


class SEQUENCER_MT_range(Menu):
    bl_label = "Range"

    def draw(self, _context):
        layout = self.layout

        layout.operator("anim.previewrange_set", text="Set Preview Range", icon="PREVIEW_RANGE")  # BFA
        layout.operator(
            "sequencer.set_range_to_strips",
            text="Set Preview Range to Strips",
            icon="PREVIEW_RANGE",
        ).preview = True  # BFA
        layout.operator("anim.previewrange_clear", text="Clear Preview Range", icon="CLEAR")  # BFA

        layout.separator()

        layout.operator("anim.start_frame_set", text="Set Start Frame", icon="AFTER_CURRENT_FRAME")  # BFA
        layout.operator("anim.end_frame_set", text="Set End Frame", icon="BEFORE_CURRENT_FRAME")  # BFA
        layout.operator(
            "sequencer.set_range_to_strips",
            text="Set Frame Range to Strips",
            icon="PREVIEW_RANGE",
        )  # BFA


class SEQUENCER_MT_preview_zoom(Menu):
    bl_label = "Zoom"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = "INVOKE_REGION_PREVIEW"
        from math import isclose

        current_zoom = context.space_data.zoom_percentage
        ratios = ((1, 8), (1, 4), (1, 2), (1, 1), (2, 1), (4, 1), (8, 1))

        for a, b in ratios:
            ratio = a / b
            percent = ratio * 100.0

            layout.operator(
                "sequencer.view_zoom_ratio",
                text="Zoom {:g}% ({:d}:{:d})".format(percent, a, b),  # BFA
                translate=False,
                icon="ZOOM_SET",  # BFA
            ).ratio = ratio

        # BFA - redundant zoom operators were removed


class SEQUENCER_MT_proxy(Menu):
    bl_label = "Proxy"

    def draw(self, context):
        layout = self.layout
        st = context.space_data
        _, nonsound = selected_strips_count(context)

        col = layout.column()
        col.operator("sequencer.enable_proxies", text="Setup")
        col.operator("sequencer.rebuild_proxy", text="Rebuild")
        col.enabled = nonsound >= 1
        layout.prop(st, "proxy_render_size", text="")


# BFA menu
class SEQUENCER_MT_view_pie_menus(Menu):
    bl_label = "Pie Menus"

    def draw(self, context):
        layout = self.layout

        st = context.space_data

        layout.operator_context = "INVOKE_REGION_PREVIEW"
        if st.view_type == "PREVIEW":
            layout.operator("wm.call_menu_pie", text="Pivot Point", icon="MENU_PANEL").name = "SEQUENCER_MT_pivot_pie"
        layout.operator("wm.call_menu_pie", text="View", icon="MENU_PANEL").name = "SEQUENCER_MT_preview_view_pie"


# BFA - this menu has most of the property toggles now show exclusively in the property shelf.
class SEQUENCER_MT_view_render(Menu):
    bl_label = "Render Preview"

    def draw(self, _context):
        layout = self.layout
        layout.operator("render.opengl", text="Render Sequencer Image", icon="RENDER_STILL").sequencer = True
        props = layout.operator("render.opengl", text="Render Sequencer Animation", icon="RENDER_ANIMATION")
        props.animation = True
        props.sequencer = True


class SEQUENCER_MT_view(Menu):
    bl_label = "View"

    def draw(self, context):
        layout = self.layout

        st = context.space_data
        is_preview = st.view_type in {"PREVIEW", "SEQUENCER_PREVIEW"}
        is_sequencer_view = st.view_type in {"SEQUENCER", "SEQUENCER_PREVIEW"}
        is_sequencer_only = st.view_type == "SEQUENCER"

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        # bfa - we have it already separated with correct invoke.

        # if st.view_type == 'PREVIEW':
        #     # Specifying the REGION_PREVIEW context is needed in preview-only
        #     # mode, else the lookup for the shortcut will fail in
        #     # wm_keymap_item_find_props() (see #32595).
        #     layout.operator_context = 'INVOKE_REGION_PREVIEW'
        layout.prop(st, "show_region_toolbar")
        layout.prop(st, "show_region_ui")
        layout.prop(st, "show_region_tool_header")

        layout.operator_context = "INVOKE_DEFAULT"
        if is_sequencer_view:
            layout.prop(st, "show_region_hud")
        if is_sequencer_only:
            layout.prop(st, "show_region_channels")

        layout.prop(st, "show_toolshelf_tabs")

        layout.prop(st, "show_region_footer", text="Playback Controls")
        layout.separator()

        layout.menu("SEQUENCER_MT_view_annotations")  # BFA
        # BFA - properties in properties menu

        layout.separator()

        layout.operator_context = "INVOKE_REGION_WIN"
        layout.operator("sequencer.refresh_all", icon="FILE_REFRESH", text="Refresh All")
        layout.operator_context = "INVOKE_DEFAULT"
        layout.separator()

        layout.operator_context = "INVOKE_REGION_WIN"
        layout.operator("view2d.zoom_in", icon="ZOOM_IN")
        layout.operator("view2d.zoom_out", icon="ZOOM_OUT")
        # BFA - properties in properties menu
        if is_sequencer_view:
            layout.operator_context = "INVOKE_REGION_WIN"
            layout.operator("view2d.zoom_border", text="Zoom Border", icon="ZOOM_BORDER")  # BFA

            layout.separator()

            layout.operator("sequencer.view_all", text="Frame All", icon="VIEWALL")

            if context.sequencer_scene.use_preview_range:
                layout.operator("anim.scene_range_frame", text="Frame Preview Range", icon="FRAME_PREVIEW_RANGE")
            else:
                layout.operator("anim.scene_range_frame", text="Frame Scene Range", icon="FRAME_SCENE_RANGE")

            layout.operator("sequencer.view_frame", icon="VIEW_FRAME")
            layout.operator("sequencer.view_selected", text="Frame Selected", icon="VIEW_SELECTED")

        if is_preview:
            layout.operator_context = "INVOKE_REGION_PREVIEW"

            if is_sequencer_view:
                layout.menu("SEQUENCER_MT_preview_zoom", text="Preview Zoom")
            else:
                layout.operator("view2d.zoom_border", text="Zoom Border", icon="ZOOM_BORDER")  # BFA
                layout.menu("SEQUENCER_MT_preview_zoom")
            layout.separator()

            layout.operator(
                "sequencer.view_all_preview",
                text="Fit Preview in window",
                icon="VIEW_FIT",
            )
            layout.operator("sequencer.view_selected", text="Frame Selected", icon="VIEW_SELECTED")

            layout.separator()
            layout.menu("SEQUENCER_MT_proxy")
            layout.operator_context = "INVOKE_DEFAULT"

        layout.separator()

        layout.operator_context = "INVOKE_REGION_WIN"
        layout.operator("sequencer.refresh_all", icon="FILE_REFRESH", text="Refresh All")
        layout.operator_context = "INVOKE_DEFAULT"

        layout.separator()
        # BFA - properties in properties menu

        layout.operator("render.opengl", text="Sequence Render Image", icon="RENDER_STILL").sequencer = True
        props = layout.operator("render.opengl", text="Sequence Render Animation", icon="RENDER_ANIMATION")
        props.animation = True
        props.sequencer = True
        layout.separator()

        # Note that the context is needed for the shortcut to display properly.
        layout.operator_context = "INVOKE_REGION_PREVIEW" if is_preview else "INVOKE_REGION_WIN"
        props = layout.operator(
            "wm.context_toggle_enum",
            text="Toggle Sequencer/Preview",
            icon="SEQ_SEQUENCER" if is_preview else "SEQ_PREVIEW",
        )
        props.data_path = "space_data.view_type"
        props.value_1 = "SEQUENCER"
        props.value_2 = "PREVIEW"
        layout.operator_context = "INVOKE_DEFAULT"

        layout.menu("SEQUENCER_MT_view_pie_menus")  # BFA

        layout.separator()

        layout.menu("INFO_MT_area")


# BFA - Hidden legacy operators exposed to GUI
class SEQUENCER_MT_view_annotations(Menu):
    bl_label = "Annotations (Legacy)"

    def draw(self, context):
        layout = self.layout

        layout.operator(
            "gpencil.annotate",
            text="Draw Annotation",
            icon="PAINT_DRAW",
        ).mode = "DRAW"
        layout.operator("gpencil.annotate", text="Draw Line Annotation", icon="PAINT_DRAW").mode = "DRAW_STRAIGHT"
        layout.operator("gpencil.annotate", text="Draw Polyline Annotation", icon="PAINT_DRAW").mode = "DRAW_POLY"
        layout.operator("gpencil.annotate", text="Erase Annotation", icon="ERASE").mode = "ERASER"

        layout.separator()

        layout.operator("gpencil.annotation_add", text="Add Annotation Layer", icon="ADD")
        layout.operator(
            "gpencil.annotation_active_frame_delete",
            text="Erase Annotation Active Keyframe",
            icon="DELETE",
        )


# BFA menu
class SEQUENCER_MT_export(Menu):
    bl_label = "Export"

    def draw(self, context):
        layout = self.layout

        layout.operator("sequencer.export_subtitles", text="Export Subtitles", icon="EXPORT")


class SEQUENCER_MT_select_handle(Menu):
    bl_label = "Select Handle"

    def draw(self, _context):
        layout = self.layout

        layout.operator("sequencer.select_handles", text="Both", icon="SELECT_HANDLE_BOTH").side = "BOTH"
        layout.operator("sequencer.select_handles", text="Left", icon="SELECT_HANDLE_LEFT").side = "LEFT"
        layout.operator("sequencer.select_handles", text="Right", icon="SELECT_HANDLE_RIGHT").side = "RIGHT"

        layout.separator()

        layout.operator(
            "sequencer.select_handles", text="Both Neighbors", icon="SELECT_HANDLE_BOTH"
        ).side = "BOTH_NEIGHBORS"
        layout.operator(
            "sequencer.select_handles", text="Left Neighbor", icon="SELECT_HANDLE_LEFT"
        ).side = "LEFT_NEIGHBOR"
        layout.operator(
            "sequencer.select_handles",
            text="Right Neighbor",
            icon="SELECT_HANDLE_RIGHT",
        ).side = "RIGHT_NEIGHBOR"


class SEQUENCER_MT_select_channel(Menu):
    bl_label = "Select Channel"

    def draw(self, _context):
        layout = self.layout

        layout.operator("sequencer.select_side", text="Left", icon="RESTRICT_SELECT_OFF").side = "LEFT"
        layout.operator("sequencer.select_side", text="Right", icon="RESTRICT_SELECT_OFF").side = "RIGHT"
        layout.separator()
        layout.operator("sequencer.select_side", text="Both Sides", icon="RESTRICT_SELECT_OFF").side = "BOTH"


# BFA - submenu
class SEQUENCER_MT_select_linked(Menu):
    bl_label = "Select Linked"

    def draw(self, _context):
        layout = self.layout

        layout.operator("sequencer.select_linked", text="All", icon="SELECT_ALL")
        layout.operator("sequencer.select_less", text="Less", icon="SELECTLESS")
        layout.operator("sequencer.select_more", text="More", icon="SELECTMORE")


class SEQUENCER_MT_select(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout

        st = context.space_data
        has_sequencer, has_preview = _space_view_types(st)
        # BFA - is_redtiming not used
        if has_preview:
            layout.operator_context = "INVOKE_REGION_PREVIEW"
        else:
            layout.operator_context = "INVOKE_REGION_WIN"
        layout.operator("sequencer.select_all", text="All", icon="SELECT_ALL").action = "SELECT"
        layout.operator("sequencer.select_all", text="None", icon="SELECT_NONE").action = "DESELECT"
        layout.operator("sequencer.select_all", text="Invert", icon="INVERSE").action = "INVERT"

        layout.separator()

        layout.operator("sequencer.select_box", text="Box Select", icon="BORDER_RECT")

        col = layout.column()
        if has_sequencer:
            props = col.operator(
                "sequencer.select_box",
                text="Box Select (Include Handles)",
                icon="BORDER_RECT",
            )
            props.include_handles = True

        col.separator()

        if has_sequencer:
            col.operator_menu_enum("sequencer.select_side_of_frame", "side", text="Side of Frame")
            col.menu("SEQUENCER_MT_select_handle", text="Handle")
            col.menu("SEQUENCER_MT_select_channel", text="Channel")
            col.menu("SEQUENCER_MT_select_linked", text="Linked")

        col.operator_menu_enum("sequencer.select_grouped", "type", text="Select Grouped")

        # BFA - start
        strip = context.active_strip

        if has_preview:
            if strip and strip.type == "TEXT":
                col.separator()

                col.operator(
                    "sequencer.text_select_all",
                    text="Select All Text",
                    icon="SELECT_ALL",
                )
                col.operator(
                    "sequencer.text_deselect_all",
                    text="Deselect All Text",
                    icon="SELECT_NONE",
                )

                col.separator()

                props = col.operator(
                    "sequencer.text_cursor_move",
                    text="Line End",
                    icon="HAND",
                    text_ctxt="Select",
                )
                props.type = "LINE_END"
                props.select_text = True

                props = col.operator(
                    "sequencer.text_cursor_move",
                    text="Line Begin",
                    icon="HAND",
                    text_ctxt="Select",
                )
                props.type = "LINE_BEGIN"
                props.select_text = True

                col.separator()

                props = col.operator(
                    "sequencer.text_cursor_move",
                    text="Top",
                    icon="HAND",
                    text_ctxt="Select",
                )
                props.type = "TEXT_BEGIN"
                props.select_text = True

                props = col.operator(
                    "sequencer.text_cursor_move",
                    text="Bottom",
                    icon="HAND",
                    text_ctxt="Select",
                )
                props.type = "TEXT_END"
                props.select_text = True

                col.separator()

                props = col.operator("sequencer.text_cursor_move", text="Previous Character", icon="HAND")
                props.type = "PREVIOUS_CHARACTER"
                props.select_text = True

                props = col.operator("sequencer.text_cursor_move", text="Next Character", icon="HAND")
                props.type = "NEXT_CHARACTER"
                props.select_text = True

                col.separator()

                props = col.operator("sequencer.text_cursor_move", text="Previous Word", icon="HAND")
                props.type = "PREVIOUS_WORD"
                props.select_text = True

                props = col.operator("sequencer.text_cursor_move", text="Next Word", icon="HAND")
                props.type = "NEXT_WORD"
                props.select_text = True

                col.separator()

                props = layout.operator("sequencer.text_cursor_move", text="Previous Line", icon="HAND")
                props.type = "PREVIOUS_LINE"
                props.select_text = True

                props = col.operator("sequencer.text_cursor_move", text="Next Line", icon="HAND")
                props.type = "NEXT_LINE"
                props.select_text = True
        # BFA - end


class SEQUENCER_MT_marker(Menu):
    bl_label = "Marker"

    def draw(self, context):
        layout = self.layout

        st = context.space_data
        is_sequencer_view = st.view_type in {"SEQUENCER", "SEQUENCER_PREVIEW"}

        from bl_ui.space_time import marker_menu_generic

        marker_menu_generic(layout, context)

        # BFA - no longer used
        # if is_sequencer_view:
        # 	layout.prop(st, "use_marker_sync")


class SEQUENCER_MT_change(Menu):
    bl_label = "Change"

    def draw(self, context):
        layout = self.layout
        strip = context.active_strip

        # BFA - Changed the Change contextual operator visibility to be based on strip type selection
        # BFA - This is done by listing the strip types then checking if it exists for the relevant operators
        # BFA - If there is no correct strip selected, a label will advise what to do
        try:
            layout.operator_context = "INVOKE_REGION_WIN"
            if strip and strip.type == "SCENE":
                bpy_data_scenes_len = len(bpy.data.scenes)

                layout.operator_context = 'INVOKE_DEFAULT'
                if strip and strip.type in {
                    'CROSS', 'ADD', 'SUBTRACT', 'ALPHA_OVER', 'ALPHA_UNDER',
                    'GAMMA_CROSS', 'MULTIPLY', 'WIPE', 'GLOW',
                    'SPEED', 'MULTICAM', 'ADJUSTMENT', 'GAUSSIAN_BLUR',
                }:
                    layout.menu("SEQUENCER_MT_strip_effect_change")
                    layout.operator("sequencer.swap_inputs")
                props = layout.operator("sequencer.change_path", text="Path/Files")

                strip_type = strip.type
                data_strips = ["IMAGE", "MOVIE", "SOUND"]
                effect_strips = [
                    "CROSS",
                    "ADD",
                    "SUBTRACT",
                    "ALPHA_OVER",
                    "ALPHA_UNDER",
                    "GAMMA_CROSS",
                    "MULTIPLY",
                    "WIPE",
                    "GLOW",
                    "TRANSFORM",
                    "SPEED",
                    "MULTICAM",
                    "ADJUSTMENT",
                    "GAUSSIAN_BLUR",
                ]

                if strip_type in data_strips:
                    layout.operator_context = "INVOKE_DEFAULT"
                    props = layout.operator("sequencer.change_path", text="Path/Files", icon="FILE_MOVIE")

                    if strip:
                        strip_type = strip.type

                        if strip_type == "IMAGE":
                            props.filter_image = True
                        elif strip_type == "MOVIE":
                            props.filter_movie = True
                        elif strip_type == "SOUND":
                            props.filter_sound = True
                elif strip and strip_type in effect_strips:
                    layout.operator_context = "INVOKE_DEFAULT"
                    layout.menu("SEQUENCER_MT_strip_effect_change")
                    layout.operator("sequencer.reassign_inputs")
                    layout.operator("sequencer.swap_inputs")
                else:
                    layout.label(text="Please select an effects strip", icon="QUESTION")
                    pass
        except:
            layout.label(text="Please select a strip", icon="QUESTION")
        # BFA - End of changes


class SEQUENCER_MT_navigation(Menu):
    bl_label = "Navigation"

    def draw(self, _context):
        layout = self.layout

        layout.operator("screen.animation_play", icon="PLAY")
        # layout.operator("sequencer.view_frame") # BFA - redundant

        layout.separator()

        props = layout.operator("sequencer.strip_jump", text="Jump to Previous Strip", icon="PREVIOUSACTIVE")
        props.next = False
        props.center = False
        props = layout.operator("sequencer.strip_jump", text="Jump to Next Strip", icon="NEXTACTIVE")
        props.next = True
        props.center = False

        layout.separator()

        props = layout.operator(
            "sequencer.strip_jump",
            text="Jump to Previous Strip (Center)",
            icon="PREVIOUSACTIVE",
        )
        props.next = False
        props.center = True
        props = layout.operator(
            "sequencer.strip_jump",
            text="Jump to Next Strip (Center)",
            icon="NEXTACTIVE",
        )
        props.next = True
        props.center = True

        layout.separator()

        layout.menu("SEQUENCER_MT_range")  # BFA


class SEQUENCER_MT_add(Menu):
    bl_label = "Add"
    bl_translation_context = i18n_contexts.operator_default
    bl_options = {"SEARCH_ON_KEY_PRESS"}

    def draw(self, context):
        layout = self.layout
        layout.operator_context = "INVOKE_REGION_WIN"

        layout.operator(
            "WM_OT_search_single_menu", text="Search...", icon="VIEWZOOM"
        ).menu_idname = "SEQUENCER_MT_add"  # BFA

        layout.separator()

        bpy_data_movieclips_len = len(bpy.data.movieclips)
        if bpy_data_movieclips_len > 10:
            layout.operator_context = "INVOKE_DEFAULT"
            layout.operator("sequencer.movieclip_strip_add", text="Clip...", icon="TRACKER")
        elif bpy_data_movieclips_len > 0:
            layout.operator_menu_enum("sequencer.movieclip_strip_add", "clip", text="Clip", icon="TRACKER")
        else:
            layout.menu(
                "SEQUENCER_MT_add_empty",
                text="Clip",
                text_ctxt=i18n_contexts.id_movieclip,
                icon="TRACKER",
            )
        del bpy_data_movieclips_len

        bpy_data_masks_len = len(bpy.data.masks)
        if bpy_data_masks_len > 10:
            layout.operator_context = "INVOKE_DEFAULT"
            layout.operator("sequencer.mask_strip_add", text="Mask...", icon="MOD_MASK")
        elif bpy_data_masks_len > 0:
            layout.operator_menu_enum("sequencer.mask_strip_add", "mask", text="Mask", icon="MOD_MASK")
        else:
            layout.menu("SEQUENCER_MT_add_empty", text="Mask", icon="MOD_MASK")
        del bpy_data_masks_len

        layout.separator()

        layout.operator("sequencer.movie_strip_add", text="Movie", icon="FILE_MOVIE")
        layout.operator("sequencer.sound_strip_add", text="Sound", icon="FILE_SOUND")
        layout.operator("sequencer.image_strip_add", text="Image/Sequence", icon="FILE_IMAGE")

        layout.separator()

        layout.operator_context = "INVOKE_REGION_WIN"
        layout.operator("sequencer.effect_strip_add", text="Color", icon="COLOR").type = "COLOR"
        layout.operator("sequencer.effect_strip_add", text="Text", icon="FONT_DATA").type = "TEXT"

        layout.separator()

        layout.operator("sequencer.effect_strip_add", text="Adjustment Layer", icon="COLOR").type = "ADJUSTMENT"

        layout.operator_context = "INVOKE_DEFAULT"
        layout.menu("SEQUENCER_MT_add_effect", icon="SHADERFX")

        total, nonsound = selected_strips_count(context)

        col = layout.column()
        col.menu("SEQUENCER_MT_add_transitions", icon="ARROW_LEFTRIGHT")
        # Enable for video transitions or sound crossfade.
        col.enabled = nonsound == 2 or (nonsound == 0 and total == 2)

        col = layout.column()
        # col.operator_menu_enum("sequencer.fades_add", "type", text="Fade",
        # icon='IPO_EASE_IN_OUT') # BFA - now it's own menu
        col.menu("SEQUENCER_MT_fades_add", icon="IPO_EASE_IN_OUT")
        col.enabled = total >= 1
        col.operator("sequencer.fades_clear", text="Clear Fade", icon="CLEAR")  # BFA - added icon


class SEQUENCER_MT_add_empty(Menu):
    bl_label = "Empty"

    def draw(self, _context):
        layout = self.layout

        layout.label(text="No Items Available")


class SEQUENCER_MT_add_transitions(Menu):
    bl_label = "Transition"

    def draw(self, context):
        total, nonsound = selected_strips_count(context)

        layout = self.layout

        col = layout.column()
        col.operator("sequencer.crossfade_sounds", text="Sound Crossfade", icon="SPEAKER")
        col.enabled = nonsound == 0 and total == 2

        layout.separator()

        col = layout.column()
        col.operator("sequencer.effect_strip_add", text="Cross", icon="NODE_VECTOR").type = "CROSS"
        col.operator("sequencer.effect_strip_add", text="Gamma Cross", icon="NODE_GAMMA").type = "GAMMA_CROSS"

        col.separator()

        col.operator("sequencer.effect_strip_add", text="Wipe", icon="NODE_VECTOR_TRANSFORM").type = "WIPE"
        col.enabled = nonsound == 2


class SEQUENCER_MT_add_effect(Menu):
    bl_label = "Effect Strip"

    def draw(self, context):
        total, nonsound = selected_strips_count(context)

        layout = self.layout
        layout.operator_context = "INVOKE_REGION_WIN"
        _, nonsound = selected_strips_count(context)

        layout.operator("sequencer.effect_strip_add", text="Multicam Selector", icon="SEQ_MULTICAM").type = "MULTICAM"

        layout.separator()

        col = layout.column()
        col.operator("sequencer.effect_strip_add", text="Speed Control", icon="NODE_CURVE_TIME").type = "SPEED"

        col.separator()

        col.operator(
            "sequencer.effect_strip_add",
            text="Glow",
            icon="LIGHT_SUN",
        ).type = "GLOW"
        col.operator(
            "sequencer.effect_strip_add",
            text="Gaussian Blur",
            icon="NODE_BLUR",
        ).type = "GAUSSIAN_BLUR"
        col.enabled = nonsound == 1

        layout.separator()

        col = layout.column()
        col.operator(
            "sequencer.effect_strip_add",
            text="Add",
            text_ctxt=i18n_contexts.id_sequence,
            icon="SEQ_ADD",
        ).type = "ADD"
        col.operator(
            "sequencer.effect_strip_add",
            text="Subtract",
            text_ctxt=i18n_contexts.id_sequence,
            icon="NODE_INVERT",
        ).type = "SUBTRACT"
        col.operator(
            "sequencer.effect_strip_add",
            text="Multiply",
            text_ctxt=i18n_contexts.id_sequence,
            icon="SEQ_MULTIPLY",
        ).type = "MULTIPLY"
        col.operator(
            "sequencer.effect_strip_add",
            text="Alpha Over",
            text_ctxt=i18n_contexts.id_sequence,
            icon="IMAGE_ALPHA",
        ).type = "ALPHA_OVER"
        col.operator(
            "sequencer.effect_strip_add",
            text="Alpha Under",
            text_ctxt=i18n_contexts.id_sequence,
            icon="NODE_HOLDOUTSHADER",
        ).type = "ALPHA_UNDER"
        col.operator(
            "sequencer.effect_strip_add",
            text="Color Mix",
            text_ctxt=i18n_contexts.id_sequence,
            icon="NODE_MIXRGB",
        ).type = "COLORMIX"
        col.enabled = total >= 2


class SEQUENCER_MT_strip_transform(Menu):
    bl_label = "Transform"

    def draw(self, context):
        layout = self.layout
        st = context.space_data
        has_sequencer, has_preview = _space_view_types(st)

        if has_preview:
            layout.operator_context = "INVOKE_REGION_PREVIEW"
        else:
            layout.operator_context = "INVOKE_REGION_WIN"

        col = layout.column()
        if has_preview:
            col.operator("transform.translate", text="Move", icon="TRANSFORM_MOVE")
            col.operator("transform.rotate", text="Rotate", icon="TRANSFORM_ROTATE")
            col.operator("transform.resize", text="Scale", icon="TRANSFORM_SCALE")
        else:
            col.operator("transform.seq_slide", text="Move", icon="TRANSFORM_MOVE").view2d_edge_pan = True
            col.operator(
                "transform.transform",
                text="Move/Extend from Current Frame",
                icon="SEQ_MOVE_EXTEND",
            ).mode = "TIME_EXTEND"
            col.operator("sequencer.slip", text="Slip Strip Contents", icon="SEQ_SLIP_CONTENTS")

        # TODO (for preview)
        if has_sequencer:
            col.separator()
            col.operator("sequencer.snap", icon="SEQ_SNAP_STRIP")
            col.operator("sequencer.offset_clear", icon="SEQ_CLEAR_OFFSET")

            col.separator()

        if has_sequencer:
            col.operator("sequencer.swap", text="Swap Strip Left", icon="SEQ_SWAP_LEFT").side = "LEFT"  # BFA
            col.operator("sequencer.swap", text="Swap Strip Right", icon="SEQ_SWAP_RIGHT").side = "RIGHT"  # BFA

            col.separator()
            col.operator("sequencer.gap_remove", icon="SEQ_REMOVE_GAPS").all = False
            col.operator(
                "sequencer.gap_remove",
                text="Remove Gaps (All)",
                icon="SEQ_REMOVE_GAPS_ALL",
            ).all = True
            col.operator("sequencer.gap_insert", icon="SEQ_INSERT_GAPS")
        col.enabled = bool(context.sequencer_scene)


class SEQUENCER_MT_strip_text(Menu):
    bl_label = "Text"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = "INVOKE_REGION_PREVIEW"
        layout.operator("sequencer.text_edit_mode_toggle", icon="OUTLINER_OB_FONT")
        layout.separator()
        layout.operator("sequencer.text_edit_cut", icon="CUT")  # BFA - consistent order
        layout.operator("sequencer.text_edit_copy", icon="COPYDOWN")
        layout.operator("sequencer.text_edit_paste", icon="PASTEDOWN")

        layout.separator()
        layout.menu("SEQUENCER_MT_strip_text_characters")  # BFA - menu

        layout.separator()
        props = layout.operator("sequencer.text_delete", icon="DELETE")
        props.type = "PREVIOUS_OR_SELECTION"
        layout.operator("sequencer.text_line_break", icon="CARET_NEXT_CHAR")


# BFA - Menu
class SEQUENCER_MT_strip_text_characters(Menu):
    bl_label = "Move Cursor"

    def draw(self, context):
        layout = self.layout

        layout.operator_enum("sequencer.text_cursor_move", "type")


class SEQUENCER_MT_strip_show_hide(Menu):
    bl_label = "Show/Hide"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = "INVOKE_REGION_PREVIEW"

        col = layout.column()
        col.operator("sequencer.unmute", text="Show Hidden Strips", icon="HIDE_OFF").unselected = False
        col.separator()
        col.operator("sequencer.mute", text="Hide Selected", icon="HIDE_ON").unselected = False
        col.operator("sequencer.mute", text="Hide Unselected", icon="HIDE_UNSELECTED").unselected = True
        col.enabled = bool(context.sequencer_scene)


class SEQUENCER_MT_strip_animation(Menu):
    bl_label = "Animation"

    def draw(self, _context):
        layout = self.layout
        layout.operator_context = "INVOKE_REGION_PREVIEW"

        layout.operator("anim.keyframe_insert", text="Insert Keyframe", icon="KEYFRAMES_INSERT")
        layout.operator(
            "anim.keyframe_insert_menu", text="Insert Keyframe with Keying Set", icon="KEYFRAMES_INSERT"
        ).always_prompt = True
        layout.operator("anim.keying_set_active_set", text="Change Keying Set", icon="KEYINGSET")
        layout.operator("anim.keyframe_delete_vse", text="Delete Keyframes", icon="KEYFRAMES_REMOVE")
        layout.operator("anim.keyframe_clear_vse", text="Clear Keyframes...", icon="KEYFRAMES_CLEAR")


class SEQUENCER_MT_strip_mirror(Menu):
    bl_label = "Mirror"

    def draw(self, context):
        layout = self.layout

        col = layout.column()
        col.operator_context = "INVOKE_REGION_PREVIEW"
        col.operator("transform.mirror", text="Interactive Mirror")

        col.separator()

        # Only interactive mirror should invoke the modal, all others should immediately run.
        col.operator_context = "EXEC_REGION_PREVIEW"

        for space_name, space_id in (("Global", "GLOBAL"), ("Local", "LOCAL")):
            for axis_index, axis_name in enumerate("XY"):
                props = col.operator(
                    "transform.mirror",
                    text="{:s} {:s}".format(axis_name, iface_(space_name)),
                    translate=False,
                )
                props.constraint_axis[axis_index] = True
                props.orient_type = space_id

            if space_id == "GLOBAL":
                col.separator()
        col.enabled = bool(context.sequencer_scene)


class SEQUENCER_MT_strip_input(Menu):
    bl_label = "Inputs"

    def draw(self, context):
        layout = self.layout
        strip = context.active_strip

        layout.operator("sequencer.reload", text="Reload Strips", icon="FILE_REFRESH")
        layout.operator(
            "sequencer.reload",
            text="Reload Strips and Adjust Length",
            icon="FILE_REFRESH",
        ).adjust_length = True
        props = layout.operator("sequencer.change_path", text="Change Path/Files", icon="FILE_MOVIE")
        layout.operator("sequencer.swap_data", text="Swap Data", icon="SWAP")

        if strip:
            strip_type = strip.type

            if strip_type == "IMAGE":
                props.filter_image = True
            elif strip_type == "MOVIE":
                props.filter_movie = True
            elif strip_type == "SOUND":
                props.filter_sound = True


class SEQUENCER_MT_strip_lock_mute(Menu):
    bl_label = "Lock/Mute"

    def draw(self, _context):
        layout = self.layout

        layout.operator("sequencer.lock", icon="LOCKED")
        layout.operator("sequencer.unlock", icon="UNLOCKED")

        layout.separator()

        layout.operator("sequencer.mute", icon="HIDE_ON").unselected = False
        layout.operator("sequencer.unmute", icon="HIDE_OFF").unselected = False
        layout.operator("sequencer.mute", text="Mute Unselected Strips", icon="HIDE_UNSELECTED").unselected = True
        layout.operator("sequencer.unmute", text="Unmute Deselected Strips", icon="SHOW_UNSELECTED").unselected = True


class SEQUENCER_MT_strip_modifiers(Menu):
    bl_label = "Modifiers"

    def draw(self, _context):
        layout = self.layout

        layout.menu("SEQUENCER_MT_modifier_add", text="Add Modifier")

        layout.operator("sequencer.strip_modifier_copy", text="Copy to Selected Strips...")


class SEQUENCER_MT_strip_effect(Menu):
    bl_label = "Effect Strip"

    def draw(self, _context):
        layout = self.layout

        # BFA - WIP - couple of these operators were moved to a conditional
        layout.menu("SEQUENCER_MT_strip_effect_change")
        layout.operator("sequencer.reassign_inputs", icon="RANDOMIZE_TRANSFORM")
        layout.operator("sequencer.swap_inputs", icon="RANDOMIZE")


class SEQUENCER_MT_strip_effect_change(Menu):
    bl_label = "Change Effect Type"

    def draw(self, context):
        layout = self.layout

        strip = context.active_strip

        col = layout.column()
        col.operator("sequencer.change_effect_type", text="Adjustment Layer").type = "ADJUSTMENT"
        col.operator("sequencer.change_effect_type", text="Multicam Selector").type = "MULTICAM"
        col.enabled = strip.input_count == 0

        layout.separator()

        col = layout.column()
        col.operator("sequencer.change_effect_type", text="Speed Control").type = "SPEED"
        col.operator("sequencer.change_effect_type", text="Glow").type = "GLOW"
        col.operator("sequencer.change_effect_type", text="Gaussian Blur").type = "GAUSSIAN_BLUR"
        col.enabled = strip.input_count == 1

        layout.separator()

        col = layout.column()
        col.operator("sequencer.change_effect_type", text="Add").type = "ADD"
        col.operator("sequencer.change_effect_type", text="Subtract").type = "SUBTRACT"
        col.operator("sequencer.change_effect_type", text="Multiply").type = "MULTIPLY"
        col.operator("sequencer.change_effect_type", text="Alpha Over").type = "ALPHA_OVER"
        col.operator("sequencer.change_effect_type", text="Alpha Under").type = "ALPHA_UNDER"
        col.operator("sequencer.change_effect_type", text="Color Mix").type = "COLORMIX"
        col.operator("sequencer.change_effect_type", text="Crossfade").type = "CROSS"
        col.operator("sequencer.change_effect_type", text="Gamma Crossfade").type = "GAMMA_CROSS"
        col.operator("sequencer.change_effect_type", text="Wipe").type = "WIPE"
        col.enabled = strip.input_count == 2


class SEQUENCER_MT_strip_movie(Menu):
    bl_label = "Movie Strip"

    def draw(self, _context):
        layout = self.layout

        layout.operator("sequencer.rendersize", icon="RENDER_REGION")
        layout.operator("sequencer.deinterlace_selected_movies", icon="SEQ_DEINTERLACE")


class SEQUENCER_MT_strip_retiming(Menu):
    bl_label = "Retiming"

    def draw(self, context):
        layout = self.layout
        try:  # BFA - detect if correct relevant strip is selected to apply as a clearer UX. Only works on Movie and Image strips
            is_retiming = (
                context.sequencer_scene is not None and
                context.sequencer_scene.sequence_editor is not None and
                context.sequencer_scene.sequence_editor.selected_retiming_keys is not None
            )
            strip = context.active_strip

            layout.operator_context = "INVOKE_REGION_WIN"  # BFA
            # BFA - is_redtiming not used

            strip = context.active_strip  # BFA
            strip_type = strip.type  # BFA

            if strip and strip_type == "MOVIE" or strip_type == "IMAGE" or strip_type == "SOUND":
                # BFA - Moved retiming_show and retiming_segment_speed_set to top for UX
                layout.operator(
                    "sequencer.retiming_show",
                    # BFA - changed icon and title
                    icon="MOD_TIME" if (strip and strip.show_retiming_keys) else "TIME",
                    text="Disable Retiming" if (strip and strip.show_retiming_keys) else "Enable Retiming",
                )
                layout.separator()
                layout.operator("sequencer.retiming_segment_speed_set", icon="SET_TIME")  # BFA - moved up for UX

                layout.separator()  # BFA - added seperator

                layout.operator("sequencer.retiming_key_add", icon="KEYFRAMES_INSERT")
                layout.operator("sequencer.retiming_key_delete", icon="DELETE")
                layout.operator(
                    "sequencer.retiming_add_freeze_frame_slide",
                    icon="KEYTYPE_MOVING_HOLD_VEC",
                )
                col = layout.column()
                col.operator("sequencer.retiming_add_transition_slide", icon="NODE_CURVE_TIME")
                col.enabled = is_retiming

                layout.separator()

                col = layout.column()

                col.operator("sequencer.retiming_reset", icon="KEYFRAMES_REMOVE")
                col.enabled = not is_retiming
            else:
                layout.label(text="To retime, select a movie or sound strip", icon="QUESTION")  # BFA
        except:
            layout.label(text="To retime, select a movie or sound strip", icon="QUESTION")  # BFA


# BFA menu
class SEQUENCER_MT_change_scene_with_icons(Menu):
    bl_label = "Change Scene with Icons"

    def draw(self, context):
        layout = self.layout
        scenes = bpy.data.scenes
        current_scene_name = context.sequencer_scene.name  # Get the current scene name
        for scene in scenes:
            # Skip the current scene to avoid the error
            if scene.name == current_scene_name:
                continue
            # Here 'SCENE_DATA' is used as a placeholder icon for all items
            layout.operator("sequencer.change_scene", text=scene.name, icon="SCENE_DATA").scene = scene.name


class SEQUENCER_MT_strip(Menu):
    bl_label = "Strip"

    def draw(self, context):
        from bl_ui_utils.layout import operator_context

        layout = self.layout
        st = context.space_data
        has_sequencer, has_preview = _space_view_types(st)

        layout.menu("SEQUENCER_MT_strip_transform")

        if has_preview:
            layout.operator_context = "INVOKE_REGION_PREVIEW"
        else:
            layout.operator_context = "INVOKE_REGION_WIN"

        strip = context.active_strip

        if has_preview:
            layout.menu("SEQUENCER_MT_strip_mirror")
            layout.separator()
            layout.operator("sequencer.preview_duplicate_move", text="Duplicate", icon="DUPLICATE")
            layout.separator()

            layout.menu("SEQUENCER_MT_strip_animation")

            layout.separator()

            layout.menu("SEQUENCER_MT_strip_show_hide")

            layout.separator()

        if has_sequencer:
            layout.menu("SEQUENCER_MT_strip_retiming")
            layout.separator()

            with operator_context(layout, "EXEC_REGION_WIN"):
                props = layout.operator(
                    "sequencer.split", text="Split", text_ctxt=i18n_contexts.id_sequence, icon="CUT"
                )
                props.type = "SOFT"

                props = layout.operator(
                    "sequencer.split", text="Hold Split", text_ctxt=i18n_contexts.id_sequence, icon="HOLD_SPLIT"
                )
                props.type = "HARD"

            layout.separator()

            layout.operator("sequencer.copy", text="Copy", icon="COPYDOWN")
            layout.operator("sequencer.paste", text="Paste", icon="PASTEDOWN")
            layout.operator("sequencer.duplicate_move", icon="DUPLICATE")
            layout.operator("sequencer.duplicate_move_linked", text="Duplicate Linked", icon="DUPLICATE")

        layout.separator()
        layout.operator("sequencer.delete", text="Delete", icon="DELETE")

        if strip and strip.type == "SCENE":
            layout.operator("sequencer.delete", text="Delete Strip & Data", icon="DELETE_DUPLICATE").delete_data = True
            layout.operator("sequencer.scene_frame_range_update", icon="NODE_MAP_RANGE")

        # layout.menu("SEQUENCER_MT_change") # BFA - replaced to be a top-level series of conditional operators

        # BFA - Changed the Change contextual operator visibility to be based on strip type selection
        # BFA - This is done by listing the strip types then checking if it exists for the relevant operators
        # BFA - If there is no correct strip selected, a label will advise what to do
        try:
            layout.operator_context = "INVOKE_REGION_WIN"
            if strip and strip.type == "SCENE":
                bpy_data_scenes_len = len(bpy.data.scenes)

                if bpy_data_scenes_len > 14:
                    layout.separator()
                    layout.operator_context = "INVOKE_DEFAULT"
                    layout.operator("sequencer.change_scene", text="Change Scene", icon="SCENE_DATA")
                elif bpy_data_scenes_len > 1:
                    layout.separator()
                    layout.menu("SEQUENCER_MT_change_scene_with_icons", text="Change Scene")
                del bpy_data_scenes_len
            else:
                layout.operator_context = "INVOKE_DEFAULT"

                strip_type = strip.type
                data_strips = ["IMAGE", "MOVIE", "SOUND"]
                effect_strips = [
                    "GAUSSIAN_BLUR",
                    "SPEED",
                    'GLOW"',
                    "TRANSFORM",
                    "MULTICAM",
                    "ADD",
                    "SUBRACT",
                    "ALPHA_OVER",
                    "ALPHA_UNDER",
                    "COLORMIX",
                ]

                if strip_type in data_strips:
                    layout.operator_context = "INVOKE_DEFAULT"
                    layout.separator()
                    props = layout.operator(
                        "sequencer.change_path",
                        text="Change Path/Files",
                        icon="FILE_MOVIE",
                    )

                    if strip:
                        strip_type = strip.type

                        if strip_type == "IMAGE":
                            props.filter_image = True
                        elif strip_type == "MOVIE":
                            props.filter_movie = True
                        elif strip_type == "SOUND":
                            props.filter_sound = True
                elif strip_type in effect_strips:
                    layout.operator_context = "INVOKE_DEFAULT"
                    layout.separator()
                    layout.operator("sequencer.change_effect_input")
                    layout.operator_menu_enum("sequencer.change_effect_type", "type")
                else:
                    # layout.label(text="Please select a changeable strip", icon="QUESTION")
                    pass
        except:
            # layout.label(text="Please select a strip to change", icon="QUESTION")
            pass
        # BFA - End of changes

        if has_sequencer:
            if strip:
                strip_type = strip.type
                layout.separator()
                layout.menu("SEQUENCER_MT_strip_modifiers", icon="MODIFIER")

                if strip_type in {
                        'CROSS', 'ADD', 'SUBTRACT', 'ALPHA_OVER', 'ALPHA_UNDER',
                        'GAMMA_CROSS', 'MULTIPLY', 'WIPE', 'GLOW',
                        'SPEED', 'MULTICAM', 'ADJUSTMENT', 'GAUSSIAN_BLUR',
                }:
                    layout.separator()
                    layout.menu("SEQUENCER_MT_strip_effect")
                elif strip_type == "MOVIE":
                    layout.separator()
                    layout.menu("SEQUENCER_MT_strip_movie")
                elif strip_type == "IMAGE":
                    layout.separator()
                    layout.operator("sequencer.rendersize", icon="RENDER_REGION")
                    layout.operator("sequencer.images_separate", icon="SEPARATE")
                elif strip_type == "TEXT":
                    layout.separator()
                    layout.menu("SEQUENCER_MT_strip_effect")
                elif strip_type == "META":
                    layout.separator()
                    layout.operator("sequencer.meta_make", icon="ADD_METASTRIP")
                    layout.operator("sequencer.meta_separate", icon="REMOVE_METASTRIP")
                    layout.operator("sequencer.meta_toggle", text="Toggle Meta", icon="TOGGLE_META")
                if strip_type != "META":
                    layout.separator()
                    layout.operator("sequencer.meta_make", icon="ADD_METASTRIP")
                    layout.operator("sequencer.meta_toggle", text="Toggle Meta", icon="TOGGLE_META")

        if has_sequencer:
            layout.separator()
            layout.menu("SEQUENCER_MT_color_tag_picker")

            layout.separator()
            layout.menu("SEQUENCER_MT_strip_lock_mute")

            layout.separator()
            layout.menu("SEQUENCER_MT_strip_input")

            layout.separator()
            layout.operator("sequencer.connect", icon="LINKED").toggle = True
            layout.operator("sequencer.disconnect", icon="UNLINKED")

        # bfa - preview mode only
        if has_preview:
            layout.separator()
            layout.menu("SEQUENCER_MT_strip_lock_mute")


class SEQUENCER_MT_image(Menu):
    bl_label = "Image"

    def draw(self, context):
        layout = self.layout
        st = context.space_data

        if st.view_type in {"PREVIEW", "SEQUENCER_PREVIEW"}:
            layout.menu("SEQUENCER_MT_image_transform")

        layout.menu("SEQUENCER_MT_image_clear")
        # BFA - moved these up
        layout.separator()

        layout.operator("sequencer.strip_transform_fit", text="Scale To Fit", icon="VIEW_FIT").fit_method = "FIT"
        layout.operator("sequencer.strip_transform_fit", text="Scale to Fill", icon="VIEW_FILL").fit_method = "FILL"
        layout.operator(
            "sequencer.strip_transform_fit", text="Stretch To Fill", icon="VIEW_STRETCH"
        ).fit_method = "STRETCH"


class SEQUENCER_MT_image_transform(Menu):
    bl_label = "Transform"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = "INVOKE_REGION_PREVIEW"

        col = layout.column()
        col.operator("transform.translate", icon="TRANSFORM_MOVE")
        col.operator("transform.rotate", icon="TRANSFORM_ROTATE")
        col.operator("transform.resize", text="Scale", icon="TRANSFORM_SCALE")
        col.separator()
        col.operator("transform.translate", text="Move Origin", icon="OBJECT_ORIGIN").translate_origin = True
        col.enabled = bool(context.sequencer_scene)


# BFA - Was used in the image menu. But not used in the UI anymore, remains for compatibility
class SEQUENCER_MT_image_clear(Menu):
    bl_label = "Clear"

    def draw(self, _context):
        layout = self.layout
        layout.operator(
            "sequencer.strip_transform_clear",
            text="Position",
            icon="CLEARMOVE",
            text_ctxt=i18n_contexts.default,
        ).property = "POSITION"
        layout.operator(
            "sequencer.strip_transform_clear",
            text="Scale",
            icon="CLEARSCALE",
            text_ctxt=i18n_contexts.default,
        ).property = "SCALE"
        layout.operator(
            "sequencer.strip_transform_clear",
            text="Rotation",
            icon="CLEARROTATE",
            text_ctxt=i18n_contexts.default,
        ).property = "ROTATION"
        layout.operator("sequencer.strip_transform_clear", text="All Transforms", icon="CLEAR").property = "ALL"


class SEQUENCER_MT_image_apply(Menu):
    bl_label = "Apply"

    def draw(self, _context):
        layout = self.layout

        layout.operator("sequencer.strip_transform_fit", text="Scale To Fit", icon="VIEW_FIT").fit_method = "FIT"
        layout.operator("sequencer.strip_transform_fit", text="Scale to Fill", icon="VIEW_FILL").fit_method = "FILL"
        layout.operator(
            "sequencer.strip_transform_fit", text="Stretch To Fill", icon="VIEW_STRETCH"
        ).fit_method = "STRETCH"


class SEQUENCER_MT_retiming(Menu):
    bl_label = "Retiming"
    bl_translation_context = i18n_contexts.operator_default

    def draw(self, context):
        layout = self.layout
        layout.operator_context = "INVOKE_REGION_WIN"

        layout.operator("sequencer.retiming_key_add", icon="KEYFRAMES_INSERT")
        layout.operator("sequencer.retiming_key_delete", icon="DELETE")
        layout.operator("sequencer.retiming_add_freeze_frame_slide", icon="KEYTYPE_MOVING_HOLD_VEC")


class SEQUENCER_MT_context_menu(Menu):
    bl_label = "Sequencer"

    def draw_generic(self, context):
        layout = self.layout

        layout.operator_context = "INVOKE_REGION_WIN"

        layout.operator("sequencer.split", text="Split", text_ctxt=i18n_contexts.id_sequence, icon="CUT").type = "SOFT"

        layout.separator()

        layout.operator("sequencer.copy", text="Copy", icon="COPYDOWN")
        layout.operator("sequencer.paste", text="Paste", icon="PASTEDOWN")
        layout.operator("sequencer.duplicate_move", icon="DUPLICATE")
        props = layout.operator("wm.call_panel", text="Rename", icon="RENAME")
        props.name = "TOPBAR_PT_name"
        props.keep_open = False
        layout.operator("sequencer.delete", text="Delete", icon="DELETE")

        strip = context.active_strip
        if strip and strip.type == "SCENE":
            layout.operator("sequencer.delete", text="Delete Strip & Data", icon="DELETE_DUPLICATE").delete_data = True
            layout.operator("sequencer.scene_frame_range_update")

        # layout.separator()
        # layout.menu("SEQUENCER_MT_change") # BFA - replaced to be a top-level series of conditional operators

        # BFA - Changed the Change contextual operator visibility to be based on strip type selection
        # BFA - This is done by listing the strip types then checking if it exists for the relevant operators
        # BFA - If there is no correct strip selected, a label will advise what to do
        try:
            layout.operator_context = "INVOKE_REGION_WIN"
            if strip and strip.type == "SCENE":
                bpy_data_scenes_len = len(bpy.data.scenes)

                if bpy_data_scenes_len > 14:
                    layout.operator_context = "INVOKE_DEFAULT"
                    layout.operator("sequencer.change_scene", text="Change Scene", icon="SCENE_DATA")
                elif bpy_data_scenes_len > 1:
                    layout.menu("SEQUENCER_MT_change_scene_with_icons", text="Change Scene")
                del bpy_data_scenes_len
            else:
                layout.operator_context = "INVOKE_DEFAULT"

                strip_type = strip.type
                data_strips = ["IMAGE", "MOVIE", "SOUND"]
                effect_strips = [
                    "GAUSSIAN_BLUR",
                    "SPEED",
                    "GLOW",
                    "TRANSFORM",
                    "MULTICAM",
                    "ADD",
                    "SUBRACT",
                    "ALPHA_OVER",
                    "ALPHA_UNDER",
                    "COLORMIX",
                ]

                if strip_type in data_strips:
                    layout.operator_context = "INVOKE_DEFAULT"
                    props = layout.operator(
                        "sequencer.change_path",
                        text="Change Path/Files",
                        icon="FILE_MOVIE",
                    )

                    if strip:
                        strip_type = strip.type

                        if strip_type == "IMAGE":
                            props.filter_image = True
                        elif strip_type == "MOVIE":
                            props.filter_movie = True
                        elif strip_type == "SOUND":
                            props.filter_sound = True
                elif strip_type in effect_strips:
                    layout.operator_context = "INVOKE_DEFAULT"
                    # BFA - Minimized a bit
                    layout.operator("sequencer.change_effect_input")
                    layout.operator_menu_enum("sequencer.change_effect_type", "type")
                else:
                    # layout.label(text="Please select a changeable strip", icon="QUESTION")
                    pass
        except:
            # layout.label(text="Please select a strip to change", icon="QUESTION")
            pass
        # BFA - End of changes

        layout.separator()

        layout.operator("sequencer.slip", text="Slip Strip Contents", icon="SEQ_SLIP_CONTENTS")
        layout.operator("sequencer.snap", icon="SEQ_SNAP_STRIP")

        layout.separator()

        layout.operator(
            "sequencer.set_range_to_strips",
            text="Set Preview Range to Strips",
            icon="PREVIEW_RANGE",
        ).preview = True

        layout.separator()

        layout.operator("sequencer.gap_remove", icon="SEQ_REMOVE_GAPS").all = False
        layout.operator("sequencer.gap_insert", icon="SEQ_INSERT_GAPS")

        layout.separator()

        if strip:
            strip_type = strip.type
            total, nonsound = selected_strips_count(context)

            layout.separator()
            layout.menu("SEQUENCER_MT_strip_modifiers", icon="MODIFIER")

            if total == 2:
                if nonsound == 2:
                    layout.separator()
                    col = layout.column()
                    col.menu("SEQUENCER_MT_add_transitions", text="Add Transition")
                elif nonsound == 0:
                    layout.separator()
                    layout.operator(
                        "sequencer.crossfade_sounds",
                        text="Crossfade Sounds",
                        icon="SPEAKER",
                    )

            if total >= 1:
                col = layout.column()
                # col.operator_menu_enum("sequencer.fades_add", "type", text="Fade") # BFA - now it's own menu
                col.menu("SEQUENCER_MT_fades_add", text="Fade", icon="IPO_EASE_IN_OUT")
                layout.operator("sequencer.fades_clear", text="Clear Fade", icon="CLEAR")

            if strip_type in {
                    'CROSS', 'ADD', 'SUBTRACT', 'ALPHA_OVER', 'ALPHA_UNDER',
                    'GAMMA_CROSS', 'MULTIPLY', 'WIPE', 'GLOW',
                    'SPEED', 'MULTICAM', 'ADJUSTMENT', 'GAUSSIAN_BLUR',
            }:
                layout.separator()
                layout.menu("SEQUENCER_MT_strip_effect")
            elif strip_type == "MOVIE":
                layout.separator()
                layout.menu("SEQUENCER_MT_strip_movie")
            elif strip_type == "IMAGE":
                layout.separator()
                layout.operator("sequencer.rendersize", icon="RENDER_REGION")
                layout.operator("sequencer.images_separate", icon="SEPARATE")
            elif strip_type == "TEXT":
                layout.separator()
                layout.menu("SEQUENCER_MT_strip_effect")
            elif strip_type == "META":
                layout.separator()
                layout.operator("sequencer.meta_make", icon="ADD_METASTRIP")
                layout.operator("sequencer.meta_separate", icon="REMOVE_METASTRIP")
                layout.operator("sequencer.meta_toggle", text="Toggle Meta", icon="TOGGLE_META")
            if strip_type != "META":
                layout.separator()
                layout.operator("sequencer.meta_make", icon="ADD_METASTRIP")
                layout.operator("sequencer.meta_toggle", text="Toggle Meta", icon="TOGGLE_META")

        layout.separator()

        layout.menu("SEQUENCER_MT_color_tag_picker")

        layout.separator()
        layout.menu("SEQUENCER_MT_strip_lock_mute")

        layout.separator()

        layout.operator("sequencer.connect", icon="LINKED").toggle = True
        layout.operator("sequencer.disconnect", icon="UNLINKED")

    def draw_retime(self, context):
        layout = self.layout
        layout.operator_context = "INVOKE_REGION_WIN"

        if context.sequencer_scene.sequence_editor.selected_retiming_keys:
            layout.operator("sequencer.retiming_segment_speed_set", icon="SET_TIME")

            layout.separator()

            layout.operator("sequencer.retiming_key_delete", icon="DELETE")
            layout.operator(
                "sequencer.retiming_add_freeze_frame_slide",
                icon="KEYTYPE_MOVING_HOLD_VEC",
            )
            layout.operator("sequencer.retiming_add_transition_slide", icon="NODE_CURVE_TIME")

    def draw(self, context):
        ed = context.sequencer_scene.sequence_editor
        if ed.selected_retiming_keys:
            self.draw_retime(context)
        else:
            self.draw_generic(context)


class SEQUENCER_MT_preview_context_menu(Menu):
    bl_label = "Sequencer Preview"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = "INVOKE_REGION_WIN"

        props = layout.operator("wm.call_panel", text="Rename", icon="RENAME")
        props.name = "TOPBAR_PT_name"
        props.keep_open = False

        # TODO: support in preview.
        # layout.operator("sequencer.delete", text="Delete")


class SEQUENCER_MT_pivot_pie(Menu):
    bl_label = "Pivot Point"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        if context.sequencer_scene:
            sequencer_tool_settings = context.sequencer_scene.tool_settings.sequencer_tool_settings

        pie.prop_enum(sequencer_tool_settings, "pivot_point", value="CENTER")
        pie.prop_enum(sequencer_tool_settings, "pivot_point", value="CURSOR")
        pie.prop_enum(sequencer_tool_settings, "pivot_point", value="INDIVIDUAL_ORIGINS")
        pie.prop_enum(sequencer_tool_settings, "pivot_point", value="MEDIAN")


class SEQUENCER_MT_view_pie(Menu):
    bl_label = "View"

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()
        pie.operator("sequencer.view_all")
        pie.operator("sequencer.view_selected", text="Frame Selected", icon="ZOOM_SELECTED")
        pie.separator()
        if context.sequencer_scene.use_preview_range:
            pie.operator("anim.scene_range_frame", text="Frame Preview Range")
        else:
            pie.operator("anim.scene_range_frame", text="Frame Scene Range")


class SEQUENCER_MT_preview_view_pie(Menu):
    bl_label = "View"

    def draw(self, _context):
        layout = self.layout

        pie = layout.menu_pie()
        pie.operator_context = "INVOKE_REGION_PREVIEW"
        pie.operator("sequencer.view_all_preview")
        pie.operator("sequencer.view_selected", text="Frame Selected", icon="ZOOM_SELECTED")
        pie.separator()
        pie.operator("sequencer.view_zoom_ratio", text="Zoom 1:1").ratio = 1


class SEQUENCER_MT_modifier_add(Menu):
    bl_label = "Add Modifier"
    bl_options = {"SEARCH_ON_KEY_PRESS"}

    MODIFIER_TYPES_TO_ICONS = {
        enum_it.identifier: enum_it.icon
        for enum_it in bpy.types.StripModifier.bl_rna.properties["type"].enum_items_static
    }
    MODIFIER_TYPES_TO_LABELS = {
        enum_it.identifier: enum_it.name
        for enum_it in bpy.types.StripModifier.bl_rna.properties["type"].enum_items_static
    }
    MODIFIER_TYPES_I18N_CONTEXT = bpy.types.StripModifier.bl_rna.properties["type"].translation_context

    @classmethod
    def operator_modifier_add(cls, layout, mod_type):
        layout.operator(
            "sequencer.strip_modifier_add",
            text=cls.MODIFIER_TYPES_TO_LABELS[mod_type],
            # Although these are operators, the label actually comes from an (enum) property,
            # so the property's translation context must be used here.
            text_ctxt=cls.MODIFIER_TYPES_I18N_CONTEXT,
            icon=cls.MODIFIER_TYPES_TO_ICONS[mod_type],
        ).type = mod_type

    def draw(self, context):
        layout = self.layout
        strip = context.active_strip
        if not strip:
            return

        if layout.operator_context == "EXEC_REGION_WIN":
            layout.operator_context = "INVOKE_REGION_WIN"
            layout.operator(
                "WM_OT_search_single_menu",
                text="Search...",
                icon="VIEWZOOM",
            ).menu_idname = "SEQUENCER_MT_modifier_add"
            layout.separator()

        layout.operator_context = "INVOKE_REGION_WIN"

        if strip.type == "SOUND":
            self.operator_modifier_add(layout, "SOUND_EQUALIZER")
        else:
            self.operator_modifier_add(layout, "BRIGHT_CONTRAST")
            self.operator_modifier_add(layout, "COLOR_BALANCE")
            self.operator_modifier_add(layout, 'COMPOSITOR')
            self.operator_modifier_add(layout, "CURVES")
            self.operator_modifier_add(layout, "HUE_CORRECT")
            self.operator_modifier_add(layout, "MASK")
            self.operator_modifier_add(layout, "TONEMAP")
            self.operator_modifier_add(layout, "WHITE_BALANCE")


class SequencerButtonsPanel:
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"

    @staticmethod
    def has_sequencer(context):
        return context.space_data.view_type in {"SEQUENCER", "SEQUENCER_PREVIEW"}

    @classmethod
    def poll(cls, context):
        return cls.has_sequencer(context) and (context.active_strip is not None)


class SequencerButtonsPanel_Output:
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"

    @staticmethod
    def has_preview(context):
        st = context.space_data
        return st.view_type in {"PREVIEW", "SEQUENCER_PREVIEW"}

    @classmethod
    def poll(cls, context):
        return cls.has_preview(context)


class SequencerColorTagPicker:
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"

    @staticmethod
    def has_sequencer(context):
        return context.space_data.view_type in {"SEQUENCER", "SEQUENCER_PREVIEW"}

    @classmethod
    def poll(cls, context):
        return cls.has_sequencer(context) and context.active_strip is not None


class SEQUENCER_PT_color_tag_picker(SequencerColorTagPicker, Panel):
    bl_label = "Color Tag"
    bl_category = "Strip"
    bl_options = {"HIDE_HEADER", "INSTANCED"}

    def draw(self, _context):
        layout = self.layout

        row = layout.row(align=True)
        row.operator("sequencer.strip_color_tag_set", icon="X").color = "NONE"
        for i in range(1, 10):
            icon = "STRIP_COLOR_{:02d}".format(i)
            row.operator("sequencer.strip_color_tag_set", icon=icon).color = "COLOR_{:02d}".format(i)


class SEQUENCER_MT_color_tag_picker(SequencerColorTagPicker, Menu):
    bl_label = "Set Color Tag"

    def draw(self, _context):
        layout = self.layout

        row = layout.row(align=True)
        row.operator_enum("sequencer.strip_color_tag_set", "color", icon_only=True)


class SEQUENCER_PT_strip(SequencerButtonsPanel, Panel):
    bl_label = ""
    bl_options = {"HIDE_HEADER"}
    bl_category = "Strip"

    def draw(self, context):
        layout = self.layout
        strip = context.active_strip
        strip_type = strip.type

        if strip_type in {
            "ADD",
            "SUBTRACT",
            "ALPHA_OVER",
            "ALPHA_UNDER",
            "MULTIPLY",
            "GLOW",
            "TRANSFORM",
            "SPEED",
            "MULTICAM",
            "GAUSSIAN_BLUR",
            "COLORMIX",
        }:
            icon_header = "SHADERFX"
        elif strip_type in {
            "CROSS",
            "GAMMA_CROSS",
            "WIPE",
        }:
            icon_header = "ARROW_LEFTRIGHT"
        elif strip_type == "SCENE":
            icon_header = "SCENE_DATA"
        elif strip_type == "MOVIECLIP":
            icon_header = "TRACKER"
        elif strip_type == "MASK":
            icon_header = "MOD_MASK"
        elif strip_type == "MOVIE":
            icon_header = "FILE_MOVIE"
        elif strip_type == "SOUND":
            icon_header = "FILE_SOUND"
        elif strip_type == "IMAGE":
            icon_header = "FILE_IMAGE"
        elif strip_type == "COLOR":
            icon_header = "COLOR"
        elif strip_type == "TEXT":
            icon_header = "FONT_DATA"
        elif strip_type == "ADJUSTMENT":
            icon_header = "COLOR"
        elif strip_type == "META":
            icon_header = "SEQ_STRIP_META"
        else:
            icon_header = "SEQ_SEQUENCER"

        row = layout.row(align=True)
        row.use_property_decorate = False
        row.label(text="", icon=icon_header)
        row.separator()
        row.prop(strip, "name", text="")

        sub = row.row(align=True)
        if strip.color_tag == "NONE":
            sub.popover(panel="SEQUENCER_PT_color_tag_picker", text="", icon="COLOR")
        else:
            icon = "STRIP_" + strip.color_tag
            sub.popover(panel="SEQUENCER_PT_color_tag_picker", text="", icon=icon)

        row.separator()
        row.prop(strip, "mute", toggle=True, icon_only=True, emboss=False)


class SEQUENCER_PT_adjust_crop(SequencerButtonsPanel, Panel):
    bl_label = "Crop"
    bl_options = {"DEFAULT_CLOSED"}
    bl_category = "Strip"

    @classmethod
    def poll(cls, context):
        if not cls.has_sequencer(context):
            return False

        strip = context.active_strip
        if not strip:
            return False

        return strip.type != "SOUND"

    def draw(self, context):
        strip = context.active_strip
        layout = self.layout
        layout.use_property_split = True
        layout.active = not strip.mute

        col = layout.column(align=True)
        col.prop(strip.crop, "min_x")
        col.prop(strip.crop, "max_x")
        col.prop(strip.crop, "max_y")
        col.prop(strip.crop, "min_y")


class SEQUENCER_PT_effect(SequencerButtonsPanel, Panel):
    bl_label = "Effect Strip"
    bl_category = "Strip"

    @classmethod
    def poll(cls, context):
        if not cls.has_sequencer(context):
            return False

        strip = context.active_strip
        if not strip:
            return False

        return strip.type in {
            "ADD",
            "SUBTRACT",
            "ALPHA_OVER",
            "ALPHA_UNDER",
            "CROSS",
            "GAMMA_CROSS",
            "MULTIPLY",
            "WIPE",
            "GLOW",
            "TRANSFORM",
            "COLOR",
            "SPEED",
            "MULTICAM",
            "GAUSSIAN_BLUR",
            "TEXT",
            "COLORMIX",
        }

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        strip = context.active_strip

        layout.active = not strip.mute

        if strip.input_count > 0:
            col = layout.column()
            row = col.row()
            row.prop(strip, "input_1")

            if strip.input_count > 1:
                row.operator("sequencer.swap_inputs", text="", icon="SORT_ASC")
                row = col.row()
                row.prop(strip, "input_2")
                row.operator("sequencer.swap_inputs", text="", icon="SORT_DESC")

        strip_type = strip.type

        if strip_type == "COLOR":
            layout.template_color_picker(strip, "color", value_slider=True, cubic=True)
            layout.prop(strip, "color", text="")

        elif strip_type == "WIPE":
            col = layout.column()
            col.prop(strip, "transition_type")
            col.alignment = "RIGHT"
            col.row().prop(strip, "direction", expand=True)

            col = layout.column()
            col.prop(strip, "blur_width", slider=True)
            if strip.transition_type in {"SINGLE", "DOUBLE"}:
                col.prop(strip, "angle")

        elif strip_type == "GLOW":
            flow = layout.column_flow()
            flow.prop(strip, "threshold", slider=True)
            flow.prop(strip, "clamp", slider=True)
            flow.prop(strip, "boost_factor")
            flow.prop(strip, "blur_radius")
            flow.prop(strip, "quality", slider=True)
            flow.use_property_split = False
            flow.prop(strip, "use_only_boost")

        elif strip_type == "SPEED":
            col = layout.column(align=True)
            col.prop(strip, "speed_control", text="Speed Control")
            if strip.speed_control == "MULTIPLY":
                col.prop(strip, "speed_factor", text=" ")
            elif strip.speed_control == "LENGTH":
                col.prop(strip, "speed_length", text=" ")
            elif strip.speed_control == "FRAME_NUMBER":
                col.prop(strip, "speed_frame_number", text=" ")

            row = layout.row(align=True)
            if strip.speed_control != "STRETCH":
                row.use_property_split = False
                row.prop(strip, "use_frame_interpolate", text="Interpolation")

        elif strip_type == "TRANSFORM":
            col = layout.column()

            col.prop(strip, "interpolation")
            col.prop(strip, "translation_unit")
            col = layout.column(align=True)
            col.prop(strip, "translate_start_x", text="Position X")
            col.prop(strip, "translate_start_y", text="Y")

            col.separator()

            colsub = col.column(align=True)
            colsub.use_property_split = False
            colsub.prop(strip, "use_uniform_scale")

            if strip.use_uniform_scale:
                colsub = col.column(align=True)
                colsub.prop(strip, "scale_start_x", text="Scale")
            else:
                col.prop(strip, "scale_start_x", text="Scale X")
                col.prop(strip, "scale_start_y", text="Y")

            col = layout.column(align=True)
            col.prop(strip, "rotation_start", text="Rotation")

        elif strip_type == "MULTICAM":
            col = layout.column(align=True)
            strip_channel = strip.channel

            col.prop(strip, "multicam_source", text="Source Channel")

            # The multicam strip needs at least 2 strips to be useful
            if strip_channel > 2:
                BT_ROW = 4
                col.label(text="Cut To")
                row = col.row()

                for i in range(1, strip_channel):
                    if (i % BT_ROW) == 1:
                        row = col.row(align=True)

                    # Workaround - .enabled has to have a separate UI block to work
                    if i == strip.multicam_source:
                        sub = row.row(align=True)
                        sub.enabled = False
                        sub.operator(
                            "sequencer.split_multicam",
                            text="{:d}".format(i),
                            translate=False,
                        ).camera = i
                    else:
                        sub_1 = row.row(align=True)
                        sub_1.enabled = True
                        sub_1.operator(
                            "sequencer.split_multicam",
                            text="{:d}".format(i),
                            translate=False,
                        ).camera = i

                if strip.channel > BT_ROW and (strip_channel - 1) % BT_ROW:
                    for i in range(
                        strip.channel,
                        strip_channel + ((BT_ROW + 1 - strip_channel) % BT_ROW),
                    ):
                        row.label(text="")
            else:
                col.separator()
                col.label(text="Two or more channels are needed below this strip", icon="INFO")

        elif strip_type == "TEXT":
            layout = self.layout
            col = layout.column()
            col.scale_x = 1.3
            col.scale_y = 1.3
            col.use_property_split = False
            col.prop(strip, "text", text="")
            col.use_property_split = True
            layout.prop(strip, "wrap_width", text="Wrap Width")

        col = layout.column(align=True)
        if strip_type in {
            "CROSS",
            "GAMMA_CROSS",
            "WIPE",
            "ALPHA_OVER",
            "ALPHA_UNDER",
        }:
            col.use_property_split = False
            col.prop(strip, "use_default_fade", text="Default Fade")
            col.use_property_split = True
            if not strip.use_default_fade:
                col.prop(strip, "effect_fader", text="Effect Fader")
        elif strip_type == "GAUSSIAN_BLUR":
            col = layout.column(align=True)
            col.prop(strip, "size_x", text="Size X")
            col.prop(strip, "size_y", text="Y")
        elif strip_type == "COLORMIX":
            layout.prop(strip, "blend_effect", text="Blend Mode")
            row = layout.row(align=True)
            row.prop(strip, "factor", slider=True)


class SEQUENCER_PT_effect_text_layout(SequencerButtonsPanel, Panel):
    bl_label = "Layout"
    bl_parent_id = "SEQUENCER_PT_effect"
    bl_category = "Strip"

    @classmethod
    def poll(cls, context):
        strip = context.active_strip
        return strip.type == "TEXT"

    def draw(self, context):
        strip = context.active_strip
        layout = self.layout
        layout.use_property_split = True
        col = layout.column()
        col.prop(strip, "location", text="Location")
        col.prop(strip, "alignment_x", text="Alignment")

        col = layout.column()  # BFA - label and indent
        col.label(text="Anchor")

        row = col.row()
        row.separator()
        row.prop(strip, "anchor_x", text="X")
        row = col.row()
        row.separator()
        row.prop(strip, "anchor_y", text="Y")


class SEQUENCER_PT_effect_text_style(SequencerButtonsPanel, Panel):
    bl_label = "Style"
    bl_parent_id = "SEQUENCER_PT_effect"
    bl_category = "Strip"

    @classmethod
    def poll(cls, context):
        strip = context.active_strip
        return strip.type == "TEXT"

    def draw(self, context):
        strip = context.active_strip
        layout = self.layout
        layout.use_property_split = True
        col = layout.column()

        row = col.row(align=True)
        row.use_property_decorate = False
        row.template_ID(strip, "font", open="font.open", unlink="font.unlink")
        row.prop(strip, "use_bold", text="", icon="BOLD")
        row.prop(strip, "use_italic", text="", icon="ITALIC")

        col = layout.column()
        split = col.split(factor=0.4, align=True)
        split.label(text="Size")
        split.prop(strip, "font_size", text="")

        split = col.split(factor=0.4, align=True)
        split.label(text="Color")
        split.prop(strip, "color", text="")

        split = col.split(factor=0.4, align=True)
        row = split.row()
        row.use_property_decorate = False
        row.use_property_split = False
        row.prop(strip, "use_shadow", text="Shadow")
        sub = split.column()
        if strip.use_shadow and (not strip.mute):
            sub.prop(strip, "shadow_color", text="")
            row = col.row()
            row.separator()
            row.prop(strip, "shadow_angle", text="Angle")
            row = col.row()
            row.separator()
            row.prop(strip, "shadow_offset", text="Offset")
            row = col.row()
            row.separator()
            row.prop(strip, "shadow_blur", text="Blur")
            sub.active = strip.use_shadow and (not strip.mute)
        else:
            sub.label(icon="DISCLOSURE_TRI_RIGHT")

        split = col.split(factor=0.4, align=True)
        row = split.row()
        row.use_property_decorate = False
        row.use_property_split = False
        row.prop(strip, "use_outline", text="Outline")
        sub = split.column()
        if strip.use_outline and (not strip.mute):
            sub.prop(strip, "outline_color", text="")
            row = col.row()
            row.separator()
            row.prop(strip, "outline_width", text="Width")
            row.active = strip.use_outline
        else:
            sub.label(icon="DISCLOSURE_TRI_RIGHT")

        split = col.split(factor=0.4, align=True)
        row = split.row()
        row.use_property_decorate = False
        row.use_property_split = False
        row.prop(strip, "use_box", text="Box")
        sub = split.column()
        if strip.use_box and (not strip.mute):
            sub.prop(strip, "box_color", text="")
            row = col.row()
            row.separator()
            row.prop(strip, "box_margin", text="Margin")
        else:
            sub.label(icon="DISCLOSURE_TRI_RIGHT")


class SEQUENCER_PT_effect_text_outline(SequencerButtonsPanel, Panel):
    bl_label = "Outline"
    bl_options = {"DEFAULT_CLOSED"}
    bl_category = "Strip"
    bl_parent_id = "SEQUENCER_PT_effect_text_style"

    @classmethod
    def poll(cls, context):
        strip = context.active_strip
        return strip.type == "TEXT"

    def draw_header(self, context):
        strip = context.active_strip
        layout = self.layout
        layout.prop(strip, "use_outline", text="")

    def draw(self, context):
        strip = context.active_strip
        layout = self.layout
        layout.use_property_split = True

        col = layout.column()
        col.prop(strip, "outline_color", text="Color")
        col.prop(strip, "outline_width", text="Width")
        col.active = strip.use_outline and (not strip.mute)


class SEQUENCER_PT_effect_text_shadow(SequencerButtonsPanel, Panel):
    bl_label = "Shadow"
    bl_options = {"DEFAULT_CLOSED"}
    bl_category = "Strip"
    bl_parent_id = "SEQUENCER_PT_effect_text_style"

    @classmethod
    def poll(cls, context):
        strip = context.active_strip
        return strip.type == "TEXT"

    def draw_header(self, context):
        strip = context.active_strip
        layout = self.layout
        layout.prop(strip, "use_shadow", text="")

    def draw(self, context):
        strip = context.active_strip
        layout = self.layout
        layout.use_property_split = True

        col = layout.column()
        col.prop(strip, "shadow_color", text="Color")
        col.prop(strip, "shadow_angle", text="Angle")
        col.prop(strip, "shadow_offset", text="Offset")
        col.prop(strip, "shadow_blur", text="Blur")
        col.active = strip.use_shadow and (not strip.mute)


class SEQUENCER_PT_effect_text_box(SequencerButtonsPanel, Panel):
    bl_label = "Box"
    bl_translation_context = i18n_contexts.id_sequence
    bl_options = {"DEFAULT_CLOSED"}
    bl_category = "Strip"
    bl_parent_id = "SEQUENCER_PT_effect_text_style"

    @classmethod
    def poll(cls, context):
        strip = context.active_strip
        return strip.type == "TEXT"

    def draw_header(self, context):
        strip = context.active_strip
        layout = self.layout
        layout.prop(strip, "use_box", text="")

    def draw(self, context):
        strip = context.active_strip
        layout = self.layout
        layout.use_property_split = True

        col = layout.column()
        col.prop(strip, "box_color", text="Color")
        col.prop(strip, "box_margin", text="Margin")
        col.prop(strip, "box_roundness", text="Roundness")
        col.active = strip.use_box and (not strip.mute)


class SEQUENCER_PT_source(SequencerButtonsPanel, Panel):
    bl_label = "Source"
    bl_options = {"DEFAULT_CLOSED"}
    bl_category = "Strip"

    @classmethod
    def poll(cls, context):
        if not cls.has_sequencer(context):
            return False

        strip = context.active_strip
        if not strip:
            return False

        return strip.type in {"MOVIE", "IMAGE", "SOUND"}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        scene = context.sequencer_scene
        strip = context.active_strip
        strip_type = strip.type

        layout.active = not strip.mute

        # Draw a filename if we have one.
        if strip_type == "SOUND":
            sound = strip.sound
            layout.template_ID(strip, "sound", open="sound.open")
            if sound is not None:
                col = layout.column()
                col.prop(sound, "filepath", text="")

                col.alignment = "RIGHT"
                sub = col.column(align=True)
                split = sub.split(factor=0.5, align=True)
                split.alignment = "RIGHT"
                if sound.packed_file:
                    split.label(text="Unpack")
                    split.operator("sound.unpack", icon="PACKAGE", text="")
                else:
                    split.label(text="Pack")
                    split.operator("sound.pack", icon="UGLYPACKAGE", text="")

                layout.use_property_split = False
                layout.prop(sound, "use_memory_cache")

                col = layout.box()
                col = col.column(align=True)
                split = col.split(factor=0.5, align=False)
                split.alignment = "RIGHT"
                split.label(text="Sample Rate")
                split.alignment = "LEFT"
                if sound.samplerate <= 0:
                    split.label(text="Unknown")
                else:
                    split.label(text="{:d} Hz".format(sound.samplerate), translate=False)

                split = col.split(factor=0.5, align=False)
                split.alignment = "RIGHT"
                split.label(text="Channels")
                split.alignment = "LEFT"

                # FIXME(@campbellbarton): this is ugly, we may want to support a way of showing a label from an enum.
                channel_enum_items = sound.bl_rna.properties["channels"].enum_items
                split.label(text=channel_enum_items[channel_enum_items.find(sound.channels)].name)
                del channel_enum_items
        else:
            if strip_type == "IMAGE":
                col = layout.column()
                col.prop(strip, "directory", text="")

                # Current element for the filename.
                elem = strip.strip_elem_from_frame(scene.frame_current)
                if elem:
                    col.prop(elem, "filename", text="")  # strip.elements[0] could be a fallback

                col.prop(strip.colorspace_settings, "name", text="Color Space")

                col.prop(strip, "alpha_mode", text="Alpha")
                sub = col.column(align=True)
                sub.operator("sequencer.change_path", text="Change Data/Files", icon="FILE_MOVIE").filter_image = True
            else:  # elif strip_type == 'MOVIE':
                elem = strip.elements[0]

                col = layout.column()
                col.prop(strip, "filepath", text="")
                col.prop(strip.colorspace_settings, "name", text="Color Space")
                col.prop(strip, "stream_index")

                col.use_property_split = False
                col.prop(strip, "use_deinterlace")
                col.use_property_split = True

            if scene.render.use_multiview:
                layout.prop(strip, "use_multiview")

                col = layout.column()
                col.active = strip.use_multiview

                col.row().prop(strip, "views_format", expand=True)

                box = col.box()
                box.active = strip.views_format == "STEREO_3D"
                box.template_image_stereo_3d(strip.stereo_3d_format)

            # Resolution.
            col = layout.box()
            col = col.column(align=True)
            split = col.split(factor=0.5, align=False)
            split.alignment = "RIGHT"
            split.label(text="Resolution")
            size = (elem.orig_width, elem.orig_height) if elem else (0, 0)
            if size[0] and size[1]:
                split.alignment = "LEFT"
                split.label(text="{:d}x{:d}".format(*size), translate=False)
            else:
                split.label(text="None")
            # FPS
            if elem.orig_fps:
                split = col.split(factor=0.5, align=False)
                split.alignment = "RIGHT"
                split.label(text="FPS")
                split.alignment = "LEFT"
                split.label(text="{:.2f}".format(elem.orig_fps), translate=False)


class SEQUENCER_PT_movie_clip(SequencerButtonsPanel, Panel):
    bl_label = "Movie Clip"
    bl_options = {"DEFAULT_CLOSED"}
    bl_category = "Strip"

    @classmethod
    def poll(cls, context):
        if not cls.has_sequencer(context):
            return False

        strip = context.active_strip
        if not strip:
            return False

        return strip.type == "MOVIECLIP"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False  # BFA
        layout.use_property_decorate = False

        strip = context.active_strip

        layout.active = not strip.mute
        layout.template_ID(strip, "clip")

        if strip.type == "MOVIECLIP":
            col = layout.column(heading="Use")
            col.prop(strip, "stabilize2d", text="2D Stabilized Clip")
            col.prop(strip, "undistort", text="Undistorted Clip")

        clip = strip.clip
        if clip:
            sta = clip.frame_start
            end = clip.frame_start + clip.frame_duration
            layout.label(
                text=rpt_("Original frame range: {:d}-{:d} ({:d})").format(sta, end, end - sta + 1),
                translate=False,
            )


class SEQUENCER_PT_scene(SequencerButtonsPanel, Panel):
    bl_label = "Scene"
    bl_category = "Strip"

    @classmethod
    def poll(cls, context):
        if not cls.has_sequencer(context):
            return False

        strip = context.active_strip
        if not strip:
            return False

        return strip.type == "SCENE"

    def draw(self, context):
        strip = context.active_strip
        scene = strip.scene

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        layout.active = not strip.mute

        layout.template_ID(strip, "scene", text="Scene", new="scene.new_sequencer")
        layout.prop(strip, "scene_input", text="Input")

        if strip.scene_input == "CAMERA":
            layout.template_ID(strip, "scene_camera", text="Camera")

        if strip.scene_input == "CAMERA":
            layout = layout.column(align=True)
            layout.label(text="Show")

            # BFA - Align bool properties left and indent
            row = layout.row()
            row.separator()
            col = row.column(align=True)
            col.use_property_split = False

            col.prop(strip, "use_annotations", text="Annotations")
            if scene:
                # Warning, this is not a good convention to follow.
                # Expose here because setting the alpha from the "Render" menu is very inconvenient.
                col.prop(scene.render, "film_transparent")


class SEQUENCER_PT_scene_sound(SequencerButtonsPanel, Panel):
    bl_label = "Sound"
    bl_category = "Strip"

    @classmethod
    def poll(cls, context):
        if not cls.has_sequencer(context):
            return False

        strip = context.active_strip
        if not strip:
            return False

        return strip.type == "SCENE"

    def draw(self, context):
        strip = context.active_strip

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        layout.active = not strip.mute

        col = layout.column()

        col.use_property_decorate = True
        split = col.split(factor=0.4)
        split.alignment = "RIGHT"
        split.label(text="Strip Volume", text_ctxt=i18n_contexts.id_sound)
        split.prop(strip, "volume", text="")
        col.use_property_decorate = False


class SEQUENCER_PT_mask(SequencerButtonsPanel, Panel):
    bl_label = "Mask"
    bl_category = "Strip"

    @classmethod
    def poll(cls, context):
        if not cls.has_sequencer(context):
            return False

        strip = context.active_strip
        if not strip:
            return False

        return strip.type == "MASK"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        strip = context.active_strip

        layout.active = not strip.mute

        layout.template_ID(strip, "mask")

        mask = strip.mask

        if mask:
            sta = mask.frame_start
            end = mask.frame_end
            layout.label(
                text=rpt_("Original frame range: {:d}-{:d} ({:d})").format(sta, end, end - sta + 1),
                translate=False,
            )


class SEQUENCER_PT_time(SequencerButtonsPanel, Panel):
    bl_label = "Time"
    bl_options = {"DEFAULT_CLOSED"}
    bl_category = "Strip"

    @classmethod
    def poll(cls, context):
        if not cls.has_sequencer(context):
            return False

        strip = context.active_strip
        if not strip:
            return False

        return strip.type

    def draw_header_preset(self, context):
        layout = self.layout
        layout.alignment = "RIGHT"
        strip = context.active_strip

        layout.prop(strip, "lock", text="", icon_only=True, emboss=False)

    def draw(self, context):
        from bpy.utils import smpte_from_frame

        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False

        scene = context.sequencer_scene
        frame_current = scene.frame_current
        strip = context.active_strip

        is_effect = isinstance(strip, bpy.types.EffectStrip)

        # Get once.
        frame_start = strip.frame_start
        frame_final_start = strip.frame_final_start
        frame_final_end = strip.frame_final_end
        frame_final_duration = strip.frame_final_duration
        frame_offset_start = strip.frame_offset_start
        frame_offset_end = strip.frame_offset_end

        length_list = (
            str(round(frame_start, 0)),
            str(round(frame_final_end, 0)),
            str(round(frame_final_duration, 0)),
            str(round(frame_offset_start, 0)),
            str(round(frame_offset_end, 0)),
        )

        if not is_effect:
            length_list = length_list + (
                str(round(strip.animation_offset_start, 0)),
                str(round(strip.animation_offset_end, 0)),
            )

        max_length = max(len(x) for x in length_list)
        max_factor = (1.9 - max_length) / 30
        factor = 0.45

        layout.enabled = not strip.lock
        layout.active = not strip.mute

        sub = layout.row(align=True)
        split = sub.split(factor=factor + max_factor)
        split.alignment = "RIGHT"

        try:  # BFA - detect if correct relevant strip is selected to apply as a clearer UX. Only works on Movie and Image strips
            is_retiming = context.sequencer_scene.sequence_editor.selected_retiming_keys
            strip = context.active_strip
            layout = self.layout

            layout.operator_context = "INVOKE_REGION_WIN"  # BFA

            strip = context.active_strip  # BFA
            strip_type = strip.type  # BFA

            if strip and strip_type == "MOVIE" or strip_type == "IMAGE" or strip_type == "SOUND":
                # BFA - Made the show_retiming_keys conditional
                col = layout.column()
                col.prop(strip, "show_retiming_keys", text="Show Retiming Keys")
            else:
                layout.label(text="To retime, select a movie or sound strip", icon="QUESTION")  # BFA
        except Exception:
            layout.label(text="To retime, select a movie or sound strip", icon="QUESTION")  # BFA

        sub = layout.row(align=True)
        split = sub.split(factor=factor + max_factor)
        split.alignment = "RIGHT"
        split.label(text="Channel")
        split.prop(strip, "channel", text="")

        sub = layout.column(align=True)
        split = sub.split(factor=factor + max_factor, align=True)
        split.alignment = "RIGHT"
        split.label(text="Start")
        split.prop(strip, "frame_start", text=smpte_from_frame(frame_start))

        split = sub.split(factor=factor + max_factor, align=True)
        split.alignment = "RIGHT"
        split.label(text="Duration")
        split.prop(strip, "frame_final_duration", text=smpte_from_frame(frame_final_duration))

        # Use label, editing this value from the UI allows negative values,
        # users can adjust duration.
        split_factor = factor + max_factor - 0.005  # BFA - Nudge split to the left for better text alignment
        split = sub.split(factor=split_factor, align=True)
        row = split.row()
        row.alignment = "LEFT"
        row.label(text="End")

        # BFA - Improve text alignment
        row = split.row()
        row.separator(factor=0)  # BFA - slight indent
        row.label(text="{:>14s}".format(smpte_from_frame(frame_final_end)), translate=False)
        row = row.row()
        row.alignment = "RIGHT"
        row.label(text=str(frame_final_end) + " ")
        row.separator(factor=0)  # BFA - slight indent
        # BFA - Improve text alignment (end)

        if not is_effect:
            layout.alignment = "RIGHT"
            sub = layout.column(align=True)

            split = sub.split(factor=factor + max_factor, align=True)
            split.alignment = "RIGHT"
            split.label(text="Strip Offset Start")
            split.prop(strip, "frame_offset_start", text=smpte_from_frame(frame_offset_start))

            split = sub.split(factor=factor + max_factor, align=True)
            split.alignment = "RIGHT"
            split.label(text="End")
            split.prop(strip, "frame_offset_end", text=smpte_from_frame(frame_offset_end))

            layout.alignment = "RIGHT"
            sub = layout.column(align=True)

            split = sub.split(factor=factor + max_factor, align=True)
            split.alignment = "RIGHT"
            split.label(text="Hold Offset Start")
            split.prop(
                strip,
                "animation_offset_start",
                text=smpte_from_frame(strip.animation_offset_start),
            )

            split = sub.split(factor=factor + max_factor, align=True)
            split.alignment = "RIGHT"
            split.label(text="End")
            split.prop(
                strip,
                "animation_offset_end",
                text=smpte_from_frame(strip.animation_offset_end),
            )
            if strip.type == "SOUND":
                sub2 = layout.column(align=True)
                split = sub2.split(factor=factor + max_factor, align=True)
                split.alignment = "RIGHT"
                split.label(text="Sound Offset", text_ctxt=i18n_contexts.id_sound)
                split.prop(strip, "sound_offset", text="")

        col = layout.column(align=True)
        col = col.box()
        col.active = (frame_current >= frame_final_start) and (
            frame_current <= frame_final_start + frame_final_duration
        )

        split = col.split(factor=factor + max_factor, align=True)
        split.alignment = "RIGHT"
        split.label(text="Current Frame")
        split = split.split(factor=factor + 0.3 + max_factor, align=True)
        frame_display = frame_current - frame_final_start
        split.label(text="{:>14s}".format(smpte_from_frame(frame_display)), translate=False)
        split.alignment = "RIGHT"
        split.label(text=str(frame_display) + " ")

        if strip.type == "SCENE":
            scene = strip.scene

            if scene:
                sta = scene.frame_start
                end = scene.frame_end
                split = col.split(factor=factor + max_factor)
                split.alignment = "RIGHT"
                split.label(text="Original Frame Range")
                split.alignment = "LEFT"
                split.label(
                    text="{:d}-{:d} ({:d})".format(sta, end, end - sta + 1),
                    translate=False,
                )


class SEQUENCER_PT_adjust_sound(SequencerButtonsPanel, Panel):
    bl_label = "Sound"
    bl_category = "Strip"

    @classmethod
    def poll(cls, context):
        if not cls.has_sequencer(context):
            return False

        strip = context.active_strip
        if not strip:
            return False

        return strip.type == "SOUND"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False

        st = context.space_data
        overlay_settings = st.timeline_overlay
        strip = context.active_strip
        sound = strip.sound

        layout.active = not strip.mute

        if sound is not None:
            layout.use_property_split = True
            col = layout.column()

            split = col.split(factor=0.4)
            split.alignment = "RIGHT"
            split.label(text="Volume", text_ctxt=i18n_contexts.id_sound)
            split.prop(strip, "volume", text="")

            col = layout.column(align=True)  # BFA - Put all panning settings in its own column layout
            row = col.row()
            row.alignment = "LEFT"
            row.use_property_split = False
            row.prop(sound, "use_mono")  # BFA - Align bool property left

            audio_channels = context.sequencer_scene.render.ffmpeg.audio_channels
            is_mono = audio_channels == "MONO"

            # BFA - Add dropdown icon
            if not is_mono:
                row.label(text="", icon="DISCLOSURE_TRI_DOWN" if sound.use_mono else "DISCLOSURE_TRI_RIGHT")

            pan_enabled = sound.use_mono and not is_mono
            pan_text = "{:.2f}°".format(strip.pan * 90.0)

            # BFA - Only draw if enabled
            if pan_enabled:
                row = col.row()
                row.separator()

                split = row.column().split(factor=0.385)
                col1 = split.column()
                col2 = split.column()
                col1.alignment = "LEFT"
                col2.alignment = "RIGHT"

                col1.label(text="Pan", text_ctxt=i18n_contexts.id_sound)
                col2.prop(strip, "pan", text="")

                if audio_channels not in {"MONO", "STEREO"}:
                    col1.label(text="Pan Angle")
                    row = col2.row()
                    row.alignment = "CENTER"
                    row.label(text=pan_text)
                    row.separator()  # Compensate for no decorate.

            col = layout.column()
            col.use_property_split = False  # BFA - Align bool property left

            if overlay_settings.waveform_display_type == "DEFAULT_WAVEFORMS":
                col.prop(strip, "show_waveform")


class SEQUENCER_PT_adjust_comp(SequencerButtonsPanel, Panel):
    bl_label = "Compositing"
    bl_category = "Strip"

    @classmethod
    def poll(cls, context):
        if not cls.has_sequencer(context):
            return False

        strip = context.active_strip
        if not strip:
            return False

        return strip.type != "SOUND"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        strip = context.active_strip

        layout.active = not strip.mute

        col = layout.column()
        col.prop(strip, "blend_type", text="Blend")
        col.prop(strip, "blend_alpha", text="Opacity", slider=True)


class SEQUENCER_PT_adjust_transform(SequencerButtonsPanel, Panel):
    bl_label = "Transform"
    bl_category = "Strip"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        if not cls.has_sequencer(context):
            return False

        strip = context.active_strip
        if not strip:
            return False

        return strip.type != "SOUND"

    def draw(self, context):
        strip = context.active_strip
        layout = self.layout
        layout.use_property_split = True
        layout.active = not strip.mute

        col = layout.column(align=True)
        col.prop(strip.transform, "filter", text="Filter")

        col = layout.column(align=True)
        col.prop(strip.transform, "offset_x", text="Position X")
        col.prop(strip.transform, "offset_y", text="Y")

        col = layout.column(align=True)
        col.prop(strip.transform, "scale_x", text="Scale X")
        col.prop(strip.transform, "scale_y", text="Y")

        col = layout.column(align=True)
        col.prop(strip.transform, "rotation", text="Rotation")

        col = layout.column(align=True)
        col.prop(strip.transform, "origin")

        row = layout.row(heading="Mirror", heading_ctxt=i18n_contexts.id_image)
        sub = row.row(align=True)
        sub.prop(strip, "use_flip_x", text="X", toggle=True)
        sub.prop(strip, "use_flip_y", text="Y", toggle=True)


class SEQUENCER_PT_adjust_video(SequencerButtonsPanel, Panel):
    bl_label = "Video"
    bl_options = {"DEFAULT_CLOSED"}
    bl_category = "Strip"

    @classmethod
    def poll(cls, context):
        if not cls.has_sequencer(context):
            return False

        strip = context.active_strip
        if not strip:
            return False

        return strip.type in {
            "MOVIE",
            "IMAGE",
            "SCENE",
            "MOVIECLIP",
            "MASK",
            "META",
            "ADD",
            "SUBTRACT",
            "ALPHA_OVER",
            "ALPHA_UNDER",
            "CROSS",
            "GAMMA_CROSS",
            "MULTIPLY",
            "WIPE",
            "GLOW",
            "TRANSFORM",
            "COLOR",
            "MULTICAM",
            "SPEED",
            "ADJUSTMENT",
            "COLORMIX",
        }

    def draw(self, context):
        layout = self.layout

        layout.use_property_split = True

        col = layout.column()

        strip = context.active_strip

        layout.active = not strip.mute

        col.prop(strip, "strobe")

        # BFA - Align bool property left
        col.use_property_split = False
        col.prop(strip, "use_reverse_frames")


class SEQUENCER_PT_adjust_color(SequencerButtonsPanel, Panel):
    bl_label = "Color"
    bl_options = {"DEFAULT_CLOSED"}
    bl_category = "Strip"

    @classmethod
    def poll(cls, context):
        if not cls.has_sequencer(context):
            return False

        strip = context.active_strip
        if not strip:
            return False

        return strip.type in {
            "MOVIE",
            "IMAGE",
            "SCENE",
            "MOVIECLIP",
            "MASK",
            "META",
            "ADD",
            "SUBTRACT",
            "ALPHA_OVER",
            "ALPHA_UNDER",
            "CROSS",
            "GAMMA_CROSS",
            "MULTIPLY",
            "WIPE",
            "GLOW",
            "TRANSFORM",
            "COLOR",
            "MULTICAM",
            "SPEED",
            "ADJUSTMENT",
            "COLORMIX",
        }

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        strip = context.active_strip

        layout.active = not strip.mute

        col = layout.column()
        col.prop(strip, "color_saturation", text="Saturation")
        col.prop(strip, "color_multiply", text="Multiply")

        row = col.row()
        row.use_property_split = False
        row.prop(strip, "multiply_alpha")
        row.prop_decorator(strip, "multiply_alpha")

        row = col.row()
        row.use_property_split = False
        row.prop(strip, "use_float", text="Convert to Float")
        row.prop_decorator(strip, "use_float")


class SEQUENCER_PT_cache_settings(SequencerButtonsPanel, Panel):
    bl_label = "Cache Settings"
    bl_category = "Cache"

    @classmethod
    def poll(cls, context):
        return cls.has_sequencer(context) and context.sequencer_scene and context.sequencer_scene.sequence_editor

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False

        ed = context.sequencer_scene.sequence_editor

        col = layout.column()

        # BFA - double entries


class SEQUENCER_PT_cache_view_settings(SequencerButtonsPanel, Panel):
    bl_label = "Display Cache"
    bl_category = "Cache"
    bl_parent_id = "SEQUENCER_PT_cache_settings"

    @classmethod
    def poll(cls, context):
        return cls.has_sequencer(context) and context.sequencer_scene and context.sequencer_scene.sequence_editor

    def draw_header(self, context):
        cache_settings = context.space_data.cache_overlay

        self.layout.prop(cache_settings, "show_cache", text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False

        cache_settings = context.space_data.cache_overlay
        ed = context.sequencer_scene.sequence_editor
        layout.active = cache_settings.show_cache

        col = layout.column(align=True)
        col.use_property_split = False

        split = layout.split(factor=0.15)
        col = split.column()
        col.label(text="")

        col = split.column()

        show_developer_ui = context.preferences.view.show_developer_ui
        col.prop(cache_settings, "show_cache_final_out", text="Final")
        if show_developer_ui:
            col.prop(cache_settings, "show_cache_raw", text="Raw")

        show_cache_size = show_developer_ui and (ed.use_cache_raw or ed.use_cache_final)
        if show_cache_size:
            cache_raw_size = ed.cache_raw_size
            cache_final_size = ed.cache_final_size

            col = layout.box()
            col = col.column(align=True)

            # BFA - Rework UI to avoid labels cutting off
            split = col.split(factor=0.75, align=True)
            col1 = split.column(align=True)
            col2 = split.column(align=True)
            col1.alignment = "LEFT"
            col2.alignment = "RIGHT"

            col1.label(text="Current Cache Size")
            col1.label(text="Raw")
            col1.label(text="Final")

            col2.label(text=iface_("{:d} MB").format(cache_raw_size + cache_final_size), translate=False)
            col2.label(text=iface_("{:d} MB").format(cache_raw_size), translate=False)
            col2.label(text=iface_("{:d} MB").format(cache_final_size), translate=False)


class SEQUENCER_PT_proxy_settings(SequencerButtonsPanel, Panel):
    bl_label = "Proxy Settings"
    bl_category = "Proxy"

    @classmethod
    def poll(cls, context):
        return cls.has_sequencer(context) and context.sequencer_scene and context.sequencer_scene.sequence_editor

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        ed = context.sequencer_scene.sequence_editor
        flow = layout.column_flow()
        flow.prop(ed, "proxy_storage", text="Storage")

        if ed.proxy_storage == "PROJECT":
            flow.prop(ed, "proxy_dir", text="Directory")

        col = layout.column()
        col.operator("sequencer.enable_proxies")
        col.operator("sequencer.rebuild_proxy", icon="LASTOPERATOR")


class SEQUENCER_PT_strip_proxy(SequencerButtonsPanel, Panel):
    bl_label = "Strip Proxy & Timecode"
    bl_category = "Proxy"

    @classmethod
    def poll(cls, context):
        if not cls.has_sequencer(context) or not context.sequencer_scene or not context.sequencer_scene.sequence_editor:
            return False

        strip = context.active_strip
        if not strip:
            return False

        return strip.type in {"MOVIE", "IMAGE"}

    def draw_header(self, context):
        strip = context.active_strip

        self.layout.prop(strip, "use_proxy", text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False

        ed = context.sequencer_scene.sequence_editor

        strip = context.active_strip

        if strip.proxy:
            proxy = strip.proxy

            if ed.proxy_storage == "PER_STRIP":
                col = layout.column(align=True)
                col.label(text="Custom Proxy")
                row = col.row()
                row.separator()
                row.prop(proxy, "use_proxy_custom_directory")
                row = col.row()
                row.separator()
                row.prop(proxy, "use_proxy_custom_file")
                col.use_property_split = True
                if proxy.use_proxy_custom_directory and not proxy.use_proxy_custom_file:
                    col.prop(proxy, "directory")
                if proxy.use_proxy_custom_file:
                    col.prop(proxy, "filepath")

            layout.use_property_split = True
            row = layout.row(heading="Resolutions", align=True)
            row.prop(strip.proxy, "build_25", toggle=True)
            row.prop(strip.proxy, "build_50", toggle=True)
            row.prop(strip.proxy, "build_75", toggle=True)
            row.prop(strip.proxy, "build_100", toggle=True)

            layout.use_property_split = False
            layout.prop(proxy, "use_overwrite")

            layout.use_property_split = True

            col = layout.column()
            col.prop(proxy, "quality", text="Quality")

            if strip.type == "MOVIE":
                col = layout.column()

                col.prop(proxy, "timecode", text="Timecode Index")


class SEQUENCER_PT_strip_cache(SequencerButtonsPanel, Panel):
    bl_label = "Strip Cache"
    bl_category = "Cache"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        show_developer_ui = context.preferences.view.show_developer_ui
        if not cls.has_sequencer(context):
            return False
        if context.active_strip is not None and show_developer_ui:
            return True
        return False

    def draw_header(self, context):
        strip = context.active_strip
        self.layout.prop(strip, "override_cache_settings", text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False

        strip = context.active_strip
        layout.active = strip.override_cache_settings

        col = layout.column()
        col.prop(strip, "use_cache_raw")

        show_cache_size = show_developer_ui and (ed.use_cache_raw or ed.use_cache_final)
        if show_cache_size:
            cache_raw_size = ed.cache_raw_size
            cache_final_size = ed.cache_final_size

            col = layout.box()
            col = col.column(align=True)

            # BFA - Rework UI to avoid labels cutting off
            split = col.split(factor=0.75, align=True)
            col1 = split.column(align=True)
            col2 = split.column(align=True)
            col1.alignment = "LEFT"
            col2.alignment = "RIGHT"

            col1.label(text="Current Cache Size")
            col1.label(text="Raw")
            col1.label(text="Final")

            col2.label(text=iface_("{:d} MB").format(cache_raw_size + cache_final_size), translate=False)
            col2.label(text=iface_("{:d} MB").format(cache_raw_size), translate=False)
            col2.label(text=iface_("{:d} MB").format(cache_final_size), translate=False)


class SEQUENCER_PT_preview(SequencerButtonsPanel_Output, Panel):
    bl_label = "Scene Strip Display"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_category = "View"

    @classmethod
    def poll(cls, context):
        return SequencerButtonsPanel_Output.poll(context) and context.sequencer_scene

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        render = context.sequencer_scene.render

        col = layout.column()
        col.prop(render, "sequencer_gl_preview", text="Shading")

        if render.sequencer_gl_preview in {"SOLID", "WIREFRAME"}:
            col.use_property_split = False
            col.prop(render, "use_sequencer_override_scene_strip")


class SEQUENCER_PT_view(SequencerButtonsPanel_Output, Panel):
    bl_label = "View Settings"
    bl_category = "View"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        st = context.space_data
        ed = context.sequencer_scene.sequence_editor

        col = layout.column()

        col.prop(st, "proxy_render_size")

        col = layout.column()
        if st.proxy_render_size in {"NONE", "SCENE"}:
            col.enabled = False
        col.prop(st, "use_proxies")

        col = layout.column()
        col.prop(st, "display_channel", text="Channel")

        if st.display_mode == "IMAGE":
            col.prop(st, "show_overexposed")

        elif st.display_mode == "WAVEFORM":  # BFA
            col.prop(st, "show_separate_color")  # BFA

        if ed:
            col.use_property_split = False
            col.prop(ed, "show_missing_media")


class SEQUENCER_PT_view_cursor(SequencerButtonsPanel_Output, Panel):
    bl_category = "View"
    bl_label = "2D Cursor"

    def draw(self, context):
        layout = self.layout

        st = context.space_data

        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column()
        col.prop(st, "cursor_location", text="Location")


class SEQUENCER_PT_frame_overlay(SequencerButtonsPanel_Output, Panel):
    bl_label = "Frame Overlay"
    bl_category = "View"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        if not context.sequencer_scene or not context.sequencer_scene.sequence_editor:
            return False
        return SequencerButtonsPanel_Output.poll(context)

    def draw_header(self, context):
        scene = context.sequencer_scene
        ed = scene.sequence_editor

        self.layout.prop(ed, "show_overlay_frame", text="")

    def draw(self, context):
        layout = self.layout

        layout.operator_context = "INVOKE_REGION_PREVIEW"
        layout.operator("sequencer.view_ghost_border", text="Set Overlay Region")
        layout.operator_context = "INVOKE_DEFAULT"

        layout.use_property_split = True
        layout.use_property_decorate = False

        st = context.space_data
        scene = context.sequencer_scene
        ed = scene.sequence_editor

        layout.active = ed.show_overlay_frame

        col = layout.column()
        col.prop(ed, "overlay_frame", text="Frame Offset")
        col.prop(st, "overlay_frame_type")
        col.use_property_split = False
        col.prop(ed, "use_overlay_frame_lock")


class SEQUENCER_PT_view_safe_areas(SequencerButtonsPanel_Output, Panel):
    bl_label = "Safe Areas"
    bl_options = {"DEFAULT_CLOSED"}
    bl_category = "View"

    @classmethod
    def poll(cls, context):
        st = context.space_data
        is_preview = st.view_type in {"PREVIEW", "SEQUENCER_PREVIEW"}
        return is_preview and (st.display_mode == "IMAGE") and context.sequencer_scene

    def draw_header(self, context):
        overlay_settings = context.space_data.preview_overlay
        self.layout.prop(overlay_settings, "show_safe_areas", text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        overlay_settings = context.space_data.preview_overlay
        safe_data = context.sequencer_scene.safe_areas

        layout.active = overlay_settings.show_safe_areas

        col = layout.column()

        sub = col.column()
        sub.prop(safe_data, "title", slider=True)
        sub.prop(safe_data, "action", slider=True)


class SEQUENCER_PT_view_safe_areas_center_cut(SequencerButtonsPanel_Output, Panel):
    bl_label = "Center-Cut Safe Areas"
    bl_parent_id = "SEQUENCER_PT_view_safe_areas"
    bl_options = {"DEFAULT_CLOSED"}
    bl_category = "View"

    @classmethod
    def poll(cls, context):
        return SequencerButtonsPanel_Output.poll(context) and context.sequencer_scene

    def draw_header(self, context):
        st = context.space_data

        layout = self.layout
        overlay_settings = context.space_data.preview_overlay
        layout.active = overlay_settings.show_safe_areas
        layout.prop(overlay_settings, "show_safe_center", text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        safe_data = context.sequencer_scene.safe_areas
        overlay_settings = context.space_data.preview_overlay

        layout.active = overlay_settings.show_safe_areas and overlay_settings.show_safe_center

        col = layout.column()
        col.prop(safe_data, "title_center", slider=True)
        col.prop(safe_data, "action_center", slider=True)


class SEQUENCER_PT_modifiers(SequencerButtonsPanel, Panel):
    bl_label = ""
    bl_options = {"HIDE_HEADER"}
    bl_category = "Modifiers"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        strip = context.active_strip
        if strip.type == "SOUND":
            sound = strip.sound
        else:
            sound = None

        if sound is None:
            row = layout.row()  # BFA - float left
            row.use_property_split = False
            row.prop(strip, "use_linear_modifiers")
            row.prop_decorator(strip, "use_linear_modifiers")

        layout.operator("wm.call_menu", text="Add Modifier", icon="ADD").name = "SEQUENCER_MT_modifier_add"
        layout.template_strip_modifiers()


class SEQUENCER_PT_annotation(AnnotationDataPanel, SequencerButtonsPanel_Output, Panel):
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_category = "View"

    @staticmethod
    def has_preview(context):
        st = context.space_data
        return st.view_type in {"PREVIEW", "SEQUENCER_PREVIEW"}

    @classmethod
    def poll(cls, context):
        return cls.has_preview(context)

    # NOTE: this is just a wrapper around the generic GP Panel
    # But, it should only show up when there are images in the preview region


class SEQUENCER_PT_annotation_onion(AnnotationOnionSkin, SequencerButtonsPanel_Output, Panel):
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_category = "View"
    bl_parent_id = "SEQUENCER_PT_annotation"
    bl_options = {"DEFAULT_CLOSED"}

    @staticmethod
    def has_preview(context):
        st = context.space_data
        return st.view_type in {"PREVIEW", "SEQUENCER_PREVIEW"}

    @classmethod
    def poll(cls, context):
        if context.annotation_data_owner is None:
            return False
        elif type(context.annotation_data_owner) is bpy.types.Object:
            return False
        else:
            gpl = context.active_annotation_layer
            if gpl is None:
                return False

        return cls.has_preview(context)

    # NOTE: this is just a wrapper around the generic GP Panel
    # But, it should only show up when there are images in the preview region


class SEQUENCER_PT_custom_props(SequencerButtonsPanel, PropertyPanel, Panel):
    COMPAT_ENGINES = {
        "BLENDER_RENDER",
        "BLENDER_WORKBENCH",
    }
    _context_path = "active_strip"
    _property_type = (bpy.types.Strip,)
    bl_category = "Strip"


class SEQUENCER_PT_snapping(Panel):
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "HEADER"
    bl_label = "Snapping"
    bl_ui_units_x = 11

    def draw(self, _context):
        pass


class SEQUENCER_PT_preview_snapping(Panel):
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "HEADER"
    bl_parent_id = "SEQUENCER_PT_snapping"
    bl_label = "Preview Snapping"

    @classmethod
    def poll(cls, context):
        st = context.space_data
        return st.view_type in {'PREVIEW', 'SEQUENCER_PREVIEW'} and context.sequencer_scene

    def draw(self, context):
        tool_settings = context.tool_settings
        sequencer_tool_settings = tool_settings.sequencer_tool_settings

        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False

        col = layout.column(align=True)
        col.label(text="Snap to")
        row = col.row()
        row.separator()
        row.prop(sequencer_tool_settings, "snap_to_borders")
        row = col.row()
        row.separator()
        row.prop(sequencer_tool_settings, "snap_to_center")
        row = col.row()
        row.separator()
        row.prop(sequencer_tool_settings, "snap_to_strips_preview")


class SEQUENCER_PT_sequencer_snapping(Panel):
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "HEADER"
    bl_parent_id = "SEQUENCER_PT_snapping"
    bl_label = "Sequencer Snapping"

    @classmethod
    def poll(cls, context):
        st = context.space_data
        return st.view_type in {'SEQUENCER', 'SEQUENCER_PREVIEW'} and context.sequencer_scene

    def draw(self, context):
        tool_settings = context.tool_settings
        sequencer_tool_settings = tool_settings.sequencer_tool_settings

        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False

        col = layout.column(align=True)
        col.label(text="Snap to")

        row = col.row()
        row.separator()
        row.prop(sequencer_tool_settings, "snap_to_frame_range")
        row = col.row()
        row.separator()
        row.prop(sequencer_tool_settings, "snap_to_current_frame")
        row = col.row()
        row.separator()
        row.prop(sequencer_tool_settings, "snap_to_hold_offset")
        row = col.row()
        row.separator()
        row.prop(sequencer_tool_settings, "snap_to_markers")
        row = col.row()
        row.separator()
        col.prop(sequencer_tool_settings, "snap_to_retiming_keys")

        col = layout.column(align=True)
        col.label(text="Ignore")
        row = col.row()
        row.separator()
        row.prop(sequencer_tool_settings, "snap_ignore_muted", text="Muted Strips")
        row = col.row()
        row.separator()
        row.prop(sequencer_tool_settings, "snap_ignore_sound", text="Sound Strips")

        col = layout.column(align=True)
        col.label(text="Current Frame")
        row = col.row()
        row.separator()
        row.prop(
            sequencer_tool_settings,
            "use_snap_current_frame_to_strips",
            text="Snap to Strips",
        )


# BFA menu
class SEQUENCER_PT_view_options(bpy.types.Panel):
    bl_label = "View Options"
    bl_category = "View"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "HEADER"

    def draw(self, context):
        layout = self.layout

        st = context.space_data
        overlay_settings = st.preview_overlay
        is_preview = st.view_type in {"PREVIEW", "SEQUENCER_PREVIEW"}
        is_sequencer_view = st.view_type in {"SEQUENCER", "SEQUENCER_PREVIEW"}
        tool_settings = context.tool_settings

        cache_settings = context.space_data.cache_overlay  # BFA

        if is_sequencer_view:
            col = layout.column(align=True)
            if st.view_type == "SEQUENCER":
                split = layout.split(factor=0.6)
                col = split.column()
                col.use_property_split = False
                col = split.column()

                if is_preview:
                    row = layout.row()
                    row.separator()
                    row.prop(st, "show_transform_preview", text="Preview During Transform")

            else:
                col.prop(st, "show_transform_preview", text="Preview During Transform")

            col = layout.column(align=True)
            col.prop(st, "show_seconds")
            col.prop(st, "show_locked_time")

            # BFA - Cache settings
            row = layout.row()
            row.prop(cache_settings, "show_cache", text="Display Cache")
            if cache_settings.show_cache:
                row.label(icon="DISCLOSURE_TRI_DOWN")
            else:
                row.label(icon="DISCLOSURE_TRI_RIGHT")

            if cache_settings.show_cache:
                split = layout.split(factor=0.05)
                col = split.column()
                col.label(text="")

                col = split.column()
                show_developer_ui = context.preferences.view.show_developer_ui
                col.prop(cache_settings, "show_cache_final_out", text="Final")
                if show_developer_ui:
                    col.prop(cache_settings, "show_cache_raw", text="Raw")

            layout.use_property_split = False
            layout.prop(st, "show_markers")

        if is_preview:
            layout.use_property_split = False
            if st.display_mode == "IMAGE":
                layout.prop(overlay_settings, "show_metadata")

            layout.use_property_split = False
            layout.prop(st, "use_zoom_to_fit", text="Auto Zoom to Fit")

        if is_sequencer_view:
            col = layout.column(align=True)
            col.prop(tool_settings, "lock_markers")
            col.prop(st, "use_marker_sync")
            col.prop(st, "use_clamp_view")


# BFA menu
class SEQUENCER_MT_fades_add(Menu):
    bl_label = "Fade"

    def draw(self, context):
        layout = self.layout

        layout.operator("sequencer.fades_add", text="Fade In and Out", icon="IPO_EASE_IN_OUT").type = "IN_OUT"
        layout.operator("sequencer.fades_add", text="Fade In", icon="IPO_EASE_IN").type = "IN"
        layout.operator("sequencer.fades_add", text="Fade Out", icon="IPO_EASE_OUT").type = "OUT"
        layout.operator(
            "sequencer.fades_add",
            text="From current Frame",
            icon="BEFORE_CURRENT_FRAME",
        ).type = "CURSOR_FROM"
        layout.operator("sequencer.fades_add", text="To current Frame", icon="AFTER_CURRENT_FRAME").type = "CURSOR_TO"


classes = (
    SEQUENCER_MT_change,  # BFA - no longer used
    SEQUENCER_HT_tool_header,
    SEQUENCER_HT_header,
    SEQUENCER_HT_playback_controls,
    SEQUENCER_MT_editor_menus,
    SEQUENCER_MT_range,
    SEQUENCER_MT_view_pie_menus,  # BFA
    SEQUENCER_MT_view,
    SEQUENCER_MT_view_annotations,  # BFA
    SEQUENCER_MT_export,  # BFA
    SEQUENCER_MT_view_cache,  # BFA
    SEQUENCER_MT_preview_zoom,
    SEQUENCER_MT_proxy,
    SEQUENCER_MT_select_handle,
    SEQUENCER_MT_select_channel,
    SEQUENCER_MT_select_linked,  # BFA - sub menu
    SEQUENCER_MT_select,
    SEQUENCER_MT_marker,
    SEQUENCER_MT_navigation,
    SEQUENCER_MT_add,
    SEQUENCER_MT_add_effect,
    SEQUENCER_MT_add_transitions,
    SEQUENCER_MT_add_empty,
    SEQUENCER_MT_strip_effect,
    SEQUENCER_MT_strip_effect_change,
    SEQUENCER_MT_strip_movie,
    SEQUENCER_MT_strip,
    SEQUENCER_MT_strip_transform,
    SEQUENCER_MT_strip_retiming,
    SEQUENCER_MT_strip_text,
    SEQUENCER_MT_strip_show_hide,
    SEQUENCER_MT_strip_animation,
    SEQUENCER_MT_strip_mirror,
    SEQUENCER_MT_strip_input,
    SEQUENCER_MT_strip_lock_mute,
    SEQUENCER_MT_strip_modifiers,
    SEQUENCER_MT_image,
    SEQUENCER_MT_image_transform,
    SEQUENCER_MT_image_clear,
    SEQUENCER_MT_image_apply,
    SEQUENCER_MT_color_tag_picker,
    SEQUENCER_MT_context_menu,
    SEQUENCER_MT_preview_context_menu,
    SEQUENCER_MT_pivot_pie,
    SEQUENCER_MT_retiming,
    SEQUENCER_MT_view_pie,
    SEQUENCER_MT_preview_view_pie,
    SEQUENCER_MT_modifier_add,
    SEQUENCER_PT_color_tag_picker,
    SEQUENCER_PT_active_tool,
    SEQUENCER_MT_change_scene_with_icons,  # BFA
    SEQUENCER_PT_strip,

    SEQUENCER_PT_gizmo_display,
    SEQUENCER_PT_overlay,
    SEQUENCER_PT_preview_overlay,
    SEQUENCER_PT_sequencer_overlay,
    SEQUENCER_PT_sequencer_overlay_strips,
    SEQUENCER_PT_sequencer_overlay_waveforms,
    SEQUENCER_PT_effect,
    SEQUENCER_PT_scene,
    SEQUENCER_PT_scene_sound,
    SEQUENCER_PT_mask,
    SEQUENCER_PT_effect_text_style,
    SEQUENCER_PT_effect_text_outline,
    SEQUENCER_PT_effect_text_shadow,
    SEQUENCER_PT_effect_text_box,
    SEQUENCER_PT_effect_text_layout,
    SEQUENCER_PT_movie_clip,
    SEQUENCER_PT_adjust_comp,
    SEQUENCER_PT_adjust_transform,
    SEQUENCER_PT_adjust_crop,
    SEQUENCER_PT_adjust_video,
    SEQUENCER_PT_adjust_color,
    SEQUENCER_PT_adjust_sound,
    SEQUENCER_PT_time,
    SEQUENCER_PT_source,
    SEQUENCER_PT_modifiers,
    SEQUENCER_PT_cache_settings,
    SEQUENCER_PT_cache_view_settings,
    SEQUENCER_PT_proxy_settings,
    SEQUENCER_PT_strip_proxy,
    SEQUENCER_PT_custom_props,
    SEQUENCER_PT_view,
    SEQUENCER_PT_view_cursor,
    SEQUENCER_PT_frame_overlay,
    SEQUENCER_PT_view_safe_areas,
    SEQUENCER_PT_view_safe_areas_center_cut,
    SEQUENCER_PT_preview,
    SEQUENCER_PT_annotation,
    SEQUENCER_PT_annotation_onion,
    SEQUENCER_PT_snapping,
    SEQUENCER_PT_preview_snapping,
    SEQUENCER_PT_sequencer_snapping,
    SEQUENCER_PT_view_options,  # BFA
    SEQUENCER_MT_fades_add,  # BFA
    SEQUENCER_MT_strip_text_characters,  # BFA
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)
