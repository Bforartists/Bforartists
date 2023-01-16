# SPDX-License-Identifier: GPL-2.0-or-later
import bpy
from bpy.types import Menu, Panel, UIList
from bl_ui.utils import PresetPanel

from bpy.app.translations import (
    contexts as i18n_contexts,
    pgettext_tip as tip_,
)


class RENDER_PT_format_presets(PresetPanel, Panel):
    bl_label = "Format Presets"
    preset_subdir = "render"
    preset_operator = "script.execute_preset"
    preset_add_operator = "render.preset_add"


class RENDER_PT_ffmpeg_presets(PresetPanel, Panel):
    bl_label = "FFMPEG Presets"
    preset_subdir = "ffmpeg"
    preset_operator = "script.python_file_run"


class RENDER_MT_framerate_presets(Menu):
    bl_label = "Frame Rate Presets"
    preset_subdir = "framerate"
    preset_operator = "script.execute_preset"
    draw = Menu.draw_preset


class RenderOutputButtonsPanel:
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "output"
    # COMPAT_ENGINES must be defined in each subclass, external engines can add themselves here

    @classmethod
    def poll(cls, context):
        return (context.engine in cls.COMPAT_ENGINES)


class RENDER_PT_format(RenderOutputButtonsPanel, Panel):
    bl_label = "Format"
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT', 'BLENDER_WORKBENCH'}

    _frame_rate_args_prev = None
    _preset_class = None

    def draw_header_preset(self, _context):
        RENDER_PT_format_presets.draw_panel_header(self.layout)

    @staticmethod
    def _draw_framerate_label(*args):
        # avoids re-creating text string each draw
        if RENDER_PT_format._frame_rate_args_prev == args:
            return RENDER_PT_format._frame_rate_ret

        fps, fps_base, preset_label = args

        if fps_base == 1.0:
            fps_rate = round(fps)
        else:
            fps_rate = round(fps / fps_base, 2)

        # TODO: Change the following to iterate over existing presets
        custom_framerate = (fps_rate not in {23.98, 24, 25, 29.97, 30, 50, 59.94, 60, 120, 240})

        if custom_framerate is True:
            fps_label_text = tip_("Custom (%.4g fps)") % fps_rate
            show_framerate = True
        else:
            fps_label_text = tip_("%.4g fps") % fps_rate
            show_framerate = (preset_label == "Custom")

        RENDER_PT_format._frame_rate_args_prev = args
        RENDER_PT_format._frame_rate_ret = args = (fps_label_text, show_framerate)
        return args

    @staticmethod
    def draw_framerate(layout, rd):
        if RENDER_PT_format._preset_class is None:
            RENDER_PT_format._preset_class = bpy.types.RENDER_MT_framerate_presets

        args = rd.fps, rd.fps_base, RENDER_PT_format._preset_class.bl_label
        fps_label_text, show_framerate = RENDER_PT_format._draw_framerate_label(*args)

        layout.menu("RENDER_MT_framerate_presets", text=fps_label_text)

        if show_framerate:
            col = layout.column(align=True)
            col.prop(rd, "fps")
            col.prop(rd, "fps_base", text="Base")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        rd = context.scene.render

        col = layout.column(align=True)
        col.label(text = "Resolution")
        row = col.row()
        row.separator()
        col = row.column(align=True)
        col.prop(rd, "resolution_x", text="X")
        col.prop(rd, "resolution_y", text="Y")
        col.prop(rd, "resolution_percentage", text="Percent %")

        col = layout.column(align=True)
        col.label(text = "Aspect")
        row = col.row()
        row.separator()
        col = row.column(align=True)
        col.prop(rd, "pixel_aspect_x", text="X")
        col.prop(rd, "pixel_aspect_y", text="Y")


        split = layout.split(factor=.4)
        split.use_property_split=False
        split.prop(rd, "use_border")

        split.alignment = 'LEFT'
        if rd.use_border:
            split.use_property_split = False
            split.prop(rd, "use_crop_to_border")
        else:
            split.label(icon='DISCLOSURE_TRI_RIGHT')


        col = layout.column(heading="Frame Rate")
        self.draw_framerate(col, rd)


class RENDER_PT_frame_range(RenderOutputButtonsPanel, Panel):
    bl_label = "Frame Range"
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT', 'BLENDER_WORKBENCH'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        scene = context.scene

        col = layout.column(align=True)
        col.label(text = "Frame")
        row = col.row()
        row.separator()
        col = row.column(align=True)
        col.prop(scene, "frame_start", text="Start")
        col.prop(scene, "frame_end", text="End")
        col.prop(scene, "frame_step", text="Step")


class RENDER_PT_time_stretching(RenderOutputButtonsPanel, Panel):
    bl_label = "Time Stretching"
    bl_parent_id = "RENDER_PT_frame_range"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT', 'BLENDER_WORKBENCH'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        rd = context.scene.render

        col = layout.column(align=True)
        col.prop(rd, "frame_map_old", text="Old")
        col.prop(rd, "frame_map_new", text="New")


class RENDER_PT_post_processing(RenderOutputButtonsPanel, Panel):
    bl_label = "Post Processing"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT', 'BLENDER_WORKBENCH'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        rd = context.scene.render

        col = layout.column(align = True)
        col.label(text = "Pipeline")
        col.use_property_split = False
        row = col.row()
        row.separator()
        row.prop(rd, "use_compositing")
        row = col.row()
        row.separator()
        row.prop(rd, "use_sequencer")

        layout.prop(rd, "dither_intensity", text="Dither", slider=True)


class RENDER_PT_stamp(RenderOutputButtonsPanel, Panel):
    bl_label = "Metadata"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT', 'BLENDER_WORKBENCH'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False  # No animation.

        rd = context.scene.render

        if rd.use_sequencer:
            layout.prop(rd, "metadata_input")

        col = layout.column(align = True)
        col.label(text = "Include")
        row = col.row()
        row.separator()
        row.prop(rd, "use_stamp_date", text="Date")
        row = col.row()
        row.separator()
        row.prop(rd, "use_stamp_time", text="Time")
        row = col.row()
        row.separator()
        row.prop(rd, "use_stamp_render_time", text="Render Time")
        row = col.row()
        row.separator()
        row.prop(rd, "use_stamp_frame", text="Frame")
        row = col.row()
        row.separator()
        row.prop(rd, "use_stamp_frame_range", text="Frame Range")
        row = col.row()
        row.separator()
        row.prop(rd, "use_stamp_memory", text="Memory")
        row = col.row()
        row.separator()
        row.prop(rd, "use_stamp_hostname", text="Hostname")
        row = col.row()
        row.separator()
        row.prop(rd, "use_stamp_camera", text="Camera")
        row = col.row()
        row.separator()
        row.prop(rd, "use_stamp_lens", text="Lens")
        row = col.row()
        row.separator()
        row.prop(rd, "use_stamp_scene", text="Scene")
        row = col.row()
        row.separator()
        row.prop(rd, "use_stamp_marker", text="Marker")
        row = col.row()
        row.separator()
        row.prop(rd, "use_stamp_filename", text="Filename")

        if rd.use_sequencer:
            row = col.row()
            row.separator()
            row.prop(rd, "use_stamp_sequencer_strip", text="Strip Name")


class RENDER_PT_stamp_note(RenderOutputButtonsPanel, Panel):
    bl_label = "Note"
    bl_parent_id = "RENDER_PT_stamp"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT', 'BLENDER_WORKBENCH'}

    def draw_header(self, context):
        rd = context.scene.render

        self.layout.prop(rd, "use_stamp_note", text="")

    def draw(self, context):
        layout = self.layout

        rd = context.scene.render

        layout.active = rd.use_stamp_note
        layout.prop(rd, "stamp_note_text", text="")


class RENDER_PT_stamp_burn(RenderOutputButtonsPanel, Panel):
    bl_label = "Burn Into Image"
    bl_parent_id = "RENDER_PT_stamp"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT', 'BLENDER_WORKBENCH'}

    def draw_header(self, context):
        rd = context.scene.render

        self.layout.prop(rd, "use_stamp", text="")

    def draw(self, context):
        layout = self.layout

        rd = context.scene.render

        layout.use_property_split = True

        col = layout.column()
        col.active = rd.use_stamp
        col.prop(rd, "stamp_font_size", text="Font Size")
        col.column().prop(rd, "stamp_foreground", slider=True)
        col.column().prop(rd, "stamp_background", slider=True)
        row = layout.row()
        row.active = rd.use_stamp
        row.use_property_split = False
        row.prop(rd, "use_stamp_labels", text="Include Labels")
        row.prop_decorator(rd, "use_stamp_labels")


class RENDER_PT_output(RenderOutputButtonsPanel, Panel):
    bl_label = "Output"
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT', 'BLENDER_WORKBENCH'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False  # No animation.

        rd = context.scene.render
        image_settings = rd.image_settings
        is_eevee = context.scene.render.engine == 'BLENDER_EEVEE'
        is_workbench = context.scene.render.engine == 'BLENDER_WORKBENCH'

        layout.prop(rd, "filepath", text="")

        layout.template_image_settings(image_settings, color_management=False)

        if is_eevee or is_workbench:
            row = layout.row()
            row.prop(rd, "film_transparent", text="Transparent")
            row.prop_decorator(rd, "film_transparent")


# Options subpanel for the output panel
class RENDER_PT_output_options(RenderOutputButtonsPanel, Panel):
    bl_label = "Options"
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'}
    bl_parent_id = "RENDER_PT_output"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False  # No animation.

        rd = context.scene.render
        image_settings = rd.image_settings

        col = layout.column(align = True)
        col.label(text = "Saving")
        row = col.row()
        row.separator()
        row.prop(rd, "use_file_extension")
        row = col.row()
        row.separator()
        row.prop(rd, "use_render_cache")

        if not rd.is_movie_format:
            col = layout.column(align = True)
            col.label(text = "Image Sequence")
            row = col.row()
            row.separator()
            row.prop(rd, "use_overwrite")
            row = col.row()
            row.separator()
            row.prop(rd, "use_placeholder")


class RENDER_PT_output_views(RenderOutputButtonsPanel, Panel):
    bl_label = "Views"
    bl_parent_id = "RENDER_PT_output"
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT', 'BLENDER_WORKBENCH'}

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return rd.use_multiview

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False  # No animation.

        rd = context.scene.render
        layout.template_image_views(rd.image_settings)


class RENDER_PT_output_color_management(RenderOutputButtonsPanel, Panel):
    bl_label = "Color Management"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "RENDER_PT_output"
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT', 'BLENDER_WORKBENCH'}

    def draw(self, context):
        scene = context.scene
        image_settings = scene.render.image_settings

        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False  # No animation.

        layout.row().prop(image_settings, "color_management", text=" ", expand=True)
        layout.use_property_split = True

        flow = layout.grid_flow(row_major=True, columns=0, even_columns=False, even_rows=False, align=True)

        if image_settings.color_management == 'OVERRIDE':
            owner = image_settings
        else:
            owner = scene
            flow.enabled = False

        col = flow.column()

        if image_settings.has_linear_colorspace:
            if hasattr(owner, "linear_colorspace_settings"):
                col.prop(owner.linear_colorspace_settings, "name", text="Color Space")
        else:
            col.prop(owner.display_settings, "display_device")
            col.separator()
            col.template_colormanaged_view_settings(owner, "view_settings")


class RENDER_PT_encoding(RenderOutputButtonsPanel, Panel):
    bl_label = "Encoding"
    bl_parent_id = "RENDER_PT_output"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT', 'BLENDER_WORKBENCH'}

    def draw_header_preset(self, _context):
        RENDER_PT_ffmpeg_presets.draw_panel_header(self.layout)

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return rd.image_settings.file_format in {'FFMPEG', 'XVID', 'H264', 'THEORA'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        rd = context.scene.render
        ffmpeg = rd.ffmpeg

        layout.prop(rd.ffmpeg, "format")
        layout.use_property_split = False
        layout.prop(ffmpeg, "use_autosplit")


class RENDER_PT_encoding_video(RenderOutputButtonsPanel, Panel):
    bl_label = "Video"
    bl_parent_id = "RENDER_PT_encoding"
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT', 'BLENDER_WORKBENCH'}

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return rd.image_settings.file_format in {'FFMPEG', 'XVID', 'H264', 'THEORA'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        self.draw_vcodec(context)

    def draw_vcodec(self, context):
        """Video codec options."""
        layout = self.layout
        ffmpeg = context.scene.render.ffmpeg

        needs_codec = ffmpeg.format in {
            'AVI',
            'QUICKTIME',
            'MKV',
            'OGG',
            'MPEG4',
            'WEBM',
        }
        if needs_codec:
            layout.prop(ffmpeg, "codec")

        if needs_codec and ffmpeg.codec == 'NONE':
            return

        if ffmpeg.codec == 'DNXHD':
            layout.use_property_split = False
            layout.prop(ffmpeg, "use_lossless_output")
            layout.use_property_split = True

        # Output quality
        use_crf = needs_codec and ffmpeg.codec in {
            'H264',
            'MPEG4',
            'WEBM',
            'AV1',
        }
        if use_crf:
            layout.prop(ffmpeg, "constant_rate_factor")

        # Encoding speed
        layout.prop(ffmpeg, "ffmpeg_preset")
        # I-frames
        layout.prop(ffmpeg, "gopsize")
        # B-Frames
        split = layout.split( factor = 0.39)
        col = split.column()
        col.use_property_split = False
        col.prop(ffmpeg, "use_max_b_frames", text = "Max B_Frames")
        col = split.column()
        if ffmpeg.use_max_b_frames:
            col.prop(ffmpeg, "max_b_frames", text="")
        else:
            col.label(icon='DISCLOSURE_TRI_RIGHT')

        if not use_crf or ffmpeg.constant_rate_factor == 'NONE':
            col = layout.column()

            sub = col.column(align=True)
            sub.prop(ffmpeg, "video_bitrate")
            sub.prop(ffmpeg, "minrate", text="Minimum")
            sub.prop(ffmpeg, "maxrate", text="Maximum")

            col.prop(ffmpeg, "buffersize", text="Buffer")

            col.separator()

            col.prop(ffmpeg, "muxrate", text="Mux Rate")
            col.prop(ffmpeg, "packetsize", text="Mux Packet Size")


class RENDER_PT_encoding_audio(RenderOutputButtonsPanel, Panel):
    bl_label = "Audio"
    bl_parent_id = "RENDER_PT_encoding"
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT', 'BLENDER_WORKBENCH'}

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return rd.image_settings.file_format in {'FFMPEG', 'XVID', 'H264', 'THEORA'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        rd = context.scene.render
        ffmpeg = rd.ffmpeg

        if ffmpeg.format != 'MP3':
            layout.prop(ffmpeg, "audio_codec", text="Audio Codec")

        if ffmpeg.audio_codec != 'NONE':
            layout.prop(ffmpeg, "audio_channels")
            layout.prop(ffmpeg, "audio_mixrate", text="Sample Rate")
            layout.prop(ffmpeg, "audio_bitrate")
            layout.prop(ffmpeg, "audio_volume", slider=True)


class RENDER_UL_renderviews(UIList):
    def draw_item(self, _context, layout, _data, item, icon, _active_data, _active_propname, index):
        view = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if view.name in {"left", "right"}:
                layout.label(text=view.name, icon_value=icon + (not view.use))
            else:
                layout.prop(view, "name", text="", index=index, icon_value=icon, emboss=False)
            layout.prop(view, "use", text="", index=index)

        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon + (not view.use))


class RENDER_PT_stereoscopy(RenderOutputButtonsPanel, Panel):
    bl_label = "Stereoscopy"
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT', 'BLENDER_WORKBENCH'}
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        rd = context.scene.render
        self.layout.prop(rd, "use_multiview", text="")

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        rd = scene.render
        rv = rd.views.active

        layout.active = rd.use_multiview
        basic_stereo = rd.views_format == 'STEREO_3D'

        row = layout.row()
        layout.row().prop(rd, "views_format", expand=True)

        if basic_stereo:
            row = layout.row()
            row.template_list("RENDER_UL_renderviews", "name", rd, "stereo_views", rd.views, "active_index", rows=2)

            row = layout.row()
            row.use_property_split = True
            row.use_property_decorate = False
            row.prop(rv, "file_suffix")

        else:
            row = layout.row()
            row.template_list("RENDER_UL_renderviews", "name", rd, "views", rd.views, "active_index", rows=2)

            col = row.column(align=True)
            col.operator("scene.render_view_add", icon='ADD', text="")
            col.operator("scene.render_view_remove", icon='REMOVE', text="")

            row = layout.row()
            row.use_property_split = True
            row.use_property_decorate = False
            row.prop(rv, "camera_suffix")


classes = (
    RENDER_PT_format_presets,
    RENDER_PT_ffmpeg_presets,
    RENDER_MT_framerate_presets,
    RENDER_PT_format,
    RENDER_PT_frame_range,
    RENDER_PT_time_stretching,
    RENDER_PT_stereoscopy,
    RENDER_PT_output,
    RENDER_PT_output_options,
    RENDER_PT_output_views,
    RENDER_PT_output_color_management,
    RENDER_PT_encoding,
    RENDER_PT_encoding_video,
    RENDER_PT_encoding_audio,
    RENDER_PT_stamp,
    RENDER_PT_stamp_note,
    RENDER_PT_stamp_burn,
    RENDER_UL_renderviews,
    RENDER_PT_post_processing,
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
