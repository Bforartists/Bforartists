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
        is_nla = context.area.type == 'NLA_EDITOR'

        col = layout.column(align=True)
        if not is_nla:
            row = col.row(align=True)
            row.prop(dopesheet, "filter_fcurve_name", text="")
        else:
            row = col.row(align=True)
            row.prop(dopesheet, "filter_text", text="")

        if (not generic_filters_only) and (bpy.data.collections):
            col = layout.column(align=True)
            col.prop(dopesheet, "filter_collection", text="")

    # Standard = Present in all panels
    @classmethod
    def draw_standard_filters(cls, context, layout):
        dopesheet = context.space_data.dopesheet

        # datablock filters
        layout.label(text="Filter by Type:")
        flow = layout.grid_flow(row_major=True, columns=2, even_rows=False, align=False)

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
        col.prop(dopesheet, "use_datablock_sort", icon='NONE')


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

        layout.prop(dopesheet, "show_summary", text="Summary")

        DopesheetFilterPopoverBase.draw_generic_filters(context, layout)

        if ds_mode in {'DOPESHEET', 'ACTION', 'GPENCIL'}:
            layout.separator()
            generic_filters_only = ds_mode != 'DOPESHEET'
            DopesheetFilterPopoverBase.draw_search_filters(context, layout,
                                                           generic_filters_only=generic_filters_only)

        if ds_mode == 'DOPESHEET':
            layout.separator()
            DopesheetFilterPopoverBase.draw_standard_filters(context, layout)

            layout.prop(st.dopesheet, "use_multi_word_filter", text="Multi-word Match Search")


#######################################
# DopeSheet Editor - General/Standard UI

class DOPESHEET_HT_header(Header):
    bl_space_type = 'DOPESHEET_EDITOR'

    def draw(self, context):
        layout = self.layout

        st = context.space_data

        ALL_MT_editormenu.draw_hidden(context, layout) # bfa - show hide the editormenu

        if st.mode == 'TIMELINE':
            from bl_ui.space_time import (
                TIME_MT_editor_menus,
                TIME_HT_editor_buttons,
            )
            TIME_MT_editor_menus.draw_collapsible(context, layout)
            TIME_HT_editor_buttons.draw_header(context, layout)
        else:
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
        row.template_header() # editor type menus

# Header for "normal" dopesheet editor modes (e.g. Dope Sheet, Action, Shape Keys, etc.)
class DOPESHEET_HT_editor_buttons(Header):
    bl_idname = "DOPESHEET_HT_editor_buttons"
    bl_space_type = 'DOPESHEET_EDITOR'
    bl_label = ""

    def draw(self, context):
        pass

    @staticmethod
    def draw_header(context, layout):
        st = context.space_data
        tool_settings = context.tool_settings

        if st.mode in {'ACTION', 'SHAPEKEY'}:
            # TODO: These buttons need some tidying up -
            # Probably by using a popover, and bypassing the template_id() here
            row = layout.row(align=True)
            row.operator("action.layer_prev", text="", icon='TRIA_DOWN')
            row.operator("action.layer_next", text="", icon='TRIA_UP')

            row = layout.row(align=True)
            row.operator("action.push_down", text="Push Down", icon='NLA_PUSHDOWN')
            row.operator("action.stash", text="Stash", icon='FREEZE')

            layout.separator_spacer()

            layout.template_ID(st, "action", new="action.new", unlink="action.unlink")

        layout.separator_spacer()


        if st.mode == 'GPENCIL':
            row = layout.row(align=True)
            row.prop(st.dopesheet, "show_gpencil_3d_only", text="Active Only")

            if st.dopesheet.show_gpencil_3d_only:
                row = layout.row(align=True)
                row.prop(st.dopesheet, "show_only_selected", text="")
                row.prop(st.dopesheet, "show_hidden", text="")

        layout.popover(panel="DOPESHEET_PT_filters", text="", icon='FILTER')

        # Grease Pencil mode doesn't need snapping, as it's frame-aligned only
        if st.mode != 'GPENCIL':
            layout.prop(st, "auto_snap", text="")

        row = layout.row(align=True)
        row.prop(tool_settings, "use_proportional_action", text="", icon_only=True)
        if tool_settings.use_proportional_action:
            sub = row.row(align=True)
            sub.prop(tool_settings, "proportional_edit_falloff", text="", icon_only=True)
            
        layout.operator_menu_enum("action.handle_type", "type", text="", icon = "HANDLE_AUTO")
        layout.operator_menu_enum("action.interpolation_type", "type", text="", icon = "INTERPOLATE")
        layout.prop(tool_settings, "keyframe_type", text="", icon_only=True)


class DOPESHEET_MT_editor_menus(Menu):
    bl_idname = "DOPESHEET_MT_editor_menus"
    bl_label = ""

    def draw(self, context):
        layout = self.layout
        st = context.space_data

        layout.menu("DOPESHEET_MT_view")
        layout.menu("DOPESHEET_MT_select")
        layout.menu("DOPESHEET_MT_marker")

        if st.mode == 'DOPESHEET' or (st.mode == 'ACTION' and st.action is not None):
            layout.menu("DOPESHEET_MT_channel")
        elif st.mode == 'GPENCIL':
            layout.menu("DOPESHEET_MT_gpencil_channel")

        if st.mode != 'GPENCIL':
            layout.menu("DOPESHEET_MT_key")
        else:
            layout.menu("DOPESHEET_MT_gpencil_frame")


class DOPESHEET_MT_view(Menu):
    bl_label = "View"

    def draw(self, context):
        layout = self.layout

        st = context.space_data

        layout.prop(st, "show_region_ui")

        layout.separator()

        layout.operator("anim.previewrange_set", icon='BORDER_RECT')
        layout.operator("anim.previewrange_clear", icon = "CLEAR")
        layout.operator("action.previewrange_set", icon='BORDER_RECT')

        layout.separator()

        layout.operator("action.view_all", icon = "VIEWALL")
        layout.operator("action.view_selected", icon = "VIEW_SELECTED")
        layout.operator("action.view_frame", icon = "VIEW_FRAME" )

        # Add this to show key-binding (reverse action in dope-sheet).
        layout.separator()

        props = layout.operator("wm.context_set_enum", text="Toggle Graph Editor", icon='GRAPH')
        props.data_path = "area.type"
        props.value = 'GRAPH_EDITOR'

        layout.separator()

        layout.menu("INFO_MT_area")

# Workaround to separate the tooltips
class DOPESHEET_MT_select_before_current_frame(bpy.types.Operator):
    """Select Before Current Frame\nSelects the keyframes before the current frame """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "action.select_leftright_before"        # unique identifier for buttons and menu items to reference.
    bl_label = "Before Current Frame"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.action.select_leftright(extend = False, mode = 'LEFT')
        return {'FINISHED'}  

# Workaround to separate the tooltips
class DOPESHEET_MT_select_after_current_frame(bpy.types.Operator):
    """Select After Current Frame\nSelects the keyframes after the current frame """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "action.select_leftright_after"        # unique identifier for buttons and menu items to reference.
    bl_label = "After Current Frame"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.action.select_leftright(extend = False, mode = 'RIGHT')

# Workaround to separate the tooltips
class DOPESHEET_MT_select_inverse(bpy.types.Operator):
    """Inverse\nInverts the current selection """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "action.select_all_inverse"        # unique identifier for buttons and menu items to reference.
    bl_label = "Select Inverse"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.action.select_all(action = 'INVERT')
        return {'FINISHED'}

# Workaround to separate the tooltips
class DOPESHEET_MT_select_none(bpy.types.Operator):
    """None\nDeselects everything """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "action.select_all_none"        # unique identifier for buttons and menu items to reference.
    bl_label = "Select None"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.action.select_all(action = 'DESELECT')
        return {'FINISHED'}

class DOPESHEET_MT_select(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout

        layout.operator("action.select_all", text="All", icon='SELECT_ALL').action = 'SELECT'
        layout.operator("action.select_all_none", text="None", icon='SELECT_NONE') # bfa - separated tooltip
        layout.operator("action.select_all_inverse", text="Inverse", icon='INVERSE') # bfa - separated tooltip

        layout.separator()
        layout.operator("action.select_box", icon='BORDER_RECT').axis_range = False
        layout.operator("action.select_box", text="Border Axis Range", icon='BORDER_RECT').axis_range = True

        layout.operator("action.select_circle", icon = 'CIRCLE_SELECT')

        layout.separator()
        layout.operator("action.select_column", text="Columns on Selected Keys", icon = "COLUMNS_KEYS").mode = 'KEYS'
        layout.operator("action.select_column", text="Column on Current Frame", icon = "COLUMN_CURRENT_FRAME").mode = 'CFRA'

        layout.operator("action.select_column", text="Columns on Selected Markers", icon = "COLUMNS_MARKERS").mode = 'MARKERS_COLUMN'
        layout.operator("action.select_column", text="Between Selected Markers", icon = "BETWEEN_MARKERS").mode = 'MARKERS_BETWEEN'

        layout.separator()

        if context.space_data.mode != 'GPENCIL':
            layout.operator("action.select_linked", text = "Linked", icon = "CONNECTED")

            layout.separator()

        layout.operator("action.select_leftright_before", text="Before Current Frame", icon = "BEFORE_CURRENT_FRAME") # bfa - the separated tooltip
        layout.operator("action.select_leftright_after", text="After Current Frame", icon = "AFTER_CURRENT_FRAME") # bfa - the separated tooltip

        # FIXME: grease pencil mode isn't supported for these yet, so skip for that mode only
        if context.space_data.mode != 'GPENCIL':
            layout.separator()
            layout.operator("action.select_more",text = "More", icon = "SELECTMORE")
            layout.operator("action.select_less",text = "Less", icon = "SELECTLESS")



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

        layout.operator("anim.channels_delete", icon = "DELETE")

        layout.separator()

        layout.operator("anim.channels_group", icon = "NEW_GROUP")
        layout.operator("anim.channels_ungroup", icon = "REMOVE_FROM_ALL_GROUPS")

        layout.separator()

        layout.menu("GRAPH_MT_channel_settings_toggle")#bfa - menu comes from space_graph

        layout.separator()

        layout.operator("anim.channels_editable_toggle", icon = "LOCKED")
        layout.menu("DOPESHEET_MT_channel_extrapolation")

        layout.separator()

        layout.operator("anim.channels_expand", icon = "EXPANDMENU")
        layout.operator("anim.channels_collapse", icon = "COLLAPSEMENU")

        layout.separator()

        layout.menu("GRAPH_MT_channel_move") #bfa - menu comes from space_graph

        # bfa - the channels find menu item is already in the marker menu. But should be here.
        # The marker menu is a shared menu from the time line. And the time line editor and nla does not have a channel menu.
        #layout.separator()

        #layout.operator("anim.channels_find", icon = "VIEWZOOM") 

        layout.separator()

        layout.operator("anim.channels_fcurves_enable", icon = "UNLOCKED")


class DOPESHEET_MT_channel_extrapolation(Menu):
    bl_label = "Extrapolation Mode"

    def draw(self, context):
        layout = self.layout

        layout.operator("action.extrapolation_type", text = "Constant Extrapolation", icon = "EXTRAPOLATION_CONSTANT").type = 'CONSTANT'
        layout.operator("action.extrapolation_type", text = "Linear Extrapolation", icon = "EXTRAPOLATION_LINEAR").type = 'LINEAR'
        layout.operator("action.extrapolation_type", text = "Make Cyclic (F-Modifier)", icon = "EXTRAPOLATION_CYCLIC").type = 'MAKE_CYCLIC'
        layout.operator("action.extrapolation_type", text = "Clear Cyclic (F-Modifier)", icon = "EXTRAPOLATION_CYCLIC_CLEAR").type = 'CLEAR_CYCLIC'


# Workaround to separate the tooltips
class DOPESHEET_MT_key_clean_channels(bpy.types.Operator):
    """Clean Channels\nSimplify F-Curves by removing closely spaced keyframes in selected channels"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "action.clean_channels"        # unique identifier for buttons and menu items to reference.
    bl_label = "Clean Channels"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.action.clean(channels = True)
        return {'FINISHED'}  


class DOPESHEET_MT_key(Menu):
    bl_label = "Key"

    def draw(self, _context):
        layout = self.layout

        layout.menu("DOPESHEET_MT_key_transform", text="Transform")
        layout.menu("DOPESHEET_MT_key_snap")
        layout.menu("DOPESHEET_MT_key_mirror")

        layout.separator()

        layout.operator("action.keyframe_insert", icon = 'KEYFRAMES_INSERT')

        layout.separator()

        layout.operator("action.frame_jump", icon = 'JUMP_TO_KEYFRAMES')   

        layout.separator()

        layout.operator("action.copy", text="Copy Keyframes", icon='COPYDOWN')
        layout.operator("action.paste", text="Paste Keyframes", icon='PASTEDOWN')
        layout.operator("action.paste", text="Paste Flipped", icon='PASTEFLIPDOWN').flipped = True

        layout.separator()

        layout.operator("action.duplicate_move", icon = "DUPLICATE")
        layout.operator("action.delete", icon = "DELETE")

        layout.separator()

        layout.operator("action.clean", icon = "CLEAN_KEYS").channels = False
        layout.operator("action.clean_channels", text="Clean Channels", icon = "CLEAN_CHANNELS") # bfa -  separated tooltips
        layout.operator("action.sample", icon = "SAMPLE_KEYFRAMES")


class DOPESHEET_PT_view_marker_options(Panel):
    bl_label = "Marker Options"
    bl_space_type = 'DOPESHEET_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'View'

    # dopesheet and timeline is a wild mix. We need to separate them by the following two defs
    @staticmethod
    def in_dopesheet(context):
        return context.space_data.mode != 'TIMELINE' # dopesheet, not timeline

    @classmethod
    def poll(cls, context):
        # only for dopesheet editor
        return cls.in_dopesheet(context)

    def draw(self, context):
        layout = self.layout

        tool_settings = context.tool_settings
        st = context.space_data

        layout.prop(tool_settings, "lock_markers")


        layout.prop(st, "use_marker_sync")


class DOPESHEET_PT_view_view_options(bpy.types.Panel):
    bl_label = "View Options"
    bl_category = "View"
    bl_space_type = 'DOPESHEET_EDITOR'
    bl_region_type = 'UI'

    # dopesheet and timeline is a wild mix. We need to separate them by the following two defs
    @staticmethod
    def in_dopesheet(context):
        return context.space_data.mode != 'TIMELINE' # dopesheet, not timeline

    @classmethod
    def poll(cls, context):
        # only for dopesheet editor
        return cls.in_dopesheet(context)
    
    def draw(self, context):
        sc = context.scene
        layout = self.layout
        
        st = context.space_data

        layout.prop(st, "use_realtime_update")
        layout.prop(st, "show_marker_lines")
        layout.prop(st, "show_frame_indicator")

        layout.separator()

        layout.prop(st, "show_seconds")
        layout.prop(st, "show_locked_time")

        layout.separator()

        layout.prop(st, "show_sliders")
        layout.prop(st, "show_group_colors")
        layout.prop(st, "show_interpolation")
        layout.prop(st, "show_extremes")       
        layout.prop(st, "use_auto_merge_keyframes")




class DOPESHEET_MT_key_transform(Menu):
    bl_label = "Transform"

    def draw(self, _context):
        layout = self.layout

        layout.operator("transform.transform", text="Grab/Move", icon = "TRANSFORM_MOVE").mode = 'TIME_TRANSLATE'
        layout.operator("transform.transform", text="Extend", icon = "SHRINK_FATTEN").mode = 'TIME_EXTEND'
        layout.operator("transform.transform", text="Slide", icon = "PUSH_PULL").mode = 'TIME_SLIDE'
        layout.operator("transform.transform", text="Scale", icon = "TRANSFORM_SCALE").mode = 'TIME_SCALE'

class DOPESHEET_MT_key_mirror(Menu):
    bl_label = "Mirror"

    def draw(self, context):
        layout = self.layout

        layout.operator("action.mirror", text="By Times over Current Frame", icon = "MIRROR_TIME").type = 'CFRA'
        layout.operator("action.mirror", text="By Values over Value=0", icon = "MIRROR_CURSORVALUE").type = 'XAXIS'
        layout.operator("action.mirror", text="By Times over First Selected Marker", icon = "MIRROR_MARKER").type = 'MARKER'

class DOPESHEET_MT_key_snap(Menu):
    bl_label = "Snap"

    def draw(self, context):
        layout = self.layout

        layout.operator("action.snap", text="Current Frame", icon = "SNAP_CURRENTFRAME").type= 'CFRA'
        layout.operator("action.snap", text="Nearest Frame", icon = "SNAP_NEARESTFRAME").type= 'NEAREST_FRAME'
        layout.operator("action.snap", text="Nearest Second", icon = "SNAP_NEARESTSECOND").type= 'NEAREST_SECOND'
        layout.operator("action.snap", text="Nearest Marker", icon = "SNAP_NEARESTMARKER").type= 'NEAREST_MARKER'


#######################################
# Grease Pencil Editing

class DOPESHEET_MT_gpencil_channel(Menu):
    bl_label = "Channel"

    def draw(self, _context):
        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_CHANNELS'

        layout.operator("anim.channels_delete")

        layout.separator()

        layout.operator("anim.channels_setting_toggle", icon = "LOCKED")
        layout.operator("anim.channels_setting_enable", icon = "UNLOCKED")
        layout.operator("anim.channels_setting_disable", icon = "LOCKED")

        layout.separator()

        layout.operator("anim.channels_editable_toggle", icon = "LOCKED")

        layout.separator()

        layout.operator("anim.channels_editable_toggle")

        # XXX: to be enabled when these are ready for use!
        # layout.separator()
        # layout.operator("anim.channels_expand")
        # layout.operator("anim.channels_collapse")

        # layout.separator()
        #layout.operator_menu_enum("anim.channels_move", "direction", text="Move...")


class DOPESHEET_MT_gpencil_frame(Menu):
    bl_label = "Frame"

    def draw(self, _context):
        layout = self.layout

        layout.menu("DOPESHEET_MT_key_transform", text="Transform")
        layout.menu("DOPESHEET_MT_key_snap")
        layout.menu("DOPESHEET_MT_key_mirror")

        layout.separator()

        layout.operator("action.duplicate", icon = "DUPLICATE")
        layout.operator("action.delete", icon = "DELETE")

        layout.separator()

        layout.operator("action.keyframe_type", icon = "SPACE2")

        # layout.separator()
        # layout.operator("action.copy")
        # layout.operator("action.paste")


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

    def draw(self, _context):
        layout = self.layout

        layout.operator_context = 'INVOKE_DEFAULT'

        layout.operator("action.copy", text="Copy", icon='COPYDOWN')
        layout.operator("action.paste", text="Paste", icon='PASTEDOWN')
        layout.operator("action.paste", text="Paste Flipped", icon='PASTEFLIPDOWN').flipped = True

        layout.separator()

        layout.operator_menu_enum("action.keyframe_type", "type", text="Keyframe Type")
        layout.operator_menu_enum("action.handle_type", "type", text="Handle Type")
        layout.operator_menu_enum("action.interpolation_type", "type", text="Interpolation Mode")

        layout.separator()

        layout.operator("action.keyframe_insert").type = 'SEL'
        layout.operator("action.duplicate_move")
        layout.operator_context = 'EXEC_REGION_WIN'
        layout.operator("action.delete")

        layout.separator()

        layout.operator_menu_enum("action.mirror", "type", text="Mirror")
        layout.operator_menu_enum("action.snap", "type", text="Snap")


class DOPESHEET_MT_channel_context_menu(Menu):
    bl_label = "Dope Sheet Channel Context Menu"

    def draw(self, _context):
        layout = self.layout

        layout.operator("anim.channels_setting_enable", text="Mute Channels").type = 'MUTE'
        layout.operator("anim.channels_setting_disable", text="Unmute Channels").type = 'MUTE'
        layout.separator()
        layout.operator("anim.channels_setting_enable", text="Protect Channels").type = 'PROTECT'
        layout.operator("anim.channels_setting_disable", text="Unprotect Channels").type = 'PROTECT'

        layout.separator()
        layout.operator("anim.channels_group")
        layout.operator("anim.channels_ungroup")

        layout.separator()
        layout.operator("anim.channels_editable_toggle")
        layout.operator_menu_enum("action.extrapolation_type", "type", text="Extrapolation Mode")

        layout.separator()
        layout.operator("anim.channels_expand")
        layout.operator("anim.channels_collapse")

        layout.separator()
        layout.operator_menu_enum("anim.channels_move", "direction", text="Move...")

        layout.separator()

        layout.operator("anim.channels_delete")


class DOPESHEET_MT_snap_pie(Menu):
    bl_label = "Snap"

    def draw(self, _context):
        layout = self.layout
        pie = layout.menu_pie()

        pie.operator("action.snap", text="Current Frame").type = 'CFRA'
        pie.operator("action.snap", text="Nearest Frame").type = 'NEAREST_FRAME'
        pie.operator("action.snap", text="Nearest Second").type = 'NEAREST_SECOND'
        pie.operator("action.snap", text="Nearest Marker").type = 'NEAREST_MARKER'


classes = (
    ALL_MT_editormenu,
    DOPESHEET_HT_header,
    DOPESHEET_HT_editor_buttons,
    DOPESHEET_MT_editor_menus,
    DOPESHEET_MT_view,
    DOPESHEET_MT_select_before_current_frame,
    DOPESHEET_MT_select_after_current_frame,
    DOPESHEET_MT_select_inverse,
    DOPESHEET_MT_select_none,
    DOPESHEET_MT_select,
    DOPESHEET_MT_marker,
    DOPESHEET_MT_channel,
    DOPESHEET_MT_channel_extrapolation,
    DOPESHEET_MT_key_clean_channels,
    DOPESHEET_MT_key,
    DOPESHEET_PT_view_marker_options,
    DOPESHEET_PT_view_view_options,
    DOPESHEET_MT_key_transform,
    DOPESHEET_MT_key_mirror,
    DOPESHEET_MT_key_snap,
    DOPESHEET_MT_gpencil_channel,
    DOPESHEET_MT_gpencil_frame,
    DOPESHEET_MT_delete,
    DOPESHEET_MT_context_menu,
    DOPESHEET_MT_channel_context_menu,
    DOPESHEET_MT_snap_pie,
    DOPESHEET_PT_filters,
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
