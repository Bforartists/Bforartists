import bpy

from math import atan, pi, degrees
import subprocess
import os
import sys
import time

import platform as pltfrm

if pltfrm.architecture()[0] == '64bit':
	bitness = 64
else:
	bitness = 32

def write_pov(filename, scene=None, info_callback = None):
	file = open(filename, 'w')
	
	# Only for testing
	if not scene:
		scene = bpy.data.scenes[0]
	
	render = scene.render_data
	world = scene.world
	
	# --- taken from fbx exporter 
	## This was used to make V, but faster not to do all that
	##valid = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_,.()[]{}'
	##v = range(255)
	##for c in valid: v.remove(ord(c))
	v = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,42,43,46,47,58,59,60,61,62,63,64,92,94,96,124,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192,193,194,195,196,197,198,199,200,201,202,203,204,205,206,207,208,209,210,211,212,213,214,215,216,217,218,219,220,221,222,223,224,225,226,227,228,229,230,231,232,233,234,235,236,237,238,239,240,241,242,243,244,245,246,247,248,249,250,251,252,253,254]
	invalid = ''.join([chr(i) for i in v])
	def cleanName(name):
		for ch in invalid:	name = name.replace(ch, '_')
		return name
	del v
	
	# --- done with clean name.
	
	def uniqueName(name, nameSeq):
		
		if name not in nameSeq:
			return name
		
		name_orig = name
		i = 1
		while name in nameSeq:
			name = '%s_%.3d' % (name_orig, i)
			i+=1
		
		return name
		
	
	def writeMatrix(matrix):
		file.write('\tmatrix <%.6f, %.6f, %.6f,  %.6f, %.6f, %.6f,  %.6f, %.6f, %.6f,  %.6f, %.6f, %.6f>\n' %\
		(matrix[0][0], matrix[0][1], matrix[0][2],  matrix[1][0], matrix[1][1], matrix[1][2],  matrix[2][0], matrix[2][1], matrix[2][2],  matrix[3][0], matrix[3][1], matrix[3][2]) )
	
	def writeObjectMaterial(material):
		if material and material.transparency_method=='RAYTRACE':
			file.write('\tinterior { ior %.6f }\n' % material.raytrace_transparency.ior)
			
			# Other interior args
			# fade_distance 2
			# fade_power [Value]
			# fade_color
			
			# dispersion
			# dispersion_samples
	
	materialNames = {}
	DEF_MAT_NAME = 'Default'
	def writeMaterial(material):
		# Assumes only called once on each material
		
		if material:
			name_orig = material.name
		else:
			name_orig = DEF_MAT_NAME
		
		name = materialNames[name_orig] = uniqueName(cleanName(name_orig), materialNames)
		
		file.write('#declare %s = finish {\n' % name)
		
		if material:
			file.write('\tdiffuse %.3g\n' % material.diffuse_reflection)
			file.write('\tspecular %.3g\n' % material.specular_reflection)
			
			file.write('\tambient %.3g\n' % material.ambient)
			#file.write('\tambient rgb <%.3g, %.3g, %.3g>\n' % tuple([c*material.ambient for c in world.ambient_color])) # povray blends the global value
			
			# map hardness between 0.0 and 1.0
			roughness = ((1.0 - ((material.specular_hardness-1.0)/510.0)))
			# scale from 0.0 to 0.1
			roughness *= 0.1
			# add a small value because 0.0 is invalid
			roughness += (1/511.0)
			
			file.write('\troughness %.3g\n' % roughness)
			
			# 'phong 70.0 '
			
			if material.raytrace_mirror.enabled:
				raytrace_mirror= material.raytrace_mirror
				if raytrace_mirror.reflect:
					file.write('\treflection {\n')
					file.write('\t\trgb <%.3g, %.3g, %.3g>' % tuple(material.mirror_color))
					file.write('\t\tfresnel 1 falloff %.3g exponent %.3g metallic %.3g} ' % (raytrace_mirror.fresnel, raytrace_mirror.fresnel_fac, raytrace_mirror.reflect))
		
		else:
			file.write('\tdiffuse 0.8\n')
			file.write('\tspecular 0.2\n')
			
			
		
		# This is written into the object
		'''
		if material and material.transparency_method=='RAYTRACE':
			'interior { ior %.3g} ' % material.raytrace_transparency.ior
		'''
		
		#file.write('\t\t\tcrand 1.0\n') # Sand granyness
		#file.write('\t\t\tmetallic %.6f\n' % material.spec)
		#file.write('\t\t\tphong %.6f\n' % material.spec)
		#file.write('\t\t\tphong_size %.6f\n' % material.spec)
		#file.write('\t\t\tbrilliance %.6f ' % (material.specular_hardness/256.0) # Like hardness
		
		file.write('}\n')
	
	def exportCamera():
		camera = scene.camera
		matrix = camera.matrix
		
		# compute resolution
		Qsize=float(render.resolution_x)/float(render.resolution_y)
		
		file.write('camera {\n')
		file.write('\tlocation  <0, 0, 0>\n')
		file.write('\tlook_at  <0, 0, -1>\n')
		file.write('\tright <%s, 0, 0>\n' % -Qsize)
		file.write('\tup <0, 1, 0>\n')
		file.write('\tangle  %f \n' % (360.0*atan(16.0/camera.data.lens)/pi))
		
		file.write('\trotate  <%.6f, %.6f, %.6f>\n' % tuple([degrees(e) for e in matrix.rotationPart().toEuler()]))
		file.write('\ttranslate <%.6f, %.6f, %.6f>\n' % (matrix[3][0], matrix[3][1], matrix[3][2]))
		file.write('}\n')
	
	
	
	def exportLamps(lamps):
		# Get all lamps
		for ob in lamps:
			lamp = ob.data
			
			matrix = ob.matrix
			
			color = tuple([c * lamp.energy for c in lamp.color]) # Colour is modified by energy
			
			file.write('light_source {\n')
			file.write('\t< 0,0,0 >\n')
			file.write('\tcolor rgb<%.3g, %.3g, %.3g>\n' % color)
			
			if lamp.type == 'POINT': # Point Lamp 
				pass
			elif lamp.type == 'SPOT': # Spot
				file.write('\tspotlight\n')
				
				# Falloff is the main radius from the centre line
				file.write('\tfalloff %.2f\n' % (lamp.spot_size/2.0) ) # 1 TO 179 FOR BOTH
				file.write('\tradius %.6f\n' % ((lamp.spot_size/2.0) * (1-lamp.spot_blend)) ) 
				
				# Blender does not have a tightness equivilent, 0 is most like blender default.
				file.write('\ttightness 0\n') # 0:10f
				
				file.write('\tpoint_at  <0, 0, -1>\n')
			elif lamp.type == 'SUN':
				file.write('\tparallel\n')
				file.write('\tpoint_at  <0, 0, -1>\n') # *must* be after 'parallel'
				
			elif lamp.type == 'AREA':
				
				size_x = lamp.size
				samples_x = lamp.shadow_ray_samples_x
				if lamp.shape == 'SQUARE':
					size_y = size_x
					samples_y = samples_x
				else:
					size_y = lamp.size_y
					samples_y = lamp.shadow_ray_samples_y
				
				
				
				file.write('\tarea_light <%d,0,0>,<0,0,%d> %d, %d\n' % (size_x, size_y, samples_x, samples_y))
				if lamp.shadow_ray_sampling_method == 'CONSTANT_JITTERED':
					if lamp.jitter:
						file.write('\tjitter\n')
				else:
					file.write('\tadaptive 1\n')
					file.write('\tjitter\n')
			
			if lamp.shadow_method == 'NOSHADOW':
				file.write('\tshadowless\n')	
			
			file.write('\tfade_distance %.6f\n' % lamp.distance)
			file.write('\tfade_power %d\n' % 1) # Could use blenders lamp quad?
			writeMatrix(matrix)
			
			file.write('}\n')
	
	def exportMeta(metas):
		
		# TODO - blenders 'motherball' naming is not supported.
		
		for ob in metas:
			meta = ob.data
			
			file.write('blob {\n')
			file.write('\t\tthreshold %.4g\n' % meta.threshold)
			
			try:
				material= meta.materials[0] # lame! - blender cant do enything else.
			except:
				material= None
			
			for elem in meta.elements:
				
				if elem.type not in ('BALL', 'ELLIPSOID'):
					continue # Not supported
				
				loc = elem.location
				
				stiffness= elem.stiffness
				if elem.negative:
					stiffness = -stiffness
				
				if elem.type == 'BALL':
					
					file.write('\tsphere { <%.6g, %.6g, %.6g>, %.4g, %.4g ' % (loc.x, loc.y, loc.z, elem.radius, stiffness))
					
					# After this wecould do something simple like...
					# 	"pigment {Blue} }"
					# except we'll write the color
				
				elif elem.type == 'ELLIPSOID':
					# location is modified by scale
					file.write('\tsphere { <%.6g, %.6g, %.6g>, %.4g, %.4g ' % (loc.x/elem.size_x, loc.y/elem.size_y, loc.z/elem.size_z, elem.radius, stiffness))
					file.write(	'scale <%.6g, %.6g, %.6g> ' % (elem.size_x, elem.size_y, elem.size_z))
				
				if material:
					diffuse_color = material.diffuse_color
					
					if material.transparency and material.transparency_method=='RAYTRACE':	trans = 1-material.raytrace_transparency.filter
					else:																	trans = 0.0
					
					file.write(
						'pigment {rgbft<%.3g, %.3g, %.3g, %.3g, %.3g>} finish {%s} }\n' % \
						(diffuse_color[0], diffuse_color[1], diffuse_color[2], 1-material.alpha, trans, materialNames[material.name])
					)
					
				else:
					file.write('pigment {rgb<1 1 1>} finish {%s} }\n' % DEF_MAT_NAME)		# Write the finish last.
			
			writeObjectMaterial(material)

			writeMatrix(ob.matrix)
			
			file.write('}\n')
		
		
	
	
	def exportMeshs(sel):
		
		ob_num = 0
		
		for ob in sel:
			ob_num+= 1
			
			if ob.type in ('LAMP', 'CAMERA', 'EMPTY'):
				continue
			
			me = ob.data
			me_materials= me.materials
			
			me = ob.create_render_mesh(scene)
			
			if not me:
				continue
			
			if info_callback:
				info_callback('Object %2.d of %2.d (%s)' % (ob_num, len(sel), ob.name))
			
			#if ob.type!='MESH':
			#	continue
			# me = ob.data
			
			matrix = ob.matrix
			try:	uv_layer = me.active_uv_texture.data
			except:uv_layer = None
				
			try:	vcol_layer = me.active_vertex_color.data
			except:vcol_layer = None
			
			
			def regular_face(f):
				fv = f.verts
				if fv[3]== 0:
					return fv[0], fv[1], fv[2]
				return fv[0], fv[1], fv[2], fv[3]
			
			faces_verts = [regular_face(f) for f in me.faces]
			faces_normals = [tuple(f.normal) for f in me.faces]
			verts_normals = [tuple(v.normal) for v in me.verts]
			
			# quads incur an extra face
			quadCount = len([f for f in faces_verts if len(f)==4])
			
			file.write('mesh2 {\n')
			file.write('\tvertex_vectors {\n')
			file.write('\t\t%s' % (len(me.verts))) # vert count
			for v in me.verts:
				file.write(',\n\t\t<%.6f, %.6f, %.6f>' % tuple(v.co)) # vert count
			file.write('\n  }\n')
			
			
			# Build unique Normal list
			uniqueNormals = {}
			for fi, f in enumerate(me.faces):
				fv = faces_verts[fi]
				# [-1] is a dummy index, use a list so we can modify in place
				if f.smooth: # Use vertex normals
					for v in fv:
						key = verts_normals[v]
						uniqueNormals[key] = [-1]
				else: # Use face normal
					key = faces_normals[fi]
					uniqueNormals[key] = [-1]
			
			file.write('\tnormal_vectors {\n')
			file.write('\t\t%d' % len(uniqueNormals)) # vert count
			idx = 0
			for no, index in uniqueNormals.items():
				file.write(',\n\t\t<%.6f, %.6f, %.6f>' % no) # vert count
				index[0] = idx
				idx +=1
			file.write('\n  }\n')
			
			
			# Vertex colours
			vertCols = {} # Use for material colours also.
			
			if uv_layer:
				# Generate unique UV's
				uniqueUVs = {}
				
				for fi, uv in enumerate(uv_layer):
					
					if len(faces_verts[fi])==4:
						uvs = uv.uv1, uv.uv2, uv.uv3, uv.uv4
					else:
						uvs = uv.uv1, uv.uv2, uv.uv3
					
					for uv in uvs:
						uniqueUVs[tuple(uv)] = [-1]
				
				file.write('\tuv_vectors {\n')
				#print unique_uvs
				file.write('\t\t%s' % (len(uniqueUVs))) # vert count
				idx = 0
				for uv, index in uniqueUVs.items():
					file.write(',\n\t\t<%.6f, %.6f>' % uv)
					index[0] = idx
					idx +=1
				'''
				else:
					# Just add 1 dummy vector, no real UV's
					file.write('\t\t1') # vert count
					file.write(',\n\t\t<0.0, 0.0>')
				'''
				file.write('\n  }\n')
			
			
			if me.vertex_colors:
				
				for fi, f in enumerate(me.faces):
					material_index = f.material_index
					material = me_materials[material_index]
					
					if material and material.vertex_color_paint:
						
						col = vcol_layer[fi]
						
						if len(faces_verts[fi])==4:
							cols = col.color1, col.color2, col.color3, col.color4
						else:
							cols = col.color1, col.color2, col.color3
						
						for col in cols:					
							key = col[0], col[1], col[2], material_index # Material index!
							vertCols[key] = [-1]
						
					else:
						if material:
							diffuse_color = tuple(material.diffuse_color)
							key = diffuse_color[0], diffuse_color[1], diffuse_color[2], material_index
							vertCols[key] = [-1]
						
			
			else:
				# No vertex colours, so write material colours as vertex colours
				for i, material in enumerate(me_materials):
					
					if material:
						diffuse_color = tuple(material.diffuse_color)
						key = diffuse_color[0], diffuse_color[1], diffuse_color[2], i # i == f.mat
						vertCols[key] = [-1]
				
			
			# Vert Colours
			file.write('\ttexture_list {\n')
			file.write('\t\t%s' % (len(vertCols))) # vert count
			idx=0
			for col, index in vertCols.items():
				
				if me_materials:
					material = me_materials[col[3]]
					material_finish = materialNames[material.name]
					
					if material.transparency and material.transparency_method=='RAYTRACE':	trans = 1-material.raytrace_transparency.filter
					else:																	trans = 0.0
					
				else:
					material_finish = DEF_MAT_NAME # not working properly,
					trans = 0.0
				
				#print material.apl
				file.write(	',\n\t\ttexture { pigment {rgbft<%.3g, %.3g, %.3g, %.3g, %.3g>} finish {%s}}' %
							(col[0], col[1], col[2], 1-material.alpha, trans, material_finish) )
				
				index[0] = idx
				idx+=1
			
			file.write( '\n  }\n' )
			
			# Face indicies
			file.write('\tface_indices {\n')
			file.write('\t\t%d' % (len(me.faces) + quadCount)) # faces count
			for fi, f in enumerate(me.faces):
				fv = faces_verts[fi]
				material_index= f.material_index
				if len(fv) == 4:	indicies = (0,1,2), (0,2,3)
				else:				indicies = ((0,1,2),)
				
				if vcol_layer:
					col = vcol_layer[fi]
					
					if len(fv) == 4:
						cols = col.color1, col.color2, col.color3, col.color4
					else:
						cols = col.color1, col.color2, col.color3
				
				
				if not me_materials or me_materials[material_index] == None: # No materials
					for i1, i2, i3 in indicies:
						file.write(',\n\t\t<%d,%d,%d>' % (fv[i1], fv[i2], fv[i3])) # vert count
				else:
					material = me_materials[material_index]
					for i1, i2, i3 in indicies:
						if me.vertex_colors and material.vertex_color_paint:
							# Colour per vertex - vertex colour
							
							col1 = cols[i1]
							col2 = cols[i2]
							col3 = cols[i3]
						
							ci1 = vertCols[col1[0], col1[1], col1[2], material_index][0]
							ci2 = vertCols[col2[0], col2[1], col2[2], material_index][0]
							ci3 = vertCols[col3[0], col3[1], col3[2], material_index][0]
						else:
							# Colour per material - flat material colour
							diffuse_color= material.diffuse_color
							ci1 = ci2 = ci3 = vertCols[diffuse_color[0], diffuse_color[1], diffuse_color[2], f.material_index][0]
						
						file.write(',\n\t\t<%d,%d,%d>, %d,%d,%d' % (fv[i1], fv[i2], fv[i3], ci1, ci2, ci3)) # vert count
					
					
					
			file.write('\n  }\n')
			
			# normal_indices indicies
			file.write('\tnormal_indices {\n')
			file.write('\t\t%d' % (len(me.faces) + quadCount)) # faces count
			for fi, fv in enumerate(faces_verts):
				
				if len(fv) == 4:	indicies = (0,1,2), (0,2,3)
				else:				indicies = ((0,1,2),)
				
				for i1, i2, i3 in indicies:
					if f.smooth:
						file.write(',\n\t\t<%d,%d,%d>' %\
						(uniqueNormals[verts_normals[fv[i1]]][0],\
						 uniqueNormals[verts_normals[fv[i2]]][0],\
						 uniqueNormals[verts_normals[fv[i3]]][0])) # vert count
					else:
						idx = uniqueNormals[faces_normals[fi]][0]
						file.write(',\n\t\t<%d,%d,%d>' % (idx, idx, idx)) # vert count
						
			file.write('\n  }\n')
			
			if uv_layer:
				file.write('\tuv_indices {\n')
				file.write('\t\t%d' % (len(me.faces) + quadCount)) # faces count
				for fi, fv in enumerate(faces_verts):
					
					if len(fv) == 4:	indicies = (0,1,2), (0,2,3)
					else:				indicies = ((0,1,2),)
					
					uv = uv_layer[fi]
					if len(faces_verts[fi])==4:
						uvs = tuple(uv.uv1), tuple(uv.uv2), tuple(uv.uv3), tuple(uv.uv4)
					else:
						uvs = tuple(uv.uv1), tuple(uv.uv2), tuple(uv.uv3)
					
					for i1, i2, i3 in indicies:
						file.write(',\n\t\t<%d,%d,%d>' %\
						(uniqueUVs[uvs[i1]][0],\
						 uniqueUVs[uvs[i2]][0],\
						 uniqueUVs[uvs[i2]][0])) # vert count
				file.write('\n  }\n')
			
			if me.materials:
				material = me.materials[0] # dodgy
				writeObjectMaterial(material)
			
			writeMatrix(matrix)
			file.write('}\n')
			
			bpy.data.remove_mesh(me)
	
	def exportWorld(world):
		if not world:
			return
		
		mist = world.mist
		
		if mist.enabled:
			file.write('fog {\n')
			file.write('\tdistance %.6f\n' % mist.depth)
			file.write('\tcolor rgbt<%.3g, %.3g, %.3g, %.3g>\n' % (tuple(world.horizon_color) + (1-mist.intensity,)))
			#file.write('\tfog_offset %.6f\n' % mist.start)
			#file.write('\tfog_alt 5\n')
			#file.write('\tturbulence 0.2\n')
			#file.write('\tturb_depth 0.3\n')
			file.write('\tfog_type 1\n')
			file.write('}\n')
	
	def exportGlobalSettings(scene):
		
		file.write('global_settings {\n')

		if scene.pov_radio_enable:
			file.write('\tradiosity {\n')
			file.write("\t\tadc_bailout %.4g\n" % scene.pov_radio_adc_bailout)
			file.write("\t\talways_sample %d\n" % scene.pov_radio_always_sample)
			file.write("\t\tbrightness %.4g\n" % scene.pov_radio_brightness)
			file.write("\t\tcount %d\n" % scene.pov_radio_count)
			file.write("\t\terror_bound %.4g\n" % scene.pov_radio_error_bound)
			file.write("\t\tgray_threshold %.4g\n" % scene.pov_radio_gray_threshold)
			file.write("\t\tlow_error_factor %.4g\n" % scene.pov_radio_low_error_factor)
			file.write("\t\tmedia %d\n" % scene.pov_radio_media)
			file.write("\t\tminimum_reuse %.4g\n" % scene.pov_radio_minimum_reuse)
			file.write("\t\tnearest_count %d\n" % scene.pov_radio_nearest_count)
			file.write("\t\tnormal %d\n" % scene.pov_radio_normal)
			file.write("\t\trecursion_limit %d\n" % scene.pov_radio_recursion_limit)
			file.write('\t}\n')
		
		if world:
			file.write("\tambient_light rgb<%.3g, %.3g, %.3g>\n" % tuple(world.ambient_color))
		
		file.write('}\n')
	
	
	# Convert all materials to strings we can access directly per vertex.
	writeMaterial(None) # default material
	
	for material in bpy.data.materials:
		writeMaterial(material)
	
	exportCamera()
	#exportMaterials()
	sel = scene.objects
	exportLamps([l for l in sel if l.type == 'LAMP'])
	exportMeta([l for l in sel if l.type == 'META'])
	exportMeshs(sel)
	exportWorld(scene.world)
	exportGlobalSettings(scene)
	
	file.close()


def write_pov_ini(filename_ini, filename_pov, filename_image):
	scene = bpy.data.scenes[0]
	render = scene.render_data
	
	x= int(render.resolution_x*render.resolution_percentage*0.01)
	y= int(render.resolution_y*render.resolution_percentage*0.01)
	
	file = open(filename_ini, 'w')
	
	file.write('Input_File_Name="%s"\n' % filename_pov)
	file.write('Output_File_Name="%s"\n' % filename_image)
	
	file.write('Width=%d\n' % x)
	file.write('Height=%d\n' % y)
	
	# Needed for border render.
	'''
	file.write('Start_Column=%d\n' % part.x)
	file.write('End_Column=%d\n' % (part.x+part.w))
	
	file.write('Start_Row=%d\n' % (part.y))
	file.write('End_Row=%d\n' % (part.y+part.h))
	'''
	
	file.write('Display=0\n')
	file.write('Pause_When_Done=0\n')
	file.write('Output_File_Type=C\n') # TGA, best progressive loading
	file.write('Output_Alpha=1\n')
	
	if render.antialiasing: 
		aa_mapping = {'OVERSAMPLE_5':2, 'OVERSAMPLE_8':3, 'OVERSAMPLE_11':4, 'OVERSAMPLE_16':5} # method 1 assumed
		file.write('Antialias=1\n')
		file.write('Antialias_Depth=%d\n' % aa_mapping[render.antialiasing_samples])
	else:
		file.write('Antialias=0\n')
	
	file.close()


class PovrayRender(bpy.types.RenderEngine):
	__idname__ = 'POVRAY_RENDER'
	__label__ = "Povray"
	DELAY = 0.02
	def _export(self, scene):
		import tempfile
		
		self.temp_file_in = tempfile.mktemp(suffix='.pov')
		self.temp_file_out = tempfile.mktemp(suffix='.tga')
		self.temp_file_ini = tempfile.mktemp(suffix='.ini')
		'''
		self.temp_file_in = '/test.pov'
		self.temp_file_out = '/test.tga'
		self.temp_file_ini = '/test.ini'
		'''
		
		def info_callback(txt):
			self.update_stats("", "POVRAY: " + txt)
			
		write_pov(self.temp_file_in, scene, info_callback)
		
	def _render(self):
		
		try:		os.remove(self.temp_file_out) # so as not to load the old file
		except:	pass
		
		write_pov_ini(self.temp_file_ini, self.temp_file_in, self.temp_file_out)
		
		print ("***-STARTING-***")
		
		pov_binary = "povray"
		
		if sys.platform=='win32':
			if bitness == 64:
				pov_binary = "pvengine64"
			else:
				pov_binary = "pvengine"
			
		if 1:
			self.process = subprocess.Popen([pov_binary, self.temp_file_ini]) # stdout=subprocess.PIPE, stderr=subprocess.PIPE
		else:
			# This works too but means we have to wait until its done
			os.system('%s %s' % (pov_binary, self.temp_file_ini))
		
		print ("***-DONE-***")
	
	def _cleanup(self):
		for f in (self.temp_file_in, self.temp_file_ini, self.temp_file_out):
			try:		os.remove(f)
			except:	pass
		
		self.update_stats("", "")
	
	def render(self, scene):
		
		self.update_stats("", "POVRAY: Exporting data from Blender")
		self._export(scene)
		self.update_stats("", "POVRAY: Parsing File")
		self._render()
		
		r = scene.render_data
		
		# compute resolution
		x= int(r.resolution_x*r.resolution_percentage*0.01)
		y= int(r.resolution_y*r.resolution_percentage*0.01)
		
		
		
		# Wait for the file to be created
		while not os.path.exists(self.temp_file_out):
			if self.test_break():
				try:		self.process.terminate()
				except:	pass
				break
			
			if self.process.poll() != None:
				self.update_stats("", "POVRAY: Failed")
				break
			
			time.sleep(self.DELAY)
		
		if os.path.exists(self.temp_file_out):
			
			self.update_stats("", "POVRAY: Rendering")
			
			prev_size = -1
			
			def update_image():
				result = self.begin_result(0, 0, x, y)
				lay = result.layers[0]
				# possible the image wont load early on.
				try:		lay.load_from_file(self.temp_file_out)
				except:	pass
				self.end_result(result)
			
			# Update while povray renders
			while True:
				
				# test if povray exists
				if self.process.poll() != None:
					update_image();
					break
				
				# user exit
				if self.test_break():
					try:		self.process.terminate()
					except:	pass
					
					break
				
				# Would be nice to redirect the output
				# stdout_value, stderr_value = self.process.communicate() # locks
				
				
				# check if the file updated
				new_size = os.path.getsize(self.temp_file_out)
				
				if new_size != prev_size:
					update_image()
					prev_size = new_size
				
				time.sleep(self.DELAY)
		
		self._cleanup()


bpy.types.register(PovrayRender)



# Use some of the existing buttons.
import buttons_scene
buttons_scene.SCENE_PT_render.COMPAT_ENGINES.add('POVRAY_RENDER')
buttons_scene.SCENE_PT_dimensions.COMPAT_ENGINES.add('POVRAY_RENDER')
buttons_scene.SCENE_PT_antialiasing.COMPAT_ENGINES.add('POVRAY_RENDER')
buttons_scene.SCENE_PT_output.COMPAT_ENGINES.add('POVRAY_RENDER')
del buttons_scene

# Use only a subset of the world panels
import buttons_world
buttons_world.WORLD_PT_preview.COMPAT_ENGINES.add('POVRAY_RENDER')
buttons_world.WORLD_PT_context_world.COMPAT_ENGINES.add('POVRAY_RENDER')
buttons_world.WORLD_PT_world.COMPAT_ENGINES.add('POVRAY_RENDER')
buttons_world.WORLD_PT_mist.COMPAT_ENGINES.add('POVRAY_RENDER')
del buttons_world

# Example of wrapping every class 'as is'
import buttons_material
for member in dir(buttons_material):
	subclass = getattr(buttons_material, member)
	try:		subclass.COMPAT_ENGINES.add('POVRAY_RENDER')
	except:	pass
del buttons_material

class RenderButtonsPanel(bpy.types.Panel):
	__space_type__ = 'PROPERTIES'
	__region_type__ = 'WINDOW'
	__context__ = "scene"
	# COMPAT_ENGINES must be defined in each subclass, external engines can add themselves here
	
	def poll(self, context):
		rd = context.scene.render_data
		return (rd.use_game_engine==False) and (rd.engine in self.COMPAT_ENGINES)

# Radiosity panel, use in the scene for now.
class SCENE_PT_povray_radiosity(RenderButtonsPanel):
	__label__ = "Radiosity"
	COMPAT_ENGINES = set(['POVRAY_RENDER'])

	def draw_header(self, context):
		layout = self.layout
		scene = context.scene
		layout.itemR(scene, "pov_radio_enable", text="")

	def draw(self, context):
		layout = self.layout
		scene = context.scene
		rd = scene.render_data
		
		layout.active = scene.pov_radio_enable
		
		split = layout.split()
		
		col = split.column()
		
		col.itemR(scene, "pov_radio_count", text="Rays")
		col.itemR(scene, "pov_radio_recursion_limit", text="Recursions")
		col = split.column()
		col.itemR(scene, "pov_radio_error_bound", text="Error")
		
		layout.itemR(scene, "pov_radio_display_advanced")
		
		if scene.pov_radio_display_advanced:
			split = layout.split()
		
			col = split.column()
			col.itemR(scene, "pov_radio_adc_bailout", slider=True)
			col.itemR(scene, "pov_radio_gray_threshold", slider=True)
			col.itemR(scene, "pov_radio_low_error_factor", slider=True)
			
			
			
			col = split.column()
			col.itemR(scene, "pov_radio_brightness")
			col.itemR(scene, "pov_radio_minimum_reuse", text="Min Reuse")
			col.itemR(scene, "pov_radio_nearest_count")
			
			
			split = layout.split()
		
			col = split.column()
			col.itemL(text="Estimation Influence:")
			col.itemR(scene, "pov_radio_media")
			col.itemR(scene, "pov_radio_normal")
			
			col = split.column()
			col.itemR(scene, "pov_radio_always_sample")
		

bpy.types.register(SCENE_PT_povray_radiosity)


FloatProperty= bpy.types.Scene.FloatProperty
IntProperty= bpy.types.Scene.IntProperty
BoolProperty= bpy.types.Scene.BoolProperty

# Not a real pov option, just to know if we should write
BoolProperty(	attr="pov_radio_enable",
				name="Enable Radiosity",
				description="Enable povrays radiosity calculation.",
				default= False)
BoolProperty(	attr="pov_radio_display_advanced",
				name="Advanced Options",
				description="Show advanced options.",
				default= False)

# Real pov options
FloatProperty(	attr="pov_radio_adc_bailout",
				name="ADC Bailout",
				description="The adc_bailout for radiosity rays. Use adc_bailout = 0.01 / brightest_ambient_object for good results.",
				min=0.0, max=1000.0, soft_min=0.0, soft_max=1.0, default= 0.01)

BoolProperty(	attr="pov_radio_always_sample",
				name="Always Sample",
				description="Only use the data from the pretrace step and not gather any new samples during the final radiosity pass..",
				default= True)

FloatProperty(	attr="pov_radio_brightness",
				name="Brightness",
				description="Ammount objects are brightened before being returned upwards to the rest of the system.",
				min=0.0, max=1000.0, soft_min=0.0, soft_max=10.0, default= 1.0)

IntProperty(	attr="pov_radio_count",
				name="Ray Count",
				description="number of rays that are sent out whenever a new radiosity value has to be calculated.",
				min=1, max=1600, default= 35)

FloatProperty(	attr="pov_radio_error_bound",
				name="Error Bound",
				description="one of the two main speed/quality tuning values, lower values are more accurate.",
				min=0.0, max=1000.0, soft_min=0.1, soft_max=10.0, default= 1.8)

FloatProperty(	attr="pov_radio_gray_threshold",
				name="Gray Threshold",
				description="one of the two main speed/quality tuning values, lower values are more accurate.",
				min=0.0, max=1.0, soft_min=0, soft_max=1, default= 0.0)
								
FloatProperty(	attr="pov_radio_low_error_factor",
				name="Low Error Factor",
				description="If you calculate just enough samples, but no more, you will get an image which has slightly blotchy lighting.",
				min=0.0, max=1.0, soft_min=0.0, soft_max=1.0, default= 0.5)

# max_sample - not available yet

BoolProperty(	attr="pov_radio_media",
				name="Media",
				description="Radiosity estimation can be affected by media.",
				default= False)

FloatProperty(	attr="pov_radio_minimum_reuse",
				name="Minimum Reuse",
				description="Fraction of the screen width which sets the minimum radius of reuse for each sample point (At values higher than 2% expect errors).",
				min=0.0, max=1.0, soft_min=0.1, soft_max=0.1, default= 0.015)
				
IntProperty(	attr="pov_radio_nearest_count",
				name="Nearest Count",
				description="Number of old ambient values blended together to create a new interpolated value.",
				min=1, max=20, default= 5)
				
BoolProperty(	attr="pov_radio_normal",
				name="Normals",
				description="Radiosity estimation can be affected by normals.",
				default= False)

IntProperty(	attr="pov_radio_recursion_limit",
				name="Recursion Limit",
				description="how many recursion levels are used to calculate the diffuse inter-reflection.",
				min=1, max=20, default= 3)
