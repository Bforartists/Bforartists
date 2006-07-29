import Blender
from Blender import Scene, sys, Camera, Object, Image
from Blender.Scene import Render
Vector= Blender.Mathutils.Vector

def imageFromObjectsOrtho(objects, path, width, height, smooth, alpha= True):
	'''
	Takes any number of objects and renders them on the z axis, between x:y-0 and x:y-1
	Usefull for making images from a mesh without per pixel operations
	- objects must be alredy placed
	- path renders to a PNG image
	'''
	
	# remove an extension if its alredy there
	if path.lower().endswith('.png'):
		path= path[:-4] 
	
	path_expand= sys.expandpath(path) + '.png'
	
	# Touch the path
	try:
		f= open(path_expand, 'w')
		f.close()
	except:
		raise 'Error, could not write to path'
	
	
	# RENDER THE FACES.
	scn= Scene.GetCurrent()
	render_scn= Scene.New()
	render_scn.makeCurrent()
	
	# Add objects into the current scene
	for ob in objects:
		render_scn.link(ob)
		# set layers
	
	render_context= render_scn.getRenderingContext()
	render_context.setRenderPath('') # so we can ignore any existing path and save to the abs path.
	
	
	render_context.imageSizeX(width)
	render_context.imageSizeY(height)
	
	if smooth:
		render_context.enableOversampling(True) 
		render_context.setOversamplingLevel(16)
	else:
		render_context.enableOversampling(False) 
	
	render_context.setRenderWinSize(100)
	render_context.setImageType(Render.PNG)
	render_context.enableExtensions(True) 
	#render_context.enableSky() # No alpha needed.
	if alpha:
		render_context.alphaMode= 1
		render_context.enableRGBAColor()
	else:
		render_context.alphaMode= 0
		render_context.enableRGBColor()
	
	render_context.displayMode= 0 # fullscreen
	
	# New camera and object
	render_cam_data= Camera.New('ortho')
	render_cam_ob= Object.New('Camera')
	render_cam_ob.link(render_cam_data)
	render_scn.link(render_cam_ob)
	render_scn.setCurrentCamera(render_cam_ob)
	
	render_cam_data.type= 1 # ortho
	render_cam_data.scale= 1.0
	
	
	# Position the camera
	render_cam_ob.LocZ= 1.0
	render_cam_ob.LocX= 0.5
	render_cam_ob.LocY= 0.5
	
	render_context.render()
	render_context.saveRenderedImage(path)
	# Render.CloseRenderWindow()
	#if not B.sys.exists(PREF_IMAGE_PATH_EXPAND):
	#	raise 'Error!!!'
	
	
	# NOW APPLY THE SAVED IMAGE TO THE FACES!
	#print PREF_IMAGE_PATH_EXPAND
	try:
		target_image= Image.Load(path_expand)
	except:
		raise 'Error: Could not render or load the image at path "%s"' % path_expand
		return
	
	scn.makeCurrent()
	Scene.Unlink(render_scn)







#-----------------------------------------------------------------------------#
# UV Baking functions, make a picture from mesh(es) uvs                       #
#-----------------------------------------------------------------------------#

def mesh2uv(me_s, PREF_SEL_FACES_ONLY=False):
	'''
	Converts a uv mapped mesh into a 2D Mesh from UV coords.
	returns a triple -
	(mesh2d, face_list, col_list)
	"mesh" is the new mesh and...
	"face_list" is the faces that were used to make the mesh,
	"material_list" is a list of materials used by each face
	These are in sync with the meshes faces, so you can easerly copy data between them
	
	'''
	render_me= Blender.Mesh.New()
	render_me.verts.extend( [Vector(0,0,0),] ) # 0 vert uv bugm dummy vert
	face_list= []
	material_list= []
	for me in me_s:
		me_materials= me.materials
		
		if PREF_SEL_FACES_ONLY:
			me_faces= [f for f in me.faces if f.flag & FACE_SEL]
		else:
			me_faces= me.faces
		
		# Keep in sync with render_me.faces
		face_list.extend(me_faces)
		
		# Dittro
		if me_materials:
			material_list.extend([me_materials[f.mat] for f in me_faces])
		else:
			material_list.extend([None]*len(me_faces))
		
	# Now add the verts
	render_me.verts.extend( [ Vector(uv.x, uv.y, 0) for f in face_list for uv in f.uv ] )
	
	# Now add the faces
	tmp_faces= []
	vert_offset= 1
	for f in face_list:
		tmp_faces.append( [ii+vert_offset for ii in xrange(len(f))] )
		vert_offset+= len(f)
	
	render_me.faces.extend(tmp_faces)
	render_me.faceUV=1
	return render_me, face_list, material_list


def uvmesh_apply_normals(render_me, face_list):
	'''Worldspace normals to vertex colors'''
	for i, f in enumerate(render_me.faces):
		face_orig= face_list[i]
		f_col= f.col
		for j, v in enumerate(face_orig):
			c= f_col[j]
			nx, ny, nz= v.no
			c.r= int((nx+1)*128)-1
			c.g= int((ny+1)*128)-1
			c.b= int((nz+1)*128)-1

def uvmesh_apply_image(render_me, face_list):
	'''Copy the image and uvs from the original faces'''
	for i, f in enumerate(render_me.faces):
		f.uv= face_list[i].uv
		f.image= face_list[i].image


def uvmesh_apply_vcol(render_me, face_list):
	'''Copy the vertex colors from the original faces'''
	for i, f in enumerate(render_me.faces):
		face_orig= face_list[i]
		f_col= f.col
		for j, c_orig in enumerate(face_orig.col):
			c= f_col[j]
			c.r= c_orig.r
			c.g= c_orig.g
			c.b= c_orig.b

def uvmesh_apply_matcol(render_me, material_list):
	'''Get the vertex colors from the original materials'''
	for i, f in enumerate(render_me.faces):
		mat_orig= material_list[i]
		f_col= f.col
		if mat_orig:
			for c in f_col:
				c.r= int(mat_orig.R*255)
				c.g= int(mat_orig.G*255)
				c.b= int(mat_orig.B*255)
		else:
			for c in f_col:
				c.r= 255
				c.g= 255
				c.b= 255

def uvmesh_apply_col(render_me, color):
	'''Get the vertex colors from the original materials'''
	r,g,b= color
	for i, f in enumerate(render_me.faces):
		f_col= f.col
		for c in f_col:
			c.r= r
			c.g= g
			c.b= b


def vcol2image(me_s,\
	PREF_IMAGE_PATH,\
	PREF_IMAGE_SIZE,\
	PREF_IMAGE_BLEED,\
	PREF_IMAGE_SMOOTH,\
	PREF_IMAGE_WIRE,\
	PREF_IMAGE_WIRE_INVERT,\
	PREF_IMAGE_WIRE_UNDERLAY,\
	PREF_USE_IMAGE,\
	PREF_USE_VCOL,\
	PREF_USE_MATCOL,\
	PREF_USE_NORMAL,\
	PREF_SEL_FACES_ONLY):
	
	
	def rnd_mat():
		render_mat= Blender.Material.New()
		mode= render_mat.mode
		
		# Dont use lights ever
		mode |= Blender.Material.Modes.SHADELESS
		
		if PREF_IMAGE_WIRE:
			# Set the wire color
			if PREF_IMAGE_WIRE_INVERT:
				render_mat.rgbCol= (1,1,1)
			else:
				render_mat.rgbCol= (0,0,0)
			
			mode |= Blender.Material.Modes.WIRE
		if PREF_USE_VCOL or PREF_USE_MATCOL or PREF_USE_NORMAL: # both vcol and material color use vertex cols to avoid the 16 max limit in materials
			mode |= Blender.Material.Modes.VCOL_PAINT
		if PREF_USE_IMAGE:
			mode |= Blender.Material.Modes.TEXFACE
		
		# Copy back the mode
		render_mat.mode |= mode
		return render_mat
	
	
	render_me, face_list, material_list= mesh2uv(me_s, PREF_SEL_FACES_ONLY)

	# Normals exclude all others
	if PREF_USE_NORMAL:
		uvmesh_apply_normals(render_me, face_list)
	else:
		if PREF_USE_IMAGE:
			uvmesh_apply_image(render_me, face_list)
			uvmesh_apply_vcol(render_me, face_list)
	
		elif PREF_USE_VCOL:
			uvmesh_apply_vcol(render_me, face_list)
		
		elif PREF_USE_MATCOL:
			uvmesh_apply_matcol(render_me, material_list)
	
	# Handel adding objects
	render_ob= Blender.Object.New('Mesh')
	render_me.materials= [rnd_mat()]
	
	render_ob.link(render_me)
	obs= [render_ob]
	
	if PREF_IMAGE_WIRE_UNDERLAY:
		# Make another mesh with the material colors
		render_me_under, face_list, material_list= mesh2uv(me_s, PREF_SEL_FACES_ONLY)
		
		uvmesh_apply_matcol(render_me_under, material_list)
		
		# Handel adding objects
		render_ob= Blender.Object.New('Mesh')
		render_ob.link(render_me_under)
		render_ob.LocZ= -0.01
		
		# Add material and disable wire
		mat= rnd_mat()
		mat.rgbCol= 1,1,1
		mat.alpha= 0.5
		mat.mode &= ~Blender.Material.Modes.WIRE
		mat.mode |= Blender.Material.Modes.VCOL_PAINT
		
		render_me_under.materials= [mat]
		
		obs.append(render_ob)
		
	elif PREF_IMAGE_BLEED and not PREF_IMAGE_WIRE:
		# EVIL BLEEDING CODE!! - Just do copys of the mesh and place behind. Crufty but better then many other methods I have seen. - Cam
		BLEED_PIXEL= 1.0/PREF_IMAGE_SIZE
		z_offset= 0.0
		for i in xrange(PREF_IMAGE_BLEED):
			for diag1, diag2 in ((-1,-1),(-1,1),(1,-1),(1,1), (1,0), (0,1), (-1,0), (0, -1)): # This line extends the object in 8 different directions, top avoid bleeding.
				
				render_ob= Blender.Object.New('Mesh')
				render_ob.link(render_me)
				
				render_ob.LocX= (i+1)*diag1*BLEED_PIXEL
				render_ob.LocY= (i+1)*diag2*BLEED_PIXEL
				render_ob.LocZ= -z_offset
				
				obs.append(render_ob)
				z_offset += 0.01
	
	
	
	im= imageFromObjectsOrtho(obs, PREF_IMAGE_PATH, PREF_IMAGE_SIZE, PREF_IMAGE_SIZE, PREF_IMAGE_SMOOTH)
	
	# Clear from memory as best as we can
	render_me.verts= None
	
	if PREF_IMAGE_WIRE_UNDERLAY:
		render_me_under.verts= None
