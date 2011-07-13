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


class CLIP_OT_apply_follow_track(bpy.types.Operator):
    bl_idname = "clip.apply_follow_track"
    bl_label = "Apply Follow Track"
    bl_options = {'UNDO', 'REGISTER'}

    @classmethod
    def poll(cls, context):
        if context.space_data.type != 'CLIP_EDITOR':
            return False

        sc = context.space_data
        clip = sc.clip

        return clip and clip.tracking.active_track and context.active_object

    def execute(self, context):
        ob = context.active_object
        sc = context.space_data
        clip = sc.clip
        track = clip.tracking.active_track
        constraint = None

        for con in ob.constraints:
            if con.type == 'FOLLOW_TRACK':
                constraint = con
                break

        if constraint is None:
            constraint = ob.constraints.new(type='FOLLOW_TRACK')

        constraint.clip = sc.clip
        constraint.track = track.name
        constraint.reference = 'TRACK'

        return {'FINISHED'}


class CLIP_OT_bundles_to_mesh(bpy.types.Operator):
    bl_idname = "clip.bundles_to_mesh"
    bl_label = "Bundles to Mesh"
    bl_options = {'UNDO', 'REGISTER'}

    @classmethod
    def poll(cls, context):
        if context.space_data.type != 'CLIP_EDITOR':
            return False

        sc = context.space_data
        clip = sc.clip

        return clip

    def execute(self, context):
        sc = context.space_data
        clip = sc.clip

        mesh = bpy.data.meshes.new(name="Bundles")
        for track in clip.tracking.tracks:
            if track.has_bundle:
                mesh.vertices.add(1)
                mesh.vertices[-1].co = track.bundle

        ob = bpy.data.objects.new(name="Bundles", object_data=mesh)

        bpy.context.scene.objects.link(ob)

        return {'FINISHED'}


class CLIP_HT_header(bpy.types.Header):
    bl_space_type = 'CLIP_EDITOR'

    def draw(self, context):
        layout = self.layout

        sc = context.space_data
        clip = sc.clip

        row = layout.row(align=True)
        row.template_header()

        if context.area.show_menus:
            sub = row.row(align=True)
            sub.menu("CLIP_MT_view")
            sub.menu("CLIP_MT_clip")

            if clip:
                sub.menu("CLIP_MT_select")
                sub.menu("CLIP_MT_track")

        layout.template_ID(sc, "clip")


class CLIP_PT_tools(bpy.types.Panel):
    bl_space_type = 'CLIP_EDITOR'
    bl_region_type = 'TOOLS'
    bl_label = "Tools"

    def draw(self, context):
        layout = self.layout
        clip = context.space_data.clip
        settings = clip.tracking.settings

        if clip:
            col = layout.column(align=True)
            col.label(text="Transform:")
            col.operator("transform.translate")
            col.operator("transform.resize")

            col = layout.column(align=True)
            col.label(text="Marker:")
            col.operator("clip.add_marker_move")
            col.operator("clip.delete_track")
            col.operator("clip.delete_marker")

            col = layout.column(align=True)
            col.label(text="2D tracking:")
            row = col.row(align=True)

            op = row.operator("clip.track_markers", text="", icon='FRAME_PREV')
            op.backwards = True
            op = row.operator("clip.track_markers", text="", \
                 icon='PLAY_REVERSE')
            op.backwards = True
            op.sequence = True
            op = row.operator("clip.track_markers", text="", icon='PLAY')
            op.sequence = True
            row.operator("clip.track_markers", text="", icon='FRAME_NEXT')

            col = layout.column(align=True)
            op = col.operator("clip.clear_track_path", \
                 text="Clear Remained Path")
            op.action = 'REMAINED'

            op = col.operator("clip.clear_track_path", text="Clear Path Up To")
            op.action = 'UPTO'

            op = col.operator("clip.clear_track_path", text="Clear Track Path")
            op.action = 'ALL'

            layout.operator("clip.apply_follow_track")

            col = layout.column(align=True)
            col.label(text="Reconstruction:")

            col.prop(settings, "keyframe1")
            col.prop(settings, "keyframe2")

            col = layout.column(align=True)
            col.operator("clip.solve_camera")
            col.operator("clip.clear_reconstruction")

            col = layout.column(align=True)
            col.operator("clip.bundles_to_mesh")

            col = layout.column(align=True)
            col.label(text="Scene Orientation:")
            col.operator("clip.set_floor")
            col.operator("clip.set_origin")

            row = col.row()
            row.operator("clip.set_axis", text="Set X Axis").axis = 'X'
            row.operator("clip.set_axis", text="Set Y Axis").axis = 'Y'
        else:
            layout.operator('clip.open')


class CLIP_PT_track(bpy.types.Panel):
    bl_space_type = 'CLIP_EDITOR'
    bl_region_type = 'UI'
    bl_label = "Track"

    @classmethod
    def poll(cls, context):
        sc = context.space_data
        clip = sc.clip

        return clip and clip.tracking.active_track

    def draw(self, context):
        layout = self.layout
        sc = context.space_data
        clip = context.space_data.clip
        act_track = clip.tracking.active_track

        layout.prop(act_track, "name")

        layout.template_track(clip.tracking, "active_track", \
            sc.clip_user, clip)

        if act_track:
            row = layout.row()
            row.prop(act_track, "use_red_channel", text="Red")
            row.prop(act_track, "use_green_channel", text="Green")
            row.prop(act_track, "use_blue_channel", text="Blue")


class CLIP_PT_track_settings(bpy.types.Panel):
    bl_space_type = 'CLIP_EDITOR'
    bl_region_type = 'UI'
    bl_label = "Tracking Settings"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        sc = context.space_data

        return sc.clip

    def draw(self, context):
        layout = self.layout
        clip = context.space_data.clip
        settings = clip.tracking.settings

        layout.label(text="2D tracking:")
        layout.prop(settings, "speed")
        layout.prop(settings, "use_frames_limit")

        row = layout.row()
        row.active = settings.use_frames_limit
        row.prop(settings, "frames_limit")


class CLIP_PT_tracking_camera(bpy.types.Panel):
    bl_space_type = 'CLIP_EDITOR'
    bl_region_type = 'UI'
    bl_label = "Camera Data"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        sc = context.space_data

        return sc.clip

    def draw(self, context):
        layout = self.layout

        sc = context.space_data
        clip = sc.clip

        layout.prop(clip.tracking.camera, "sensor_width")

        row = layout.row(align=True)
        sub = row.split(percentage=0.65)
        sub.prop(clip.tracking.camera, "focal_length")
        sub.prop(clip.tracking.camera, "units", text="")

        layout.label(text="Principal Point")
        layout.prop(clip.tracking.camera, "principal", text="")

        col = layout.column(align=True)
        col.prop(clip.tracking.camera, "k1")
        col.prop(clip.tracking.camera, "k2")
        col.prop(clip.tracking.camera, "k3")


class CLIP_PT_display(bpy.types.Panel):
    bl_space_type = 'CLIP_EDITOR'
    bl_region_type = 'UI'
    bl_label = "Display"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        sc = context.space_data

        row = layout.row()
        row.prop(sc, "show_marker_pattern", text="Pattern")
        row.prop(sc, "show_marker_search", text="Search")

        row = layout.row()
        row.prop(sc, "show_track_path", text="Path")
        row.active = sc.show_track_path
        row.prop(sc, "path_length", text="Length")

        layout.prop(sc, "show_tiny_markers", text="Tiny Markers")
        layout.prop(sc, "show_bundles", text="Bundles")

        layout.prop(sc, "lock_selection")
        layout.prop(sc, "use_mute_footage")


class CLIP_PT_footage(bpy.types.Panel):
    bl_space_type = 'CLIP_EDITOR'
    bl_region_type = 'UI'
    bl_label = "Footage Settings"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        sc = context.space_data

        return sc.clip

    def draw(self, context):
        layout = self.layout

        sc = context.space_data
        clip = sc.clip

        if clip:
            layout.template_movieclip(sc, "clip", sc.clip_user, compact=True)
        else:
            layout.operator("clip.open", icon='FILESEL')


class CLIP_MT_view(bpy.types.Menu):
    bl_label = "View"

    def draw(self, context):
        layout = self.layout

        layout.operator("clip.properties", icon='MENU_PANEL')
        layout.operator("clip.tools", icon='MENU_PANEL')
        layout.separator()

        layout.operator("clip.view_selected")
        layout.operator("clip.view_all")

        layout.separator()
        layout.operator("clip.view_zoom_in")
        layout.operator("clip.view_zoom_out")

        layout.separator()

        ratios = [[1, 8], [1, 4], [1, 2], [1, 1], [2, 1], [4, 1], [8, 1]]

        for a, b in ratios:
            text = "Zoom %d:%d" % (a, b)
            layout.operator("clip.view_zoom_ratio", text=text).ratio = a / b

        layout.separator()
        layout.operator("screen.area_dupli")
        layout.operator("screen.screen_full_area")


class CLIP_MT_clip(bpy.types.Menu):
    bl_label = "Clip"

    def draw(self, context):
        layout = self.layout

        sc = context.space_data
        clip = sc.clip

        if clip:
            layout.operator("clip.reload")

        layout.operator("clip.open")


class CLIP_MT_track(bpy.types.Menu):
    bl_label = "Track"

    def draw(self, context):
        layout = self.layout

        layout.operator("clip.set_origin")

        layout.separator()
        layout.operator("clip.clear_reconstruction")
        layout.operator("clip.solve_camera")

        layout.separator()
        op = layout.operator("clip.clear_track_path", \
             text="Clear Remained Path")
        op.action = 'REMAINED'

        op = layout.operator("clip.clear_track_path", \
             text="Clear Path Up To")
        op.action = 'UPTO'

        op = layout.operator("clip.clear_track_path", \
             text="Clear Track Path")
        op.action = 'ALL'

        layout.separator()
        op = layout.operator("clip.track_markers", \
            text="Track Frame Backwards")
        op.backwards = True

        op = layout.operator("clip.track_markers", text="Track Backwards")
        op.backwards = True
        op.sequence = True

        op = layout.operator("clip.track_markers", text="Track Forwards")
        op.sequence = True
        layout.operator("clip.track_markers", text="Track Frame Forwards")

        layout.separator()
        layout.operator("clip.delete_track")
        layout.operator("clip.delete_marker")

        layout.separator()
        layout.operator("clip.add_marker_move")

        layout.separator()
        layout.menu("CLIP_MT_track_visibility")
        layout.menu("CLIP_MT_track_transform")


class CLIP_MT_track_visibility(bpy.types.Menu):
    bl_label = "Show/Hide"

    def draw(self, context):
        layout = self.layout

        layout.operator("clip.hide_tracks_clear", text="Show Hidden")
        layout.operator("clip.hide_tracks", text="Hide Selected")

        op = layout.operator("clip.hide_tracks", text="Hide Unselected")
        op.unselected = True


class CLIP_MT_track_transform(bpy.types.Menu):
    bl_label = "Transform"

    def draw(self, context):
        layout = self.layout

        layout.operator("transform.translate")
        layout.operator("transform.resize")


class CLIP_MT_select(bpy.types.Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout

        sc = context.space_data

        layout.operator("clip.select_border")
        layout.operator("clip.select_circle")
        layout.operator("clip.select_all", text="Select/Deselect all")
        layout.operator("clip.select_all", text="Inverse").action = 'INVERT'


class CLIP_MT_tracking_specials(bpy.types.Menu):
    bl_label = "Specials"

    @classmethod
    def poll(cls, context):
        return context.space_data.clip

    def draw(self, context):
        layout = self.layout

        op = layout.operator("clip.disable_markers", text="Enable Markers")
        op.action = 'ENABLE'

        op = layout.operator("clip.disable_markers", text="Disable markers")
        op.action = 'DISABLE'

        layout.operator("clip.set_origin")

        layout.separator()
        layout.operator("clip.hide_tracks")
        layout.operator("clip.hide_tracks_clear", text="Show Tracks")

if __name__ == "__main__":  # only for live edit.
    bpy.utils.register_module(__name__)
