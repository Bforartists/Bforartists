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

################################ Switch between the editors ##########################################


class switch_editors_in_nla(bpy.types.Operator):
    """You are in NLA editor"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "wm.switch_editor_in_nla"        # unique identifier for buttons and menu items to reference.
    bl_label = "NLA Editor"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    #def execute(self, context):        # execute() is called by blender when running the operator.
    #    bpy.ops.wm.context_set_enum(data_path="area.type", value="NLA_EDITOR")
    #    return {'FINISHED'}  

##########################################################################


class NLA_HT_header(Header):
    bl_space_type = 'NLA_EDITOR'

    def draw(self, context):
        from .space_dopesheet import dopesheet_filter

        layout = self.layout

        st = context.space_data

        ALL_MT_editormenu.draw_hidden(context, layout) # bfa - show hide the editormenu

        # bfa - The tabs to switch between the four animation editors. The classes are in space_time.py
        row = layout.row(align=True)
        row.operator("wm.switch_editor_to_timeline", text="", icon='TIME')
        row.operator("wm.switch_editor_to_graph", text="", icon='IPO')
        row.operator("wm.switch_editor_to_dopesheet", text="", icon='ACTION')     
        row.operator("wm.switch_editor_in_nla", text="", icon='NLA_ACTIVE')
  
        NLA_MT_editor_menus.draw_collapsible(context, layout)

        dopesheet_filter(layout, context)

        layout.prop(st, "auto_snap", text="")

# bfa - show hide the editormenu
class ALL_MT_editormenu(Menu):
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):

        row = layout.row(align=True)
        row.template_header() # editor type menus


class NLA_MT_editor_menus(Menu):
    bl_idname = "NLA_MT_editor_menus"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):
        layout.menu("NLA_MT_view")
        layout.menu("NLA_MT_select")
        layout.menu("NLA_MT_marker")
        layout.menu("NLA_MT_edit")
        layout.menu("NLA_MT_add")


class NLA_MT_view(Menu):
    bl_label = "View"

    def draw(self, context):
        layout = self.layout

        st = context.space_data

        layout.operator("nla.properties", icon='MENU_PANEL')

        layout.separator()
        layout.operator("anim.previewrange_set", icon='BORDER_RECT')
        layout.operator("anim.previewrange_clear", icon = "CLEAR")
        layout.operator("nla.previewrange_set", icon='BORDER_RECT')

        layout.separator()
        layout.operator("nla.view_all", icon = "VIEWALL")
        layout.operator("nla.view_selected", icon = "VIEW_SELECTED")
        layout.operator("nla.view_frame", icon = "VIEW_FRAME" )

        layout.separator()
        layout.operator("screen.area_dupli", icon = "NEW_WINDOW")
        layout.operator("screen.screen_full_area", icon = "MAXIMIZE_AREA")
        layout.operator("screen.screen_full_area", text="Toggle Fullscreen Area", icon = "FULLSCREEN_AREA").use_hide_panels = True


class NLA_MT_select(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout      

        layout.operator("nla.select_border", icon='BORDER_RECT').axis_range = False
        layout.operator("nla.select_border", text="Border Axis Range", icon='BORDER_RECT').axis_range = True

        layout.separator()

        # This is a bit misleading as the operator's default text is "Select All" while it actually *toggles* All/None
        layout.operator("nla.select_all_toggle", icon='SELECT_ALL').invert = False
        layout.operator("nla.select_all_toggle", text="Invert Selection", icon = 'INVERSE').invert = True        

        layout.separator()

        props = layout.operator("nla.select_leftright", text="Before Current Frame", icon = "BEFORE_CURRENT_FRAME")
        props.extend = False
        props.mode = 'LEFT'
        props = layout.operator("nla.select_leftright", text="After Current Frame", icon = "AFTER_CURRENT_FRAME")
        props.extend = False
        props.mode = 'RIGHT'


class NLA_MT_marker(Menu):
    bl_label = "Marker"

    def draw(self, context):
        layout = self.layout

        from .space_time import marker_menu_generic
        marker_menu_generic(layout)


class NLA_MT_edit(Menu):
    bl_label = "Edit"

    def draw(self, context):
        layout = self.layout

        scene = context.scene

        layout.menu("NLA_MT_edit_transform", text="Transform")
        layout.menu("NLA_MT_edit_snap")

        layout.separator()
        layout.operator("nla.duplicate", text="Duplicate", icon = "DUPLICATE").linked = False
        layout.operator("nla.duplicate", text="Linked Duplicate", icon = "DUPLICATE").linked = True
        layout.operator("nla.split", icon = "SPLIT")
        layout.operator("nla.delete", icon = "DELETE")

        layout.separator()
        layout.operator("nla.mute_toggle", icon = "MUTE_IPO_ON")

        layout.separator()
        layout.operator("nla.apply_scale", icon = "APPLYSCALE")
        layout.operator("nla.clear_scale", icon = "CLEARSCALE")
        layout.operator("nla.action_sync_length", icon = "SYNC").active = False

        layout.separator()
        layout.operator("nla.make_single_user", icon = "MAKE_SINGLE_USER")

        layout.separator()
        layout.operator("nla.swap", icon = "SWAP")
        layout.operator("nla.move_up", icon = "MOVE_UP")
        layout.operator("nla.move_down", icon = "MOVE_DOWN")

        # TODO: this really belongs more in a "channel" (or better, "track") menu
        layout.separator()
        layout.menu("NLA_MT_edit_move") # bfa - content is in real the same content than the Move menu in graph editor. Just the title is different ...
        layout.operator("anim.channels_clean_empty", icon = "CLEAN_CHANNELS")

        layout.separator()
        # TODO: names of these tools for 'tweak-mode' need changing?
        if scene.is_nla_tweakmode:
            layout.operator("nla.tweakmode_exit", text="Stop Editing Stashed Action", icon = "ACTION_TWEAK").isolate_action = True
            layout.operator("nla.tweakmode_exit", text="Stop Tweaking Strip Actions", icon = "ACTION_TWEAK")
        else:
            layout.operator("nla.tweakmode_enter", text="Start Editing Stashed Action", icon = "ACTION_TWEAK").isolate_action = True
            layout.operator("nla.tweakmode_enter", text="Start Tweaking Strip Actions", icon = "ACTION_TWEAK")


class NLA_MT_add(Menu):
    bl_label = "Add"

    def draw(self, context):
        layout = self.layout

        layout.operator("nla.actionclip_add", icon = "ADD_STRIP")
        layout.operator("nla.transition_add", icon = "TRANSITION")
        layout.operator("nla.soundclip_add", icon = "SOUND")

        layout.separator()
        layout.operator("nla.meta_add", icon = "ADD_METASTRIP")
        layout.operator("nla.meta_remove", icon = "REMOVE_MTEASTRIP")

        layout.separator()
        layout.operator("nla.tracks_add", icon = "ADD_TRACK").above_selected = False
        layout.operator("nla.tracks_add", text="Add Tracks Above Selected", icon = "ADD_TRACK_ABOVE").above_selected = True

        layout.separator()
        layout.operator("nla.selected_objects_add", icon = "ADD_SELECTED")


class NLA_MT_edit_transform(Menu):
    bl_label = "Transform"

    def draw(self, context):
        layout = self.layout

        layout.operator("transform.translate", text="Grab/Move", icon = "TRANSFORM_MOVE")
        layout.operator("transform.transform", text="Extend", icon = "SHRINK_FATTEN").mode = 'TIME_EXTEND'
        layout.operator("transform.transform", text="Scale", icon = "TRANSFORM_SCALE").mode = 'TIME_SCALE'


class NLA_MT_edit_move(Menu):
    bl_label = "Track Ordering"

    def draw(self, context):
        layout = self.layout
        layout.operator("anim.channels_move", text= "To Top", icon = "MOVE_TO_TOP").direction = 'TOP'
        layout.operator("anim.channels_move", text= "Up", icon = "MOVE_UP").direction = 'UP'
        layout.operator("anim.channels_move", text= "Down", icon = "MOVE_DOWN").direction = 'DOWN'
        layout.operator("anim.channels_move", text= "To Bottom", icon = "MOVE_TO_BOTTOM").direction = 'BOTTOM'

class NLA_MT_edit_snap(Menu):
    bl_label = "Snap"

    def draw(self, context):
        layout = self.layout

        layout.operator("nla.snap", text="Current Frame", icon = "SNAP_CURRENTFRAME").type= 'CFRA'
        layout.operator("nla.snap", text="Nearest Frame", icon = "SNAP_NEARESTFRAME").type= 'NEAREST_FRAME'
        layout.operator("nla.snap", text="Nearest Second", icon = "SNAP_NEARESTSECOND").type= 'NEAREST_SECOND'
        layout.operator("nla.snap", text="Nearest Marker", icon = "SNAP_NEARESTMARKER").type= 'NEAREST_MARKER'

class NLA_PT_view_view_options(Panel):
    bl_label = "View Options"
    bl_space_type = 'NLA_EDITOR'
    bl_region_type = 'UI'

    def draw(self, context):
        layout = self.layout

        st = context.space_data

        layout.separator()

        layout.prop(st, "use_realtime_update")
        layout.prop(st, "show_frame_indicator")

        layout.prop(st, "show_seconds")
        layout.prop(st, "show_locked_time")

        layout.prop(st, "show_strip_curves")
        layout.prop(st, "show_local_markers")




classes = (
    switch_editors_in_nla,
    NLA_HT_header,
    ALL_MT_editormenu,
    NLA_MT_edit,
    NLA_MT_editor_menus,
    NLA_MT_view,
    NLA_MT_select,
    NLA_MT_marker,
    NLA_MT_add,
    NLA_MT_edit_transform,
    NLA_MT_edit_move,
    NLA_MT_edit_snap,
    NLA_PT_view_view_options,
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
