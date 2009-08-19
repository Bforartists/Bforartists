
import bpy

# ********** Header **********

class VIEW3D_HT_header(bpy.types.Header):
	__space_type__ = "VIEW_3D"

	def draw(self, context):
		layout = self.layout
		
		view = context.space_data
		mode_string = context.mode
		edit_object = context.edit_object
		
		row = layout.row(align=True)
		row.template_header()

		# Menus
		if context.area.show_menus:
			sub = row.row(align=True)

			sub.itemM("VIEW3D_MT_view")
			
			# Select Menu
			if mode_string not in ('EDIT_TEXT', 'SCULPT', 'PAINT_WEIGHT', 'PAINT_VERTEX', 'PAINT_TEXTURE', 'PARTICLE'):
				# XXX: Particle Mode has Select Menu.
				sub.itemM("VIEW3D_MT_select_%s" % mode_string)
			
			if mode_string == 'OBJECT':
				sub.itemM("VIEW3D_MT_object")
			elif mode_string == 'SCULPT':
				sub.itemM("VIEW3D_MT_sculpt")
			elif edit_object:
				sub.itemM("VIEW3D_MT_edit_%s" % edit_object.type)

		layout.template_header_3D()

# ********** Menu **********

# ********** View menus **********

class VIEW3D_MT_view(bpy.types.Menu):
	__space_type__ = "VIEW_3D"
	__label__ = "View"

	def draw(self, context):
		layout = self.layout

		layout.itemO("view3d.properties", icon="ICON_MENU_PANEL")
		layout.itemO("view3d.toolbar", icon="ICON_MENU_PANEL")
		
		layout.itemS()
		
		layout.item_enumO("view3d.viewnumpad", "type", 'CAMERA')
		layout.item_enumO("view3d.viewnumpad", "type", 'TOP')
		layout.item_enumO("view3d.viewnumpad", "type", 'FRONT')
		layout.item_enumO("view3d.viewnumpad", "type", 'RIGHT')
		
		# layout.itemM("VIEW3D_MT_view_cameras", text="Cameras")
		
		layout.itemS()

		layout.itemO("view3d.view_persportho")
		
		layout.itemS()
		
		# layout.itemO("view3d.view_show_all_layers")
		
		# layout.itemS()
		
		# layout.itemO("view3d.view_local_view")
		# layout.itemO("view3d.view_global_view")
		
		# layout.itemS()
		
		layout.itemM("VIEW3D_MT_view_navigation")
		# layout.itemM("VIEW3D_MT_view_align", text="Align View")
		
		layout.itemS()

		layout.operator_context = "INVOKE_REGION_WIN"

		layout.itemO("view3d.clip_border")
		layout.itemO("view3d.zoom_border")
		
		layout.itemS()
		
		layout.itemO("view3d.view_center")
		layout.itemO("view3d.view_all")
		
		layout.itemS()
		
		layout.itemO("screen.region_foursplit", text="Toggle Quad View")
		layout.itemO("screen.screen_full_area", text="Toggle Full Screen")
		
class VIEW3D_MT_view_navigation(bpy.types.Menu):
	__space_type__ = "VIEW_3D"
	__label__ = "Navigation"

	def draw(self, context):
		layout = self.layout

		# layout.itemO("view3d.view_fly_mode")
		# layout.itemS()
		
		layout.items_enumO("view3d.view_orbit", "type")
		
		layout.itemS()
		
		layout.items_enumO("view3d.view_pan", "type")
		
		layout.itemS()
		
		layout.item_floatO("view3d.zoom", "delta", 1.0, text="Zoom In")
		layout.item_floatO("view3d.zoom", "delta", -1.0, text="Zoom Out")

# ********** Select menus, suffix from context.mode **********

class VIEW3D_MT_select_OBJECT(bpy.types.Menu):
	__space_type__ = "VIEW_3D"
	__label__ = "Select"

	def draw(self, context):
		layout = self.layout

		layout.itemO("view3d.select_border")

		layout.itemS()

		layout.itemO("object.select_all_toggle", text="Select/Deselect All")
		layout.itemO("object.select_inverse", text="Inverse")
		layout.itemO("object.select_random", text="Random")
		layout.itemO("object.select_by_layer", text="Select All by Layer")
		layout.item_enumO("object.select_by_type", "type", "", text="Select All by Type")
		layout.itemO("object.select_grouped", text="Select Grouped")

class VIEW3D_MT_select_POSE(bpy.types.Menu):
	__space_type__ = "VIEW_3D"
	__label__ = "Select"

	def draw(self, context):
		layout = self.layout

		layout.itemO("view3d.select_border")

		layout.itemS()
		
		layout.itemO("pose.select_all_toggle", text="Select/Deselect All")
		layout.itemO("pose.select_inverse", text="Inverse")
		layout.itemO("pose.select_constraint_target", text="Constraint Target")
		
		layout.itemS()
		
		layout.item_enumO("pose.select_hierarchy", "direction", 'PARENT')
		layout.item_enumO("pose.select_hierarchy", "direction", 'CHILD')
		
		layout.itemS()
		
		layout.view3d_select_posemenu()

class VIEW3D_MT_select_PARTICLE(bpy.types.Menu):
	__space_type__ = "VIEW_3D"
	__label__ = "Select"

	def draw(self, context):
		layout = self.layout

		layout.itemO("view3d.select_border")

		layout.itemS()
		
		layout.itemO("particle.select_all_toggle", text="Select/Deselect All")
		layout.itemO("particle.select_linked")
		
		layout.itemS()
		
		#layout.itemO("particle.select_last")
		#layout.itemO("particle.select_first")
		
		layout.itemO("particle.select_more")
		layout.itemO("particle.select_less")

class VIEW3D_MT_select_EDIT_MESH(bpy.types.Menu):
	__space_type__ = "VIEW_3D"
	__label__ = "Select"

	def draw(self, context):
		layout = self.layout

		layout.itemO("view3d.select_border")

		layout.itemS()

		layout.itemO("mesh.select_all_toggle", text="Select/Deselect All")
		layout.itemO("mesh.select_inverse", text="Inverse")

		layout.itemS()

		layout.itemO("mesh.select_random", text="Random...")
		layout.itemO("mesh.edges_select_sharp", text="Sharp Edges")
		layout.itemO("mesh.faces_select_linked_flat", text="Linked Flat Faces")

		layout.itemS()

		layout.item_enumO("mesh.select_by_number_vertices", "type", 'TRIANGLES', text="Triangles")
		layout.item_enumO("mesh.select_by_number_vertices", "type", 'QUADS', text="Quads")
		layout.item_enumO("mesh.select_by_number_vertices", "type", 'OTHER', text="Loose Verts/Edges")
		layout.itemO("mesh.select_similar", text="Similar...")

		layout.itemS()

		layout.itemO("mesh.select_less", text="Less")
		layout.itemO("mesh.select_more", text="More")

		layout.itemS()

		layout.itemO("mesh.select_linked", text="Linked")
		layout.itemO("mesh.select_vertex_path", text="Vertex Path")
		layout.itemO("mesh.loop_multi_select", text="Edge Loop")
		layout.item_booleanO("mesh.loop_multi_select", "ring", True, text="Edge Ring")

		layout.itemS()

		layout.itemO("mesh.loop_to_region")
		layout.itemO("mesh.region_to_loop")

class VIEW3D_MT_select_EDIT_CURVE(bpy.types.Menu):
	__space_type__ = "VIEW_3D"
	__label__ = "Select"

	def draw(self, context):
		layout = self.layout

		layout.itemO("view3d.select_border")
		layout.itemO("view3d.select_circle")

		layout.itemS()
		
		layout.itemO("curve.select_all_toggle", text="Select/Deselect All")
		layout.itemO("curve.select_inverse")
		layout.itemO("curve.select_random")
		layout.itemO("curve.select_every_nth")

		layout.itemS()
		
		layout.itemO("curve.de_select_first")
		layout.itemO("curve.de_select_last")
		layout.itemO("curve.select_next")
		layout.itemO("curve.select_previous")

		layout.itemS()
		
		layout.itemO("curve.select_more")
		layout.itemO("curve.select_less")

class VIEW3D_MT_select_EDIT_SURFACE(bpy.types.Menu):
	__space_type__ = "VIEW_3D"
	__label__ = "Select"

	def draw(self, context):
		layout = self.layout

		layout.itemO("view3d.select_border")
		layout.itemO("view3d.select_circle")

		layout.itemS()
		
		layout.itemO("curve.select_all_toggle", text="Select/Deselect All")
		layout.itemO("curve.select_inverse")
		layout.itemO("curve.select_random")
		layout.itemO("curve.select_every_nth")

		layout.itemS()
		
		layout.itemO("curve.select_row")

		layout.itemS()
		
		layout.itemO("curve.select_more")
		layout.itemO("curve.select_less")

class VIEW3D_MT_select_EDIT_METABALL(bpy.types.Menu):
	__space_type__ = "VIEW_3D"
	__label__ = "Select"

	def draw(self, context):
		layout = self.layout

		layout.itemO("view3d.select_border")
		
		layout.itemS()
		
		layout.itemL(text="Select/Deselect All")
		layout.itemL(text="Inverse")
		
		layout.itemS()
		
		layout.itemL(text="Random")

class VIEW3D_MT_select_EDIT_LATTICE(bpy.types.Menu):
	__space_type__ = "VIEW_3D"
	__label__ = "Select"

	def draw(self, context):
		layout = self.layout

		layout.itemO("view3d.select_border")

		layout.itemS()
		
		layout.itemO("lattice.select_all_toggle", text="Select/Deselect All")

class VIEW3D_MT_select_EDIT_ARMATURE(bpy.types.Menu):
	__space_type__ = "VIEW_3D"
	__label__ = "Select"

	def draw(self, context):
		layout = self.layout

		layout.itemO("view3d.select_border")

		layout.itemS()
		
		layout.itemO("armature.select_all_toggle", text="Select/Deselect All")
		layout.itemO("armature.select_inverse", text="Inverse")

		layout.itemS()
		
		layout.item_enumO("armature.select_hierarchy", "direction", 'PARENT')
		layout.item_enumO("armature.select_hierarchy", "direction", 'CHILD')
		
		layout.itemS()
		
		layout.view3d_select_armaturemenu()

class VIEW3D_MT_select_FACE(bpy.types.Menu):# XXX no matching enum
	__space_type__ = "VIEW_3D"
	__label__ = "Select"

	def draw(self, context):
		layout = self.layout

		layout.view3d_select_faceselmenu()

# ********** Object menu **********

class VIEW3D_MT_object(bpy.types.Menu):
	__space_type__ = "VIEW_3D"
	__context__ = "objectmode"
	__label__ = "Object"

	def draw(self, context):
		layout = self.layout

		layout.itemM("VIEW3D_MT_object_clear")
		layout.itemM("VIEW3D_MT_object_snap")
		
		layout.itemS()
		
		layout.itemO("anim.insert_keyframe_menu")
		layout.itemO("anim.delete_keyframe_v3d")
		
		layout.itemS()
		
		layout.itemO("object.duplicate")
		layout.item_booleanO("object.duplicate", "linked", True, text="Duplicate Linked")
		layout.itemO("object.delete")
		layout.itemO("object.proxy_make")
		
		layout.itemS()
		
		layout.itemM("VIEW3D_MT_object_parent")
		layout.itemM("VIEW3D_MT_object_track")
		layout.itemM("VIEW3D_MT_object_group")
		layout.itemM("VIEW3D_MT_object_constraints")
		
		layout.itemS()
		
		layout.itemO("object.join")
		
		layout.itemS()
		
		layout.itemM("VIEW3D_MT_object_show")
		
class VIEW3D_MT_object_clear(bpy.types.Menu):
	__space_type__ = "VIEW_3D"
	__label__ = "Clear"

	def draw(self, context):
		layout = self.layout
		
		layout.itemO("object.location_clear")
		layout.itemO("object.rotation_clear")
		layout.itemO("object.scale_clear")
		layout.itemO("object.origin_clear")
		
class VIEW3D_MT_object_snap(bpy.types.Menu):
	__space_type__ = "VIEW_3D"
	__label__ = "Snap"

	def draw(self, context):
		layout = self.layout
		
		layout.itemO("view3d.snap_selected_to_grid")
		layout.itemO("view3d.snap_selected_to_cursor")
		layout.itemO("view3d.snap_selected_to_center")
		
		layout.itemS()
		
		layout.itemO("view3d.snap_cursor_to_selected")
		layout.itemO("view3d.snap_cursor_to_grid")
		layout.itemO("view3d.snap_cursor_to_active")
		
class VIEW3D_MT_object_parent(bpy.types.Menu):
	__space_type__ = "VIEW_3D"
	__label__ = "Parent"

	def draw(self, context):
		layout = self.layout
		
		layout.itemO("object.parent_set")
		layout.itemO("object.parent_clear")
		
class VIEW3D_MT_object_track(bpy.types.Menu):
	__space_type__ = "VIEW_3D"
	__label__ = "Track"

	def draw(self, context):
		layout = self.layout
		
		layout.itemO("object.track_set")
		layout.itemO("object.track_clear")
		
class VIEW3D_MT_object_group(bpy.types.Menu):
	__space_type__ = "VIEW_3D"
	__label__ = "Group"

	def draw(self, context):
		layout = self.layout
		
		layout.itemO("group.group_create")
		layout.itemO("group.objects_remove")
		
		layout.itemS()
		
		layout.itemO("group.objects_add_active")
		layout.itemO("group.objects_remove_active")
		
class VIEW3D_MT_object_constraints(bpy.types.Menu):
	__space_type__ = "VIEW_3D"
	__label__ = "Constraints"

	def draw(self, context):
		layout = self.layout
		
		layout.itemO("object.constraint_add_with_targets")
		layout.itemO("object.constraints_clear")
		
class VIEW3D_MT_object_show(bpy.types.Menu):
	__space_type__ = "VIEW_3D"
	__label__ = "Show/Hide"

	def draw(self, context):
		layout = self.layout
		
		layout.itemO("object.restrictview_clear")
		layout.itemO("object.restrictview_set")
		layout.item_booleanO("object.restrictview_set", "unselected", True, text="Hide Unselected")

# ********** Sculpt menu **********	
	
class VIEW3D_MT_sculpt(bpy.types.Menu):
	__space_type__ = "VIEW_3D"
	__label__ = "Sculpt"

	def draw(self, context):
		layout = self.layout
		
		sculpt = context.tool_settings.sculpt
		brush = context.tool_settings.sculpt.brush
		
		layout.itemR(sculpt, "symmetry_x")
		layout.itemR(sculpt, "symmetry_y")
		layout.itemR(sculpt, "symmetry_z")
		layout.itemS()
		layout.itemR(sculpt, "lock_x")
		layout.itemR(sculpt, "lock_y")
		layout.itemR(sculpt, "lock_z")
		layout.itemS()
		layout.item_menu_enumO("brush.curve_preset", property="shape")
		layout.itemS()
		
		if brush.sculpt_tool != 'GRAB':
			layout.itemR(brush, "airbrush")
			
			if brush.sculpt_tool != 'LAYER':
				layout.itemR(brush, "anchored")
			
			if brush.sculpt_tool in ('DRAW', 'PINCH', 'INFLATE', 'LAYER', 'CLAY'):
				layout.itemR(brush, "flip_direction")

			if brush.sculpt_tool == 'LAYER':
				layout.itemR(brush, "persistent")
				layout.itemO("sculpt.set_persistent_base")

# ********** Edit Menus, suffix from ob.type **********

class VIEW3D_MT_edit_snap(bpy.types.Menu):
	__space_type__ = "VIEW_3D"
	__label__ = "Snap"

	def draw(self, context):
		layout = self.layout
		
		layout.itemO("view3d.snap_selected_to_grid")
		layout.itemO("view3d.snap_selected_to_cursor")
		layout.itemO("view3d.snap_selected_to_center")
		
		layout.itemS()
		
		layout.itemO("view3d.snap_cursor_to_selected")
		layout.itemO("view3d.snap_cursor_to_grid")
		layout.itemO("view3d.snap_cursor_to_active")

# Edit MESH
class VIEW3D_MT_edit_MESH(bpy.types.Menu):
	__space_type__ = "VIEW_3D"
	__label__ = "Mesh"

	def draw(self, context):
		layout = self.layout
		
		settings = context.tool_settings

		layout.itemO("ed.undo")
		layout.itemO("ed.redo")
		
		layout.itemS()
		
		layout.itemM("VIEW3D_MT_edit_snap")
		
		layout.itemS()
		
		layout.itemO("uv.mapping_menu")
		
		layout.itemS()
		
		layout.itemO("mesh.extrude")
		layout.itemO("mesh.duplicate")
		layout.itemO("mesh.delete")
		
		layout.itemS()
		
		layout.itemM("VIEW3D_MT_edit_MESH_vertices")
		layout.itemM("VIEW3D_MT_edit_MESH_edges")
		layout.itemM("VIEW3D_MT_edit_MESH_faces")
		layout.itemM("VIEW3D_MT_edit_MESH_normals")
		
		layout.itemS()
		
		layout.itemR(settings, "automerge_editing")
		layout.itemR(settings, "proportional_editing")
		layout.item_menu_enumR(settings, "proportional_editing_falloff")
		
		layout.itemS()
		
		layout.itemM("VIEW3D_MT_edit_MESH_showhide")

class VIEW3D_MT_edit_MESH_vertices(bpy.types.Menu):
	__space_type__ = "VIEW_3D"
	__label__ = "Vertices"

	def draw(self, context):
		layout = self.layout
		
		layout.itemO("mesh.merge")
		layout.itemO("mesh.rip")
		layout.itemO("mesh.split")
		layout.itemO("mesh.separate")

		layout.itemS()
		
		layout.itemO("mesh.vertices_smooth")
		layout.itemO("mesh.remove_doubles")
		
class VIEW3D_MT_edit_MESH_edges(bpy.types.Menu):
	__space_type__ = "VIEW_3D"
	__label__ = "Edges"

	def draw(self, context):
		layout = self.layout

		layout.itemO("mesh.edge_face_add")
		layout.itemO("mesh.subdivide")
		layout.item_floatO("mesh.subdivide", "smoothness", 1.0, text="Subdivide Smooth")

		layout.itemS()
		
		layout.itemO("mesh.mark_seam")
		layout.item_booleanO("mesh.mark_seam", "clear", True, text="Clear Seam")
		
		layout.itemS()
		
		layout.itemO("mesh.mark_sharp")
		layout.item_booleanO("mesh.mark_sharp", "clear", True, text="Clear Sharp")
		
		layout.itemS()
		
		layout.item_enumO("mesh.edge_rotate", "direction", 'CW', text="Rotate Edge CW")
		layout.item_enumO("mesh.edge_rotate", "direction", 'CCW', text="Rotate Edge CCW")
		
class VIEW3D_MT_edit_MESH_faces(bpy.types.Menu):
	__space_type__ = "VIEW_3D"
	__label__ = "Faces"

	def draw(self, context):
		layout = self.layout

		layout.itemO("mesh.edge_face_add")
		layout.itemO("mesh.fill")
		layout.itemO("mesh.beauty_fill")

		layout.itemS()
		
		layout.itemO("mesh.quads_convert_to_tris")
		layout.itemO("mesh.tris_convert_to_quads")
		layout.itemO("mesh.edge_flip")
		
		layout.itemS()
		
		layout.itemO("mesh.faces_shade_smooth")
		layout.itemO("mesh.faces_shade_flat")

class VIEW3D_MT_edit_MESH_normals(bpy.types.Menu):
	__space_type__ = "VIEW_3D"
	__label__ = "Normals"

	def draw(self, context):
		layout = self.layout

		layout.itemO("mesh.normals_make_consistent", text="Recalculate Outside")
		layout.item_booleanO("mesh.normals_make_consistent", "inside", True, text="Recalculate Inside")

		layout.itemS()
		
		layout.itemO("mesh.flip_normals")
		
class VIEW3D_MT_edit_MESH_showhide(bpy.types.Menu):
	__space_type__ = "VIEW_3D"
	__label__ = "Show/Hide"

	def draw(self, context):
		layout = self.layout

		layout.itemO("mesh.reveal")
		layout.itemO("mesh.hide")
		layout.item_booleanO("mesh.hide", "unselected", True, text="Hide Unselected")

# Edit CURVE

# draw_CURVE is used by VIEW3D_MT_edit_CURVE and VIEW3D_MT_edit_SURFACE
def draw_CURVE(self, context):
	layout = self.layout
	
	settings = context.tool_settings

	layout.itemM("VIEW3D_MT_edit_snap")
	
	layout.itemS()
	
	layout.itemO("curve.extrude")
	layout.itemO("curve.duplicate")
	layout.itemO("curve.separate")
	layout.itemO("curve.make_segment")
	layout.itemO("curve.cyclic_toggle")
	layout.itemO("curve.delete")
	
	layout.itemS()
	
	layout.itemM("VIEW3D_MT_edit_CURVE_ctrlpoints")
	layout.itemM("VIEW3D_MT_edit_CURVE_segments")
	
	layout.itemS()
	
	layout.itemR(settings, "proportional_editing")
	layout.item_menu_enumR(settings, "proportional_editing_falloff")
	
	layout.itemS()
	
	layout.itemM("VIEW3D_MT_edit_CURVE_showhide")

class VIEW3D_MT_edit_CURVE(bpy.types.Menu):
	__space_type__ = "VIEW_3D"
	__label__ = "Curve"

	draw = draw_CURVE
	
class VIEW3D_MT_edit_CURVE_ctrlpoints(bpy.types.Menu):
	__space_type__ = "VIEW_3D"
	__label__ = "Control Points"

	def draw(self, context):
		layout = self.layout
		
		edit_object = context.edit_object
		
		if edit_object.type == 'CURVE':
			layout.item_enumO("tfm.transform", "mode", 'TILT')
			layout.itemO("curve.tilt_clear")
			layout.itemO("curve.separate")
			
			layout.itemS()
			
			layout.item_menu_enumO("curve.handle_type_set", "type")
		
class VIEW3D_MT_edit_CURVE_segments(bpy.types.Menu):
	__space_type__ = "VIEW_3D"
	__label__ = "Segments"

	def draw(self, context):
		layout = self.layout
		
		layout.itemO("curve.subdivide")
		layout.itemO("curve.switch_direction")

class VIEW3D_MT_edit_CURVE_showhide(bpy.types.Menu):
	__space_type__ = "VIEW_3D"
	__label__ = "Show/Hide"

	def draw(self, context):
		layout = self.layout
		
		layout.itemO("curve.reveal")
		layout.itemO("curve.hide")
		layout.item_booleanO("curve.hide", "unselected", True, text="Hide Unselected")

# Edit SURFACE
class VIEW3D_MT_edit_SURFACE(bpy.types.Menu):
	__space_type__ = "VIEW_3D"
	__label__ = "Surface"

	draw = draw_CURVE

# Edit TEXT
class VIEW3D_MT_edit_TEXT(bpy.types.Menu):
	__space_type__ = "VIEW_3D"
	__label__ = "Text"

	def draw(self, context):
		layout = self.layout
		
		layout.itemO("font.file_paste")
		
		layout.itemS()
		
		layout.itemM("VIEW3D_MT_edit_TEXT_chars")

class VIEW3D_MT_edit_TEXT_chars(bpy.types.Menu):
	__space_type__ = "VIEW_3D"
	__label__ = "Special Characters"

	def draw(self, context):
		layout = self.layout
		
		layout.item_stringO("font.text_insert", "text", b'\xC2\xA9'.decode(), text="Copyright|Alt C")
		layout.item_stringO("font.text_insert", "text", b'\xC2\xAE'.decode(), text="Registered Trademark|Alt R")
		
		layout.itemS()
		
		layout.item_stringO("font.text_insert", "text", b'\xC2\xB0'.decode(), text="Degree Sign|Alt G")
		layout.item_stringO("font.text_insert", "text", b'\xC3\x97'.decode(), text="Multiplication Sign|Alt x")
		layout.item_stringO("font.text_insert", "text", b'\xC2\x8A'.decode(), text="Circle|Alt .")
		layout.item_stringO("font.text_insert", "text", b'\xC2\xB9'.decode(), text="Superscript 1|Alt 1")
		layout.item_stringO("font.text_insert", "text", b'\xC2\xB2'.decode(), text="Superscript 2|Alt 2")
		layout.item_stringO("font.text_insert", "text", b'\xC2\xB3'.decode(), text="Superscript 3|Alt 3")
		layout.item_stringO("font.text_insert", "text", b'\xC2\xBB'.decode(), text="Double >>|Alt >")
		layout.item_stringO("font.text_insert", "text", b'\xC2\xAB'.decode(), text="Double <<|Alt <")
		layout.item_stringO("font.text_insert", "text", b'\xE2\x80\xB0'.decode(), text="Promillage|Alt %")
		
		layout.itemS()
		
		layout.item_stringO("font.text_insert", "text", b'\xC2\xA4'.decode(), text="Dutch Florin|Alt F")
		layout.item_stringO("font.text_insert", "text", b'\xC2\xA3'.decode(), text="British Pound|Alt L")
		layout.item_stringO("font.text_insert", "text", b'\xC2\xA5'.decode(), text="Japanese Yen|Alt Y")
		
		layout.itemS()
		
		layout.item_stringO("font.text_insert", "text", b'\xC3\x9F'.decode(), text="German S|Alt S")
		layout.item_stringO("font.text_insert", "text", b'\xC2\xBF'.decode(), text="Spanish Question Mark|Alt ?")
		layout.item_stringO("font.text_insert", "text", b'\xC2\xA1'.decode(), text="Spanish Exclamation Mark|Alt !")

# Edit META
class VIEW3D_MT_edit_META(bpy.types.Menu):
	__space_type__ = "VIEW_3D"
	__label__ = "Metaball"

	def draw(self, context):
		layout = self.layout
		
		settings = context.tool_settings

		layout.itemO("ed.undo")
		layout.itemO("ed.redo")
		
		layout.itemS()
		
		layout.itemM("VIEW3D_MT_edit_snap")
		
		layout.itemS()
		
		layout.itemO("mball.delete_metaelems")
		layout.itemO("mball.duplicate_metaelems")
		
		layout.itemS()
		
		layout.itemR(settings, "proportional_editing")
		layout.item_menu_enumR(settings, "proportional_editing_falloff")
		
		layout.itemS()
		
		layout.itemM("VIEW3D_MT_edit_META_showhide")

class VIEW3D_MT_edit_META_showhide(bpy.types.Menu):
	__space_type__ = "VIEW_3D"
	__label__ = "Show/Hide"

	def draw(self, context):
		layout = self.layout
		
		layout.itemO("mball.reveal_metaelems")
		layout.itemO("mball.hide_metaelems")
		layout.item_booleanO("mball.hide_metaelems", "unselected", True, text="Hide Unselected")

# Edit LATTICE
class VIEW3D_MT_edit_LATTICE(bpy.types.Menu):
	__space_type__ = "VIEW_3D"
	__label__ = "Lattice"

	def draw(self, context):
		layout = self.layout
		
		settings = context.tool_settings

		layout.itemM("VIEW3D_MT_edit_snap")
		
		layout.itemS()
		
		layout.itemO("lattice.make_regular")
		
		layout.itemS()
		
		layout.itemR(settings, "proportional_editing")
		layout.item_menu_enumR(settings, "proportional_editing_falloff")

# Edit ARMATURE
class VIEW3D_MT_edit_ARMATURE(bpy.types.Menu):
	__space_type__ = "VIEW_3D"
	__label__ = "Armature"

	def draw(self, context):
		layout = self.layout
		
		edit_object = context.edit_object
		arm = edit_object.data
		
		layout.itemM("VIEW3D_MT_edit_snap")
		layout.itemM("VIEW3D_MT_edit_ARMATURE_roll")
		
		if arm.drawtype == 'ENVELOPE':
			layout.item_enumO("tfm.transform", "mode", 'BONESIZE', text="Scale Envelope Distance")
		else:
			layout.item_enumO("tfm.transform", "mode", 'BONESIZE', text="Scale B-Bone Width")
				
		layout.itemS()
		
		layout.itemO("armature.extrude")
		
		if arm.x_axis_mirror:
			layout.item_booleanO("armature.extrude", "forked", True, text="Extrude Forked")
		
		layout.itemO("armature.duplicate")
		layout.itemO("armature.merge")
		layout.itemO("armature.fill")
		layout.itemO("armature.delete")
		layout.itemO("armature.separate")

		layout.itemS()

		layout.itemO("armature.subdivide_simple")
		layout.itemO("armature.subdivide_multi")
		
		layout.itemS()

		layout.item_enumO("armature.autoside_names", "axis", 'XAXIS', text="AutoName Left/Right")
		layout.item_enumO("armature.autoside_names", "axis", 'YAXIS', text="AutoName Front/Back")
		layout.item_enumO("armature.autoside_names", "axis", 'ZAXIS', text="AutoName Top/Bottom")
		layout.itemO("armature.flip_names")

		layout.itemS()

		layout.itemO("armature.armature_layers")
		layout.itemO("armature.bone_layers")

		layout.itemS()

		layout.itemM("VIEW3D_MT_edit_ARMATURE_parent")

		layout.itemS()

		layout.item_menu_enumO("armature.flags_set", "mode", text="Bone Settings")

class VIEW3D_MT_edit_ARMATURE_parent(bpy.types.Menu):
	__space_type__ = "VIEW_3D"
	__label__ = "Parent"

	def draw(self, context):
		layout = self.layout
		
		layout.itemO("armature.parent_set")
		layout.itemO("armature.parent_clear")

class VIEW3D_MT_edit_ARMATURE_roll(bpy.types.Menu):
	__space_type__ = "VIEW_3D"
	__label__ = "Bone Roll"

	def draw(self, context):
		layout = self.layout
		
		layout.item_enumO("armature.calculate_roll", "type", 'GLOBALUP', text="Clear Roll (Z-Axis Up)")
		layout.item_enumO("armature.calculate_roll", "type", 'CURSOR', text="Roll to Cursor")
		
		layout.itemS()
		
		layout.item_enumO("tfm.transform", "mode", 'BONE_ROLL', text="Set Roll")

# ********** Panel **********

class VIEW3D_PT_3dview_properties(bpy.types.Panel):
	__space_type__ = "VIEW_3D"
	__region_type__ = "UI"
	__label__ = "View"

	def poll(self, context):
		view = context.space_data
		return (view)

	def draw(self, context):
		layout = self.layout
		
		view = context.space_data
		scene = context.scene
		
		col = layout.column()
		col.itemR(view, "camera")
		col.itemR(view, "lens")
		
		layout.itemL(text="Clip:")
		col = layout.column(align=True)
		col.itemR(view, "clip_start", text="Start")
		col.itemR(view, "clip_end", text="End")
		
		layout.itemL(text="Grid:")
		col = layout.column(align=True)
		col.itemR(view, "grid_lines", text="Lines")
		col.itemR(view, "grid_spacing", text="Spacing")
		col.itemR(view, "grid_subdivisions", text="Subdivisions")
		
		layout.column().itemR(scene, "cursor_location", text="3D Cursor:")
		
class VIEW3D_PT_3dview_display(bpy.types.Panel):
	__space_type__ = "VIEW_3D"
	__region_type__ = "UI"
	__label__ = "Display"

	def poll(self, context):
		view = context.space_data
		return (view)

	def draw(self, context):
		layout = self.layout
		view = context.space_data
		
		col = layout.column()
		col.itemR(view, "display_floor", text="Grid Floor")
		col.itemR(view, "display_x_axis", text="X Axis")
		col.itemR(view, "display_y_axis", text="Y Axis")
		col.itemR(view, "display_z_axis", text="Z Axis")
		col.itemR(view, "outline_selected")
		col.itemR(view, "all_object_centers")
		col.itemR(view, "relationship_lines")
		col.itemR(view, "textured_solid")
		
		layout.itemS()
		
		layout.itemO("screen.region_foursplit")
		
		col = layout.column()
		col.itemR(view, "lock_rotation")
		col.itemR(view, "box_preview")
		col.itemR(view, "box_clip")
	
class VIEW3D_PT_background_image(bpy.types.Panel):
	__space_type__ = "VIEW_3D"
	__region_type__ = "UI"
	__label__ = "Background Image"
	__default_closed__ = True

	def poll(self, context):
		view = context.space_data
		bg = context.space_data.background_image
		return (view)

	def draw_header(self, context):
		layout = self.layout
		view = context.space_data

		layout.itemR(view, "display_background_image", text="")

	def draw(self, context):
		layout = self.layout
		
		view = context.space_data
		bg = view.background_image

		if bg:
			layout.active = view.display_background_image

			col = layout.column()
			col.itemR(bg, "image", text="")
			#col.itemR(bg, "image_user")
			col.itemR(bg, "size")
			col.itemR(bg, "transparency", slider=True)
			col.itemL(text="Offset:")
			
			col = layout.column(align=True)
			col.itemR(bg, "x_offset", text="X")
			col.itemR(bg, "y_offset", text="Y")

bpy.types.register(VIEW3D_HT_header) # Header

bpy.types.register(VIEW3D_MT_view) #View Menus
bpy.types.register(VIEW3D_MT_view_navigation)

bpy.types.register(VIEW3D_MT_select_OBJECT) # Select Menus
bpy.types.register(VIEW3D_MT_select_POSE)
bpy.types.register(VIEW3D_MT_select_PARTICLE)
bpy.types.register(VIEW3D_MT_select_EDIT_MESH)
bpy.types.register(VIEW3D_MT_select_EDIT_CURVE)
bpy.types.register(VIEW3D_MT_select_EDIT_SURFACE)
bpy.types.register(VIEW3D_MT_select_EDIT_METABALL)
bpy.types.register(VIEW3D_MT_select_EDIT_LATTICE)
bpy.types.register(VIEW3D_MT_select_EDIT_ARMATURE)
bpy.types.register(VIEW3D_MT_select_FACE) # XXX todo

bpy.types.register(VIEW3D_MT_object) # Object Menu
bpy.types.register(VIEW3D_MT_object_clear)
bpy.types.register(VIEW3D_MT_object_snap)
bpy.types.register(VIEW3D_MT_object_parent)
bpy.types.register(VIEW3D_MT_object_track)
bpy.types.register(VIEW3D_MT_object_group)
bpy.types.register(VIEW3D_MT_object_constraints)
bpy.types.register(VIEW3D_MT_object_show)

bpy.types.register(VIEW3D_MT_sculpt) # Sculpt Menu

bpy.types.register(VIEW3D_MT_edit_snap) # Edit Menus

bpy.types.register(VIEW3D_MT_edit_MESH)
bpy.types.register(VIEW3D_MT_edit_MESH_vertices)
bpy.types.register(VIEW3D_MT_edit_MESH_edges)
bpy.types.register(VIEW3D_MT_edit_MESH_faces)
bpy.types.register(VIEW3D_MT_edit_MESH_normals)
bpy.types.register(VIEW3D_MT_edit_MESH_showhide)

bpy.types.register(VIEW3D_MT_edit_CURVE)
bpy.types.register(VIEW3D_MT_edit_CURVE_ctrlpoints)
bpy.types.register(VIEW3D_MT_edit_CURVE_segments)
bpy.types.register(VIEW3D_MT_edit_CURVE_showhide)

bpy.types.register(VIEW3D_MT_edit_SURFACE)

bpy.types.register(VIEW3D_MT_edit_TEXT)
bpy.types.register(VIEW3D_MT_edit_TEXT_chars)

bpy.types.register(VIEW3D_MT_edit_META)
bpy.types.register(VIEW3D_MT_edit_META_showhide)

bpy.types.register(VIEW3D_MT_edit_LATTICE)

bpy.types.register(VIEW3D_MT_edit_ARMATURE)
bpy.types.register(VIEW3D_MT_edit_ARMATURE_parent)
bpy.types.register(VIEW3D_MT_edit_ARMATURE_roll)

bpy.types.register(VIEW3D_PT_3dview_properties) # Panels
bpy.types.register(VIEW3D_PT_3dview_display)
bpy.types.register(VIEW3D_PT_background_image)
