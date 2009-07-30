	
import bpy

class MaterialButtonsPanel(bpy.types.Panel):
	__space_type__ = "BUTTONS_WINDOW"
	__region_type__ = "WINDOW"
	__context__ = "material"
	# COMPAT_ENGINES must be defined in each subclass, external engines can add themselves here

	def poll(self, context):
		return (context.material) and (context.scene.render_data.engine in self.COMPAT_ENGINES)

class MATERIAL_PT_preview(MaterialButtonsPanel):
	__label__ = "Preview"
	COMPAT_ENGINES = set(['BLENDER_RENDER', 'BLENDER_GAME'])

	def draw(self, context):
		layout = self.layout
		
		mat = context.material
		
		layout.template_preview(mat)
		
class MATERIAL_PT_context_material(MaterialButtonsPanel):
	__show_header__ = False
	COMPAT_ENGINES = set(['BLENDER_RENDER', 'BLENDER_GAME'])

	def poll(self, context):
		# An exception, dont call the parent poll func because
		# this manages materials for all engine types
		
		return (context.object) and (context.scene.render_data.engine in self.COMPAT_ENGINES)

	def draw(self, context):
		layout = self.layout
		
		mat = context.material
		ob = context.object
		slot = context.material_slot
		space = context.space_data

		if ob:
			row = layout.row()

			row.template_list(ob, "materials", ob, "active_material_index", rows=2)

			col = row.column(align=True)
			col.itemO("object.material_slot_add", icon="ICON_ZOOMIN", text="")
			col.itemO("object.material_slot_remove", icon="ICON_ZOOMOUT", text="")

			if context.edit_object:
				row = layout.row(align=True)
				row.itemO("object.material_slot_assign", text="Assign")
				row.itemO("object.material_slot_select", text="Select")
				row.itemO("object.material_slot_deselect", text="Deselect")

		split = layout.split(percentage=0.65)

		if ob:
			split.template_ID(ob, "active_material", new="material.new")
			row = split.row()
			if slot:
				row.itemR(slot, "link", expand=True)
			else:
				row.itemL()
		elif mat:
			split.template_ID(space, "pin_id")
			split.itemS()
	
class MATERIAL_PT_material(MaterialButtonsPanel):
	__idname__= "MATERIAL_PT_material"
	__label__ = "Shading"
	COMPAT_ENGINES = set(['BLENDER_RENDER', 'BLENDER_GAME'])

	def draw(self, context):
		layout = self.layout
		
		mat = context.material
		ob = context.object
		slot = context.material_slot
		space = context.space_data

		if mat:
			layout.itemR(mat, "type", expand=True)

			if mat.type in ('SURFACE', 'WIRE', 'VOLUME'):
				split = layout.split()
	
				col = split.column()
				col.itemR(mat, "alpha", slider=True)
				col.itemR(mat, "ambient", slider=True)
				col.itemR(mat, "emit")
				col.itemR(mat, "translucency", slider=True)
				
				col = split.column()
				col.itemR(mat, "z_transparency")
				col.itemR(mat, "shadeless")	
				col.itemR(mat, "tangent_shading")
				col.itemR(mat, "cubic", slider=True)
				
			elif mat.type == 'HALO':
				layout.itemR(mat, "alpha", slider=True)
			
class MATERIAL_PT_strand(MaterialButtonsPanel):
	__label__ = "Strand"
	__default_closed__ = True
	COMPAT_ENGINES = set(['BLENDER_RENDER'])
	
	def draw(self, context):
		layout = self.layout
		
		mat = context.material
		tan = mat.strand
		
		split = layout.split()
		
		col = split.column()
		col.itemL(text="Size:")
		col.itemR(tan, "start_size", text="Root")
		col.itemR(tan, "end_size", text="Tip")
		col.itemR(tan, "min_size", text="Minimum")
		col.itemR(tan, "blender_units")
		sub = col.column()
		sub.active = mat.shadeless == False
		sub.itemR(tan, "tangent_shading")
		
		col = split.column()
		col.itemR(tan, "shape")
		col.itemR(tan, "width_fade")
		col.itemR(tan, "uv_layer")
		sub = col.column()
		sub.active = mat.shadeless == False
		sub.itemR(tan, "surface_diffuse")
		sub = col.column()
		sub.active = tan.surface_diffuse
		sub.itemR(tan, "blend_distance", text="Distance")
		
class MATERIAL_PT_options(MaterialButtonsPanel):
	__label__ = "Options"
	COMPAT_ENGINES = set(['BLENDER_RENDER', 'BLENDER_GAME'])

	def draw(self, context):
		layout = self.layout
		
		mat = context.material
		
		split = layout.split()
		
		col = split.column()
		col.itemR(mat, "traceable")
		col.itemR(mat, "full_oversampling")
		col.itemR(mat, "sky")
		col.itemR(mat, "exclude_mist")
		col.itemR(mat, "invert_z")
		sub = col.column(align=True)
		sub.itemL(text="Light Group:")
		sub.itemR(mat, "light_group", text="")
		row = sub.row()
		row.active = mat.light_group
		row.itemR(mat, "light_group_exclusive", text="Exclusive")

		col = split.column()
		col.itemR(mat, "face_texture")
		sub = col.column()
		sub.active = mat.face_texture
		sub.itemR(mat, "face_texture_alpha")
		col.itemR(mat, "vertex_color_paint")
		col.itemR(mat, "vertex_color_light")
		col.itemR(mat, "object_color")

class MATERIAL_PT_shadows(MaterialButtonsPanel):
	__label__ = "Shadows"
	COMPAT_ENGINES = set(['BLENDER_RENDER', 'BLENDER_GAME'])

	def draw(self, context):
		layout = self.layout
		
		mat = context.material
		
		split = layout.split()
		
		col = split.column()
		col.itemR(mat, "shadows", text="Receive")
		col.itemR(mat, "transparent_shadows", text="Receive Transparent")
		col.itemR(mat, "only_shadow", text="Shadows Only")
		col.itemR(mat, "cast_shadows_only", text="Cast Only")
		col.itemR(mat, "shadow_casting_alpha", text="Casting Alpha", slider=True)
		
		col = split.column()
		col.itemR(mat, "ray_shadow_bias", text="Auto Ray Bias")
		sub = col.column()
		sub.active = not mat.ray_shadow_bias
		sub.itemR(mat, "shadow_ray_bias", text="Ray Shadow Bias")
		sub.itemR(mat, "cast_buffer_shadows")
		sub.itemR(mat, "shadow_buffer_bias", text="Buffer Bias")

class MATERIAL_PT_diffuse(MaterialButtonsPanel):
	__label__ = "Diffuse"
	COMPAT_ENGINES = set(['BLENDER_RENDER', 'BLENDER_GAME'])

	def poll(self, context):
		return (context.material.type != 'HALO') and (context.scene.render_data.engine in self.COMPAT_ENGINES)

	def draw(self, context):
		layout = self.layout
		
		mat = context.material	
		
		split = layout.split()
		
		col = split.column()
		col.itemR(mat, "diffuse_color", text="")
		sub = col.column()
		sub.active = mat.shadeless== False
		sub.itemR(mat, "diffuse_reflection", text="Intensity", slider=True)
		
		col = split.column()
		col.active = mat.shadeless== False
		col.itemR(mat, "diffuse_shader", text="")
		col.itemR(mat, "use_diffuse_ramp", text="Ramp")
		
		col = layout.column()
		col.active = mat.shadeless== False
		if mat.diffuse_shader == 'OREN_NAYAR':
			col.itemR(mat, "roughness")
		elif mat.diffuse_shader == 'MINNAERT':
			col.itemR(mat, "darkness")
		elif mat.diffuse_shader == 'TOON':
			row = col.row()
			row.itemR(mat, "diffuse_toon_size", text="Size")
			row.itemR(mat, "diffuse_toon_smooth", text="Smooth")
		elif mat.diffuse_shader == 'FRESNEL':
			row = col.row()
			row.itemR(mat, "diffuse_fresnel", text="Fresnel")
			row.itemR(mat, "diffuse_fresnel_factor", text="Factor")
			
		elif mat.use_diffuse_ramp:
			layout.template_color_ramp(mat.diffuse_ramp, expand=True)
		
class MATERIAL_PT_specular(MaterialButtonsPanel):
	__label__ = "Specular"
	COMPAT_ENGINES = set(['BLENDER_RENDER', 'BLENDER_GAME'])

	def poll(self, context):
		return (context.material.type != 'HALO') and (context.scene.render_data.engine in self.COMPAT_ENGINES)

	def draw(self, context):
		layout = self.layout
		
		mat = context.material
		
		layout.active = mat.shadeless == False
		
		split = layout.split()
		
		col = split.column()
		col.itemR(mat, "specular_color", text="")
		col.itemR(mat, "specular_reflection", text="Intensity", slider=True)

		col = split.column()
		col.itemR(mat, "specular_shader", text="")
		col.itemR(mat, "use_specular_ramp", text="Ramp")

		col = layout.column()
		if mat.specular_shader in ('COOKTORR', 'PHONG'):
			col.itemR(mat, "specular_hardness", text="Hardness")
		elif mat.specular_shader == 'BLINN':
			row = col.row()
			row.itemR(mat, "specular_hardness", text="Hardness")
			row.itemR(mat, "specular_ior", text="IOR")
		elif mat.specular_shader == 'WARDISO':
			col.itemR(mat, "specular_slope", text="Slope")
		elif mat.specular_shader == 'TOON':
			row = col.row()
			row.itemR(mat, "specular_toon_size", text="Size")
			row.itemR(mat, "specular_toon_smooth", text="Smooth")
		
		if mat.use_specular_ramp:
			layout.template_color_ramp(mat.specular_ramp, expand=True)
		
class MATERIAL_PT_sss(MaterialButtonsPanel):
	__label__ = "Subsurface Scattering"
	__default_closed__ = True
	COMPAT_ENGINES = set(['BLENDER_RENDER'])
	
	def poll(self, context):
		return (context.material.type in ('SURFACE', 'WIRE')) and (context.scene.render_data.engine in self.COMPAT_ENGINES)

	def draw_header(self, context):
		layout = self.layout
		sss = context.material.subsurface_scattering

		layout.itemR(sss, "enabled", text="")
	
	def draw(self, context):
		layout = self.layout
		
		mat = context.material
		sss = context.material.subsurface_scattering

		layout.active = sss.enabled	
		
		split = layout.split()
		split.active = mat.shadeless== False
		
		col = split.column()
		col.itemR(sss, "color", text="")
		col.itemL(text="Blend:")
		col.itemR(sss, "color_factor", slider=True)
		col.itemR(sss, "texture_factor", slider=True)
		col.itemL(text="Scattering Weight:")
		col.itemR(sss, "front")
		col.itemR(sss, "back")
		
		col = split.column()
		col.itemR(sss, "ior")
		col.itemR(sss, "scale")
		col.itemR(sss, "radius", text="RGB Radius")
		col.itemR(sss, "error_tolerance")

class MATERIAL_PT_raymir(MaterialButtonsPanel):
	__label__ = "Ray Mirror"
	__default_closed__ = True
	COMPAT_ENGINES = set(['BLENDER_RENDER'])
	
	def poll(self, context):
		return (context.material.type in 'SURFACE', 'WIRE') and (context.scene.render_data.engine in self.COMPAT_ENGINES)
	
	def draw_header(self, context):
		layout = self.layout
		
		raym = context.material.raytrace_mirror

		layout.itemR(raym, "enabled", text="")
	
	def draw(self, context):
		layout = self.layout
		
		mat = context.material
		raym = context.material.raytrace_mirror
		
		layout.active = raym.enabled
		
		split = layout.split()
		
		col = split.column()
		col.itemR(raym, "reflect", text="Reflectivity", slider=True)
		col.itemR(mat, "mirror_color", text="")
		col.itemR(raym, "fresnel")
		col.itemR(raym, "fresnel_fac", text="Fac", slider=True)
		
		col = split.column()
		col.itemR(raym, "gloss", slider=True)
		sub = col.column()
		sub.active = raym.gloss < 1
		sub.itemR(raym, "gloss_threshold", slider=True, text="Threshold")
		sub.itemR(raym, "gloss_samples", text="Samples")
		sub.itemR(raym, "gloss_anisotropic", slider=True, text="Anisotropic")
		
		row = layout.row()
		row.itemR(raym, "distance", text="Max Dist")
		row.itemR(raym, "depth")
		
		layout.itemR(raym, "fade_to")
		
class MATERIAL_PT_raytransp(MaterialButtonsPanel):
	__label__= "Ray Transparency"
	__default_closed__ = True
	COMPAT_ENGINES = set(['BLENDER_RENDER'])
		
	def poll(self, context):
		return (context.material.type in 'SURFACE', 'WIRE') and (context.scene.render_data.engine in self.COMPAT_ENGINES)

	def draw_header(self, context):
		layout = self.layout
		
		rayt = context.material.raytrace_transparency

		layout.itemR(rayt, "enabled", text="")

	def draw(self, context):
		layout = self.layout
		
		mat = context.material
		rayt = context.material.raytrace_transparency
		
		layout.active = rayt.enabled and mat.shadeless == False
		
		split = layout.split()
		
		col = split.column()
		col.itemR(rayt, "ior")
		col.itemR(rayt, "fresnel")
		col.itemR(rayt, "fresnel_fac", text="Fac", slider=True)
		
		col = split.column()
		col.itemR(rayt, "gloss", slider=True)
		sub = col.column()
		sub.active = rayt.gloss < 1
		sub.itemR(rayt, "gloss_threshold", slider=True, text="Threshold")
		sub.itemR(rayt, "gloss_samples", text="Samples")
		
		flow = layout.column_flow()
		flow.itemR(rayt, "filter", slider=True)
		flow.itemR(rayt, "limit")
		flow.itemR(rayt, "falloff")
		flow.itemR(rayt, "specular_opacity", slider=True, text="Spec Opacity")
		flow.itemR(rayt, "depth")
		
class MATERIAL_PT_halo(MaterialButtonsPanel):
	__label__= "Halo"
	COMPAT_ENGINES = set(['BLENDER_RENDER'])
	
	def poll(self, context):
		return (context.material.type == 'HALO') and (context.scene.render_data.engine in self.COMPAT_ENGINES)
	
	def draw(self, context):
		layout = self.layout
		
		mat = context.material
		halo = mat.halo

		split = layout.split()
		
		col = split.column()
		col.itemR(mat, "diffuse_color", text="")
		col.itemR(halo, "size")
		col.itemR(halo, "hardness")
		col.itemR(halo, "add", slider=True)
		col.itemL(text="Options:")
		col.itemR(halo, "use_texture", text="Texture")
		col.itemR(halo, "use_vertex_normal", text="Vertex Normal")
		col.itemR(halo, "xalpha")
		col.itemR(halo, "shaded")
		col.itemR(halo, "soft")

		col = split.column()
		col.itemR(halo, "ring")
		sub = col.column()
		sub.active = halo.ring
		sub.itemR(halo, "rings")
		sub.itemR(mat, "mirror_color", text="")
		col.itemR(halo, "lines")
		sub = col.column()
		sub.active = halo.lines
		sub.itemR(halo, "line_number", text="Lines")
		sub.itemR(mat, "specular_color", text="")
		col.itemR(halo, "star")
		sub = col.column()
		sub.active = halo.star
		sub.itemR(halo, "star_tips")
		col.itemR(halo, "flare_mode")
		sub = col.column()
		sub.active = halo.flare_mode
		sub.itemR(halo, "flare_size", text="Size")
		sub.itemR(halo, "flare_subsize", text="Subsize")
		sub.itemR(halo, "flare_boost", text="Boost")
		sub.itemR(halo, "flare_seed", text="Seed")
		sub.itemR(halo, "flares_sub", text="Sub")

bpy.types.register(MATERIAL_PT_context_material)
bpy.types.register(MATERIAL_PT_preview)
bpy.types.register(MATERIAL_PT_material)
bpy.types.register(MATERIAL_PT_diffuse)
bpy.types.register(MATERIAL_PT_specular)
bpy.types.register(MATERIAL_PT_raymir)
bpy.types.register(MATERIAL_PT_raytransp)
bpy.types.register(MATERIAL_PT_sss)
bpy.types.register(MATERIAL_PT_halo)
bpy.types.register(MATERIAL_PT_strand)
bpy.types.register(MATERIAL_PT_options)
bpy.types.register(MATERIAL_PT_shadows)
