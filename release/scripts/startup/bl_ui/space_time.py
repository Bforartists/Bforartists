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

class switch_editors_to_graph(bpy.types.Operator):
    """Switch to Graph editor"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "wm.switch_editor_to_graph"        # unique identifier for buttons and menu items to reference.
    bl_label = "Switch to Graph Editor"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.wm.context_set_enum(data_path="area.type", value="GRAPH_EDITOR")
        return {'FINISHED'}

class switch_editors_to_dopesheet(bpy.types.Operator):
    """Switch to Dopesheet Editor"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "wm.switch_editor_to_dopesheet"        # unique identifier for buttons and menu items to reference.
    bl_label = "Switch to Dopesheet Editor"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.wm.context_set_enum(data_path="area.type", value="DOPESHEET_EDITOR")
        return {'FINISHED'} 

class switch_editors_to_timeline(bpy.types.Operator):
    """Switch to Timeline editor"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "wm.switch_editor_to_timeline"        # unique identifier for buttons and menu items to reference.
    bl_label = "Switch to Timeline Editor"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.wm.context_set_enum(data_path="area.type", value="TIMELINE")
        return {'FINISHED'}

class switch_editors_to_nla(bpy.types.Operator):
    """Switch to NLA editor"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "wm.switch_editor_to_nla"        # unique identifier for buttons and menu items to reference.
    bl_label = "Switch to NLA Editor"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.wm.context_set_enum(data_path="area.type", value="NLA_EDITOR")
        return {'FINISHED'}  

##########################################################################

# The blank button, we don't want to switch to the editor in which we are already.

class switch_editors_in_timeline(bpy.types.Operator):
    """You are in Timeline editor"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "wm.switch_editor_in_timeline"        # unique identifier for buttons and menu items to reference.
    bl_label = "Timeline Editor"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.


class TIME_HT_header(Header):
    bl_space_type = 'TIMELINE'

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        toolsettings = context.tool_settings
        screen = context.screen
        userprefs = context.user_preferences

        ALL_MT_editormenu.draw_hidden(context, layout) # bfa - show hide the editormenu

        # bfa - The tabs to switch between the four animation editors
        row = layout.row(align=True)
        row.operator("wm.switch_editor_in_timeline", text="", icon='TIME_ACTIVE')
        row.operator("wm.switch_editor_to_graph", text="", icon='IPO')
        row.operator("wm.switch_editor_to_dopesheet", text="", icon='ACTION')     
        row.operator("wm.switch_editor_to_nla", text="", icon='NLA')

        TIME_MT_editor_menus.draw_collapsible(context, layout)

        row = layout.row(align=True)
        row.prop(scene, "use_preview_range", text="", toggle=True)
        row.prop(scene, "lock_frame_selection_to_range", text="", toggle=True)

        row = layout.row(align=True)
        if not scene.use_preview_range:
            row.prop(scene, "frame_start", text="Start")
            row.prop(scene, "frame_end", text="End")
        else:
            row.prop(scene, "frame_preview_start", text="Start")
            row.prop(scene, "frame_preview_end", text="End")

        if scene.show_subframe:
            layout.prop(scene, "frame_float", text="")
        else:
            layout.prop(scene, "frame_current", text="")

        layout.separator()

        row = layout.row(align=True)
        row.operator("screen.frame_jump", text="", icon='REW').end = False
        row.operator("screen.keyframe_jump", text="", icon='PREV_KEYFRAME').next = False
        if not screen.is_animation_playing:
            # if using JACK and A/V sync:
            #   hide the play-reversed button
            #   since JACK transport doesn't support reversed playback
            if scene.sync_mode == 'AUDIO_SYNC' and context.user_preferences.system.audio_device == 'JACK':
                sub = row.row(align=True)
                sub.scale_x = 2.0
                sub.operator("screen.animation_play", text="", icon='PLAY')
            else:
                row.operator("screen.animation_play", text="", icon='PLAY_REVERSE').reverse = True
                row.operator("screen.animation_play", text="", icon='PLAY')
        else:
            sub = row.row(align=True)
            sub.scale_x = 2.0
            sub.operator("screen.animation_play", text="", icon='PAUSE')
        row.operator("screen.keyframe_jump", text="", icon='NEXT_KEYFRAME').next = True
        row.operator("screen.frame_jump", text="", icon='FF').end = True

        layout.prop(scene, "sync_mode", text="")

        layout.separator()

        row = layout.row(align=True)
        row.prop(toolsettings, "use_keyframe_insert_auto", text="", toggle=True)
        if toolsettings.use_keyframe_insert_auto:
            row.prop(toolsettings, "use_keyframe_insert_keyingset", text="", toggle=True)

            if screen.is_animation_playing and not userprefs.edit.use_keyframe_insert_available:
                subsub = row.row(align=True)
                subsub.prop(toolsettings, "use_record_with_nla", toggle=True)

        row = layout.row(align=True)
        row.prop_search(scene.keying_sets_all, "active", scene, "keying_sets_all", text="")
        row.operator("anim.keyframe_insert", text="", icon='KEY_HLT')
        row.operator("anim.keyframe_delete", text="", icon='KEY_DEHLT')

# bfa - show hide the editormenu
class ALL_MT_editormenu(Menu):
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):

        row = layout.row(align=True)
        row.template_header() # editor type menus

class TIME_MT_editor_menus(Menu):
    bl_idname = "TIME_MT_editor_menus"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):
        layout.menu("TIME_MT_view")
        layout.menu("TIME_MT_marker")
        layout.menu("TIME_MT_frame")
        layout.menu("TIME_MT_playback")


class TIME_MT_marker(Menu):
    bl_label = "Marker"

    def draw(self, context):
        layout = self.layout

        marker_menu_generic(layout)


class TIME_MT_view(Menu):
    bl_label = "View"

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        st = context.space_data

        layout.prop(st, "show_seconds")
        layout.prop(st, "show_locked_time")

        layout.separator()

        layout.prop(st, "show_frame_indicator")
        layout.prop(scene, "show_keys_from_selected_only")
        layout.prop(scene, "show_subframe")

        layout.separator()

        layout.menu("TIME_MT_cache")

        layout.separator()

        layout.operator("time.view_all")
        layout.operator("time.view_frame")

        layout.separator()

        layout.operator("marker.camera_bind")

        layout.separator()

        layout.operator("screen.area_dupli")
        layout.operator("screen.toggle_maximized_area", text="Toggle Maximize Area") # bfa - the separated tooltip. Class is in space_text.py
        layout.operator("screen.screen_full_area", text="Toggle Fullscreen Area").use_hide_panels = True


class TIME_MT_cache(Menu):
    bl_label = "Cache"

    def draw(self, context):
        layout = self.layout

        st = context.space_data

        layout.prop(st, "show_cache")

        layout.separator()

        col = layout.column()
        col.enabled = st.show_cache
        col.prop(st, "cache_softbody")
        col.prop(st, "cache_particles")
        col.prop(st, "cache_cloth")
        col.prop(st, "cache_smoke")
        col.prop(st, "cache_dynamicpaint")
        col.prop(st, "cache_rigidbody")


class TIME_MT_frame(Menu):
    bl_label = "Frame"

    def draw(self, context):
        layout = self.layout

        layout.operator("anim.previewrange_clear")
        layout.operator("anim.previewrange_set")
        layout.separator()
        layout.operator("time.end_frame_set")
        layout.operator("time.start_frame_set")

        layout.separator()

        layout.menu("TIME_MT_autokey")


class TIME_MT_playback(Menu):
    bl_label = "Playback"

    def draw(self, context):
        layout = self.layout

        screen = context.screen
        scene = context.scene

        layout.prop(screen, "use_play_top_left_3d_editor")
        layout.prop(screen, "use_play_3d_editors")
        layout.prop(screen, "use_play_animation_editors")
        layout.prop(screen, "use_play_properties_editors")
        layout.prop(screen, "use_play_image_editors")
        layout.prop(screen, "use_play_sequence_editors")
        layout.prop(screen, "use_play_node_editors")
        layout.prop(screen, "use_play_clip_editors")

        layout.separator()
        layout.prop(screen, "use_follow")
        layout.separator()

        layout.prop(scene, "use_frame_drop", text="Frame Dropping")
        layout.prop(scene, "use_audio_sync", text="AV-sync", icon='SPEAKER')
        layout.prop(scene, "use_audio")
        layout.prop(scene, "use_audio_scrub")


class TIME_MT_autokey(Menu):
    bl_label = "Auto-Keyframing Mode"

    def draw(self, context):
        layout = self.layout
        toolsettings = context.tool_settings

        layout.prop_enum(toolsettings, "auto_keying_mode", 'ADD_REPLACE_KEYS')
        layout.prop_enum(toolsettings, "auto_keying_mode", 'REPLACE_KEYS')


# Workaround to separate the tooltips
class marker_menu_generic_marker_jump_previous(bpy.types.Operator):
    """Jump to previous Marker\nJumps to previous marker """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "screen.marker_jump_previous"        # unique identifier for buttons and menu items to reference.
    bl_label = "Jump to previous Marker"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.screen.marker_jump(next = False)
        return {'FINISHED'}  


def marker_menu_generic(layout):

    # layout.operator_context = 'EXEC_REGION_WIN'

    layout.column()
    layout.operator("marker.add", "Add Marker")
    layout.operator("marker.duplicate", text="Duplicate Marker")

    if len(bpy.data.scenes) > 10:
        layout.operator_context = 'INVOKE_DEFAULT'
        layout.operator("marker.make_links_scene", text="Duplicate Marker to Scene...", icon='OUTLINER_OB_EMPTY')
    else:
        layout.operator_menu_enum("marker.make_links_scene", "scene", text="Duplicate Marker to Scene...")

    layout.operator("marker.delete", text="Delete Marker")

    layout.separator()

    layout.operator("marker.rename", text="Rename Marker")
    layout.operator("marker.move", text="Grab/Move Marker")

    layout.separator()

    layout.operator("screen.marker_jump", text="Jump to Next Marker").next = True
    layout.operator("screen.marker_jump_previous", text="Jump to Previous Marker") # bfa - the separated tooltip

    layout.separator()
    ts = bpy.context.tool_settings
    layout.prop(ts, "lock_markers")


classes = (
    ALL_MT_editormenu,
    switch_editors_to_graph,
    switch_editors_to_dopesheet,
    switch_editors_to_timeline,
    switch_editors_to_nla,
    switch_editors_in_timeline,
    TIME_HT_header,
    TIME_MT_editor_menus,
    TIME_MT_marker,
    TIME_MT_view,
    TIME_MT_cache,
    TIME_MT_frame,
    TIME_MT_playback,
    TIME_MT_autokey,
    marker_menu_generic_marker_jump_previous,
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
