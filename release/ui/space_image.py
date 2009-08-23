
import bpy

class IMAGE_MT_view(bpy.types.Menu):
	__space_type__ = 'IMAGE_EDITOR'
	__label__ = "View"

	def draw(self, context):
		layout = self.layout
		sima = context.space_data
		uv = sima.uv_editor
		settings = context.tool_settings

		show_uvedit = sima.show_uvedit

		layout.itemO("image.properties", icon='ICON_MENU_PANEL')

		layout.itemS()

		layout.itemR(sima, "update_automatically")
		if show_uvedit:
			layout.itemR(settings, "uv_local_view") # Numpad /

		layout.itemS()

		layout.itemO("image.view_zoom_in")
		layout.itemO("image.view_zoom_out")

		layout.itemS()

		ratios = [[1, 8], [1, 4], [1, 2], [1, 1], [2, 1], [4, 1], [8, 1]];

		for a, b in ratios:
			text = "Zoom %d:%d" % (a, b)
			layout.item_floatO("image.view_zoom_ratio", "ratio", a/float(b), text=text)

		layout.itemS()

		if show_uvedit:
			layout.itemO("image.view_selected")

		layout.itemO("image.view_all")
		layout.itemO("screen.screen_full_area")

class IMAGE_MT_select(bpy.types.Menu):
	__space_type__ = 'IMAGE_EDITOR'
	__label__ = "Select"

	def draw(self, context):
		layout = self.layout

		layout.itemO("uv.select_border")
		layout.item_booleanO("uv.select_border", "pinned", True)

		layout.itemS()
		
		layout.itemO("uv.select_all_toggle")
		layout.itemO("uv.select_inverse")
		layout.itemO("uv.unlink_selection")
		
		layout.itemS()

		layout.itemO("uv.select_pinned")
		layout.itemO("uv.select_linked")

class IMAGE_MT_image(bpy.types.Menu):
	__space_type__ = 'IMAGE_EDITOR'
	__label__ = "Image"

	def draw(self, context):
		layout = self.layout
		sima = context.space_data
		ima = sima.image

		layout.itemO("image.new")
		layout.itemO("image.open")

		show_render = sima.show_render

		if ima:
			if not show_render:
				layout.itemO("image.replace")
				layout.itemO("image.reload")

			layout.itemO("image.save")
			layout.itemO("image.save_as")

			if ima.source == 'SEQUENCE':
				layout.itemO("image.save_sequence")

			if not show_render:
				layout.itemS()

				if ima.packed_file:
					layout.itemO("image.unpack")
				else:
					layout.itemO("image.pack")

				# only for dirty && specific image types, perhaps
				# this could be done in operator poll too
				if ima.dirty:
					if ima.source in ('FILE', 'GENERATED') and ima.type != 'MULTILAYER':
						layout.item_booleanO("image.pack", "as_png", True, text="Pack As PNG")

			layout.itemS()

			layout.itemR(sima, "image_painting")

class IMAGE_MT_uvs_showhide(bpy.types.Menu):
	__space_type__ = 'IMAGE_EDITOR'
	__label__ = "Show/Hide Faces"

	def draw(self, context):
		layout = self.layout

		layout.itemO("uv.reveal")
		layout.itemO("uv.hide")
		layout.item_booleanO("uv.hide", "unselected", True)

class IMAGE_MT_uvs_transform(bpy.types.Menu):
	__space_type__ = 'IMAGE_EDITOR'
	__label__ = "Transform"

	def draw(self, context):
		layout = self.layout

		layout.item_enumO("tfm.transform", "mode", 'TRANSLATION')
		layout.item_enumO("tfm.transform", "mode", 'ROTATION')
		layout.item_enumO("tfm.transform", "mode", 'RESIZE')

class IMAGE_MT_uvs_mirror(bpy.types.Menu):
	__space_type__ = 'IMAGE_EDITOR'
	__label__ = "Mirror"

	def draw(self, context):
		layout = self.layout

		layout.item_enumO("uv.mirror", "axis", 'MIRROR_X') # "X Axis", M, 
		layout.item_enumO("uv.mirror", "axis", 'MIRROR_Y') # "Y Axis", M, 

class IMAGE_MT_uvs_weldalign(bpy.types.Menu):
	__space_type__ = 'IMAGE_EDITOR'
	__label__ = "Weld/Align"

	def draw(self, context):
		layout = self.layout

		layout.itemO("uv.weld") # W, 1
		layout.items_enumO("uv.align", "axis") # W, 2/3/4


class IMAGE_MT_uvs(bpy.types.Menu):
	__space_type__ = 'IMAGE_EDITOR'
	__label__ = "UVs"

	def draw(self, context):
		layout = self.layout
		sima = context.space_data
		uv = sima.uv_editor
		settings = context.tool_settings

		layout.itemR(uv, "snap_to_pixels")
		layout.itemR(uv, "constrain_to_image_bounds")

		layout.itemS()

		layout.itemR(uv, "live_unwrap")
		layout.itemO("uv.unwrap")
		layout.item_booleanO("uv.pin", "clear", True, text="Unpin")
		layout.itemO("uv.pin")

		layout.itemS()

		layout.itemO("uv.pack_islands")
		layout.itemO("uv.average_islands_scale")
		layout.itemO("uv.minimize_stretch")
		layout.itemO("uv.stitch")

		layout.itemS()

		layout.itemM("IMAGE_MT_uvs_transform")
		layout.itemM("IMAGE_MT_uvs_mirror")
		layout.itemM("IMAGE_MT_uvs_weldalign")

		layout.itemS()

		layout.itemR(settings, "proportional_editing")
		layout.item_menu_enumR(settings, "proportional_editing_falloff")

		layout.itemS()

		layout.itemM("IMAGE_MT_uvs_showhide")

class IMAGE_HT_header(bpy.types.Header):
	__space_type__ = 'IMAGE_EDITOR'

	def draw(self, context):
		sima = context.space_data
		ima = sima.image
		iuser = sima.image_user
		layout = self.layout
		settings = context.tool_settings

		show_render = sima.show_render
		show_paint = sima.show_paint
		show_uvedit = sima.show_uvedit

		row = layout.row(align=True)
		row.template_header()

		# menus
		if context.area.show_menus:
			sub = row.row(align=True)
			sub.itemM("IMAGE_MT_view")

			if show_uvedit:
				sub.itemM("IMAGE_MT_select")

			if ima and ima.dirty:
				sub.itemM("IMAGE_MT_image", text="Image*")
			else:
				sub.itemM("IMAGE_MT_image", text="Image")

			if show_uvedit:
				sub.itemM("IMAGE_MT_uvs")

		layout.template_ID(sima, "image", new="image.new")

		# uv editing
		if show_uvedit:
			uvedit = sima.uv_editor

			layout.itemR(uvedit, "pivot", text="")
			layout.itemR(settings, "uv_sync_selection", text="")

			if settings.uv_sync_selection:
				layout.itemR(settings, "mesh_selection_mode", text="", expand=True)
			else:
				layout.itemR(settings, "uv_selection_mode", text="", expand=True)
				layout.itemR(uvedit, "sticky_selection_mode", text="")
			pass

			row = layout.row(align=True)
			row.itemR(settings, "snap", text="")
			if settings.snap:
				row.itemR(settings, "snap_mode", text="")

			"""
			mesh = context.edit_object.data
			row.item_pointerR(mesh, "active_uv_layer", mesh, "uv_textures")
			"""

		if ima:
			# layers
			layout.template_image_layers(ima, iuser)

			# painting
			layout.itemR(sima, "image_painting", text="")

			# draw options
			row = layout.row(align=True)
			row.itemR(sima, "draw_channels", text="", expand=True)

			row = layout.row(align=True)
			if ima.type == 'COMPOSITE':
				row.itemO("image.record_composite", icon='ICON_REC')
			if ima.type == 'COMPOSITE' and ima.source in ('MOVIE', 'SEQUENCE'):
				row.itemO("image.play_composite", icon='ICON_PLAY')
		
		if show_uvedit or sima.image_painting:
			layout.itemR(sima, "update_automatically", text="")

class IMAGE_PT_game_properties(bpy.types.Panel):
	__space_type__ = 'IMAGE_EDITOR'
	__region_type__ = 'UI'
	__label__ = "Game Properties"

	def poll(self, context):
		rd = context.scene.render_data
		sima = context.space_data
		return (sima and sima.image) and (rd.engine == 'BLENDER_GAME')

	def draw(self, context):
		sima = context.space_data
		layout = self.layout

		ima = sima.image

		if ima:
			split = layout.split()

			col = split.column()

			subcol = col.column(align=True)
			subcol.itemR(ima, "clamp_x")
			subcol.itemR(ima, "clamp_y")

			col.itemR(ima, "mapping", expand=True)
			col.itemR(ima, "tiles")

			col = split.column()

			subcol = col.column(align=True)
			subcol.itemR(ima, "animated")

			subcol = subcol.column()
			subcol.itemR(ima, "animation_start", text="Start")
			subcol.itemR(ima, "animation_end", text="End")
			subcol.itemR(ima, "animation_speed", text="Speed")
			subcol.active = ima.animated

			subrow = col.row(align=True)
			subrow.itemR(ima, "tiles_x", text="X")
			subrow.itemR(ima, "tiles_y", text="Y")
			subrow.active = ima.tiles or ima.animated

class IMAGE_PT_view_properties(bpy.types.Panel):
	__space_type__ = 'IMAGE_EDITOR'
	__region_type__ = 'UI'
	__label__ = "View Properties"

	def poll(self, context):
		sima = context.space_data
		return (sima and (sima.image or sima.show_uvedit))

	def draw(self, context):
		sima = context.space_data
		layout = self.layout

		ima = sima.image
		show_uvedit = sima.show_uvedit
		uvedit = sima.uv_editor

		split = layout.split()

		col = split.column()
		if ima:
			col.itemR(ima, "display_aspect")

			col = split.column()
			col.itemR(sima, "draw_repeated", text="Repeat")
			if show_uvedit:
				col.itemR(uvedit, "normalized_coordinates", text="Normalized")
		elif show_uvedit:
			col.itemR(uvedit, "normalized_coordinates", text="Normalized")

		if show_uvedit:
			col = layout.column()
			row = col.row()
			row.itemR(uvedit, "edge_draw_type", expand=True)
			row = col.row()
			row.itemR(uvedit, "draw_smooth_edges", text="Smooth")
			row.itemR(uvedit, "draw_modified_edges", text="Modified")

			row = col.row()
			row.itemR(uvedit, "draw_stretch", text="Stretch")
			row.itemR(uvedit, "draw_stretch_type", text="")
			#col.itemR(uvedit, "draw_edges")
			#col.itemR(uvedit, "draw_faces")

bpy.types.register(IMAGE_MT_view)
bpy.types.register(IMAGE_MT_select)
bpy.types.register(IMAGE_MT_image)
bpy.types.register(IMAGE_MT_uvs_showhide)
bpy.types.register(IMAGE_MT_uvs_transform)
bpy.types.register(IMAGE_MT_uvs_mirror)
bpy.types.register(IMAGE_MT_uvs_weldalign)
bpy.types.register(IMAGE_MT_uvs)
bpy.types.register(IMAGE_HT_header)
bpy.types.register(IMAGE_PT_game_properties)
bpy.types.register(IMAGE_PT_view_properties)

