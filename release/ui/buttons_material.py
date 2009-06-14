
import bpy

class MaterialButtonsPanel(bpy.types.Panel):
	__space_type__ = "BUTTONS_WINDOW"
	__region_type__ = "WINDOW"
	__context__ = "material"

	def poll(self, context):
		return (context.material != None)

class MATERIAL_PT_preview(MaterialButtonsPanel):
	__idname__= "MATERIAL_PT_preview"
	__label__ = "Preview"

	def draw(self, context):
		layout = self.layout
		mat = context.material
		
		layout.template_preview(mat)
	
class MATERIAL_PT_material(MaterialButtonsPanel):
	__idname__= "MATERIAL_PT_material"
	__label__ = "Material"

	def poll(self, context):
		return (context.object != None)

	def draw(self, context):
		layout = self.layout
		
		mat = context.material
		ob = context.object
		slot = context.material_slot
		space = context.space_data

		split = layout.split(percentage=0.65)

		if ob and slot:
			split.template_ID(context, slot, "material", new="MATERIAL_OT_new")
			split.itemR(ob, "active_material_index", text="Active")
		elif mat:
			split.template_ID(context, space, "pin_id")
			split.itemS()

		if mat:
			layout.itemS()
		
			layout.itemR(mat, "type", expand=True)
			
			layout.itemR(mat, "alpha", slider=True)

			row = layout.row()
			row.itemR(mat, "shadeless")	
			row.itemR(mat, "wireframe")
			
			
class MATERIAL_PT_tangent(MaterialButtonsPanel):
	__idname__= "MATERIAL_PT_tangent"
	__label__ = "Tangent Shading"

	def draw_header(self, context):
		layout = self.layout
		mat = context.material
		
		layout.itemR(mat, "tangent_shading", text="",)
	
	def draw(self, context):
		layout = self.layout
		tan = context.material.strand
		mat = context.material
		layout.active = mat.tangent_shading	
		
		split = layout.split()
		
		sub = split.column()
		sub.itemL(text="Size:")
		sub.itemR(tan, "start_size", text="Root")
		sub.itemR(tan, "end_size", text="Tip")
		sub.itemR(tan, "min_size", text="Minimum")
		sub.itemR(tan, "blend_distance")
		sub.itemR(tan, "blender_units")
		
		sub = split.column()
		sub.itemR(tan, "surface_diffuse")
		sub.itemR(tan, "shape")
		sub.itemR(tan, "width_fade")
		sub.itemR(tan, "uv_layer")
		
class MATERIAL_PT_options(MaterialButtonsPanel):
	__idname__= "MATERIAL_PT_options"
	__label__ = "Options"

	def draw(self, context):
		layout = self.layout
		mat = context.material
		
		split = layout.split()
		
		sub = split.column()
		sub.itemR(mat, "traceable")
		sub.itemR(mat, "full_oversampling")
		sub.itemR(mat, "sky")
		sub.itemR(mat, "exclude_mist")
		sub.itemR(mat, "face_texture")
		colsub = sub.column()
		colsub.active = mat.face_texture
		colsub.itemR(mat, "face_texture_alpha")
		sub.itemR(mat, "invert_z")
		sub.itemR(mat, "light_group")
		sub.itemR(mat, "light_group_exclusive")
		
		sub = split.column()
		sub.itemL(text="Shadows:")
		sub.itemR(mat, "shadows", text="Recieve")
		sub.itemR(mat, "transparent_shadows", text="Recieve Transparent")
		sub.itemR(mat, "only_shadow", text="Shadows Only")
		sub.itemR(mat, "cast_shadows_only", text="Cast Only")
		sub.itemR(mat, "shadow_casting_alpha", text="Casting Alpha", slider=True)
		
		sub.itemR(mat, "ray_shadow_bias")
		colsub = sub.column()
		colsub.active = mat.ray_shadow_bias
		colsub.itemR(mat, "shadow_ray_bias", text="Raytracing Bias")
		sub.itemR(mat, "cast_buffer_shadows")
		colsub = sub.column()
		colsub.active = mat.cast_buffer_shadows
		colsub.itemR(mat, "shadow_buffer_bias", text="Buffer Bias")

class MATERIAL_PT_diffuse(MaterialButtonsPanel):
	__idname__= "MATERIAL_PT_diffuse"
	__label__ = "Diffuse"

	def poll(self, context):
		mat = context.material
		return (mat and mat.type != "HALO")

	def draw(self, context):
		layout = self.layout
		mat = context.material	
		
		split = layout.split()
		
		sub = split.column()
		sub.itemR(mat, "diffuse_color", text="")
		sub.itemR(mat, "diffuse_reflection", text="Reflection", slider=True)
		sub.itemR(mat, "emit")
		sub.itemR(mat, "ambient", slider=True)
		sub.itemR(mat, "translucency", slider=True)
		
		sub = split.column()
		sub.itemR(mat, "object_color")
		sub.itemR(mat, "vertex_color_light")
		sub.itemR(mat, "vertex_color_paint")
		sub.itemR(mat, "cubic")
		
		layout.itemR(mat, "diffuse_shader", text="Shader")
		split = layout.split()
		sub = split.column()
		if mat.diffuse_shader == 'OREN_NAYAR':
				sub.itemR(mat, "roughness")
		if mat.diffuse_shader == 'MINNAERT':
			sub.itemR(mat, "darkness")
		sub = split.column()
		sub.itemR(mat, "params1_4", text="")
		
		layout.itemR(mat, "diffuse_ramp", text="Ramp")

class MATERIAL_PT_specular(MaterialButtonsPanel):
	__idname__= "MATERIAL_PT_specular"
	__label__ = "Specular"

	def poll(self, context):
		mat = context.material
		return (mat and mat.type != "HALO")

	def draw(self, context):
		layout = self.layout
		mat = context.material
		
		split = layout.split()
		
		sub = split.column()
		sub.itemR(mat, "specular_color", text="")
		sub = split.column()
		sub.itemR(mat, "specularity", text="Intensity", slider=True)
		
		layout.itemR(mat, "spec_shader", text="Shader")
		
		split = layout.split()
		
		sub = split.column()
		if (mat.spec_shader in ('COOKTORR', 'PHONG', 'BLINN')):
			sub.itemR(mat, "specular_hardness", text="Hardness")
		if (mat.spec_shader in ('BLINN')):
			sub.itemR(mat, "specular_refraction", text="IOR")
		if (mat.spec_shader in ('WARDISO')):
			sub.itemR(mat, "specular_slope", text="Slope")
		
		layout.itemR(mat, "specular_ramp", text="Ramp")

class MATERIAL_PT_sss(MaterialButtonsPanel):
	__idname__= "MATERIAL_PT_sss"
	__label__ = "Subsurface Scattering"

	def poll(self, context):
		mat = context.material
		return (mat and mat.type == "SURFACE")

	def draw_header(self, context):
		layout = self.layout
		sss = context.material.subsurface_scattering

		layout.itemR(sss, "enabled", text="")
	
	def draw(self, context):
		layout = self.layout
		sss = context.material.subsurface_scattering
		layout.active = sss.enabled	
		
		split = layout.split()
		
		sub = split.column()
		sub.itemR(sss, "ior")
		sub.itemR(sss, "scale")
		sub.itemR(sss, "radius", text="RGB Radius")
		sub.itemR(sss, "error_tolerance")
		
		sub = split.column()
		sub.itemR(sss, "color", text="")
		sub.itemL(text="Blend:")
		sub.itemR(sss, "color_factor", slider=True)
		sub.itemR(sss, "texture_factor", slider=True)
		sub.itemL(text="Scattering Weight:")
		sub.itemR(sss, "front")
		sub.itemR(sss, "back")

class MATERIAL_PT_raymir(MaterialButtonsPanel):
	__idname__= "MATERIAL_PT_raymir"
	__label__ = "Ray Mirror"
	
	def poll(self, context):
		mat = context.material
		return (mat and mat.type == "SURFACE")
	
	def draw_header(self, context):
		layout = self.layout
		raym = context.material.raytrace_mirror

		layout.itemR(raym, "enabled", text="")
	
	def draw(self, context):
		layout = self.layout
		raym = context.material.raytrace_mirror
		mat = context.material
		
		layout.active = raym.enabled
		
		split = layout.split()
		
		sub = split.column()
		sub.itemR(mat, "mirror_color", text="")
		sub.itemR(raym, "reflect", text="RayMir", slider=True)
		sub.itemR(raym, "fresnel")
		sub.itemR(raym, "fresnel_fac", text="Fac", slider=True)
		
		sub = split.column()
		sub.itemR(raym, "gloss", slider=True)
		sub.itemR(raym, "gloss_threshold", slider=True)
		sub.itemR(raym, "gloss_samples")
		sub.itemR(raym, "gloss_anisotropic", slider=True)
		
		row = layout.row()
		row.itemR(raym, "distance", text="Max Dist")
		row.itemR(raym, "depth")
		
		layout.itemR(raym, "fade_to")
		
class MATERIAL_PT_raytransp(MaterialButtonsPanel):
	__idname__= "MATERIAL_PT_raytransp"
	__label__= "Ray Transparency"
	
	def poll(self, context):
		mat = context.material
		return (mat and mat.type == "SURFACE")

	def draw_header(self, context):
		layout = self.layout
		rayt = context.material.raytrace_transparency

		layout.itemR(rayt, "enabled", text="")

	def draw(self, context):
		layout = self.layout
		rayt = context.material.raytrace_transparency
		
		layout.active = rayt.enabled	
		
		split = layout.split()
		
		sub = split.column()
		sub.itemR(rayt, "ior")
		sub.itemR(rayt, "fresnel")
		sub.itemR(rayt, "fresnel_fac", text="Fac", slider=True)
		
		sub = split.column()
		sub.itemR(rayt, "gloss", slider=True)
		sub.itemR(rayt, "gloss_threshold", slider=True)
		sub.itemR(rayt, "gloss_samples")
		
		flow = layout.column_flow()
		flow.itemR(rayt, "filter", slider=True)
		flow.itemR(rayt, "limit")
		flow.itemR(rayt, "falloff")
		flow.itemR(rayt, "specular_opacity", slider=True, text="Spec Opacity")
		flow.itemR(rayt, "depth")
		
class MATERIAL_PT_halo(MaterialButtonsPanel):
	__idname__= "MATERIAL_PT_halo"
	__label__= "Halo"
	
	def poll(self, context):
		mat = context.material
		return (mat and mat.type == "HALO")
	
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
		col = col.column()
		col.itemR(halo, "ring")
		colsub = col.column()
		colsub.active = halo.ring
		colsub.itemR(halo, "rings")
		colsub.itemR(mat, "mirror_color", text="")
		col.itemR(halo, "lines")
		colsub = col.column()
		colsub.active = halo.lines
		colsub.itemR(halo, "line_number", text="Lines")
		colsub.itemR(mat, "specular_color", text="")
		col.itemR(halo, "star")
		colsub = col.column()
		colsub.active = halo.star
		colsub.itemR(halo, "star_tips")
		col.itemR(halo, "flare_mode")
		colsub = col.column()
		colsub.active = halo.flare_mode
		colsub.itemR(halo, "flare_size", text="Size")
		colsub.itemR(halo, "flare_subsize", text="Subsize")
		colsub.itemR(halo, "flare_boost", text="Boost")
		colsub.itemR(halo, "flare_seed", text="Seed")
		colsub.itemR(halo, "flares_sub", text="Sub")

bpy.types.register(MATERIAL_PT_preview)
bpy.types.register(MATERIAL_PT_material)
bpy.types.register(MATERIAL_PT_diffuse)
bpy.types.register(MATERIAL_PT_specular)
bpy.types.register(MATERIAL_PT_raymir)
bpy.types.register(MATERIAL_PT_raytransp)
bpy.types.register(MATERIAL_PT_sss)
bpy.types.register(MATERIAL_PT_halo)
bpy.types.register(MATERIAL_PT_tangent)
bpy.types.register(MATERIAL_PT_options)