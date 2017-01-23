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
from bpy.types import Header, Menu


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
        from bl_ui.space_dopesheet import dopesheet_filter

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

        layout.prop(st, "use_realtime_update")
        layout.prop(st, "show_frame_indicator")

        layout.prop(st, "show_seconds")
        layout.prop(st, "show_locked_time")

        layout.prop(st, "show_strip_curves")
        layout.prop(st, "show_local_markers")

        layout.separator()
        layout.operator("anim.previewrange_set")
        layout.operator("anim.previewrange_clear")
        layout.operator("nla.previewrange_set")

        layout.separator()
        layout.operator("nla.view_all")
        layout.operator("nla.view_selected")
        layout.operator("nla.view_frame")

        layout.separator()
        layout.operator("screen.area_dupli")
        layout.operator("screen.screen_full_area")
        layout.operator("screen.screen_full_area", text="Toggle Fullscreen Area").use_hide_panels = True


class NLA_MT_select(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout

        # This is a bit misleading as the operator's default text is "Select All" while it actually *toggles* All/None
        layout.operator("nla.select_all_toggle").invert = False
        layout.operator("nla.select_all_toggle", text="Invert Selection").invert = True

        layout.separator()
        layout.operator("nla.select_border").axis_range = False
        layout.operator("nla.select_border", text="Border Axis Range").axis_range = True

        layout.separator()
        props = layout.operator("nla.select_leftright", text="Before Current Frame")
        props.extend = False
        props.mode = 'LEFT'
        props = layout.operator("nla.select_leftright", text="After Current Frame")
        props.extend = False
        props.mode = 'RIGHT'


class NLA_MT_marker(Menu):
    bl_label = "Marker"

    def draw(self, context):
        layout = self.layout

        from bl_ui.space_time import marker_menu_generic
        marker_menu_generic(layout)


class NLA_MT_edit(Menu):
    bl_label = "Edit"

    def draw(self, context):
        layout = self.layout

        scene = context.scene

        layout.menu("NLA_MT_edit_transform", text="Transform")

        layout.operator_menu_enum("nla.snap", "type", text="Snap")

        layout.separator()
        layout.operator("nla.duplicate", text="Duplicate").linked = False
        layout.operator("nla.duplicate", text="Linked Duplicate").linked = True
        layout.operator("nla.split")
        layout.operator("nla.delete")

        layout.separator()
        layout.operator("nla.mute_toggle")

        layout.separator()
        layout.operator("nla.apply_scale")
        layout.operator("nla.clear_scale")
        layout.operator("nla.action_sync_length").active = False

        layout.separator()
        layout.operator("nla.make_single_user")

        layout.separator()
        layout.operator("nla.swap")
        layout.operator("nla.move_up")
        layout.operator("nla.move_down")

        # TODO: this really belongs more in a "channel" (or better, "track") menu
        layout.separator()
        layout.operator_menu_enum("anim.channels_move", "direction", text="Track Ordering...")
        layout.operator("anim.channels_clean_empty")

        layout.separator()
        # TODO: names of these tools for 'tweak-mode' need changing?
        if scene.is_nla_tweakmode:
            layout.operator("nla.tweakmode_exit", text="Stop Editing Stashed Action").isolate_action = True
            layout.operator("nla.tweakmode_exit", text="Stop Tweaking Strip Actions")
        else:
            layout.operator("nla.tweakmode_enter", text="Start Editing Stashed Action").isolate_action = True
            layout.operator("nla.tweakmode_enter", text="Start Tweaking Strip Actions")

#Add F-Modifier submenu
class NLA_OT_fmodifier_add(Menu):
    bl_label = "Add F-Modifier"

    def draw(self, context):
        layout = self.layout

        layout.operator("nla.fmodifier_add", text = "Generator" ).type = 'GENERATOR'
        layout.operator("nla.fmodifier_add", text = "Built-In Function" ).type = 'FNGENERATOR'
        layout.operator("nla.fmodifier_add", text = "Envelope" ).type = 'ENVELOPE'
        layout.operator("nla.fmodifier_add", text = "Cycles" ).type = 'CYCLES'
        layout.operator("nla.fmodifier_add", text = "Noise" ).type = 'NOISE'
        layout.operator("nla.fmodifier_add", text = "Python" ).type = 'PYTHON'
        layout.operator("nla.fmodifier_add", text = "Limits" ).type = 'LIMITS'
        layout.operator("nla.fmodifier_add", text = "Stepped Interpolation" ).type = 'STEPPED'


class NLA_MT_add(Menu):
    bl_label = "Add"

    def draw(self, context):
        layout = self.layout

        layout.operator("nla.actionclip_add")
        layout.operator("nla.transition_add")
        layout.operator("nla.soundclip_add")

        layout.separator()
        layout.operator("nla.meta_add")
        layout.operator("nla.meta_remove")

        layout.separator()
        layout.operator("nla.tracks_add").above_selected = False
        layout.operator("nla.tracks_add", text="Add Tracks Above Selected").above_selected = True

        layout.separator()
        layout.operator("nla.selected_objects_add")
        layout.menu("NLA_OT_fmodifier_add") #Add F-Modifier submenu


class NLA_MT_edit_transform(Menu):
    bl_label = "Transform"

    def draw(self, context):
        layout = self.layout

        layout.operator("transform.translate", text="Grab/Move")
        layout.operator("transform.transform", text="Extend").mode = 'TIME_EXTEND'
        layout.operator("transform.transform", text="Scale").mode = 'TIME_SCALE'

if __name__ == "__main__":  # only for live edit.
    bpy.utils.register_module(__name__)
