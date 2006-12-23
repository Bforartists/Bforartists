#!BPY
"""
Name: 'Follow Active (quads)'
Blender: 242
Group: 'UVCalculation'
Tooltip: 'Follow from active quads.'
"""
__author__ = "Campbell Barton"
__url__ = ("blender", "elysiun")
__version__ = "1.0 2006/02/07"

__bpydoc__ = """\
This script sets the UV mapping and image of selected faces from adjacent unselected faces.

for full docs see...
http://mediawiki.blender.org/index.php/Scripts/Manual/UV_Calculate/Follow_active_quads
"""

# ***** BEGIN GPL LICENSE BLOCK *****
#
# Script copyright (C) Campbell J Barton
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


from Blender import *


def extend():
	scn = Scene.GetCurrent()
	ob = scn.objects.active
	
	# print ob, ob.type
	if ob == None or ob.type != 'Mesh':
		Draw.PupMenu('ERROR: No mesh object.')
		return
	
	me = ob.getData(mesh=1)
	me_verts = me.verts
	
	# 0:normal extend, 1:edge length
	EXTEND_MODE = Draw.PupMenu("Use Face Area%t|Loop Average%x2|Face Average%x1|None%x0")
	if EXTEND_MODE == -1:
		return
	
	Window.WaitCursor(1)
	
	edge_average_lengths = {}
	
	OTHER_INDEX = 2,3,0,1
	FAST_INDICIES = 0,2,1,3 # order is faster
	def extend_uvs(face_source, face_target, edge_key):
		'''
		Takes 2 faces,
		Projects its extends its UV coords onto the face next to it.
		Both faces must share an edge.
		'''
		
		def face_edge_vs(vi):
			# assunme a quad
			return [(vi[0], vi[1]), (vi[1], vi[2]), (vi[2], vi[3]), (vi[3], vi[0])]
		
		uvs_source = face_source.uv
		uvs_target = face_target.uv
		
		vidx_source = [v.index for v in face_source] 
		vidx_target = [v.index for v in face_target]
		
		# vertex index is the key, uv is the value
		uvs_vhash_source = dict( [ (vindex, uvs_source[i]) for i, vindex in enumerate(vidx_source)] )
		uvs_vhash_target = dict( [ (vindex, uvs_target[i]) for i, vindex in enumerate(vidx_target)] )
		
		edge_idxs_source = face_edge_vs(vidx_source)
		edge_idxs_target = face_edge_vs(vidx_target)
		
		source_matching_edge = -1
		target_matching_edge = -1
		
		edge_key_swap = edge_key[1], edge_key[0]
		
		try:	source_matching_edge = edge_idxs_source.index(edge_key)
		except:	source_matching_edge = edge_idxs_source.index(edge_key_swap)
		try:	target_matching_edge = edge_idxs_target.index(edge_key)
		except:	target_matching_edge = edge_idxs_target.index(edge_key_swap)
		

		
		edgepair_inner_source = edge_idxs_source[source_matching_edge]
		edgepair_inner_target = edge_idxs_target[target_matching_edge]
		edgepair_outer_source = edge_idxs_source[OTHER_INDEX[source_matching_edge]]
		edgepair_outer_target = edge_idxs_target[OTHER_INDEX[target_matching_edge]]
		
		if edge_idxs_source[source_matching_edge] == edge_idxs_target[target_matching_edge]:
			iA= 0; iB= 1 # Flipped, most common
		else: # The normals of these faces must be different
			iA= 1; iB= 0

		
		# Set the target UV's touching source face, no tricky calc needed,
		uvs_vhash_target[edgepair_inner_target[0]][:] = uvs_vhash_source[edgepair_inner_source[iA]]
		uvs_vhash_target[edgepair_inner_target[1]][:] = uvs_vhash_source[edgepair_inner_source[iB]]


		# Set the 2 UV's on the target face that are not touching
		# for this we need to do basic expaning on the source faces UV's
		if EXTEND_MODE == 1 or EXTEND_MODE == 2:
			
			try: # divide by zero is possible
				'''
				measure the length of each face from the middle of each edge to the opposite
				allong the axis we are copying, use this
				'''
				
				if EXTEND_MODE == 1:
				# Average lengths with edge_average_lengths
					
					factor =\
					(\
					 (me_verts[edgepair_outer_target[iB]].co + me_verts[edgepair_outer_target[iA]].co)-\
					 (me_verts[edgepair_inner_target[iA]].co + me_verts[edgepair_inner_target[iB]].co)\
					).length / (\
					 (me_verts[edgepair_outer_source[iB]].co + me_verts[edgepair_outer_source[iA]].co)-\
					 (me_verts[edgepair_inner_source[iA]].co + me_verts[edgepair_inner_source[iB]].co)\
					).length
				else: # EXTEND_MODE == 2
					i1a= edgepair_outer_target[iB]
					i2a= edgepair_inner_target[iA]
					if i1a>i2a: i1a, i2a = i2a, i1a
					
					i1b= edgepair_outer_source[iB]
					i2b= edgepair_inner_source[iA]
					if i1b>i2b: i1b, i2b = i2b, i1b
					# print edge_average_lengths
					factor = edge_average_lengths[i1a, i2a][0] / edge_average_lengths[i1b, i2b][0]
					
					
					
					
			except:
				# Div By Zero?
				factor = 1.0
			
			uvs_vhash_target[edgepair_outer_target[iB]][:] = uvs_vhash_source[edgepair_inner_source[0]]  +factor * (uvs_vhash_source[edgepair_inner_source[0]] - uvs_vhash_source[edgepair_outer_source[1]])
			uvs_vhash_target[edgepair_outer_target[iA]][:] = uvs_vhash_source[edgepair_inner_source[1]]  +factor * (uvs_vhash_source[edgepair_inner_source[1]] - uvs_vhash_source[edgepair_outer_source[0]])
		
			
			
			
			
			
		
		else:
			# same as above but with no factor
			uvs_vhash_target[edgepair_outer_target[iB]][:] = uvs_vhash_source[edgepair_inner_source[0]] + (uvs_vhash_source[edgepair_inner_source[0]] - uvs_vhash_source[edgepair_outer_source[1]])
			uvs_vhash_target[edgepair_outer_target[iA]][:] = uvs_vhash_source[edgepair_inner_source[1]] + (uvs_vhash_source[edgepair_inner_source[1]] - uvs_vhash_source[edgepair_outer_source[0]])
	
	if not me.faceUV:
		Draw.PupMenu('ERROR: Mesh has no face UV coords.')
		return

	SEL_FLAG = Mesh.FaceFlags['SELECT']
	
	face_act = 	me.activeFace
	if face_act == -1:
		Draw.PupMenu('ERROR: No active face')
		return
	
	
	face_sel= [f for f in me.faces if len(f) == 4 if f.flag & SEL_FLAG]
	
	face_act_local_index = -1
	for i, f in enumerate(face_sel):
		if f.index == face_act:
			face_act_local_index = i
			break
	
	if face_act_local_index == -1:
		Draw.PupMenu('ERROR: Active face not selected')
		return
	
	
	
	# Modes
	# 0 unsearched
	# 1:mapped, use search from this face.
	# 2:all siblings have been searched. dont search again.
	face_modes = [0] * len(face_sel)
	face_modes[face_act_local_index] = 1 # extend UV's from this face.
	
	
	# Edge connectivty
	edge_faces = {}
	for i, f in enumerate(face_sel):
		for edkey in f.edge_keys:
			try:	edge_faces[edkey].append(i)
			except:	edge_faces[edkey] = [i]
	
	SEAM = Mesh.EdgeFlags.SEAM
	
	if EXTEND_MODE == 2:
		# Generate grid average edge lengths per edgeloop!
		# this means that for each face loop, the edges on it will have new fake, everaged lengths
		# WARNING! - This is not that optimal!!!... but neither is it horrid - Campbell
		
		seam_keys = {} # should be a set
		for ed in me.edges:
			if ed.flag & SEAM:
				seam_keys[ed.key] = None
		
		
		# edge_average_lengths = {} # ed.key:length
		# #edge_average_lengths.fromkeys(edge_faces)
		# Why dosnt fromkeys work?
		for edkey in edge_faces.keys():
			edge_average_lengths[edkey] = None
		
		# EDGROUP is the current edge loop index, assigned to all edges
		EDGROUP = [0]
		EDGROUPS = [EDGROUP] # 
		while 1:
			
			start_edge = None
			
			# get the first unused edge
			for edkey, value in edge_average_lengths.iteritems():
				if value == None:
					start_edge = edkey
					break
			
			if start_edge == None:
				break
			
			edge_average_lengths[start_edge] = EDGROUP
			
			one_more_edge = True
			while one_more_edge:
				one_more_edge = False
				for f in face_sel:
					edge_keys = f.edge_keys
					for i, edkey in enumerate(edge_keys):
						if edge_average_lengths[edkey] == EDGROUP:
							# if the opposite edge has not been assigned then assign it
							if (not seam_keys.has_key(edge_keys[OTHER_INDEX[i]])) and\
							edge_average_lengths[edge_keys[OTHER_INDEX[i]]] == None:
								
								edge_average_lengths[edge_keys[OTHER_INDEX[i]]] = EDGROUP
								one_more_edge = True
			
			# new list
			EDGROUP = [EDGROUP[0]+1]
			EDGROUPS.append(EDGROUP)
		
		edge_average_length_groups = [0.0] * len(EDGROUPS)
		edge_average_count = [0] * len(EDGROUPS)
		
		edge_lengths = dict([(ed.key, ed.length) for ed in me.edges])
		
		# Now we have the edge loops, average the lengths.
		for edkey, edgroup in edge_average_lengths.iteritems():
			edge_average_length_groups[edgroup[0]] += edge_lengths[edkey]
			edge_average_count[edgroup[0]] += 1
		
		for i in xrange(len(edge_average_count)):
			if edge_average_count[i]:
				# so edge_average_lengths now referenced the length rather then the group.
				EDGROUPS[i][0] = edge_average_length_groups[i] / edge_average_count[i]
		
		# Finished averaging lengths
		# edge_average_lengths can be used.
		
	
	
	# remove seams, so we dont map accross seams.
	for ed in me.edges:
		if ed.flag & SEAM:
			# remove the edge pair if we can
			try:	del edge_faces[ed.key]
			except:	pass
	# Done finding seams
	
	
	# face connectivity - faces around each face
	# only store a list of indicies for each face.
	face_faces = [[] for i in xrange(len(face_sel))]
	
	for edge_key, faces in edge_faces.iteritems():
		if len(faces) == 2: # Only do edges with 2 face users for now
			face_faces[faces[0]].append((faces[1], edge_key))
			face_faces[faces[1]].append((faces[0], edge_key))
	
	
	# Now we know what face is connected to what other face, map them by connectivity
	ok = True
	while ok:
		ok = False
		for i in xrange(len(face_sel)):
			if face_modes[i] == 1: # searchable
				for f_sibling, edge_key in face_faces[i]:
					if face_modes[f_sibling] == 0:
						face_modes[f_sibling] = 1 # mapped and search from.
						extend_uvs(face_sel[i], face_sel[f_sibling], edge_key)
						face_modes[i] = 1 # we can map from this one now.
						ok= True # keep searching
				
				face_modes[i] = 2 # dont search again
	me.update()
	Window.RedrawAll()
	Window.WaitCursor(0)

if __name__ == '__main__':
	#t = sys.time()
	extend()
	#print  sys.time() - t
	