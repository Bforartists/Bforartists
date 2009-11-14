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
#  Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>
import bpy

narrowui = 180


class RenderButtonsPanel(bpy.types.Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    # COMPAT_ENGINES must be defined in each subclass, external engines can add themselves here

    def poll(self, context):
        rd = context.scene.render_data
        return (context.scene and rd.use_game_engine == False) and (rd.engine in self.COMPAT_ENGINES)


class RENDER_PT_render(RenderButtonsPanel):
    bl_label = "Render"
    COMPAT_ENGINES = set(['BLENDER_RENDER'])

    def draw(self, context):
        layout = self.layout

        rd = context.scene.render_data
        col2 = context.region.width > narrowui

        split = layout.split()

        col = split.column()
        col.itemO("screen.render", text="Image", icon='ICON_RENDER_STILL')

        if col2:
            col = split.column()
        col.item_booleanO("screen.render", "animation", True, text="Animation", icon='ICON_RENDER_ANIMATION')

        layout.itemR(rd, "display_mode", text="Display")


class RENDER_PT_layers(RenderButtonsPanel):
    bl_label = "Layers"
    bl_default_closed = True
    COMPAT_ENGINES = set(['BLENDER_RENDER'])

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        rd = scene.render_data
        col2 = context.region.width > narrowui

        row = layout.row()
        row.template_list(rd, "layers", rd, "active_layer_index", rows=2)

        col = row.column(align=True)
        col.itemO("scene.render_layer_add", icon='ICON_ZOOMIN', text="")
        col.itemO("scene.render_layer_remove", icon='ICON_ZOOMOUT', text="")

        rl = rd.layers[rd.active_layer_index]

        if rl:
            layout.itemR(rl, "name")

        split = layout.split()

        col = split.column()
        col.itemR(scene, "visible_layers", text="Scene")
        if col2:
            col = split.column()
        col.itemR(rl, "visible_layers", text="Layer")

        layout.itemR(rl, "light_override", text="Light")
        layout.itemR(rl, "material_override", text="Material")

        layout.itemS()
        layout.itemL(text="Include:")

        split = layout.split()

        col = split.column()
        col.itemR(rl, "zmask")
        row = col.row()
        row.itemR(rl, "zmask_negate", text="Negate")
        row.active = rl.zmask
        col.itemR(rl, "all_z")

        col = split.column()
        col.itemR(rl, "solid")
        col.itemR(rl, "halo")
        col.itemR(rl, "ztransp")

        col = split.column()
        col.itemR(rl, "sky")
        col.itemR(rl, "edge")
        col.itemR(rl, "strand")

        if rl.zmask:
            split = layout.split()
            split.itemL(text="Zmask Layers:")
            split.column().itemR(rl, "zmask_layers", text="")

        layout.itemS()

        split = layout.split()

        col = split.column()
        col.itemL(text="Passes:")
        col.itemR(rl, "pass_combined")
        col.itemR(rl, "pass_z")
        col.itemR(rl, "pass_vector")
        col.itemR(rl, "pass_normal")
        col.itemR(rl, "pass_uv")
        col.itemR(rl, "pass_mist")
        col.itemR(rl, "pass_object_index")

        if col2:
            col = split.column()
        col.itemL()
        col.itemR(rl, "pass_color")
        col.itemR(rl, "pass_diffuse")
        row = col.row()
        row.itemR(rl, "pass_specular")
        row.itemR(rl, "pass_specular_exclude", text="", icon='ICON_X')
        row = col.row()
        row.itemR(rl, "pass_shadow")
        row.itemR(rl, "pass_shadow_exclude", text="", icon='ICON_X')
        row = col.row()
        row.itemR(rl, "pass_ao")
        row.itemR(rl, "pass_ao_exclude", text="", icon='ICON_X')
        row = col.row()
        row.itemR(rl, "pass_reflection")
        row.itemR(rl, "pass_reflection_exclude", text="", icon='ICON_X')
        row = col.row()
        row.itemR(rl, "pass_refraction")
        row.itemR(rl, "pass_refraction_exclude", text="", icon='ICON_X')


class RENDER_PT_shading(RenderButtonsPanel):
    bl_label = "Shading"
    COMPAT_ENGINES = set(['BLENDER_RENDER'])

    def draw(self, context):
        layout = self.layout

        rd = context.scene.render_data
        col2 = context.region.width > narrowui

        split = layout.split()

        col = split.column()
        col.itemR(rd, "render_textures", text="Textures")
        col.itemR(rd, "render_shadows", text="Shadows")
        col.itemR(rd, "render_sss", text="Subsurface Scattering")
        col.itemR(rd, "render_envmaps", text="Environment Map")

        if col2:
            col = split.column()
        col.itemR(rd, "render_raytracing", text="Ray Tracing")
        col.itemR(rd, "color_management")
        col.itemR(rd, "alpha_mode", text="Alpha")


class RENDER_PT_performance(RenderButtonsPanel):
    bl_label = "Performance"
    bl_default_closed = True
    COMPAT_ENGINES = set(['BLENDER_RENDER'])

    def draw(self, context):
        layout = self.layout

        rd = context.scene.render_data
        col2 = context.region.width > narrowui

        split = layout.split()

        col = split.column(align=True)
        col.itemL(text="Threads:")
        col.row().itemR(rd, "threads_mode", expand=True)
        sub = col.column()
        sub.enabled = rd.threads_mode == 'THREADS_FIXED'
        sub.itemR(rd, "threads")
        col.itemL(text="Tiles:")
        col.itemR(rd, "parts_x", text="X")
        col.itemR(rd, "parts_y", text="Y")

        if col2:
            col = split.column()
        col.itemL(text="Memory:")
        sub = col.column()
        sub.itemR(rd, "save_buffers")
        sub.enabled = not rd.full_sample
        sub = col.column()
        sub.active = rd.use_compositing
        sub.itemR(rd, "free_image_textures")
        sub = col.column()
        sub.active = rd.render_raytracing
        sub.itemL(text="Acceleration structure:")
        sub.itemR(rd, "raytrace_structure", text="")
        if rd.raytrace_structure == 'OCTREE':
            sub.itemR(rd, "octree_resolution", text="Resolution")
        else:
            sub.itemR(rd, "use_instances", text="Instances")
        sub.itemR(rd, "use_local_coords", text="Local Coordinates")


class RENDER_PT_post_processing(RenderButtonsPanel):
    bl_label = "Post Processing"
    bl_default_closed = True
    COMPAT_ENGINES = set(['BLENDER_RENDER'])

    def draw(self, context):
        layout = self.layout

        rd = context.scene.render_data
        col2 = context.region.width > narrowui

        split = layout.split()

        col = split.column()
        col.itemR(rd, "use_compositing")
        col.itemR(rd, "use_sequencer")

        if col2:
            col = split.column()
        col.itemR(rd, "dither_intensity", text="Dither", slider=True)

        layout.itemS()

        split = layout.split()

        col = split.column()
        col.itemR(rd, "fields", text="Fields")
        sub = col.column()
        sub.active = rd.fields
        sub.row().itemR(rd, "field_order", expand=True)
        sub.itemR(rd, "fields_still", text="Still")


        if col2:
            col = split.column()
        else:
            col.itemS()
        col.itemR(rd, "edge")
        sub = col.column()
        sub.active = rd.edge
        sub.itemR(rd, "edge_threshold", text="Threshold", slider=True)
        sub.itemR(rd, "edge_color", text="")


class RENDER_PT_output(RenderButtonsPanel):
    bl_label = "Output"
    COMPAT_ENGINES = set(['BLENDER_RENDER'])

    def draw(self, context):
        layout = self.layout

        rd = context.scene.render_data
        col2 = context.region.width > narrowui

        layout.itemR(rd, "output_path", text="")

        split = layout.split()
        col = split.column()
        col.itemR(rd, "file_format", text="")
        col.row().itemR(rd, "color_mode", text="Color", expand=True)

        if col2:
            col = split.column()
        col.itemR(rd, "file_extensions")
        col.itemR(rd, "use_overwrite")
        col.itemR(rd, "use_placeholder")

        if rd.file_format in ('AVIJPEG', 'JPEG'):
            split = layout.split()
            split.itemR(rd, "quality", slider=True)

        elif rd.file_format == 'OPENEXR':
            split = layout.split()

            col = split.column()
            col.itemL(text="Codec:")
            col.itemR(rd, "exr_codec", text="")

            if col2:
                subsplit = split.split()
                col = subsplit.column()
            col.itemR(rd, "exr_half")
            col.itemR(rd, "exr_zbuf")

            if col2:
                col = subsplit.column()
            col.itemR(rd, "exr_preview")

        elif rd.file_format == 'JPEG2000':
            split = layout.split()
            col = split.column()
            col.itemL(text="Depth:")
            col.row().itemR(rd, "jpeg2k_depth", expand=True)

            if col2:
                col = split.column()
            col.itemR(rd, "jpeg2k_preset", text="")
            col.itemR(rd, "jpeg2k_ycc")

        elif rd.file_format in ('CINEON', 'DPX'):
            split = layout.split()
            col = split.column()
            col.itemR(rd, "cineon_log", text="Convert to Log")

            if col2:
                col = split.column(align=True)
            col.active = rd.cineon_log
            col.itemR(rd, "cineon_black", text="Black")
            col.itemR(rd, "cineon_white", text="White")
            col.itemR(rd, "cineon_gamma", text="Gamma")

        elif rd.file_format == 'TIFF':
            split = layout.split()
            split.itemR(rd, "tiff_bit")


class RENDER_PT_encoding(RenderButtonsPanel):
    bl_label = "Encoding"
    bl_default_closed = True
    COMPAT_ENGINES = set(['BLENDER_RENDER'])

    def poll(self, context):
        rd = context.scene.render_data
        return rd.file_format in ('FFMPEG', 'XVID', 'H264', 'THEORA')

    def draw(self, context):
        layout = self.layout

        rd = context.scene.render_data
        col2 = context.region.width > narrowui

        split = layout.split()

        split.itemR(rd, "ffmpeg_format")
        if rd.ffmpeg_format in ('AVI', 'QUICKTIME', 'MKV', 'OGG'):
            split.itemR(rd, "ffmpeg_codec")
        else:
            split.itemL()

        split = layout.split()

        col = split.column()
        col.itemR(rd, "ffmpeg_video_bitrate")
        col.itemL(text="Rate:")
        col.itemR(rd, "ffmpeg_minrate", text="Minimum")
        col.itemR(rd, "ffmpeg_maxrate", text="Maximum")
        col.itemR(rd, "ffmpeg_buffersize", text="Buffer")

        if col2:
            col = split.column()
        col.itemR(rd, "ffmpeg_gopsize")
        col.itemR(rd, "ffmpeg_autosplit")
        col.itemL(text="Mux:")
        col.itemR(rd, "ffmpeg_muxrate", text="Rate")
        col.itemR(rd, "ffmpeg_packetsize", text="Packet Size")

        row = layout.row()
        row.itemL(text="Audio:")
        row = layout.row()
        row.itemR(rd, "ffmpeg_audio_codec")

        split = layout.split()

        col = split.column()
        col.itemR(rd, "ffmpeg_audio_bitrate")
        col.itemR(rd, "ffmpeg_audio_mixrate")

        if col2:
            col = split.column()
        col.itemR(rd, "ffmpeg_multiplex_audio")
        col.itemR(rd, "ffmpeg_audio_volume")


class RENDER_PT_antialiasing(RenderButtonsPanel):
    bl_label = "Anti-Aliasing"
    COMPAT_ENGINES = set(['BLENDER_RENDER'])

    def draw_header(self, context):
        rd = context.scene.render_data

        self.layout.itemR(rd, "antialiasing", text="")

    def draw(self, context):
        layout = self.layout

        rd = context.scene.render_data
        col2 = context.region.width > narrowui
        layout.active = rd.antialiasing

        split = layout.split()

        col = split.column()
        col.row().itemR(rd, "antialiasing_samples", expand=True)
        col.itemR(rd, "full_sample")

        if col2:
            col = split.column()
        col.itemR(rd, "pixel_filter", text="")
        col.itemR(rd, "filter_size", text="Size", slider=True)


class RENDER_PT_dimensions(RenderButtonsPanel):
    bl_label = "Dimensions"
    COMPAT_ENGINES = set(['BLENDER_RENDER'])

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        rd = scene.render_data
        col2 = context.region.width > narrowui

        split = layout.split()

        col = split.column()
        sub = col.column(align=True)
        sub.itemL(text="Resolution:")
        sub.itemR(rd, "resolution_x", text="X")
        sub.itemR(rd, "resolution_y", text="Y")
        sub.itemR(rd, "resolution_percentage", text="")

        sub.itemL(text="Aspect Ratio:")
        sub.itemR(rd, "pixel_aspect_x", text="X")
        sub.itemR(rd, "pixel_aspect_y", text="Y")

        row = col.row()
        row.itemR(rd, "use_border", text="Border")
        sub = row.row()
        sub.active = rd.use_border
        sub.itemR(rd, "crop_to_border", text="Crop")

        if col2:
            col = split.column()
        sub = col.column(align=True)
        sub.itemL(text="Frame Range:")
        sub.itemR(scene, "start_frame", text="Start")
        sub.itemR(scene, "end_frame", text="End")
        sub.itemR(scene, "frame_step", text="Step")

        sub = col.column(align=True)
        sub.itemL(text="Frame Rate:")
        sub.itemR(rd, "fps")
        sub.itemR(rd, "fps_base", text="/")


class RENDER_PT_stamp(RenderButtonsPanel):
    bl_label = "Stamp"
    bl_default_closed = True
    COMPAT_ENGINES = set(['BLENDER_RENDER'])

    def draw_header(self, context):
        rd = context.scene.render_data

        self.layout.itemR(rd, "render_stamp", text="")

    def draw(self, context):
        layout = self.layout

        rd = context.scene.render_data
        col2 = context.region.width > narrowui

        layout.active = rd.render_stamp

        split = layout.split()

        col = split.column()
        col.itemR(rd, "stamp_time", text="Time")
        col.itemR(rd, "stamp_date", text="Date")
        col.itemR(rd, "stamp_render_time", text="RenderTime")
        col.itemR(rd, "stamp_frame", text="Frame")
        col.itemR(rd, "stamp_scene", text="Scene")
        col.itemR(rd, "stamp_camera", text="Camera")
        col.itemR(rd, "stamp_filename", text="Filename")
        col.itemR(rd, "stamp_marker", text="Marker")
        col.itemR(rd, "stamp_sequence_strip", text="Seq. Strip")

        if col2:
            col = split.column()
        col.active = rd.render_stamp
        col.itemR(rd, "stamp_foreground", slider=True)
        col.itemR(rd, "stamp_background", slider=True)
        col.itemR(rd, "stamp_font_size", text="Font Size")

        row = layout.split(percentage=0.2)
        row.itemR(rd, "stamp_note", text="Note")
        sub = row.row()
        sub.active = rd.stamp_note
        sub.itemR(rd, "stamp_note_text", text="")

bpy.types.register(RENDER_PT_render)
bpy.types.register(RENDER_PT_layers)
bpy.types.register(RENDER_PT_dimensions)
bpy.types.register(RENDER_PT_antialiasing)
bpy.types.register(RENDER_PT_shading)
bpy.types.register(RENDER_PT_output)
bpy.types.register(RENDER_PT_encoding)
bpy.types.register(RENDER_PT_performance)
bpy.types.register(RENDER_PT_post_processing)
bpy.types.register(RENDER_PT_stamp)
