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
bl_info = {
    "name": "PolyRedux",
    "author": "Campbell J Barton - updated by Gert De Roost",
    "version": (2, 0, 4),
    "blender": (2, 63, 0),
    "location": "View3D > Tools",
    "description": "predictable mesh simplifaction maintaining face loops",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Mesh"}


if "bpy" in locals():
    import imp

import bpy
import bmesh
import time


class PolyRedux(bpy.types.Operator):
	bl_idname = "mesh.polyredux"
	bl_label = "PolyRedux"
	bl_description = "predictable mesh simplifaction maintaining face loops"
	bl_options = {"REGISTER", "UNDO"}
	

	@classmethod
	def poll(cls, context):
		obj = context.active_object
		return (obj and obj.type == 'MESH')

	def invoke(self, context, event):
		
		scn = bpy.context.scene
		
		self.save_global_undo = bpy.context.user_preferences.edit.use_global_undo
		bpy.context.user_preferences.edit.use_global_undo = False
		
		do_polyredux(self)
		
		return {'FINISHED'}

class redux_help(bpy.types.Operator):
	bl_idname = 'help.polyredux'
	bl_label = ''

	def draw(self, context):
		layout = self.layout
		layout.label('To use:')
		layout.label('Make a selection of verts or polygons to reduce.')
		layout.label('works on whole mesh or selected')
		layout.label('To Help:')
		layout.label('Single operation, no parameters.')
	
	def execute(self, context):
		return {'FINISHED'}

	def invoke(self, context, event):
		return context.window_manager.invoke_popup(self, width = 300)
'''
def panel_func(self, context):
	
	scn = bpy.context.scene
	self.layout.label(text="PolyRedux:")
	self.layout.operator("mesh.polyredux", text="Poly Redux")


def register():
	bpy.utils.register_module(__name__)
	bpy.types.VIEW3D_PT_tools_meshedit.append(panel_func)


def unregister():
	bpy.utils.unregister_module(__name__)
	bpy.types.VIEW3D_PT_tools_meshedit.remove(panel_func)


if __name__ == "__main__":
	register()


'''

def my_mesh_util():
	bm_verts = bm.verts
	
	vert_faces = [ [] for v in bm_verts]
	vert_faces_corner = [ [] for v in bm_verts]
	
	
	# Ignore topology where there are not 2 faces connected to an edge.
	edge_count = {}
	for f in bm.faces:
		for edge in f.edges:
			edkey = (edge.verts[0].index, edge.verts[1].index)
			try:
				edge_count[edkey] += 1
			except:
				edge_count[edkey]  = 1
				
	for edkey, count in edge_count.items():
		
		# Ignore verts that connect to edges with more than 2 faces.
		if count != 2:
			vert_faces[edkey[0]] = None
			vert_faces[edkey[1]] = None
	# Done
	
	
	
	def faces_set_verts(face_ls):
		unique_verts = set()
		for f in face_ls:
			for v in f.verts:
				unique_verts.add(v.index)
		return unique_verts
	
	for f in bm.faces:
		for corner, v in enumerate(f.verts):
			i = v.index
			if vert_faces[i] != None:
				vert_faces[i].append(f)
				vert_faces_corner[i].append(corner)
	
	grid_data_ls = []
	
	for vi, face_ls in enumerate(vert_faces):
		if face_ls != None:
			if len(face_ls) == 4:
				if face_ls[0].select and face_ls[1].select and face_ls[2].select and face_ls[3].select:					
					# Support triangles also
					unique_vert_count = len(faces_set_verts(face_ls))
					quads = 0
					for f in face_ls:
						if len(f.verts) ==4:
							quads += 1
					if unique_vert_count==5+quads: # yay we have a grid
						grid_data_ls.append( (vi, face_ls) )
			
			elif len(face_ls) == 3:
				if face_ls[0].select and face_ls[1].select and face_ls[2].select:
					unique_vert_count = len(faces_set_verts(face_ls))
					if unique_vert_count==4: # yay we have 3 triangles to make into a bigger triangle
						grid_data_ls.append( (vi, face_ls) )
				
	
	
	# Now sort out which grid faces to use
	
	
	# This list will be used for items we can convert, vertex is key, faces are values
	grid_data_dict = {}
	
	if not grid_data_ls:
		print ("doing nothing")
		return
	
	# quick lookup for the opposing corner of a qiad
	quad_diag_mapping = 2,3,0,1
	
	verts_used = [0] * len(bm_verts) # 0 == untouched, 1==should touch, 2==touched
	verts_used[grid_data_ls[0][0]] = 1 # start touching 1!
	
	# From the corner vert, get the 2 edges that are not the corner or its opposing vert, this edge will make a new face
	quad_edge_mapping = (1,3), (2,0), (1,3), (0,2) # hi-low, low-hi order is intended
	tri_edge_mapping = (1,2), (0,2), (0,1)
	
	done_somthing = True
	while done_somthing:
		done_somthing = False
		grid_data_ls_index = -1
		
		for vi, face_ls in grid_data_ls:
			grid_data_ls_index += 1
			if len(face_ls) == 3:
				grid_data_dict[bm.verts[vi]] = face_ls
				grid_data_ls.pop( grid_data_ls_index )
				break
			elif len(face_ls) == 4:
				# print vi
				if verts_used[vi] == 1:
					verts_used[vi] = 2 # dont look at this again.
					done_somthing = True
					
					grid_data_dict[bm.verts[vi]] = face_ls
					
					# Tag all faces verts as used
					
					for i, f in enumerate(face_ls):
						# i == face index on vert, needed to recall which corner were on.
						v_corner = vert_faces_corner[vi][i]
						fv =f.verts
						
						if len(f.verts) == 4:
							v_other = quad_diag_mapping[v_corner]
							# get the 2 other corners
							corner1, corner2 = quad_edge_mapping[v_corner]
							if verts_used[fv[v_other].index] == 0:
								verts_used[fv[v_other].index] = 1 # TAG for touching!
						else:
							corner1, corner2 = tri_edge_mapping[v_corner]
						
						verts_used[fv[corner1].index] = 2 # Dont use these, they are 
						verts_used[fv[corner2].index] = 2
						
						
					# remove this since we have used it.
					grid_data_ls.pop( grid_data_ls_index )
					
					break
		
		if done_somthing == False:
			# See if there are any that have not even been tagged, (probably on a different island), then tag them.
			
			for vi, face_ls in grid_data_ls:
				if verts_used[vi] == 0:
					verts_used[vi] = 1
					done_somthing = True
					break
	
	
	# Now we have all the areas we will fill, calculate corner triangles we need to fill in.
	new_faces = []
	quad_del_vt_map = (1,2,3), (0,2,3), (0,1,3), (0,1,2)
	for v, face_ls in grid_data_dict.items():
		for i, f in enumerate(face_ls):
			if len(f.verts) == 4:
				# i == face index on vert, needed to recall which corner were on.
				v_corner = vert_faces_corner[v.index][i]
				v_other = quad_diag_mapping[v_corner]
				fv =f.verts
				
				#print verts_used[fv[v_other].index]
				#if verts_used[fv[v_other].index] != 2: # DOSNT WORK ALWAYS
				
				if 1: # THIS IS LAzY - some of these faces will be removed after adding.
					# Ok we are removing half of this face, add the other half
					
					# This is probably slower
					# new_faces.append( [fv[ii].index for ii in (0,1,2,3) if ii != v_corner ] )
					
					# do this instead
					new_faces.append( (fv[quad_del_vt_map[v_corner][0]].index, fv[quad_del_vt_map[v_corner][1]].index, fv[quad_del_vt_map[v_corner][2]].index) )
	
	del grid_data_ls
	
	
	# me.sel = 0
	def faceCombine4(vi, face_ls):
		edges = []
		
		for i, f in enumerate(face_ls):
			fv = f.verts
			v_corner = vert_faces_corner[vi][i]
			if len(f.verts)==4:	ed = quad_edge_mapping[v_corner]
			else:			ed = tri_edge_mapping[v_corner]
			
			edges.append( [fv[ed[0]].index, fv[ed[1]].index] )
		
		# get the face from the edges 
		face = edges.pop()
		while len(face) != 4:
			# print len(edges), edges, face
			for ed_idx, ed in enumerate(edges):
				if face[-1] == ed[0] and (ed[1] != face[0]):
					face.append(ed[1])
				elif face[-1] == ed[1] and (ed[0] != face[0]):
					face.append(ed[0])
				else:
					continue
				
				edges.pop(ed_idx) # we used the edge alredy
				break
		
		return face	
	
	for v, face_ls in grid_data_dict.items():
		vi = v.index
		if len(face_ls) == 4:
			new_faces.append( faceCombine4(vi, face_ls) )
			#pass
		if len(face_ls) == 3: # 3 triangles
			face = list(faces_set_verts(face_ls))
			face.remove(vi)
			new_faces.append( face )
			
	
	# Now remove verts surounded by 3 triangles
	

		
	# print new_edges
	# me.faces.extend(new_faces, ignoreDups=True)
	
	'''
	faces_remove = []
	for vi, face_ls in grid_data_dict.items():
		faces_remove.extend(face_ls)
	'''
	
	orig_facelen = len(bm.faces)
	
	orig_faces = list(bm.faces)
	made_faces = []
	bpy.ops.mesh.select_all(action="DESELECT")
	for vertidxs in new_faces:
		verts = []
		for idx in vertidxs:
			verts.append(bm.verts[idx])
		verts.append(verts[0])
		for idx in range(len(verts) - 1):
			verts.append(verts[0])
			v1 = verts[idx]
			v2 = verts[idx + 1]
			if bm.edges.get((v1, v2)) == None:
				for f in v1.link_faces:
					if f in v2.link_faces:
						bmesh.utils.face_split(f, v1, v2)
						break

	for vert in grid_data_dict.keys():
		bmesh.utils.face_join(vert.link_faces[:])
	
	# me.faces.delete(1, faces_remove)
	
	bm.normal_update()

def do_polyredux(self):
	
	global bm, me
	
	# Gets the current scene, there can be many scenes in 1 blend file.
	sce = bpy.context.scene
	
	# Get the active object, there can only ever be 1
	# and the active object is always the editmode object.
	mode = "EDIT"
	if bpy.context.mode == "OBJECT":
		mode = "OBJECT"
		bpy.ops.object.editmode_toggle()
	ob_act = bpy.context.active_object
	if not ob_act or ob_act.type != 'MESH':
		return 
	me = ob_act.data
	bm = bmesh.from_edit_mesh(me)
	
	t = time.time()
	
	# Run the mesh editing function
	my_mesh_util()
	me.update(calc_edges=True, calc_tessface=True)
	bm.free()
	
	# Restore editmode if it was enabled
	if mode == "OBJECT":
		bpy.ops.object.editmode_toggle()
	else:
		bpy.ops.object.editmode_toggle()
		bpy.ops.object.editmode_toggle()
	
	# Timing the script is a good way to be aware on any speed hits when scripting
	print ('My Script finished in %.2f seconds' % (time.time()-t))
	
	

