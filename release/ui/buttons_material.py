	
import bpy

class MaterialButtonsPanel(bpy.types.Panel):
	__space_type__ = 'PROPERTIES'
	__region_type__ = 'WINDOW'
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
		
		engine = context.scene.render_data.engine
		return (context.object) and (engine in self.COMPAT_ENGINES)

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
			col.itemO("object.material_slot_add", icon='ICON_ZOOMIN', text="")
			col.itemO("object.material_slot_remove", icon='ICON_ZOOMOUT', text="")

			if ob.mode == 'EDIT':
				row = layout.row(align=True)
				row.itemO("object.material_slot_assign", text="Assign")
				row.itemO("object.material_slot_select", text="Select")
				row.itemO("object.material_slot_deselect", text="Deselect")

		split = layout.split(percentage=0.65)

		if ob:
			split.template_ID(ob, "active_material", new="material.new")
			row = split.row()
			if slot:
				row.itemR(slot, "link", text="")
			else:
				row.itemL()
		elif mat:
			split.template_ID(space, "pin_id")
			split.itemS()

		layout.itemR(mat, "type", expand=True)
	
class MATERIAL_PT_shading(MaterialButtonsPanel):
	__label__ = "Shading"
	COMPAT_ENGINES = set(['BLENDER_RENDER', 'BLENDER_GAME'])

	def poll(self, context):
		mat = context.material
		engine = context.scene.render_data.engine
		return mat and (mat.type in ('SURFACE', 'WIRE', 'HALO')) and (engine in self.COMPAT_ENGINES)

	def draw(self, context):
		layout = self.layout
		
		mat = context.material
		ob = context.object
		slot = context.material_slot
		space = context.space_data

		if mat:

			if mat.type in ('SURFACE', 'WIRE'):
				split = layout.split()
	
				col = split.column()
				sub = col.column()
				sub.active = not mat.shadeless
				sub.itemR(mat, "emit")
				sub.itemR(mat, "ambient")
				sub = col.column()
				sub.itemR(mat, "translucency")
				
				col = split.column()
				col.itemR(mat, "shadeless")	
				sub = col.column()
				sub.active = not mat.shadeless
				sub.itemR(mat, "tangent_shading")
				sub.itemR(mat, "cubic")
				
			elif mat.type == 'HALO':
				layout.itemR(mat, "alpha")
			
class MATERIAL_PT_strand(MaterialButtonsPanel):
	__label__ = "Strand"
	__default_closed__ = True
	COMPAT_ENGINES = set(['BLENDER_RENDER'])

	def poll(self, context):
		mat = context.material
		engine = context.scene.render_data.engine
		return mat and (mat.type in ('SURFACE', 'WIRE', 'HALO')) and (engine in self.COMPAT_ENGINES)
	
	def draw(self, context):
		layout = self.layout
		
		mat = context.material
		tan = mat.strand
		
		split = layout.split()
		
		col = split.column(align=True)
		col.itemL(text="Size:")
		col.itemR(tan, "start_size", text="Root")
		col.itemR(tan, "end_size", text="Tip")
		col.itemR(tan, "min_size", text="Minimum")
		col.itemR(tan, "blender_units")
		sub = col.column()
		sub.active = (not mat.shadeless)
		sub.itemR(tan, "tangent_shading")
		col.itemR(tan, "shape")
		
		col = split.column()
		col.itemL(text="Shading:")
		col.itemR(tan, "width_fade")
		col.itemR(tan, "uv_layer")
		col.itemS()
		sub = col.column()
		sub.active = (not mat.shadeless)
		sub.itemR(tan, "surface_diffuse")
		sub = col.column()
		sub.active = tan.surface_diffuse
		sub.itemR(tan, "blend_distance", text="Distance")
		
class MATERIAL_PT_physics(MaterialButtonsPanel):
	__label__ = "Physics"
	COMPAT_ENGINES = set(['BLENDER_GAME'])
	
	def draw(self, context):
		layout = self.layout
		
		mat = context.material
		phys = mat.physics
		
		split = layout.split()
		
		col = split.column()
		col.itemR(phys, "distance")
		col.itemR(phys, "friction")
		col.itemR(phys, "align_to_normal")
		
		col = split.column()
		col.itemR(phys, "force", slider=True)
		col.itemR(phys, "elasticity", slider=True)
		col.itemR(phys, "damp", slider=True)
		
class MATERIAL_PT_options(MaterialButtonsPanel):
	__label__ = "Options"
	COMPAT_ENGINES = set(['BLENDER_RENDER', 'BLENDER_GAME'])

	def poll(self, context):
		mat = context.material
		engine = context.scene.render_data.engine
		return mat and (mat.type in ('SURFACE', 'WIRE', 'HALO')) and (engine in self.COMPAT_ENGINES)

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
		col.itemS()
		col.itemR(mat, "vertex_color_paint")
		col.itemR(mat, "vertex_color_light")
		col.itemR(mat, "object_color")

class MATERIAL_PT_shadow(MaterialButtonsPanel):
	__label__ = "Shadow"
	__default_closed__ = True
	COMPAT_ENGINES = set(['BLENDER_RENDER', 'BLENDER_GAME'])
	
	def poll(self, context):
		mat = context.material
		engine = context.scene.render_data.engine
		return mat and (mat.type in ('SURFACE', 'WIRE')) and (engine in self.COMPAT_ENGINES)

	def draw(self, context):
		layout = self.layout
		
		mat = context.material
		
		split = layout.split()
		
		col = split.column()
		col.itemR(mat, "shadows", text="Receive")
		col.itemR(mat, "transparent_shadows", text="Receive Transparent")
		col.itemR(mat, "only_shadow", text="Shadows Only")
		col.itemR(mat, "cast_shadows_only", text="Cast Only")
		col.itemR(mat, "shadow_casting_alpha", text="Casting Alpha")
		
		col = split.column()
		col.itemR(mat, "cast_buffer_shadows")
		sub = col.column()
		sub.active = mat.cast_buffer_shadows
		sub.itemR(mat, "shadow_buffer_bias", text="Buffer Bias")
		col.itemR(mat, "ray_shadow_bias", text="Auto Ray Bias")
		sub = col.column()
		sub.active = (not mat.ray_shadow_bias)
		sub.itemR(mat, "shadow_ray_bias", text="Ray Bias")

class MATERIAL_PT_diffuse(MaterialButtonsPanel):
	__label__ = "Diffuse"
	COMPAT_ENGINES = set(['BLENDER_RENDER', 'BLENDER_GAME'])

	def poll(self, context):
		mat = context.material
		engine = context.scene.render_data.engine
		return mat and (mat.type in ('SURFACE', 'WIRE')) and (engine in self.COMPAT_ENGINES)

	def draw(self, context):
		layout = self.layout
		
		mat = context.material	
		
		split = layout.split()
		
		col = split.column()
		col.itemR(mat, "diffuse_color", text="")
		sub = col.column()
		sub.active = (not mat.shadeless)
		sub.itemR(mat, "diffuse_reflection", text="Intensity")
		
		col = split.column()
		col.active = (not mat.shadeless)
		col.itemR(mat, "diffuse_shader", text="")
		col.itemR(mat, "use_diffuse_ramp", text="Ramp")
		
		col = layout.column()
		col.active = (not mat.shadeless)
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
			
		if mat.use_diffuse_ramp:
			layout.itemS()
			layout.template_color_ramp(mat.diffuse_ramp, expand=True)
			layout.itemS()
			row = layout.row()
			split = row.split(percentage=0.3)
			split.itemL(text="Input:")
			split.itemR(mat, "diffuse_ramp_input", text="")
			split = row.split(percentage=0.3)
			split.itemL(text="Blend:")
			split.itemR(mat, "diffuse_ramp_blend", text="")

class MATERIAL_PT_specular(MaterialButtonsPanel):
	__label__ = "Specular"
	COMPAT_ENGINES = set(['BLENDER_RENDER', 'BLENDER_GAME'])

	def poll(self, context):
		mat = context.material
		engine = context.scene.render_data.engine
		return mat and (mat.type in ('SURFACE', 'WIRE')) and (engine in self.COMPAT_ENGINES)

	def draw(self, context):
		layout = self.layout
		
		mat = context.material
		
		layout.active = (not mat.shadeless)
		
		split = layout.split()
		
		col = split.column()
		col.itemR(mat, "specular_color", text="")
		col.itemR(mat, "specular_reflection", text="Intensity")

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
			layout.itemS()
			layout.template_color_ramp(mat.specular_ramp, expand=True)
			layout.itemS()
			row = layout.row()
			split = row.split(percentage=0.3)
			split.itemL(text="Input:")
			split.itemR(mat, "specular_ramp_input", text="")
			split = row.split(percentage=0.3)
			split.itemL(text="Blend:")
			split.itemR(mat, "specular_ramp_blend", text="")
		
class MATERIAL_PT_sss(MaterialButtonsPanel):
	__label__ = "Subsurface Scattering"
	__default_closed__ = True
	COMPAT_ENGINES = set(['BLENDER_RENDER'])
	
	def poll(self, context):
		mat = context.material
		engine = context.scene.render_data.engine
		return mat and (mat.type in ('SURFACE', 'WIRE')) and (engine in self.COMPAT_ENGINES)

	def draw_header(self, context):
		layout = self.layout
		sss = context.material.subsurface_scattering
		mat = context.material
		
		layout.active = (not mat.shadeless)
		layout.itemR(sss, "enabled", text="")
	
	def draw(self, context):
		layout = self.layout
		
		mat = context.material
		sss = context.material.subsurface_scattering

		layout.active = sss.enabled	
		
		split = layout.split()
		split.active = (not mat.shadeless)
		
		col = split.column()
		col.itemR(sss, "ior")
		col.itemR(sss, "scale")
		col.itemR(sss, "color", text="")
		col.itemR(sss, "radius", text="RGB Radius")
		
		col = split.column()
		sub = col.column(align=True)
		sub.itemL(text="Blend:")
		sub.itemR(sss, "color_factor", text="Color")
		sub.itemR(sss, "texture_factor", text="Texture")
		sub.itemL(text="Scattering Weight:")
		sub.itemR(sss, "front")
		sub.itemR(sss, "back")
		col.itemS()
		col.itemR(sss, "error_tolerance", text="Error")

class MATERIAL_PT_mirror(MaterialButtonsPanel):
	__label__ = "Mirror"
	__default_closed__ = True
	COMPAT_ENGINES = set(['BLENDER_RENDER'])
	
	def poll(self, context):
		mat = context.material
		engine = context.scene.render_data.engine
		return mat and (mat.type in ('SURFACE', 'WIRE')) and (engine in self.COMPAT_ENGINES)
	
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
		col.itemR(raym, "reflect", text="Reflectivity")
		col.itemR(mat, "mirror_color", text="")

		col = split.column()
		col.itemR(raym, "fresnel")
		sub = col.column()
		sub.active = raym.fresnel > 0
		sub.itemR(raym, "fresnel_factor", text="Blend")
		
		split = layout.split()
		
		col = split.column()
		col.itemS()
		col.itemR(raym, "distance", text="Max Dist")
		col.itemR(raym, "depth")
		col.itemS()
		sub = col.split(percentage=0.4)
		sub.itemL(text="Fade To:")
		sub.itemR(raym, "fade_to", text="")
		
		col = split.column()
		col.itemL(text="Gloss:")
		col.itemR(raym, "gloss", text="Amount")
		sub = col.column()
		sub.active = raym.gloss < 1
		sub.itemR(raym, "gloss_threshold", text="Threshold")
		sub.itemR(raym, "gloss_samples", text="Samples")
		sub.itemR(raym, "gloss_anisotropic", text="Anisotropic")

class MATERIAL_PT_transp(MaterialButtonsPanel):
	__label__= "Transparency"
	__default_closed__ = True
	COMPAT_ENGINES = set(['BLENDER_RENDER'])
		
	def poll(self, context):
		mat = context.material
		engine = context.scene.render_data.engine
		return mat and (mat.type in ('SURFACE', 'WIRE')) and (engine in self.COMPAT_ENGINES)

	def draw_header(self, context):
		layout = self.layout
		
		mat = context.material
		layout.itemR(mat, "transparency", text="")

	def draw(self, context):
		layout = self.layout
		
		mat = context.material
		rayt = context.material.raytrace_transparency
		
		row= layout.row()
		row.itemR(mat, "transparency_method", expand=True)
		row.active = mat.transparency and (not mat.shadeless)
		
		split = layout.split()
		
		col = split.column()
		row = col.row()
		row.itemR(mat, "alpha")
		row = col.row()
		row.active = mat.transparency and (not mat.shadeless)
		row.itemR(mat, "specular_alpha", text="Specular")

		col = split.column()
		col.active = (not mat.shadeless)
		col.itemR(rayt, "fresnel")
		sub = col.column()
		sub.active = rayt.fresnel > 0
		sub.itemR(rayt, "fresnel_factor", text="Blend")

		if mat.transparency_method == 'RAYTRACE':
			layout.itemS()
			split = layout.split()
			split.active = mat.transparency

			col = split.column()
			col.itemR(rayt, "ior")
			col.itemR(rayt, "filter")
			col.itemR(rayt, "falloff")
			col.itemR(rayt, "limit")
			col.itemR(rayt, "depth")
			
			col = split.column()
			col.itemL(text="Gloss:")
			col.itemR(rayt, "gloss", text="Amount")
			sub = col.column()
			sub.active = rayt.gloss < 1
			sub.itemR(rayt, "gloss_threshold", text="Threshold")
			sub.itemR(rayt, "gloss_samples", text="Samples")

class MATERIAL_PT_volume_shading(MaterialButtonsPanel):
	__label__ = "Shading"
	__default_closed__ = False
	COMPAT_ENGINES = set(['BLENDER_RENDER'])
	
	def poll(self, context):
		mat = context.material
		engine = context.scene.render_data.engine
		return mat and (mat.type == 'VOLUME') and (engine in self.COMPAT_ENGINES)
	
	def draw(self, context):
		layout = self.layout

		mat = context.material
		vol = context.material.volume
		
		split = layout.split()
		
		row = split.row()
		row.itemR(vol, "density")
		row.itemR(vol, "scattering")
		
		split = layout.split()
		col = split.column()
		col.itemR(vol, "absorption")
		col.itemR(vol, "absorption_color", text="")

		col = split.column()
		col.itemR(vol, "emission")
		col.itemR(vol, "emission_color", text="")

class MATERIAL_PT_volume_scattering(MaterialButtonsPanel):
	__label__ = "Scattering"
	__default_closed__ = False
	COMPAT_ENGINES = set(['BLENDER_RENDER'])
	
	def poll(self, context):
		mat = context.material
		engine = context.scene.render_data.engine
		return mat and (mat.type == 'VOLUME') and (engine in self.COMPAT_ENGINES)
	
	def draw(self, context):
		layout = self.layout
		
		mat = context.material
		vol = context.material.volume
		
		split = layout.split()
		
		col = split.column()
		col.itemR(vol, "scattering_mode", text="")
		if vol.scattering_mode == 'SINGLE_SCATTERING':
			col.itemR(vol, "light_cache")
			sub = col.column()
			sub.active = vol.light_cache
			sub.itemR(vol, "cache_resolution")
		elif vol.scattering_mode in ('MULTIPLE_SCATTERING', 'SINGLE_PLUS_MULTIPLE_SCATTERING'):
			col.itemR(vol, "cache_resolution")
			
			col = col.column(align=True)
			col.itemR(vol, "ms_diffusion")
			col.itemR(vol, "ms_spread")
			col.itemR(vol, "ms_intensity")
		
		col = split.column()
		# col.itemL(text="Anisotropic Scattering:")
		col.itemR(vol, "phase_function", text="")
		if vol.phase_function in ('SCHLICK', 'HENYEY-GREENSTEIN'):
			col.itemR(vol, "asymmetry")

class MATERIAL_PT_volume_transp(MaterialButtonsPanel):
	__label__= "Transparency"
	COMPAT_ENGINES = set(['BLENDER_RENDER'])
		
	def poll(self, context):
		mat = context.material
		engine = context.scene.render_data.engine
		return mat and (mat.type == 'VOLUME') and (engine in self.COMPAT_ENGINES)

	def draw_header(self, context):
		layout = self.layout

	def draw(self, context):
		layout = self.layout
		
		mat = context.material
		rayt = context.material.raytrace_transparency
		
		row= layout.row()
		row.itemR(mat, "transparency_method", expand=True)
		row.active = mat.transparency and (not mat.shadeless)
		
class MATERIAL_PT_volume_integration(MaterialButtonsPanel):
	__label__ = "Integration"
	__default_closed__ = False
	COMPAT_ENGINES = set(['BLENDER_RENDER'])
	
	def poll(self, context):
		mat = context.material
		engine = context.scene.render_data.engine
		return mat and (mat.type == 'VOLUME') and (engine in self.COMPAT_ENGINES)
	
	def draw(self, context):
		layout = self.layout
		
		mat = context.material
		vol = context.material.volume
		
		split = layout.split()
		
		col = split.column()
		col.itemL(text="Step Calculation:")
		col.itemR(vol, "step_calculation", text="")
		col = col.column(align=True)
		col.itemR(vol, "step_size")
		col.itemR(vol, "shading_step_size")
		
		col = split.column()
		col.itemL()
		col.itemR(vol, "depth_cutoff")
		col.itemR(vol, "density_scale")
		
		
class MATERIAL_PT_halo(MaterialButtonsPanel):
	__label__= "Halo"
	COMPAT_ENGINES = set(['BLENDER_RENDER'])
	
	def poll(self, context):
		mat = context.material
		engine = context.scene.render_data.engine
		return mat and (mat.type == 'HALO') and (engine in self.COMPAT_ENGINES)
	
	def draw(self, context):
		layout = self.layout
		
		mat = context.material
		halo = mat.halo

		split = layout.split()
		
		col = split.column()
		col.itemR(mat, "diffuse_color", text="")
		col.itemR(halo, "size")
		col.itemR(halo, "hardness")
		col.itemR(halo, "add")
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
		col.itemS()
		col.itemR(halo, "lines")
		sub = col.column()
		sub.active = halo.lines
		sub.itemR(halo, "line_number", text="Lines")
		sub.itemR(mat, "specular_color", text="")
		col.itemS()
		col.itemR(halo, "star")
		sub = col.column()
		sub.active = halo.star
		sub.itemR(halo, "star_tips")
		
class MATERIAL_PT_flare(MaterialButtonsPanel):
	__label__= "Flare"
	COMPAT_ENGINES = set(['BLENDER_RENDER'])
	
	def poll(self, context):
		mat = context.material
		engine = context.scene.render_data.engine
		return mat and (mat.type == 'HALO') and (engine in self.COMPAT_ENGINES)
	
	def draw_header(self, context):
		layout = self.layout
		
		mat = context.material
		halo = mat.halo
		layout.itemR(halo, "flare_mode", text="")
	
	def draw(self, context):
		layout = self.layout
		
		mat = context.material
		halo = mat.halo

		layout.active = halo.flare_mode
		
		split = layout.split()
		
		col = split.column()
		col.itemR(halo, "flare_size", text="Size")
		col.itemR(halo, "flare_boost", text="Boost")
		col.itemR(halo, "flare_seed", text="Seed")
		col = split.column()
		col.itemR(halo, "flares_sub", text="Subflares")
		col.itemR(halo, "flare_subsize", text="Subsize")

bpy.types.register(MATERIAL_PT_context_material)
bpy.types.register(MATERIAL_PT_preview)
bpy.types.register(MATERIAL_PT_diffuse)
bpy.types.register(MATERIAL_PT_specular)
bpy.types.register(MATERIAL_PT_shading)
bpy.types.register(MATERIAL_PT_transp)
bpy.types.register(MATERIAL_PT_mirror)
bpy.types.register(MATERIAL_PT_sss)
bpy.types.register(MATERIAL_PT_volume_shading)
bpy.types.register(MATERIAL_PT_volume_scattering)
bpy.types.register(MATERIAL_PT_volume_transp)
bpy.types.register(MATERIAL_PT_volume_integration)
bpy.types.register(MATERIAL_PT_halo)
bpy.types.register(MATERIAL_PT_flare)
bpy.types.register(MATERIAL_PT_physics)
bpy.types.register(MATERIAL_PT_strand)
bpy.types.register(MATERIAL_PT_options)
bpy.types.register(MATERIAL_PT_shadow)
