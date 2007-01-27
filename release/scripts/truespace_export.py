#!BPY

"""
Name: 'TrueSpace (.cob)...'
Blender: 232
Group: 'Export'
Tooltip: 'Export selected meshes to TrueSpace File Format (.cob)'
"""

__author__ = "Anthony D'Agostino (Scorpius)"
__url__ = ("blender", "elysiun",
"Author's homepage, http://www.redrival.com/scorpius")
__version__ = "Part of IOSuite 0.5"

__bpydoc__ = """\
This script exports meshes to TrueSpace file format.

TrueSpace is a commercial modeling and rendering application. The .cob
file format is composed of 'chunks,' is well defined, and easy to read and
write. It's very similar to LightWave's lwo format.

Usage:<br>
	Select meshes to be exported and run this script from "File->Export" menu.

Supported:<br>
	Vertex colors will be exported, if they are present.

Known issues:<br>
	Before exporting to .cob format, the mesh must have real-time UV
coordinates.  Press the FKEY to assign them.

Notes:<br>
	There are a few differences between how Blender & TrueSpace represent
their objects' transformation matrices. Blender simply uses a 4x4 matrix,
and trueSpace splits it into the following two fields.

	For the 'Local Axes' values: The x, y, and z-axis represent a simple
rotation matrix.  This is equivalent to Blender's object matrix before
it was combined with the object's scaling matrix. Dividing each value by
the appropriate scaling factor (and transposing at the same time)
produces the original rotation matrix.

	For the 'Current Position' values:	This is equivalent to Blender's
object matrix except that the last row is omitted and the xyz location
is used in the last column. Binary format uses a 4x3 matrix, ascii
format uses a 4x4 matrix.

For Cameras: The matrix here gets a little confusing, and I'm not sure of 
how to handle it.
"""

# $Id$
#
# +---------------------------------------------------------+
# | Copyright (c) 2001 Anthony D'Agostino                   |
# | http://www.redrival.com/scorpius                        |
# | scorpius@netzero.com                                    |
# | June 12, 2001                                           |
# | Read and write Caligari trueSpace File Format (*.cob)   |
# +---------------------------------------------------------+

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

import Blender, meshtools
import struct, cStringIO, time

# ==============================
# === Write trueSpace Format ===
# ==============================
def write(filename):
	start = time.clock()
	file = open(filename, "wb")
	objects = Blender.Object.GetSelected()

	write_header(file)

	G,P,V,U,M = 1000,2000,3000,4000,5000
	for obj_index, obj in enumerate(objects):
		objname = obj.name
		meshname = obj.getData(name_only=1)
		mesh = Blender.NMesh.GetRaw(meshname)
		
		if not mesh: continue

		grou = generate_grou('Group ' + `obj_index+1`)
		polh = generate_polh(objname, obj, mesh)
		if meshtools.has_vertex_colors(mesh): vcol = generate_vcol(mesh)
		unit = generate_unit()
		mat1 = generate_mat1(mesh)

		if obj_index == 0: X = 0

		write_chunk(file, "Grou", 0, 1, G, X, grou)
		write_chunk(file, "PolH", 0, 4, P, G, polh)
		if meshtools.has_vertex_colors(mesh) and vcol:
			write_chunk(file, "VCol", 1, 0, V, P, vcol)
		write_chunk(file, "Unit", 0, 1, U, P, unit)
		write_chunk(file, "Mat1", 0, 5, M, P, mat1)

		X = G
		G,P,V,U,M = map(lambda x: x+1, [G,P,V,U,M])

	write_chunk(file, "END ", 1, 0, 0, 0, '') # End Of File Chunk

	Blender.Window.DrawProgressBar(1.0, '')  # clear progressbar
	file.close()
	end = time.clock()
	seconds = " in %.2f %s" % (end-start, "seconds")
	message = "Successfully exported " + filename.split('\\')[-1].split('/')[-1] + seconds
	meshtools.print_boxed(message)

# =============================
# === Write COB File Header ===
# =============================
def write_header(file):
	file.write("Caligari V00.01BLH"+" "*13+"\n")

# ===================
# === Write Chunk ===
# ===================
def write_chunk(file, name, major, minor, chunk_id, parent_id, data):
	file.write(name)
	file.write(struct.pack("<2h", major, minor))
	file.write(struct.pack("<2l", chunk_id, parent_id))
	file.write(struct.pack("<1l", len(data)))
	file.write(data)

# ============================================
# === Generate PolH (Polygonal Data) Chunk ===
# ============================================
def generate_polh(objname, obj, mesh):
	data = cStringIO.StringIO()
	write_ObjectName(data, objname)
	write_LocalAxes(data, obj)
	write_CurrentPosition(data, obj)
	write_VertexList(data, mesh)
	uvcoords = write_UVCoordsList(data, mesh)
	write_FaceList(data, mesh, uvcoords)
	return data.getvalue()

# === Write Object Name ===
def write_ObjectName(data, objname):
	data.write(struct.pack("<h", 0))  # dupecount
	data.write(struct.pack("<h", len(objname)))
	data.write(objname)

# === Write Local Axes ===
def write_LocalAxes(data, obj):
	mat = obj.mat
	data.write(struct.pack("<fff", mat[3][0], mat[3][1], mat[3][2]))
	data.write(struct.pack("<fff", mat[0][0]/obj.SizeX, mat[1][0]/obj.SizeX, mat[2][0]/obj.SizeX))
	data.write(struct.pack("<fff", mat[0][1]/obj.SizeY, mat[1][1]/obj.SizeY, mat[2][1]/obj.SizeY))
	data.write(struct.pack("<fff", mat[0][2]/obj.SizeZ, mat[1][2]/obj.SizeZ, mat[2][2]/obj.SizeZ))

# === Write Current Position ===
def write_CurrentPosition(data, obj):
	mat = obj.mat
	data.write(struct.pack("<ffff", mat[0][0], mat[0][1], mat[0][2], mat[3][0]))
	data.write(struct.pack("<ffff", mat[1][0], mat[1][1], mat[1][2], mat[3][1]))
	data.write(struct.pack("<ffff", mat[2][0], mat[2][1], mat[2][2], mat[3][2]))

# === Write Vertex List ===
def write_VertexList(data, mesh):
	data.write(struct.pack("<l", len(mesh.verts)))
	for i, v in enumerate(mesh.verts):
		if not i%100 and meshtools.show_progress:
			Blender.Window.DrawProgressBar(float(i)/len(mesh.verts), "Writing Verts")
		x, y, z = v.co
		data.write(struct.pack("<fff", -y, x, z))

# === Write UV Vertex List ===
def write_UVCoordsList(data, mesh):
	if not mesh.hasFaceUV():
		data.write(struct.pack("<l", 1))
		data.write(struct.pack("<2f", 0,0))
		return {(0,0): 0}
		# === Default UV Coords (one image per face) ===
		# data.write(struct.pack("<l", 4))
		# data.write(struct.pack("<8f", 0,0, 0,1, 1,1, 1,0))
		# return {(0,0): 0, (0,1): 1, (1,1): 2, (1,0): 3}
		# === Default UV Coords (one image per face) ===

	# === collect, remove duplicates, add indices, and write the uv list ===
	uvdata = cStringIO.StringIO()
	uvcoords = {}
	uvidx = 0
	for i, f in enumerate(mesh.faces):
		if not i%100 and meshtools.show_progress:
			Blender.Window.DrawProgressBar(float(i)/len(mesh.faces), "Writing UV Coords")
		numfaceverts = len(f)
		for j in xrange(numfaceverts-1, -1, -1): 	# Reverse order
			u,v = f.uv[j]
			if not uvcoords.has_key((u,v)):
				uvcoords[(u,v)] = uvidx
				uvidx += 1
				uvdata.write(struct.pack("<ff", u,v))
	uvdata = uvdata.getvalue()

	numuvcoords = len(uvdata)/8
	data.write(struct.pack("<l", numuvcoords))
	data.write(uvdata)
	#print "Number of uvcoords:", numuvcoords, '=', len(uvcoords)
	return uvcoords

# === Write Face List ===
def write_FaceList(data, mesh, uvcoords):
	data.write(struct.pack("<l", len(mesh.faces)))
	for i in xrange(len(mesh.faces)):
		if not i%100 and meshtools.show_progress:
			Blender.Window.DrawProgressBar(float(i)/len(mesh.faces), "Writing Faces")
		numfaceverts = len(mesh.faces[i].v)
		data.write(struct.pack("<B", 0x10))         # Cull Back Faces Flag
		data.write(struct.pack("<h", numfaceverts))
		data.write(struct.pack("<h", 0))            # Material Index
		for j in xrange(numfaceverts-1, -1, -1): 	# Reverse order
			index = mesh.faces[i].v[j].index
			if mesh.hasFaceUV():
				uv = mesh.faces[i].uv[j]
				uvidx = uvcoords[uv]
			else:
				uvidx = 0
			data.write(struct.pack("<ll", index, uvidx))

# ===========================================
# === Generate VCol (Vertex Colors) Chunk ===
# ===========================================
def generate_vcol(mesh):
	data = cStringIO.StringIO()
	data.write(struct.pack("<l", len(mesh.faces)))
	uniquecolors = {}
	unique_alpha = {}
	for i in xrange(len(mesh.faces)):
		if not i%100 and meshtools.show_progress:
			Blender.Window.DrawProgressBar(float(i)/len(mesh.faces), "Writing Vertex Colors")
		numfaceverts = len(mesh.faces[i].v)
		data.write(struct.pack("<ll", i, numfaceverts))
		for j in xrange(numfaceverts-1, -1, -1): 	# Reverse order
			r = mesh.faces[i].col[j].r
			g = mesh.faces[i].col[j].g
			b = mesh.faces[i].col[j].b
			a = 100  # 100 is opaque in ts
			uniquecolors[(r,g,b)] = None
			unique_alpha[mesh.faces[i].col[j].a] = None
			data.write(struct.pack("<BBBB", r,g,b,a))

	#print "uniquecolors:", uniquecolors.keys()
	#print "unique_alpha:", unique_alpha.keys()
	if len(uniquecolors) == 1:
		return None
	else:
		return data.getvalue()

# ==================================
# === Generate Unit (Size) Chunk ===
# ==================================
def generate_unit():
	data = cStringIO.StringIO()
	data.write(struct.pack("<h", 2))
	return data.getvalue()

# ======================================
# === Generate Mat1 (Material) Chunk ===
# ======================================
def generate_mat1(mesh):
	
	def get_crufty_mesh_image():
		'''Crufty because it only uses 1 image
		'''
		if mesh.hasFaceUV():
			for f in me.faces:
				i = f.image
				if i:
					return i.filename
	
	data = cStringIO.StringIO()
	data.write(struct.pack("<h", 0))
	data.write(struct.pack("<ccB", "p", "a", 0))
	data.write(struct.pack("<fff", 1.0, 1.0, 1.0))  # rgb (0.0 - 1.0)
	data.write(struct.pack("<fffff", 1, 1, 0, 0, 1))
	
	tex_mapname = get_crufty_mesh_image()
	
	if tex_mapname:
		data.write("t:")
		data.write(struct.pack("<B", 0x00))
		data.write(struct.pack("<h", len(tex_mapname)))
		data.write(tex_mapname)
		data.write(struct.pack("<4f", 0,0, 1,1))
	return data.getvalue()

# ============================
# === Generate Group Chunk ===
# ============================
def generate_grou(name):
	data = cStringIO.StringIO()
	write_ObjectName(data, name)
	data.write(struct.pack("<12f", 0,0,0, 1,0,0, 0,1,0, 0,0,1))
	data.write(struct.pack("<12f", 1,0,0,0, 0,1,0,0, 0,0,1,0))
	return data.getvalue()

def fs_callback(filename):
	if not filename.lower().endswith('.cob'): filename += '.cob'
	write(filename)

if __name__ == '__main__':
	Blender.Window.FileSelector(fs_callback, "Export COB", Blender.sys.makename(ext='.cob'))

# === Matrix Differences between Blender & trueSpace ===
#
# For the 'Local Axes' values:
# The x, y, and z-axis represent a simple rotation matrix.
# This is equivalent to Blender's object matrix before it was
# combined with the object's scaling matrix.  Dividing each value
# by the appropriate scaling factor (and transposing at the same
# time) produces the original rotation matrix.
#
# For the 'Current Position' values:
# This is equivalent to Blender's object matrix except that the
# last row is omitted and the xyz location is used in the last
# column.  Binary format uses a 4x3 matrix, ascii format uses a 4x4
# matrix.
#
# For Cameras: The matrix is a little confusing.
