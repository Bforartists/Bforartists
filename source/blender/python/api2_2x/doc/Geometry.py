# Blender.Geometry module and its subtypes

"""
The Blender.Geometry submodule.

Geometry
========

This new module provides access to a geometry function.
"""

def PolyFill(polylines):
	"""
	Takes a list of polylines and calculates triangles that would fill in the polylines.
	Multiple lines can be used to make holes inside a polyline, or fill in 2 seperate lines at once.
	@type polylines: List of lists containing vectors, each representing a closed polyline.
	@rtype: list
	@return: a list if tuples each a tuple of 3 ints representing a triangle indexing the points given.
	@note: 2D Vectors will have an assumed Z axis of zero, 4D Vectors W axis is ignored.
	@note: The order of points in a polyline effect the direction returned triangles face, reverse the order of a polyline to flip the normal of returned faces.

	I{B{Example:}}

	The example below creates 2 polylines and fills them in with faces, then makes a mesh in the current scene::
		import Blender
		Vector= Blender.Mathutils.Vector

		# Outline of 5 points
		polyline1= [Vector(-2.0, 1.0, 1.0), Vector(-1.0, 2.0, 1.0), Vector(1.0, 2.0, 1.0), Vector(1.0, -1.0, 1.0), Vector(-1.0, -1.0, 1.0)]
		polyline2= [Vector(-1, 1, 1.0), Vector(0, 1, 1.0), Vector(0, 0, 1.0), Vector(-1.0, 0.0, 1.0)]
		fill= Blender.Geometry.PolyFill([polyline1, polyline2])

		# Make a new mesh and add the truangles into it
		me= Blender.Mesh.New()
		me.verts.extend(polyline1)
		me.verts.extend(polyline2)
		me.faces.extend(fill) # Add the faces, they reference the verts in polyline 1 and 2

		scn = Blender.Scene.GetCurrent()
		ob = scn.objects.new(me)
		Blender.Redraw()
	"""

def LineIntersect2D(vec1, vec2, vec3, vec4):
	"""
	Takes 2 lines vec1, vec2 for the 2 points of the first line and vec2, vec3 for the 2 points of the second line.
	@rtype: Vector
	@return: a 2D Vector for the intersection or None where there is no intersection.
	"""

def BoxPack2D(boxlist):
	"""
	Takes a list of 2D boxes and packs them into a square.
	Each box in boxlist must be a list of at least 4 items - [x,y,w,h], after running this script,
	the X and Y values in each box will be moved to packed, non overlapping locations.
	
	Example::

		# Make 500 random boxes, pack them and make a mesh from it
		from Blender import Geometry, Scene, Mesh
		import random
		boxes = []
		for i in xrange(500):
			boxes.append( [0,0, random.random()+0.1, random.random()+0.1] )
		boxsize = Geometry.BoxPack2D(boxes)
		print 'BoxSize', boxsize
		me = Mesh.New()
		for x in boxes:
			me.verts.extend([(x[0],x[1], 0), (x[0],x[1]+x[3], 0), (x[0]+x[2],x[1]+x[3], 0), (x[0]+x[2],x[1], 0) ])
			v1= me.verts[-1]
			v2= me.verts[-2]
			v3= me.verts[-3]
			v4= me.verts[-4]
			me.faces.extend([(v1,v2,v3,v4)])
		scn = Scene.GetCurrent()
		scn.objects.new(me)
	
	@note: Each boxlist item can be longer then 4, the extra items are ignored and stay untouched.
	@rtype: tuple
	@return: a tuple pair - (width, height) of all the packed boxes.
	"""
	