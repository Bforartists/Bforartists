#!BPY

"""
Name: 'Nendo (.ndo)...'
Blender: 232
Group: 'Import'
Tooltip: 'Import Nendo Object File Format (.ndo)'
"""

__author__ = "Anthony D'Agostino (Scorpius)"
__url__ = ("blender", "elysiun",
"Author's homepage, http://www.redrival.com/scorpius")
__version__ = "Part of IOSuite 0.5"

__bpydoc__ = """\
This script imports Nendo files to Blender.

Nendo is (was) a commercial polygon modeler that has about half of the
features found in Wings. The .ndo file format is a simple, uncompressed,
memory dump of structures that represent the mesh objects, uv coords,
and image textures.

Usage:<br>
	Execute this script from the "File->Import" menu and choose a Nendo file
to open.

Supported:<br>
	Meshes only.

Missing:<br>
    Materials, UV Coordinates, and Vertex Color info will be ignored.

Known issues:<br>
	Triangulation of convex polygons works fine, and uses a very simple
fanning algorithm. Convex polygons (i.e., shaped like the letter "U")
require a different algorithm, and will be triagulated incorrectly.

Notes:<br>
	Last tested with Wings 3D 0.98.25 & Nendo 1.1.6. Some models cannot be
imported due to the fact that Nendo erroneously creates doubled back
edges during the course of modeling.
"""

# $Id$
#
# +---------------------------------------------------------+
# | Copyright (c) 2001 Anthony D'Agostino                   |
# | http://www.redrival.com/scorpius                        |
# | scorpius@netzero.com                                    |
# | September 25, 2001                                      |
# | Read and write Nendo File Format (*.nendo)              |
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
try:
	import struct, os
except:
	struct= None

# =============================
# === Read Nendo 1.x Format ===
# =============================
def read(filename):
	start = Blender.sys.time()
	
	scn= Blender.Scene.GetCurrent()
	for obj in scn.getChildren():
		obj.sel= 0
		
	file = open(filename, "rb")
	version, numobjs = read_header(file)

	for object in xrange(numobjs):
		good, = struct.unpack(">B",  file.read(1))
		if not good: continue	# an empty object
		objname = read_object_flags(file)
		edge_table = read_edge_table(file, version)
		face_table = read_face_table(file)
		vert_table = read_vert_table(file)
		uv = read_uv(file)
		verts = make_verts(vert_table)
		faces = make_faces(edge_table)
		meshtools.create_mesh(verts, faces, objname)

	Blender.Window.DrawProgressBar(1.0, "Done")    # clear progressbar
	file.close()
	end = Blender.sys.time()
	seconds = " in %.2f %s" % (end-start, "seconds")
	message = "Successfully imported " + filename.split(Blender.sys.sep)[-1] + seconds
	message += " (%s)" % version.title()
	meshtools.print_boxed(message)

# =======================
# === Read The Header ===
# =======================
def read_header(file):
	version, = struct.unpack(">9s", file.read(9))
	misc,	 = struct.unpack(">H",  file.read(2))
	numobjs, = struct.unpack(">B",  file.read(1))
	if (version != "nendo 1.0") and (version != "nendo 1.1"):
		meshtools.print_boxed(file.name, "is not a Nendo file")
		return
	return version, numobjs

# =========================
# === Read Object Flags ===
# =========================
def read_object_flags(file):
	namelen, = struct.unpack(">H",  file.read(2))
	objname  = file.read(namelen)
	visible, = struct.unpack(">B", file.read(1))
	sensity, = struct.unpack(">B", file.read(1))
	other,	 = struct.unpack(">H", file.read(2))    # or 2 more flags?
	misc	 = struct.unpack(">18f", file.read(72))
	return objname

# =======================
# === Read Edge Table ===
# =======================
def read_edge_table(file, version):
	numedges, = struct.unpack(">H", file.read(2))
	edge_table = {}
	for i in xrange(numedges):
		if not i%100 and meshtools.show_progress:
			Blender.Window.DrawProgressBar(float(i)/numedges, "Reading Edge Table")
		edge = struct.unpack(">8H", file.read(16))
		if version == "nendo 1.1":
			hard, = struct.unpack(">B",  file.read(1))  # edge hardness flag
		color = struct.unpack(">8B", file.read(8))
		edge_table[i] = edge
	return edge_table

# =======================
# === Read Face Table ===
# =======================
def read_face_table(file):
	numfaces, = struct.unpack(">H", file.read(2))
	face_table = {}
	for i in xrange(numfaces):
		if not i%100 and meshtools.show_progress:
			Blender.Window.DrawProgressBar(float(i)/numfaces, "Reading Face Table")
		face_table[i] = struct.unpack(">H", file.read(2))[0]
	return face_table

# =======================
# === Read Vert Table ===
# =======================
def read_vert_table(file):
	numverts, = struct.unpack(">H", file.read(2))
	vert_table = []
	for i in xrange(numverts):
		if not i%100 and meshtools.show_progress:
			Blender.Window.DrawProgressBar(float(i)/numverts, "Reading Vertex Table")
		w, x, y, z = struct.unpack(">H3f", file.read(14))
		vert_table.append((w,(x, y, z)))
	return vert_table

# ====================
# === Read Texture ===
# ====================
def read_uv(file):
	numuvs, = struct.unpack(">H", file.read(2))
	uvlist	= struct.unpack(">"+`numuvs`+"H", file.read(numuvs*2))
	numfacesT, = struct.unpack(">H", file.read(2))
	facesT = struct.unpack(">"+`numfacesT`+"H", file.read(numfacesT*2))
	textureflag, = struct.unpack(">B", file.read(1))
	if textureflag:
		xres, yres = struct.unpack(">2H", file.read(4))
		print "%ix%i" % (xres, yres)
		pixel = 0
		while pixel < (xres*yres):
			if not pixel%100 and meshtools.show_progress:
				Blender.Window.DrawProgressBar(float(pixel)/xres*yres, "Reading Texture")
			count, = struct.unpack(">B", file.read(1))
			rgb = file.read(3)
			pixel = pixel+count
	return numuvs

# ==================
# === Make Verts ===
# ==================
def make_verts(vert_table):
	matrix = [ # Rotate 90*x and Scale 0.1
	[0.1, 0.0, 0.0, 0.0],
	[0.0, 0.0, 0.1, 0.0],
	[0.0,-0.1, 0.0, 0.0],
	[0.0, 0.0, 0.0, 1.0]]
	verts = []
	for i in xrange(len(vert_table)):
		vertex = vert_table[i][1]
		vertex = meshtools.apply_transform(vertex, matrix)
		verts.append(vertex)
	return verts

# =======================
# === Make Face Table ===
# =======================
def make_face_table(edge_table): # For Nendo
	face_table = {}
	for i in xrange(len(edge_table)):
		Lf = edge_table[i][2]
		Rf = edge_table[i][3]
		face_table[Lf] = face_table[Rf] = i
	return face_table

# =======================
# === Make Vert Table ===
# =======================
def make_vert_table(edge_table): # For Nendo
	vert_table = {}
	for i in xrange(len(edge_table)):
		Sv = edge_table[i][1]
		Ev = edge_table[i][0]
		vert_table[Sv] = vert_table[Ev]= i
	return vert_table

# ==================
# === Make Faces ===
# ==================
def make_faces(edge_table): # For Nendo
	face_table = make_face_table(edge_table)
	faces=[]
	#for i in range(len(face_table)):
	for i in face_table.iterkeys(): # avoids a whole class of errors
		face_verts = []
		current_edge = face_table[i]
		while(1):
			if i == edge_table[current_edge][3]:
				next_edge = edge_table[current_edge][5] # Right successor edge
				next_vert = edge_table[current_edge][1]
			else:
				next_edge = edge_table[current_edge][4] # Left successor edge
				next_vert = edge_table[current_edge][0]
			face_verts.append(next_vert)
			current_edge = next_edge
			if current_edge == face_table[i]: break
		face_verts.reverse() # Flip all face normals
		faces.append(face_verts)
	return faces


def main():
	if not struct:
		Blender.Draw.PupMenu('This importer requires a full python install')
		return
	
	Blender.Window.FileSelector(read, 'Import Nendo', '*.ndo')

if __name__=='__main__':
	main()

