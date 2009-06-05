
import bpy

class TextureButtonsPanel(bpy.types.Panel):
	__space_type__ = "BUTTONS_WINDOW"
	__region_type__ = "WINDOW"
	__context__ = "texture"
	
	def poll(self, context):
		return (context.texture != None)

class TEXTURE_PT_preview(TextureButtonsPanel):
	__idname__= "TEXTURE_PT_preview"
	__label__ = "Preview"

	def draw(self, context):
		layout = self.layout

		tex = context.texture
		layout.template_preview(tex)

class TEXTURE_PT_texture(TextureButtonsPanel):
	__idname__= "TEXTURE_PT_texture"
	__label__ = "Texture"

	def draw(self, context):
		layout = self.layout
		tex = context.texture
		
		layout.itemR(tex, "type")

class TEXTURE_PT_colors(TextureButtonsPanel):
	__idname__= "TEXTURE_PT_colors"
	__label__ = "Colors"

	def draw(self, context):
		layout = self.layout
		tex = context.texture

		if tex.color_ramp:
			layout.template_color_ramp(tex.color_ramp, expand=True)
		else:
			layout.itemR(tex, "rgb_factor")

		row = layout.row()
		row.itemR(tex, "brightness")
		row.itemR(tex, "contrast")

class TEXTURE_PT_clouds(TextureButtonsPanel):
	__idname__= "TEXTURE_PT_clouds"
	__label__ = "Clouds"
	
	def poll(self, context):
		tex = context.texture
		return (tex and tex.type == 'CLOUDS')

	def draw(self, context):
		layout = self.layout
		tex = context.texture
		
		layout.itemR(tex, "stype", expand=True)
		layout.itemL(text="Noise:")
		layout.itemR(tex, "noise_type", text="Type", expand=True)
		layout.itemR(tex, "noise_basis", text="Basis")
		
		col = layout.column_flow()
		col.itemR(tex, "noise_size", text="Size")
		col.itemR(tex, "noise_depth", text="Depth")
		col.itemR(tex, "nabla", text="Nabla")

class TEXTURE_PT_wood(TextureButtonsPanel):
	__idname__= "TEXTURE_PT_wood"
	__label__ = "Wood"
	
	def poll(self, context):
		tex = context.texture
		return (tex and tex.type == 'WOOD')

	def draw(self, context):
		layout = self.layout
		tex = context.texture
		
		layout.itemR(tex, "stype", expand=True)
		layout.itemR(tex, "noisebasis2", expand=True)
		layout.itemL(text="Noise:")
		layout.itemR(tex, "noise_type", text="Type", expand=True)
		layout.itemR(tex, "noise_basis", text="Basis")
		
		col = layout.column_flow()
		col.itemR(tex, "noise_size", text="Size")
		col.itemR(tex, "turbulence")
		col.itemR(tex, "nabla")
		
class TEXTURE_PT_marble(TextureButtonsPanel):
	__idname__= "TEXTURE_PT_marble"
	__label__ = "Marble"
	
	def poll(self, context):
		tex = context.texture
		return (tex and tex.type == 'MARBLE')

	def draw(self, context):
		layout = self.layout
		tex = context.texture
		
		layout.itemR(tex, "stype", expand=True)
		layout.itemR(tex, "noisebasis2", expand=True)
		layout.itemL(text="Noise:")
		layout.itemR(tex, "noise_type", text="Type", expand=True)
		layout.itemR(tex, "noise_basis", text="Basis")
		
		col = layout.column_flow()	
		col.itemR(tex, "noise_size", text="Size")
		col.itemR(tex, "noise_depth", text="Depth")
		col.itemR(tex, "turbulence")
		col.itemR(tex, "nabla")

class TEXTURE_PT_magic(TextureButtonsPanel):
	__idname__= "TEXTURE_PT_magic"
	__label__ = "Magic"
	
	def poll(self, context):
		tex = context.texture
		return (tex and tex.type == 'MAGIC')

	def draw(self, context):
		layout = self.layout
		tex = context.texture
			
		row = layout.row()
		row.itemR(tex, "noise_depth", text="Depth")
		row.itemR(tex, "turbulence")

class TEXTURE_PT_blend(TextureButtonsPanel):
	__idname__= "TEXTURE_PT_blend"
	__label__ = "Blend"
	
	def poll(self, context):
		tex = context.texture
		return (tex and tex.type == 'BLEND')

	def draw(self, context):
		layout = self.layout
		tex = context.texture

		layout.itemR(tex, "progression")
		layout.itemR(tex, "flip_axis")
			
class TEXTURE_PT_stucci(TextureButtonsPanel):
	__idname__= "TEXTURE_PT_stucci"
	__label__ = "Stucci"
	
	def poll(self, context):
		tex = context.texture
		return (tex and tex.type == 'STUCCI')

	def draw(self, context):
		layout = self.layout
		tex = context.texture
		
		layout.itemR(tex, "stype", expand=True)
		layout.itemL(text="Noise:")
		layout.itemR(tex, "noise_type", text="Type", expand=True)
		layout.itemR(tex, "noise_basis", text="Basis")
		
		row = layout.row()
		row.itemR(tex, "noise_size", text="Size")
		row.itemR(tex, "turbulence")
		
class TEXTURE_PT_image(TextureButtonsPanel):
	__idname__= "TEXTURE_PT_image"
	__label__ = "Image/Movie"
	
	def poll(self, context):
		tex = context.texture
		return (tex and tex.type == 'IMAGE')

	def draw(self, context):
		layout = self.layout
		tex = context.texture
		
		split = layout.split()
		
		sub = split.column()   		
		sub.itemR(tex, "flip_axis")
		sub.itemR(tex, "normal_map")
		sub.itemL(text="Filter:")
		sub.itemR(tex, "mipmap")
		sub.itemR(tex, "mipmap_gauss")
		sub.itemR(tex, "interpolation")
		sub = split.column() 
		sub.itemL(text="Alpha:")
		sub.itemR(tex, "use_alpha")
		sub.itemR(tex, "calculate_alpha")
		sub.itemR(tex, "invert_alpha")

class TEXTURE_PT_mapping(TextureButtonsPanel):
	__idname__= "TEXTURE_PT_mapping"
	__label__ = "Mapping"
	
	def poll(self, context):
		tex = context.texture
		return (tex and tex.type == 'IMAGE')

	def draw(self, context):
		layout = self.layout
		tex = context.texture
				
		split = layout.split()
		
		sub = split.column()
		#sub.itemR(tex, "crop_rectangle")
		sub.itemL(text="Crop Minimum:")
		sub.itemR(tex, "crop_min_x", text="X")
		sub.itemR(tex, "crop_min_y", text="Y")
		sub = split.column()
		sub.itemL(text="Crop Maximum:")
		sub.itemR(tex, "crop_max_x", text="X")
		sub.itemR(tex, "crop_max_y", text="Y")
		
		layout.itemR(tex, "extension")
		
		split = layout.split()
		
		sub = split.column()
		if tex.extension == 'REPEAT': 
			sub.itemL(text="Repeat:")
			sub.itemR(tex, "repeat_x", text="X")
			sub.itemR(tex, "repeat_y", text="Y")
			sub = split.column()
			sub.itemL(text="Mirror:")
			sub.itemR(tex, "mirror_x", text="X")
			sub.itemR(tex, "mirror_y", text="Y")
		elif tex.extension == 'CHECKER': 
			sub.itemR(tex, "checker_even", text="Even")
			sub.itemR(tex, "checker_odd", text="Odd")
			sub = split.column()
			sub.itemR(tex, "checker_distance", text="Distance")
	
class TEXTURE_PT_plugin(TextureButtonsPanel):
	__idname__= "TEXTURE_PT_plugin"
	__label__ = "Plugin"
	
	def poll(self, context):
		tex = context.texture
		return (tex and tex.type == 'PLUGIN')

	def draw(self, context):
		layout = self.layout
		tex = context.texture
		
		layout.itemL(text="Nothing yet")
		
class TEXTURE_PT_envmap(TextureButtonsPanel):
	__idname__= "TEXTURE_PT_envmap"
	__label__ = "Environment Map"
	
	def poll(self, context):
		tex = context.texture
		return (tex and tex.type == 'ENVIRONMENT_MAP')

	def draw(self, context):
		layout = self.layout
		tex = context.texture
		
		layout.itemL(text="Nothing yet")
		
class TEXTURE_PT_musgrave(TextureButtonsPanel):
	__idname__= "TEXTURE_PT_musgrave"
	__label__ = "Musgrave"
	
	def poll(self, context):
		tex = context.texture
		return (tex and tex.type == 'MUSGRAVE')

	def draw(self, context):
		layout = self.layout
		tex = context.texture
		
		layout.itemR(tex, "musgrave_type")	
		
		split = layout.split()
		
		sub = split.column()
		sub.itemR(tex, "highest_dimension", text="Dimension")
		sub.itemR(tex, "lacunarity")
		sub.itemR(tex, "octaves")
		sub = split.column() 
		if (tex.musgrave_type in ('HETERO_TERRAIN', 'RIDGED_MULTIFRACTAL', 'HYBRID_MULTIFRACTAL')):
			sub.itemR(tex, "offset")
		if (tex.musgrave_type in ('RIDGED_MULTIFRACTAL', 'HYBRID_MULTIFRACTAL')):
			sub.itemR(tex, "gain")
			sub.itemR(tex, "noise_intensity", text="Intensity")
		
		layout.itemL(text="Noise:")
		
		layout.itemR(tex, "noise_basis", text="Basis")
		
		row = layout.row()
		row.itemR(tex, "noise_size", text="Size")
		row.itemR(tex, "nabla")

class TEXTURE_PT_voronoi(TextureButtonsPanel):
	__idname__= "TEXTURE_PT_voronoi"
	__label__ = "Voronoi"
	
	def poll(self, context):
		tex = context.texture
		return (tex and tex.type == 'VORONOI')

	def draw(self, context):
		layout = self.layout
		tex = context.texture
	
		layout.itemR(tex, "distance_metric")
		layout.itemR(tex, "coloring")
		
		split = layout.split()
		
		sub = split.column()   
		
		sub.itemR(tex, "noise_intensity", text="Intensity")
		if tex.distance_metric == 'MINKOVSKY':
			sub.itemR(tex, "minkovsky_exponent", text="Exponent")
		sub = split.column()
		sub.itemR(tex, "feature_weights", slider=True)
		
		layout.itemL(text="Noise:")
		
		row = layout.row()
		row.itemR(tex, "noise_size", text="Size")
		row.itemR(tex, "nabla")
			
class TEXTURE_PT_distortednoise(TextureButtonsPanel):
	__idname__= "TEXTURE_PT_distortednoise"
	__label__ = "Distorted Noise"
	
	def poll(self, context):
		tex = context.texture
		return (tex and tex.type == 'DISTORTED_NOISE')

	def draw(self, context):
		layout = self.layout
		tex = context.texture

		layout.itemR(tex, "noise_distortion")
		layout.itemR(tex, "noise_basis", text="Basis")
		
		split = layout.split()
		
		sub = split.column()
		sub.itemR(tex, "distortion_amount", text="Amount")
		sub.itemR(tex, "noise_size", text="Size")
		
		sub = split.column()
		sub.itemR(tex, "nabla")	

bpy.types.register(TEXTURE_PT_preview)
bpy.types.register(TEXTURE_PT_texture)
bpy.types.register(TEXTURE_PT_colors)
bpy.types.register(TEXTURE_PT_clouds)
bpy.types.register(TEXTURE_PT_wood)
bpy.types.register(TEXTURE_PT_marble)
bpy.types.register(TEXTURE_PT_magic)
bpy.types.register(TEXTURE_PT_blend)
bpy.types.register(TEXTURE_PT_stucci)
bpy.types.register(TEXTURE_PT_image)
bpy.types.register(TEXTURE_PT_mapping)
bpy.types.register(TEXTURE_PT_plugin)
bpy.types.register(TEXTURE_PT_envmap)
bpy.types.register(TEXTURE_PT_musgrave)
bpy.types.register(TEXTURE_PT_voronoi)
bpy.types.register(TEXTURE_PT_distortednoise)

