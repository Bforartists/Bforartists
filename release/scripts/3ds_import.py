#!BPY
""" 
Name: '3D Studio (.3ds)...'
Blender: 241
Group: 'Import'
Tooltip: 'Import from 3DS file format (.3ds)'
"""

__author__ = ["Bob Holcomb", "Richard L�rk�ng", "Damien McGinnes", "Campbell Barton"]
__url__ = ("blender", "elysiun", "http://www.gametutorials.com")
__version__ = "0.93"
__bpydoc__ = """\

3ds Importer

This script imports a 3ds file and the materials into Blender for editing.

Loader is based on 3ds loader from www.gametutorials.com (Thanks DigiBen).


0.93 by Campbell Barton<br> 
- Tested with 400 3ds files from turbosquid and samples.
- Tactfully ignore faces that used the same verts twice.
- Rollback to 0.83 sloppy un-reorganized code, this broke UV coord loading.
- Converted from NMesh to Mesh.
- Faster and cleaner new names.
- Use external comprehensive image loader.
- Re intergrated 0.92 and 0.9 changes
- Fixes for 2.41 compat.
- Non textured faces do not use a texture flag.

0.92<br>
- Added support for diffuse, alpha, spec, bump maps in a single material

0.9<br>
- Reorganized code into object/material block functions<br>
- Use of Matrix() to copy matrix data<br>
- added support for material transparency<br>

0.83 2005-08-07: Campell Barton
-  Aggressive image finding and case insensitivy for posisx systems.

0.82a 2005-07-22
- image texture loading (both for face uv and renderer)

0.82 - image texture loading (for face uv)

0.81a (fork- not 0.9) Campbell Barton 2005-06-08
- Simplified import code
- Never overwrite data
- Faster list handling
- Leaves import selected

0.81 Damien McGinnes 2005-01-09
- handle missing images better
    
0.8 Damien McGinnes 2005-01-08
- copies sticky UV coords to face ones
- handles images better
- Recommend that you run 'RemoveDoubles' on each imported mesh after using this script

"""

# Importing modules

import Blender
from Blender import Mesh, Scene, Object, Material, Image, Texture, Lamp, Mathutils
from Blender.Mathutils import Vector
import BPyImage
reload(BPyImage)

import struct

import os

#this script imports uvcoords as sticky vertex coords
#this parameter enables copying these to face uv coords
#which shold be more useful.


#===========================================================================#
# Returns unique name of object/mesh (stops overwriting existing meshes)    #
#===========================================================================#
def getUniqueName(name):
	count = 0
	newname = name[:19]
	while newname in getUniqueName.uniqueObNames:
		newname = '%s.%.3i' % (name[:15], count)
		count+=1
	# Dont use again.
	getUniqueName.uniqueObNames.append(newname)
	return newname
getUniqueName.uniqueObNames = Blender.NMesh.GetNames() + [ob.name for ob in Object.Get()]

def createBlenderTexture(material, name, image):
	texture = Texture.New(name)
	texture.setType('Image')
	texture.image = image
	material.setTexture(0, texture, Texture.TexCo.UV, Texture.MapTo.COL)



######################################################
# Data Structures
######################################################

#Some of the chunks that we will see
#----- Primary Chunk, at the beginning of each file
PRIMARY= long("0x4D4D",16)

#------ Main Chunks
OBJECTINFO   =      long("0x3D3D",16);      #This gives the version of the mesh and is found right before the material and object information
VERSION      =      long("0x0002",16);      #This gives the version of the .3ds file
EDITKEYFRAME=      long("0xB000",16);      #This is the header for all of the key frame info

#------ sub defines of OBJECTINFO
MATERIAL=45055		#0xAFFF				// This stored the texture info
OBJECT=16384		#0x4000				// This stores the faces, vertices, etc...

#>------ sub defines of MATERIAL
#------ sub defines of MATERIAL_BLOCK
MAT_NAME		=	long("0xA000",16)	# This holds the material name
MAT_AMBIENT		=	long("0xA010",16)	# Ambient color of the object/material
MAT_DIFFUSE		=	long("0xA020",16)	# This holds the color of the object/material
MAT_SPECULAR	=	long("0xA030",16)	# SPecular color of the object/material
MAT_SHINESS		=	long("0xA040",16)	# ??
MAT_TRANSPARENCY=	long("0xA050",16)	# Transparency value of material
MAT_SELF_ILLUM	=	long("0xA080",16)	# Self Illumination value of material
MAT_WIRE		=	long("0xA085",16)	# Only render's wireframe

MAT_TEXTURE_MAP	=	long("0xA200",16)	# This is a header for a new texture map
MAT_SPECULAR_MAP=	long("0xA204",16)	# This is a header for a new specular map
MAT_OPACITY_MAP	=	long("0xA210",16)	# This is a header for a new opacity map
MAT_REFLECTION_MAP=	long("0xA220",16)	# This is a header for a new reflection map
MAT_BUMP_MAP	=	long("0xA230",16)	# This is a header for a new bump map
MAT_MAP_FILENAME =      long("0xA300",16);      # This holds the file name of the texture

#>------ sub defines of OBJECT
OBJECT_MESH  =      long("0x4100",16);      # This lets us know that we are reading a new object
OBJECT_LAMP =      long("0x4600",16);      # This lets un know we are reading a light object
OBJECT_LAMP_SPOT = long("0x4610",16);		# The light is a spotloght.
OBJECT_LAMP_OFF = long("0x4620",16);		# The light off.
OBJECT_LAMP_ATTENUATE = long("0x4625",16);	
OBJECT_LAMP_RAYSHADE = long("0x4627",16);	
OBJECT_LAMP_SHADOWED = long("0x4630",16);	
OBJECT_LAMP_LOCAL_SHADOW = long("0x4640",16);	
OBJECT_LAMP_LOCAL_SHADOW2 = long("0x4641",16);	
OBJECT_LAMP_SEE_CONE = long("0x4650",16);	
OBJECT_LAMP_SPOT_RECTANGULAR= long("0x4651",16);
OBJECT_LAMP_SPOT_OVERSHOOT= long("0x4652",16);
OBJECT_LAMP_SPOT_PROJECTOR= long("0x4653",16);
OBJECT_LAMP_EXCLUDE= long("0x4654",16);
OBJECT_LAMP_RANGE= long("0x4655",16);
OBJECT_LAMP_ROLL= long("0x4656",16);
OBJECT_LAMP_SPOT_ASPECT= long("0x4657",16);
OBJECT_LAMP_RAY_BIAS= long("0x4658",16);
OBJECT_LAMP_INNER_RANGE= long("0x4659",16);
OBJECT_LAMP_OUTER_RANGE= long("0x465A",16);
OBJECT_LAMP_MULTIPLIER = long("0x465B",16);
OBJECT_LAMP_AMBIENT_LIGHT = long("0x4680",16);



OBJECT_CAMERA=      long("0x4700",16);      # This lets un know we are reading a camera object

#>------ sub defines of CAMERA
OBJECT_CAM_RANGES=   long("0x4720",16);      # The camera range values

#>------ sub defines of OBJECT_MESH
OBJECT_VERTICES =   long("0x4110",16);      # The objects vertices
OBJECT_FACES    =   long("0x4120",16);      # The objects faces
OBJECT_MATERIAL =   long("0x4130",16);      # This is found if the object has a material, either texture map or color
OBJECT_UV       =   long("0x4140",16);      # The UV texture coordinates
OBJECT_TRANS_MATRIX  =   long("0x4160",16); # The Object Matrix

global scn
scn = None

#the chunk class
class chunk:
	ID=0
	length=0
	bytes_read=0

	#we don't read in the bytes_read, we compute that
	binary_format="<HI"

	def __init__(self):
		self.ID=0
		self.length=0
		self.bytes_read=0

	def dump(self):
		print "ID: ", self.ID
		print "ID in hex: ", hex(self.ID)
		print "length: ", self.length
		print "bytes_read: ", self.bytes_read
		

def read_chunk(file, chunk):
		temp_data=file.read(struct.calcsize(chunk.binary_format))
		data=struct.unpack(chunk.binary_format, temp_data)
		chunk.ID=data[0]
		chunk.length=data[1]
		#update the bytes read function
		chunk.bytes_read=6

		#if debugging
		#chunk.dump()

def read_string(file):
	s=""
	index=0
	#print "reading a string"
	#read in the characters till we get a null character
	temp_data=file.read(1)
	data=struct.unpack("c", temp_data)
	s=s+(data[0])
	#print "string: ",s
	while(ord(s[index])!=0):
		index+=1
		temp_data=file.read(1)
		data=struct.unpack("c", temp_data)
		s=s+(data[0])
		#print "string: ",s
	
	#remove the null character from the string
	the_string=s[:-1]
	return the_string

######################################################
# IMPORT
######################################################
def process_next_object_chunk(file, previous_chunk):
	new_chunk=chunk()
	temp_chunk=chunk()

	while (previous_chunk.bytes_read<previous_chunk.length):
		#read the next chunk
		read_chunk(file, new_chunk)

def skip_to_end(file, skip_chunk):
	buffer_size=skip_chunk.length-skip_chunk.bytes_read
	binary_format=str(buffer_size)+"c"
	temp_data=file.read(struct.calcsize(binary_format))
	skip_chunk.bytes_read+=buffer_size


def add_texture_to_material(image, texture, material, mapto):
	if mapto=="DIFFUSE":
		map=Texture.MapTo.COL
	elif mapto=="SPECULAR":
		map=Texture.MapTo.SPEC
	elif mapto=="OPACITY":
		map=Texture.MapTo.ALPHA
	elif mapto=="BUMP":
		map=Texture.MapTo.NOR
	else:
		print "/tError:  Cannot map to ", mapto
		return
	

	texture.setImage(image)
	texture_list=material.getTextures()
	index=0
	for tex in texture_list:
		if tex==None:
			material.setTexture(index,texture,Texture.TexCo.UV,map)
			return
		else:
			index+=1
		if index>10:
			print "/tError: Cannot add diffuse map.  Too many textures"

def process_next_chunk(file, filename, previous_chunk):
	scn = Scene.GetCurrent()
	contextObName = None
	contextLamp = [None, None] # object, Data
	contextMaterial = None
	contextMatrix = Blender.Mathutils.Matrix(); contextMatrix.identity()
	contextMesh = None
	
	TEXTURE_DICT={}
	MATDICT={}
	TEXMODE = Mesh.FaceModes['TEX']
	objectList = [] # Keep a list of imported objects.
	
	# Localspace variable names, faster.
	STRUCT_SIZE_1CHAR = struct.calcsize("c")
	STRUCT_SIZE_2FLOAT = struct.calcsize("2f")
	STRUCT_SIZE_3FLOAT = struct.calcsize("3f")
	STRUCT_SIZE_UNSIGNED_SHORT = struct.calcsize("H")
	STRUCT_SIZE_4UNSIGNED_SHORT = struct.calcsize("4H")
	STRUCT_SIZE_4x3MAT = struct.calcsize("ffffffffffff")
	
	
	def putContextMesh(myContextMesh):
		INV_MAT = Blender.Mathutils.Matrix(contextMatrix)
		
		INV_MAT.invert()
		contextMesh.transform(INV_MAT)
		
		# Faces without an image can have the image flag disabled.
		if myContextMesh.faceUV:
			TEX_ON_FLAG = Mesh.FaceModes['TEX']
			for f in myContextMesh.faces:
				if not f.image:
					f.mode &= ~TEX_ON_FLAG # disable tex flag.
				for c in f.col:
					c.b=c.g=c.r=255
				
				
		newOb = Object.New('Mesh', contextMesh.name) # Meshes name is always a free object name too.
		newOb.link(contextMesh)
		scn.link(newOb)
		newOb.Layers = scn.Layers
		newOb.sel = 1
		objectList.append(newOb) # last 2 recal normals
		newOb.setMatrix(contextMatrix)
		
		Blender.Window.EditMode(1)
		Blender.Window.EditMode(0)
	
	
	#a spare chunk
	new_chunk=chunk()
	temp_chunk=chunk()

	#loop through all the data for this chunk (previous chunk) and see what it is
	while (previous_chunk.bytes_read<previous_chunk.length):
		#read the next chunk
		#print "reading a chunk"
		read_chunk(file, new_chunk)

		#is it a Version chunk?
		if (new_chunk.ID==VERSION):
			#print "found a VERSION chunk"
			#read in the version of the file
			#it's an unsigned short (H)
			temp_data=file.read(struct.calcsize("I"))
			data=struct.unpack("I", temp_data)
			version=data[0]
			new_chunk.bytes_read+=4 #read the 4 bytes for the version number
			#this loader works with version 3 and below, but may not with 4 and above
			if (version>3):
				print "\tNon-Fatal Error:  Version greater than 3, may not load correctly: ", version

		#is it an object info chunk?
		elif (new_chunk.ID==OBJECTINFO):
			# print "found an OBJECTINFO chunk"
			process_next_chunk(file, filename, new_chunk)
			
			#keep track of how much we read in the main chunk
			new_chunk.bytes_read+=temp_chunk.bytes_read

		#is it an object chunk?
		elif (new_chunk.ID==OBJECT):
			tempName = read_string(file)
			contextObName = getUniqueName( tempName )
			new_chunk.bytes_read += (len(tempName)+1)
		
		#is it a material chunk?
		elif (new_chunk.ID==MATERIAL):
			# print "found a MATERIAL chunk"
			contextMaterial = Material.New()
		
		elif (new_chunk.ID==MAT_NAME):
			# print "Found a MATNAME chunk"
			material_name=""
			material_name=read_string(file)
			
			#plus one for the null character that ended the string
			new_chunk.bytes_read+=(len(material_name)+1)
			
			contextMaterial.setName(material_name)
			MATDICT[material_name] = contextMaterial.name
		
		elif (new_chunk.ID==MAT_AMBIENT):
			# print "Found a MATAMBIENT chunk"

			read_chunk(file, temp_chunk)
			temp_data=file.read(struct.calcsize("3B"))
			data=struct.unpack("3B", temp_data)
			temp_chunk.bytes_read+=3
			contextMaterial.mirCol = [float(col)/255 for col in data] # data [0,1,2] == rgb
			new_chunk.bytes_read+=temp_chunk.bytes_read

		elif (new_chunk.ID==MAT_DIFFUSE):
			# print "Found a MATDIFFUSE chunk"

			read_chunk(file, temp_chunk)
			temp_data=file.read(struct.calcsize("3B"))
			data=struct.unpack("3B", temp_data)
			temp_chunk.bytes_read+=3
			contextMaterial.rgbCol = [float(col)/255 for col in data] # data [0,1,2] == rgb
			new_chunk.bytes_read+=temp_chunk.bytes_read

		elif (new_chunk.ID==MAT_SPECULAR):
			# print "Found a MATSPECULAR chunk"

			read_chunk(file, temp_chunk)
			temp_data=file.read(struct.calcsize("3B"))
			data=struct.unpack("3B", temp_data)
			temp_chunk.bytes_read+=3
			
			contextMaterial.specCol = [float(col)/255 for col in data] # data [0,1,2] == rgb
			new_chunk.bytes_read+=temp_chunk.bytes_read

		elif (new_chunk.ID==MAT_TEXTURE_MAP):
			#print 'DIFFUSE MAP'
			new_texture=Blender.Texture.New('Diffuse')
			new_texture.setType('Image')
			while (new_chunk.bytes_read<new_chunk.length):
				read_chunk(file, temp_chunk)
				
				if (temp_chunk.ID==MAT_MAP_FILENAME):
					texture_name=""
					texture_name=str(read_string(file))
					img = TEXTURE_DICT[contextMaterial.name] = BPyImage.comprehensiveImageLoad(texture_name, FILENAME)
					new_chunk.bytes_read += (len(texture_name)+1) #plus one for the null character that gets removed
					
				else:
					skip_to_end(file, temp_chunk)
				
				new_chunk.bytes_read+=temp_chunk.bytes_read
			
			#add the map to the material in the right channel
			add_texture_to_material(img, new_texture, contextMaterial, "DIFFUSE")
			
		elif (new_chunk.ID==MAT_SPECULAR_MAP):
			new_texture=Blender.Texture.New('Specular')
			new_texture.setType('Image')
			while (new_chunk.bytes_read<new_chunk.length):
				read_chunk(file, temp_chunk)
				
				if (temp_chunk.ID==MAT_MAP_FILENAME):
					texture_name=""
					texture_name=str(read_string(file))
					img = BPyImage.comprehensiveImageLoad(texture_name, FILENAME)
					new_chunk.bytes_read += (len(texture_name)+1) #plus one for the null character that gets removed
				else:
					skip_to_end(file, temp_chunk)
				
				new_chunk.bytes_read+=temp_chunk.bytes_read
				
			#add the map to the material in the right channel
			add_texture_to_material(img, new_texture, contextMaterial, "SPECULAR")
	
		elif (new_chunk.ID==MAT_OPACITY_MAP):
			new_texture=Blender.Texture.New('Opacity')
			new_texture.setType('Image')
			while (new_chunk.bytes_read<new_chunk.length):
				read_chunk(file, temp_chunk)
				
				if (temp_chunk.ID==MAT_MAP_FILENAME):
					texture_name=""
					texture_name=str(read_string(file))
					img = BPyImage.comprehensiveImageLoad(texture_name, FILENAME)
					new_chunk.bytes_read += (len(texture_name)+1) #plus one for the null character that gets removed
				else:
					skip_to_end(file, temp_chunk)
				
				new_chunk.bytes_read+=temp_chunk.bytes_read

			#add the map to the material in the right channel
			add_texture_to_material(img, new_texture, contextMaterial, "OPACITY")

		elif (new_chunk.ID==MAT_BUMP_MAP):
			new_texture=Blender.Texture.New('Bump')
			new_texture.setType('Image')
			while (new_chunk.bytes_read<new_chunk.length):
				read_chunk(file, temp_chunk)
				
				if (temp_chunk.ID==MAT_MAP_FILENAME):
					texture_name=""
					texture_name=str(read_string(file))
					img = BPyImage.comprehensiveImageLoad(texture_name, FILENAME)
					new_chunk.bytes_read += (len(texture_name)+1) #plus one for the null character that gets removed
				else:
					skip_to_end(file, temp_chunk)
				
				new_chunk.bytes_read+=temp_chunk.bytes_read
				
			#add the map to the material in the right channel
			add_texture_to_material(img, new_texture, contextMaterial, "BUMP")
			
		elif (new_chunk.ID==MAT_TRANSPARENCY):
			read_chunk(file, temp_chunk)
			temp_data=file.read(STRUCT_SIZE_UNSIGNED_SHORT)
			data=struct.unpack("H", temp_data)
			temp_chunk.bytes_read+=2
			contextMaterial.setAlpha(1-(float(data[0])/100))
			new_chunk.bytes_read+=temp_chunk.bytes_read


		elif (new_chunk.ID==OBJECT_LAMP): # Basic lamp support.
			# print "Found an OBJECT_MESH chunk"
			#if contextLamp != None: # Write context mesh if we have one.
			#	putContextLamp(contextLamp)
			
			#print 'LAMP!!!!!!!!!'
			temp_data=file.read(STRUCT_SIZE_3FLOAT)
			
			data=struct.unpack("3f", temp_data)
			new_chunk.bytes_read+=STRUCT_SIZE_3FLOAT
			x,y,z =tuple(data)
			
			
			contextLamp[0] = Object.New('Lamp')
			contextLamp[1] = Lamp.New()
			contextLamp[0].link(contextLamp[1])
			scn.link(contextLamp[0])
			
			
			
			#print "number of faces: ", num_faces
			#print x,y,z
			contextLamp[0].setLocation(x,y,z)
			
			# Reset matrix
			contextMatrix = Mathutils.Matrix(); contextMatrix.identity()	
			#print contextLamp.name, '"""""""'
			
			
		elif (new_chunk.ID==OBJECT_MESH):
			# print "Found an OBJECT_MESH chunk"
			if contextMesh != None: # Write context mesh if we have one.
				putContextMesh(contextMesh)
			
			contextMesh = Mesh.New()
			contextMeshUV = None
			#contextMesh.vertexUV= 1 # Make sticky coords.
			# Reset matrix
			contextMatrix = Blender.Mathutils.Matrix(); contextMatrix.identity()
		
		elif (new_chunk.ID==OBJECT_VERTICES):
			# print "Found an OBJECT_VERTICES chunk"
			#print "object_verts: length: ", new_chunk.length
			temp_data=file.read(STRUCT_SIZE_UNSIGNED_SHORT)
			data=struct.unpack("H", temp_data)
			new_chunk.bytes_read+=2
			num_verts=data[0]
			# print "number of verts: ", num_verts
			def getvert():
				temp_data=file.read(STRUCT_SIZE_3FLOAT)
				new_chunk.bytes_read += STRUCT_SIZE_3FLOAT #12: 3 floats x 4 bytes each
				data=struct.unpack("3f", temp_data)
				return Vector(data[0],data[1],data[2])
			
			contextMesh.verts.extend( [getvert() for i in xrange(num_verts)] )
			#print "object verts: bytes read: ", new_chunk.bytes_read

		elif (new_chunk.ID==OBJECT_FACES):
			# print "Found an OBJECT_FACES chunk"
			#print "object faces: length: ", new_chunk.length
			temp_data=file.read(STRUCT_SIZE_UNSIGNED_SHORT)
			data=struct.unpack("H", temp_data)
			new_chunk.bytes_read+=2
			num_faces=data[0]
			#print "number of faces: ", num_faces
			
			"""
			
			for counter in xrange(num_faces):
				temp_data=file.read(STRUCT_SIZE_4UNSIGNED_SHORT)
				new_chunk.bytes_read += STRUCT_SIZE_4UNSIGNED_SHORT #4 short ints x 2 bytes each
				data=struct.unpack("4H", temp_data)
				
				#insert the mesh info into the faces, don't worry about data[3] it is a 3D studio thing
				contextMesh.faces.extend([contextMesh.verts[data[i]] for i in xrange(3) ])
				f = contextMesh.faces[-1]
				if contextMeshUV:
					contextMesh.faceUV= 1 # Make sticky coords.
					f.uv = [ contextMeshUV[data[i]] for i in xrange(3) ]
			
			"""
			
			def getface():
				temp_data=file.read(STRUCT_SIZE_4UNSIGNED_SHORT)
				new_chunk.bytes_read += STRUCT_SIZE_4UNSIGNED_SHORT #4 short ints x 2 bytes each
				data=struct.unpack("4H", temp_data)
				verts = [contextMesh.verts[data[i]] for i in xrange(3) ]
				
				if verts[0]==verts[1] or verts[0]==verts[2] or verts[1]==verts[2]:
					return None
				else:
					return verts
			
			contextFaceMapping = {} # So error faces dont unsync the this.
			#contextMesh.faces.extend( [getface() for i in xrange(num_faces)] )
			for i in xrange(num_faces):
				ok=0
				face= getface()
				if face:
					lenback = len(contextMesh.faces)
					contextMesh.faces.extend( face )
					if len(contextMesh.faces) != lenback:
						ok=1
						contextFaceMapping[i] = len(contextMesh.faces)-1
				if not ok:
					contextFaceMapping[i] = None
					
			
			#print 'LENFACEWS', len(contextMesh.faces), num_faces
			if contextMeshUV:
				contextMesh.faceUV= 1
				for f in contextMesh.faces:
					f.uv = [contextMeshUV[v.index] for v in f.v ]
			
			#print "object faces: bytes read: ", new_chunk.bytes_read

		elif (new_chunk.ID==OBJECT_MATERIAL):
			# print "Found an OBJECT_MATERIAL chunk"
			material_name=""
			material_name = read_string(file)
			new_chunk.bytes_read += len(material_name)+1 # remove 1 null character.

			#look up the material in all the materials
			material_found=0
			for mat in Material.Get():
				
				#found it, add it to the mesh
				if(mat.name==material_name):
					if len(contextMesh.materials) >= 15:
						print "\tCant assign more than 16 materials per mesh, keep going..."
						break
					else:
						meshHasMat = 0
						for myMat in contextMesh.materials:
							if myMat.name == mat.name:
								meshHasMat = 1
						
						if meshHasMat == 0:
							contextMesh.materials =  contextMesh.materials + [mat]
							material_found=1
							
							#figure out what material index this is for the mesh
							for mat_counter in xrange(len(contextMesh.materials)):
								if contextMesh.materials[mat_counter].name == material_name:
									mat_index=mat_counter
									#print "material index: ",mat_index
							
						
						break # get out of this for loop so we don't accidentally set material_found back to 0
				else:
					material_found=0
					# print "Not matching: ", mat.name, " and ", material_name
			#print contextMesh.materials
			if material_found == 1:
				contextMaterial = mat
				#read the number of faces using this material
				temp_data=file.read(STRUCT_SIZE_UNSIGNED_SHORT)
				data=struct.unpack("H", temp_data)
				new_chunk.bytes_read += STRUCT_SIZE_UNSIGNED_SHORT
				num_faces_using_mat=data[0]
				
				#list of faces using mat
				for face_counter in xrange(num_faces_using_mat):
					temp_data=file.read(STRUCT_SIZE_UNSIGNED_SHORT)
					new_chunk.bytes_read += STRUCT_SIZE_UNSIGNED_SHORT
					data=struct.unpack("H", temp_data)
					facemap = contextFaceMapping[data[0]]
					if facemap != None: # Face map can be None when teh face has bad data.
						face = contextMesh.faces[facemap]
						face.mat = mat_index
						
						
						mname = MATDICT[contextMaterial.name]
						
						try:
							img = TEXTURE_DICT[mname]
						except:
							img = None
						
						if img:
							contextMesh.faceUV = 1
							#print 'Assigning image', img.name
							face.mode |= TEXMODE
							face.image = img
						
			else:
				#read past the information about the material you couldn't find
				#print "Couldn't find material.  Reading past face material info"
				buffer_size=new_chunk.length-new_chunk.bytes_read
				binary_format=str(buffer_size)+"c"
				temp_data=file.read(struct.calcsize(binary_format))
				new_chunk.bytes_read+=buffer_size
			
			#print "object mat: bytes read: ", new_chunk.bytes_read

		elif (new_chunk.ID == OBJECT_UV):
			# print "Found an OBJECT_UV chunk"
			temp_data=file.read(STRUCT_SIZE_UNSIGNED_SHORT)
			data=struct.unpack("H", temp_data)
			new_chunk.bytes_read+=2
			num_uv=data[0]
			def getuv():
				temp_data=file.read(STRUCT_SIZE_2FLOAT)
				new_chunk.bytes_read += STRUCT_SIZE_2FLOAT #2 float x 4 bytes each
				data=struct.unpack("2f", temp_data)
				return Vector(data[0], data[1])
				
			contextMeshUV = [ getuv() for i in xrange(num_uv) ]
			'''
			for counter in xrange(num_uv):
				temp_data=file.read(STRUCT_SIZE_2FLOAT)
				new_chunk.bytes_read += STRUCT_SIZE_2FLOAT #2 float x 4 bytes each
				data=struct.unpack("2f", temp_data)
				
				#insert the insert the UV coords in the vertex data
				contextMeshUV[counter].uvco = data
			'''
		
		elif (new_chunk.ID == OBJECT_TRANS_MATRIX):
			# print "Found an OBJECT_TRANS_MATRIX chunk"
			
			temp_data=file.read(STRUCT_SIZE_4x3MAT)
			data = list( struct.unpack("ffffffffffff", temp_data) )
			new_chunk.bytes_read += STRUCT_SIZE_4x3MAT 
			
			contextMatrix = Blender.Mathutils.Matrix(\
			 data[:3] + [0],\
			 data[3:6] + [0],\
			 data[6:9] + [0],\
			 data[9:] + [1])
		
		
		
		else: #(new_chunk.ID!=VERSION or new_chunk.ID!=OBJECTINFO or new_chunk.ID!=OBJECT or new_chunk.ID!=MATERIAL):
			# print "skipping to end of this chunk"
			buffer_size=new_chunk.length-new_chunk.bytes_read
			binary_format=str(buffer_size)+"c"
			temp_data=file.read(struct.calcsize(binary_format))
			new_chunk.bytes_read+=buffer_size


		#update the previous chunk bytes read
		previous_chunk.bytes_read += new_chunk.bytes_read
		#print "Bytes left in this chunk: ", previous_chunk.length-previous_chunk.bytes_read
	
	# FINISHED LOOP
	# There will be a number of objects still not added
	if contextMesh != None:
		putContextMesh(contextMesh)
	
	for ob in objectList:
		ob.sel = 1

def load_3ds(filename):
	print '\n\nImporting "%s"' % filename
	
	# 
	for ob in Scene.GetCurrent().getChildren():
		ob.sel = 0
	time1 = Blender.sys.time()
	
	global FILENAME
	FILENAME=filename
	current_chunk=chunk()
	
	file=open(filename,"rb")
	
	#here we go!
	# print "reading the first chunk"
	read_chunk(file, current_chunk)
	if (current_chunk.ID!=PRIMARY):
		print "\tFatal Error:  Not a valid 3ds file: ", filename
		file.close()
		return

	process_next_chunk(file, filename, current_chunk)
	
	# Select all new objects.
	print 'finished importing: "%s" in %.4f sec.' % (filename, (Blender.sys.time()-time1))
	file.close()



if __name__  == '__main__':
	Blender.Window.FileSelector(load_3ds, "Import 3DS", '*.3ds')

# For testing compatibility

"""
TIME = Blender.sys.time()
import os
os.system('find /metavr/ -iname "*.3ds" > /tmp/temp3ds_list')
file = open('/tmp/temp3ds_list', 'r')
lines = file.readlines()[200:]
file.close()		
for i, _3ds in enumerate(lines):
	_3ds= _3ds[:-1]
	print "Importing", _3ds, i
	_3ds_file = _3ds.split('/')[-1].split('\\')[-1]
	newScn = Scene.New(_3ds_file)
	newScn.makeCurrent()
	my_callback(_3ds)

print "TOTAL TIME: %.6f" % (Blender.sys.time() - TIME)
"""