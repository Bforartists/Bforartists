
import bpy

class RenderButtonsPanel(bpy.types.Panel):
	__space_type__ = "BUTTONS_WINDOW"
	__region_type__ = "WINDOW"
	__context__ = "scene"

class RENDER_PT_shading(RenderButtonsPanel):
	__label__ = "Shading"

	def draw(self, context):
		scene = context.scene
		layout = self.layout

		rd = scene.render_data
		
		split = layout.split()
		
		sub = split.column()
		sub.itemR(rd, "render_shadows", text="Shadows")
		sub.itemR(rd, "render_sss", text="Subsurface Scattering")
		sub.itemR(rd, "render_envmaps", text="Environment Map")
		#	sub.itemR(rd, "render_radiosity", text="Radio")
		
		col = split.column()
		colsub = col.column()
		colsub.active = rd.render_raytracing
		colsub.itemR(rd, "render_raytracing", text="Ray Tracing")
		colsub.itemR(rd, "octree_resolution", text="Octree")
		col.itemR(rd, "dither_intensity", text="Dither", slider=True)
		
class RENDER_PT_output(RenderButtonsPanel):
	__label__ = "Output"

	def draw(self, context):
		scene = context.scene
		layout = self.layout

		rd = scene.render_data
		
		layout.itemR(rd, "output_path")
		
		split = layout.split()
		
		sub = split.column()
		sub.itemR(rd, "file_format", text="Format")
		if rd.file_format in ("AVIJPEG", "JPEG"):
			sub.itemR(rd, "quality", slider=True)
		
		sub = split.column()
		sub.itemR(rd, "color_mode")
		sub.itemR(rd, "alpha_mode")
		
		split = layout.split()
		
		sub = split.column()
		sub.itemL(text="Distributed Rendering:")
		sub.itemR(rd, "placeholders")
		sub.itemR(rd, "no_overwrite")
		
		sub = split.column()
		sub.itemL(text="Settings:")
		sub.itemR(rd, "file_extensions")
		sub.itemR(rd, "fields", text="Fields")
		if rd.fields:
			sub.itemR(rd, "fields_still", text="Still")
			sub.row().itemR(rd, "field_order", expand=True)

class RENDER_PT_antialiasing(RenderButtonsPanel):
	__label__ = "Anti-Aliasing"

	def draw_header(self, context):
		rd = context.scene.render_data

		layout = self.layout
		layout.itemR(rd, "antialiasing", text="")

	def draw(self, context):
		scene = context.scene
		rd = scene.render_data

		layout = self.layout
		layout.active = rd.antialiasing

		split = layout.split()
		
		sub = split.column()
		sub.itemL(text="Samples:")
		sub.row().itemR(rd, "antialiasing_samples", expand=True)

		sub = split.column()
		sub.itemR(rd, "pixel_filter")
		sub.itemR(rd, "filter_size", text="Size", slider=True)
		sub.itemR(rd, "save_buffers")
		if rd.save_buffers:
			sub.itemR(rd, "full_sample")

class RENDER_PT_render(RenderButtonsPanel):
	__label__ = "Render"

	def draw(self, context):
		scene = context.scene
		layout = self.layout

		rd = scene.render_data

		row = layout.row()
		row.itemO("SCREEN_OT_render", text="Render Still", icon=109)
		row.item_booleanO("SCREEN_OT_render", "anim", True, text="Render Animation", icon=111)
		
		row = layout.row()
		row.itemR(rd, "do_composite")
		row.itemR(rd, "do_sequence")
		if rd.do_composite:
			row = layout.row()
			row.itemR(rd, "free_image_textures")

		split = layout.split()
		
		sub = split.column(align=True)
		sub.itemL(text="Threads:")
		sub.row().itemR(rd, "threads_mode", expand=True)
		if rd.threads_mode == 'THREADS_FIXED':
			sub.itemR(rd, "threads")
		
		sub = split.column(align=True)
		sub.itemL(text="Tiles:")
		sub.itemR(rd, "parts_x", text="X")
		sub.itemR(rd, "parts_y", text="Y")
		
		split = layout.split()
		sub = split.column()
		sub = split.column()
		sub.itemR(rd, "panorama")
		
		#	row.itemR(rd, "backbuf")
			
class RENDER_PT_dimensions(RenderButtonsPanel):
	__label__ = "Dimensions"

	def draw(self, context):
		scene = context.scene
		layout = self.layout

		rd = scene.render_data
		
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
		
		sub = col.column(align=False)
		sub.itemR(rd, "border", text="Border")
		if rd.border:
			sub.itemR(rd, "crop_to_border")

		col = split.column(align=True)
		col.itemL(text="Frame Range:")
		col.itemR(scene, "start_frame", text="Start")
		col.itemR(scene, "end_frame", text="End")
		col.itemR(scene, "frame_step", text="Step")
		
		col.itemL(text="Frame Rate:")
		col.itemR(rd, "fps")
		col.itemR(rd, "fps_base",text="/")

class RENDER_PT_stamp(RenderButtonsPanel):
	__label__ = "Stamp"

	def draw_header(self, context):
		rd = context.scene.render_data

		layout = self.layout
		layout.itemR(rd, "stamp", text="")

	def draw(self, context):
		scene = context.scene
		rd = scene.render_data

		layout = self.layout
		layout.active = rd.stamp

		split = layout.split()
		
		sub = split.column()
		sub.itemR(rd, "stamp_time", text="Time")
		sub.itemR(rd, "stamp_date", text="Date")
		sub.itemR(rd, "stamp_frame", text="Frame")
		sub.itemR(rd, "stamp_camera", text="Scene")
		sub.itemR(rd, "stamp_marker", text="Marker")
		sub.itemR(rd, "stamp_filename", text="Filename")
		sub.itemR(rd, "stamp_sequence_strip", text="Seq. Strip")
		sub.itemR(rd, "stamp_note", text="Note")
		if (rd.stamp_note):
			sub.itemR(rd, "stamp_note_text", text="")
		
		sub = split.column()
		sub.itemR(rd, "render_stamp")
		sub.itemR(rd, "stamp_foreground")
		sub.itemR(rd, "stamp_background")
		sub.itemR(rd, "stamp_font_size", text="Font Size")

bpy.types.register(RENDER_PT_render)
bpy.types.register(RENDER_PT_dimensions)
bpy.types.register(RENDER_PT_antialiasing)
bpy.types.register(RENDER_PT_shading)
bpy.types.register(RENDER_PT_output)
bpy.types.register(RENDER_PT_stamp)

