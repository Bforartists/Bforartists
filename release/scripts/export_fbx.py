#!BPY
"""
Name: 'Autodesk FBX (.fbx)...'
Blender: 244
Group: 'Export'
Tooltip: 'Selection to an ASCII Autodesk FBX '
"""
__author__ = "Campbell Barton"
__url__ = ['www.blender.org', 'blenderartists.org']
__version__ = "1.1"

__bpydoc__ = """\
This script is an exporter to the FBX file format.

Usage:

Select the objects you wish to export and run this script from "File->Export" menu.
All objects that can be represented as a mesh (mesh, curve, metaball, surface, text3d)
will be exported as mesh data.
"""
# --------------------------------------------------------------------------
# FBX Export v0.1 by Campbell Barton (AKA Ideasman)
# --------------------------------------------------------------------------
# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****
# --------------------------------------------------------------------------

try:
	import time
	# import os # only needed for batch export, nbot used yet
except:
	time = None # use this to check if they have python modules installed

# for python 2.3 support
try:
	set()
except:
	try:
		from sets import Set as set
	except:
		set = None # so it complains you dont have a !

# os is only needed for batch 'own dir' option
try:
	import os
except:
	os = None

import Blender
import bpy
from Blender.Mathutils import Matrix, Vector, RotationMatrix

import BPyObject
import BPyMesh
import BPySys
import BPyMessages

import sys

## This was used to make V, but faster not to do all that
##valid = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_,.()[]{}'
##v = range(255)
##for c in valid: v.remove(ord(c))
v = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,42,43,47,58,59,60,61,62,63,64,92,94,96,124,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192,193,194,195,196,197,198,199,200,201,202,203,204,205,206,207,208,209,210,211,212,213,214,215,216,217,218,219,220,221,222,223,224,225,226,227,228,229,230,231,232,233,234,235,236,237,238,239,240,241,242,243,244,245,246,247,248,249,250,251,252,253,254]
invalid = ''.join([chr(i) for i in v])
def cleanName(name):
	for ch in invalid:	name = name.replace(ch, '_')
	return name
del v, i


def copy_file(source, dest):
	file = open(source, 'rb')
	data = file.read()
	file.close()
	
	file = open(dest, 'wb')
	file.write(data)
	file.close()


def copy_images(dest_dir, textures):
	if not dest_dir.endswith(Blender.sys.sep):
		dest_dir += Blender.sys.sep
	
	image_paths = set()
	for img in textures:
		image_paths.add(Blender.sys.expandpath(img.filename))
	
	# Now copy images
	copyCount = 0
	for image_path in image_paths:
		if Blender.sys.exists(image_path):
			# Make a name for the target path.
			dest_image_path = dest_dir + image_path.split('\\')[-1].split('/')[-1]
			if not Blender.sys.exists(dest_image_path): # Image isnt alredy there
				print '\tCopying "%s" > "%s"' % (image_path, dest_image_path)
				try:
					copy_file(image_path, dest_image_path)
					copyCount+=1
				except:
					print '\t\tWarning, file failed to copy, skipping.'
	
	print '\tCopied %d images' % copyCount

mtx4_identity = Matrix()

mtx_z90 = RotationMatrix(90, 3, 'z')
mtx_x90 = RotationMatrix(90, 3, 'x')

# testing
mtx_x90		= RotationMatrix( 90, 3, 'x')
mtx_x90n	= RotationMatrix(-90, 3, 'x')
mtx_y90		= RotationMatrix( 90, 3, 'y')
mtx_y90n	= RotationMatrix(-90, 3, 'y')
mtx_z90		= RotationMatrix( 90, 3, 'z')
mtx_z90n	= RotationMatrix(-90, 3, 'z')


mtx4_x90	= RotationMatrix( 90, 4, 'x')
mtx4_x90n	= RotationMatrix(-90, 4, 'x')
mtx4_y90	= RotationMatrix( 90, 4, 'y')
mtx4_y90n	= RotationMatrix(-90, 4, 'y')
mtx4_z90	= RotationMatrix( 90, 4, 'z')
mtx4_z90n	= RotationMatrix(-90, 4, 'z')

XVEC  = Vector(1,  0, 0)
XVECN = Vector(-1, 0, 0)
YVEC  = Vector(0,  1, 0)
YVECN = Vector(0, -1, 0)
ZVEC  = Vector(0, 0,  1)
ZVECN = Vector(0, 0, -1)


def strip_path(p):
	return p.split('\\')[-1].split('/')[-1]

# Used to add the scene name into the filename without using odd chars	
sane_name_mapping_ob = {}
sane_name_mapping_mat = {}
sane_name_mapping_tex = {}
sane_name_mapping_take = {}
sane_name_mapping_group = {}

# Make sure reserved names are not used
sane_name_mapping_ob['Scene'] = 'Scene_'
sane_name_mapping_ob['blend_root'] = 'blend_root_'

def increment_string(t):
	name = t
	num = ''
	while name and name[-1].isdigit():
		num = name[-1] + num
		name = name[:-1]
	if num:	return '%s%d' % (name, int(num)+1)	
	else:	return name + '_0'



# todo - Disallow the name 'Scene' and 'blend_root' - it will bugger things up.
def sane_name(data, dct):
	#if not data: return None
	name = data.name
	
	# dont cache, only ever call once for each data type now,
	# so as to avoid namespace collision between types - like with objects <-> bones
	#try:		return dct[name]
	#except:		pass
	
	orig_name = name
	if not name:
		name = 'unnamed' # blank string, ASKING FOR TROUBLE!
	else:
		#name = BPySys.cleanName(name)
		name = cleanName(name) # use our own
	
	while name in dct.itervalues():	name = increment_string(name)
	
	dct[orig_name] = name
	return name

def sane_obname(data):		return sane_name(data, sane_name_mapping_ob)
def sane_matname(data):		return sane_name(data, sane_name_mapping_mat)
def sane_texname(data):		return sane_name(data, sane_name_mapping_tex)
def sane_takename(data):	return sane_name(data, sane_name_mapping_take)
def sane_groupname(data):	return sane_name(data, sane_name_mapping_group)




def mat4x4str(mat):
	return '%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f,%.15f' % tuple([ f for v in mat for f in v ])

def meshNormalizedWeights(me):
	try: # account for old bad BPyMesh
		groupNames, vWeightList = BPyMesh.meshWeight2List(me)
	except:
		return [],[]
	
	if not groupNames:
		return [],[]
	
	for i, vWeights in enumerate(vWeightList):
		tot = 0.0
		for w in vWeights:
			tot+=w
		
		if tot:
			for j, w in enumerate(vWeights):
				vWeights[j] = w/tot
	
	return groupNames, vWeightList

header_comment = \
'''; FBX 6.1.0 project file
; Created by Blender FBX Exporter
; for support mail: ideasman42@gmail.com
; ----------------------------------------------------

'''

# This func can be called with just the filename
def write(filename, batch_objects = None, \
		EXP_OBS_SELECTED =			True,
		EXP_MESH =					True,
		EXP_MESH_APPLY_MOD =		True,
		EXP_MESH_HQ_NORMALS =		False,
		EXP_ARMATURE =				True,
		EXP_LAMP =					True,
		EXP_CAMERA =				True,
		EXP_EMPTY =					True,
		EXP_IMAGE_COPY =			False,
		GLOBAL_MATRIX =				Matrix(),
		ANIM_ENABLE =				True,
		ANIM_OPTIMIZE =				True,
		ANIM_OPTIMIZE_PRECISSION =	6,
		ANIM_ACTION_ALL =			False,
		BATCH_ENABLE =				False,
		BATCH_GROUP =				True,
		BATCH_SCENE =				False,
		BATCH_FILE_PREFIX =			'',
		BATCH_OWN_DIR =				False
	):

	
	
	
	# ----------------- Batch support!
	if BATCH_ENABLE:
		if os == None:	BATCH_OWN_DIR = False
		
		fbxpath = filename
		
		# get the path component of filename
		
		tmp_exists = Blender.sys.exists(fbxpath)
		
		if tmp_exists != 2: # a file, we want a path
			while fbxpath and fbxpath[-1] not in ('/', '\\'):
				fbxpath = fbxpath[:-1]
			if not filename:
				Draw.PupMenu('Error%t|Directory does not exist!')
				return
			
			tmp_exists = Blender.sys.exists(fbxpath)
		
		if tmp_exists != 2:
			Draw.PupMenu('Error%t|Directory does not exist!')
			return
		
		if not fbxpath.endswith(Blender.sys.sep):
			fbxpath += Blender.sys.sep
		del tmp_exists
		
		
		if BATCH_GROUP:
			data_seq = bpy.data.groups
		else:
			data_seq = bpy.data.scenes
		
		# call this function within a loop with BATCH_ENABLE == False
		orig_sce = bpy.data.scenes.active
		
		
		new_fbxpath = fbxpath # own dir option modifies, we need to keep an original
		for data in data_seq: # scene or group
			newname = BATCH_FILE_PREFIX + BPySys.cleanName(data.name)
			
			
			if BATCH_OWN_DIR:
				new_fbxpath = fbxpath + newname + Blender.sys.sep
				# path may alredy exist
				# TODO - might exist but be a file. unlikely but should probably account for it.
				
				if Blender.sys.exists(new_fbxpath) == 0:
					os.mkdir(new_fbxpath)
				
			
			filename = new_fbxpath + newname + '.fbx'
			
			print '\nBatch exporting %s as...\n\t"%s"' % (data, filename)
			
			if BATCH_GROUP: #group
				# group, so objects update properly, add a dummy scene.
				sce = bpy.data.scenes.new()
				sce.Layers = (1<<20) -1
				bpy.data.scenes.active = sce
				for ob_base in data.objects:
					sce.objects.link(ob_base)
				
				sce.update(1)
				
				# TODO - BUMMER! Armatures not in the group wont animate the mesh
				
			else:# scene
				
				
				data_seq.active = data
			
			
			# Call self with modified args
			# Dont pass batch options since we alredy usedt them
			write(filename, data.objects,
				False,
				EXP_MESH,
				EXP_MESH_APPLY_MOD,
				EXP_MESH_HQ_NORMALS,
				EXP_ARMATURE,
				EXP_LAMP,
				EXP_CAMERA,
				EXP_EMPTY,
				EXP_IMAGE_COPY,
				GLOBAL_MATRIX,
				ANIM_ENABLE,
				ANIM_OPTIMIZE,
				ANIM_OPTIMIZE_PRECISSION,
				ANIM_ACTION_ALL
			)
			
			if BATCH_GROUP:
				# remove temp group scene
				bpy.data.scenes.unlink(sce)
		
		bpy.data.scenes.active = orig_sce
		
		return # so the script wont run after we have batch exported.
	
	# end batch support
	
	
	# ----------------------------------------------
	# storage classes
	class my_bone_class:
		__slots__ =(\
		  'blenName',\
		  'blenBone',\
		  'blenMeshes',\
		  'restMatrix',\
		  'parent',\
		  'blenName',\
		  'fbxName',\
		  'fbxArm',\
		  '__pose_bone',\
		  '__anim_poselist')
		
		def __init__(self, blenBone, fbxArm):
			
			# This is so 2 armatures dont have naming conflicts since FBX bones use object namespace
			self.fbxName = sane_obname(blenBone)
			
			self.blenName =			blenBone.name
			self.blenBone =			blenBone
			self.blenMeshes =		{}					# fbxMeshObName : mesh
			self.fbxArm =			fbxArm
			self.restMatrix =		blenBone.matrix['ARMATURESPACE']
			
			# not used yet
			# self.restMatrixInv =	self.restMatrix.copy().invert()
			# self.restMatrixLocal =	None # set later, need parent matrix
			
			self.parent =			None
			
			# not public
			pose = fbxArm.blenObject.getPose()
			self.__pose_bone =		pose.bones[self.blenName]
			
			# store a list if matricies here, (poseMatrix, head, tail)
			# {frame:posematrix, frame:posematrix, ...}
			self.__anim_poselist = {}
		
		'''
		def calcRestMatrixLocal(self):
			if self.parent:
				self.restMatrixLocal = self.restMatrix * self.parent.restMatrix.copy().invert()
			else:
				self.restMatrixLocal = self.restMatrix.copy()
		'''
		def setPoseFrame(self, f):
			# cache pose info here, frame must be set beforehand
			
			# Didnt end up needing head or tail, if we do - here it is.
			'''
			self.__anim_poselist[f] = (\
				self.__pose_bone.poseMatrix.copy(),\
				self.__pose_bone.head.copy(),\
				self.__pose_bone.tail.copy() )
			'''
			
			self.__anim_poselist[f] = self.__pose_bone.poseMatrix.copy()
		
		# get pose from frame.
		def getPoseMatrix(self, f):# ----------------------------------------------
			return self.__anim_poselist[f]
		'''
		def getPoseHead(self, f):
			#return self.__pose_bone.head.copy()
			return self.__anim_poselist[f][1].copy()
		def getPoseTail(self, f):
			#return self.__pose_bone.tail.copy()
			return self.__anim_poselist[f][2].copy()
		'''
		# end
		
		def getAnimMatrix(self, frame):
			arm_mat = self.fbxArm.matrixWorld
			if not self.parent:
				return mtx4_z90 * (self.getPoseMatrix(frame) * arm_mat)
			else:
				return (mtx4_z90 * ((self.getPoseMatrix(frame) * arm_mat)))  *  (mtx4_z90 * (self.parent.getPoseMatrix(frame) * arm_mat)).invert()
		
		# we need thes because cameras and lights modified rotations
		def getAnimMatrixRot(self, frame):
			return self.getAnimMatrix(frame)
		
		def flushAnimData(self):
			self.__anim_poselist.clear()


	class my_object_generic:
		# Other settings can be applied for each type - mesh, armature etc.
		def __init__(self, ob, matrixWorld = None):
			self.fbxName = sane_obname(ob)
			self.blenObject = ob
			self.fbxGroupNames = []
			if matrixWorld:		self.matrixWorld = matrixWorld * GLOBAL_MATRIX
			else:				self.matrixWorld = ob.matrixWorld * GLOBAL_MATRIX
			self.__anim_poselist = {}
		
		def setPoseFrame(self, f):
			self.__anim_poselist[f] =  self.blenObject.matrixWorld.copy()
		
		def getAnimMatrix(self, frame):
			return self.__anim_poselist[frame] * GLOBAL_MATRIX
		
		def getAnimMatrixRot(self, frame):
			type = self.blenObject.type
			matrix_rot = (self.__anim_poselist[frame] * GLOBAL_MATRIX).rotationPart()
			
			# Lamps need to be rotated
			if type =='Lamp':
				matrix_rot = mtx_x90 * matrix_rot
			elif ob and type =='Camera':
				y = Vector(0,1,0) * matrix_rot
				matrix_rot = matrix_rot * RotationMatrix(90, 3, 'r', y)
			
			return matrix_rot
			
	# ----------------------------------------------
	
	
	
	
	
	print '\nFBX export starting...', filename
	start_time = Blender.sys.time()
	file = open(filename, 'w')
	sce = bpy.data.scenes.active
	world = sce.world
	
	
	# ---------------------------- Write the header first
	file.write(header_comment)
	if time:
		curtime = time.localtime()[0:6]
	else:
		curtime = [0,0,0,0,0,0]
	# 
	file.write(\
'''FBXHeaderExtension:  {
	FBXHeaderVersion: 1003
	FBXVersion: 6100
	CreationTimeStamp:  {
		Version: 1000
		Year: %.4i
		Month: %.2i
		Day: %.2i
		Hour: %.2i
		Minute: %.2i
		Second: %.2i
		Millisecond: 0
	}
	Creator: "FBX SDK/FBX Plugins build 20070228"
	OtherFlags:  {
		FlagPLE: 0
	}
}''' % (curtime))
	
	file.write('\nCreationTime: "%.4i-%.2i-%.2i %.2i:%.2i:%.2i:000"' % curtime)
	file.write('\nCreator: "Blender3D version %.2f"' % Blender.Get('version'))
	
	pose_items = [] # list of (fbxName, matrix) to write pose data for, easier to collect allong the way
	
	# --------------- funcs for exporting
	def object_tx(ob, loc, matrix, matrix_mod = None):
		'''
		Matrix mod is so armature objects can modify their bone matricies
		'''
		if isinstance(ob, Blender.Types.BoneType):
			
			# we know we have a matrix
			matrix = mtx4_z90 * (ob.matrix['ARMATURESPACE'] * matrix_mod)
			
			parent = ob.parent
			if parent:
				par_matrix = mtx4_z90 * (parent.matrix['ARMATURESPACE'] * matrix_mod)
				matrix = matrix * par_matrix.copy().invert()
				
			matrix_rot =	matrix.rotationPart()
			
			loc =			tuple(matrix.translationPart())
			scale =			tuple(matrix.scalePart())
			rot =			tuple(matrix_rot.toEuler())
			
		else:
			if ob and not matrix:	matrix = ob.matrixWorld * GLOBAL_MATRIX
			matrix_rot = matrix
			#if matrix:
			#	matrix = matrix_scale * matrix
			
			if matrix:
				loc = tuple(matrix.translationPart())
				scale = tuple(matrix.scalePart())
				
				matrix_rot = matrix.rotationPart()
				# Lamps need to be rotated
				if ob and ob.type =='Lamp':
					matrix_rot = mtx_x90 * matrix_rot
					rot = tuple(matrix_rot.toEuler())
				elif ob and ob.type =='Camera':
					y = Vector(0,1,0) * matrix_rot
					matrix_rot = matrix_rot * RotationMatrix(90, 3, 'r', y)
					rot = tuple(matrix_rot.toEuler())
				else:
					rot = tuple(matrix_rot.toEuler())
			else:
				if not loc:
					loc = 0,0,0
				scale = 1,1,1
				rot = 0,0,0
		
		return loc, rot, scale, matrix, matrix_rot
	
	def write_object_tx(ob, loc, matrix, matrix_mod= None):
		'''
		We have loc to set the location if non blender objects that have a location
		
		matrix_mod is only used for bones at the moment
		'''
		loc, rot, scale, matrix, matrix_rot = object_tx(ob, loc, matrix, matrix_mod)
		
		file.write('\n\t\t\tProperty: "Lcl Translation", "Lcl Translation", "A+",%.15f,%.15f,%.15f' % loc)
		file.write('\n\t\t\tProperty: "Lcl Rotation", "Lcl Rotation", "A+",%.15f,%.15f,%.15f' % rot)
		file.write('\n\t\t\tProperty: "Lcl Scaling", "Lcl Scaling", "A+",%.15f,%.15f,%.15f' % scale)
		return loc, rot, scale, matrix, matrix_rot
	
	def write_object_props(ob=None, loc=None, matrix=None, matrix_mod=None):
		# if the type is 0 its an empty otherwise its a mesh
		# only difference at the moment is one has a color
		file.write('''
		Properties60:  {
			Property: "QuaternionInterpolate", "bool", "",0
			Property: "Visibility", "Visibility", "A+",1''')
		
		loc, rot, scale, matrix, matrix_rot = write_object_tx(ob, loc, matrix, matrix_mod)
		
		# Rotation order, note, for FBX files Iv loaded normal order is 1
		# setting to zero.
		# eEULER_XYZ = 0
		# eEULER_XZY
		# eEULER_YZX
		# eEULER_YXZ
		# eEULER_ZXY
		# eEULER_ZYX
		
		file.write('''
			Property: "RotationOffset", "Vector3D", "",0,0,0
			Property: "RotationPivot", "Vector3D", "",0,0,0
			Property: "ScalingOffset", "Vector3D", "",0,0,0
			Property: "ScalingPivot", "Vector3D", "",0,0,0
			Property: "TranslationActive", "bool", "",0
			Property: "TranslationMin", "Vector3D", "",0,0,0
			Property: "TranslationMax", "Vector3D", "",0,0,0
			Property: "TranslationMinX", "bool", "",0
			Property: "TranslationMinY", "bool", "",0
			Property: "TranslationMinZ", "bool", "",0
			Property: "TranslationMaxX", "bool", "",0
			Property: "TranslationMaxY", "bool", "",0
			Property: "TranslationMaxZ", "bool", "",0
			Property: "RotationOrder", "enum", "",0
			Property: "RotationSpaceForLimitOnly", "bool", "",0
			Property: "AxisLen", "double", "",10
			Property: "PreRotation", "Vector3D", "",0,0,0
			Property: "PostRotation", "Vector3D", "",0,0,0
			Property: "RotationActive", "bool", "",0
			Property: "RotationMin", "Vector3D", "",0,0,0
			Property: "RotationMax", "Vector3D", "",0,0,0
			Property: "RotationMinX", "bool", "",0
			Property: "RotationMinY", "bool", "",0
			Property: "RotationMinZ", "bool", "",0
			Property: "RotationMaxX", "bool", "",0
			Property: "RotationMaxY", "bool", "",0
			Property: "RotationMaxZ", "bool", "",0
			Property: "RotationStiffnessX", "double", "",0
			Property: "RotationStiffnessY", "double", "",0
			Property: "RotationStiffnessZ", "double", "",0
			Property: "MinDampRangeX", "double", "",0
			Property: "MinDampRangeY", "double", "",0
			Property: "MinDampRangeZ", "double", "",0
			Property: "MaxDampRangeX", "double", "",0
			Property: "MaxDampRangeY", "double", "",0
			Property: "MaxDampRangeZ", "double", "",0
			Property: "MinDampStrengthX", "double", "",0
			Property: "MinDampStrengthY", "double", "",0
			Property: "MinDampStrengthZ", "double", "",0
			Property: "MaxDampStrengthX", "double", "",0
			Property: "MaxDampStrengthY", "double", "",0
			Property: "MaxDampStrengthZ", "double", "",0
			Property: "PreferedAngleX", "double", "",0
			Property: "PreferedAngleY", "double", "",0
			Property: "PreferedAngleZ", "double", "",0
			Property: "InheritType", "enum", "",0
			Property: "ScalingActive", "bool", "",0
			Property: "ScalingMin", "Vector3D", "",1,1,1
			Property: "ScalingMax", "Vector3D", "",1,1,1
			Property: "ScalingMinX", "bool", "",0
			Property: "ScalingMinY", "bool", "",0
			Property: "ScalingMinZ", "bool", "",0
			Property: "ScalingMaxX", "bool", "",0
			Property: "ScalingMaxY", "bool", "",0
			Property: "ScalingMaxZ", "bool", "",0
			Property: "GeometricTranslation", "Vector3D", "",0,0,0
			Property: "GeometricRotation", "Vector3D", "",0,0,0
			Property: "GeometricScaling", "Vector3D", "",1,1,1
			Property: "LookAtProperty", "object", ""
			Property: "UpVectorProperty", "object", ""
			Property: "Show", "bool", "",1
			Property: "NegativePercentShapeSupport", "bool", "",1
			Property: "DefaultAttributeIndex", "int", "",0''')
		if ob and type(ob) != Blender.Types.BoneType:
			# Only mesh objects have color 
			file.write('\n\t\t\tProperty: "Color", "Color", "A",0.8,0.8,0.8')
			file.write('\n\t\t\tProperty: "Size", "double", "",100')
			file.write('\n\t\t\tProperty: "Look", "enum", "",1')
		
		return loc, rot, scale, matrix, matrix_rot
	
	
	# -------------------------------------------- Armatures
	#def write_bone(bone, name, matrix_mod):
	def write_bone(my_bone):
		file.write('\n\tModel: "Model::%s", "Limb" {' % my_bone.fbxName)
		file.write('\n\t\tVersion: 232')
		
		poseMatrix = write_object_props(my_bone.blenBone, None, None, my_bone.fbxArm.matrixWorld)[3]
		pose_items.append( (my_bone.fbxName, poseMatrix) )
		
		
		# file.write('\n\t\t\tProperty: "Size", "double", "",%.6f' % ((my_bone.blenData.head['ARMATURESPACE'] - my_bone.blenData.tail['ARMATURESPACE']) * my_bone.fbxArm.matrixWorld).length)
		file.write('\n\t\t\tProperty: "Size", "double", "",1')
		
		#((my_bone.blenData.head['ARMATURESPACE'] * my_bone.fbxArm.matrixWorld) - (my_bone.blenData.tail['ARMATURESPACE'] * my_bone.fbxArm.matrixWorld)).length)
		
		"""
		file.write('\n\t\t\tProperty: "LimbLength", "double", "",%.6f' %\
			((my_bone.blenBone.head['ARMATURESPACE'] - my_bone.blenBone.tail['ARMATURESPACE']) * my_bone.fbxArm.matrixWorld).length)
		"""
		
		file.write('\n\t\t\tProperty: "LimbLength", "double", "",%.6f' %\
			(my_bone.blenBone.head['ARMATURESPACE'] - my_bone.blenBone.tail['ARMATURESPACE']).length)
		
		#file.write('\n\t\t\tProperty: "LimbLength", "double", "",1')
		file.write('\n\t\t\tProperty: "Color", "ColorRGB", "",0.8,0.8,0.8')
		file.write('\n\t\t\tProperty: "Color", "Color", "A",0.8,0.8,0.8')
		file.write('\n\t\t}')
		file.write('\n\t\tMultiLayer: 0')
		file.write('\n\t\tMultiTake: 1')
		file.write('\n\t\tShading: Y')
		file.write('\n\t\tCulling: "CullingOff"')
		file.write('\n\t\tTypeFlags: "Skeleton"')
		file.write('\n\t}')
	
	def write_camera_switch():
		file.write('''
	Model: "Model::Camera Switcher", "CameraSwitcher" {
		Version: 232''')
		
		write_object_props()
		file.write('''
			Property: "Color", "Color", "A",0.8,0.8,0.8
			Property: "Camera Index", "Integer", "A+",100
		}
		MultiLayer: 0
		MultiTake: 1
		Hidden: "True"
		Shading: W
		Culling: "CullingOff"
		Version: 101
		Name: "Model::Camera Switcher"
		CameraId: 0
		CameraName: 100
		CameraIndexName: 
	}''')
	
	def write_camera_dummy(name, loc, near, far, proj_type, up):
		file.write('\n\tModel: "Model::%s", "Camera" {' % name )
		file.write('\n\t\tVersion: 232')
		write_object_props(None, loc)
		
		file.write('\n\t\t\tProperty: "Color", "Color", "A",0.8,0.8,0.8')
		file.write('\n\t\t\tProperty: "Roll", "Roll", "A+",0')
		file.write('\n\t\t\tProperty: "FieldOfView", "FieldOfView", "A+",40')
		file.write('\n\t\t\tProperty: "FieldOfViewX", "FieldOfView", "A+",1')
		file.write('\n\t\t\tProperty: "FieldOfViewY", "FieldOfView", "A+",1')
		file.write('\n\t\t\tProperty: "OpticalCenterX", "Real", "A+",0')
		file.write('\n\t\t\tProperty: "OpticalCenterY", "Real", "A+",0')
		file.write('\n\t\t\tProperty: "BackgroundColor", "Color", "A+",0.63,0.63,0.63')
		file.write('\n\t\t\tProperty: "TurnTable", "Real", "A+",0')
		file.write('\n\t\t\tProperty: "DisplayTurnTableIcon", "bool", "",1')
		file.write('\n\t\t\tProperty: "Motion Blur Intensity", "Real", "A+",1')
		file.write('\n\t\t\tProperty: "UseMotionBlur", "bool", "",0')
		file.write('\n\t\t\tProperty: "UseRealTimeMotionBlur", "bool", "",1')
		file.write('\n\t\t\tProperty: "ResolutionMode", "enum", "",0')
		file.write('\n\t\t\tProperty: "ApertureMode", "enum", "",2')
		file.write('\n\t\t\tProperty: "GateFit", "enum", "",0')
		file.write('\n\t\t\tProperty: "FocalLength", "Real", "A+",21.3544940948486')
		file.write('\n\t\t\tProperty: "CameraFormat", "enum", "",0')
		file.write('\n\t\t\tProperty: "AspectW", "double", "",320')
		file.write('\n\t\t\tProperty: "AspectH", "double", "",200')
		file.write('\n\t\t\tProperty: "PixelAspectRatio", "double", "",1')
		file.write('\n\t\t\tProperty: "UseFrameColor", "bool", "",0')
		file.write('\n\t\t\tProperty: "FrameColor", "ColorRGB", "",0.3,0.3,0.3')
		file.write('\n\t\t\tProperty: "ShowName", "bool", "",1')
		file.write('\n\t\t\tProperty: "ShowGrid", "bool", "",1')
		file.write('\n\t\t\tProperty: "ShowOpticalCenter", "bool", "",0')
		file.write('\n\t\t\tProperty: "ShowAzimut", "bool", "",1')
		file.write('\n\t\t\tProperty: "ShowTimeCode", "bool", "",0')
		file.write('\n\t\t\tProperty: "NearPlane", "double", "",%.6f' % near)
		file.write('\n\t\t\tProperty: "FarPlane", "double", "",%.6f' % far)
		file.write('\n\t\t\tProperty: "FilmWidth", "double", "",0.816')
		file.write('\n\t\t\tProperty: "FilmHeight", "double", "",0.612')
		file.write('\n\t\t\tProperty: "FilmAspectRatio", "double", "",1.33333333333333')
		file.write('\n\t\t\tProperty: "FilmSqueezeRatio", "double", "",1')
		file.write('\n\t\t\tProperty: "FilmFormatIndex", "enum", "",4')
		file.write('\n\t\t\tProperty: "ViewFrustum", "bool", "",1')
		file.write('\n\t\t\tProperty: "ViewFrustumNearFarPlane", "bool", "",0')
		file.write('\n\t\t\tProperty: "ViewFrustumBackPlaneMode", "enum", "",2')
		file.write('\n\t\t\tProperty: "BackPlaneDistance", "double", "",100')
		file.write('\n\t\t\tProperty: "BackPlaneDistanceMode", "enum", "",0')
		file.write('\n\t\t\tProperty: "ViewCameraToLookAt", "bool", "",1')
		file.write('\n\t\t\tProperty: "LockMode", "bool", "",0')
		file.write('\n\t\t\tProperty: "LockInterestNavigation", "bool", "",0')
		file.write('\n\t\t\tProperty: "FitImage", "bool", "",0')
		file.write('\n\t\t\tProperty: "Crop", "bool", "",0')
		file.write('\n\t\t\tProperty: "Center", "bool", "",1')
		file.write('\n\t\t\tProperty: "KeepRatio", "bool", "",1')
		file.write('\n\t\t\tProperty: "BackgroundMode", "enum", "",0')
		file.write('\n\t\t\tProperty: "BackgroundAlphaTreshold", "double", "",0.5')
		file.write('\n\t\t\tProperty: "ForegroundTransparent", "bool", "",1')
		file.write('\n\t\t\tProperty: "DisplaySafeArea", "bool", "",0')
		file.write('\n\t\t\tProperty: "SafeAreaDisplayStyle", "enum", "",1')
		file.write('\n\t\t\tProperty: "SafeAreaAspectRatio", "double", "",1.33333333333333')
		file.write('\n\t\t\tProperty: "Use2DMagnifierZoom", "bool", "",0')
		file.write('\n\t\t\tProperty: "2D Magnifier Zoom", "Real", "A+",100')
		file.write('\n\t\t\tProperty: "2D Magnifier X", "Real", "A+",50')
		file.write('\n\t\t\tProperty: "2D Magnifier Y", "Real", "A+",50')
		file.write('\n\t\t\tProperty: "CameraProjectionType", "enum", "",%i' % proj_type)
		file.write('\n\t\t\tProperty: "UseRealTimeDOFAndAA", "bool", "",0')
		file.write('\n\t\t\tProperty: "UseDepthOfField", "bool", "",0')
		file.write('\n\t\t\tProperty: "FocusSource", "enum", "",0')
		file.write('\n\t\t\tProperty: "FocusAngle", "double", "",3.5')
		file.write('\n\t\t\tProperty: "FocusDistance", "double", "",200')
		file.write('\n\t\t\tProperty: "UseAntialiasing", "bool", "",0')
		file.write('\n\t\t\tProperty: "AntialiasingIntensity", "double", "",0.77777')
		file.write('\n\t\t\tProperty: "UseAccumulationBuffer", "bool", "",0')
		file.write('\n\t\t\tProperty: "FrameSamplingCount", "int", "",7')
		file.write('\n\t\t}')
		file.write('\n\t\tMultiLayer: 0')
		file.write('\n\t\tMultiTake: 0')
		file.write('\n\t\tHidden: "True"')
		file.write('\n\t\tShading: Y')
		file.write('\n\t\tCulling: "CullingOff"')
		file.write('\n\t\tTypeFlags: "Camera"')
		file.write('\n\t\tGeometryVersion: 124')
		file.write('\n\t\tPosition: %.6f,%.6f,%.6f' % loc)
		file.write('\n\t\tUp: %i,%i,%i' % up)
		file.write('\n\t\tLookAt: 0,0,0')
		file.write('\n\t\tShowInfoOnMoving: 1')
		file.write('\n\t\tShowAudio: 0')
		file.write('\n\t\tAudioColor: 0,1,0')
		file.write('\n\t\tCameraOrthoZoom: 1')
		file.write('\n\t}')
	
	def write_camera_default():
		# This sucks but to match FBX converter its easier to
		# write the cameras though they are not needed.
		write_camera_dummy('Producer Perspective',	(0,71.3,287.5), 10, 4000, 0, (0,1,0))
		write_camera_dummy('Producer Top',			(0,4000,0), 1, 30000, 1, (0,0,-1))
		write_camera_dummy('Producer Bottom',			(0,-4000,0), 1, 30000, 1, (0,0,-1))
		write_camera_dummy('Producer Front',			(0,0,4000), 1, 30000, 1, (0,1,0))
		write_camera_dummy('Producer Back',			(0,0,-4000), 1, 30000, 1, (0,1,0))
		write_camera_dummy('Producer Right',			(4000,0,0), 1, 30000, 1, (0,1,0))
		write_camera_dummy('Producer Left',			(-4000,0,0), 1, 30000, 1, (0,1,0))
	
	def write_camera(my_cam):
		'''
		Write a blender camera
		'''
		render = sce.render
		width	= render.sizeX
		height	= render.sizeY
		aspect	= float(width)/height
		
		data = my_cam.blenObject.data
		
		file.write('\n\tModel: "Model::%s", "Camera" {' % my_cam.fbxName )
		file.write('\n\t\tVersion: 232')
		loc, rot, scale, matrix, matrix_rot = write_object_props(my_cam.blenObject)
		
		file.write('\n\t\t\tProperty: "Roll", "Roll", "A+",0')
		file.write('\n\t\t\tProperty: "FieldOfView", "FieldOfView", "A+",%.6f' % data.angle)
		file.write('\n\t\t\tProperty: "FieldOfViewX", "FieldOfView", "A+",1')
		file.write('\n\t\t\tProperty: "FieldOfViewY", "FieldOfView", "A+",1')
		file.write('\n\t\t\tProperty: "FocalLength", "Real", "A+",14.0323972702026')
		file.write('\n\t\t\tProperty: "OpticalCenterX", "Real", "A+",%.6f' % data.shiftX) # not sure if this is in the correct units?
		file.write('\n\t\t\tProperty: "OpticalCenterY", "Real", "A+",%.6f' % data.shiftY) # ditto 
		file.write('\n\t\t\tProperty: "BackgroundColor", "Color", "A+",0,0,0')
		file.write('\n\t\t\tProperty: "TurnTable", "Real", "A+",0')
		file.write('\n\t\t\tProperty: "DisplayTurnTableIcon", "bool", "",1')
		file.write('\n\t\t\tProperty: "Motion Blur Intensity", "Real", "A+",1')
		file.write('\n\t\t\tProperty: "UseMotionBlur", "bool", "",0')
		file.write('\n\t\t\tProperty: "UseRealTimeMotionBlur", "bool", "",1')
		file.write('\n\t\t\tProperty: "ResolutionMode", "enum", "",0')
		file.write('\n\t\t\tProperty: "ApertureMode", "enum", "",2')
		file.write('\n\t\t\tProperty: "GateFit", "enum", "",0')
		file.write('\n\t\t\tProperty: "CameraFormat", "enum", "",0')
		file.write('\n\t\t\tProperty: "AspectW", "double", "",%i' % width)
		file.write('\n\t\t\tProperty: "AspectH", "double", "",%i' % height)
		
		'''Camera aspect ratio modes.
			0 If the ratio mode is eWINDOW_SIZE, both width and height values aren't relevant.
			1 If the ratio mode is eFIXED_RATIO, the height value is set to 1.0 and the width value is relative to the height value.
			2 If the ratio mode is eFIXED_RESOLUTION, both width and height values are in pixels.
			3 If the ratio mode is eFIXED_WIDTH, the width value is in pixels and the height value is relative to the width value.
			4 If the ratio mode is eFIXED_HEIGHT, the height value is in pixels and the width value is relative to the height value. 
		
		Definition at line 234 of file kfbxcamera.h. '''
		
		file.write('\n\t\t\tProperty: "PixelAspectRatio", "double", "",2')
		
		file.write('\n\t\t\tProperty: "UseFrameColor", "bool", "",0')
		file.write('\n\t\t\tProperty: "FrameColor", "ColorRGB", "",0.3,0.3,0.3')
		file.write('\n\t\t\tProperty: "ShowName", "bool", "",1')
		file.write('\n\t\t\tProperty: "ShowGrid", "bool", "",1')
		file.write('\n\t\t\tProperty: "ShowOpticalCenter", "bool", "",0')
		file.write('\n\t\t\tProperty: "ShowAzimut", "bool", "",1')
		file.write('\n\t\t\tProperty: "ShowTimeCode", "bool", "",0')
		file.write('\n\t\t\tProperty: "NearPlane", "double", "",%.6f' % data.clipStart)
		file.write('\n\t\t\tProperty: "FarPlane", "double", "",%.6f' % data.clipStart)
		file.write('\n\t\t\tProperty: "FilmWidth", "double", "",1.0')
		file.write('\n\t\t\tProperty: "FilmHeight", "double", "",1.0')
		file.write('\n\t\t\tProperty: "FilmAspectRatio", "double", "",%.6f' % aspect)
		file.write('\n\t\t\tProperty: "FilmSqueezeRatio", "double", "",1')
		file.write('\n\t\t\tProperty: "FilmFormatIndex", "enum", "",0')
		file.write('\n\t\t\tProperty: "ViewFrustum", "bool", "",1')
		file.write('\n\t\t\tProperty: "ViewFrustumNearFarPlane", "bool", "",0')
		file.write('\n\t\t\tProperty: "ViewFrustumBackPlaneMode", "enum", "",2')
		file.write('\n\t\t\tProperty: "BackPlaneDistance", "double", "",100')
		file.write('\n\t\t\tProperty: "BackPlaneDistanceMode", "enum", "",0')
		file.write('\n\t\t\tProperty: "ViewCameraToLookAt", "bool", "",1')
		file.write('\n\t\t\tProperty: "LockMode", "bool", "",0')
		file.write('\n\t\t\tProperty: "LockInterestNavigation", "bool", "",0')
		file.write('\n\t\t\tProperty: "FitImage", "bool", "",0')
		file.write('\n\t\t\tProperty: "Crop", "bool", "",0')
		file.write('\n\t\t\tProperty: "Center", "bool", "",1')
		file.write('\n\t\t\tProperty: "KeepRatio", "bool", "",1')
		file.write('\n\t\t\tProperty: "BackgroundMode", "enum", "",0')
		file.write('\n\t\t\tProperty: "BackgroundAlphaTreshold", "double", "",0.5')
		file.write('\n\t\t\tProperty: "ForegroundTransparent", "bool", "",1')
		file.write('\n\t\t\tProperty: "DisplaySafeArea", "bool", "",0')
		file.write('\n\t\t\tProperty: "SafeAreaDisplayStyle", "enum", "",1')
		file.write('\n\t\t\tProperty: "SafeAreaAspectRatio", "double", "",%.6f' % aspect)
		file.write('\n\t\t\tProperty: "Use2DMagnifierZoom", "bool", "",0')
		file.write('\n\t\t\tProperty: "2D Magnifier Zoom", "Real", "A+",100')
		file.write('\n\t\t\tProperty: "2D Magnifier X", "Real", "A+",50')
		file.write('\n\t\t\tProperty: "2D Magnifier Y", "Real", "A+",50')
		file.write('\n\t\t\tProperty: "CameraProjectionType", "enum", "",0')
		file.write('\n\t\t\tProperty: "UseRealTimeDOFAndAA", "bool", "",0')
		file.write('\n\t\t\tProperty: "UseDepthOfField", "bool", "",0')
		file.write('\n\t\t\tProperty: "FocusSource", "enum", "",0')
		file.write('\n\t\t\tProperty: "FocusAngle", "double", "",3.5')
		file.write('\n\t\t\tProperty: "FocusDistance", "double", "",200')
		file.write('\n\t\t\tProperty: "UseAntialiasing", "bool", "",0')
		file.write('\n\t\t\tProperty: "AntialiasingIntensity", "double", "",0.77777')
		file.write('\n\t\t\tProperty: "UseAccumulationBuffer", "bool", "",0')
		file.write('\n\t\t\tProperty: "FrameSamplingCount", "int", "",7')
		
		file.write('\n\t\t}')
		file.write('\n\t\tMultiLayer: 0')
		file.write('\n\t\tMultiTake: 0')
		file.write('\n\t\tShading: Y')
		file.write('\n\t\tCulling: "CullingOff"')
		file.write('\n\t\tTypeFlags: "Camera"')
		file.write('\n\t\tGeometryVersion: 124')
		file.write('\n\t\tPosition: %.6f,%.6f,%.6f' % loc)
		file.write('\n\t\tUp: %.6f,%.6f,%.6f' % tuple(Vector(0,1,0) * matrix_rot) )
		file.write('\n\t\tLookAt: %.6f,%.6f,%.6f' % tuple(Vector(0,0,-1)*matrix_rot) )
		
		#file.write('\n\t\tUp: 0,0,0' )
		#file.write('\n\t\tLookAt: 0,0,0' )
		
		file.write('\n\t\tShowInfoOnMoving: 1')
		file.write('\n\t\tShowAudio: 0')
		file.write('\n\t\tAudioColor: 0,1,0')
		file.write('\n\t\tCameraOrthoZoom: 1')
		file.write('\n\t}')
	
	def write_light(my_light):
		light = my_light.blenObject.data
		file.write('\n\tModel: "Model::%s", "Light" {' % my_light.fbxName)
		file.write('\n\t\tVersion: 232')
		
		write_object_props(my_light.blenObject)
		
		# Why are these values here twice?????? - oh well, follow the holy sdk's output
		
		# Blender light types match FBX's, funny coincidence, we just need to
		# be sure that all unsupported types are made into a point light
		#ePOINT, 
		#eDIRECTIONAL
		#eSPOT
		light_type = light.type
		if light_type > 3: light_type = 0
		
		mode = light.mode
		if mode & Blender.Lamp.Modes.RayShadow or mode & Blender.Lamp.Modes.Shadows:
			do_shadow = 1
		else:
			do_shadow = 0
		
		if mode & Blender.Lamp.Modes.OnlyShadow or (mode & Blender.Lamp.Modes.NoDiffuse and mode & Blender.Lamp.Modes.NoSpecular):
			do_light = 0
		else:
			do_light = 1
		
		file.write('\n\t\t\tProperty: "LightType", "enum", "",%i' % light_type)
		file.write('\n\t\t\tProperty: "CastLightOnObject", "bool", "",1')
		file.write('\n\t\t\tProperty: "DrawVolumetricLight", "bool", "",1')
		file.write('\n\t\t\tProperty: "DrawGroundProjection", "bool", "",1')
		file.write('\n\t\t\tProperty: "DrawFrontFacingVolumetricLight", "bool", "",0')
		file.write('\n\t\t\tProperty: "GoboProperty", "object", ""')
		file.write('\n\t\t\tProperty: "Color", "Color", "A+",1,1,1')
		file.write('\n\t\t\tProperty: "Intensity", "Intensity", "A+",%.2f' % (min(light.energy*100, 200))) # clamp below 200
		file.write('\n\t\t\tProperty: "Cone angle", "Cone angle", "A+",%.2f' % light.spotSize)
		file.write('\n\t\t\tProperty: "Fog", "Fog", "A+",50')
		file.write('\n\t\t\tProperty: "Color", "Color", "A",%.2f,%.2f,%.2f' % tuple(light.col))
		file.write('\n\t\t\tProperty: "Intensity", "Intensity", "A+",%.2f' % (min(light.energy*100, 200))) # clamp below 200
		file.write('\n\t\t\tProperty: "Cone angle", "Cone angle", "A+",%.2f' % light.spotSize)
		file.write('\n\t\t\tProperty: "Fog", "Fog", "A+",50')
		file.write('\n\t\t\tProperty: "LightType", "enum", "",%i' % light_type)
		file.write('\n\t\t\tProperty: "CastLightOnObject", "bool", "",%i' % do_light)
		file.write('\n\t\t\tProperty: "DrawGroundProjection", "bool", "",1')
		file.write('\n\t\t\tProperty: "DrawFrontFacingVolumetricLight", "bool", "",0')
		file.write('\n\t\t\tProperty: "DrawVolumetricLight", "bool", "",1')
		file.write('\n\t\t\tProperty: "GoboProperty", "object", ""')
		file.write('\n\t\t\tProperty: "DecayType", "enum", "",0')
		file.write('\n\t\t\tProperty: "DecayStart", "double", "",%.2f' % light.dist)
		file.write('\n\t\t\tProperty: "EnableNearAttenuation", "bool", "",0')
		file.write('\n\t\t\tProperty: "NearAttenuationStart", "double", "",0')
		file.write('\n\t\t\tProperty: "NearAttenuationEnd", "double", "",0')
		file.write('\n\t\t\tProperty: "EnableFarAttenuation", "bool", "",0')
		file.write('\n\t\t\tProperty: "FarAttenuationStart", "double", "",0')
		file.write('\n\t\t\tProperty: "FarAttenuationEnd", "double", "",0')
		file.write('\n\t\t\tProperty: "CastShadows", "bool", "",%i' % do_shadow)
		file.write('\n\t\t\tProperty: "ShadowColor", "ColorRGBA", "",0,0,0,1')
		file.write('\n\t\t}')
		file.write('\n\t\tMultiLayer: 0')
		file.write('\n\t\tMultiTake: 0')
		file.write('\n\t\tShading: Y')
		file.write('\n\t\tCulling: "CullingOff"')
		file.write('\n\t\tTypeFlags: "Light"')
		file.write('\n\t\tGeometryVersion: 124')
		file.write('\n\t}')
	
	# matrixOnly is not used at the moment
	def write_null(my_null = None, fbxName = None, matrixOnly = None):
		# ob can be null
		if not fbxName: fbxName = my_null.fbxName
		
		file.write('\n\tModel: "Model::%s", "Null" {' % fbxName)
		file.write('\n\t\tVersion: 232')
		
		# only use this for the root matrix at the moment
		if matrixOnly:
			poseMatrix = write_object_props(None, None, matrixOnly)[3]
		
		else: # all other Null's
			if my_null:		poseMatrix = write_object_props(my_null.blenObject)[3]
			else:			poseMatrix = write_object_props()[3]
		
		pose_items.append((fbxName, poseMatrix))
		
		file.write('''
		}
		MultiLayer: 0
		MultiTake: 1
		Shading: Y
		Culling: "CullingOff"
		TypeFlags: "Null"
	}''')
	
	# Material Settings
	if world:	world_amb = world.getAmb()
	else:		world_amb = (0,0,0) # Default value
	
	def write_material(matname, mat):
		file.write('\n\tMaterial: "Material::%s", "" {' % matname)
		
		# Todo, add more material Properties.
		if mat:
			mat_cold = tuple(mat.rgbCol)
			mat_cols = tuple(mat.specCol)
			#mat_colm = tuple(mat.mirCol) # we wont use the mirror color
			mat_colamb = tuple([c for c in world_amb])
			
			mat_dif = mat.ref
			mat_amb = mat.amb
			mat_hard = (float(mat.hard)-1)/5.10
			mat_spec = mat.spec/2.0
			mat_alpha = mat.alpha
			mat_emit = mat.emit
			mat_shadeless = mat.mode & Blender.Material.Modes.SHADELESS
			if mat_shadeless:
				mat_shader = 'Lambert'
			else:
				if mat.diffuseShader == Blender.Material.Shaders.DIFFUSE_LAMBERT:
					mat_shader = 'Lambert'
				else:
					mat_shader = 'Phong'
		else:
			mat_cols = mat_cold = 0.8, 0.8, 0.8
			mat_colamb = 0.0,0.0,0.0
			# mat_colm 
			mat_dif = 1.0
			mat_amb = 0.5
			mat_hard = 20.0
			mat_spec = 0.2
			mat_alpha = 1.0
			mat_emit = 0.0
			mat_shadeless = False
			mat_shader = 'Phong'
		
		file.write('\n\t\tVersion: 102')
		file.write('\n\t\tShadingModel: "%s"' % mat_shader.lower())
		file.write('\n\t\tMultiLayer: 0')
		
		file.write('\n\t\tProperties60:  {')
		file.write('\n\t\t\tProperty: "ShadingModel", "KString", "", "%s"' % mat_shader)
		file.write('\n\t\t\tProperty: "MultiLayer", "bool", "",0')
		file.write('\n\t\t\tProperty: "EmissiveColor", "ColorRGB", "",%.4f,%.4f,%.4f' % mat_cold) # emit and diffuse color are he same in blender
		file.write('\n\t\t\tProperty: "EmissiveFactor", "double", "",%.4f' % mat_dif)
		
		file.write('\n\t\t\tProperty: "AmbientColor", "ColorRGB", "",%.4f,%.4f,%.4f' % mat_colamb)
		file.write('\n\t\t\tProperty: "AmbientFactor", "double", "",%.4f' % mat_amb)
		file.write('\n\t\t\tProperty: "DiffuseColor", "ColorRGB", "",%.4f,%.4f,%.4f' % mat_cold)
		file.write('\n\t\t\tProperty: "DiffuseFactor", "double", "",%.4f' % mat_emit)
		file.write('\n\t\t\tProperty: "Bump", "Vector3D", "",0,0,0')
		file.write('\n\t\t\tProperty: "TransparentColor", "ColorRGB", "",1,1,1')
		file.write('\n\t\t\tProperty: "TransparencyFactor", "double", "",%.4f' % (1.0 - mat_alpha))
		if not mat_shadeless:
			file.write('\n\t\t\tProperty: "SpecularColor", "ColorRGB", "",%.4f,%.4f,%.4f' % mat_cols)
			file.write('\n\t\t\tProperty: "SpecularFactor", "double", "",%.4f' % mat_spec)
			file.write('\n\t\t\tProperty: "ShininessExponent", "double", "",80.0')
			file.write('\n\t\t\tProperty: "ReflectionColor", "ColorRGB", "",0,0,0')
			file.write('\n\t\t\tProperty: "ReflectionFactor", "double", "",1')
		file.write('\n\t\t\tProperty: "Emissive", "ColorRGB", "",0,0,0')
		file.write('\n\t\t\tProperty: "Ambient", "ColorRGB", "",%.1f,%.1f,%.1f' % mat_colamb)
		file.write('\n\t\t\tProperty: "Diffuse", "ColorRGB", "",%.1f,%.1f,%.1f' % mat_cold)
		if not mat_shadeless:
			file.write('\n\t\t\tProperty: "Specular", "ColorRGB", "",%.1f,%.1f,%.1f' % mat_cols)
			file.write('\n\t\t\tProperty: "Shininess", "double", "",%.1f' % mat_hard)
		file.write('\n\t\t\tProperty: "Opacity", "double", "",%.1f' % mat_alpha)
		if not mat_shadeless:
			file.write('\n\t\t\tProperty: "Reflectivity", "double", "",0')

		file.write('\n\t\t}')
		file.write('\n\t}')
	
	def write_video(texname, tex):
		# Same as texture really!
		file.write('\n\tVideo: "Video::%s", "Clip" {' % texname)
		
		file.write('''
		Type: "Clip"
		Properties60:  {
			Property: "FrameRate", "double", "",0
			Property: "LastFrame", "int", "",0
			Property: "Width", "int", "",0
			Property: "Height", "int", "",0''')
		if tex:
			fname = tex.filename
			fname_strip = strip_path(fname)
		else:
			fname = fname_strip = ''
		
		file.write('\n\t\t\tProperty: "Path", "charptr", "", "%s"' % fname_strip)
		
		
		file.write('''
			Property: "StartFrame", "int", "",0
			Property: "StopFrame", "int", "",0
			Property: "PlaySpeed", "double", "",1
			Property: "Offset", "KTime", "",0
			Property: "InterlaceMode", "enum", "",0
			Property: "FreeRunning", "bool", "",0
			Property: "Loop", "bool", "",0
			Property: "AccessMode", "enum", "",0
		}
		UseMipMap: 0''')
		
		file.write('\n\t\tFilename: "%s"' % fname_strip)
		if fname_strip: fname_strip = '/' + fname_strip
		file.write('\n\t\tRelativeFilename: "fbx%s"' % fname_strip) # make relative
		file.write('\n\t}')

	
	def write_texture(texname, tex, num):
		# if tex == None then this is a dummy tex
		file.write('\n\tTexture: "Texture::%s", "TextureVideoClip" {' % texname)
		file.write('\n\t\tType: "TextureVideoClip"')
		file.write('\n\t\tVersion: 202')
		# TODO, rare case _empty_ exists as a name.
		file.write('\n\t\tTextureName: "Texture::%s"' % texname)
		
		file.write('''
		Properties60:  {
			Property: "Translation", "Vector", "A+",0,0,0
			Property: "Rotation", "Vector", "A+",0,0,0
			Property: "Scaling", "Vector", "A+",1,1,1''')
		file.write('\n\t\t\tProperty: "Texture alpha", "Number", "A+",%i' % num)
		
		
		# WrapModeU/V 0==rep, 1==clamp, TODO add support
		file.write('''
			Property: "TextureTypeUse", "enum", "",0
			Property: "CurrentTextureBlendMode", "enum", "",1
			Property: "UseMaterial", "bool", "",0
			Property: "UseMipMap", "bool", "",0
			Property: "CurrentMappingType", "enum", "",0
			Property: "UVSwap", "bool", "",0''')
		
		file.write('\n\t\t\tProperty: "WrapModeU", "enum", "",%i' % tex.clampX)
		file.write('\n\t\t\tProperty: "WrapModeV", "enum", "",%i' % tex.clampY)
		
		file.write('''
			Property: "TextureRotationPivot", "Vector3D", "",0,0,0
			Property: "TextureScalingPivot", "Vector3D", "",0,0,0
			Property: "VideoProperty", "object", ""
		}''')
		
		file.write('\n\t\tMedia: "Video::%s"' % texname)
		if tex:
			fname = tex.filename
			file.write('\n\t\tFileName: "%s"' % strip_path(fname))
			file.write('\n\t\tRelativeFilename: "fbx/%s"' % strip_path(fname)) # need some make relative command
		else:
			file.write('\n\t\tFileName: ""')
			file.write('\n\t\tRelativeFilename: "fbx"')
		
		file.write('''
		ModelUVTranslation: 0,0
		ModelUVScaling: 1,1
		Texture_Alpha_Source: "None"
		Cropping: 0,0,0,0
	}''')

	def write_deformer_skin(obname):
		'''
		Each mesh has its own deformer
		'''
		file.write('\n\tDeformer: "Deformer::Skin %s", "Skin" {' % obname)
		file.write('''
		Version: 100
		MultiLayer: 0
		Type: "Skin"
		Properties60:  {
		}
		Link_DeformAcuracy: 50
	}''')
	
	# in the example was 'Bip01 L Thigh_2'
	#def write_sub_deformer_skin(obname, group_name, bone, me, matrix_mod):
	#def write_sub_deformer_skin(obname, group_name, bone, weights, matrix_mod):
	def write_sub_deformer_skin(my_mesh, my_bone, weights):
	
		'''
		Each subdeformer is spesific to a mesh, but the bone it links to can be used by many sub-deformers
		So the SubDeformer needs the mesh-object name as a prefix to make it unique
		
		Its possible that there is no matching vgroup in this mesh, in that case no verts are in the subdeformer,
		a but silly but dosnt really matter
		'''
		file.write('\n\tDeformer: "SubDeformer::Cluster %s %s", "Cluster" {' % (my_mesh.fbxName, my_bone.fbxName))
		
		file.write('''
		Version: 100
		MultiLayer: 0
		Type: "Cluster"
		Properties60:  {
			Property: "SrcModel", "object", ""
			Property: "SrcModelReference", "object", ""
		}
		UserData: "", ""''')
		
		# Support for bone parents
		if my_mesh.fbxBoneParent:
			if my_mesh.fbxBoneParent == my_bone:
				# TODO - this is a bit lazy, we could have a simple write loop
				# for this case because all weights are 1.0 but for now this is ok
				# Parent Bones arent used all that much anyway.
				vgroup_data = [(j, 1.0) for j in xrange(len(my_mesh.blenData.verts))]
			else:
				# This bone is not a parent of this mesh object, no weights
				vgroup_data = []
			
		else:
			# Normal weight painted mesh
			if my_bone.blenName in weights[0]:
				# Before we used normalized wright list
				#vgroup_data = me.getVertsFromGroup(bone.name, 1)
				group_index = weights[0].index(my_bone.blenName)
				vgroup_data = [(j, weight[group_index]) for j, weight in enumerate(weights[1]) if weight[group_index]] 
			else:
				vgroup_data = []
		
		file.write('\n\t\tIndexes: ')
		
		i = -1
		for vg in vgroup_data:
			if i == -1:
				file.write('%i'  % vg[0])
				i=0
			else:
				if i==23:
					file.write('\n\t\t')
					i=0
				file.write(',%i' % vg[0])
			i+=1
		
		file.write('\n\t\tWeights: ')
		i = -1
		for vg in vgroup_data:
			if i == -1:
				file.write('%.8f'  % vg[1])
				i=0
			else:
				if i==38:
					file.write('\n\t\t')
					i=0
				file.write(',%.8f' % vg[1])
			i+=1
		
		
		m = mtx4_z90 * (my_bone.restMatrix * my_bone.fbxArm.matrixWorld)
		matstr = mat4x4str(m)
		matstr_i = mat4x4str(m.invert())
		
		file.write('\n\t\tTransform: %s' % matstr_i) # THIS IS __NOT__ THE GLOBAL MATRIX AS DOCUMENTED :/
		file.write('\n\t\tTransformLink: %s' % matstr)
		file.write('\n\t}')
	
	def write_mesh(my_mesh):
		
		me = my_mesh.blenData
		
		# if there are non NULL materials on this mesh
		if [mat for mat in my_mesh.blenMaterials if mat]: 	do_materials = True
		else:												do_materials = False
		
		if my_mesh.blenTextures:	do_textures = True
		else:						do_textures = False			
		
		
		file.write('\n\tModel: "Model::%s", "Mesh" {' % my_mesh.fbxName)
		file.write('\n\t\tVersion: 232') # newline is added in write_object_props
		
		if my_mesh.fbxArm:
			if my_mesh.origData:
				do_tx_write = True
			else:
				do_tx_write = False
				me.transform(my_mesh.matrixWorld)
			
		else:
			do_tx_write = False
		
		
		# When we have an armature...
		if my_mesh.fbxArm:
			# Apply the mesh matrix because bones arnt applied correctly if we use object transformation
			# Other then that, object matricies work well on meshes.
			# if this can be fixd, be sure to remove matrix multiplication on the verts.
			
			write_object_props(my_mesh.blenObject, None, mtx4_identity)
		else:
			write_object_props(my_mesh.blenObject, None, my_mesh.matrixWorld)
		
		file.write('\n\t\t}')
		file.write('\n\t\tMultiLayer: 0')
		file.write('\n\t\tMultiTake: 1')
		file.write('\n\t\tShading: Y')
		file.write('\n\t\tCulling: "CullingOff"')
		
		
		# Write the Real Mesh data here
		file.write('\n\t\tVertices: ')
		i=-1
		
		if do_tx_write :# transform verts on write?
			for v in me.verts:
				if i==-1:
					file.write('%.6f,%.6f,%.6f' % tuple(v.co * my_mesh.matrixWorld));	i=0
				else:
					if i==7:
						file.write('\n\t\t');	i=0
					file.write(',%.6f,%.6f,%.6f'% tuple(v.co * my_mesh.matrixWorld))
				i+=1
		else:	# same as above but has alredy been transformed
			for v in me.verts:
				if i==-1:
					file.write('%.6f,%.6f,%.6f' % tuple(v.co));	i=0
				else:
					if i==7:
						file.write('\n\t\t');	i=0
					file.write(',%.6f,%.6f,%.6f'% tuple(v.co))
				i+=1
				
		file.write('\n\t\tPolygonVertexIndex: ')
		i=-1
		for f in me.faces:
			fi = [v.index for v in f]
			# flip the last index, odd but it looks like
			# this is how fbx tells one face from another
			fi[-1] = -(fi[-1]+1)
			fi = tuple(fi)
			if i==-1:
				if len(f) == 3:		file.write('%i,%i,%i' % fi )
				else:				file.write('%i,%i,%i,%i' % fi )
				i=0
			else:
				if i==13:
					file.write('\n\t\t')
					i=0
				if len(f) == 3:		file.write(',%i,%i,%i' % fi )
				else:				file.write(',%i,%i,%i,%i' % fi )
			i+=1
		
		ed_val = [None, None]
		LOOSE = Blender.Mesh.EdgeFlags.LOOSE
		for ed in me.edges:
			if ed.flag & LOOSE:
				ed_val[0] = ed.v1.index
				ed_val[1] = -(ed.v2.index+1)
				if i==-1:
					file.write('%i,%i' % tuple(ed_val) )
					i=0
				else:
					if i==13:
						file.write('\n\t\t')
						i=0
					file.write(',%i,%i' % tuple(ed_val) )
				i+=1
		del LOOSE
		
		file.write('\n\t\tGeometryVersion: 124')
		
		file.write('''
		LayerElementNormal: 0 {
			Version: 101
			Name: ""
			MappingInformationType: "ByVertice"
			ReferenceInformationType: "Direct"
			Normals: ''')
		
		i=-1
		if do_tx_write: # transform normals on write?
			mtx_rot = my_mesh.matrixWorld.rotationPart()
			for v in me.verts:
				if i==-1:
					file.write('%.15f,%.15f,%.15f' % tuple(v.no * mtx_rot));	i=0
				else:
					if i==2:
						file.write('\n			 ');	i=0
					file.write(',%.15f,%.15f,%.15f' % tuple(v.no * mtx_rot))
				i+=1
			file.write('\n\t\t}')
			
		
		else:	# same as above but has alredy been transformed
			# wont handle non uniform scaling properly
			for v in me.verts:
				if i==-1:
					file.write('%.15f,%.15f,%.15f' % tuple(v.no));	i=0
				else:
					if i==2:
						file.write('\n			 ');	i=0
					file.write(',%.15f,%.15f,%.15f' % tuple(v.no))
				i+=1
			file.write('\n\t\t}')
		
		
		
		# Write VertexColor Layers
		collayers = []
		if me.vertexColors:
			collayers = me.getColorLayerNames()
			collayer_orig = me.activeColorLayer
			for colindex, collayer in enumerate(collayers):
				me.activeColorLayer = collayer
				file.write('\n\t\tLayerElementColor: %i {' % colindex)
				file.write('\n\t\t\tVersion: 101')
				file.write('\n\t\t\tName: "%s"' % collayer)
				
				file.write('''
			MappingInformationType: "ByPolygonVertex"
			ReferenceInformationType: "IndexToDirect"
			Colors: ''')
			
				i = -1
				ii = 0 # Count how many Colors we write
				
				for f in me.faces:
					for col in f.col:
						if i==-1:
							file.write('%i,%i,%i' % (col[0], col[1], col[2]))
							i=0
						else:
							if i==7:
								file.write('\n\t\t\t\t')
								i=0
							file.write(',%i,%i,%i' % (col[0], col[1], col[2]))
						i+=1
						ii+=1 # One more Color
				
				file.write('\n\t\t\tColorIndex: ')
				i = -1
				for j in xrange(ii):
					if i == -1:
						file.write('%i' % j)
						i=0
					else:
						if i==55:
							file.write('\n\t\t\t\t')
							i=0
						file.write(',%i' % j)
					i+=1
				
				file.write('\n\t\t}')
		
		
		
		# Write UV and texture layers.
		uvlayers = []
		if me.faceUV:
			uvlayers = me.getUVLayerNames()
			uvlayer_orig = me.activeUVLayer
			for uvindex, uvlayer in enumerate(uvlayers):
				me.activeUVLayer = uvlayer
				file.write('\n\t\tLayerElementUV: %i {' % uvindex)
				file.write('\n\t\t\tVersion: 101')
				file.write('\n\t\t\tName: "%s"' % uvlayer)
				
				file.write('''
			MappingInformationType: "ByPolygonVertex"
			ReferenceInformationType: "IndexToDirect"
			UV: ''')
			
				i = -1
				ii = 0 # Count how many UVs we write
				
				for f in me.faces:
					for uv in f.uv:
						if i==-1:
							file.write('%.6f,%.6f' % tuple(uv))
							i=0
						else:
							if i==7:
								file.write('\n			 ')
								i=0
							file.write(',%.6f,%.6f' % tuple(uv))
						i+=1
						ii+=1 # One more UV
				
				file.write('\n\t\t\tUVIndex: ')
				i = -1
				for j in xrange(ii):
					if i == -1:
						file.write('%i'  % j)
						i=0
					else:
						if i==55:
							file.write('\n\t\t\t\t')
							i=0
						file.write(',%i' % j)
					i+=1
				
				file.write('\n\t\t}')
				
				if do_textures:
					file.write('\n\t\tLayerElementTexture: %i {' % uvindex)
					file.write('\n\t\t\tVersion: 101')
					file.write('\n\t\t\tName: "%s"' % uvlayer)
					
					if len(my_mesh.blenTextures) == 1:
						file.write('\n\t\t\tMappingInformationType: "AllSame"')
					else:
						file.write('\n\t\t\tMappingInformationType: "ByPolygon"')
					
					file.write('\n\t\t\tReferenceInformationType: "IndexToDirect"')
					file.write('\n\t\t\tBlendMode: "Translucent"')
					file.write('\n\t\t\tTextureAlpha: 1')
					file.write('\n\t\t\tTextureId: ')
					
					if len(my_mesh.blenTextures) == 1:
						file.write('0')
					else:
						#texture_mapping_local = {None:0}
						texture_mapping_local = {None:-1}
						
						i = 0 # 1 for dummy
						for tex in my_mesh.blenTextures:
							texture_mapping_local[tex] = i
							i+=1
						
						i=-1
						for f in me.faces:
							img_key = f.image
							
							if i==-1:
								i=0
								file.write( '%s' % texture_mapping_local[img_key])
							else:
								if i==55:
									file.write('\n			 ')
									i=0
								
								file.write(',%s' % texture_mapping_local[img_key])
							i+=1
				
				else:
					file.write('''
		LayerElementTexture: 0 {
			Version: 101
			Name: ""
			MappingInformationType: "NoMappingInformation"
			ReferenceInformationType: "IndexToDirect"
			BlendMode: "Translucent"
			TextureAlpha: 1
			TextureId: ''')
				file.write('\n\t\t}')
			
			me.activeUVLayer = uvlayer_orig
			
		# Done with UV/textures.
		
		if do_materials:
			file.write('\n\t\tLayerElementMaterial: 0 {')
			file.write('\n\t\t\tVersion: 101')
			file.write('\n\t\t\tName: ""')
			
			if len(my_mesh.blenMaterials) == 1:
				file.write('\n\t\t\tMappingInformationType: "AllSame"')
			else:
				file.write('\n\t\t\tMappingInformationType: "ByPolygon"')
			
			file.write('\n\t\t\tReferenceInformationType: "IndexToDirect"')
			file.write('\n\t\t\tMaterials: ')
			
			if len(my_mesh.blenMaterials) == 1:
				file.write('0')
			else:
				# Build a material mapping for this 
				#material_mapping_local = [0] * 16 # local-index : global index.
				material_mapping_local = [-1] * 16 # local-index : global index.
				i= 0 # 1
				for j, mat in enumerate(my_mesh.blenMaterials):
					if mat:
						material_mapping_local[j] = i
						i+=1
					# else leave as -1
				
				len_material_mapping_local = len(material_mapping_local)
				
				i=-1
				for f in me.faces:
					f_mat = f.mat
					if f_mat >= len_material_mapping_local:
						f_mat = 0
					
					if i==-1:
						i=0
						file.write( '%s' % (material_mapping_local[f_mat]))
					else:
						if i==55:
							file.write('\n\t\t\t\t')
							i=0
						
						file.write(',%s' % (material_mapping_local[f_mat]))
					i+=1
			
			file.write('\n\t\t}')
		
		file.write('''
		Layer: 0 {
			Version: 100
			LayerElement:  {
				Type: "LayerElementNormal"
				TypedIndex: 0
			}''')
		
		if do_materials:
			file.write('''
			LayerElement:  {
				Type: "LayerElementMaterial"
				TypedIndex: 0
			}''')
			
		# Always write this
		if do_textures:
			file.write('''
			LayerElement:  {
				Type: "LayerElementTexture"
				TypedIndex: 0
			}''')
		
		if me.vertexColors:
			file.write('''
			LayerElement:  {
				Type: "LayerElementColor"
				TypedIndex: 0
			}''')
		
		if me.faceUV:
			file.write('''
			LayerElement:  {
				Type: "LayerElementUV"
				TypedIndex: 0
			}''')
		
		
		file.write('\n\t\t}')
		
		if len(uvlayers) > 1:
			for i in xrange(1, len(uvlayers)):
				
				file.write('\n\t\tLayer: %i {' % i)
				file.write('\n\t\t\tVersion: 100')
				
				file.write('''
			LayerElement:  {
				Type: "LayerElementUV"''')
				
				file.write('\n\t\t\t\tTypedIndex: %i' % i)
				file.write('\n\t\t\t}')
				
				if do_textures:
					
					file.write('''
			LayerElement:  {
				Type: "LayerElementTexture"''')
					
					file.write('\n\t\t\t\tTypedIndex: %i' % i)
					file.write('\n\t\t\t}')
				
				file.write('\n\t\t}')
		
		if len(collayers) > 1:
			# Take into account any UV layers
			layer_offset = 0
			if uvlayers: layer_offset = len(uvlayers)-1
			
			for i in xrange(layer_offset, len(collayers)+layer_offset):
				file.write('\n\t\tLayer: %i {' % i)
				file.write('\n\t\t\tVersion: 100')
				
				file.write('''
			LayerElement:  {
				Type: "LayerElementColor"''')
				
				file.write('\n\t\t\t\tTypedIndex: %i' % i)
				file.write('\n\t\t\t}')
				file.write('\n\t\t}')
		file.write('\n\t}')
	
	def write_group(name):
		file.write('\n\tGroupSelection: "GroupSelection::%s", "Default" {' % name)
		
		file.write('''
		Properties60:  {
			Property: "MultiLayer", "bool", "",0
			Property: "Pickable", "bool", "",1
			Property: "Transformable", "bool", "",1
			Property: "Show", "bool", "",1
		}
		MultiLayer: 0
	}''')
	
	
	# add meshes here to clear because they are not used anywhere.
	meshes_to_clear = []
	
	ob_meshes = []	
	ob_lights = []
	ob_cameras = []
	# in fbx we export bones as children of the mesh
	# armatures not a part of a mesh, will be added to ob_arms
	ob_bones = [] 
	ob_arms = []
	ob_null = [] # emptys
	
	groups = [] # blender groups, only add ones that have objects in the selections
	materials = {}
	textures = {}
	
	tmp_ob_type = ob_type = None # incase no objects are exported, so as not to raise an error
	
	# if EXP_OBS_SELECTED is false, use sceens objects
	if not batch_objects:
		if EXP_OBS_SELECTED:	tmp_objects = sce.objects.context
		else:					tmp_objects = sce.objects
	else:
		tmp_objects = batch_objects
	
	if EXP_ARMATURE:
		# This is needed so applying modifiers dosnt apply the armature deformation, its also needed
		# ...so mesh objects return their rest worldspace matrix when bone-parents are exported as weighted meshes.
		# set every armature to its rest, backup the original values so we done mess up the scene
		ob_arms_orig_rest = [arm.restPosition for arm in bpy.data.armatures]
		
		for arm in bpy.data.armatures:
			arm.restPosition = True
		
		if ob_arms_orig_rest:
			for ob_base in bpy.data.objects:
				#if ob_base.type == 'Armature':
				ob_base.makeDisplayList()
					
			# This causes the makeDisplayList command to effect the mesh
			Blender.Set('curframe', Blender.Get('curframe'))
			
		
	for ob_base in tmp_objects:
		for ob, mtx in BPyObject.getDerivedObjects(ob_base):
			#for ob in [ob_base,]:
			tmp_ob_type = ob.type
			if tmp_ob_type == 'Camera':
				if EXP_CAMERA:
					ob_cameras.append(my_object_generic(ob, mtx))
			elif tmp_ob_type == 'Lamp':
				if EXP_LAMP:
					ob_lights.append(my_object_generic(ob, mtx))
			elif tmp_ob_type == 'Armature':
				if EXP_ARMATURE:
					# TODO - armatures dont work in dupligroups!
					if ob not in ob_arms: ob_arms.append(ob)
					# ob_arms.append(ob) # replace later. was "ob_arms.append(sane_obname(ob), ob)"
			elif tmp_ob_type == 'Empty':
				if EXP_EMPTY:
					ob_null.append(my_object_generic(ob, mtx))
			elif EXP_MESH:
				origData = True
				if tmp_ob_type != 'Mesh':
					me = bpy.data.meshes.new()
					try:	me.getFromObject(ob)
					except:	me = None
					if me:
						meshes_to_clear.append( me )
						mats = me.materials
						origData = False
				else:
					# Mesh Type!
					if EXP_MESH_APPLY_MOD:
						me = bpy.data.meshes.new()
						me.getFromObject(ob)
						
						# so we keep the vert groups
						if EXP_ARMATURE:
							orig_mesh = ob.getData(mesh=1)
							if orig_mesh.getVertGroupNames():
								ob.copy().link(me)
								# If new mesh has no vgroups we can try add if verts are teh same
								if not me.getVertGroupNames(): # vgroups were not kept by the modifier
									if len(me.verts) == len(orig_mesh.verts):
										groupNames, vWeightDict = BPyMesh.meshWeight2Dict(orig_mesh)
										BPyMesh.dict2MeshWeight(me, groupNames, vWeightDict)
						
						# print ob, me, me.getVertGroupNames()
						meshes_to_clear.append( me )
						origData = False
						mats = me.materials
					else:
						me = ob.getData(mesh=1)
						mats = me.materials
						
						# Support object colors
						tmp_colbits = ob.colbits
						if tmp_colbits:
							tmp_ob_mats = ob.getMaterials(1) # 1 so we get None's too.
							for i in xrange(16):
								if tmp_colbits & (1<<i):
									mats[i] = tmp_ob_mats[i]
							del tmp_ob_mats
						del tmp_colbits
							
					
				if me:
					# This WILL modify meshes in blender if EXP_MESH_APPLY_MOD is disabled.
					# so strictly this is bad. but only in rare cases would it have negative results
					# say with dupliverts the objects would rotate a bit differently
					if EXP_MESH_HQ_NORMALS:
						BPyMesh.meshCalcNormals(me) # high quality normals nice for realtime engines.
					
					for mat in mats:
						# 2.44 use mat.lib too for uniqueness
						if mat: materials[mat] = mat
					
					texture_mapping_local = {}
					if me.faceUV:
						uvlayer_orig = me.activeUVLayer
						for uvlayer in me.getUVLayerNames():
							me.activeUVLayer = uvlayer
							for f in me.faces:
								img = f.image
								textures[img] = texture_mapping_local[img] = img
							
							me.activeUVLayer = uvlayer_orig
					
					if EXP_ARMATURE:
						armob = BPyObject.getObjectArmature(ob)
						blenParentBoneName = None
						
						# Note - Fixed in BPyObject but for now just copy the function because testers wont have up to date modukes,
						# TODO - remove this for 2.45 release since getObjectArmature has been fixed
						if (not armob) and ob.parent and ob.parent.type == 'Armature' and ob.parentType == Blender.Object.ParentTypes.ARMATURE:
							armob = ob.parent
						
						# parent bone - special case
						if (not armob) and ob.parent and ob.parent.type == 'Armature' and ob.parentType == Blender.Object.ParentTypes.BONE:
							armob = ob.parent
							blenParentBoneName = ob.parentbonename
						
							
						if armob and armob not in ob_arms:
							ob_arms.append(armob)
					
					else:
						blenParentBoneName = armob = None
					
					my_mesh = my_object_generic(ob, mtx)
					my_mesh.blenData =		me
					my_mesh.origData = 		origData
					my_mesh.blenMaterials =	mats
					my_mesh.blenTextures =	texture_mapping_local.values()
					
					# if only 1 null texture then empty the list
					if len(my_mesh.blenTextures) == 1 and my_mesh.blenTextures[0] == None:
						my_mesh.blenTextures = []
					
					my_mesh.fbxArm =	armob					# replace with my_object_generic armature instance later
					my_mesh.fbxBoneParent = blenParentBoneName	# replace with my_bone instance later
					
					ob_meshes.append( my_mesh )
	
	if EXP_ARMATURE:
		# now we have the meshes, restore the rest arm position
		for i, arm in enumerate(bpy.data.armatures):
			arm.restPosition = ob_arms_orig_rest[i]
			
		if ob_arms_orig_rest:
			for ob_base in bpy.data.objects:
				if ob_base.type == 'Armature':
					ob_base.makeDisplayList()
			# This causes the makeDisplayList command to effect the mesh
			Blender.Set('curframe', Blender.Get('curframe'))
	
	del tmp_ob_type, tmp_objects
	
	# now we have collected all armatures, add bones
	for i, ob in enumerate(ob_arms):
		
		ob_arms[i] = my_arm = my_object_generic(ob)
		
		my_arm.fbxBones =		[]
		my_arm.blenData =		ob.data
		my_arm.blenAction =		ob.action
		my_arm.blenActionList =	[]
		
		# fbxName, blenderObject, my_bones, blenderActions
		#ob_arms[i] = fbxArmObName, ob, arm_my_bones, (ob.action, [])
		
		for bone in my_arm.blenData.bones.values():
			my_bone = my_bone_class(bone, my_arm)
			my_arm.fbxBones.append( my_bone )
			ob_bones.append( my_bone )
	
	# add the meshes to the bones and replace the meshes armature with own armature class
	#for obname, ob, mtx, me, mats, arm, armname in ob_meshes:
	for my_mesh in ob_meshes:
		# Replace 
		# ...this could be sped up with dictionary mapping but its unlikely for
		# it ever to be a bottleneck - (would need 100+ meshes using armatures)
		if my_mesh.fbxArm:
			for my_arm in ob_arms:
				if my_arm.blenObject == my_mesh.fbxArm:
					my_mesh.fbxArm = my_arm
					break
		
		for my_bone in ob_bones:
			
			# The mesh uses this bones armature!
			if my_bone.fbxArm == my_mesh.fbxArm:
				my_bone.blenMeshes[my_mesh.fbxName] = me
				
				
				# parent bone: replace bone names with our class instances
				# my_mesh.fbxBoneParent is None or a blender bone name initialy, replacing if the names match.
				if my_mesh.fbxBoneParent == my_bone.blenName:
					my_mesh.fbxBoneParent = my_bone
	
	bone_deformer_count = 0 # count how many bones deform a mesh
	my_bone_blenParent = None
	for my_bone in ob_bones:
		my_bone_blenParent = my_bone.blenBone.parent
		if my_bone_blenParent:
			for my_bone_parent in ob_bones:
				# Note 2.45rc2 you can compare bones normally
				if my_bone_blenParent.name == my_bone_parent.blenName and my_bone.fbxArm == my_bone_parent.fbxArm:
					my_bone.parent = my_bone_parent
					break
		
		# Not used at the moment
		# my_bone.calcRestMatrixLocal()
		bone_deformer_count += len(my_bone.blenMeshes)
	
	del my_bone_blenParent 
	
	
	
	
	# Build a list of groups we use.
	bpy.data.objects.tag = False
	tmp_obmapping = {}
	for ob_generic in (ob_meshes, ob_arms, ob_cameras, ob_lights, ob_null):
		for ob_base in ob_generic:
			ob_base.blenObject.tag = True
			tmp_obmapping[ob_base.blenObject] = ob_base.fbxGroupNames
	
	for blenGroup in bpy.data.groups:
		fbxGroupName = None
		for ob in blenGroup.objects:
			if ob.tag:
				if fbxGroupName == None:
					fbxGroupName = sane_groupname(blenGroup)
					groups.append((fbxGroupName, blenGroup))
				
				tmp_obmapping[ob].append(fbxGroupName) # also adds to the objects fbxGroupNames
	
	groups.sort() # not really needed
	del tmp_obmapping
	# Finished finding groups we use
	
	
	
	materials =	[(sane_matname(mat), mat) for mat in materials.itervalues() if mat]
	textures =	[(sane_texname(img), img) for img in textures.itervalues()  if img]
	materials.sort() # sort by name
	textures.sort()
	
	camera_count = 8
	file.write('''

; Object definitions
;------------------------------------------------------------------

Definitions:  {
	Version: 100
	Count: %i''' % (\
		1+1+camera_count+\
		len(ob_meshes)+\
		len(ob_lights)+\
		len(ob_cameras)+\
		len(ob_arms)+\
		len(ob_null)+\
		len(ob_bones)+\
		bone_deformer_count+\
		len(materials)+\
		(len(textures)*2))) # add 1 for the root model 1 for global settings
	
	del bone_deformer_count
	
	file.write('''
	ObjectType: "Model" {
		Count: %i
	}''' % (\
		1+camera_count+\
		len(ob_meshes)+\
		len(ob_lights)+\
		len(ob_cameras)+\
		len(ob_arms)+\
		len(ob_null)+\
		len(ob_bones))) # add 1 for the root model
	
	file.write('''
	ObjectType: "Geometry" {
		Count: %i
	}''' % len(ob_meshes))
	
	if materials:
		file.write('''
	ObjectType: "Material" {
		Count: %i
	}''' % len(materials))
	
	if textures:
		file.write('''
	ObjectType: "Texture" {
		Count: %i
	}''' % len(textures)) # add 1 for an empty tex
		file.write('''
	ObjectType: "Video" {
		Count: %i
	}''' % len(textures)) # add 1 for an empty tex
	
	tmp = 0
	# Add deformer nodes
	for my_mesh in ob_meshes:
		if my_mesh.fbxArm:
			tmp+=1
	
	# Add subdeformers
	for my_bone in ob_bones:
		tmp += len(my_bone.blenMeshes)
	
	if tmp:
		file.write('''
	ObjectType: "Deformer" {
		Count: %i
	}''' % tmp)
	del tmp
	
	# we could avoid writing this possibly but for now just write it
	
	file.write('''
	ObjectType: "Pose" {
		Count: 1
	}''')
	
	if groups:
		file.write('''
	ObjectType: "GroupSelection" {
		Count: %i
	}''' % len(groups))
	
	file.write('''
	ObjectType: "GlobalSettings" {
		Count: 1
	}
}''')

	file.write('''

; Object properties
;------------------------------------------------------------------

Objects:  {''')
	
	# To comply with other FBX FILES
	write_camera_switch()
	
	# Write the null object
	write_null(None, 'blend_root')# , GLOBAL_MATRIX) 
	
	for my_null in ob_null:
		write_null(my_null)
	
	for my_arm in ob_arms:
		# Dont pass the object because that writes the armature transformation which is alredy applied to the bones.
		write_null(None, my_arm.fbxName) # armatures are just null's with bone children.
	
	for my_cam in ob_cameras:
		write_camera(my_cam)

	for my_light in ob_lights:
		write_light(my_light)
	
	for my_mesh in ob_meshes:
		write_mesh(my_mesh)

	#for bonename, bone, obname, me, armob in ob_bones:
	for my_bone in ob_bones:
		write_bone(my_bone)
	
	write_camera_default()
	
	for matname, mat in materials:
		write_material(matname, mat)
	
	# each texture uses a video, odd
	for texname, tex in textures:
		write_video(texname, tex)
	i = 0
	for texname, tex in textures:
		write_texture(texname, tex, i)
		i+=1
	
	for groupname, group in groups:
		write_group(groupname)
	
	# NOTE - c4d and motionbuilder dont need normalized weights, but deep-exploration 5 does and (max?) do.
	
	# Write armature modifiers
	# TODO - add another MODEL? - because of this skin definition.
	for my_mesh in ob_meshes:
		if my_mesh.fbxArm:
			write_deformer_skin(my_mesh.fbxName)
			
			# Get normalized weights for temorary use
			if my_mesh.fbxBoneParent:
				weights = None
			else:
				weights = meshNormalizedWeights(my_mesh.blenData)
			
			#for bonename, bone, obname, bone_mesh, armob in ob_bones:
			for my_bone in ob_bones:
				if me in my_bone.blenMeshes.itervalues():
					write_sub_deformer_skin(my_mesh, my_bone, weights)
	
	# Write pose's really weired, only needed when an armature and mesh are used together
	# each by themselves dont need pose data. for now only pose meshes and bones
	
	file.write('''
	Pose: "Pose::BIND_POSES", "BindPose" {
		Type: "BindPose"
		Version: 100
		Properties60:  {
		}
		NbPoseNodes: ''')
	file.write(str(len(pose_items)))
	

	for fbxName, matrix in pose_items:
		file.write('\n\t\tPoseNode:  {')
		file.write('\n\t\t\tNode: "Model::%s"' % fbxName )
		if matrix:		file.write('\n\t\t\tMatrix: %s' % mat4x4str(matrix))
		else:			file.write('\n\t\t\tMatrix: %s' % mat4x4str(mtx4_identity))
		file.write('\n\t\t}')
	
	file.write('\n\t}')
	
	
	# Finish Writing Objects
	# Write global settings
	file.write('''
	GlobalSettings:  {
		Version: 1000
		Properties60:  {
			Property: "UpAxis", "int", "",1
			Property: "UpAxisSign", "int", "",1
			Property: "FrontAxis", "int", "",2
			Property: "FrontAxisSign", "int", "",1
			Property: "CoordAxis", "int", "",0
			Property: "CoordAxisSign", "int", "",1
			Property: "UnitScaleFactor", "double", "",100
		}
	}
''')	
	file.write('}')
	
	file.write('''

; Object relations
;------------------------------------------------------------------

Relations:  {''')

	file.write('\n\tModel: "Model::blend_root", "Null" {\n\t}')

	for my_null in ob_null:
		file.write('\n\tModel: "Model::%s", "Null" {\n\t}' % my_null.fbxName)

	for my_arm in ob_arms:
		file.write('\n\tModel: "Model::%s", "Null" {\n\t}' % my_arm.fbxName)

	for my_mesh in ob_meshes:
		file.write('\n\tModel: "Model::%s", "Mesh" {\n\t}' % my_mesh.fbxName)

	# TODO - limbs can have the same name for multiple armatures, should prefix.
	#for bonename, bone, obname, me, armob in ob_bones:
	for my_bone in ob_bones:
		file.write('\n\tModel: "Model::%s", "Limb" {\n\t}' % my_bone.fbxName)
	
	for my_cam in ob_cameras:
		file.write('\n\tModel: "Model::%s", "Camera" {\n\t}' % my_cam.fbxName)
	
	for my_light in ob_lights:
		file.write('\n\tModel: "Model::%s", "Light" {\n\t}' % my_light.fbxName)
	
	file.write('''
	Model: "Model::Producer Perspective", "Camera" {
	}
	Model: "Model::Producer Top", "Camera" {
	}
	Model: "Model::Producer Bottom", "Camera" {
	}
	Model: "Model::Producer Front", "Camera" {
	}
	Model: "Model::Producer Back", "Camera" {
	}
	Model: "Model::Producer Right", "Camera" {
	}
	Model: "Model::Producer Left", "Camera" {
	}
	Model: "Model::Camera Switcher", "CameraSwitcher" {
	}''')
	
	for matname, mat in materials:
		file.write('\n\tMaterial: "Material::%s", "" {\n\t}' % matname)

	if textures:
		for texname, tex in textures:
			file.write('\n\tTexture: "Texture::%s", "TextureVideoClip" {\n\t}' % texname)
		for texname, tex in textures:
			file.write('\n\tVideo: "Video::%s", "Clip" {\n\t}' % texname)

	# deformers - modifiers
	for my_mesh in ob_meshes:
		if my_mesh.fbxArm:
			file.write('\n\tDeformer: "Deformer::Skin %s", "Skin" {\n\t}' % my_mesh.fbxName)
	
	#for bonename, bone, obname, me, armob in ob_bones:
	for my_bone in ob_bones:
		for fbxMeshObName in my_bone.blenMeshes: # .keys() - fbxMeshObName
			# is this bone effecting a mesh?
			file.write('\n\tDeformer: "SubDeformer::Cluster %s %s", "Cluster" {\n\t}' % (fbxMeshObName, my_bone.fbxName))
	
	# This should be at the end
	# file.write('\n\tPose: "Pose::BIND_POSES", "BindPose" {\n\t}')
	
	for groupname, group in groups:
		file.write('\n\tGroupSelection: "GroupSelection::%s", "Default" {\n\t}' % groupname)
	
	file.write('\n}')
	file.write('''

; Object connections
;------------------------------------------------------------------

Connections:  {''')
	
	# NOTE - The FBX SDK dosnt care about the order but some importers DO!
	# for instance, defining the material->mesh connection
	# before the mesh->blend_root crashes cinema4d
	

	# write the fake root node
	file.write('\n\tConnect: "OO", "Model::blend_root", "Model::Scene"')
	
	for my_null in ob_null:
		#if ob.parent:
		#	file.write('\n\tConnect: "OO", "Model::%s", "Model::%s"' % (obname, sane_name_mapping_ob[ob.parent.name]))
		#else:
		file.write('\n\tConnect: "OO", "Model::%s", "Model::blend_root"' % my_null.fbxName)

	for my_mesh in ob_meshes:
		file.write('\n\tConnect: "OO", "Model::%s", "Model::blend_root"' % my_mesh.fbxName)

	for my_arm in ob_arms:
		file.write('\n\tConnect: "OO", "Model::%s", "Model::blend_root"' % my_arm.fbxName)

	for my_cam in ob_cameras:
		file.write('\n\tConnect: "OO", "Model::%s", "Model::blend_root"' % my_cam.fbxName)
	
	for my_light in ob_lights:
		file.write('\n\tConnect: "OO", "Model::%s", "Model::blend_root"' % my_light.fbxName)
	
	if materials:
		for my_mesh in ob_meshes:
			# Connect all materials to all objects, not good form but ok for now.
			for mat in my_mesh.blenMaterials:
				if mat:
					file.write('\n\tConnect: "OO", "Material::%s", "Model::%s"' % (sane_name_mapping_mat[mat.name], my_mesh.fbxName))
			
	
	if textures:
		for my_mesh in ob_meshes:
			if my_mesh.blenTextures:
				# file.write('\n\tConnect: "OO", "Texture::_empty_", "Model::%s"' % my_mesh.fbxName)
				for tex in my_mesh.blenTextures:
					if tex:
						file.write('\n\tConnect: "OO", "Texture::%s", "Model::%s"' % (sane_name_mapping_tex[tex.name], my_mesh.fbxName))
		
		for texname, tex in textures:
			file.write('\n\tConnect: "OO", "Video::%s", "Texture::%s"' % (texname, texname))
	
	for my_mesh in ob_meshes:
		if my_mesh.fbxArm:
			file.write('\n\tConnect: "OO", "Deformer::Skin %s", "Model::%s"' % (my_mesh.fbxName, my_mesh.fbxName))
	
	#for bonename, bone, obname, me, armob in ob_bones:
	for my_bone in ob_bones:
		for fbxMeshObName in my_bone.blenMeshes: # .keys()
			file.write('\n\tConnect: "OO", "SubDeformer::Cluster %s %s", "Deformer::Skin %s"' % (fbxMeshObName, my_bone.fbxName, fbxMeshObName))
	
	# limbs -> deformers
	# for bonename, bone, obname, me, armob in ob_bones:
	for my_bone in ob_bones:
		for fbxMeshObName in my_bone.blenMeshes: # .keys()
			file.write('\n\tConnect: "OO", "Model::%s", "SubDeformer::Cluster %s %s"' % (my_bone.fbxName, fbxMeshObName, my_bone.fbxName))
	
	
	#for bonename, bone, obname, me, armob in ob_bones:
	for my_bone in ob_bones:
		# Always parent to armature now
		if my_bone.parent:
			file.write('\n\tConnect: "OO", "Model::%s", "Model::%s"' % (my_bone.fbxName, my_bone.parent.fbxName) )
		else:
			# the armature object is written as an empty and all root level bones connect to it
			file.write('\n\tConnect: "OO", "Model::%s", "Model::%s"' % (my_bone.fbxName, my_bone.fbxArm.fbxName) )
	
	# groups
	if groups:
		for ob_generic in (ob_meshes, ob_arms, ob_cameras, ob_lights, ob_null):
			for ob_base in ob_generic:
				for fbxGroupName in ob_base.fbxGroupNames:
					file.write('\n\tConnect: "OO", "Model::%s", "GroupSelection::%s"' % (ob_base.fbxName, fbxGroupName))
	
	for my_arm in ob_arms:
		file.write('\n\tConnect: "OO", "Model::%s", "Model::blend_root"' % my_arm.fbxName)
	
	file.write('\n}')
	
	
	# Needed for scene footer as well as animation
	render = sce.render
	
	# from the FBX sdk
	#define KTIME_ONE_SECOND        KTime (K_LONGLONG(46186158000))
	def fbx_time(t):
		# 0.5 + val is the same as rounding.
		return int(0.5 + ((t/fps) * 46186158000))
	
	fps = float(render.fps)	
	start =	render.sFrame
	end =	render.eFrame
	if end < start: start, end = end, start
	
	# animations for these object types
	ob_anim_lists = ob_bones, ob_meshes, ob_null, ob_cameras, ob_lights
	
	if ANIM_ENABLE and [tmp for tmp in ob_anim_lists if tmp]:
		
		frame_orig = Blender.Get('curframe')
		
		if ANIM_OPTIMIZE:
			ANIM_OPTIMIZE_PRECISSION_FLOAT = 0.1 ** ANIM_OPTIMIZE_PRECISSION
		
		# default action, when no actions are avaioable
		tmp_actions = [None] # None is the default action
		blenActionDefault = None
		action_lastcompat = None
		
		if ANIM_ACTION_ALL:
			bpy.data.actions.tag = False
			tmp_actions = list(bpy.data.actions)
			
			
			# find which actions are compatible with the armatures
			# blenActions is not yet initialized so do it now.
			tmp_act_count = 0
			for my_arm in ob_arms:
				
				# get the default name
				if not blenActionDefault:
					blenActionDefault = my_arm.blenAction
				
				arm_bone_names = set([my_bone.blenName for my_bone in my_arm.fbxBones])
				
				for action in tmp_actions:
					
					action_chan_names = arm_bone_names.intersection( set(action.getChannelNames()) )
					
					if action_chan_names: # at least one channel matches.
						my_arm.blenActionList.append(action)
						action.tag = True
						tmp_act_count += 1
						
						# incase there is no actions applied to armatures
						action_lastcompat = action
			
			if tmp_act_count:
				# unlikely to ever happen but if no actions applied to armatures, just use the last compatible armature.
				if not blenActionDefault:
					blenActionDefault = action_lastcompat
		
		del action_lastcompat
		
		file.write('''
;Takes and animation section
;----------------------------------------------------

Takes:  {''')
		
		if blenActionDefault:
			file.write('\n\tCurrent: "%s"' % sane_takename(blenActionDefault))
		else:
			file.write('\n\tCurrent: "Default Take"')
		
		for blenAction in tmp_actions:
			# we have tagged all actious that are used be selected armatures
			if blenAction:
				if blenAction.tag:
					print '\taction: "%s" exporting...' % blenAction.name
				else:
					print '\taction: "%s" has no armature using it, skipping' % blenAction.name
					continue
			
			if blenAction == None:
				# Warning, this only accounts for tmp_actions being [None]
				file.write('\n\tTake: "Default Take" {')
				act_start =	start
				act_end =	end
			else:
				# use existing name
				if blenAction == blenActionDefault: # have we alredy got the name
					file.write('\n\tTake: "%s" {' % sane_name_mapping_take[blenAction.name])
				else:
					file.write('\n\tTake: "%s" {' % sane_takename(blenAction))
					
				tmp = blenAction.getFrameNumbers()
				if tmp:
					act_start =	min(tmp)
					act_end =	max(tmp)
					del tmp
				else:
					# Fallback on this, theres not much else we can do? :/
					# when an action has no length
					act_start =	start
					act_end =	end
				
				# Set the action active
				for my_bone in ob_arms:
					if blenAction in my_bone.blenActionList:
						ob.action = blenAction
						# print '\t\tSetting Action!', blenAction
				# sce.update(1)
			
			file.write('\n\t\tFileName: "Default_Take.tak"') # ??? - not sure why this is needed
			file.write('\n\t\tLocalTime: %i,%i' % (fbx_time(act_start-1), fbx_time(act_end-1))) # ??? - not sure why this is needed
			file.write('\n\t\tReferenceTime: %i,%i' % (fbx_time(act_start-1), fbx_time(act_end-1))) # ??? - not sure why this is needed
			
			file.write('''

		;Models animation
		;----------------------------------------------------''')
			
			
			# set pose data for all bones
			# do this here incase the action changes
			'''
			for my_bone in ob_bones:
				my_bone.flushAnimData()
			'''
			i = act_start
			while i <= act_end:
				Blender.Set('curframe', i)
				for ob_generic in ob_anim_lists:
					for my_ob in ob_generic:
						#Blender.Window.RedrawAll()
						if ob_generic == ob_meshes and my_ob.fbxArm:
							# We cant animate armature meshes!
							pass
						else:
							my_ob.setPoseFrame(i)
						
				i+=1
			
			
			#for bonename, bone, obname, me, armob in ob_bones:
			for ob_generic in (ob_bones, ob_meshes, ob_null, ob_cameras, ob_lights):
					
				for my_ob in ob_generic:
					
					
					if ob_generic == ob_meshes and my_ob.fbxArm:
						# do nothing,
						pass
					else:
							
						file.write('\n\t\tModel: "Model::%s" {' % my_ob.fbxName) # ??? - not sure why this is needed
						file.write('\n\t\t\tVersion: 1.1')
						file.write('\n\t\t\tChannel: "Transform" {')
						
						context_bone_anim_mats = [ (my_ob.getAnimMatrix(frame), my_ob.getAnimMatrixRot(frame)) for frame in xrange(act_start, act_end+1) ]
						
						# ----------------
						# ----------------
						for TX_LAYER, TX_CHAN in enumerate('TRS'): # transform, rotate, scale
							
							if		TX_CHAN=='T':	context_bone_anim_vecs = [mtx[0].translationPart()	for mtx in context_bone_anim_mats]
							elif 	TX_CHAN=='R':	context_bone_anim_vecs = [mtx[1].toEuler()			for mtx in context_bone_anim_mats]
							else:					context_bone_anim_vecs = [mtx[0].scalePart()		for mtx in context_bone_anim_mats]
							
							file.write('\n\t\t\t\tChannel: "%s" {' % TX_CHAN) # translation
							
							for i in xrange(3):
								# Loop on each axis of the bone
								file.write('\n\t\t\t\t\tChannel: "%s" {'% ('XYZ'[i])) # translation
								file.write('\n\t\t\t\t\t\tDefault: %.15f' % context_bone_anim_vecs[0][i] )
								file.write('\n\t\t\t\t\t\tKeyVer: 4005')
								
								if not ANIM_OPTIMIZE:
									# Just write all frames, simple but in-eficient
									file.write('\n\t\t\t\t\t\tKeyCount: %i' % (1 + act_end - act_start))
									file.write('\n\t\t\t\t\t\tKey: ')
									frame = act_start
									while frame <= act_end:
										if frame!=act_start:
											file.write(',')
										
										# Curve types are 
										# C,n is for bezier? - linear is best for now so we can do simple keyframe removal
										file.write('\n\t\t\t\t\t\t\t%i,%.15f,C,n'  % (fbx_time(frame-1), context_bone_anim_vecs[frame-act_start][i] ))
										#file.write('\n\t\t\t\t\t\t\t%i,%.15f,L'  % (fbx_time(frame-1), context_bone_anim_vecs[frame-act_start][i] ))
										frame+=1
								else:
									# remove unneeded keys, j is the frame, needed when some frames are removed.
									context_bone_anim_keys = [ (vec[i], j) for j, vec in enumerate(context_bone_anim_vecs) ]
									
									# last frame to fisrt frame, missing 1 frame on either side.
									# removeing in a backwards loop is faster
									for j in xrange( (act_end-act_start)-1, 0, -1 ):
										# Is this key reduenant?
										if	abs(context_bone_anim_keys[j][0] - context_bone_anim_keys[j-1][0]) < ANIM_OPTIMIZE_PRECISSION_FLOAT and\
											abs(context_bone_anim_keys[j][0] - context_bone_anim_keys[j+1][0]) < ANIM_OPTIMIZE_PRECISSION_FLOAT:
											del context_bone_anim_keys[j]
									
									if len(context_bone_anim_keys) == 2 and context_bone_anim_keys[0][0] == context_bone_anim_keys[1][0]:
										# This axis has no moton, its okay to skip KeyCount and Keys in this case
										pass
									else:
										# We only need to write these if there is at least one 
										file.write('\n\t\t\t\t\t\tKeyCount: %i' % len(context_bone_anim_keys))
										file.write('\n\t\t\t\t\t\tKey: ')
										for val, frame in context_bone_anim_keys:
											if frame != context_bone_anim_keys[0][1]: # not the first
												file.write(',')
											# frame is alredy one less then blenders frame
											file.write('\n\t\t\t\t\t\t\t%i,%.15f,C,n'  % (fbx_time(frame), val ))
											#file.write('\n\t\t\t\t\t\t\t%i,%.15f,L'  % (fbx_time(frame), val ))
								
								if		i==0:	file.write('\n\t\t\t\t\t\tColor: 1,0,0')
								elif	i==1:	file.write('\n\t\t\t\t\t\tColor: 0,1,0')
								elif	i==2:	file.write('\n\t\t\t\t\t\tColor: 0,0,1')
								
								file.write('\n\t\t\t\t\t}')
							file.write('\n\t\t\t\t\tLayerType: %i' % (TX_LAYER+1) )
							file.write('\n\t\t\t\t}')
						
						# --------------- 
						
						file.write('\n\t\t\t}')
						file.write('\n\t\t}')
			
			# end the take
			file.write('\n\t}')
			
			# end action loop. set original actions 
			# do this after every loop incase actions effect eachother.
			for my_bone in ob_arms:
				my_bone.blenObject.action = my_bone.blenAction
		
		file.write('\n}')
		
		Blender.Set('curframe', frame_orig)
		
	else:
		# no animation
		file.write('\n;Takes and animation section')
		file.write('\n;----------------------------------------------------')
		file.write('\n')
		file.write('\nTakes:  {')
		file.write('\n\tCurrent: ""')
		file.write('\n}')
	
	
	# write meshes animation
	#for obname, ob, mtx, me, mats, arm, armname in ob_meshes:
		
	
	# Clear mesh data Only when writing with modifiers applied
	for me in meshes_to_clear:
		me.verts = None
	
	
	
	# --------------------------- Footer
	if world:
		has_mist = world.mode & 1
		mist_intense, mist_start, mist_end, mist_height = world.mist
		world_hor = world.hor
	else:
		has_mist = mist_intense = mist_start = mist_end = mist_height = 0
		world_hor = 0,0,0
	
	file.write('\n;Version 5 settings')
	file.write('\n;------------------------------------------------------------------')
	file.write('\n')
	file.write('\nVersion5:  {')
	file.write('\n\tAmbientRenderSettings:  {')
	file.write('\n\t\tVersion: 101')
	file.write('\n\t\tAmbientLightColor: %.1f,%.1f,%.1f,0' % tuple(world_amb))
	file.write('\n\t}')
	file.write('\n\tFogOptions:  {')
	file.write('\n\t\tFlogEnable: %i' % has_mist)
	file.write('\n\t\tFogMode: 0')
	file.write('\n\t\tFogDensity: %.3f' % mist_intense)
	file.write('\n\t\tFogStart: %.3f' % mist_start)
	file.write('\n\t\tFogEnd: %.3f' % mist_end)
	file.write('\n\t\tFogColor: %.1f,%.1f,%.1f,1' % tuple(world_hor))
	file.write('\n\t}')
	file.write('\n\tSettings:  {')
	file.write('\n\t\tFrameRate: "%i"' % int(fps))
	file.write('\n\t\tTimeFormat: 1')
	file.write('\n\t\tSnapOnFrames: 0')
	file.write('\n\t\tReferenceTimeIndex: -1')
	file.write('\n\t\tTimeLineStartTime: %i' % fbx_time(start-1))
	file.write('\n\t\tTimeLineStopTime: %i' % fbx_time(end-1))
	file.write('\n\t}')
	file.write('\n\tRendererSetting:  {')
	file.write('\n\t\tDefaultCamera: "Producer Perspective"')
	file.write('\n\t\tDefaultViewingMode: 0')
	file.write('\n\t}')
	file.write('\n}')
	file.write('\n')
	
	# Incase sombody imports this, clean up by clearing global dicts
	sane_name_mapping_ob.clear()
	sane_name_mapping_mat.clear()
	sane_name_mapping_tex.clear()
	
	ob_arms[:] =	[]
	ob_bones[:] =	[]
	ob_cameras[:] =	[]
	ob_lights[:] =	[]
	ob_meshes[:] =	[]
	ob_null[:] =	[]
	
	
	# copy images if enabled
	if EXP_IMAGE_COPY:
		copy_images( Blender.sys.dirname(filename),  [ tex[1] for tex in textures if tex[1] != None ])	
	
	print 'export finished in %.4f sec.' % (Blender.sys.time() - start_time)
	

# --------------------------------------------
# UI Function - not a part of the exporter.
# this is to seperate the user interface from the rest of the exporter.
from Blender import Draw, Window
EVENT_NONE = 0
EVENT_EXIT = 1
EVENT_REDRAW = 2
EVENT_FILESEL = 3

GLOBALS = {}

# export opts

def do_redraw(e,v):		GLOBALS['EVENT'] = e

# toggle between these 2, only allow one on at once
def do_obs_sel(e,v):
	GLOBALS['EVENT'] = e
	GLOBALS['EXP_OBS_SCENE'].val = 0
	GLOBALS['EXP_OBS_SELECTED'].val = 1

def do_obs_sce(e,v):
	GLOBALS['EVENT'] = e
	GLOBALS['EXP_OBS_SCENE'].val = 1
	GLOBALS['EXP_OBS_SELECTED'].val = 0

def do_obs_sce(e,v):
	GLOBALS['EVENT'] = e
	GLOBALS['EXP_OBS_SCENE'].val = 1
	GLOBALS['EXP_OBS_SELECTED'].val = 0

def do_batch_type_grp(e,v):
	GLOBALS['EVENT'] = e
	GLOBALS['BATCH_GROUP'].val = 1
	GLOBALS['BATCH_SCENE'].val = 0

def do_batch_type_sce(e,v):
	GLOBALS['EVENT'] = e
	GLOBALS['BATCH_GROUP'].val = 0
	GLOBALS['BATCH_SCENE'].val = 1

def do_anim_act_all(e,v):
	GLOBALS['EVENT'] = e
	GLOBALS['ANIM_ACTION_ALL'][0].val = 1
	GLOBALS['ANIM_ACTION_ALL'][1].val = 0

def do_anim_act_cur(e,v):
	if GLOBALS['BATCH_ENABLE'].val and GLOBALS['BATCH_GROUP'].val:
		Draw.PupMenu('Warning%t|Cant use this with batch export group option')
	else:
		GLOBALS['EVENT'] = e
		GLOBALS['ANIM_ACTION_ALL'][0].val = 0
		GLOBALS['ANIM_ACTION_ALL'][1].val = 1

def fbx_ui_exit(e,v):
	GLOBALS['EVENT'] = e

def do_help(e,v):
	url = 'http://wiki.blender.org/index.php/Scripts/Manual/Export/autodesk_fbx'
	print 'Trying to open web browser with documentation at this address...'
	print '\t' + url
	
	try:
		import webbrowser
		webbrowser.open(url)
	except:
		print '...could not open a browser window.'

	

# run when export is pressed
#def fbx_ui_write(e,v):
def fbx_ui_write(filename):
	
	# Dont allow overwriting files when saving normally
	if not GLOBALS['BATCH_ENABLE'].val:
		if not BPyMessages.Warning_SaveOver(filename):
			return
	
	GLOBALS['EVENT'] = EVENT_EXIT
	
	# Keep the order the same as above for simplicity
	# the [] is a dummy arg used for objects
	
	Blender.Window.WaitCursor(1)
	
	# Make the matrix
	GLOBAL_MATRIX = mtx4_identity
	GLOBAL_MATRIX[0][0] = GLOBAL_MATRIX[1][1] = GLOBAL_MATRIX[2][2] = GLOBALS['_SCALE'].val
	if GLOBALS['_XROT90'].val:	GLOBAL_MATRIX = GLOBAL_MATRIX * mtx4_x90n
	if GLOBALS['_YROT90'].val:	GLOBAL_MATRIX = GLOBAL_MATRIX * mtx4_y90n
	if GLOBALS['_ZROT90'].val:	GLOBAL_MATRIX = GLOBAL_MATRIX * mtx4_z90n
	
	write(\
		filename, None,\
		GLOBALS['EXP_OBS_SELECTED'].val,\
		GLOBALS['EXP_MESH'].val,\
		GLOBALS['EXP_MESH_APPLY_MOD'].val,\
		GLOBALS['EXP_MESH_HQ_NORMALS'].val,\
		GLOBALS['EXP_ARMATURE'].val,\
		GLOBALS['EXP_LAMP'].val,\
		GLOBALS['EXP_CAMERA'].val,\
		GLOBALS['EXP_EMPTY'].val,\
		GLOBALS['EXP_IMAGE_COPY'].val,\
		GLOBAL_MATRIX,\
		GLOBALS['ANIM_ENABLE'].val,\
		GLOBALS['ANIM_OPTIMIZE'].val,\
		GLOBALS['ANIM_OPTIMIZE_PRECISSION'].val,\
		GLOBALS['ANIM_ACTION_ALL'][0].val,\
		GLOBALS['BATCH_ENABLE'].val,\
		GLOBALS['BATCH_GROUP'].val,\
		GLOBALS['BATCH_SCENE'].val,\
		GLOBALS['BATCH_FILE_PREFIX'].val,\
		GLOBALS['BATCH_OWN_DIR'].val,\
	)
	
	Blender.Window.WaitCursor(0)
	GLOBALS.clear()


def fbx_ui():
	# Only to center the UI
	x,y = GLOBALS['MOUSE']
	x-=180; y-=0 # offset... just to get it centered
	
	Draw.Label('Export Objects...', x+20,y+165, 200, 20)
	
	if not GLOBALS['BATCH_ENABLE'].val:
		Draw.BeginAlign()
		GLOBALS['EXP_OBS_SELECTED'] =	Draw.Toggle('Selected Objects',	EVENT_REDRAW, x+20,  y+145, 160, 20, GLOBALS['EXP_OBS_SELECTED'].val,	'Export selected objects on visible layers', do_obs_sel)
		GLOBALS['EXP_OBS_SCENE'] =		Draw.Toggle('Scene Objects',	EVENT_REDRAW, x+180,  y+145, 160, 20, GLOBALS['EXP_OBS_SCENE'].val,		'Export all objects in this scene', do_obs_sce)
		Draw.EndAlign()
	
	Draw.BeginAlign()
	GLOBALS['_SCALE'] =		Draw.Number('Scale:',	EVENT_NONE, x+20, y+120, 140, 20, GLOBALS['_SCALE'].val,	0.01, 1000.0, 'Scale all data, (Note! some imports dont support scaled armatures)')
	GLOBALS['_XROT90'] =	Draw.Toggle('Rot X90',	EVENT_NONE, x+160, y+120, 60, 20, GLOBALS['_XROT90'].val,		'Rotate all objects 90 degrese about the X axis')
	GLOBALS['_YROT90'] =	Draw.Toggle('Rot Y90',	EVENT_NONE, x+220, y+120, 60, 20, GLOBALS['_YROT90'].val,		'Rotate all objects 90 degrese about the Y axis')
	GLOBALS['_ZROT90'] =	Draw.Toggle('Rot Z90',	EVENT_NONE, x+280, y+120, 60, 20, GLOBALS['_ZROT90'].val,		'Rotate all objects 90 degrese about the Z axis')
	Draw.EndAlign()
	
	y -= 35
	
	Draw.BeginAlign()
	GLOBALS['EXP_EMPTY'] =		Draw.Toggle('Empty',	EVENT_NONE, x+20, y+120, 60, 20, GLOBALS['EXP_EMPTY'].val,		'Export empty objects')
	GLOBALS['EXP_CAMERA'] =		Draw.Toggle('Camera',	EVENT_NONE, x+80, y+120, 60, 20, GLOBALS['EXP_CAMERA'].val,		'Export camera objects')
	GLOBALS['EXP_LAMP'] =		Draw.Toggle('Lamp',		EVENT_NONE, x+140, y+120, 60, 20, GLOBALS['EXP_LAMP'].val,		'Export lamp objects')
	GLOBALS['EXP_ARMATURE'] =	Draw.Toggle('Armature',	EVENT_NONE, x+200,  y+120, 60, 20, GLOBALS['EXP_ARMATURE'].val,	'Export armature objects')
	GLOBALS['EXP_MESH'] =		Draw.Toggle('Mesh',		EVENT_REDRAW, x+260,  y+120, 80, 20, GLOBALS['EXP_MESH'].val,	'Export mesh objects', do_redraw) #, do_axis_z)
	Draw.EndAlign()
	
	if GLOBALS['EXP_MESH'].val:
		# below mesh but
		Draw.BeginAlign()
		GLOBALS['EXP_MESH_APPLY_MOD'] =		Draw.Toggle('Modifiers',	EVENT_NONE, x+260,  y+100, 80, 20, GLOBALS['EXP_MESH_APPLY_MOD'].val,		'Apply modifiers to mesh objects') #, do_axis_z)
		GLOBALS['EXP_MESH_HQ_NORMALS'] =	Draw.Toggle('HQ Normals',		EVENT_NONE, x+260,  y+80, 80, 20, GLOBALS['EXP_MESH_HQ_NORMALS'].val,		'Generate high quality normals') #, do_axis_z)
		Draw.EndAlign()
	
	GLOBALS['EXP_IMAGE_COPY'] =		Draw.Toggle('Copy Image Files',	EVENT_NONE, x+20, y+80, 160, 20, GLOBALS['EXP_IMAGE_COPY'].val,		'Copy image files to the destination path') #, do_axis_z)
	
	
	Draw.Label('Export Armature Animation...', x+20,y+45, 300, 20)
	
	GLOBALS['ANIM_ENABLE'] =	Draw.Toggle('Enable Animation',		EVENT_REDRAW, x+20,  y+25, 160, 20, GLOBALS['ANIM_ENABLE'].val,		'Export keyframe animation', do_redraw)
	if GLOBALS['ANIM_ENABLE'].val:
		Draw.BeginAlign()
		GLOBALS['ANIM_OPTIMIZE'] =				Draw.Toggle('Optimize Keyframes',	EVENT_REDRAW, x+20,  y+0, 160, 20, GLOBALS['ANIM_OPTIMIZE'].val,	'Remove double keyframes', do_redraw)
		if GLOBALS['ANIM_OPTIMIZE'].val:
			GLOBALS['ANIM_OPTIMIZE_PRECISSION'] =	Draw.Number('Precission: ',			EVENT_NONE, x+180,  y+0, 160, 20, GLOBALS['ANIM_OPTIMIZE_PRECISSION'].val,	3, 16, 'Tolerence for comparing double keyframes (higher for greater accuracy)')
		Draw.EndAlign()
		
		Draw.BeginAlign()
		GLOBALS['ANIM_ACTION_ALL'][1] =	Draw.Toggle('Current Action',	EVENT_REDRAW, x+20, y-25, 160, 20, GLOBALS['ANIM_ACTION_ALL'][1].val,		'Use actions currently applied to the armatures (use scene start/end frame)', do_anim_act_cur)
		GLOBALS['ANIM_ACTION_ALL'][0] =		Draw.Toggle('All Actions',	EVENT_REDRAW, x+180,y-25, 160, 20, GLOBALS['ANIM_ACTION_ALL'][0].val,		'Use all actions for armatures', do_anim_act_all)
		Draw.EndAlign()
	
	
	Draw.Label('Export Batch...', x+20,y-60, 300, 20)
	GLOBALS['BATCH_ENABLE'] =	Draw.Toggle('Enable Batch',		EVENT_REDRAW, x+20,  y-80, 160, 20, GLOBALS['BATCH_ENABLE'].val,		'Automate exporting multiple scenes or groups to files', do_redraw)
	
	if GLOBALS['BATCH_ENABLE'].val:
		Draw.BeginAlign()
		GLOBALS['BATCH_GROUP'] =	Draw.Toggle('Group > File',	EVENT_REDRAW, x+20,  y-105, 160, 20, GLOBALS['BATCH_GROUP'].val,		'Export each group as an FBX file', do_batch_type_grp)
		GLOBALS['BATCH_SCENE'] =	Draw.Toggle('Scene > File',	EVENT_REDRAW, x+180,  y-105, 160, 20, GLOBALS['BATCH_SCENE'].val,	'Export each scene as an FBX file', do_batch_type_sce)
		
		# Own dir requires OS module
		if os:
			GLOBALS['BATCH_OWN_DIR'] =		Draw.Toggle('Own Dir',	EVENT_NONE, x+20,  y-125, 80, 20, GLOBALS['BATCH_OWN_DIR'].val,		'Create a dir for each exported file')
			GLOBALS['BATCH_FILE_PREFIX'] =	Draw.String('Prefix: ',	EVENT_NONE, x+100,  y-125, 240, 20, GLOBALS['BATCH_FILE_PREFIX'].val, 64,	'Prefix each file with this name ')
		else:
			GLOBALS['BATCH_FILE_PREFIX'] =	Draw.String('Prefix: ',	EVENT_NONE, x+20,  y-125, 320, 20, GLOBALS['BATCH_FILE_PREFIX'].val, 64,	'Prefix each file with this name ')
		
		
		Draw.EndAlign()

	#y+=80
		
	'''
	Draw.BeginAlign()
	GLOBALS['FILENAME'] =	Draw.String('path: ',	EVENT_NONE, x+20,  y-170, 300, 20, GLOBALS['FILENAME'].val, 64,	'Prefix each file with this name ')
	Draw.PushButton('..',	EVENT_FILESEL, x+320,  y-170, 20, 20,		'Select the path', do_redraw)
	'''
	# Until batch is added
	#
	
	
	#Draw.BeginAlign()
	Draw.PushButton('Online Help',	EVENT_REDRAW, x+20, y-160, 100, 20,	'Open online help in a browser window', do_help)
	Draw.PushButton('Cancel',		EVENT_EXIT, x+130, y-160, 100, 20,	'Exit the exporter', fbx_ui_exit)
	Draw.PushButton('Export',		EVENT_FILESEL, x+240, y-160, 100, 20,	'Export the fbx file', do_redraw)
	
	#Draw.PushButton('Export',	EVENT_EXIT, x+180, y-160, 160, 20,	'Export the fbx file', fbx_ui_write)
	#Draw.EndAlign()
	
	# exit when mouse out of the view?
	# GLOBALS['EVENT'] = EVENT_EXIT

#def write_ui(filename):
def write_ui():
	
	# globals
	GLOBALS['EVENT'] = 2
	#GLOBALS['MOUSE'] = Window.GetMouseCoords()
	GLOBALS['MOUSE'] = [i/2 for i in Window.GetScreenSize()]
	GLOBALS['FILENAME'] = ''
	'''
	# IF called from the fileselector
	if filename == None:
		GLOBALS['FILENAME'] = filename # Draw.Create(Blender.sys.makename(ext='.fbx'))
	else:
		GLOBALS['FILENAME'].val = filename
	'''
	GLOBALS['EXP_OBS_SELECTED'] =			Draw.Create(1) # dont need 2 variables but just do this for clarity
	GLOBALS['EXP_OBS_SCENE'] =				Draw.Create(0)

	GLOBALS['EXP_MESH'] =					Draw.Create(1)
	GLOBALS['EXP_MESH_APPLY_MOD'] =			Draw.Create(1)
	GLOBALS['EXP_MESH_HQ_NORMALS'] =		Draw.Create(0)
	GLOBALS['EXP_ARMATURE'] =				Draw.Create(1)
	GLOBALS['EXP_LAMP'] =					Draw.Create(1)
	GLOBALS['EXP_CAMERA'] =					Draw.Create(1)
	GLOBALS['EXP_EMPTY'] =					Draw.Create(1)
	GLOBALS['EXP_IMAGE_COPY'] =				Draw.Create(0)
	# animation opts
	GLOBALS['ANIM_ENABLE'] =				Draw.Create(1)
	GLOBALS['ANIM_OPTIMIZE'] =				Draw.Create(1)
	GLOBALS['ANIM_OPTIMIZE_PRECISSION'] =	Draw.Create(6) # decimal places
	GLOBALS['ANIM_ACTION_ALL'] =			[Draw.Create(0), Draw.Create(1)] # not just the current action
	
	# batch export options
	GLOBALS['BATCH_ENABLE'] =				Draw.Create(0)
	GLOBALS['BATCH_GROUP'] =				Draw.Create(1) # cant have both of these enabled at once.
	GLOBALS['BATCH_SCENE'] =				Draw.Create(0) # see above
	GLOBALS['BATCH_FILE_PREFIX'] =			Draw.Create(Blender.sys.makename(ext='_').split('\\')[-1].split('/')[-1])
	GLOBALS['BATCH_OWN_DIR'] =				Draw.Create(0)
	# done setting globals
	
	# Used by the user interface
	GLOBALS['_SCALE'] =						Draw.Create(1.0)
	GLOBALS['_XROT90'] =					Draw.Create(True)
	GLOBALS['_YROT90'] =					Draw.Create(False)
	GLOBALS['_ZROT90'] =					Draw.Create(False)
	
	# horrible ugly hack so tooltips draw, dosnt always work even
	# Fixed in Draw.UIBlock for 2.45rc2, but keep this until 2.45 is released
	Window.SetKeyQualifiers(0)
	while Window.GetMouseButtons(): Blender.sys.sleep(10)
	for i in xrange(100): Window.QHandle(i)
	# END HORRID HACK
	
	# best not do move the cursor
	# Window.SetMouseCoords(*[i/2 for i in Window.GetScreenSize()])
	
	# hack so the toggle buttons redraw. this is not nice at all
	while GLOBALS['EVENT'] != EVENT_EXIT:
		
		if GLOBALS['BATCH_ENABLE'].val and GLOBALS['BATCH_GROUP'].val and GLOBALS['ANIM_ACTION_ALL'][1].val:
			#Draw.PupMenu("Warning%t|Cant batch export groups with 'Current Action' ")
			GLOBALS['ANIM_ACTION_ALL'][0].val = 1
			GLOBALS['ANIM_ACTION_ALL'][1].val = 0
		
		if GLOBALS['EVENT'] == EVENT_FILESEL:
			if GLOBALS['BATCH_ENABLE'].val:
				txt = 'Batch FBX Dir'
				name = Blender.sys.expandpath('//')
			else:
				txt = 'Export FBX'
				name = Blender.sys.makename(ext='.fbx')
			
			Blender.Window.FileSelector(fbx_ui_write, txt, name)
			break
		
		Draw.UIBlock(fbx_ui)
	
	
	# GLOBALS.clear()
#test = [write_ui]
if __name__ == '__main__':
	# Cant call the file selector first because of a bug in the interface that crashes it.
	# Blender.Window.FileSelector(write_ui, 'Export FBX', Blender.sys.makename(ext='.fbx'))
	#write('/scratch/test.fbx')
	#write_ui('/scratch/test.fbx')
	
	if not set:
		Draw.PupMenu('Error%t|A full install of python2.3 or python 2.4+ is needed to run this script.')
	else:
		write_ui()
