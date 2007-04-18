import Blender
from Blender.Window import EditMode, GetCursorPos, GetViewQuat
import bpy

def add_mesh_simple(name, verts, edges, faces):
	'''
	Adds a mesh from verts, edges and faces
	
	name  - new object/mesh name
	verts - list of 3d vectors
	edges - list of int pairs
	faces - list of int triplets/quads
	'''
	
	scn = bpy.data.scenes.active
	if scn.lib: return
	ob_act = scn.objects.active
	
	cursor = GetCursorPos()
	try:	quat = Blender.Mathutils.Quaternion(GetViewQuat())
	except:	quat = None
	
	# Exist editmode for non mesh types
	if ob_act and ob_act.type != 'Mesh' and EditMode():
		EditMode(0)
	
	# We are in mesh editmode
	if EditMode():
		
		# Add to existing mesh
		# must exit editmode to modify mesh
		EditMode(0)
		
		me = ob_act.getData(mesh=1)
		me.sel = False
		
		vert_offset = len(me.verts)
		edge_offset = len(me.edges)
		face_offset = len(me.faces)
		
		# transform the verts
		txmat = Blender.Mathutils.TranslationMatrix(Blender.Mathutils.Vector(cursor))
		if quat:
			mat = quat.toMatrix()
			mat.invert()
			mat.resize4x4()
			txmat = mat * txmat
		
		txmat = txmat * ob_act.matrixWorld.copy().invert()
		
		
		me.verts.extend(verts)
		# Transform the verts by the cursor and view rotation
		me.transform(txmat, selected_only=True)
		
		if vert_offset:
			me.edges.extend([[i+vert_offset for i in e] for e in edges])
			me.faces.extend([[i+vert_offset for i in f] for f in faces])
		else:
			# Mesh with no data, unlikely
			me.edges.extend(edges)
			me.faces.extend(faces)
		
		EditMode(1)
		
	else:
		
		# Object mode add new
		
		me = bpy.data.meshes.new(name)
		me.verts.extend(verts)
		me.edges.extend(edges)
		me.faces.extend(faces)
		me.sel = True
		
		# Object creation and location
		scn.objects.selected = []
		ob_act = scn.objects.new(me, name)
		scn.objects.active = ob_act
		
		if quat:
			mat = quat.toMatrix()
			mat.invert()
			mat.resize4x4()
			ob_act.setMatrix(mat)
		
		ob_act.loc = cursor
		
		EditMode(1)


def write_mesh_script(filepath, me):
	'''
	filepath - path to py file
	me - mesh to write
	'''
	
	name = me.name
	file = open(filepath, 'w')
	
	file.write('#!BPY\n')
	file.write('"""\n')
	file.write('Name: \'%s\'\n' % name)
	file.write('Blender: 243\n')
	file.write('Group: \'AddMesh\'\n')
	file.write('"""\n\n')
	file.write('import BPyAddMesh\n')
	file.write('from Blender.Mathutils import Vector\n\n')
	
	file.write('verts = [\\\n')
	for v in me.verts:
		file.write('Vector(%f,%f,%f),\\\n' % tuple(v.co))
	file.write(']\n')
	
	file.write('edges = []\n') # TODO, write loose edges
	
	file.write('faces = [\\\n')
	for f in me.faces:
		file.write('%s,\\\n' % str(tuple([v.index for v in f])))
	file.write(']\n')
	
	file.write('BPyAddMesh.add_mesh_simple("%s", verts, edges, faces)\n' % name)

# The script below can make a file from a mesh with teh above function...
'''
#!BPY
"""
Name: 'Mesh as AddMesh Script'
Blender: 242
Group: 'Mesh'
Tip: ''
"""
import BPyAddMesh
reload(BPyAddMesh)

import bpy

def main():
	# Add error checking
	scn = bpy.data.scenes.active
	ob = scn.objects.active
	me = ob.getData(mesh=1)
	
	BPyAddMesh.write_mesh_script('/test.py', me)

main()
'''
