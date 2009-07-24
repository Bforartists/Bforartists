
import bpy

# ********** default tools for objectmode ****************

class View3DPanel(bpy.types.Panel):
	__space_type__ = "VIEW_3D"
	__region_type__ = "TOOLS"
	__context__ = "objectmode"

class VIEW3D_PT_tools_objectmode(View3DPanel):
	__idname__ = "VIEW3D_PT_tools_objectmode"
	__label__ = "Object Tools"

	def draw(self, context):
		layout = self.layout
		
		layout.itemL(text="Transform:")
		
		col = layout.column(align=True)
		col.itemO("tfm.translate")
		col.itemO("tfm.rotate")
		col.itemO("tfm.resize", text="Scale")
		
		layout.itemL(text="Object:")
		
		col = layout.column(align=True)
		col.itemO("object.duplicate")
		col.itemO("object.delete")
		
		layout.itemL(text="Keyframes:")
		
		col = layout.column(align=True)
		col.itemO("anim.insert_keyframe_menu", text="Insert")
		col.itemO("anim.delete_keyframe_v3d", text="Remove")

# ********** default tools for editmode_mesh ****************

class View3DPanel(bpy.types.Panel):
	__space_type__ = "VIEW_3D"
	__region_type__ = "TOOLS"
	__context__ = "editmode_mesh"

class VIEW3D_PT_tools_editmode_mesh(View3DPanel):
	__idname__ = "VIEW3D_PT_tools_editmode_mesh"
	__label__ = "Mesh Tools"

	def draw(self, context):
		layout = self.layout
		
		layout.itemL(text="Transform:")
		
		col = layout.column(align=True)
		col.itemO("tfm.translate")
		col.itemO("tfm.rotate")
		col.itemO("tfm.resize", text="Scale")
		
		layout.itemL(text="Mesh:")
		
		col = layout.column(align=True)
		col.itemO("mesh.duplicate")
		col.itemO("mesh.delete")
		
		layout.itemL(text="Modeling:")
		
		col = layout.column(align=True)
		col.itemO("mesh.extrude")
		col.itemO("mesh.subdivide")
		col.itemO("mesh.spin")
		col.itemO("mesh.screw")
		
		layout.itemL(text="Shading:")
		
		col = layout.column(align=True)
		col.itemO("mesh.faces_shade_smooth", text="Smooth")
		col.itemO("mesh.faces_shade_flat", text="Flat")
		
		layout.itemL(text="UV Mapping:")
		
		col = layout.column(align=True)
		col.itemO("uv.mapping_menu", text="Unwrap")
		col.itemO("mesh.uvs_rotate")
		col.itemO("mesh.uvs_mirror")

# ********** default tools for editmode_curve ****************

class View3DPanel(bpy.types.Panel):
	__space_type__ = "VIEW_3D"
	__region_type__ = "TOOLS"
	__context__ = "editmode_curve"

class VIEW3D_PT_tools_editmode_curve(View3DPanel):
	__idname__ = "VIEW3D_PT_tools_editmode_curve"
	__label__ = "Curve Tools"

	def draw(self, context):
		layout = self.layout
		
		layout.itemL(text="Transform:")
		
		col = layout.column(align=True)
		col.itemO("tfm.translate")
		col.itemO("tfm.rotate")
		col.itemO("tfm.resize", text="Scale")
		
		layout.itemL(text="Curve:")

		col = layout.column(align=True)
		col.itemO("curve.duplicate")
		col.itemO("curve.delete")
		col.itemO("curve.cyclic_toggle")
		col.itemO("curve.switch_direction")
		
		layout.itemL(text="Modeling:")

		col = layout.column(align=True)
		col.itemO("curve.extrude")
		col.itemO("curve.subdivide")

# ********** default tools for editmode_surface ****************

class View3DPanel(bpy.types.Panel):
	__space_type__ = "VIEW_3D"
	__region_type__ = "TOOLS"
	__context__ = "editmode_surface"

class VIEW3D_PT_tools_editmode_surface(View3DPanel):
	__idname__ = "VIEW3D_PT_tools_editmode_surface"
	__label__ = "Surface Tools"

	def draw(self, context):
		layout = self.layout
		
		layout.itemL(text="Transform:")

		col = layout.column(align=True)
		col.itemO("tfm.translate")
		col.itemO("tfm.rotate")
		col.itemO("tfm.resize", text="Scale")
		
		layout.itemL(text="Curve:")

		col = layout.column(align=True)
		col.itemO("curve.duplicate")
		col.itemO("curve.delete")
		col.itemO("curve.cyclic_toggle")
		col.itemO("curve.switch_direction")
		
		layout.itemL(text="Modeling:")

		col = layout.column(align=True)
		col.itemO("curve.extrude")
		col.itemO("curve.subdivide")

# ********** default tools for editmode_text ****************

class View3DPanel(bpy.types.Panel):
	__space_type__ = "VIEW_3D"
	__region_type__ = "TOOLS"
	__context__ = "editmode_text"

class VIEW3D_PT_tools_editmode_text(View3DPanel):
	__idname__ = "VIEW3D_PT_tools_editmode_text"
	__label__ = "Text Tools"

	def draw(self, context):
		layout = self.layout

		col = layout.column(align=True)
		col.itemO("font.text_copy", text="Copy")
		col.itemO("font.text_paste", text="Paste")
		
		col = layout.column()
		col.itemO("font.case_set")
		col.itemO("font.style_toggle")

# ********** default tools for editmode_armature ****************

class View3DPanel(bpy.types.Panel):
	__space_type__ = "VIEW_3D"
	__region_type__ = "TOOLS"
	__context__ = "editmode_armature"

class VIEW3D_PT_tools_editmode_armature(View3DPanel):
	__idname__ = "VIEW3D_PT_tools_editmode_armature"
	__label__ = "Armature Tools"

	def draw(self, context):
		layout = self.layout
		
		layout.itemL(text="Transform:")
		
		col = layout.column(align=True)
		col.itemO("tfm.translate")
		col.itemO("tfm.rotate")
		col.itemO("tfm.resize", text="Scale")
		
		layout.itemL(text="Bones:")

		col = layout.column(align=True)
		col.itemO("armature.bone_primitive_add", text="Add")
		col.itemO("armature.duplicate_selected", text="Duplicate")
		col.itemO("armature.delete", text="Delete")
		
		layout.itemL(text="Modeling:")
		layout.itemO("armature.extrude")

# ********** default tools for editmode_mball ****************

class View3DPanel(bpy.types.Panel):
	__space_type__ = "VIEW_3D"
	__region_type__ = "TOOLS"
	__context__ = "editmode_mball"

class VIEW3D_PT_tools_editmode_mball(View3DPanel):
	__idname__ = "VIEW3D_PT_tools_editmode_mball"
	__label__ = "Meta Tools"

	def draw(self, context):
		layout = self.layout
		
		layout.itemL(text="Transform:")
		
		col = layout.column(align=True)
		col.itemO("tfm.translate")
		col.itemO("tfm.rotate")
		col.itemO("tfm.resize", text="Scale")

# ********** default tools for editmode_lattice ****************

class View3DPanel(bpy.types.Panel):
	__space_type__ = "VIEW_3D"
	__region_type__ = "TOOLS"
	__context__ = "editmode_lattice"

class VIEW3D_PT_tools_editmode_lattice(View3DPanel):
	__idname__ = "VIEW3D_PT_tools_editmode_lattice"
	__label__ = "Lattice Tools"

	def draw(self, context):
		layout = self.layout
		
		layout.itemL(text="Transform:")

		col = layout.column(align=True)
		col.itemO("tfm.translate")
		col.itemO("tfm.rotate")
		col.itemO("tfm.resize", text="Scale")

# ********** default tools for posemode ****************

class View3DPanel(bpy.types.Panel):
	__space_type__ = "VIEW_3D"
	__region_type__ = "TOOLS"
	__context__ = "posemode"

class VIEW3D_PT_tools_posemode(View3DPanel):
	__idname__ = "VIEW3D_PT_tools_posemode"
	__label__ = "Pose Tools"

	def draw(self, context):
		layout = self.layout
		
		layout.itemL(text="Transform:")

		col = layout.column(align=True)
		col.itemO("tfm.translate")
		col.itemO("tfm.rotate")
		col.itemO("tfm.resize", text="Scale")
		
		layout.itemL(text="Bones:")

		col = layout.column(align=True)
		col.itemO("pose.hide", text="Hide")
		col.itemO("pose.reveal", text="Reveal")
		
		layout.itemL(text="Keyframes:")
		
		col = layout.column(align=True)
		col.itemO("anim.insert_keyframe_menu", text="Insert")
		col.itemO("anim.delete_keyframe_v3d", text="Remove")
		
		layout.itemL(text="Pose:")
		
		col = layout.column(align=True)
		col.itemO("pose.copy", text="Copy")
		col.itemO("pose.paste", text="Paste")
		
		layout.itemL(text="Library:")
		
		col = layout.column(align=True)
		col.itemO("poselib.pose_add", text="Add")
		col.itemO("poselib.pose_remove", text="Remove")

# ********** default tools for paint modes ****************

class VIEW3D_PT_tools_brush(bpy.types.Panel):
	__space_type__ = "VIEW_3D"
	__region_type__ = "TOOLS"
	__label__ = "Brush"

	def brush_src(self, context):
		ts = context.tool_settings
		if context.sculpt_object:
			return ts.sculpt
		elif context.vpaint_object:
			return ts.vpaint
		elif context.wpaint_object:
			return ts.wpaint
		elif context.tpaint_object:
			return ts.tpaint
		return False

	def poll(self, context):
		return self.brush_src(context)

	def draw(self, context):
		src = self.brush_src(context)
		brush = src.brush
		layout = self.layout

		layout.split().row().template_ID(src, "brush")

		if context.sculpt_object:
			layout.column().itemR(brush, "sculpt_tool", expand=True)

		split = layout.split()
		
		col = split.column()
		row = col.row(align=True)
		row.itemR(brush, "size", slider=True)
		row.itemR(brush, "size_pressure", toggle=True, icon='ICON_BRUSH_DATA', text="")
		
		if context.wpaint_object:
			col.itemR(context.tool_settings, "vertex_group_weight", text="Weight", slider=True)
			
		col.itemR(brush, "strength", slider=True)
		row = col.row(align=True)
		row.itemR(brush, "falloff", slider=True)
		row.itemR(brush, "falloff_pressure", toggle=True, icon='ICON_BRUSH_DATA', text="")
		
		if context.vpaint_object:
			col.itemR(brush, "color", text="")
		if context.tpaint_object:
			row = col.row(align=True)
			row.itemR(brush, "clone_opacity", slider=True, text=Opacity)
			row.itemR(brush, "opacity_pressure", toggle=True, icon='ICON_BRUSH_DATA', text="")
		
		row = col.row(align=True)
		row.itemR(brush, "space", text="")
		rowsub = row.row(align=True)
		rowsub.active = brush.space
		rowsub.itemR(brush, "spacing", text="Spacing", slider=True)
		rowsub.itemR(brush, "spacing_pressure", toggle=True, icon='ICON_BRUSH_DATA', text="")

		split = layout.split()
		col = split.column()
		col.itemR(brush, "airbrush")
		col.itemR(brush, "anchored")
		col.itemR(brush, "rake")

class VIEW3D_PT_tools_brush_curve(bpy.types.Panel):
	__space_type__ = "VIEW_3D"
	__region_type__ = "TOOLS"
	__label__ = "Curve"

	def brush_src(self, context):
		ts = context.tool_settings
		if context.sculpt_object:
			return ts.sculpt
		elif context.vpaint_object:
			return ts.vpaint
		elif context.wpaint_object:
			return ts.wpaint
		elif context.tpaint_object:
			return ts.tpaint
		return False

	def poll(self, context):
		return self.brush_src(context)

	def draw(self, context):
		src = self.brush_src(context)
		brush = src.brush
		layout = self.layout

		split = layout.split()
		split.template_curve_mapping(brush.curve)
		
class VIEW3D_PT_sculpt_options(bpy.types.Panel):
	__space_type__ = "VIEW_3D"
	__region_type__ = "TOOLS"
	__label__ = "Options"

	def poll(self, context):
		return context.sculpt_object

	def draw(self, context):
		layout = self.layout
		sculpt = context.tool_settings.sculpt

		col = layout.column()
		col.itemR(sculpt, "partial_redraw", text="Partial Refresh")
		col.itemR(sculpt, "show_brush")

		split = self.layout.split()
		
		col = split.column()
		col.itemL(text="Symmetry:")
		col.itemR(sculpt, "symmetry_x", text="X")
		col.itemR(sculpt, "symmetry_y", text="Y")
		col.itemR(sculpt, "symmetry_z", text="Z")
		
		col = split.column()
		col.itemL(text="Lock:")
		col.itemR(sculpt, "lock_x", text="X")
		col.itemR(sculpt, "lock_y", text="Y")
		col.itemR(sculpt, "lock_z", text="Z")

# ********** default tools for weightpaint ****************

class View3DPanel(bpy.types.Panel):
	__space_type__ = "VIEW_3D"
	__region_type__ = "TOOLS"
	__context__ = "weightpaint"

class VIEW3D_PT_weightpaint_options(View3DPanel):
	__idname__ = "VIEW3D_PT_tools_weightpaint"
	__label__ = "Options"

	def draw(self, context):
		layout = self.layout
		wpaint = context.tool_settings.wpaint

		col = layout.column()
		col.itemL(text="Blend:")
		col.itemR(wpaint, "mode", text="")
		col.itemR(wpaint, "all_faces")
		col.itemR(wpaint, "normals")
		col.itemR(wpaint, "spray")
		col.itemR(wpaint, "vertex_dist", text="Distance")

# Commented out because the Apply button isn't an operator yet, making these settings useless
#		col.itemL(text="Gamma:")
#		col.itemR(wpaint, "gamma", text="")
#		col.itemL(text="Multiply:")
#		col.itemR(wpaint, "mul", text="")


# ********** default tools for vertexpaint ****************

class View3DPanel(bpy.types.Panel):
	__space_type__ = "VIEW_3D"
	__region_type__ = "TOOLS"
	__context__ = "vertexpaint"

class VIEW3D_PT_vertexpaint_options(View3DPanel):
	__idname__ = "VIEW3D_PT_vertexpaintoptions"
	__label__ = "Options"

	def draw(self, context):
		layout = self.layout
		vpaint = context.tool_settings.vpaint

		col = layout.column()
		col.itemL(text="Blend:")
		col.itemR(vpaint, "mode", text="")
		col.itemR(vpaint, "all_faces")
		col.itemR(vpaint, "normals")
		col.itemR(vpaint, "spray")
		col.itemR(vpaint, "vertex_dist", text="Distance")
# Commented out because the Apply button isn't an operator yet, making these settings useless
#		col.itemL(text="Gamma:")
#		col.itemR(vpaint, "gamma", text="")
#		col.itemL(text="Multiply:")
#		col.itemR(vpaint, "mul", text="")


# ********** default tools for texturepaint ****************

class View3DPanel(bpy.types.Panel):
	__space_type__ = "VIEW_3D"
	__region_type__ = "TOOLS"
	__context__ = "texturepaint"

class VIEW3D_PT_tools_texturepaint(View3DPanel):
	__idname__ = "VIEW3D_PT_tools_texturepaint"
	__label__ = "Texture Paint Tools"

	def draw(self, context):
		layout = self.layout

		layout.itemL(text="Nothing yet")
		

bpy.types.register(VIEW3D_PT_tools_objectmode)
bpy.types.register(VIEW3D_PT_tools_editmode_mesh)
bpy.types.register(VIEW3D_PT_tools_editmode_curve)
bpy.types.register(VIEW3D_PT_tools_editmode_surface)
bpy.types.register(VIEW3D_PT_tools_editmode_text)
bpy.types.register(VIEW3D_PT_tools_editmode_armature)
bpy.types.register(VIEW3D_PT_tools_editmode_mball)
bpy.types.register(VIEW3D_PT_tools_editmode_lattice)
bpy.types.register(VIEW3D_PT_tools_posemode)
bpy.types.register(VIEW3D_PT_tools_brush)
bpy.types.register(VIEW3D_PT_tools_brush_curve)
bpy.types.register(VIEW3D_PT_sculpt_options)
bpy.types.register(VIEW3D_PT_vertexpaint_options)
bpy.types.register(VIEW3D_PT_weightpaint_options)
bpy.types.register(VIEW3D_PT_tools_texturepaint)
