#!BPY

""" Registration info for Blender menus:
Name: 'DirectX(.x)...'
Blender: 240
Group: 'Export'
Submenu: 'Export all the scene' export
Submenu: 'Export selected obj' exportsel
Tip: 'Export to DirectX text file format format.'
"""
__author__ = "Arben (Ben) Omari"
__url__ = ("blender", "elysiun", "Author's site, http://www.omariben.too.it")
__version__ = "2.0"

__bpydoc__ = """\
This script exports a Blender mesh with armature to DirectX 8's text file
format.

Notes:<br>
    Check author's site or the elYsiun forum for a new beta version of the
DX exporter.
"""
# DirectXExporter.py version 2.0
# Copyright (C) 2006  Arben OMARI -- omariarben@everyday.com 
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# This script export meshes created with Blender in DirectX8 file format
# it exports meshes,armatures,materials,normals,texturecoords and animations

# Grab the latest version here :www.omariben.too.it

import Blender
from Blender import Types, Object, NMesh, Material,Armature
from Blender.Mathutils import *
import math

global mat_flip,index_list,space,bone_list,mat_dict
bone_list =[]
index_list = []
mat_dict = {}
space = 0
ANIM = 1
NORMAL = 1
TEXCOORDS = 1
TEXTURE = 1
mat_flip = Matrix([1, 0, 0, 0], [0, 1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1])
		

#***********************************************
#***********************************************
#                EXPORTER
#***********************************************
#***********************************************

class xExport:
	def __init__(self, filename):
		self.file = open(filename, "w")

#*********************************************************************************************************************************************
	#***********************************************
	#Select Scene objects
	#***********************************************
	def SelectObjs(self):
		global chld_obj
		print "exporting..."
		self.writeHeader()
		for obj in Object.Get():
			mesh = obj.getData()
			if type(mesh) == Types.NMeshType :
				chld_obj = obj.getParent()
				if chld_obj :
					dt_chld_obj = chld_obj.getData()
					if type(dt_chld_obj) == Types.ArmatureType :
						self.writeRootBone(chld_obj, obj)
					
				else :
					self.exportMesh(obj)
		self.file.write("AnimationSet {\n")
		for obj in Object.Get():
			mesh = obj.getData()
			if type(mesh) == Types.NMeshType :
				ip_list = obj.getIpo()
				if ip_list != None :
					self.writeAnimationObj(obj)
			elif type(mesh) == Types.ArmatureType :
				act_list = obj.getAction()
				if act_list != None :
					self.writeAnimation(obj)
				ip_list = obj.getIpo()
				if ip_list != None :
					self.writeAnimationObjArm(obj)
		self.file.write("}\n")
		self.writeEnd()
	#***********************************************
	#Export Mesh without Armature
	#***********************************************
	def exportMesh(self, obj):
		tex = []
		mesh = obj.getData()
		self.writeTextures(obj, tex)		
		self.writeMeshcoord(obj, mesh)
		self.writeMeshMaterialList(obj, mesh, tex)
		self.writeMeshNormals(obj, mesh)
		self.writeMeshTextureCoords(obj, mesh)
		self.file.write(" }\n")
		self.file.write("}\n")
		
					
	#***********************************************
	#Export the Selected Mesh
	#***********************************************
	def exportSelMesh(self):
		print "exporting ..."
		self.writeHeader()
		tex = []
		obj = Object.GetSelected()[0]
		mesh = obj.getData()
		if type(mesh) == Types.NMeshType :
			self.writeTextures(obj, tex)		
			self.writeMeshcoord(obj, mesh)
			self.writeMeshMaterialList(obj, mesh, tex)
			self.writeMeshNormals(obj, mesh)
			self.writeMeshTextureCoords(obj, mesh)
			self.file.write(" }\n")
			self.file.write("}\n")
			ip_list = obj.getIpo()
			if ip_list != None :
				self.file.write("AnimationSet {\n")
				self.writeAnimationObj(obj)
				self.file.write("}\n")
			print "exporting ..."
		else :
			print "The selected object is not a mesh"
		print "...finished"
	#***********************************************
	#Export Mesh with Armature
	#***********************************************
	def exportMeshArm(self,arm,arm_ob,ch_obj):
		tex = []
		mesh = ch_obj.getData()
		self.writeTextures(ch_obj, tex)		
		self.writeMeshcoordArm(ch_obj, mesh,arm_ob)
		self.writeMeshMaterialList(ch_obj, mesh, tex)
		self.writeMeshNormals(ch_obj, mesh)
		self.writeMeshTextureCoords(ch_obj, mesh)
		self.writeSkinWeights(arm,mesh)
		self.file.write(" }\n")
		self.file.write("}\n")
		
				
	#***********************************************
	#Export Root Bone
	#***********************************************
	def writeRootBone(self,am_ob,child_obj):
		global mat_flip,space,root_bon,mat_ob
		arms = am_ob.getData()
		self.writeArmFrames(mat_flip, "RootFrame")
		for bon in arms.bones.values():
			if bon.hasParent():
				pass
			else:
				root_bon = bon
		space += 1
		mat_rb = self.writeCombineMatrix(root_bon)
		mat_r = mat_rb #* am_ob.matrixLocal
		name_r = root_bon.name
		name_f = name_r.replace(".","")
		self.writeArmFrames(mat_r, name_f)
		bon_c = self.findChildrens(root_bon)
		self.writeChildren(bon_c)
		self.file.write("  }\n")
		self.exportMeshArm(arms,am_ob,child_obj)
		
	#***********************************************
	#Create Children structure
	#***********************************************
	def writeBon(self,bon):
		global space
		mat_r = self.writeCombineMatrix(bon)
		name_r = bon.name
		name_f = name_r.replace(".","")
		self.writeArmFrames(mat_r, name_f)
		
		
	def findChildrens(self,bon):
		bon_c = bon.children
		return bon_c
		
	
	def writeChildren(self,bon_c):
		global space,bone_list
		space += 1
		if bon_c:
			for bo in bon_c:
				if bo.name not in bone_list:
					self.writeBon(bo)
					bone_list.append(bo.name)
					bo_c = bo.children 
					self.writeChildren(bo_c)
					self.closeBrackets()
				
				
					
	def closeBrackets(self):
		global space
		space = space-1
		tab = "  "
		self.file.write("%s" % (tab * space))
		self.file.write("}\n")
		
		
			
	#***********************************************
	#Offset Matrix
	#***********************************************
	def writeMatrixOffset(self,bon):
		global  chld_obj
		Blender.Set('curframe', 1)
		pose = chld_obj.getPose()
		pos_b = pose.bones[bon.name]
		mat_b = pos_b.poseMatrix
		mat_b.invert()
		return mat_b

	
	#***********************************************
	#Combine Matrix
	#***********************************************
	def writeCombineMatrix(self,bon):
		global  chld_obj
		Blender.Set('curframe', 1)
		pose = chld_obj.getPose()
		pos_b = pose.bones[bon.name]
		mat_b = pos_b.poseMatrix
		if bon.hasParent():
			pare = bon.parent
			pos_p = pose.bones[pare.name]
			mat_p = pos_p.poseMatrix
			
		else:
			mat_p = Matrix([1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1])
		mat_p.invert()
		mat_f = mat_b * mat_p
		
		return mat_f
	#***********************************************
	#Combine Matrix
	#***********************************************
	def writeAnimCombineMatrix(self,bon,fre):
		global  chld_obj
		Blender.Set('curframe', fre)
		pose = chld_obj.getPose()
		pos_b = pose.bones[bon.name]
		mat_b = pos_b.poseMatrix
		if bon.hasParent():
			pare = bon.parent
			pos_p = pose.bones[pare.name]
			mat_p = pos_p.poseMatrix
			
		else:
			mat_p = Matrix([1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1])
		mat_p.invert()
		mat_f = mat_b * mat_p
		
		return mat_f


#*********************************************************************************************************************************************
	#***********************************************
	#Write SkinWeights
	#***********************************************
	def writeSkinWeights(self, arm, mesh):
		global index_list
		v_dict = {}
		Blender.Set('curframe',1)
		self.file.write("  XSkinMeshHeader {\n")
		max_infl = 0
		#this part supply the missing getVertexInfluences(index)
		for v in index_list:
				v_dict[v] = []
		for bo in arm.bones.values() :
			name = bo.name
			
			try :
				vertx_list = mesh.getVertsFromGroup(name,1)
				for vn in vertx_list:
					v_dict[vn[0]].append(name)
				#---------------------------------------------------
				for inde in vertx_list :
					vert_infl = v_dict[inde[0]]
					ln_infl = len(vert_infl)
					if ln_infl > max_infl :
						max_infl = ln_infl
				
			except:
				pass
		
		self.file.write("    %d; \n" % (max_infl))
		self.file.write("    %d; \n" % (max_infl * 3))
		self.file.write("    %d; \n" % (len(arm.bones.values())))
		self.file.write("  }\n")
		
		for bo in arm.bones.values() :
			bo_list = []
			weight_list = []
			name = bo.name 
			f_name = name.replace(".","")
			try :
				vert_list = mesh.getVertsFromGroup(name,1)
				le = 0
				for indx in vert_list:
					ver_infl = v_dict[indx[0]]
					len_infl = float(len(ver_infl))
					infl = 1 / len_infl
					i = -1
					for el in index_list :
						i += 1
						if el == indx[0] :
							le +=1
							bo_list.append(i)
							weight_list.append(infl)


				self.file.write("  SkinWeights {\n")
				self.file.write('    "%s"; \n' % (f_name))
				self.file.write('     %d; \n' % (le))
				count = 0
				for ind in bo_list :
					count += 1
					if count == len(bo_list):
						self.file.write("    %d; \n" % (ind))
					else :
						self.file.write("    %d, \n" % (ind))
				cou = 0
				for wegh in weight_list :
					cou += 1
					
					if cou == len(weight_list):
						self.file.write("    %f; \n" % (round(wegh,6)))
					else :
						self.file.write("    %f, \n" % (round(wegh,6)))

			
				matx = self.writeMatrixOffset(bo)
				self.writeOffsFrames(matx, name)
			except :
				pass
		self.file.write("  }\n")
		

	#***********************************************
	# Write Matrices
	#***********************************************
	def writeArmFrames(self, matx, name):
		global space
		tab = "  "
		self.file.write("%s" % (tab * space))
		self.file.write("Frame ")  
		self.file.write("%s {\n\n" % (name))
		self.file.write("%s" % (tab * space))
		self.file.write("  FrameTransformMatrix {\n")
		self.file.write("%s" % (tab * space))
		self.file.write("    %f,%f,%f,%f,\n" %
							(round(matx[0][0],4),round(matx[0][1],4),round(matx[0][2],4),round(matx[0][3],4)))
		self.file.write("%s" % (tab * space))
		self.file.write("    %f,%f,%f,%f,\n" %
							(round(matx[1][0],4),round(matx[1][1],4),round(matx[1][2],4),round(matx[1][3],4)))
		self.file.write("%s" % (tab * space))	
		self.file.write("    %f,%f,%f,%f,\n" %
							(round(matx[2][0],4),round(matx[2][1],4),round(matx[2][2],4),round(matx[2][3],4)))
		self.file.write("%s" % (tab * space))
		self.file.write("    %f,%f,%f,%f;;\n" %
							(round(matx[3][0],4),round(matx[3][1],4),round(matx[3][2],4),round(matx[3][3],6)))
		self.file.write("%s" % (tab * space))
		self.file.write("  }\n")
	
	#***********************************************
	# Write Matrices
	#***********************************************
	def writeOffsFrames(self, matx, name):
		space = 1
		tab = "  "
		self.file.write("%s" % (tab * space))
		self.file.write("    %f,%f,%f,%f,\n" %
							(round(matx[0][0],4),round(matx[0][1],4),round(matx[0][2],4),round(matx[0][3],4)))
		self.file.write("%s" % (tab * space))
		self.file.write("    %f,%f,%f,%f,\n" %
							(round(matx[1][0],4),round(matx[1][1],4),round(matx[1][2],4),round(matx[1][3],4)))
		self.file.write("%s" % (tab * space))	
		self.file.write("    %f,%f,%f,%f,\n" %
							(round(matx[2][0],4),round(matx[2][1],4),round(matx[2][2],4),round(matx[2][3],4)))
		self.file.write("%s" % (tab * space))
		self.file.write("    %f,%f,%f,%f;;\n" %
							(round(matx[3][0],4),round(matx[3][1],4),round(matx[3][2],4),round(matx[3][3],6)))
		self.file.write("%s" % (tab * space))
		self.file.write("  }\n")
	
	 
#*********************************************************************************************************************************************
	
	#***********************************************
	#HEADER
	#***********************************************  
	def writeHeader(self):
		self.file.write("xof 0303txt 0032\n\n\n")
		self.file.write("template VertexDuplicationIndices { \n\
 <b8d65549-d7c9-4995-89cf-53a9a8b031e3>\n\
 DWORD nIndices;\n\
 DWORD nOriginalVertices;\n\
 array DWORD indices[nIndices];\n\
}\n\
template XSkinMeshHeader {\n\
 <3cf169ce-ff7c-44ab-93c0-f78f62d172e2>\n\
 WORD nMaxSkinWeightsPerVertex;\n\
 WORD nMaxSkinWeightsPerFace;\n\
 WORD nBones;\n\
}\n\
template SkinWeights {\n\
 <6f0d123b-bad2-4167-a0d0-80224f25fabb>\n\
 STRING transformNodeName;\n\
 DWORD nWeights;\n\
 array DWORD vertexIndices[nWeights];\n\
 array float weights[nWeights];\n\
 Matrix4x4 matrixOffset;\n\
}\n\n")
		
	#***********************************************
	#CLOSE FILE
	#***********************************************
	def writeEnd(self):
		self.file.close()
		print "... finished"


	#***********************************************
	#EXPORT TEXTURES
	#***********************************************
	def writeTextures(self,name, tex):
		mesh = name.data
		for face in mesh.faces:
			if face.image and face.image.name not in tex:
				tex.append(face.image.name)
				


	#***********************************************
	#EXPORT MESH DATA with Armature
	#***********************************************
	def writeMeshcoordArm(self, name, meshEX,arm_ob):
		global index_list
		#ROTATION
		mat_arm = arm_ob.matrixWorld
		mat_ob = name.getMatrix('localspace')
		mat_ob.invert()
		mat = mat_arm * mat_ob
		mat.invert()
		name_f = name.name.replace(".","")
		self.writeArmFrames(mat, name_f)
		mesh = NMesh.GetRawFromObject(name.name)
		self.file.write("Mesh {\n")    
		numface=len(mesh.faces)
		#VERTICES NUMBER
		numvert = 0
		for face in mesh.faces:
			numvert = numvert + len(face.v)
		self.file.write("%s;\n" % (numvert))
		#VERTICES COORDINATES
		counter = 0
		for face in mesh.faces:
			counter += 1
			for n in range(len(face.v)):
				index_list.append(face.v[n].index)
				vec_vert = Vector([face.v[n].co[0], face.v[n].co[1], face.v[n].co[2], 1])
				f_vec_vert = vec_vert * mat
				self.file.write("%f; %f; %f;" % (round(f_vec_vert[0],4), round(f_vec_vert[1],4), round(f_vec_vert[2],4)))
				if counter == numface :
					if n == len(face.v)-1 :
						self.file.write(";\n")
					else :
						self.file.write(",\n")
				else :
					self.file.write(",\n")

		#FACES NUMBER 
		self.file.write("%s;\n" % (numface))  
		coun,counter = 0, 0
		for face in mesh.faces :
			coun += 1
			if coun == numface:
				if len(face.v) == 3:
					self.file.write("3; %s, %s, %s;;\n" % (counter, counter + 2, counter + 1))
					counter += 3
				elif len(face.v) == 4:
					self.file.write("4; %s, %s, %s, %s;;\n" % (counter, counter + 3, counter + 2, counter + 1))
					counter += 4
				elif len(face.v) < 3:
					print "WARNING:the mesh has faces with less then 3 vertices"
					print "        It my be not exported correctly."
			else:
				
				if len(face.v) == 3:
					self.file.write("3; %s, %s, %s;,\n" % (counter, counter + 2, counter + 1))
					counter += 3
				elif len(face.v) == 4:
					self.file.write("4; %s, %s, %s, %s;,\n" % (counter, counter + 3, counter + 2, counter + 1))
					counter += 4
				elif len(face.v) < 3:
					print "WARNING:the mesh has faces with less then 3 vertices"
					print "        It my be not exported correctly."

	#***********************************************
	#EXPORT MESH DATA without Armature
	#***********************************************
	def writeMeshcoord(self, name, mesh):
		global index_list
		#ROTATION
		mat_ob = mat_flip * name.matrixWorld
		name_f = name.name.replace(".","")
		self.writeArmFrames(mat_ob, name_f)

		self.file.write("Mesh {\n")    
		numface=len(mesh.faces)
		#VERTICES NUMBER
		numvert = 0
		for face in mesh.faces:
			numvert = numvert + len(face.v)
		self.file.write("%s;\n" % (numvert))
		#VERTICES COORDINATES
		counter = 0
		for face in mesh.faces:
			counter += 1
			for n in range(len(face.v)):
				index_list.append(face.v[n].index)
				self.file.write("%s; %s; %s;" % (face.v[n].co[0], face.v[n].co[1], face.v[n].co[2]))
				if counter == numface :
					if n == len(face.v)-1 :
						self.file.write(";\n")
					else :
						self.file.write(",\n")
				else :
					self.file.write(",\n")

		#FACES NUMBER 
		self.file.write("%s;\n" % (numface))  
		coun,counter = 0, 0
		for face in mesh.faces :
			coun += 1
			if coun == numface:
				if len(face.v) == 3:
					self.file.write("3; %s, %s, %s;;\n" % (counter, counter + 2, counter + 1))
					counter += 3
				elif len(face.v) == 4:
					self.file.write("4; %s, %s, %s, %s;;\n" % (counter, counter + 3, counter + 2, counter + 1))
					counter += 4
				elif len(face.v) < 3:
					print "WARNING:the mesh has faces with less then 3 vertices(edges and points)"
					print "        It my be not exported correctly."
			else:
				
				if len(face.v) == 3:
					self.file.write("3; %s, %s, %s;,\n" % (counter, counter + 2, counter + 1))
					counter += 3
				elif len(face.v) == 4:
					self.file.write("4; %s, %s, %s, %s;,\n" % (counter, counter + 3, counter + 2, counter + 1))
					counter += 4
				elif len(face.v) < 3:
					print "WARNING:the mesh has faces with less then 3 vertices(edges and points)\n"
					print "        It my be not exported correctly."
	
		
	#***********************************************
	#MESH MATERIAL LIST
	#***********************************************
	def writeMeshMaterialList(self, name, obj, tex):
		self.file.write("  MeshMaterialList {\n")
		#HOW MANY MATERIALS ARE USED
		count = 0
		for mat in Material.Get():
			count+=1
		self.file.write("    %s;\n" % (len(tex) + count))
		#HOW MANY FACES IT HAS
		numfaces=len(obj.faces)
		self.file.write("    %s;\n" % (numfaces))
		##MATERIALS INDEX FOR EVERY FACE
		counter = 0
		for face in obj.faces :
			counter += 1
			mater = face.materialIndex
			if counter == numfaces:
				if face.image and face.image.name in tex :
					self.file.write("    %s;;\n" % (tex.index(face.image.name) + count))
				else :
					self.file.write("    %s;;\n" % (mater))
			else :
				if face.image and face.image.name in tex :
					self.file.write("    %s,\n" % (tex.index(face.image.name) + count))
				else :
					self.file.write("    %s,\n" % (mater))
			
		##MATERIAL NAME
		for mat in Material.Get():
			self.file.write("  Material")
			name_m = mat.name
			name_f = name_m.replace(".","")
			self.file.write(" %s "% (name_f))
			self.file.write("{\n")
			self.file.write("    %s; %s; %s;" % (mat.R, mat.G, mat.B))
			self.file.write("%s;;\n" % (mat.alpha))
			self.file.write("    %s;\n" % (mat.spec))
			self.file.write("    %s; %s; %s;;\n" % (mat.specR, mat.specG, mat.specB))
			self.file.write("    0.0; 0.0; 0.0;;\n")
			self.file.write("  }\n") 
		
		for mat in tex:
			self.file.write("  Material Mat")
			self.file.write("%s "% (len(tex)))
			self.file.write("{\n")
			self.file.write("    1.0; 1.0; 1.0; 1.0;;\n")
			self.file.write("    1.0;\n")
			self.file.write("    1.0; 1.0; 1.0;;\n")
			self.file.write("    0.0; 0.0; 0.0;;\n")
			self.file.write("  TextureFilename {")
			self.file.write('    "%s" ;'% (mat))
			self.file.write("  }\n")
			self.file.write("  }\n") 
		self.file.write("    }\n")

	#***********************************************
	#MESH NORMALS
	#***********************************************
	def writeMeshNormals(self,name,mesh):
		self.file.write("  MeshNormals {\n")
		#VERTICES NUMBER
		numvert = 0
		for face in mesh.faces:
			numvert = numvert + len(face.v)
		self.file.write("%s;\n" % (numvert))
		numfaces=len(mesh.faces)
		
		#VERTICES NORMAL
		counter = 0
		for face in mesh.faces:
			counter += 1  
			for n in range(len(face.v)):
				self.file.write("    %s; %s; %s;" % ((round(face.v[n].no[0],6)),(round(face.v[n].no[1],6)),(round(face.v[n].no[2],6))))
				if counter == numfaces :
					if n == len(face.v)-1 :
						self.file.write(";\n")
					else :
						self.file.write(",\n")
				else :
					self.file.write(",\n")
		


		#FACES NUMBER 
		self.file.write("%s;\n" % (numfaces))  
		coun,counter = 0, 0
		for face in mesh.faces :
			coun += 1
			if coun == numfaces:
				if len(face.v) == 3:
					self.file.write("3; %s, %s, %s;;\n" % (counter, counter + 2, counter + 1))
					counter += 3
				else :
					self.file.write("4; %s, %s, %s, %s;;\n" % (counter, counter + 3, counter + 2, counter + 1))
					counter += 4
			else:
				
				if len(face.v) == 3:
					self.file.write("3; %s, %s, %s;,\n" % (counter, counter + 2, counter + 1))
					counter += 3
				else :
					self.file.write("4; %s, %s, %s, %s;,\n" % (counter, counter + 3, counter + 2, counter + 1))
					counter += 4
		self.file.write("}\n")

	#***********************************************
	#MESH TEXTURE COORDS
	#***********************************************
	def writeMeshTextureCoords(self, name, mesh):
		if mesh.hasFaceUV():
			self.file.write("MeshTextureCoords {\n")
			#VERTICES NUMBER
			numvert = 0
			for face in mesh.faces:
				numvert += len(face.v)
			self.file.write("%s;\n" % (numvert))
			#UV COORDS
			numfaces = len(mesh.faces)
			counter = -1
			co = 0
			for face in mesh.faces:
				counter += 1
				co += 1
				for n in range(len(face.v)):
					self.file.write("%s;%s;" % (mesh.faces[counter].uv[n][0], -mesh.faces[counter].uv[n][1]))
					if co == numfaces :
						if n == len(face.v) - 1 :
							self.file.write(";\n")
						else :
							self.file.write(",\n")
					else :
						self.file.write(",\n")

			self.file.write("}\n")
#***********************************************#***********************************************#***********************************************
	#***********************************************
	#FRAMES
	#***********************************************
	def writeFrames(self, matx):
		
		self.file.write("%s,%s,%s,%s," %
							(round(matx[0][0],4),round(matx[0][1],4),round(matx[0][2],4),round(matx[0][3],6)))
		self.file.write("%s,%s,%s,%s," %
							(round(matx[1][0],4),round(matx[1][1],4),round(matx[1][2],4),round(matx[1][3],6)))	
		self.file.write("%s,%s,%s,%s," %
							(round(matx[2][0],4),round(matx[2][1],4),round(matx[2][2],4),round(matx[2][3],6)))
		self.file.write("%s,%s,%s,%s;;" %
							(round(matx[3][0],4),round(matx[3][1],4),round(matx[3][2],4),round(matx[3][3],6)))
		
		
		
	
	
	#***********************************************
	#WRITE ANIMATION KEYS
	#***********************************************
	def writeAnimation(self,arm_ob):
		global mat_dict
		arm = arm_ob.getData()
		act_list = arm_ob.getAction()
		ip = act_list.getAllChannelIpos()
		for bon in arm.bones.values() :
			point_list = []
			name = bon.name
			name_f = name.replace(".", "")
			try :
				ip_bon_channel = ip[bon.name]
				ip_bon_name = ip_bon_channel.getName()
				
				ip_bon = Blender.Ipo.Get(ip_bon_name)
				poi = ip_bon.getCurves()
				
				for po in poi[3].getPoints():
					a = po.getPoints()
					point_list.append(int(a[0]))
				#point_list.pop(0) 
				
				self.file.write(" Animation { \n")
				self.file.write("  {%s}\n" %(name_f))
				self.file.write("  AnimationKey { \n")
				self.file.write("   4;\n")
				self.file.write("   %s; \n" % (len(point_list)))

				for fr in point_list:
					mat = self.writeAnimCombineMatrix(bon,fr)	
					
					self.file.write("   %s;" % (fr))
					self.file.write("16;")
				
					self.writeFrames(mat)
				
					if fr == point_list[len(point_list)-1]:
						self.file.write(";\n")
					else:
						self.file.write(",\n")
				self.file.write("   }\n")
				self.file.write(" }\n")
				self.file.write("\n")
			except:
				pass
		
		

	#***********************************************
	#WRITE ANIMATION KEYS
	#***********************************************
	def writeAnimationObj(self, obj):
		point_list = []
		ip = obj.getIpo()
		poi = ip.getCurves()
		for po in poi[0].getPoints():
			a = po.getPoints()
			point_list.append(int(a[0]))
		point_list.pop(0)
		
		self.file.write(" Animation {\n")
		self.file.write("  {")
		self.file.write("%s }\n" % (obj.name))
		self.file.write("   AnimationKey { \n")
		self.file.write("   4;\n")
		self.file.write("   %s; \n" % (len(point_list)+1))
		self.file.write("   %s;" % (1))
		self.file.write("16;")
		Blender.Set('curframe',1)
		mat = obj.matrixWorld * mat_flip
		self.writeFrames(mat)
		self.file.write(",\n")
		for fr in point_list:
			self.file.write("   %s;" % (fr))
			self.file.write("16;")
			Blender.Set('curframe',fr)
				
			mat_new = obj.matrixWorld * mat_flip
			self.writeFrames(mat_new)

			if fr == point_list[len(point_list)-1]:
				self.file.write(";\n")
			else:
				self.file.write(",\n")
		self.file.write("   }\n")
		self.file.write("  }\n")

	#***********************************************
	#WRITE ANIMATION KEYS
	#***********************************************
	def writeAnimationObjArm(self, obj):
		point_list = []
		ip = obj.getIpo()
		poi = ip.getCurves()
		for po in poi[0].getPoints():
			a = po.getPoints()
			point_list.append(int(a[0]))
		point_list.pop(0)
		
		self.file.write(" Animation {\n")
		self.file.write("  {RootFrame}\n" )
		self.file.write("   AnimationKey { \n")
		self.file.write("   4;\n")
		self.file.write("   %s; \n" % (len(point_list)+1))
		self.file.write("   %s;" % (1))
		self.file.write("16;")
		Blender.Set('curframe',1)
		mat = mat_flip * obj.getMatrix('worldspace')
		self.writeFrames(mat)
		self.file.write(",\n")
		for fr in point_list:
			self.file.write("   %s;" % (fr))
			self.file.write("16;")
			Blender.Set('curframe',fr)
				
			mat_new = mat_flip * obj.getMatrix('worldspace')
			self.writeFrames(mat_new)

			if fr == point_list[len(point_list)-1]:
				self.file.write(";\n")
			else:
				self.file.write(",\n")
		self.file.write("   }\n")
		self.file.write("  }\n")
		
#***********************************************#***********************************************#***********************************************



#***********************************************
# MAIN
#***********************************************

def my_callback(filename):
	if filename.find('.x', -2) <= 0: filename += '.x' 
	xexport = xExport(filename)
	xexport.SelectObjs()

def my_callback_sel(filename):
	if filename.find('.x', -2) <= 0: filename += '.x' 
	xexport = xExport(filename)
	xexport.exportSelMesh()

arg = __script__['arg']

if arg == 'exportsel':
	fname = Blender.sys.makename(ext = ".x")
	Blender.Window.FileSelector(my_callback_sel, "Export DirectX", fname)	
else:
	fname = Blender.sys.makename(ext = ".x")
	Blender.Window.FileSelector(my_callback, "Export DirectX", fname)	
	