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

from bl_ui.properties_grease_pencil_common import (
    GreasePencilLayerMasksPanel,
    GreasePencilLayerTransformPanel,
    GreasePencilLayerAdjustmentsPanel,
    GreasePencilLayerRelationsPanel,
    GreasePencilLayerDisplayPanel,
)

#######################################
# DopeSheet Filtering - Header Buttons

# used for DopeSheet, NLA, and Graph Editors


def dopesheet_filter(layout, context):
    dopesheet = context.space_data.dopesheet
    is_nla = context.area.type == 'NLA_EDITOR'

    row = layout.row(align=True)
    row.prop(dopesheet, "show_only_selected", text="")
    row.prop(dopesheet, "show_hidden", text="")

    if is_nla:
        row.prop(dopesheet, "show_missing_nla", text="")
    else:  # graph and dopesheet editors - F-Curves and drivers only
        row.prop(dopesheet, "show_only_errors", text="")


#######################################
# Dopesheet Filtering Popovers

# Generic Layout - Used as base for filtering popovers used in all animation editors
# Used for DopeSheet, NLA, and Graph Editors


class DopesheetFilterPopoverBase:
    bl_region_type = 'HEADER'
    bl_label = "Filters"

    # Generic = Affects all datatypes
    # XXX: Perhaps we want these to stay in the header instead, for easy/fast access
    @classmethod
    def draw_generic_filters(cls, context, layout):
        dopesheet = context.space_data.dopesheet
        is_nla = context.area.type == 'NLA_EDITOR'

        col = layout.column(align=True)
        col.prop(dopesheet, "show_only_selected", icon='NONE')
        col.prop(dopesheet, "show_hidden", icon='NONE')

        if is_nla:
            col.prop(dopesheet, "show_missing_nla", icon='NONE')
        else:  # graph and dopesheet editors - F-Curves and drivers only
            col.prop(dopesheet, "show_only_errors", icon='NONE')

    # Name/Membership Filters
    # XXX: Perhaps these should just stay in the headers (exclusively)?
    @classmethod
    def draw_search_filters(cls, context, layout, generic_filters_only=False):
        dopesheet = context.space_data.dopesheet

        if (not generic_filters_only) and bpy.data.collections:
            col = layout.column(align=True)
            col.label(text="Filter by Collection:")
            # col.separator()
            row = col.row()
            row.separator()
            row.prop(dopesheet, "filter_collection", text="")

    # Standard = Present in all panels
    @classmethod
    def draw_standard_filters(cls, context, layout):
        dopesheet = context.space_data.dopesheet

        # datablock filters
        layout.label(text="Filter by Type:")
        flow = layout.grid_flow(row_major=True, columns=2,
                                even_rows=False, align=False)

        flow.prop(dopesheet, "show_scenes", text="Scenes")
        flow.prop(dopesheet, "show_nodes", text="Node Trees")

        # object types
        if bpy.data.armatures:
            flow.prop(dopesheet, "show_armatures", text="Armatures")
        if bpy.data.cameras:
            flow.prop(dopesheet, "show_cameras", text="Cameras")
        if bpy.data.grease_pencils:
            flow.prop(dopesheet, "show_gpencil", text="Grease Pencil Objects")
        if bpy.data.lights:
            flow.prop(dopesheet, "show_lights", text="Lights")
        if bpy.data.meshes:
            flow.prop(dopesheet, "show_meshes", text="Meshes")
        if bpy.data.curves:
            flow.prop(dopesheet, "show_curves", text="Curves")
        if bpy.data.lattices:
            flow.prop(dopesheet, "show_lattices", text="Lattices")
        if bpy.data.metaballs:
            flow.prop(dopesheet, "show_metaballs", text="Metaballs")
        if hasattr(bpy.data, "hairs") and bpy.data.hairs:
            flow.prop(dopesheet, "show_hairs", text="Hairs")
        if hasattr(bpy.data, "pointclouds") and bpy.data.pointclouds:
            flow.prop(dopesheet, "show_pointclouds", text="Point Clouds")
        if bpy.data.volumes:
            flow.prop(dopesheet, "show_volumes", text="Volumes")

        # data types
        flow.prop(dopesheet, "show_worlds", text="Worlds")
        if bpy.data.particles:
            flow.prop(dopesheet, "show_particles", text="Particles")
        if bpy.data.linestyles:
            flow.prop(dopesheet, "show_linestyles", text="Line Styles")
        if bpy.data.speakers:
            flow.prop(dopesheet, "show_speakers", text="Speakers")
        if bpy.data.materials:
            flow.prop(dopesheet, "show_materials", text="Materials")
        if bpy.data.textures:
            flow.prop(dopesheet, "show_textures", text="Textures")
        if bpy.data.shape_keys:
            flow.prop(dopesheet, "show_shapekeys", text="Shape Keys")
        if bpy.data.cache_files:
            flow.prop(dopesheet, "show_cache_files", text="Cache Files")
        if bpy.data.movieclips:
            flow.prop(dopesheet, "show_movieclips", text="Movie Clips")

        layout.separator()

        # Object Data Filters

        # TODO: Add per-channel/axis convenience toggles?
        split = layout.split()

        col = split.column()
        col.prop(dopesheet, "show_transforms", text="Transforms")

        col = split.column()
        col.prop(dopesheet, "show_modifiers", text="Modifiers")

        layout.separator()

        # performance-related options (users will mostly have these enabled)
        col = layout.column(align=True)
        col.label(text="Options:")
        row = col.row()
        row.separator()
        row.prop(dopesheet, "use_datablock_sort", icon='NONE')


# Popover for Dopesheet Editor(s) - Dopesheet, Action, Shapekey, GPencil, Mask, etc.
class DOPESHEET_PT_filters(DopesheetFilterPopoverBase, Panel):
    bl_space_type = 'DOPESHEET_EDITOR'
    bl_region_type = 'HEADER'
    bl_label = "Filters"

    def draw(self, context):
        layout = self.layout

        dopesheet = context.space_data.dopesheet
        ds_mode = context.space_data.mode
        st = context.space_data

        if ds_mode in {'DOPESHEET', 'ACTION', 'GPENCIL'}:
            layout.separator()
            generic_filters_only = ds_mode != 'DOPESHEET'
            DopesheetFilterPopoverBase.draw_search_filters(context, layout,
                                                           generic_filters_only=generic_filters_only)

        if ds_mode == 'DOPESHEET':
            layout.separator()
            DopesheetFilterPopoverBase.draw_standard_filters(context, layout)

            row = layout.row()
            row.separator()
            row.prop(st.dopesheet, "use_multi_word_filter",
                     text="Multi-Word Match Search")


################################ Switch between the editors ##########################################

class ANIM_OT_switch_editors_to_dopesheet(bpy.types.Operator):
    """Switch to Dopesheet Editor"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "wm.switch_editor_to_dopesheet"        # unique identifier for buttons and menu items to reference.
    # display name in the interface.
    bl_label = "Switch to Dopesheet Editor"
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    # execute() is called by blender when running the operator.
    def execute(self, context):
        bpy.ops.wm.context_set_enum(
            data_path="area.ui_type", value="DOPESHEET")
        return {'FINISHED'}


class ANIM_OT_switch_editors_to_graph(bpy.types.Operator):
    """Switch to Graph editor"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "wm.switch_editor_to_graph"        # unique identifier for buttons and menu items to reference.
    # display name in the interface.
    bl_label = "Switch to Graph Editor"
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    # execute() is called by blender when running the operator.
    def execute(self, context):
        # area.ui_type, not area.type. Subeditor ...
        bpy.ops.wm.context_set_enum(data_path="area.ui_type", value="FCURVES")
        return {'FINISHED'}


class ANIM_OT_switch_editors_to_driver(bpy.types.Operator):
    """Switch to Driver editor"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "wm.switch_editor_to_driver"        # unique identifier for buttons and menu items to reference.
    # display name in the interface.
    bl_label = "Switch to Driver Editor"
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    # execute() is called by blender when running the operator.
    def execute(self, context):
        # area.ui_type, not area.type. Subeditor ...
        bpy.ops.wm.context_set_enum(data_path="area.ui_type", value="DRIVERS")
        return {'FINISHED'}


class ANIM_OT_switch_editors_to_nla(bpy.types.Operator):
    """Switch to NLA editor"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "wm.switch_editor_to_nla"        # unique identifier for buttons and menu items to reference.
    bl_label = "Switch to NLA Editor"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    # execute() is called by blender when running the operator.
    def execute(self, context):
        bpy.ops.wm.context_set_enum(data_path="area.type", value="NLA_EDITOR")
        return {'FINISHED'}


# The blank button, we don't want to switch to the editor in which we are already.

class ANIM_OT_switch_editors_in_dopesheet(bpy.types.Operator):
    """You are in Dopesheet Editor"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "wm.switch_editor_in_dopesheet"        # unique identifier for buttons and menu items to reference.
    bl_label = "Dopesheet Editor"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    # Blank button, we don't execute anything here.
    def execute(self, context):
        return {'FINISHED'}


#######################################
# DopeSheet Editor - General/Standard UI

class DOPESHEET_HT_header(Header):
    bl_space_type = 'DOPESHEET_EDITOR'

    def draw(self, context):
        layout = self.layout

        st = context.space_data

        # bfa - show hide the editormenu
        ALL_MT_editormenu.draw_hidden(context, layout)

        if st.mode == 'TIMELINE':
            from bl_ui.space_time import (
                TIME_MT_editor_menus,
                TIME_HT_editor_buttons,
            )
            TIME_MT_editor_menus.draw_collapsible(context, layout)
            TIME_HT_editor_buttons.draw_header(context, layout)
        else:

            # Switch between the editors

            # bfa - The tabs to switch between the four animation editors. The classes are in space_dopesheet.py
            row = layout.row(align=True)

            row.operator("wm.switch_editor_in_dopesheet",
                         text="", icon='DOPESHEET_ACTIVE')
            row.operator("wm.switch_editor_to_graph", text="", icon='GRAPH')
            row.operator("wm.switch_editor_to_driver", text="", icon='DRIVER')
            row.operator("wm.switch_editor_to_nla", text="", icon='NLA')

            ###########################

            layout.prop(st, "ui_mode", text="")

            DOPESHEET_MT_editor_menus.draw_collapsible(context, layout)
            DOPESHEET_HT_editor_buttons.draw_header(context, layout)

# bfa - show hide the editormenu


class ALL_MT_editormenu(Menu):
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):

        row = layout.row(align=True)
        row.template_header()  # editor type menus

# Header for "normal" dopesheet editor modes (e.g. Dope Sheet, Action, Shape Keys, etc.)


class DOPESHEET_HT_editor_buttons:

    @staticmethod
    def draw_header(context, layout):
        st = context.space_data
        tool_settings = context.tool_settings

        dopesheet = context.space_data.dopesheet
        ds_mode = context.space_data.mode
        st = context.space_data

        if st.mode in {'ACTION', 'SHAPEKEY'}:
            # TODO: These buttons need some tidying up -
            # Probably by using a popover, and bypassing the template_id() here
            row = layout.row(align=True)
            row.operator("action.layer_prev", text="", icon='TRIA_DOWN')
            row.operator("action.layer_next", text="", icon='TRIA_UP')

            row = layout.row(align=True)
            row.operator("action.push_down", text="Push Down",
                         icon='NLA_PUSHDOWN')
            row.operator("action.stash", text="Stash", icon='FREEZE')

            layout.separator_spacer()

            layout.template_ID(st, "action", new="action.new", unlink="action.unlink")

        # Layer management
        if st.mode == 'GPENCIL':
            ob = context.active_object
            selected = st.dopesheet.show_only_selected
            enable_but = selected and ob is not None and ob.type == 'GPENCIL'

            row = layout.row(align=True)
            row.enabled = enable_but
            row.operator("gpencil.layer_add", icon='ADD', text="")
            row.operator("gpencil.layer_remove", icon='REMOVE', text="")
            row.menu("GPENCIL_MT_layer_context_menu",
                     icon='DOWNARROW_HLT', text="")

            row = layout.row(align=True)
            row.enabled = enable_but
            row.operator("gpencil.layer_move",
                         icon='TRIA_UP', text="").type = 'UP'
            row.operator("gpencil.layer_move", icon='TRIA_DOWN',
                         text="").type = 'DOWN'

            row = layout.row(align=True)
            row.enabled = enable_but
            row.operator("gpencil.layer_isolate", icon='RESTRICT_VIEW_ON',
                         text="").affect_visibility = True
            row.operator("gpencil.layer_isolate", icon='LOCKED',
                         text="").affect_visibility = False

        layout.separator_spacer()

        layout.prop(dopesheet, "show_summary", text="")

        dopesheet_filter(layout, context)

        if ds_mode in {'DOPESHEET'}:
            layout.popover(panel="DOPESHEET_PT_filters",
                           text="", icon='FILTER')

        # Grease Pencil mode doesn't need snapping, as it's frame-aligned only
        if st.mode != 'GPENCIL':
            layout.prop(st, "auto_snap", text="")

        row = layout.row(align=True)
        row.prop(tool_settings, "use_proportional_action",
                 text="", icon_only=True)
        if tool_settings.use_proportional_action:
            sub = row.row(align=True)
            sub.prop(tool_settings, "proportional_edit_falloff",
                     text="", icon_only=True)

        layout.operator_menu_enum(
            "action.handle_type", "type", text="", icon="HANDLE_AUTO")
        layout.operator_menu_enum(
            "action.interpolation_type", "type", text="", icon="INTERPOLATE")
        layout.operator_menu_enum(
            "action.keyframe_type", "type", text="", icon="SPACE2")
            
        row = layout.row()
        row.popover(panel = "DOPESHEET_PT_view_view_options", text = "Options")


class DOPESHEET_MT_editor_menus(Menu):
    bl_idname = "DOPESHEET_MT_editor_menus"
    bl_label = ""

    def draw(self, context):
        layout = self.layout
        st = context.space_data
        # Quick favourites menu
        layout.menu("SCREEN_MT_user_menu", text="Quick")
        layout.menu("DOPESHEET_MT_view")
        layout.menu("DOPESHEET_MT_select")
        if st.show_markers:
            layout.menu("DOPESHEET_MT_marker")

        if st.mode == 'DOPESHEET' or (st.mode == 'ACTION' and st.action is not None):
            layout.menu("DOPESHEET_MT_channel")
        elif st.mode == 'GPENCIL':
            layout.menu("DOPESHEET_MT_gpencil_channel")

        if st.mode != 'GPENCIL':
            layout.menu("DOPESHEET_MT_key")
        else:
            layout.menu("DOPESHEET_MT_gpencil_key")


class DOPESHEET_MT_view(Menu):
    bl_label = "View"

    def draw(self, context):
        layout = self.layout

        st = context.space_data

        layout.prop(st, "show_region_channels") # bfa - channels
        layout.prop(st, "show_region_ui")

        layout.separator()

        layout.operator("anim.previewrange_set", icon='BORDER_RECT')
        layout.operator("anim.previewrange_clear", icon="CLEAR")
        layout.operator("action.previewrange_set", icon='BORDER_RECT')

        layout.separator()

        layout.operator("view2d.zoom_in", text="Zoom In", icon="ZOOM_IN")
        layout.operator("view2d.zoom_out", text="Zoom Out", icon="ZOOM_OUT")
        layout.operator("view2d.zoom_border", icon="ZOOM_BORDER")

        layout.separator()

        layout.operator("action.view_all", icon="VIEWALL")
        layout.operator("action.view_selected", icon="VIEW_SELECTED")
        layout.operator("action.view_frame", icon="VIEW_FRAME")

        layout.separator()

        layout.menu("INFO_MT_area")
        layout.menu("DOPESHEET_MT_view_pie_menus")


class DOPESHEET_MT_view_pie_menus(Menu):
    bl_label = "Pie menus"

    def draw(self, _context):
        layout = self.layout

        layout.operator("wm.call_menu_pie", text="Snap",
                        icon="MENU_PANEL").name = 'DOPESHEET_MT_snap_pie'


class DOPESHEET_MT_select(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout

        layout.operator("action.select_all", text="All", icon='SELECT_ALL').action = 'SELECT'
        layout.operator("action.select_all", text="None", icon='SELECT_NONE').action = 'DESELECT'
        layout.operator("action.select_all", text="Invert", icon='INVERSE').action = 'INVERT'

        layout.separator()

        layout.operator("action.select_box", icon='BORDER_RECT').axis_range = False
        layout.operator("action.select_box", text="Box Select (Axis Range)", icon='BORDER_RECT').axis_range = True

        layout.operator("action.select_circle", icon='CIRCLE_SELECT')
        layout.operator_menu_enum("action.select_lasso", "mode")

        layout.separator()

        layout.operator("action.select_column", text="Columns on Selected Keys", icon="COLUMNS_KEYS").mode = 'KEYS'
        layout.operator("action.select_column", text="Column on Current Frame", icon="COLUMN_CURRENT_FRAME").mode = 'CFRA'

        layout.operator("action.select_column", text="Columns on Selected Markers", icon="COLUMNS_MARKERS").mode = 'MARKERS_COLUMN'
        layout.operator("action.select_column", text="Between Selected Markers", icon="BETWEEN_MARKERS").mode = 'MARKERS_BETWEEN'

        layout.separator()

        if context.space_data.mode != 'GPENCIL':
            layout.operator("action.select_linked", text="Linked", icon="CONNECTED")

            layout.separator()

        props = layout.operator("action.select_leftright", text="Before Current Frame", icon="BEFORE_CURRENT_FRAME")
        props.extend = False
        props.mode = 'LEFT'
        props = layout.operator("action.select_leftright", text="After Current Frame", icon="AFTER_CURRENT_FRAME")
        props.extend = False
        props.mode = 'RIGHT'

        # FIXME: grease pencil mode isn't supported for these yet, so skip for that mode only
        if context.space_data.mode != 'GPENCIL':
            layout.separator()
            layout.operator("action.select_more", text="More", icon="SELECTMORE")
            layout.operator("action.select_less", text="Less", icon="SELECTLESS")


class DOPESHEET_MT_marker(Menu):
    bl_label = "Marker"

    def draw(self, context):
        layout = self.layout

        from bl_ui.space_time import marker_menu_generic
        marker_menu_generic(layout, context)

        st = context.space_data

        if st.mode in {'ACTION', 'SHAPEKEY'} and st.action:
            layout.separator()
            layout.prop(st, "show_pose_markers")

            if st.show_pose_markers is False:
                layout.operator("action.markers_make_local")


#######################################
# Keyframe Editing


class DOPESHEET_MT_channel(Menu):
    bl_label = "Channel"

    def draw(self, _context):
        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_CHANNELS'

        layout.operator("anim.channels_delete", icon="DELETE")

        layout.separator()

        layout.operator("anim.channels_group", icon="NEW_GROUP")
        layout.operator("anim.channels_ungroup", icon="REMOVE_FROM_ALL_GROUPS")

        layout.separator()

        # bfa - menu comes from space_graph
        layout.menu("GRAPH_MT_channel_settings_toggle")

        layout.separator()

        layout.operator("anim.channels_editable_toggle", icon="LOCKED")
        layout.menu("DOPESHEET_MT_channel_extrapolation")

        layout.separator()

        layout.operator("anim.channels_expand", icon="EXPANDMENU")
        layout.operator("anim.channels_collapse", icon="COLLAPSEMENU")

        layout.separator()

        # bfa - menu comes from space_graph
        layout.menu("GRAPH_MT_channel_move")

        layout.separator()

        layout.operator("anim.channels_fcurves_enable", icon="UNLOCKED")


class DOPESHEET_MT_channel_extrapolation(Menu):
    bl_label = "Extrapolation Mode"

    def draw(self, context):
        layout = self.layout

        layout.operator("action.extrapolation_type", text="Constant Extrapolation",
                        icon="EXTRAPOLATION_CONSTANT").type = 'CONSTANT'
        layout.operator("action.extrapolation_type", text="Linear Extrapolation",
                        icon="EXTRAPOLATION_LINEAR").type = 'LINEAR'
        layout.operator("action.extrapolation_type", text="Make Cyclic (F-Modifier)",
                        icon="EXTRAPOLATION_CYCLIC").type = 'MAKE_CYCLIC'
        layout.operator("action.extrapolation_type", text="Clear Cyclic (F-Modifier)",
                        icon="EXTRAPOLATION_CYCLIC_CLEAR").type = 'CLEAR_CYCLIC'


class DOPESHEET_MT_key(Menu):
    bl_label = "Key"

    def draw(self, _context):
        layout = self.layout

        layout.menu("DOPESHEET_MT_key_transform", text="Transform")
        layout.menu("DOPESHEET_MT_key_snap")
        layout.menu("DOPESHEET_MT_key_mirror")

        layout.separator()

        layout.operator_menu_enum("action.keyframe_insert", "type")

        layout.separator()

        layout.operator("action.frame_jump", icon='JUMP_TO_KEYFRAMES')

        layout.separator()

        layout.operator("action.copy", text="Copy Keyframes", icon='COPYDOWN')
        layout.operator("action.paste", text="Paste Keyframes", icon='PASTEDOWN')
        layout.operator("action.paste", text="Paste Flipped", icon='PASTEFLIPDOWN').flipped = True

        layout.separator()

        layout.operator("action.duplicate_move", icon="DUPLICATE")
        layout.operator("action.delete", icon="DELETE")

        layout.separator()

        layout.operator_menu_enum("action.easing_type", "type", text="Easing Mode")

        layout.separator()

        layout.operator("action.clean", icon="CLEAN_KEYS").channels = False
        layout.operator("action.clean", text = "Clean Channels", icon="CLEAN_CHANNELS").channels = True

        layout.operator("action.sample", icon="SAMPLE_KEYFRAMES")


class DOPESHEET_PT_view_view_options(bpy.types.Panel):
    bl_label = "View Options"
    bl_category = "View"
    bl_space_type = 'DOPESHEET_EDITOR'
    bl_region_type = 'HEADER'

    # dopesheet and timeline is a wild mix. We need to separate them by the following two defs
    @staticmethod
    def in_dopesheet(context):
        return context.space_data.mode != 'TIMELINE'  # dopesheet, not timeline

    @classmethod
    def poll(cls, context):
        # only for dopesheet editor
        return cls.in_dopesheet(context)

    def draw(self, context):
        sc = context.scene
        layout = self.layout
        tool_settings = context.tool_settings
        st = context.space_data

        col = layout.column(align=True)

        col.prop(st, "use_realtime_update")
        col.prop(st, "show_markers")

        col.separator()

        col.prop(st, "show_seconds")
        col.prop(st, "show_locked_time")

        col.separator()

       # Sliders are always shown in the Shape Key Editor regardless of this setting.
        col = col.column(align=True)
        col.active = context.space_data.mode != 'SHAPEKEY'
        col.prop(st, "show_sliders")

        if bpy.app.version < (2, 93):
            col.operator("anim.show_group_colors_deprecated", icon='CHECKBOX_HLT')
        col.prop(st, "show_interpolation")
        col.prop(st, "show_extremes")
        col.prop(st, "use_auto_merge_keyframes")

        col = layout.column(align=True)
        col.prop(tool_settings, "lock_markers")
        col.prop(st, "use_marker_sync")


class DOPESHEET_MT_key_transform(Menu):
    bl_label = "Transform"

    def draw(self, _context):
        layout = self.layout

        layout.operator("transform.transform", text="Grab/Move",
                        icon="TRANSFORM_MOVE").mode = 'TIME_TRANSLATE'
        layout.operator("transform.transform", text="Extend",
                        icon="SHRINK_FATTEN").mode = 'TIME_EXTEND'
        layout.operator("transform.transform", text="Slide",
                        icon="PUSH_PULL").mode = 'TIME_SLIDE'
        layout.operator("transform.transform", text="Scale",
                        icon="TRANSFORM_SCALE").mode = 'TIME_SCALE'


class DOPESHEET_MT_key_mirror(Menu):
    bl_label = "Mirror"

    def draw(self, context):
        layout = self.layout

        layout.operator("action.mirror", text="By Times over Current Frame",
                        icon="MIRROR_TIME").type = 'CFRA'
        layout.operator("action.mirror", text="By Values over Value=0",
                        icon="MIRROR_CURSORVALUE").type = 'XAXIS'
        layout.operator("action.mirror", text="By Times over First Selected Marker",
                        icon="MIRROR_MARKER").type = 'MARKER'


class DOPESHEET_MT_key_snap(Menu):
    bl_label = "Snap"

    def draw(self, context):
        layout = self.layout

        layout.operator("action.snap", text="Current Frame",
                        icon="SNAP_CURRENTFRAME").type = 'CFRA'
        layout.operator("action.snap", text="Nearest Frame",
                        icon="SNAP_NEARESTFRAME").type = 'NEAREST_FRAME'
        layout.operator("action.snap", text="Nearest Second",
                        icon="SNAP_NEARESTSECOND").type = 'NEAREST_SECOND'
        layout.operator("action.snap", text="Nearest Marker",
                        icon="SNAP_NEARESTMARKER").type = 'NEAREST_MARKER'


#######################################
# Grease Pencil Editing

class DOPESHEET_MT_gpencil_channel(Menu):
    bl_label = "Channel"

    def draw(self, _context):
        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_CHANNELS'

        layout.operator("anim.channels_delete", icon="DELETE")

        layout.separator()
        #bfa - menu comes from space_graph.py
        layout.menu("GRAPH_MT_channel_settings_toggle")

        layout.separator()

        layout.operator("anim.channels_editable_toggle", icon="LOCKED")

        # XXX: to be enabled when these are ready for use!
        # layout.separator()
        # layout.operator("anim.channels_expand")
        # layout.operator("anim.channels_collapse")

        layout.separator()
        layout.operator_menu_enum(
            "anim.channels_move", "direction", text="Move...")


class DOPESHEET_MT_gpencil_key(Menu):
    bl_label = "Key"

    def draw(self, _context):
        layout = self.layout

        layout.menu("DOPESHEET_MT_key_transform", text="Transform")
        layout.operator_menu_enum("action.snap", "type", text="Snap")
        layout.operator_menu_enum("action.mirror", "type", text="Mirror")

        layout.separator()

        layout.operator_menu_enum("action.keyframe_insert", "type")

        layout.separator()

        layout.operator("action.delete", icon="DELETE")
        layout.operator("gpencil.interpolate_reverse", icon="DELETE")


class DOPESHEET_MT_delete(Menu):
    bl_label = "Delete"

    def draw(self, _context):
        layout = self.layout

        layout.operator("action.delete")

        layout.separator()

        layout.operator("action.clean").channels = False
        layout.operator("action.clean", text="Clean Channels").channels = True


class DOPESHEET_MT_context_menu(Menu):
    bl_label = "Dope Sheet Context Menu"

    def draw(self, context):
        layout = self.layout
        st = context.space_data

        layout.operator_context = 'INVOKE_DEFAULT'

        layout.operator("action.copy", text="Copy", icon='COPYDOWN')
        layout.operator("action.paste", text="Paste", icon='PASTEDOWN')
        layout.operator("action.paste", text="Paste Flipped",
                        icon='PASTEFLIPDOWN').flipped = True

        layout.separator()

        layout.operator_menu_enum(
            "action.keyframe_type", "type", text="Keyframe Type")
        if st.mode != 'GPENCIL':
            layout.operator_menu_enum("action.handle_type", "type", text="Handle Type")
            layout.operator_menu_enum("action.interpolation_type", "type", text="Interpolation Mode")
            layout.operator_menu_enum("action.easing_type", "type", text="Easing Mode")

        layout.separator()

        layout.operator("action.keyframe_insert", icon='COPYDOWN').type = 'SEL'
        layout.operator("action.duplicate_move", icon='DUPLICATE')

        if st.mode == 'GPENCIL':
            layout.separator()

        layout.operator_context = 'EXEC_REGION_WIN'
        layout.operator("action.delete", icon='DELETE')

        if st.mode == 'GPENCIL':
            layout.operator("gpencil.interpolate_reverse")
            layout.operator("gpencil.frame_clean_duplicate", text="Delete Duplicate Frames")

        layout.separator()

        layout.operator_menu_enum("action.mirror", "type", text="Mirror")
        layout.operator_menu_enum("action.snap", "type", text="Snap")


class DOPESHEET_MT_channel_context_menu(Menu):
    bl_label = "Dope Sheet Channel Context Menu"

    def draw(self, context):
        layout = self.layout

        # This menu is used from the graph editor too.
        is_graph_editor = context.area.type == 'GRAPH_EDITOR'

        layout.operator("anim.channels_setting_enable", text="Mute Channels", icon='MUTE_IPO_ON').type = 'MUTE'
        layout.operator("anim.channels_setting_disable", text="Unmute Channels", icon='MUTE_IPO_OFF').type = 'MUTE'
        layout.separator()
        layout.operator("anim.channels_setting_enable", text="Protect Channels", icon='LOCKED').type = 'PROTECT'
        layout.operator("anim.channels_setting_disable", text="Unprotect Channels", icon='UNLOCKED').type = 'PROTECT'

        layout.separator()
        layout.operator("anim.channels_group", icon='NEW_GROUP')
        layout.operator("anim.channels_ungroup", icon='REMOVE_ALL_GROUPS')

        layout.separator()
        layout.operator("anim.channels_editable_toggle", icon='RESTRICT_SELECT_ON')
        if is_graph_editor:
            operator = "graph.extrapolation_type"
        else:
            operator = "action.extrapolation_type"
        layout.operator_menu_enum(operator, "type", text="Extrapolation Mode")

        layout.separator()
        layout.operator("anim.channels_expand", icon='EXPANDMENU')
        layout.operator("anim.channels_collapse", icon='COLLAPSEMENU')

        layout.separator()
        layout.operator_menu_enum("anim.channels_move", "direction", text="Move...")

        layout.separator()

        layout.operator("anim.channels_delete", icon='DELETE')


class DOPESHEET_MT_snap_pie(Menu):
    bl_label = "Snap"

    def draw(self, _context):
        layout = self.layout
        pie = layout.menu_pie()

        pie.operator(
            "action.snap", text="Selection to Current Frame").type = 'CFRA'
        pie.operator(
            "action.snap", text="Selection to Nearest Frame").type = 'NEAREST_FRAME'
        pie.operator(
            "action.snap", text="Selection to Nearest Second").type = 'NEAREST_SECOND'
        pie.operator(
            "action.snap", text="Selection to Nearest Marker").type = 'NEAREST_MARKER'


class LayersDopeSheetPanel:
    bl_space_type = 'DOPESHEET_EDITOR'
    bl_region_type = 'UI'
    bl_category = "View"

    @classmethod
    def poll(cls, context):
        st = context.space_data
        ob = context.object
        if st.mode != 'GPENCIL' or ob is None or ob.type != 'GPENCIL':
            return False

        gpd = ob.data
        gpl = gpd.layers.active
        if gpl:
            return True

        return False


class DOPESHEET_PT_gpencil_mode(LayersDopeSheetPanel, Panel):
    # bl_space_type = 'DOPESHEET_EDITOR'
    # bl_region_type = 'UI'
    # bl_category = "View"
    bl_label = "Layer"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        ob = context.object
        gpd = ob.data
        gpl = gpd.layers.active
        if gpl:
            row = layout.row(align=True)
            row.prop(gpl, "blend_mode", text="Blend")

            row = layout.row(align=True)
            row.prop(gpl, "opacity", text="Opacity", slider=True)

            col = layout.column(align=True)
            col.use_property_split = False
            col.prop(gpl, "use_lights")
            col.prop(gpd, "use_autolock_layers",
                     text="Autolock Inactive Layers")


class DOPESHEET_PT_gpencil_layer_masks(LayersDopeSheetPanel, GreasePencilLayerMasksPanel, Panel):
    bl_label = "Masks"
    bl_parent_id = 'DOPESHEET_PT_gpencil_mode'
    bl_options = {'DEFAULT_CLOSED'}


class DOPESHEET_PT_gpencil_layer_transform(LayersDopeSheetPanel, GreasePencilLayerTransformPanel, Panel):
    bl_label = "Transform"
    bl_parent_id = 'DOPESHEET_PT_gpencil_mode'
    bl_options = {'DEFAULT_CLOSED'}


class DOPESHEET_PT_gpencil_layer_adjustments(LayersDopeSheetPanel, GreasePencilLayerAdjustmentsPanel, Panel):
    bl_label = "Adjustments"
    bl_parent_id = 'DOPESHEET_PT_gpencil_mode'
    bl_options = {'DEFAULT_CLOSED'}


class DOPESHEET_PT_gpencil_layer_relations(LayersDopeSheetPanel, GreasePencilLayerRelationsPanel, Panel):
    bl_label = "Relations"
    bl_parent_id = 'DOPESHEET_PT_gpencil_mode'
    bl_options = {'DEFAULT_CLOSED'}


class DOPESHEET_PT_gpencil_layer_display(LayersDopeSheetPanel, GreasePencilLayerDisplayPanel, Panel):
    bl_label = "Display"
    bl_parent_id = 'DOPESHEET_PT_gpencil_mode'
    bl_options = {'DEFAULT_CLOSED'}


classes = (
    ALL_MT_editormenu,
    ANIM_OT_switch_editors_to_dopesheet,
    ANIM_OT_switch_editors_to_graph,
    ANIM_OT_switch_editors_to_driver,
    ANIM_OT_switch_editors_to_nla,
    ANIM_OT_switch_editors_in_dopesheet,
    DOPESHEET_HT_header,
    DOPESHEET_MT_editor_menus,
    DOPESHEET_MT_view,
    DOPESHEET_MT_view_pie_menus,
    DOPESHEET_MT_select,
    DOPESHEET_MT_marker,
    DOPESHEET_MT_channel,
    DOPESHEET_MT_channel_extrapolation,
    DOPESHEET_MT_key,
    DOPESHEET_PT_view_view_options,
    DOPESHEET_MT_key_transform,
    DOPESHEET_MT_key_mirror,
    DOPESHEET_MT_key_snap,
    DOPESHEET_MT_gpencil_channel,
    DOPESHEET_MT_gpencil_key,
    DOPESHEET_MT_delete,
    DOPESHEET_MT_context_menu,
    DOPESHEET_MT_channel_context_menu,
    DOPESHEET_MT_snap_pie,
    DOPESHEET_PT_filters,
    DOPESHEET_PT_gpencil_mode,
    DOPESHEET_PT_gpencil_layer_masks,
    DOPESHEET_PT_gpencil_layer_transform,
    DOPESHEET_PT_gpencil_layer_adjustments,
    DOPESHEET_PT_gpencil_layer_relations,
    DOPESHEET_PT_gpencil_layer_display,
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
