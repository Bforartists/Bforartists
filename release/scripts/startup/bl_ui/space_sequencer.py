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
from bpy.types import (
    Header,
    Menu,
    Panel,
)
from bpy.app.translations import (
    contexts as i18n_contexts,
    pgettext_iface as iface_,
)
from bl_ui.properties_grease_pencil_common import (
    AnnotationDataPanel,
    AnnotationOnionSkin,
)
from bl_ui.space_toolsystem_common import (
    ToolActivePanelHelper,
)
from rna_prop_ui import PropertyPanel


def act_strip(context):
    try:
        return context.scene.sequence_editor.active_strip
    except AttributeError:
        return None


def selected_sequences_len(context):
    selected_sequences = getattr(context, "selected_sequences", None)
    if selected_sequences is None:
        return 0
    return len(selected_sequences)


def draw_color_balance(layout, color_balance):

    layout.use_property_split = False

    flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=False)
    col = flow.column()

    box = col.box()
    split = box.split(factor=0.35)
    col = split.column(align=True)
    col.label(text="Lift:")
    col.separator()
    col.separator()
    col.prop(color_balance, "lift", text="")
    col.prop(color_balance, "invert_lift", text="Invert", icon='ARROW_LEFTRIGHT')
    split.template_color_picker(color_balance, "lift", value_slider=True, cubic=True)

    col = flow.column()

    box = col.box()
    split = box.split(factor=0.35)
    col = split.column(align=True)
    col.label(text="Gamma:")
    col.separator()
    col.separator()
    col.prop(color_balance, "gamma", text="")
    col.prop(color_balance, "invert_gamma", text="Invert", icon='ARROW_LEFTRIGHT')
    split.template_color_picker(color_balance, "gamma", value_slider=True, lock_luminosity=True, cubic=True)

    col = flow.column()

    box = col.box()
    split = box.split(factor=0.35)
    col = split.column(align=True)
    col.label(text="Gain:")
    col.separator()
    col.separator()
    col.prop(color_balance, "gain", text="")
    col.prop(color_balance, "invert_gain", text="Invert", icon='ARROW_LEFTRIGHT')
    split.template_color_picker(color_balance, "gain", value_slider=True, lock_luminosity=True, cubic=True)


class SEQUENCER_PT_active_tool(ToolActivePanelHelper, Panel):
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Tool"


class SEQUENCER_HT_tool_header(Header):
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'TOOL_HEADER'

    def draw(self, context):
        layout = self.layout

        self.draw_tool_settings(context)

        # TODO: options popover.

    def draw_tool_settings(self, context):
        layout = self.layout

        # Active Tool
        # -----------
        from bl_ui.space_toolsystem_common import ToolSelectPanelHelper
        tool = ToolSelectPanelHelper.draw_active_tool_header(context, layout)
        tool_mode = context.mode if tool is None else tool.mode


class SEQUENCER_HT_header(Header):
    bl_space_type = 'SEQUENCE_EDITOR'

    def draw(self, context):
        layout = self.layout

        st = context.space_data
        scene = context.scene
        sequencer_tool_settings = context.tool_settings.sequencer_tool_settings

        ALL_MT_editormenu.draw_hidden(context, layout) # bfa - show hide the editormenu
        layout.prop(st, "view_type", text="")
        SEQUENCER_MT_editor_menus.draw_collapsible(context, layout)

        if st.view_type in {'SEQUENCER', 'SEQUENCER_PREVIEW'}:
            layout.separator_spacer()
            row = layout.row(align=True)
            row.prop(sequencer_tool_settings, "fit_method", text="")

        if st.view_type in {'PREVIEW', 'SEQUENCER_PREVIEW'}:
            if st.view_type == 'PREVIEW':
                layout.separator_spacer()

            layout.prop(st, "display_mode", text="", icon_only=True)
            layout.prop(st, "preview_channels", text="", icon_only=True)

            gpd = context.gpencil_data
            tool_settings = context.tool_settings

            # Proportional editing
            if gpd and gpd.use_stroke_edit_mode:
                row = layout.row(align=True)
                row.prop(tool_settings, "use_proportional_edit", icon_only=True)
                if tool_settings.use_proportional_edit:
                    row.prop(tool_settings, "proportional_edit_falloff", icon_only=True)

        row = layout.row(align=True)
        row.prop(st, "show_strip_overlay", text="", icon='OVERLAY')
        sub = row.row(align=True)
        sub.popover(panel="SEQUENCER_PT_overlay", text="")
        sub.active = st.show_strip_overlay


class SEQUENCER_PT_overlay(Panel):
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'HEADER'
    bl_label = "Overlays"
    bl_ui_units_x = 7

    def draw(self, _context):
        pass


class SEQUENCER_PT_preview_overlay(Panel):
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'HEADER'
    bl_parent_id = 'SEQUENCER_PT_overlay'
    bl_label = "Preview Overlays"

    @classmethod
    def poll(cls, context):
        st = context.space_data
        return st.view_type in {'PREVIEW', 'SEQUENCER_PREVIEW'} and st.display_mode == 'IMAGE'

    def draw(self, context):
        ed = context.scene.sequence_editor
        st = context.space_data
        layout = self.layout

        layout.active = st.show_strip_overlay
        layout.prop(ed, "show_overlay", text="Frame Overlay")
        layout.prop(st, "show_safe_areas", text="Safe Areas")
        layout.prop(st, "show_metadata", text="Metadata")
        layout.prop(st, "show_annotation", text="Annotations")


class SEQUENCER_PT_sequencer_overlay(Panel):
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'HEADER'
    bl_parent_id = 'SEQUENCER_PT_overlay'
    bl_label = "Sequencer Overlays"

    @classmethod
    def poll(cls, context):
        st = context.space_data
        return st.view_type in {'SEQUENCER', 'SEQUENCER_PREVIEW'}

    def draw(self, context):
        st = context.space_data
        layout = self.layout

        layout.active = st.show_strip_overlay

        layout.prop(st, "show_strip_name", text="Name")
        layout.prop(st, "show_strip_source", text="Source")
        layout.prop(st, "show_strip_duration", text="Duration")

        layout.separator()

        layout.prop(st, "show_strip_offset", text="Offsets")
        layout.prop(st, "show_fcurves", text="F-Curves")

        layout.separator()

        layout.prop_menu_enum(st, "waveform_display_type")


# bfa - show hide the editormenu
class ALL_MT_editormenu(Menu):
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):

        row = layout.row(align=True)
        row.template_header() # editor type menus

class SEQUENCER_MT_editor_menus(Menu):
    bl_idname = "SEQUENCER_MT_editor_menus"
    bl_label = ""

    def draw(self, context):
        layout = self.layout
        st = context.space_data

        layout.menu("SCREEN_MT_user_menu", text = "Quick") # Quick favourites menu
        layout.menu("SEQUENCER_MT_view")
        layout.menu("SEQUENCER_MT_export")

        if st.view_type in {'SEQUENCER', 'SEQUENCER_PREVIEW'}:
            layout.menu("SEQUENCER_MT_navigation")
            layout.menu("SEQUENCER_MT_select")
            if st.show_markers:
                layout.menu("SEQUENCER_MT_marker")
            layout.menu("SEQUENCER_MT_add")
            layout.menu("SEQUENCER_MT_strip")


class SEQUENCER_MT_view_cache(Menu):
    bl_label = "Cache"

    def draw(self, context):
        layout = self.layout

        ed = context.scene.sequence_editor
        layout.prop(ed, "show_cache")
        layout.separator()

        col = layout.column()
        col.enabled = ed.show_cache

        col.prop(ed, "show_cache_final_out")
        col.prop(ed, "show_cache_raw")
        col.prop(ed, "show_cache_preprocessed")
        col.prop(ed, "show_cache_composite")


class SEQUENCER_MT_range(Menu):
    bl_label = "Range"

    def draw(self, _context):
        layout = self.layout

        layout.operator("anim.previewrange_set", text="Set Preview Range", icon = "PREVIEW_RANGE")
        layout.operator("sequencer.set_range_to_strips", text="Set Preview Range to Strips", icon = "PREVIEW_RANGE").preview = True
        layout.operator("anim.previewrange_clear", text="Clear Preview Range", icon = "CLEAR")

        layout.separator()

        layout.operator("anim.start_frame_set", text="Set Start Frame", icon = "AFTER_CURRENT_FRAME")
        layout.operator("anim.end_frame_set", text="Set End Frame", icon = "BEFORE_CURRENT_FRAME")
        layout.operator("sequencer.set_range_to_strips", text="Set Frame Range to Strips", icon = "PREVIEW_RANGE")

class SEQUENCER_MT_preview_zoom(Menu):
    bl_label = "Fractional Zoom"

    def draw(self, _context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_PREVIEW'

        ratios = ((1, 8), (1, 4), (1, 2), (1, 1), (2, 1), (4, 1), (8, 1))

        for i, (a, b) in enumerate(ratios):
            if i in {3, 4}:  # Draw separators around Zoom 1:1.
                layout.separator()

            layout.operator(
                "sequencer.view_zoom_ratio",
                text=iface_("Zoom %d:%d") % (a, b), icon = "ZOOM_SET",
                translate=False,
            ).ratio = a / b
        layout.operator_context = 'INVOKE_DEFAULT'


class SEQUENCER_MT_proxy(Menu):
    bl_label = "Proxy"

    def draw(self, context):
        layout = self.layout

        st = context.space_data
        col = layout.column()
        col.operator("sequencer.enable_proxies", text="Setup")
        col.operator("sequencer.rebuild_proxy", text="Rebuild")
        col.enabled = selected_sequences_len(context) >= 1
        layout.prop(st, "proxy_render_size", text="")


class SEQUENCER_MT_view(Menu):
    bl_label = "View"

    def draw(self, context):
        layout = self.layout

        st = context.space_data
        is_preview = st.view_type in {'PREVIEW', 'SEQUENCER_PREVIEW'}
        is_sequencer_view = st.view_type in {'SEQUENCER', 'SEQUENCER_PREVIEW'}
        scene = context.scene
        ed = scene.sequence_editor

        if st.view_type == 'PREVIEW':
            # Specifying the REGION_PREVIEW context is needed in preview-only
            # mode, else the lookup for the shortcut will fail in
            # wm_keymap_item_find_props() (see T32595).
            layout.operator_context = 'INVOKE_REGION_PREVIEW'
        layout.prop(st, "show_region_ui")
        layout.prop(st, "show_region_toolbar")
        layout.operator_context = 'INVOKE_DEFAULT'

        if is_sequencer_view:
            layout.prop(st, "show_region_hud")

        layout.separator()

        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("view2d.zoom_in", icon = "ZOOM_IN")
        layout.operator("view2d.zoom_out", icon = "ZOOM_OUT")

        if is_sequencer_view:
            layout.operator_context = 'INVOKE_REGION_WIN'
            layout.operator("view2d.zoom_border", text = "Zoom Border", icon = "ZOOM_BORDER")

            layout.separator()

            layout.operator("sequencer.view_all", text="Frame All", icon = "VIEWALL" )
            layout.operator("sequencer.view_selected", text = "Frame Selected", icon='VIEW_SELECTED')

        if is_preview:
            layout.operator_context = 'INVOKE_REGION_PREVIEW'

            if is_sequencer_view:
                layout.menu("SEQUENCER_MT_preview_zoom", text="Fractional Preview Zoom")
            else:
                layout.operator("view2d.zoom_border", text="Zoom Border", icon = "ZOOM_BORDER")
                layout.menu("SEQUENCER_MT_preview_zoom")

            if st.display_mode == 'IMAGE':
                layout.prop(st, "use_zoom_to_fit")
            elif st.display_mode == 'WAVEFORM':
                layout.separator()
                layout.prop(st, "show_separate_color", text="Show Separate Color Channels")

            layout.separator()

            layout.operator("sequencer.view_all_preview", text="Fit Preview in window", icon = "VIEW_FIT")

            layout.separator()

            layout.menu("SEQUENCER_MT_proxy")

            layout.operator_context = 'INVOKE_DEFAULT'

        if is_sequencer_view:
            layout.separator()

            layout.operator_context = 'INVOKE_DEFAULT'

            layout.separator()

            layout.operator_context = 'INVOKE_REGION_WIN'
            layout.operator("sequencer.refresh_all", icon='FILE_REFRESH', text="Refresh All")


        layout.separator()

        layout.operator("render.opengl", text="Sequence Render Image", icon='RENDER_STILL').sequencer = True
        props = layout.operator("render.opengl", text="Sequence Render Animation", icon='RENDER_ANIMATION')
        props.animation = True
        props.sequencer = True

        layout.separator()

        # Note that the context is needed for the shortcut to display properly.
        layout.operator_context = 'INVOKE_REGION_PREVIEW' if is_preview else 'INVOKE_REGION_WIN'
        props = layout.operator(
            "wm.context_toggle_enum",
            text="Toggle Sequencer/Preview",
            icon='SEQ_SEQUENCER' if is_preview else 'SEQ_PREVIEW',
        )
        props.data_path = "space_data.view_type"
        props.value_1 = 'SEQUENCER'
        props.value_2 = 'PREVIEW'
        layout.operator_context = 'INVOKE_DEFAULT'

        layout.separator()

        layout.menu("INFO_MT_area")


class SEQUENCER_MT_export(Menu):
    bl_label = "Export"

    def draw(self, context):
        layout = self.layout

        layout.operator("sequencer.export_subtitles", text="Export Subtitles", icon='EXPORT')


# Workaround to separate the tooltips
class SEQUENCER_MT_select_inverse(bpy.types.Operator):
    """Inverts the current selection """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "sequencer.select_all_inverse"        # unique identifier for buttons and menu items to reference.
    bl_label = "Select Inverse"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.sequencer.select_all(action = 'INVERT')
        return {'FINISHED'}

# Workaround to separate the tooltips
class SEQUENCER_MT_select_none(bpy.types.Operator):
    """Deselects everything """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "sequencer.select_all_none"        # unique identifier for buttons and menu items to reference.
    bl_label = "Select None"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.sequencer.select_all(action = 'DESELECT')
        return {'FINISHED'}


class SEQUENCER_MT_select_handle(Menu):
    bl_label = "Select Handle"

    def draw(self, _context):
        layout = self.layout

        layout.operator("sequencer.select_handles", text="Both", icon = "SELECT_HANDLE_BOTH").side = 'BOTH'
        layout.operator("sequencer.select_handles", text="Left", icon = "SELECT_HANDLE_LEFT").side = 'LEFT'
        layout.operator("sequencer.select_handles", text="Right", icon = "SELECT_HANDLE_RIGHT").side = 'RIGHT'

        layout.separator()

        layout.operator("sequencer.select_handles", text="Both Neighbors", icon = "SELECT_HANDLE_BOTH").side = 'BOTH_NEIGHBORS'
        layout.operator("sequencer.select_handles", text="Left Neighbor", icon = "SELECT_HANDLE_LEFT").side = 'LEFT_NEIGHBOR'
        layout.operator("sequencer.select_handles", text="Right Neighbor", icon = "SELECT_HANDLE_RIGHT").side = 'RIGHT_NEIGHBOR'


class SEQUENCER_MT_select_channel(Menu):
    bl_label = "Select Channel"

    def draw(self, _context):
        layout = self.layout

        layout.operator("sequencer.select_side", text="Left", icon = "RESTRICT_SELECT_OFF").side = 'LEFT'
        layout.operator("sequencer.select_side", text="Right", icon = "RESTRICT_SELECT_OFF").side = 'RIGHT'
        layout.separator()
        layout.operator("sequencer.select_side", text="Both Sides", icon = "RESTRICT_SELECT_OFF").side = 'BOTH'


class SEQUENCER_MT_select_linked(Menu):
    bl_label = "Select Linked"

    def draw(self, _context):
        layout = self.layout

        layout.operator("sequencer.select_linked", text="All", icon='SELECT_ALL')
        layout.operator("sequencer.select_less", text="Less", icon = "SELECTLESS")
        layout.operator("sequencer.select_more", text="More", icon = "SELECTMORE")


class SEQUENCER_MT_select(Menu):
    bl_label = "Select"

    def draw(self, _context):
        layout = self.layout

        layout.operator("sequencer.select_all", text="All", icon='SELECT_ALL').action = 'SELECT'
        layout.operator("sequencer.select_all_none", text="None", icon='SELECT_NONE') # bfa - separated tooltip
        layout.operator("sequencer.select_all_inverse", text="Inverse", icon='INVERSE') # bfa - separated tooltip

        layout.separator()

        layout.operator("sequencer.select_box", text="Box Select", icon='BORDER_RECT')
        props = layout.operator("sequencer.select_box", text="Box Select (Include Handles)", icon='BORDER_RECT')
        props.include_handles = True

        layout.separator()

        layout.operator_menu_enum("sequencer.select_side_of_frame", "side", text="Side of Frame")
        layout.menu("SEQUENCER_MT_select_handle", text="Handle")
        layout.menu("SEQUENCER_MT_select_channel", text="Channel")
        layout.menu("SEQUENCER_MT_select_linked", text="Linked")

        layout.separator()
        layout.operator_menu_enum("sequencer.select_grouped", "type", text="Grouped")


class SEQUENCER_MT_marker(Menu):
    bl_label = "Marker"

    def draw(self, context):
        layout = self.layout

        st = context.space_data
        is_sequencer_view = st.view_type in {'SEQUENCER', 'SEQUENCER_PREVIEW'}

        from bl_ui.space_time import marker_menu_generic
        marker_menu_generic(layout, context)


class SEQUENCER_MT_change(Menu):
    bl_label = "Change"

    def draw(self, context):
        layout = self.layout
        strip = act_strip(context)

        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.operator_menu_enum("sequencer.change_effect_input", "swap")
        layout.operator_menu_enum("sequencer.change_effect_type", "type")
        prop = layout.operator("sequencer.change_path", text="Path/Files")

        if strip:
            strip_type = strip.type

            if strip_type == 'IMAGE':
                prop.filter_image = True
            elif strip_type == 'MOVIE':
                prop.filter_movie = True
            elif strip_type == 'SOUND':
                prop.filter_sound = True


class SEQUENCER_MT_navigation(Menu):
    bl_label = "Navi"

    def draw(self, _context):
        layout = self.layout

        layout.operator("screen.animation_play", icon='PLAY')

        layout.separator()

        layout.operator("sequencer.view_frame", icon = "VIEW_FRAME" )

        layout.separator()

        props = layout.operator("sequencer.strip_jump", text="Jump to Previous Strip", icon='PREVIOUSACTIVE')
        props.next = False
        props.center = False
        props = layout.operator("sequencer.strip_jump", text="Jump to Next Strip", icon='NEXTACTIVE')
        props.next = True
        props.center = False

        layout.separator()

        props = layout.operator("sequencer.strip_jump", text="Jump to Previous Strip (Center)", icon='PREVIOUSACTIVE')
        props.next = False
        props.center = True
        props = layout.operator("sequencer.strip_jump", text="Jump to Next Strip (Center)", icon='NEXTACTIVE')
        props.next = True
        props.center = True

        layout.separator()

        layout.menu("SEQUENCER_MT_range")


class SEQUENCER_MT_add(Menu):
    bl_label = "Add"
    bl_translation_context = i18n_contexts.operator_default

    def draw(self, context):

        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        bpy_data_scenes_len = len(bpy.data.scenes)
        if bpy_data_scenes_len > 10:
            layout.operator_context = 'INVOKE_DEFAULT'
            layout.operator("sequencer.scene_strip_add", text="Scene...", icon='SCENE_DATA')
        elif bpy_data_scenes_len > 1:
            layout.operator_menu_enum("sequencer.scene_strip_add", "scene", text="Scene", icon='SCENE_DATA')
        else:
            layout.menu("SEQUENCER_MT_add_empty", text="Scene", icon='SCENE_DATA')
        del bpy_data_scenes_len

        bpy_data_movieclips_len = len(bpy.data.movieclips)
        if bpy_data_movieclips_len > 10:
            layout.operator_context = 'INVOKE_DEFAULT'
            layout.operator("sequencer.movieclip_strip_add", text="Clip...", icon='TRACKER')
        elif bpy_data_movieclips_len > 0:
            layout.operator_menu_enum("sequencer.movieclip_strip_add", "clip", text="Clip", icon='TRACKER')
        else:
            layout.menu("SEQUENCER_MT_add_empty", text="Clip", icon='TRACKER')
        del bpy_data_movieclips_len

        bpy_data_masks_len = len(bpy.data.masks)
        if bpy_data_masks_len > 10:
            layout.operator_context = 'INVOKE_DEFAULT'
            layout.operator("sequencer.mask_strip_add", text="Mask...", icon='MOD_MASK')
        elif bpy_data_masks_len > 0:
            layout.operator_menu_enum("sequencer.mask_strip_add", "mask", text="Mask", icon='MOD_MASK')
        else:
            layout.menu("SEQUENCER_MT_add_empty", text="Mask", icon='MOD_MASK')
        del bpy_data_masks_len

        layout.separator()

        layout.operator("sequencer.movie_strip_add", text="Movie", icon='FILE_MOVIE')
        layout.operator("sequencer.sound_strip_add", text="Sound", icon='FILE_SOUND')
        layout.operator("sequencer.image_strip_add", text="Image/Sequence", icon='FILE_IMAGE')

        layout.separator()

        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("sequencer.effect_strip_add", text="Color", icon='COLOR').type = 'COLOR'
        layout.operator("sequencer.effect_strip_add", text="Text", icon='FONT_DATA').type = 'TEXT'

        layout.separator()

        layout.operator("sequencer.effect_strip_add", text="Adjustment Layer", icon='COLOR').type = 'ADJUSTMENT'

        layout.operator_context = 'INVOKE_DEFAULT'
        layout.menu("SEQUENCER_MT_add_effect", icon='SHADERFX')

        col = layout.column()
        col.menu("SEQUENCER_MT_add_transitions", icon='ARROW_LEFTRIGHT')
        col.enabled = selected_sequences_len(context) >= 2

        col = layout.column()
        col.operator_menu_enum("sequencer.fades_add", "type", text="Fade", icon='IPO_EASE_IN_OUT')
        col.enabled = selected_sequences_len(context) >= 1
        col.operator("sequencer.fades_clear", text="Clear Fade", icon="CLEAR")


class SEQUENCER_MT_add_empty(Menu):
    bl_label = "Empty"

    def draw(self, _context):
        layout = self.layout

        layout.label(text="No Items Available")


class SEQUENCER_MT_add_transitions(Menu):
    bl_label = "Transition"

    def draw(self, context):

        layout = self.layout

        col = layout.column()

        col.operator("sequencer.crossfade_sounds", text="Sound Crossfade", icon='SPEAKER')

        col.separator()

        col.operator("sequencer.effect_strip_add", text="Cross", icon='NODE_VECTOR').type = 'CROSS'
        col.operator("sequencer.effect_strip_add", text="Gamma Cross", icon='NODE_GAMMA').type = 'GAMMA_CROSS'

        col.separator()

        col.operator("sequencer.effect_strip_add", text="Wipe", icon='NODE_VECTOR_TRANSFORM').type = 'WIPE'
        col.enabled = selected_sequences_len(context) >= 2


class SEQUENCER_MT_add_effect(Menu):
    bl_label = "Effect Strip"

    def draw(self, context):

        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        col = layout.column()
        col.operator("sequencer.effect_strip_add", text="Add", icon='SEQ_ADD').type = 'ADD'
        col.operator("sequencer.effect_strip_add", text="Subtract", icon='NODE_INVERT').type = 'SUBTRACT'
        col.operator("sequencer.effect_strip_add", text="Multiply", icon='SEQ_MULTIPLY').type = 'MULTIPLY'
        col.operator("sequencer.effect_strip_add", text="Over Drop", icon='SEQ_ALPHA_OVER').type = 'OVER_DROP'
        col.operator("sequencer.effect_strip_add", text="Alpha Over", icon='IMAGE_ALPHA').type = 'ALPHA_OVER'
        col.operator("sequencer.effect_strip_add", text="Alpha Under", icon='NODE_HOLDOUTSHADER').type = 'ALPHA_UNDER'
        col.operator("sequencer.effect_strip_add", text="Color Mix", icon='NODE_MIXRGB').type = 'COLORMIX'
        col.enabled = selected_sequences_len(context) >= 2

        layout.separator()

        layout.operator("sequencer.effect_strip_add", text="Multicam Selector", icon='SEQ_MULTICAM').type = 'MULTICAM'

        layout.separator()

        col = layout.column()
        col.operator("sequencer.effect_strip_add", text="Transform", icon='TRANSFORM_MOVE').type = 'TRANSFORM'
        col.operator("sequencer.effect_strip_add", text="Speed Control", icon='NODE_CURVE_TIME').type = 'SPEED'

        col.separator()

        col.operator("sequencer.effect_strip_add", text="Glow", icon='LIGHT_SUN').type = 'GLOW'
        col.operator("sequencer.effect_strip_add", text="Gaussian Blur", icon='NODE_BLUR').type = 'GAUSSIAN_BLUR'
        col.enabled = selected_sequences_len(context) != 0


class SEQUENCER_MT_strip_image_transform(Menu):
    bl_label = "Image Transform"

    def draw(self, _context):
        layout = self.layout

        layout.operator("sequencer.strip_transform_fit", text="Scale To Fit").fit_method = 'FIT'
        layout.operator("sequencer.strip_transform_fit", text="Scale to Fill").fit_method = 'FILL'
        layout.operator("sequencer.strip_transform_fit", text="Stretch To Fill").fit_method = 'STRETCH'
        layout.separator()

        layout.operator("sequencer.strip_transform_clear", text="Clear Position").property = 'POSITION'
        layout.operator("sequencer.strip_transform_clear", text="Clear Scale").property = 'SCALE'
        layout.operator("sequencer.strip_transform_clear", text="Clear Rotation").property = 'ROTATION'
        layout.operator("sequencer.strip_transform_clear", text="Clear All").property = 'ALL'


class SEQUENCER_MT_strip_transform(Menu):
    bl_label = "Transform"

    def draw(self, _context):
        layout = self.layout

        layout.operator("transform.seq_slide", text="Move", icon = "TRANSFORM_MOVE")
        layout.operator("transform.transform", text="Move/Extend from Current Frame", icon = "SEQ_MOVE_EXTEND").mode = 'TIME_EXTEND'
        layout.operator("sequencer.slip", text="Slip Strip Contents", icon = "SEQ_SLIP_CONTENTS")

        layout.separator()
        layout.operator("sequencer.swap", text="Swap Strip Left", icon = "SEQ_SWAP_LEFT").side = 'LEFT'
        layout.operator("sequencer.swap", text="Swap Strip Right", icon = "SEQ_SWAP_RIGHT").side = 'RIGHT'

        layout.separator()
        layout.operator("sequencer.gap_remove", icon = "SEQ_REMOVE_GAPS").all = False
        layout.operator("sequencer.gap_insert", icon = "SEQ_INSERT_GAPS")


class SEQUENCER_MT_strip_input(Menu):
    bl_label = "Inputs"

    def draw(self, context):
        layout = self.layout
        strip = act_strip(context)

        layout.operator("sequencer.reload", text="Reload Strips", icon = "FILE_REFRESH")
        layout.operator("sequencer.reload", text="Reload Strips and Adjust Length", icon = "FILE_REFRESH").adjust_length = True
        prop = layout.operator("sequencer.change_path", text="Change Path/Files", icon = "FILE_MOVIE")
        layout.operator("sequencer.swap_data", text="Swap Data", icon = "SWAP")

        if strip:
            strip_type = strip.type

            if strip_type == 'IMAGE':
                prop.filter_image = True
            elif strip_type == 'MOVIE':
                prop.filter_movie = True
            elif strip_type == 'SOUND':
                prop.filter_sound = True


class SEQUENCER_MT_strip_lock_mute(Menu):
    bl_label = "Lock/Mute"

    def draw(self, _context):
        layout = self.layout

        layout.operator("sequencer.lock", icon='LOCKED')
        layout.operator("sequencer.unlock", icon='UNLOCKED')

        layout.separator()

        layout.operator("sequencer.mute", icon='HIDE_ON').unselected = False
        layout.operator("sequencer.unmute", icon='HIDE_OFF').unselected = False
        layout.operator("sequencer.mute", text="Mute Unselected Strips", icon='HIDE_UNSELECTED').unselected = True
        layout.operator("sequencer.unmute", text="Unmute Deselected Strips", icon='SHOW_UNSELECTED').unselected = True


class SEQUENCER_MT_strip_effect(Menu):
    bl_label = "Effect Strip"

    def draw(self, _context):
        layout = self.layout

        layout.operator_menu_enum("sequencer.change_effect_input", "swap")
        layout.operator_menu_enum("sequencer.change_effect_type", "type")
        layout.operator("sequencer.reassign_inputs", icon='RANDOMIZE_TRANSFORM')
        layout.operator("sequencer.swap_inputs", icon='RANDOMIZE')


class SEQUENCER_MT_strip_movie(Menu):
    bl_label = "Movie Strip"

    def draw(self, _context):
        layout = self.layout

        layout.operator("sequencer.rendersize", icon='RENDER_REGION')
        layout.operator("sequencer.deinterlace_selected_movies", icon='SEQ_DEINTERLACE')


class SEQUENCER_MT_strip(Menu):
    bl_label = "Strip"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.separator()
        layout.menu("SEQUENCER_MT_strip_transform")
        layout.menu("SEQUENCER_MT_strip_image_transform")
        layout.operator("sequencer.snap", icon = "SEQ_SNAP_STRIP")
        layout.operator("sequencer.offset_clear", icon = "SEQ_CLEAR_OFFSET")

        layout.separator()
        layout.operator("sequencer.split", text="Split", icon='CUT').type = 'SOFT'
        layout.operator("sequencer.split", text="Hold Split", icon='CUT').type = 'HARD'

        layout.separator()
        layout.operator("sequencer.copy", text="Copy", icon='COPYDOWN')
        layout.operator("sequencer.paste", text="Paste", icon='PASTEDOWN')
        layout.operator("sequencer.duplicate_move", icon='DUPLICATE')
        layout.operator("sequencer.delete", text="Delete", icon='DELETE')

        strip = act_strip(context)

        if strip:
            strip_type = strip.type

            if strip_type != 'SOUND':
                layout.separator()
                layout.operator_menu_enum("sequencer.strip_modifier_add", "type", text="Add Strip Modifier")
                layout.operator("sequencer.strip_modifier_copy", text="Copy Modifiers to Selection", icon='COPYDOWN')

            if strip_type in {
                    'CROSS', 'ADD', 'SUBTRACT', 'ALPHA_OVER', 'ALPHA_UNDER',
                    'GAMMA_CROSS', 'MULTIPLY', 'OVER_DROP', 'WIPE', 'GLOW',
                    'TRANSFORM', 'COLOR', 'SPEED', 'MULTICAM', 'ADJUSTMENT',
                    'GAUSSIAN_BLUR',
            }:
                layout.separator()
                layout.menu("SEQUENCER_MT_strip_effect")
            elif strip_type == 'MOVIE':
                layout.separator()
                layout.menu("SEQUENCER_MT_strip_movie")
            elif strip_type == 'IMAGE':
                layout.separator()
                layout.operator("sequencer.rendersize", icon='RENDER_REGION')
                layout.operator("sequencer.images_separate", icon='SEPARATE')
            elif strip_type == 'TEXT':
                layout.separator()
                layout.menu("SEQUENCER_MT_strip_effect")
            elif strip_type == 'META':
                layout.separator()
                layout.operator("sequencer.meta_make", icon='ADD_METASTRIP')
                layout.operator("sequencer.meta_separate", icon='REMOVE_METASTRIP')
                layout.operator("sequencer.meta_toggle", text="Toggle Meta", icon='TOGGLE_META')
            if strip_type != 'META':
                layout.separator()
                layout.operator("sequencer.meta_make", icon='ADD_METASTRIP')
                layout.operator("sequencer.meta_toggle", text="Toggle Meta", icon='TOGGLE_META')

        layout.separator()
        layout.menu("SEQUENCER_MT_strip_lock_mute")

        layout.separator()
        layout.menu("SEQUENCER_MT_strip_input")


class SEQUENCER_MT_context_menu(Menu):
    bl_label = "Sequencer Context Menu"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.operator("sequencer.split", text="Split", icon='CUT').type = 'SOFT'

        layout.separator()

        layout.operator("sequencer.copy", text="Copy", icon='COPYDOWN')
        layout.operator("sequencer.paste", text="Paste", icon='PASTEDOWN')
        layout.operator("sequencer.duplicate_move", icon='DUPLICATE')
        props = layout.operator("wm.call_panel", text="Rename", icon = "RENAME")
        props.name = "TOPBAR_PT_name"
        props.keep_open = False
        layout.operator("sequencer.delete", text="Delete", icon='DELETE')

        layout.separator()

        layout.operator("sequencer.slip", text="Slip Strip Contents", icon = "SEQ_SLIP_CONTENTS")
        layout.operator("sequencer.snap", icon = "SEQ_SNAP_STRIP")

        layout.separator()

        layout.operator("sequencer.set_range_to_strips", text="Set Preview Range to Strips", icon = "PREVIEW_RANGE").preview = True

        layout.separator()

        layout.operator("sequencer.gap_remove", icon = "SEQ_REMOVE_GAPS").all = False
        layout.operator("sequencer.gap_insert", icon = "SEQ_INSERT_GAPS")

        layout.separator()

        strip = act_strip(context)

        if strip:
            strip_type = strip.type
            selected_sequences_count = selected_sequences_len(context)

            if strip_type != 'SOUND':
                layout.separator()
                layout.operator_menu_enum("sequencer.strip_modifier_add", "type", text="Add Modifier")
                layout.operator("sequencer.strip_modifier_copy", text="Copy Modifiers to Selection", icon='COPYDOWN')

                if selected_sequences_count >= 2:
                    layout.separator()
                    col = layout.column()
                    col.menu("SEQUENCER_MT_add_transitions", text="Add Transition")

            elif selected_sequences_count >= 2:
                layout.separator()
                layout.operator("sequencer.crossfade_sounds", text="Crossfade Sounds", icon='SPEAKER')

            if selected_sequences_count >= 1:
                col = layout.column()
                col.operator_menu_enum("sequencer.fades_add", "type", text="Fade")
                layout.operator("sequencer.fades_clear", text="Clear Fade", icon="CLEAR")

            if strip_type in {
                    'CROSS', 'ADD', 'SUBTRACT', 'ALPHA_OVER', 'ALPHA_UNDER',
                    'GAMMA_CROSS', 'MULTIPLY', 'OVER_DROP', 'WIPE', 'GLOW',
                    'TRANSFORM', 'COLOR', 'SPEED', 'MULTICAM', 'ADJUSTMENT',
                    'GAUSSIAN_BLUR',
            }:
                layout.separator()
                layout.menu("SEQUENCER_MT_strip_effect")
            elif strip_type == 'MOVIE':
                layout.separator()
                layout.menu("SEQUENCER_MT_strip_movie")
            elif strip_type == 'IMAGE':
                layout.separator()
                layout.operator("sequencer.rendersize", icon='RENDER_REGION')
                layout.operator("sequencer.images_separate", icon='SEPARATE')
            elif strip_type == 'TEXT':
                layout.separator()
                layout.menu("SEQUENCER_MT_strip_effect")
            elif strip_type == 'META':
                layout.separator()
                layout.operator("sequencer.meta_make", icon='ADD_METASTRIP')
                layout.operator("sequencer.meta_separate", icon='REMOVE_METASTRIP')
                layout.operator("sequencer.meta_toggle", text="Toggle Meta", icon='TOGGLE_META')
            if strip_type != 'META':
                layout.separator()
                layout.operator("sequencer.meta_make", icon='ADD_METASTRIP')
                layout.operator("sequencer.meta_toggle", text="Toggle Meta", icon='TOGGLE_META')

        layout.separator()

        layout.menu("SEQUENCER_MT_strip_lock_mute")


class SequencerButtonsPanel:
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'

    @staticmethod
    def has_sequencer(context):
        return (context.space_data.view_type in {'SEQUENCER', 'SEQUENCER_PREVIEW'})

    @classmethod
    def poll(cls, context):
        return cls.has_sequencer(context) and (act_strip(context) is not None)


class SequencerButtonsPanel_Output:
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'

    @staticmethod
    def has_preview(context):
        st = context.space_data
        return (st.view_type in {'PREVIEW', 'SEQUENCER_PREVIEW'}) or st.show_backdrop

    @classmethod
    def poll(cls, context):
        return cls.has_preview(context)


class SEQUENCER_PT_strip(SequencerButtonsPanel, Panel):
    bl_label = ""
    bl_options = {'HIDE_HEADER'}
    bl_category = "Strip"

    def draw(self, context):
        layout = self.layout
        strip = act_strip(context)
        strip_type = strip.type

        if strip_type in {
                'ADD', 'SUBTRACT', 'ALPHA_OVER', 'ALPHA_UNDER', 'MULTIPLY',
                'OVER_DROP', 'GLOW', 'TRANSFORM', 'SPEED', 'MULTICAM',
                'GAUSSIAN_BLUR', 'COLORMIX',
        }:
            icon_header = 'SHADERFX'
        elif strip_type in {
                'CROSS', 'GAMMA_CROSS', 'WIPE',
        }:
            icon_header = 'ARROW_LEFTRIGHT'
        elif strip_type == 'SCENE':
            icon_header = 'SCENE_DATA'
        elif strip_type == 'MOVIECLIP':
            icon_header = 'TRACKER'
        elif strip_type == 'MASK':
            icon_header = 'MOD_MASK'
        elif strip_type == 'MOVIE':
            icon_header = 'FILE_MOVIE'
        elif strip_type == 'SOUND':
            icon_header = 'FILE_SOUND'
        elif strip_type == 'IMAGE':
            icon_header = 'FILE_IMAGE'
        elif strip_type == 'COLOR':
            icon_header = 'COLOR'
        elif strip_type == 'TEXT':
            icon_header = 'FONT_DATA'
        elif strip_type == 'ADJUSTMENT':
            icon_header = 'COLOR'
        elif strip_type == 'META':
            icon_header = 'SEQ_STRIP_META'
        else:
            icon_header = 'SEQ_SEQUENCER'

        row = layout.row()
        row.label(text="", icon=icon_header)
        row.prop(strip, "name", text="")
        row.prop(strip, "mute", toggle=True, icon_only=True, emboss=False)


class SEQUENCER_PT_adjust_crop(SequencerButtonsPanel, Panel):
    bl_label = "Crop"
    bl_options = {'DEFAULT_CLOSED'}
    bl_category = "Strip"

    @classmethod
    def poll(cls, context):
        if not cls.has_sequencer(context):
            return False

        strip = act_strip(context)
        if not strip:
            return False

        strip = act_strip(context)
        return strip.type != 'SOUND'

    def draw(self, context):
        strip = act_strip(context)
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

        strip = act_strip(context)
        if not strip:
            return False

        return strip.type in {
            'ADD', 'SUBTRACT', 'ALPHA_OVER', 'ALPHA_UNDER',
            'CROSS', 'GAMMA_CROSS', 'MULTIPLY', 'OVER_DROP',
            'WIPE', 'GLOW', 'TRANSFORM', 'COLOR', 'SPEED',
            'MULTICAM', 'GAUSSIAN_BLUR', 'TEXT', 'COLORMIX'
        }

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        strip = act_strip(context)

        layout.active = not strip.mute

        if strip.input_count > 0:
            col = layout.column()
            row = col.row()
            row.prop(strip, "input_1")

            if strip.input_count > 1:
                row.operator("sequencer.swap_inputs", text="", icon='SORT_ASC')
                row = col.row()
                row.prop(strip, "input_2")
                row.operator("sequencer.swap_inputs", text="", icon='SORT_DESC')

        strip_type = strip.type

        if strip_type == 'COLOR':
            layout.template_color_picker(strip, "color", value_slider=True, cubic=True)
            layout.prop(strip, "color", text="")

        elif strip_type == 'WIPE':
            col = layout.column()
            col.prop(strip, "transition_type")
            col.alignment = 'RIGHT'
            col.row().prop(strip, "direction", expand=True)

            col = layout.column()
            col.prop(strip, "blur_width", slider=True)
            if strip.transition_type in {'SINGLE', 'DOUBLE'}:
                col.prop(strip, "angle")

        elif strip_type == 'GLOW':
            flow = layout.column_flow()
            flow.prop(strip, "threshold", slider=True)
            flow.prop(strip, "clamp", slider=True)
            flow.prop(strip, "boost_factor")
            flow.prop(strip, "blur_radius")
            flow.prop(strip, "quality", slider=True)
            flow.use_property_split = False
            flow.prop(strip, "use_only_boost")

        elif strip_type == 'SPEED':
            layout.use_property_split = False
            layout.prop(strip, "use_default_fade", text="Stretch to Input Strip Length")
            layout.use_property_split = True
            if not strip.use_default_fade:
                layout.use_property_split = False
                layout.prop(strip, "use_as_speed")
                layout.use_property_split = True
                if strip.use_as_speed:
                    layout.prop(strip, "speed_factor")
                else:
                    layout.prop(strip, "speed_factor", text="Frame Number")
                    layout.use_property_split = False
                    layout.prop(strip, "use_scale_to_length")

        elif strip_type == 'TRANSFORM':
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

        elif strip_type == 'MULTICAM':
            col = layout.column(align=True)
            strip_channel = strip.channel

            col.prop(strip, "multicam_source", text="Source Channel")

            # The multicam strip needs at least 2 strips to be useful
            if strip_channel > 2:
                BT_ROW = 4
                col.label(text="Cut to")
                row = col.row()

                for i in range(1, strip_channel):
                    if (i % BT_ROW) == 1:
                        row = col.row(align=True)

                    # Workaround - .enabled has to have a separate UI block to work
                    if i == strip.multicam_source:
                        sub = row.row(align=True)
                        sub.enabled = False
                        sub.operator("sequencer.split_multicam", text="%d" % i).camera = i
                    else:
                        sub_1 = row.row(align=True)
                        sub_1.enabled = True
                        sub_1.operator("sequencer.split_multicam", text="%d" % i).camera = i

                if strip.channel > BT_ROW and (strip_channel - 1) % BT_ROW:
                    for i in range(strip.channel, strip_channel + ((BT_ROW + 1 - strip_channel) % BT_ROW)):
                        row.label(text="")
            else:
                col.separator()
                col.label(text="Two or more channels are needed below this strip", icon='INFO')

        elif strip_type == 'TEXT':
            layout = self.layout
            col = layout.column()
            col.scale_x = 1.3
            col.scale_y = 1.3
            col.use_property_split = False
            col.prop(strip, "text", text="")
            col.use_property_split = True
            layout.prop(strip, "wrap_width", text="Wrap Width")

        col = layout.column(align=True)
        if strip_type == 'SPEED':
            col.use_property_split = True
            col.prop(strip, "multiply_speed")
            col.use_property_split = False
            col.prop(strip, "use_frame_interpolate")

        elif strip_type in {'CROSS', 'GAMMA_CROSS', 'WIPE', 'ALPHA_OVER', 'ALPHA_UNDER', 'OVER_DROP'}:
            col.use_property_split = False
            col.prop(strip, "use_default_fade", text="Default Fade")
            col.use_property_split = True
            if not strip.use_default_fade:
                col.prop(strip, "effect_fader", text="Effect Fader")
        elif strip_type == 'GAUSSIAN_BLUR':
            col = layout.column(align=True)
            col.prop(strip, "size_x", text="Size X")
            col.prop(strip, "size_y", text="Y")
        elif strip_type == 'COLORMIX':
            layout.prop(strip, "blend_effect", text="Blend Mode")
            row = layout.row(align=True)
            row.prop(strip, "factor", slider=True)


class SEQUENCER_PT_effect_text_layout(SequencerButtonsPanel, Panel):
    bl_label = "Layout"
    bl_parent_id = "SEQUENCER_PT_effect"
    bl_category = "Strip"

    @classmethod
    def poll(cls, context):
        strip = act_strip(context)
        return strip.type == 'TEXT'

    def draw(self, context):
        strip = act_strip(context)
        layout = self.layout
        layout.use_property_split = True
        col = layout.column()
        col.prop(strip, "location", text="Location")
        col.prop(strip, "align_x", text="Anchor X")
        col.prop(strip, "align_y", text="Y")


class SEQUENCER_PT_effect_text_style(SequencerButtonsPanel, Panel):
    bl_label = "Style"
    bl_parent_id = "SEQUENCER_PT_effect"
    bl_category = "Strip"

    @classmethod
    def poll(cls, context):
        strip = act_strip(context)
        return strip.type == 'TEXT'

    def draw(self, context):
        strip = act_strip(context)
        layout = self.layout
        layout.use_property_split = True
        col = layout.column()
        col.template_ID(strip, "font", open="font.open", unlink="font.unlink")

        col = layout.column()
        split = col.split(factor=.4, align=True)
        split.label(text="Size")
        split.prop(strip, "font_size", text="")

        split = col.split(factor=.4, align=True)
        split.label(text="Color")
        split.prop(strip, "color", text="")

        split = col.split(factor=.4, align=True)
        row = split.row()
        row.use_property_decorate = False
        row.use_property_split = False
        row = row.prop(strip, "use_shadow", text="Shadow")
        if (strip.use_shadow and (not strip.mute)):
            split.prop(strip, "shadow_color", text="")
        else:
            split.label(icon='DISCLOSURE_TRI_RIGHT')

        split = col.split(factor=.4, align=True)
        col = split.column(align=True)
        col.use_property_decorate = False
        col.use_property_split = False
        col.prop(strip, "use_box", text="Box")

        sub = split.column()
        if (strip.use_box and (not strip.mute)):
            sub.prop(strip, "box_color", text="")
            row = col.row()
            row.separator()
            row.label(text="Box Margin")
            sub.prop(strip, "box_margin", text="")
        else:
            sub.label(icon='DISCLOSURE_TRI_RIGHT')


class SEQUENCER_PT_source(SequencerButtonsPanel, Panel):
    bl_label = "Source"
    bl_options = {'DEFAULT_CLOSED'}
    bl_category = "Strip"

    @classmethod
    def poll(cls, context):
        if not cls.has_sequencer(context):
            return False

        strip = act_strip(context)
        if not strip:
            return False

        return strip.type in {'MOVIE', 'IMAGE', 'SOUND'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        scene = context.scene
        strip = act_strip(context)
        strip_type = strip.type

        layout.active = not strip.mute

        # Draw a filename if we have one.
        if strip_type == 'SOUND':
            sound = strip.sound
            layout.template_ID(strip, "sound", open="sound.open")
            if sound is not None:

                col = layout.column()
                col.prop(sound, "filepath", text="")

                col.alignment = 'RIGHT'
                sub = col.column(align=True)
                split = sub.split(factor=0.5, align=True)
                split.alignment = 'RIGHT'
                if sound.packed_file:
                    split.label(text="Unpack")
                    split.operator("sound.unpack", icon='PACKAGE', text="")
                else:
                    split.label(text="Pack")
                    split.operator("sound.pack", icon='UGLYPACKAGE', text="")

                layout.use_property_split = False
                layout.prop(sound, "use_memory_cache")
        else:
            if strip_type == 'IMAGE':
                col = layout.column()
                col.prop(strip, "directory", text="")

                # Current element for the filename.
                elem = strip.strip_elem_from_frame(scene.frame_current)
                if elem:
                    col.prop(elem, "filename", text="")  # strip.elements[0] could be a fallback

                col.prop(strip.colorspace_settings, "name", text="Color Space")

                col.prop(strip, "alpha_mode", text="Alpha")
                sub = col.column(align=True)
                sub.operator("sequencer.change_path", text="Change Data/Files", icon='FILEBROWSER').filter_image = True
            else:  # elif strip_type == 'MOVIE':
                elem = strip.elements[0]

                col = layout.column()
                col.prop(strip, "filepath", text="")
                col.prop(strip.colorspace_settings, "name", text="Color Space")
                col.prop(strip, "mpeg_preseek")
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
            box.active = strip.views_format == 'STEREO_3D'
            box.template_image_stereo_3d(strip.stereo_3d_format)

            # Resolution.
            col = layout.column(align=True)
            col = col.box()
            split = col.split(factor=0.5, align=False)
            split.alignment = 'RIGHT'
            split.label(text="Resolution")
            size = (elem.orig_width, elem.orig_height) if elem else (0, 0)
            if size[0] and size[1]:
                split.alignment = 'LEFT'
                split.label(text="%dx%d" % size, translate=False)
            else:
                split.label(text="None")


class SEQUENCER_PT_sound(SequencerButtonsPanel, Panel):
    bl_label = "Sound"
    bl_parent_id = ""
    bl_category = "Strip"

    @classmethod
    def poll(cls, context):
        if not cls.has_sequencer(context):
            return False

        strip = act_strip(context)
        if not strip:
            return False

        return (strip.type == 'SOUND')

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        strip = act_strip(context)
        sound = strip.sound

        layout.active = not strip.mute

        layout.template_ID(strip, "sound", open="sound.open")
        if sound is not None:
            layout.prop(sound, "filepath", text="")

            layout.use_property_split = True
            layout.use_property_decorate = False

            layout.alignment = 'RIGHT'
            sub = layout.column(align=True)
            split = sub.split(factor=0.5, align=True)
            split.alignment = 'RIGHT'
            if sound.packed_file:
                split.label(text="Unpack")
                split.operator("sound.unpack", icon='PACKAGE', text="")
            else:
                split.label(text="Pack")
                split.operator("sound.pack", icon='UGLYPACKAGE', text="")

            layout.prop(sound, "use_memory_cache")


class SEQUENCER_PT_scene(SequencerButtonsPanel, Panel):
    bl_label = "Scene"
    bl_category = "Strip"

    @classmethod
    def poll(cls, context):
        if not cls.has_sequencer(context):
            return False

        strip = act_strip(context)
        if not strip:
            return False

        return (strip.type == 'SCENE')

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        strip = act_strip(context)

        layout.active = not strip.mute

        layout.template_ID(strip, "scene")

        scene = strip.scene
        layout.prop(strip, "scene_input")

        if scene:
            layout.prop(scene, "audio_volume", text="Volume")

        if strip.scene_input == 'CAMERA':
            layout.alignment = 'RIGHT'
            sub = layout.column(align=True)
            split = sub.split(factor=0.5, align=True)
            split.alignment = 'RIGHT'
            split.label(text="Camera")
            split.template_ID(strip, "scene_camera")

            layout.use_property_split = False

            layout.prop(strip, "use_grease_pencil", text="Show Grease Pencil")

            if scene:
                # Warning, this is not a good convention to follow.
                # Expose here because setting the alpha from the 'Render' menu is very inconvenient.
                # layout.label(text="Preview")
                layout.prop(scene.render, "film_transparent")


class SEQUENCER_PT_mask(SequencerButtonsPanel, Panel):
    bl_label = "Mask"
    bl_category = "Strip"

    @classmethod
    def poll(cls, context):
        if not cls.has_sequencer(context):
            return False

        strip = act_strip(context)
        if not strip:
            return False

        return (strip.type == 'MASK')

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        strip = act_strip(context)

        layout.active = not strip.mute

        layout.template_ID(strip, "mask")

        mask = strip.mask

        if mask:
            sta = mask.frame_start
            end = mask.frame_end
            layout.label(text=iface_("Original frame range: %d-%d (%d)") % (sta, end, end - sta + 1), translate=False)


class SEQUENCER_PT_time(SequencerButtonsPanel, Panel):
    bl_label = "Time"
    bl_options = {'DEFAULT_CLOSED'}
    bl_category = "Strip"

    @classmethod
    def poll(cls, context):
        if not cls.has_sequencer(context):
            return False

        strip = act_strip(context)
        if not strip:
            return False

        return strip.type

    def draw_header_preset(self, context):
        layout = self.layout
        layout.alignment = 'RIGHT'
        strip = act_strip(context)

        layout.prop(strip, "lock", text="", icon_only=True, emboss=False)

    def draw(self, context):
        from bpy.utils import smpte_from_frame

        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False

        scene = context.scene
        frame_current = scene.frame_current
        strip = act_strip(context)

        is_effect = isinstance(strip, bpy.types.EffectSequence)

        # Get once.
        frame_start = strip.frame_start
        frame_final_start = strip.frame_final_start
        frame_final_end = strip.frame_final_end
        frame_final_duration = strip.frame_final_duration
        frame_offset_start = strip.frame_offset_start
        frame_offset_end = strip.frame_offset_end

        length_list = (
            str(frame_start),
            str(frame_final_end),
            str(frame_final_duration),
            str(frame_offset_start),
            str(frame_offset_end),
        )

        if not is_effect:
            length_list = length_list + (
                str(strip.animation_offset_start),
                str(strip.animation_offset_end),
            )

        max_length = max(len(x) for x in length_list)
        max_factor = (1.9 - max_length) / 30

        layout.enabled = not strip.lock
        layout.active = not strip.mute

        sub = layout.row(align=True)
        split = sub.split(factor=0.5 + max_factor)
        split.alignment = 'RIGHT'
        split.label(text="Channel")
        split.prop(strip, "channel", text="")

        sub = layout.column(align=True)
        split = sub.split(factor=0.5 + max_factor, align=True)
        split.alignment = 'RIGHT'
        split.label(text="Start")
        split.prop(strip, "frame_start", text=smpte_from_frame(frame_start))

        split = sub.split(factor=0.5 + max_factor, align=True)
        split.alignment = 'RIGHT'
        split.label(text="Duration")
        split.prop(strip, "frame_final_duration", text=smpte_from_frame(frame_final_duration))

        # Use label, editing this value from the UI allows negative values,
        # users can adjust duration.
        split = sub.split(factor=0.5 + max_factor, align=True)
        split.alignment = 'RIGHT'
        split.label(text="End")
        split = split.split(factor=0.8 + max_factor, align=True)
        split.label(text="%14s" % smpte_from_frame(frame_final_end))
        split.alignment = 'RIGHT'
        split.label(text=str(frame_final_end) + " ")

        if not is_effect:

            layout.alignment = 'RIGHT'
            sub = layout.column(align=True)

            split = sub.split(factor=0.5 + max_factor, align=True)
            split.alignment = 'RIGHT'
            split.label(text="Strip Offset Start")
            split.prop(strip, "frame_offset_start", text=smpte_from_frame(frame_offset_start))

            split = sub.split(factor=0.5 + max_factor, align=True)
            split.alignment = 'RIGHT'
            split.label(text="End")
            split.prop(strip, "frame_offset_end", text=smpte_from_frame(frame_offset_end))

            layout.alignment = 'RIGHT'
            sub = layout.column(align=True)

            split = sub.split(factor=0.5 + max_factor, align=True)
            split.alignment = 'RIGHT'
            split.label(text="Hold Offset Start")
            split.prop(strip, "animation_offset_start", text=smpte_from_frame(strip.animation_offset_start))

            split = sub.split(factor=0.5 + max_factor, align=True)
            split.alignment = 'RIGHT'
            split.label(text="End")
            split.prop(strip, "animation_offset_end", text=smpte_from_frame(strip.animation_offset_end))

        col = layout.column(align=True)
        col = col.box()
        col.active = (
            (frame_current >= frame_final_start) and
            (frame_current <= frame_final_start + frame_final_duration)
        )

        split = col.split(factor=0.5 + max_factor, align=True)
        split.alignment = 'RIGHT'
        split.label(text="Current Frame")
        split = split.split(factor=0.8 + max_factor, align=True)
        frame_display = frame_current - frame_final_start
        split.label(text="%14s" % smpte_from_frame(frame_display))
        split.alignment = 'RIGHT'
        split.label(text=str(frame_display) + " ")

        if strip.type == 'SCENE':
            scene = strip.scene

            if scene:
                sta = scene.frame_start
                end = scene.frame_end
                split = col.split(factor=0.5 + max_factor)
                split.alignment = 'RIGHT'
                split.label(text="Original Frame Range")
                split.alignment = 'LEFT'
                split.label(text="%d-%d (%d)" % (sta, end, end - sta + 1), translate=False)


class SEQUENCER_PT_adjust_sound(SequencerButtonsPanel, Panel):
    bl_label = "Sound"
    bl_category = "Strip"

    @classmethod
    def poll(cls, context):
        if not cls.has_sequencer(context):
            return False

        strip = act_strip(context)
        if not strip:
            return False

        strip = act_strip(context)
        return strip.type == 'SOUND'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        st = context.space_data
        strip = act_strip(context)
        sound = strip.sound

        layout.active = not strip.mute

        col = layout.column()

        col.prop(strip, "volume", text="Volume")
        col.prop(strip, "pitch")

        col = layout.column()
        col.prop(strip, "pan")
        col.enabled = sound is not None and sound.use_mono

        if sound is not None:
            col = layout.column()
            if st.waveform_display_type == 'DEFAULT_WAVEFORMS':
                row = col.row()
                row.use_property_split = False
                row.prop(strip, "show_waveform")
                row.prop_decorator(strip, "show_waveform")
            col.use_property_split = False
            col.prop(sound, "use_mono")


class SEQUENCER_PT_adjust_comp(SequencerButtonsPanel, Panel):
    bl_label = "Compositing"
    bl_category = "Strip"

    @classmethod
    def poll(cls, context):
        if not cls.has_sequencer(context):
            return False

        strip = act_strip(context)
        if not strip:
            return False

        strip = act_strip(context)
        return strip.type != 'SOUND'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        strip = act_strip(context)

        layout.active = not strip.mute

        col = layout.column()
        col.prop(strip, "blend_type", text="Blend")
        col.prop(strip, "blend_alpha", text="Opacity", slider=True)


class SEQUENCER_PT_adjust_transform(SequencerButtonsPanel, Panel):
    bl_label = "Transform"
    bl_category = "Strip"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if not cls.has_sequencer(context):
            return False

        strip = act_strip(context)
        if not strip:
            return False

        strip = act_strip(context)
        return strip.type != 'SOUND'

    def draw(self, context):
        strip = act_strip(context)
        layout = self.layout
        layout.use_property_split = True
        layout.active = not strip.mute

        col = layout.column(align=True)
        col.prop(strip.transform, "offset_x", text="Position X")
        col.prop(strip.transform, "offset_y", text="Y")

        col = layout.column(align=True)
        col.prop(strip.transform, "scale_x", text="Scale X")
        col.prop(strip.transform, "scale_y", text="Y")

        col = layout.column(align=True)
        col.prop(strip.transform, "rotation", text="Rotation")

        row = layout.row(heading="Mirror")
        sub = row.row(align=True)
        sub.prop(strip, "use_flip_x", text="X", toggle=True)
        sub.prop(strip, "use_flip_y", text="Y", toggle=True)


class SEQUENCER_PT_adjust_video(SequencerButtonsPanel, Panel):
    bl_label = "Video"
    bl_options = {'DEFAULT_CLOSED'}
    bl_category = "Strip"

    @classmethod
    def poll(cls, context):
        if not cls.has_sequencer(context):
            return False

        strip = act_strip(context)
        if not strip:
            return False

        return strip.type in {
            'MOVIE', 'IMAGE', 'SCENE', 'MOVIECLIP', 'MASK',
            'META', 'ADD', 'SUBTRACT', 'ALPHA_OVER',
            'ALPHA_UNDER', 'CROSS', 'GAMMA_CROSS', 'MULTIPLY',
            'OVER_DROP', 'WIPE', 'GLOW', 'TRANSFORM', 'COLOR',
            'MULTICAM', 'SPEED', 'ADJUSTMENT', 'COLORMIX'
        }

    def draw(self, context):
        layout = self.layout

        layout.use_property_split = True

        col = layout.column()

        strip = act_strip(context)

        layout.active = not strip.mute

        col.prop(strip, "strobe")

        if strip.type == 'MOVIECLIP':
            col = layout.column()
            col.label(text="Tracker")
            col = layout.column(align = True)
            row = col.row()
            row.separator()
            row.use_property_split = False
            row.prop(strip, "stabilize2d")
            row.prop_decorator(strip, "stabilize2d")

            col = layout.column()
            col.label(text="Distortion")
            col = layout.column(align = True)
            row = col.row()
            row.separator()
            row.use_property_split = False
            row.prop(strip, "undistort")
            row.prop_decorator(strip, "undistort")
            col.separator()

        row = col.row()
        row.use_property_split = False
        row.prop(strip, "use_reverse_frames")
        row.prop_decorator(strip, "use_reverse_frames")


class SEQUENCER_PT_adjust_color(SequencerButtonsPanel, Panel):
    bl_label = "Color"
    bl_options = {'DEFAULT_CLOSED'}
    bl_category = "Strip"

    @classmethod
    def poll(cls, context):
        if not cls.has_sequencer(context):
            return False

        strip = act_strip(context)
        if not strip:
            return False

        return strip.type in {
            'MOVIE', 'IMAGE', 'SCENE', 'MOVIECLIP', 'MASK',
            'META', 'ADD', 'SUBTRACT', 'ALPHA_OVER',
            'ALPHA_UNDER', 'CROSS', 'GAMMA_CROSS', 'MULTIPLY',
            'OVER_DROP', 'WIPE', 'GLOW', 'TRANSFORM', 'COLOR',
            'MULTICAM', 'SPEED', 'ADJUSTMENT', 'COLORMIX'
        }

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        strip = act_strip(context)

        layout.active = not strip.mute

        col = layout.column()
        col.prop(strip, "color_saturation", text="Saturation")
        col.prop(strip, "color_multiply", text="Multiply")
        row = col.row()
        row.use_property_split = False
        row.prop(strip, "use_float", text="Convert to Float")
        row.prop_decorator(strip, "use_float")


class SEQUENCER_PT_cache_settings(SequencerButtonsPanel, Panel):
    bl_label = "Cache Settings"
    bl_category = "Proxy & Cache"

    @classmethod
    def poll(cls, context):
        return cls.has_sequencer(context) and context.scene.sequence_editor

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False

        ed = context.scene.sequence_editor

        col = layout.column()


        col.prop(ed, "use_cache_raw")
        col.prop(ed, "use_cache_preprocessed")
        col.prop(ed, "use_cache_composite")
        col.prop(ed, "use_cache_final")


class SEQUENCER_PT_proxy_settings(SequencerButtonsPanel, Panel):
    bl_label = "Proxy Settings"
    bl_category = "Proxy & Cache"

    @classmethod
    def poll(cls, context):
        return cls.has_sequencer(context) and context.scene.sequence_editor

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        ed = context.scene.sequence_editor
        flow = layout.column_flow()
        flow.prop(ed, "proxy_storage", text="Storage")

        if ed.proxy_storage == 'PROJECT':
            flow.prop(ed, "proxy_dir", text="Directory")

        col = layout.column()
        col.operator("sequencer.enable_proxies")
        col.operator("sequencer.rebuild_proxy", icon='LASTOPERATOR')


class SEQUENCER_PT_strip_proxy(SequencerButtonsPanel, Panel):
    bl_label = "Strip Proxy & Timecode"
    bl_category = "Proxy & Cache"

    @classmethod
    def poll(cls, context):
        if not cls.has_sequencer(context) and context.scene.sequence_editor:
            return False

        strip = act_strip(context)
        if not strip:
            return False

        return strip.type in {'MOVIE', 'IMAGE', 'SCENE', 'META', 'MULTICAM'}

    def draw_header(self, context):
        strip = act_strip(context)

        self.layout.prop(strip, "use_proxy", text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False

        ed = context.scene.sequence_editor

        strip = act_strip(context)

        if strip.proxy:
            proxy = strip.proxy

            flow = layout.column_flow()
            if ed.proxy_storage == 'PER_STRIP':
                flow.prop(proxy, "use_proxy_custom_directory")
                flow.prop(proxy, "use_proxy_custom_file")
                flow.use_property_split = True
                if proxy.use_proxy_custom_directory and not proxy.use_proxy_custom_file:
                    flow.prop(proxy, "directory")
                if proxy.use_proxy_custom_file:
                    flow.prop(proxy, "filepath")

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
            col.prop(proxy, "quality", text="Build JPEG Quality")

            if strip.type == 'MOVIE':
                col = layout.column()

                col.prop(proxy, "timecode", text="Timecode Index")


class SEQUENCER_PT_strip_cache(SequencerButtonsPanel, Panel):
    bl_label = "Strip Cache"
    bl_category = "Proxy & Cache"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if not cls.has_sequencer(context):
            return False
        if act_strip(context) is not None:
            return True
        return False

    def draw_header(self, context):
        strip = act_strip(context)
        self.layout.prop(strip, "override_cache_settings", text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False

        strip = act_strip(context)
        layout.active = strip.override_cache_settings

        col = layout.column()
        col.prop(strip, "use_cache_raw")
        col.prop(strip, "use_cache_preprocessed")
        col.prop(strip, "use_cache_composite")


class SEQUENCER_PT_preview(SequencerButtonsPanel_Output, Panel):
    bl_label = "Scene Strip Display"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}
    bl_category = "View"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        render = context.scene.render

        col = layout.column()
        col.prop(render, "sequencer_gl_preview", text="Shading")

        if render.sequencer_gl_preview in {'SOLID', 'WIREFRAME'}:
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
        ed = context.scene.sequence_editor

        col = layout.column()
        col.prop(st, "display_channel", text="Channel")

        if st.display_mode == 'IMAGE':
            col.prop(st, "show_overexposed")

        elif st.display_mode == 'WAVEFORM':
            col.use_property_split = False
            col.prop(st, "show_separate_color")

        col.use_property_split = True
        col.prop(st, "proxy_render_size")

        col.use_property_split = False
        if ed:
            col.prop(ed, "use_prefetch")
        if st.display_mode == 'IMAGE':
            layout.use_property_split = False
            layout.prop(st, "use_zoom_to_fit")


class SEQUENCER_PT_frame_overlay(SequencerButtonsPanel_Output, Panel):
    bl_label = "Frame Overlay"
    bl_category = "View"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if not context.scene.sequence_editor:
            return False
        return SequencerButtonsPanel_Output.poll(context)

    def draw(self, context):
        scene = context.scene
        ed = scene.sequence_editor

        self.layout.prop(ed, "show_overlay", text="")

    def draw_header(self, context):
        scene = context.scene
        ed = scene.sequence_editor

        self.layout.prop(ed, "show_overlay", text="")

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_PREVIEW'
        layout.operator("sequencer.view_ghost_border", text="Set Overlay Region")
        layout.operator_context = 'INVOKE_DEFAULT'

        layout.use_property_split = True
        layout.use_property_decorate = False

        st = context.space_data
        scene = context.scene
        ed = scene.sequence_editor

        layout.active = ed.show_overlay

        col = layout.column()
        col.prop(ed, "overlay_frame", text="Frame Offset")
        col.prop(st, "overlay_type")
        col.use_property_split = False
        col.prop(ed, "use_overlay_lock")


class SEQUENCER_PT_view_safe_areas(SequencerButtonsPanel_Output, Panel):
    bl_label = "Safe Areas"
    bl_options = {'DEFAULT_CLOSED'}
    bl_category = "View"

    @classmethod
    def poll(cls, context):
        st = context.space_data
        is_preview = st.view_type in {'PREVIEW', 'SEQUENCER_PREVIEW'}
        return is_preview and (st.display_mode == 'IMAGE')

    def draw_header(self, context):
        st = context.space_data

        self.layout.prop(st, "show_safe_areas", text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        st = context.space_data
        safe_data = context.scene.safe_areas

        layout.active = st.show_safe_areas

        col = layout.column()

        sub = col.column()
        sub.prop(safe_data, "title", slider=True)
        sub.prop(safe_data, "action", slider=True)


class SEQUENCER_PT_view_safe_areas_center_cut(SequencerButtonsPanel_Output, Panel):
    bl_label = "Center-Cut Safe Areas"
    bl_parent_id = "SEQUENCER_PT_view_safe_areas"
    bl_options = {'DEFAULT_CLOSED'}
    bl_category = "View"

    def draw_header(self, context):
        st = context.space_data

        layout = self.layout
        layout.active = st.show_safe_areas
        layout.prop(st, "show_safe_center", text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        safe_data = context.scene.safe_areas
        st = context.space_data

        layout.active = st.show_safe_areas and st.show_safe_center

        col = layout.column()
        col.prop(safe_data, "title_center", slider=True)


class SEQUENCER_PT_modifiers(SequencerButtonsPanel, Panel):
    bl_label = "Modifiers"
    bl_category = "Modifiers"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        strip = act_strip(context)
        ed = context.scene.sequence_editor

        row = layout.row()
        row.use_property_split = False
        row.prop(strip, "use_linear_modifiers")
        row.prop_decorator(strip, "use_linear_modifiers")

        layout.operator_menu_enum("sequencer.strip_modifier_add", "type")
        layout.operator("sequencer.strip_modifier_copy", icon='COPYDOWN')

        for mod in strip.modifiers:
            box = layout.box()

            row = box.row()
            row.use_property_decorate = False
            row.prop(mod, "show_expanded", text="", emboss=False)
            row.prop(mod, "name", text="")

            row.prop(mod, "mute", text="")
            row.use_property_decorate = True

            sub = row.row(align=True)
            props = sub.operator("sequencer.strip_modifier_move", text="", icon='TRIA_UP')
            props.name = mod.name
            props.direction = 'UP'
            props = sub.operator("sequencer.strip_modifier_move", text="", icon='TRIA_DOWN')
            props.name = mod.name
            props.direction = 'DOWN'

            row.operator("sequencer.strip_modifier_remove", text="", icon='X', emboss=False).name = mod.name

            if mod.show_expanded:
                row = box.row()
                row.prop(mod, "input_mask_type", expand=True)

                if mod.input_mask_type == 'STRIP':
                    sequences_object = ed
                    if ed.meta_stack:
                        sequences_object = ed.meta_stack[-1]
                    box.prop_search(mod, "input_mask_strip", sequences_object, "sequences", text="Mask")
                else:
                    box.prop(mod, "input_mask_id")
                    row = box.row()
                    row.prop(mod, "mask_time", expand=True)

                if mod.type == 'COLOR_BALANCE':
                    box.prop(mod, "color_multiply")
                    draw_color_balance(box, mod.color_balance)
                elif mod.type == 'CURVES':
                    box.template_curve_mapping(mod, "curve_mapping", type='COLOR', show_tone=True)
                elif mod.type == 'HUE_CORRECT':
                    box.template_curve_mapping(mod, "curve_mapping", type='HUE')
                elif mod.type == 'BRIGHT_CONTRAST':
                    col = box.column()
                    col.prop(mod, "bright")
                    col.prop(mod, "contrast")
                elif mod.type == 'WHITE_BALANCE':
                    col = box.column()
                    col.prop(mod, "white_value")
                elif mod.type == 'TONEMAP':
                    col = box.column()
                    col.prop(mod, "tonemap_type")
                    if mod.tonemap_type == 'RD_PHOTORECEPTOR':
                        col.prop(mod, "intensity")
                        col.prop(mod, "contrast")
                        col.prop(mod, "adaptation")
                        col.prop(mod, "correction")
                    elif mod.tonemap_type == 'RH_SIMPLE':
                        col.prop(mod, "key")
                        col.prop(mod, "offset")
                        col.prop(mod, "gamma")


class SEQUENCER_PT_annotation(AnnotationDataPanel, SequencerButtonsPanel_Output, Panel):
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "View"

    @staticmethod
    def has_preview(context):
        st = context.space_data
        return st.view_type in {'PREVIEW', 'SEQUENCER_PREVIEW'}

    @classmethod
    def poll(cls, context):
        return cls.has_preview(context)

    # NOTE: this is just a wrapper around the generic GP Panel
    # But, it should only show up when there are images in the preview region


class SEQUENCER_PT_annotation_onion(AnnotationOnionSkin, SequencerButtonsPanel_Output, Panel):
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "View"

    @staticmethod
    def has_preview(context):
        st = context.space_data
        return st.view_type in {'PREVIEW', 'SEQUENCER_PREVIEW'}

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
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'}
    _context_path = "scene.sequence_editor.active_strip"
    _property_type = (bpy.types.Sequence,)
    bl_category = "Strip"


class SEQUENCER_PT_marker_options(Panel):
    bl_label = "Marker Options"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'View'

    @classmethod
    def poll(cls, context):
        st = context.space_data
        return st.view_type in {'SEQUENCER', 'SEQUENCER_PREVIEW'}

    def draw(self, context):
        layout = self.layout

        tool_settings = context.tool_settings
        st = context.space_data

        col = layout.column(align = True)
        col.prop(tool_settings, "lock_markers")
        col.prop(st, "use_marker_sync")


class SEQUENCER_PT_view_options(bpy.types.Panel):
    bl_label = "View Options"
    bl_category = "View"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'

    def draw(self, context):
        layout = self.layout

        st = context.space_data
        is_preview = st.view_type in {'PREVIEW', 'SEQUENCER_PREVIEW'}
        is_sequencer_view = st.view_type in {'SEQUENCER', 'SEQUENCER_PREVIEW'}

        if is_sequencer_view:

            col = layout.column(align = True)
            if st.view_type == 'SEQUENCER':
                col.prop(st, "show_backdrop", text="Preview as Backdrop")
            col.prop(st, "show_seconds")
            col.prop(st, "show_locked_time")

            layout.menu("SEQUENCER_MT_view_cache")

            layout.separator()

            layout.use_property_split = False
            layout.prop(st, "show_markers")

        if is_preview:
            layout.use_property_split = False
            if st.display_mode == 'IMAGE':
                layout.prop(st, "show_metadata")


classes = (
    ALL_MT_editormenu,
    SEQUENCER_MT_change,
    SEQUENCER_HT_tool_header,
    SEQUENCER_HT_header,
    SEQUENCER_MT_editor_menus,
    SEQUENCER_MT_range,
    SEQUENCER_MT_view,
    SEQUENCER_MT_export,
    SEQUENCER_MT_view_cache,
    SEQUENCER_MT_preview_zoom,
    SEQUENCER_MT_proxy,
    SEQUENCER_MT_select_handle,
    SEQUENCER_MT_select_channel,
    SEQUENCER_MT_select_linked,
    SEQUENCER_MT_select,
    SEQUENCER_MT_select_none,
    SEQUENCER_MT_select_inverse,
    SEQUENCER_MT_marker,
    SEQUENCER_MT_navigation,
    SEQUENCER_MT_add,
    SEQUENCER_MT_add_effect,
    SEQUENCER_MT_add_transitions,
    SEQUENCER_MT_add_empty,
    SEQUENCER_MT_strip_effect,
    SEQUENCER_MT_strip_movie,
    SEQUENCER_MT_strip,
    SEQUENCER_MT_strip_image_transform,
    SEQUENCER_MT_strip_transform,
    SEQUENCER_MT_strip_input,
    SEQUENCER_MT_strip_lock_mute,
    SEQUENCER_MT_context_menu,

    SEQUENCER_PT_active_tool,
    SEQUENCER_PT_strip,

    SEQUENCER_PT_overlay,
    SEQUENCER_PT_preview_overlay,
    SEQUENCER_PT_sequencer_overlay,

    SEQUENCER_PT_effect,
    SEQUENCER_PT_scene,
    SEQUENCER_PT_mask,
    SEQUENCER_PT_effect_text_style,
    SEQUENCER_PT_effect_text_layout,

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
    SEQUENCER_PT_strip_cache,
    SEQUENCER_PT_proxy_settings,
    SEQUENCER_PT_strip_proxy,

    SEQUENCER_PT_custom_props,

    SEQUENCER_PT_view,
    SEQUENCER_PT_frame_overlay,
    SEQUENCER_PT_view_safe_areas,
    SEQUENCER_PT_view_safe_areas_center_cut,
    SEQUENCER_PT_preview,

    SEQUENCER_PT_annotation,
    SEQUENCER_PT_annotation_onion,

#BFA

    SEQUENCER_PT_marker_options,
    SEQUENCER_PT_view_options
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
