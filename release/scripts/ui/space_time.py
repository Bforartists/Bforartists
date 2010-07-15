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


class TIME_HT_header(bpy.types.Header):
    bl_space_type = 'TIMELINE'

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        tools = context.tool_settings
        screen = context.screen

        row = layout.row(align=True)
        row.template_header()

        if context.area.show_menus:
            sub = row.row(align=True)
            sub.menu("TIME_MT_view")
            sub.menu("TIME_MT_frame")
            sub.menu("TIME_MT_playback")

        layout.prop(scene, "use_preview_range", text="", toggle=True)

        row = layout.row(align=True)
        if not scene.use_preview_range:
            row.prop(scene, "frame_start", text="Start")
            row.prop(scene, "frame_end", text="End")
        else:
            row.prop(scene, "preview_range_frame_start", text="Start")
            row.prop(scene, "preview_range_frame_end", text="End")

        layout.prop(scene, "frame_current", text="")

        layout.separator()

        row = layout.row(align=True)
        row.operator("screen.frame_jump", text="", icon='REW').end = False
        row.operator("screen.keyframe_jump", text="", icon='PREV_KEYFRAME').next = False
        if not screen.animation_playing:
            row.operator("screen.animation_play", text="", icon='PLAY_REVERSE').reverse = True
            row.operator("screen.animation_play", text="", icon='PLAY')
        else:
            sub = row.row()
            sub.scale_x = 2.0
            sub.operator("screen.animation_play", text="", icon='PAUSE')
        row.operator("screen.keyframe_jump", text="", icon='NEXT_KEYFRAME').next = True
        row.operator("screen.frame_jump", text="", icon='FF').end = True

        row = layout.row(align=True)
        row.prop(tools, "use_auto_keying", text="", toggle=True)
        if screen.animation_playing and tools.use_auto_keying:
            subsub = row.row()
            subsub.prop(tools, "record_with_nla", toggle=True)

        layout.prop(scene, "sync_mode", text="")

        layout.separator()

        row = layout.row(align=True)
        row.prop_object(scene, "active_keying_set", scene, "all_keying_sets", text="")
        row.operator("anim.keyframe_insert", text="", icon='KEY_HLT')
        row.operator("anim.keyframe_delete", text="", icon='KEY_DEHLT')


class TIME_MT_view(bpy.types.Menu):
    bl_label = "View"

    def draw(self, context):
        layout = self.layout

        st = context.space_data

        layout.operator("anim.time_toggle")
        layout.operator("time.view_all")

        layout.separator()

        layout.prop(st, "show_cframe_indicator")
        layout.prop(st, "only_selected")

        layout.separator()

        layout.menu("TIME_MT_cache")

        layout.separator()

        layout.operator("marker.camera_bind")


class TIME_MT_cache(bpy.types.Menu):
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


class TIME_MT_frame(bpy.types.Menu):
    bl_label = "Frame"

    def draw(self, context):
        layout = self.layout
        # tools = context.tool_settings

        layout.operator("marker.add", text="Add Marker")
        layout.operator("marker.duplicate", text="Duplicate Marker")
        layout.operator("marker.move", text="Grab/Move Marker")
        layout.operator("marker.delete", text="Delete Marker")

        # it was ok for riscos... ok TODO, operator
        for marker in context.scene.timeline_markers:
            if marker.select:
                layout.separator()
                layout.prop(marker, "name", text="", icon='MARKER_HLT')
                break

        layout.separator()

        layout.operator("time.start_frame_set")
        layout.operator("time.end_frame_set")

        layout.separator()

        sub = layout.row()
        sub.menu("TIME_MT_autokey")


class TIME_MT_playback(bpy.types.Menu):
    bl_label = "Playback"

    def draw(self, context):
        layout = self.layout

        st = context.space_data
        scene = context.scene

        layout.prop(st, "play_top_left")
        layout.prop(st, "play_all_3d")
        layout.prop(st, "play_anim")
        layout.prop(st, "play_buttons")
        layout.prop(st, "play_image")
        layout.prop(st, "play_sequencer")
        layout.prop(st, "play_nodes")

        layout.separator()

        layout.prop(scene, "frame_drop", text="Frame Dropping")
        layout.prop(scene, "sync_audio", text="AV-sync", icon='SPEAKER')
        layout.prop(scene, "mute_audio")
        layout.prop(scene, "scrub_audio")


class TIME_MT_autokey(bpy.types.Menu):
    bl_label = "Auto-Keyframing Mode"

    def draw(self, context):
        layout = self.layout
        tools = context.tool_settings

        layout.prop_enum(tools, "autokey_mode", 'ADD_REPLACE_KEYS')
        layout.prop_enum(tools, "autokey_mode", 'REPLACE_KEYS')

classes = [
    TIME_HT_header,
    TIME_MT_view,
    TIME_MT_cache,
    TIME_MT_frame,
    TIME_MT_autokey,
    TIME_MT_playback]


def register():
    register = bpy.types.register
    for cls in classes:
        register(cls)


def unregister():
    unregister = bpy.types.unregister
    for cls in classes:
        unregister(cls)

if __name__ == "__main__":
    register()
