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


#######################################
# DopeSheet Filtering

# used for DopeSheet, NLA, and Graph Editors
def dopesheet_filter(layout, context, genericFiltersOnly=False):
    dopesheet = context.space_data.dopesheet
    is_nla = context.area.type == 'NLA_EDITOR'

    row = layout.row(align=True)
    row.prop(dopesheet, "show_only_selected", text="")
    row.prop(dopesheet, "show_hidden", text="")

    if is_nla:
        row.prop(dopesheet, "show_missing_nla", text="")
    else:  # graph and dopesheet editors - F-Curves and drivers only
        row.prop(dopesheet, "show_only_errors", text="")

    if not genericFiltersOnly:
        if bpy.data.groups:
            row = layout.row(align=True)
            row.prop(dopesheet, "show_only_group_objects", text="")
            if dopesheet.show_only_group_objects:
                row.prop(dopesheet, "filter_group", text="")

    if not is_nla:
        row = layout.row(align=True)
        row.prop(dopesheet, "show_only_matching_fcurves", text="")
        if dopesheet.show_only_matching_fcurves:
            row.prop(dopesheet, "filter_fcurve_name", text="")
            row.prop(dopesheet, "use_multi_word_filter", text="")
    else:
        row = layout.row(align=True)
        row.prop(dopesheet, "use_filter_text", text="")
        if dopesheet.use_filter_text:
            row.prop(dopesheet, "filter_text", text="")
            row.prop(dopesheet, "use_multi_word_filter", text="")

    if not genericFiltersOnly:
        row = layout.row(align=True)
        row.prop(dopesheet, "show_datablock_filters", text="Filters")

        if dopesheet.show_datablock_filters:
            row.prop(dopesheet, "show_scenes", text="")
            row.prop(dopesheet, "show_worlds", text="")
            row.prop(dopesheet, "show_nodes", text="")

            row.prop(dopesheet, "show_transforms", text="")

            if bpy.data.meshes:
                row.prop(dopesheet, "show_meshes", text="")
            if bpy.data.shape_keys:
                row.prop(dopesheet, "show_shapekeys", text="")
            if bpy.data.meshes:
                row.prop(dopesheet, "show_modifiers", text="")
            if bpy.data.materials:
                row.prop(dopesheet, "show_materials", text="")
            if bpy.data.lamps:
                row.prop(dopesheet, "show_lamps", text="")
            if bpy.data.textures:
                row.prop(dopesheet, "show_textures", text="")
            if bpy.data.cameras:
                row.prop(dopesheet, "show_cameras", text="")
            if bpy.data.curves:
                row.prop(dopesheet, "show_curves", text="")
            if bpy.data.metaballs:
                row.prop(dopesheet, "show_metaballs", text="")
            if bpy.data.lattices:
                row.prop(dopesheet, "show_lattices", text="")
            if bpy.data.armatures:
                row.prop(dopesheet, "show_armatures", text="")
            if bpy.data.particles:
                row.prop(dopesheet, "show_particles", text="")
            if bpy.data.speakers:
                row.prop(dopesheet, "show_speakers", text="")
            if bpy.data.linestyles:
                row.prop(dopesheet, "show_linestyles", text="")
            if bpy.data.grease_pencil:
                row.prop(dopesheet, "show_gpencil", text="")

            layout.prop(dopesheet, "use_datablock_sort", text="")


#######################################
# DopeSheet Editor - General/Standard UI


# Editor types: 
# ('VIEW_3D', 'TIMELINE', 'GRAPH_EDITOR', 'DOPESHEET_EDITOR', 'NLA_EDITOR', 'IMAGE_EDITOR', 
# 'CLIP_EDITOR', 'TEXT_EDITOR', 'NODE_EDITOR', 'PROPERTIES', 'OUTLINER', 'USER_PREFERENCES', 'INFO', 'FILE_BROWSE)


################################ Switch between the editors ##########################################


class switch_editors_in_dopesheet(bpy.types.Operator):
    """You are in Dopesheet Editor"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "wm.switch_editor_in_dopesheet"        # unique identifier for buttons and menu items to reference.
    bl_label = "Dopesheet Editor"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.


##########################################################################

class DOPESHEET_HT_header(Header):
    bl_space_type = 'DOPESHEET_EDITOR'

    def draw(self, context):
        layout = self.layout

        st = context.space_data
        toolsettings = context.tool_settings

        ALL_MT_editormenu.draw_hidden(context, layout) # bfa - show hide the editormenu

         # bfa - The tabs to switch between the four animation editors. The classes are in space_time.py
        row = layout.row(align=True)
        row.operator("wm.switch_editor_to_timeline", text="", icon='TIME')
        row.operator("wm.switch_editor_to_graph", text="", icon='IPO')
        row.operator("wm.switch_editor_in_dopesheet", text="", icon='DOPESHEET_ACTIVE')
        row.operator("wm.switch_editor_to_nla", text="", icon='NLA')

        DOPESHEET_MT_editor_menus.draw_collapsible(context, layout)


        layout.prop(st, "mode", text="")

        if st.mode in {'ACTION', 'SHAPEKEY'}:
            row = layout.row(align=True)
            row.operator("action.layer_prev", text="", icon='TRIA_DOWN')
            row.operator("action.layer_next", text="", icon='TRIA_UP')

            layout.template_ID(st, "action", new="action.new", unlink="action.unlink")

            row = layout.row(align=True)
            row.operator("action.push_down", text="", icon='NLA_PUSHDOWN')
            row.operator("action.stash", text="", icon='FREEZE')

        layout.prop(st.dopesheet, "show_summary", text="")

        if st.mode == 'DOPESHEET':
            dopesheet_filter(layout, context)
        elif st.mode == 'ACTION':
            # 'genericFiltersOnly' limits the options to only the relevant 'generic' subset of
            # filters which will work here and are useful (especially for character animation)
            dopesheet_filter(layout, context, genericFiltersOnly=True)
        elif st.mode == 'GPENCIL':
            row = layout.row(align=True)
            row.prop(st.dopesheet, "show_gpencil_3d_only", text="Active Only")

            if st.dopesheet.show_gpencil_3d_only:
                row = layout.row(align=True)
                row.prop(st.dopesheet, "show_only_selected", text="")
                row.prop(st.dopesheet, "show_hidden", text="")

            row = layout.row(align=True)
            row.prop(st.dopesheet, "use_filter_text", text="")
            if st.dopesheet.use_filter_text:
                row.prop(st.dopesheet, "filter_text", text="")
                row.prop(st.dopesheet, "use_multi_word_filter", text="")

        row = layout.row(align=True)
        row.prop(toolsettings, "use_proportional_action",
                 text="", icon_only=True)
        if toolsettings.use_proportional_action:
            row.prop(toolsettings, "proportional_edit_falloff",
                     text="", icon_only=True)

        # Grease Pencil mode doesn't need snapping, as it's frame-aligned only
        if st.mode != 'GPENCIL':
            layout.prop(st, "auto_snap", text="", icon = "SNAP_ON")

# bfa - show hide the editormenu
class ALL_MT_editormenu(Menu):
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):

        row = layout.row(align=True)
        row.template_header() # editor type menus


class DOPESHEET_MT_editor_menus(Menu):
    bl_idname = "DOPESHEET_MT_editor_menus"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):
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

        layout.operator("action.properties", icon='MENU_PANEL')

        layout.separator()
        layout.operator("anim.previewrange_set", icon='BORDER_RECT')
        layout.operator("anim.previewrange_clear", icon = "CLEAR")
        layout.operator("action.previewrange_set", icon='BORDER_RECT')

        layout.separator()
        layout.operator("action.view_all", icon = "VIEWALL")
        layout.operator("action.view_selected", icon = "VIEW_SELECTED")
        layout.operator("action.view_frame", icon = "VIEW_FRAME" )

        layout.separator()
        layout.operator("screen.area_dupli", icon = "NEW_WINDOW")
        layout.operator("screen.toggle_maximized_area", text="Toggle Maximize Area", icon = "MAXIMIZE_AREA") # bfa - the separated tooltip. Class is in space_text.py
        layout.operator("screen.screen_full_area", text="Toggle Fullscreen Area", icon = "FULLSCREEN_AREA").use_hide_panels = True


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
        return {'FINISHED'}  


class DOPESHEET_MT_select(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout       
        
        myvar = layout.operator("action.select_lasso", icon='BORDER_LASSO')
        myvar.deselect = False
        layout.operator("action.select_border", icon='BORDER_RECT').axis_range = False
        layout.operator("action.select_border", text="Border Axis Range", icon='BORDER_RECT').axis_range = True
        layout.operator("action.select_circle", icon = 'CIRCLE_SELECT')
        
        layout.separator()
        
        layout.operator("action.select_all_toggle", text = "(De)Select all", icon='SELECT_ALL').invert = False
        layout.operator("action.select_all_toggle", text="Inverse", icon='INVERSE').invert = True 

        layout.separator()
        
        layout.operator("action.select_column", text="Columns on Selected Keys", icon = "COLUMNS_KEYS").mode = 'KEYS'
        layout.operator("action.select_column", text="Column on Current Frame", icon = "COLUMN_CURRENT_FRAME").mode = 'CFRA'
        layout.operator("action.select_column", text="Columns on Selected Markers", icon = "COLUMNS_MARKERS").mode = 'MARKERS_COLUMN'
        layout.operator("action.select_column", text="Between Selected Markers", icon = "BETWEEN_MARKERS").mode = 'MARKERS_BETWEEN'
        
        layout.separator()
        
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

        from .space_time import marker_menu_generic
        marker_menu_generic(layout)

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

    def draw(self, context):
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

        layout.separator()
        layout.operator("anim.channels_fcurves_enable", icon = "UNLOCKED")

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

    def draw(self, context):
        layout = self.layout

        layout.operator("action.copy", text="Copy Keyframes", icon='COPYDOWN')
        layout.operator("action.paste", text="Paste Keyframes", icon='PASTEDOWN')
        layout.operator("action.paste", text="Paste Flipped", icon='PASTEFLIPDOWN').flipped = True

        layout.separator()

        layout.operator("action.duplicate_move", icon = "DUPLICATE")
        layout.operator("action.delete", icon = "DELETE")

        layout.separator()

        layout.menu("DOPESHEET_MT_key_transform", text="Transform")
        layout.menu("DOPESHEET_MT_key_snap")
        layout.menu("DOPESHEET_MT_key_mirror")

        layout.separator()

        layout.operator("action.keyframe_insert", icon = 'KEYFRAMES_INSERT')

        layout.separator()

        layout.operator("action.frame_jump", icon = 'JUMP_TO_KEYFRAMES')     

        layout.separator()

        layout.operator("action.clean", icon = "CLEAN_KEYS").channels = False
        layout.operator("action.clean_channels", text="Clean Channels", icon = "CLEAN_CHANNELS") # bfa -  separated tooltips
        layout.operator("action.sample", icon = "SAMPLE_KEYFRAMES")

        
class DOPESHEET_MT_key_handle_type(Menu):
    bl_label = "Handle Type"

    def draw(self, context):
        layout = self.layout
        layout.operator("action.handle_type", text= "Free", icon = "HANDLE_FREE").type = 'FREE'
        layout.operator("action.handle_type", text= "Vector", icon = "HANDLE_VECTOR").type = 'VECTOR'
        layout.operator("action.handle_type", text= "Aligned", icon = "HANDLE_ALIGN").type = 'ALIGNED'
        layout.operator("action.handle_type", text= "Automatic", icon = "HANDLE_AUTO").type = 'AUTO'
        layout.operator("action.handle_type", text= "Auto Clamped", icon = "HANDLE_AUTO_CLAMPED").type = 'AUTO_CLAMPED'


class DOPESHEET_MT_key_transform(Menu):
    bl_label = "Transform"

    def draw(self, context):
        layout = self.layout

        layout.operator("transform.transform", text="Grab/Move", icon = "TRANSFORM_MOVE").mode = 'TIME_TRANSLATE'
        layout.operator("transform.transform", text="Extend", icon = "SHRINK_FATTEN").mode = 'TIME_EXTEND'
        layout.operator("transform.transform", text="Slide", icon = "PUSH_PULL").mode = 'TIME_SLIDE'
        layout.operator("transform.transform", text="Scale", icon = "TRANSFORM_SCALE").mode = 'TIME_SCALE'


#######################################
# Grease Pencil Editing

class DOPESHEET_MT_gpencil_channel(Menu):
    bl_label = "Channel"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_CHANNELS'

        layout.operator("anim.channels_delete", icon = "DELETE")

        layout.separator()
        layout.operator("anim.channels_setting_toggle", icon = "LOCKED")
        layout.operator("anim.channels_setting_enable", icon = "UNLOCKED")
        layout.operator("anim.channels_setting_disable", icon = "LOCKED")

        layout.separator()
        layout.operator("anim.channels_editable_toggle", icon = "LOCKED")

        # XXX: to be enabled when these are ready for use!
        #layout.separator()
        #layout.operator("anim.channels_expand")
        #layout.operator("anim.channels_collapse")

        #layout.separator()
        #layout.operator_menu_enum("anim.channels_move", "direction", text="Move...")


class DOPESHEET_MT_gpencil_frame(Menu):
    bl_label = "Frame"

    def draw(self, context):
        layout = self.layout

        layout.menu("DOPESHEET_MT_key_transform", text="Transform")
        layout.menu("DOPESHEET_MT_key_snap")
        layout.menu("DOPESHEET_MT_key_mirror")
       
        layout.separator()
        layout.operator("action.duplicate", icon = "DUPLICATE")
        layout.operator("action.delete", icon = "DELETE")

        layout.separator()
        layout.operator("action.keyframe_type", icon = "SPACE2")

        #layout.separator()
        #layout.operator("action.copy")
        #layout.operator("action.paste")


class DOPESHEET_MT_delete(Menu):
    bl_label = "Delete"

    def draw(self, context):
        layout = self.layout

        layout.operator("action.delete")

        layout.separator()

        layout.operator("action.clean").channels = False
        layout.operator("action.clean", text="Clean Channels").channels = True

class DOPESHEET_MT_channel_extrapolation(Menu):
    bl_label = "Extrapolation Mode"

    def draw(self, context):
        layout = self.layout

        layout.operator("action.extrapolation_type", text = "Constant Extrapolation", icon = "EXTRAPOLATION_CONSTANT").type = 'CONSTANT'
        layout.operator("action.extrapolation_type", text = "Linear Extrapolation", icon = "EXTRAPOLATION_LINEAR").type = 'LINEAR'
        layout.operator("action.extrapolation_type", text = "Make Cyclic (F-Modifier)", icon = "EXTRAPOLATION_CYCLIC").type = 'MAKE_CYCLIC'
        layout.operator("action.extrapolation_type", text = "Clear Cyclic (F-Modifier)", icon = "EXTRAPOLATION_CYCLIC_CLEAR").type = 'CLEAR_CYCLIC'

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

class DOPESHEET_PT_view_view_options(bpy.types.Panel):
    bl_label = "View Options"
    bl_category = "View"
    bl_space_type = 'DOPESHEET_EDITOR'
    bl_region_type = 'UI'
    
    def draw(self, context):
        sc = context.scene
        layout = self.layout
        
        st = context.space_data

        layout.prop(st, "use_realtime_update")
        layout.prop(st, "show_frame_indicator")
        layout.prop(st, "show_sliders")
        layout.prop(st, "show_group_colors")
        layout.prop(st, "use_auto_merge_keyframes")
        layout.prop(st, "use_marker_sync")

        layout.prop(st, "show_seconds")
        layout.prop(st, "show_locked_time")


class DOPESHEET_PT_key_properties(Panel):
    bl_label = "Keyframe Options"
    bl_category = "F-Curve"
    bl_space_type = 'DOPESHEET_EDITOR'
    bl_region_type = 'UI'
    
    def draw(self, context):
        sc = context.scene
        layout = self.layout
        
        layout.operator_menu_enum("action.keyframe_type", "type", text="Keyframe Type")
        layout.menu("DOPESHEET_MT_key_handle_type")
        layout.operator_menu_enum("action.interpolation_type", "type", text="Interpolation Mode")

classes = (
    switch_editors_in_dopesheet,
    DOPESHEET_HT_header,
    ALL_MT_editormenu,
    DOPESHEET_MT_editor_menus,
    DOPESHEET_MT_view,
    DOPESHEET_MT_select_before_current_frame,
    DOPESHEET_MT_select_after_current_frame,
    DOPESHEET_MT_select,
    DOPESHEET_MT_marker,
    DOPESHEET_MT_channel,
    DOPESHEET_MT_key_clean_channels,
    DOPESHEET_MT_key,
    DOPESHEET_MT_key_handle_type,
    DOPESHEET_MT_key_transform,
    DOPESHEET_MT_gpencil_channel,
    DOPESHEET_MT_gpencil_frame,
    DOPESHEET_MT_delete,
    DOPESHEET_MT_channel_extrapolation,
    DOPESHEET_MT_key_mirror,
    DOPESHEET_MT_key_snap,
    DOPESHEET_PT_view_view_options,
    DOPESHEET_PT_key_properties,
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
