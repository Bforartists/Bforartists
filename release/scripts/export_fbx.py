#!BPY
"""
Name: 'Autodesk FBX (.fbx)...'
Blender: 243
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

import Blender
import BPyObject
import BPyMesh
import BPySys
import BPyMessages
import time
from math import degrees
# Used to add the scene name into the filename without using odd chars
sane_name_mapping_ob = {}
sane_name_mapping_mat = {}
sane_name_mapping_tex = {}
sane_name_mapping_arm = {}

# Copied from CVS bpyObject
def getObjectArmature(ob):
	'''
	This returns the first armature the mesh uses.
	remember there can be more then 1 armature but most people dont do that.
	'''
	arm = ob.parent
	if arm and arm.type == 'Armature' and ob.parentType == Blender.Object.ParentTypes.ARMATURE:
		arm
	
	for m in ob.modifiers:
		if m.type== Blender.Modifier.Types.ARMATURE:
			arm = m[Blender.Modifier.Settings.OBJECT]
			if arm:
				return arm
	
	return None

BPyObject.getObjectArmature = getObjectArmature



def strip_path(p):
	return p.split('\\')[-1].split('/')[-1]

def sane_name(data, dct):
	if not data: return None
	name = data.name
	try:		return dct[name]
	except:		pass
	
	orig_name = name
	name = BPySys.cleanName(name)
	dct[orig_name] = name
	return name

def sane_obname(data):
	return sane_name(data, sane_name_mapping_ob)

def sane_matname(data):
	return sane_name(data, sane_name_mapping_mat)

def sane_texname(data):
	return sane_name(data, sane_name_mapping_tex)

def sane_armname(data):
	return sane_name(data, sane_name_mapping_arm)

# May use this later
"""
# Auto class, use for datastorage only, a like a dictionary but with limited slots
def auto_class(slots):
	exec('class container_class(object): __slots__=%s' % slots)
	return container_class
"""


header_comment = \
'''; FBX 6.1.0 project file
; Created by Blender FBX Exporter
; for support mail cbarton@metavr.com
; ----------------------------------------------------

'''

def write_header(file):
	file.write(header_comment)
	curtime = time.localtime()[0:6]
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
}
''' % (curtime))
	
	file.write('CreationTime: "%.4i-%.2i-%.2i %.2i:%.2i:%.2i:000"\n' % curtime)
	file.write('Creator: "Blender3D version %.2f"\n' % Blender.Get('version'))




def write_scene(file, sce, world):
	
	def write_camera_switch():
		file.write('''
	Model: "Model::Camera Switcher", "CameraSwitcher" {
		Version: 232
		Properties60:  {
			Property: "QuaternionInterpolate", "bool", "",0
			Property: "Visibility", "Visibility", "A+",0
			Property: "Lcl Translation", "Lcl Translation", "A+",0,0,0
			Property: "Lcl Rotation", "Lcl Rotation", "A+",0,0,0
			Property: "Lcl Scaling", "Lcl Scaling", "A+",1,1,1
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
			Property: "Show", "bool", "",0
			Property: "NegativePercentShapeSupport", "bool", "",1
			Property: "DefaultAttributeIndex", "int", "",0
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
	
	def write_camera(name, loc, near, far, proj_type, up):
		file.write('\n\tModel: "Model::%s", "Camera" {\n' % name )
		file.write('\t\tVersion: 232\n')
		file.write('\t\tProperties60:  {\n')
		file.write('\t\t\tProperty: "QuaternionInterpolate", "bool", "",0\n')
		file.write('\t\t\tProperty: "Visibility", "Visibility", "A+",0\n')
		file.write('\t\t\tProperty: "Lcl Translation", "Lcl Translation", "A+",%.6f,%.6f,%.6f\n' % loc)
		file.write('\t\t\tProperty: "Lcl Rotation", "Lcl Rotation", "A+",0,0,0\n')
		file.write('\t\t\tProperty: "Lcl Scaling", "Lcl Scaling", "A+",1,1,1\n')
		file.write('\t\t\tProperty: "RotationOffset", "Vector3D", "",0,0,0\n')
		file.write('\t\t\tProperty: "RotationPivot", "Vector3D", "",0,0,0\n')
		file.write('\t\t\tProperty: "ScalingOffset", "Vector3D", "",0,0,0\n')
		file.write('\t\t\tProperty: "ScalingPivot", "Vector3D", "",0,0,0\n')
		file.write('\t\t\tProperty: "TranslationActive", "bool", "",0\n')
		file.write('\t\t\tProperty: "TranslationMin", "Vector3D", "",0,0,0\n')
		file.write('\t\t\tProperty: "TranslationMax", "Vector3D", "",0,0,0\n')
		file.write('\t\t\tProperty: "TranslationMinX", "bool", "",0\n')
		file.write('\t\t\tProperty: "TranslationMinY", "bool", "",0\n')
		file.write('\t\t\tProperty: "TranslationMinZ", "bool", "",0\n')
		file.write('\t\t\tProperty: "TranslationMaxX", "bool", "",0\n')
		file.write('\t\t\tProperty: "TranslationMaxY", "bool", "",0\n')
		file.write('\t\t\tProperty: "TranslationMaxZ", "bool", "",0\n')
		file.write('\t\t\tProperty: "RotationOrder", "enum", "",0\n')
		file.write('\t\t\tProperty: "RotationSpaceForLimitOnly", "bool", "",0\n')
		file.write('\t\t\tProperty: "AxisLen", "double", "",10\n')
		file.write('\t\t\tProperty: "PreRotation", "Vector3D", "",0,0,0\n')
		file.write('\t\t\tProperty: "PostRotation", "Vector3D", "",0,0,0\n')
		file.write('\t\t\tProperty: "RotationActive", "bool", "",0\n')
		file.write('\t\t\tProperty: "RotationMin", "Vector3D", "",0,0,0\n')
		file.write('\t\t\tProperty: "RotationMax", "Vector3D", "",0,0,0\n')
		file.write('\t\t\tProperty: "RotationMinX", "bool", "",0\n')
		file.write('\t\t\tProperty: "RotationMinY", "bool", "",0\n')
		file.write('\t\t\tProperty: "RotationMinZ", "bool", "",0\n')
		file.write('\t\t\tProperty: "RotationMaxX", "bool", "",0\n')
		file.write('\t\t\tProperty: "RotationMaxY", "bool", "",0\n')
		file.write('\t\t\tProperty: "RotationMaxZ", "bool", "",0\n')
		file.write('\t\t\tProperty: "RotationStiffnessX", "double", "",0\n')
		file.write('\t\t\tProperty: "RotationStiffnessY", "double", "",0\n')
		file.write('\t\t\tProperty: "RotationStiffnessZ", "double", "",0\n')
		file.write('\t\t\tProperty: "MinDampRangeX", "double", "",0\n')
		file.write('\t\t\tProperty: "MinDampRangeY", "double", "",0\n')
		file.write('\t\t\tProperty: "MinDampRangeZ", "double", "",0\n')
		file.write('\t\t\tProperty: "MaxDampRangeX", "double", "",0\n')
		file.write('\t\t\tProperty: "MaxDampRangeY", "double", "",0\n')
		file.write('\t\t\tProperty: "MaxDampRangeZ", "double", "",0\n')
		file.write('\t\t\tProperty: "MinDampStrengthX", "double", "",0\n')
		file.write('\t\t\tProperty: "MinDampStrengthY", "double", "",0\n')
		file.write('\t\t\tProperty: "MinDampStrengthZ", "double", "",0\n')
		file.write('\t\t\tProperty: "MaxDampStrengthX", "double", "",0\n')
		file.write('\t\t\tProperty: "MaxDampStrengthY", "double", "",0\n')
		file.write('\t\t\tProperty: "MaxDampStrengthZ", "double", "",0\n')
		file.write('\t\t\tProperty: "PreferedAngleX", "double", "",0\n')
		file.write('\t\t\tProperty: "PreferedAngleY", "double", "",0\n')
		file.write('\t\t\tProperty: "PreferedAngleZ", "double", "",0\n')
		file.write('\t\t\tProperty: "InheritType", "enum", "",0\n')
		file.write('\t\t\tProperty: "ScalingActive", "bool", "",0\n')
		file.write('\t\t\tProperty: "ScalingMin", "Vector3D", "",1,1,1\n')
		file.write('\t\t\tProperty: "ScalingMax", "Vector3D", "",1,1,1\n')
		file.write('\t\t\tProperty: "ScalingMinX", "bool", "",0\n')
		file.write('\t\t\tProperty: "ScalingMinY", "bool", "",0\n')
		file.write('\t\t\tProperty: "ScalingMinZ", "bool", "",0\n')
		file.write('\t\t\tProperty: "ScalingMaxX", "bool", "",0\n')
		file.write('\t\t\tProperty: "ScalingMaxY", "bool", "",0\n')
		file.write('\t\t\tProperty: "ScalingMaxZ", "bool", "",0\n')
		file.write('\t\t\tProperty: "GeometricTranslation", "Vector3D", "",0,0,0\n')
		file.write('\t\t\tProperty: "GeometricRotation", "Vector3D", "",0,0,0\n')
		file.write('\t\t\tProperty: "GeometricScaling", "Vector3D", "",1,1,1\n')
		file.write('\t\t\tProperty: "LookAtProperty", "object", ""\n')
		file.write('\t\t\tProperty: "UpVectorProperty", "object", ""\n')
		file.write('\t\t\tProperty: "Show", "bool", "",0\n')
		file.write('\t\t\tProperty: "NegativePercentShapeSupport", "bool", "",1\n')
		file.write('\t\t\tProperty: "DefaultAttributeIndex", "int", "",0\n')
		file.write('\t\t\tProperty: "Color", "Color", "A",0.8,0.8,0.8\n')
		file.write('\t\t\tProperty: "Roll", "Roll", "A+",0\n')
		file.write('\t\t\tProperty: "FieldOfView", "FieldOfView", "A+",40\n')
		file.write('\t\t\tProperty: "FieldOfViewX", "FieldOfView", "A+",1\n')
		file.write('\t\t\tProperty: "FieldOfViewY", "FieldOfView", "A+",1\n')
		file.write('\t\t\tProperty: "OpticalCenterX", "Real", "A+",0\n')
		file.write('\t\t\tProperty: "OpticalCenterY", "Real", "A+",0\n')
		file.write('\t\t\tProperty: "BackgroundColor", "Color", "A+",0.63,0.63,0.63\n')
		file.write('\t\t\tProperty: "TurnTable", "Real", "A+",0\n')
		file.write('\t\t\tProperty: "DisplayTurnTableIcon", "bool", "",1\n')
		file.write('\t\t\tProperty: "Motion Blur Intensity", "Real", "A+",1\n')
		file.write('\t\t\tProperty: "UseMotionBlur", "bool", "",0\n')
		file.write('\t\t\tProperty: "UseRealTimeMotionBlur", "bool", "",1\n')
		file.write('\t\t\tProperty: "ResolutionMode", "enum", "",0\n')
		file.write('\t\t\tProperty: "ApertureMode", "enum", "",2\n')
		file.write('\t\t\tProperty: "GateFit", "enum", "",0\n')
		file.write('\t\t\tProperty: "FocalLength", "Real", "A+",21.3544940948486\n')
		file.write('\t\t\tProperty: "CameraFormat", "enum", "",0\n')
		file.write('\t\t\tProperty: "AspectW", "double", "",320\n')
		file.write('\t\t\tProperty: "AspectH", "double", "",200\n')
		file.write('\t\t\tProperty: "PixelAspectRatio", "double", "",1\n')
		file.write('\t\t\tProperty: "UseFrameColor", "bool", "",0\n')
		file.write('\t\t\tProperty: "FrameColor", "ColorRGB", "",0.3,0.3,0.3\n')
		file.write('\t\t\tProperty: "ShowName", "bool", "",1\n')
		file.write('\t\t\tProperty: "ShowGrid", "bool", "",1\n')
		file.write('\t\t\tProperty: "ShowOpticalCenter", "bool", "",0\n')
		file.write('\t\t\tProperty: "ShowAzimut", "bool", "",1\n')
		file.write('\t\t\tProperty: "ShowTimeCode", "bool", "",0\n')
		file.write('\t\t\tProperty: "NearPlane", "double", "",%.6f\n' % near)
		file.write('\t\t\tProperty: "FarPlane", "double", "",%.6f\n' % far)
		file.write('\t\t\tProperty: "FilmWidth", "double", "",0.816\n')
		file.write('\t\t\tProperty: "FilmHeight", "double", "",0.612\n')
		file.write('\t\t\tProperty: "FilmAspectRatio", "double", "",1.33333333333333\n')
		file.write('\t\t\tProperty: "FilmSqueezeRatio", "double", "",1\n')
		file.write('\t\t\tProperty: "FilmFormatIndex", "enum", "",4\n')
		file.write('\t\t\tProperty: "ViewFrustum", "bool", "",1\n')
		file.write('\t\t\tProperty: "ViewFrustumNearFarPlane", "bool", "",0\n')
		file.write('\t\t\tProperty: "ViewFrustumBackPlaneMode", "enum", "",2\n')
		file.write('\t\t\tProperty: "BackPlaneDistance", "double", "",100\n')
		file.write('\t\t\tProperty: "BackPlaneDistanceMode", "enum", "",0\n')
		file.write('\t\t\tProperty: "ViewCameraToLookAt", "bool", "",1\n')
		file.write('\t\t\tProperty: "LockMode", "bool", "",0\n')
		file.write('\t\t\tProperty: "LockInterestNavigation", "bool", "",0\n')
		file.write('\t\t\tProperty: "FitImage", "bool", "",0\n')
		file.write('\t\t\tProperty: "Crop", "bool", "",0\n')
		file.write('\t\t\tProperty: "Center", "bool", "",1\n')
		file.write('\t\t\tProperty: "KeepRatio", "bool", "",1\n')
		file.write('\t\t\tProperty: "BackgroundMode", "enum", "",0\n')
		file.write('\t\t\tProperty: "BackgroundAlphaTreshold", "double", "",0.5\n')
		file.write('\t\t\tProperty: "ForegroundTransparent", "bool", "",1\n')
		file.write('\t\t\tProperty: "DisplaySafeArea", "bool", "",0\n')
		file.write('\t\t\tProperty: "SafeAreaDisplayStyle", "enum", "",1\n')
		file.write('\t\t\tProperty: "SafeAreaAspectRatio", "double", "",1.33333333333333\n')
		file.write('\t\t\tProperty: "Use2DMagnifierZoom", "bool", "",0\n')
		file.write('\t\t\tProperty: "2D Magnifier Zoom", "Real", "A+",100\n')
		file.write('\t\t\tProperty: "2D Magnifier X", "Real", "A+",50\n')
		file.write('\t\t\tProperty: "2D Magnifier Y", "Real", "A+",50\n')
		file.write('\t\t\tProperty: "CameraProjectionType", "enum", "",%i\n' % proj_type)
		file.write('\t\t\tProperty: "UseRealTimeDOFAndAA", "bool", "",0\n')
		file.write('\t\t\tProperty: "UseDepthOfField", "bool", "",0\n')
		file.write('\t\t\tProperty: "FocusSource", "enum", "",0\n')
		file.write('\t\t\tProperty: "FocusAngle", "double", "",3.5\n')
		file.write('\t\t\tProperty: "FocusDistance", "double", "",200\n')
		file.write('\t\t\tProperty: "UseAntialiasing", "bool", "",0\n')
		file.write('\t\t\tProperty: "AntialiasingIntensity", "double", "",0.77777\n')
		file.write('\t\t\tProperty: "UseAccumulationBuffer", "bool", "",0\n')
		file.write('\t\t\tProperty: "FrameSamplingCount", "int", "",7\n')
		file.write('\t\t}\n')
		file.write('\t\tMultiLayer: 0\n')
		file.write('\t\tMultiTake: 0\n')
		file.write('\t\tHidden: "True"\n')
		file.write('\t\tShading: Y\n')
		file.write('\t\tCulling: "CullingOff"\n')
		file.write('\t\tTypeFlags: "Camera"\n')
		file.write('\t\tGeometryVersion: 124\n')
		file.write('\t\tPosition: 0,71.3,287.5\n')
		file.write('\t\tUp: %i,%i,%i\n' % up)
		file.write('\t\tLookAt: 0,0,0\n')
		file.write('\t\tShowInfoOnMoving: 1\n')
		file.write('\t\tShowAudio: 0\n')
		file.write('\t\tAudioColor: 0,1,0\n')
		file.write('\t\tCameraOrthoZoom: 1\n')
		file.write('\t}\n')
	
	def write_camera_default():
		# This sucks but to match FBX converter its easier to
		# write the cameras though they are not needed.
		write_camera('Producer Perspective', (0,71.3,287.5), 10, 4000, 0, (0,1,0))
		write_camera('Producer Top', (0,4000,0), 1, 30000, 1, (0,0,-1))
		write_camera('Producer Bottom', (0,-4000,0), 1, 30000, 1, (0,0,-1))
		write_camera('Producer Front', (0,0,4000), 1, 30000, 1, (0,1,0))
		write_camera('Producer Back', (0,0,-4000), 1, 30000, 1, (0,1,0))
		write_camera('Producer Right', (4000,0,0), 1, 30000, 1, (0,1,0))
		write_camera('Producer Left', (-4000,0,0), 1, 30000, 1, (0,1,0))
	
	def write_object_props(ob):
		# if the type is 0 its an empty otherwise its a mesh
		# only difference at the moment is one has a color
		file.write('''
		Properties60:  {
			Property: "QuaternionInterpolate", "bool", "",0
			Property: "Visibility", "Visibility", "A+",1''')
		
		if ob:
			file.write('\n\t\t\tProperty: "Lcl Translation", "Lcl Translation", "A+",%.15f,%.15f,%.15f' % tuple(ob.getLocation('worldspace')))
			file.write('\n\t\t\tProperty: "Lcl Rotation", "Lcl Rotation", "A+",%.15f,%.15f,%.15f' % tuple([degrees(a) for a in ob.getEuler('worldspace')]))
			file.write('\n\t\t\tProperty: "Lcl Scaling", "Lcl Scaling", "A+",%.15f,%.15f,%.15f' % tuple(ob.getSize('worldspace')))
		else:
			file.write('''
			Property: "Lcl Translation", "Lcl Translation", "A+",0,0,0
			Property: "Lcl Rotation", "Lcl Rotation", "A+",0,0,0
			Property: "Lcl Scaling", "Lcl Scaling", "A+",1,1,1''')
		
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
		if ob:
			# Only mesh objects have color 
			file.write('\n\t\t\tProperty: "Color", "Color", "A",0.8,0.8,0.8')
			file.write('\n\t\t\tProperty: "Size", "double", "",100')
			file.write('\n\t\t\tProperty: "Look", "enum", "",1')
		
		file.write('\n\t\t}\n')
	
	
	
	# Material Settings
	if world:
		world_amb = world.getAmb()
	else:
		world_amb = (0,0,0) # Default value
	
	
	def write_material(matname, mat):
		file.write('\n\tMaterial: "Material::%s", "" {' % matname)
		
		# Todo, add more material Properties.
		if mat:
			mat_cold = tuple(mat.rgbCol)
			mat_cols = tuple(mat.specCol)
			#mat_colm = tuple(mat.mirCol)
			mat_colamb = tuple([c for c in world_amb])
			
			mat_dif = mat.ref
			mat_amb = mat.amb
			mat_hard = (float(mat.hard)-1)/5.10
			mat_spec = mat.spec/2.0
			mat_alpha = mat.alpha
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
			mat_shadeless = False
			mat_shader = 'Phong'
		
		file.write('\n\t\tVersion: 102\n')
		file.write('\t\tShadingModel: "%s"\n' % mat_shader.lower())
		file.write('\t\tMultiLayer: 0\n')
		file.write('\t\tProperties60:  {\n')
		file.write('\t\t\tProperty: "ShadingModel", "KString", "", "%s"\n' % mat_shader)
		file.write('\t\t\tProperty: "MultiLayer", "bool", "",0\n')
		file.write('\t\t\tProperty: "EmissiveColor", "ColorRGB", "",0,0,0\n')
		file.write('\t\t\tProperty: "EmissiveFactor", "double", "",1\n')
		
		file.write('\t\t\tProperty: "AmbientColor", "ColorRGB", "",%.1f,%.1f,%.1f\n' % mat_colamb)
		file.write('\t\t\tProperty: "AmbientFactor", "double", "",%.1f\n' % mat_amb)
		file.write('\t\t\tProperty: "DiffuseColor", "ColorRGB", "",%.1f,%.1f,%.1f\n' % mat_cold)
		file.write('\t\t\tProperty: "DiffuseFactor", "double", "",%.1f\n' % mat_dif)
		file.write('\t\t\tProperty: "Bump", "Vector3D", "",0,0,0\n')
		file.write('\t\t\tProperty: "TransparentColor", "ColorRGB", "",1,1,1\n')
		file.write('\t\t\tProperty: "TransparencyFactor", "double", "",0\n')
		if not mat_shadeless:
			file.write('\t\t\tProperty: "SpecularColor", "ColorRGB", "",%.1f,%.1f,%.1f\n' % mat_cols)
			file.write('\t\t\tProperty: "SpecularFactor", "double", "",%.1f\n' % mat_spec)
			file.write('\t\t\tProperty: "ShininessExponent", "double", "",80.0\n')
			file.write('\t\t\tProperty: "ReflectionColor", "ColorRGB", "",0,0,0\n')
			file.write('\t\t\tProperty: "ReflectionFactor", "double", "",1\n')
		file.write('\t\t\tProperty: "Emissive", "Vector3D", "",0,0,0\n')
		file.write('\t\t\tProperty: "Ambient", "Vector3D", "",%.1f,%.1f,%.1f\n' % mat_colamb)
		file.write('\t\t\tProperty: "Diffuse", "Vector3D", "",%.1f,%.1f,%.1f\n' % mat_cold)
		if not mat_shadeless:
			file.write('\t\t\tProperty: "Specular", "Vector3D", "",%.1f,%.1f,%.1f\n' % mat_cols)
			file.write('\t\t\tProperty: "Shininess", "double", "",%.1f\n' % mat_hard)
		file.write('\t\t\tProperty: "Opacity", "double", "",%.1f\n' % mat_alpha)
		if not mat_shadeless:
			file.write('\t\t\tProperty: "Reflectivity", "double", "",0\n')

		file.write('\t\t}\n')
		file.write('\t}')
	
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
		file.write('''
			Property: "TextureTypeUse", "enum", "",0
			Property: "CurrentTextureBlendMode", "enum", "",1
			Property: "UseMaterial", "bool", "",0
			Property: "UseMipMap", "bool", "",0
			Property: "CurrentMappingType", "enum", "",0
			Property: "UVSwap", "bool", "",0
			Property: "WrapModeU", "enum", "",0
			Property: "WrapModeV", "enum", "",0
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
	
	objects = []
	materials = {}
	textures = {}
	armatures = [] # We should export standalone armatures also
	armatures_totbones = 0 # we need this because each bone is a model
	for ob in sce.objects.context:
		if ob.type == 'Mesh':	me = ob.getData(mesh=1)
		else:					me = BPyMesh.getMeshFromObject(ob)
		
		if me:
			mats = me.materials
			for mat in mats:
				# 2.44 use mat.lib too for uniqueness
				if mat: materials[mat.name] = mat
			
			if me.faceUV:
				uvlayer_orig = me.activeUVLayer
				for uvlayer in me.getUVLayerNames():
					me.activeUVLayer = uvlayer
					for f in me.faces:
						img = f.image
						if img: textures[img.name] = img
					
					me.activeUVLayer = uvlayer_orig
			
			arm = BPyObject.getObjectArmature(ob)
			
			if arm:
				armname = sane_armname(arm)
				bones = arm.bones.values()
				armatures_totbones += len(bones)
				armatures.append((arm, armname, bones))
			else:
				armname = None
			
			#### me.transform(ob.matrixWorld) # Export real ob coords.
			#### High Quality, not realy needed for now.
			#BPyMesh.meshCalcNormals(me) # high quality normals nice for realtime engines.
			objects.append( (sane_obname(ob), ob, me, mats, arm, armname) )
	
	materials = [(sane_matname(mat), mat) for mat in materials.itervalues()]
	textures = [(sane_texname(img), img) for img in textures.itervalues()]
	materials.sort() # sort by name
	textures.sort()
	
	if not materials:
		materials = [('null', None)]
	
	material_mapping = {} # blen name : index
	if textures:
		texture_mapping_local = {None:0} # ditto
		i = 0
		for texname, tex in textures:
			texture_mapping_local[tex.name] = i
			i+=1
		textures.insert(0, ('_empty_', None))
	
	i = 0
	for matname, mat in materials:
		if mat: mat = mat.name
		material_mapping[mat] = i
		i+=1

	camera_count = 8
	file.write(\
'''
; Object definitions
;------------------------------------------------------------------

Definitions:  {
	Version: 100
	Count: %i''' % (1+1+camera_count+len(objects)+len(armatures)+armatures_totbones+len(materials)+(len(textures)*2))) # add 1 for the root model 1 for global settings
	
	file.write('''
	ObjectType: "Model" {
		Count: %i
	}''' % (1+camera_count+len(objects)+len(armatures)+armatures_totbones)) # add 1 for the root model
	
	file.write('''
	ObjectType: "Geometry" {
		Count: %i
	}''' % len(objects))
	
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
	
	file.write('''
	ObjectType: "GlobalSettings" {
		Count: 1
	}
}
''')
	
	file.write(\
'''
; Object properties
;------------------------------------------------------------------

Objects:  {''')
	
	# To comply with other FBX FILES
	write_camera_switch()
	
	# Write the null object
	file.write('''
	Model: "Model::blend_root", "Null" {
		Version: 232''')
	write_object_props(None)
	file.write(\
'''		MultiLayer: 0
		MultiTake: 1
		Shading: Y
		Culling: "CullingOff"
		TypeFlags: "Null"
	}''')

	
	for obname, ob, me, mats, arm, armname in objects:
		file.write('\n\tModel: "Model::%s", "Mesh" {\n' % sane_obname(ob))
		file.write('\t\tVersion: 232') # newline is added in write_object_props
		write_object_props(ob)
		
		file.write('\t\tMultiLayer: 0\n')
		file.write('\t\tMultiTake: 1\n')
		file.write('\t\tShading: Y\n')
		file.write('\t\tCulling: "CullingOff"')
		
		# Write the Real Mesh data here
		file.write('\n\t\tVertices: ')
		i=-1
		for v in me.verts:
			if i==-1:
				file.write('%.6f,%.6f,%.6f' % tuple(v.co))
				i=0
			else:
				if i==7:
					file.write('\n		')
					i=0
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
					file.write('\n		')
					i=0
				if len(f) == 3:		file.write(',%i,%i,%i' % fi )
				else:				file.write(',%i,%i,%i,%i' % fi )
			i+=1
		
		file.write('\n\t\tGeometryVersion: 124')
		
		file.write('''
		LayerElementNormal: 0 {
			Version: 101
			Name: ""
			MappingInformationType: "ByVertice"
			ReferenceInformationType: "Direct"
			Normals: ''')

		i=-1
		for v in me.verts:
			if i==-1:
				file.write('%.15f,%.15f,%.15f' % tuple(v.no))
				i=0
			else:
				if i==2:
					file.write('\n			 ')
					i=0
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
								file.write('\n			 ')
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
							file.write('\n			 ')
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
				
				if textures:
					file.write('\n\t\tLayerElementTexture: %i {' % uvindex)
					file.write('\n\t\t\tVersion: 101')
					file.write('\n\t\t\tName: "%s"' % uvlayer)
					
					file.write('''
			MappingInformationType: "ByPolygon"
			ReferenceInformationType: "IndexToDirect"
			BlendMode: "Translucent"
			TextureAlpha: 1
			TextureId: ''')
					i=-1
					for f in me.faces:
						img_key = f.image
						if img_key: img_key = img_key.name
						
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
		
		if materials:
			file.write('''
		LayerElementMaterial: 0 {
			Version: 101
			Name: ""
			MappingInformationType: "ByPolygon"
			ReferenceInformationType: "IndexToDirect"
			Materials: ''')
			
			# Build a material mapping for this 
			material_mapping_local = {} # local-index : global index.
			for i, mat in enumerate(mats):
				if mat:
					material_mapping_local[i] = material_mapping[mat.name]
				else:
					material_mapping_local[i] = 0 # None material is zero for now.
			
			if not material_mapping_local:
				material_mapping_local[0] = 0
			
			len_material_mapping_local = len(material_mapping_local)
			
			i=-1
			for f in me.faces:
				if i==-1:
					i=0
					f_mat = f.mat
					if f_mat >= len_material_mapping_local:
						f_mat = 0
					
					file.write( '%s' % material_mapping_local[f_mat])
				else:
					if i==55:
						file.write('\n			 ')
						i=0
					
					file.write(',%s' % material_mapping_local[f_mat])
				i+=1
			
			file.write('\n		}')
		
		
		
		file.write('''
		Layer: 0 {
			Version: 100
			LayerElement:  {
				Type: "LayerElementNormal"
				TypedIndex: 0
			}''')
		
		if materials:
			file.write('''
			LayerElement:  {
				Type: "LayerElementMaterial"
				TypedIndex: 0
			}''')
			
		# Always write this
		if textures:
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
				
				if textures:
					
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
			Property: "UnitScaleFactor", "double", "",1
		}
	}
''')	
	file.write('}\n\n')
	
	file.write(\
'''; Object relations
;------------------------------------------------------------------

Relations:  {
''')

	file.write('\tModel: "Model::blend_root", "Null" {\n\t}\n')
	
	for obname, ob, me, mats, arm, armname in objects:
		file.write('\tModel: "Model::%s", "Mesh" {\n\t}\n' % obname)
	
	file.write('''	Model: "Model::Producer Perspective", "Camera" {
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
	}
''')
	
	for matname, mat in materials:
		file.write('\tMaterial: "Material::%s", "" {\n\t}\n' % matname)

	if textures:
		for texname, tex in textures:
			file.write('\tTexture: "Texture::%s", "TextureVideoClip" {\n\t}\n' % texname)
		for texname, tex in textures:
			file.write('\tVideo: "Video::%s", "Clip" {\n\t}\n' % texname)		

	file.write('}\n')
	file.write(\
'''
; Object connections
;------------------------------------------------------------------

Connections:  {
''')

	# write the fake root node
	file.write('\tConnect: "OO", "Model::blend_root", "Model::Scene"\n')
	
	for obname, ob, me, mats, arm, armname in objects:
		file.write('\tConnect: "OO", "Model::%s", "Model::blend_root"\n' % obname)
	
	for obname, ob, me, mats, arm, armname in objects:
		# Connect all materials to all objects, not good form but ok for now.
		for mat in mats:
			file.write('	Connect: "OO", "Material::%s", "Model::%s"\n' % (sane_matname(mat), obname))
	
	if textures:
		for obname, ob, me, mats, arm, armname in objects:
			for texname, tex in textures:
				file.write('\tConnect: "OO", "Texture::%s", "Model::%s"\n' % (texname, obname))
		
		for texname, tex in textures:
			file.write('\tConnect: "OO", "Video::%s", "Texture::%s"\n' % (texname, texname))
	
	file.write('}\n')
	
	
	# Clear mesh data Only when writing with modifiers applied
	#for obname, ob, me, mats, arm, armname in objects:
	#	me.verts = None


def write_footer(file, sce, world):
	
	tuple(world.hor)
	tuple(world.amb)
	
	has_mist = world.mode & 1
	
	mist_intense, mist_start, mist_end, mist_height = world.mist
	
	render = sce.getRenderingContext() # NEWAPY sce.render
	
	file.write(';Takes and animation section\n')
	file.write(';----------------------------------------------------\n')
	file.write('\n')
	file.write('Takes:  {\n')
	file.write('	Current: ""\n')
	file.write('}\n')
	file.write(';Version 5 settings\n')
	file.write(';------------------------------------------------------------------\n')
	file.write('\n')
	file.write('Version5:  {\n')
	file.write('\tAmbientRenderSettings:  {\n')
	file.write('\t\tVersion: 101\n')
	file.write('\t\tAmbientLightColor: %.1f,%.1f,%.1f,0\n' % tuple(world.amb))
	file.write('\t}\n')
	file.write('\tFogOptions:  {\n')
	file.write('\t\tFlogEnable: %i\n' % has_mist)
	file.write('\t\tFogMode: 0\n')
	file.write('\t\tFogDensity: %.3f\n' % mist_intense)
	file.write('\t\tFogStart: %.3f\n' % mist_start)
	file.write('\t\tFogEnd: %.3f\n' % mist_end)
	file.write('\t\tFogColor: %.1f,%.1f,%.1f,1\n' % tuple(world.hor))
	file.write('\t}\n')
	file.write('\tSettings:  {\n')
	file.write('\t\tFrameRate: "%i"\n' % render.fps)
	file.write('\t\tTimeFormat: 1\n')
	file.write('\t\tSnapOnFrames: 0\n')
	file.write('\t\tReferenceTimeIndex: -1\n')
	file.write('\t\tTimeLineStartTime: %i\n' % render.sFrame)
	file.write('\t\tTimeLineStopTime: %i\n' % render.eFrame)
	file.write('\t}\n')
	file.write('\tRendererSetting:  {\n')
	file.write('\t\tDefaultCamera: "Producer Perspective"\n')
	file.write('\t\tDefaultViewingMode: 0\n')
	file.write('\t}\n')
	file.write('}\n')

def write_ui(filename):
	if not BPyMessages.Warning_SaveOver(filename):
		return
	sce = Blender.Scene.GetCurrent() # NEWAPI bpy.data.scenes.active
	world = Blender.World.GetCurrent() # NEWAPI sce.world
	
	Blender.Window.WaitCursor(1)
	file = open(filename, 'w')
	write_header(file)
	write_scene(file, sce, world)
	write_footer(file, sce, world)
	Blender.Window.WaitCursor(0)

if __name__ == '__main__':
	Blender.Window.FileSelector(write_ui, 'Export FBX', Blender.sys.makename(ext='.fbx'))
