import bpy, mathutils, math
from mathutils import geometry

# Get a matrix for the selected faces that you can use to do local transforms
def get_selection_matrix(faces=False):
	
	me = bpy.context.active_object.data
	
	if not faces:
		faces = get_selected_faces()
	
	yVec = mathutils.Vector()
	zVec = mathutils.Vector()
	
	# Ok so we have a basic matrix, but lets base it more on the mesh!
	for f in faces:
			
		v1 = me.vertices[f.vertices[0]].co
		v2 = me.vertices[f.vertices[1]].co
		edge = v2-v1
		
		yVec += edge
		
		if len(f.vertices) == 4:
			v1 = me.vertices[f.vertices[2]].co
			v2 = me.vertices[f.vertices[3]].co
			edge = v1-v2
			
			yVec += edge
		
		zVec += mathutils.Vector(f.normal)
					
	if not yVec.length:
		quat = zVec.to_track_quat('-Z', 'Y')
		tMat = quat.to_matrix()
		yVec = tMat[1]
		yVec = yVec.normalized()
	else:
		yVec = yVec.normalized()
	zVec = zVec.normalized()
	
	# Rotate yVec so it's 90 degrees to zVec
	cross =yVec.cross(zVec)
	vec = float(yVec.angle(zVec) - math.radians(90))
	mat = mathutils.Matrix.Rotation(vec, 3, cross)
	yVec =  (mat * yVec)
	
	xVec = yVec.cross(zVec)
	
	xVec = xVec.normalized()
	
	nMat = mathutils.Matrix((xVec, yVec, zVec))
	
	return nMat



# Get the selection radius (minimum distance of an outer edge to the centre)
def get_selection_radius():

	ob = bpy.context.active_object

	radius = 0.0
	
	# no use continueing if nothing is selected
	if contains_selected_item(ob.data.polygons):
	
		# Find the center of the selection
		cent = mathutils.Vector()
		nr = 0
		nonVerts = []
		selVerts = []
		for f in ob.data.polygons:
			if f.select:
				nr += 1
				cent += f.center
			else:
				nonVerts.extend(f.vertices)
				
		cent /= nr
		
		chk = 0
		
		# Now that we know the center.. we can figure out how close the nearest point on an outer edge is
		for e in get_selected_edges():
		
			nonSection = [v for v in e.vertices if v in nonVerts]
			if len(nonSection):
			
				v0 = ob.data.vertices[e.vertices[0]].co
				v1 = ob.data.vertices[e.vertices[1]].co
				
				# If there's more than 1 vert of this edge on the outside... we need the edge length to be long enough too!
				if len(nonSection) > 1:
					edge = v0 - v1
					edgeRad = edge.length * 0.5
					
					if edgeRad < radius or not chk:
						radius = edgeRad
						chk += 1
				
				int = geometry.intersect_point_line(cent, v0, v1)
				
				rad = cent - int[0]
				l = rad.length
				
				if l < radius or not chk:
					radius = l
					chk += 1
					
	return radius
	
	
	
# Get the average length of the outer edges of the current selection
def get_shortest_outer_edge_length():

	ob = bpy.context.active_object

	min = False
	me = ob.data
	
	delVerts = []
	for f in me.faces:
		if not f.select:
			delVerts.extend(f.vertices)
	selEdges = [e.vertices for e in me.edges if e.select]

	if len(selEdges) and len(delVerts):
		
		for eVerts in selEdges:
			
			v0 = eVerts[0]
			v1 = eVerts[1]
			
			if v0 in delVerts and v1 in delVerts:
				ln = (me.vertices[v0].co - me.vertices[v1].co).length
				if min is False or (ln > 0.0 and ln < min):
					min = ln
						
	return min


# Get the average length of the outer edges of the current selection
def get_average_outer_edge_length():

	ob = bpy.context.active_object

	ave = 0.0
	me = ob.data
	
	delFaces = [f.vertices for f  in me.polygons if not f.select]
	selEdges = [e.vertices for e in me.edges if e.select]

	if len(selEdges) and len(delFaces):
	
		number = 0
		
		for eVerts in selEdges:
			
			v0 = eVerts[0]
			v1 = eVerts[1]
			
			for fVerts in delFaces:
				if v0 in fVerts and v1 in fVerts:
					number += 1
					ave += (me.vertices[v0].co - me.vertices[v1].co).length
					break
						
		if number:
			ave /= number
			
	return ave


	
# Get the selected (or deselected items)
def get_selected(type='vertices',invert=False):
	
	mesh = bpy.context.active_object.data
	
	if type == 'vertices':
		items = mesh.vertices
	elif type == 'edges':
		items = mesh.edges
	else:
		items = mesh.polygons
		
	if invert:
		L = [i for i in items if not i.select]
	else:
		L = [i for i in items if i.select]
	return L
	
	
	
# See if the mesh has something selected
def has_selected(type='vertices',invert=False):
	
	mesh = bpy.context.active_object.data
	
	if type == 'vertices':
		items = mesh.vertices
	elif type == 'edges':
		items = mesh.edges
	else:
		items = mesh.polygons
		
	for i in items:
		if not invert and i.select:
			return True
		elif invert and not i.select:
			return True
			
	return False
		
		

# Get all the selected vertices (mode is selected or deselected)
def get_selected_vertices(mode='selected'):

	vertices = bpy.context.active_object.data.vertices

	if mode == 'deselected':
		L = [v for v in vertices if not v.select]
	else:
		L = [v for v in vertices if v.select]
	return L
	
	
	
# Get all the selected edges (mode is selected or deselected)
def get_selected_edges(mode='selected'):

	edges = bpy.context.active_object.data.edges

	if mode == 'deselected':
		L = [e for e in edges if not e.select]
	else:
		L = [e for e in edges if e.select]
	return L


	
# Get all the selected faces (mode is selected or deselected)
def get_selected_faces(mode='selected'):
	
	polygons = bpy.context.active_object.data.polygons
	
	if mode == 'deselected':
		L = [f for f in polygons if not f.select]
	else:
		L = [f for f in polygons if f.select]
	return L
	
	
	
# See if there is at least one selected item in 'items'
def contains_selected_item(items):

	for item in items:
		if item.select:
			return True
				
	return False
	





	
	
		