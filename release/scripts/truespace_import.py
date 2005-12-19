#!BPY

"""
Name: 'TrueSpace (.cob)...'
Blender: 232
Group: 'Import'
Tooltip: 'Import TrueSpace Object File Format (.cob)'
"""

__author__ = "Anthony D'Agostino (Scorpius)"
__url__ = ("blender", "elysiun",
"Author's homepage, http://www.redrival.com/scorpius")
__version__ = "Part of IOSuite 0.5"

__bpydoc__ = """\
This script imports TrueSpace files to Blender

TrueSpace is a commercial modeling and rendering application. The .cob
file format is composed of 'chunks,' is well defined, and easy to read and
write. It's very similar to LightWave's lwo format.

Usage:<br>
	Execute this script from the "File->Import" menu and choose a TrueSpace
file to open.

Supported:<br>
	Meshes only. Supports UV Coordinates. COB files in ascii format can't be
read.

Missing:<br>
	Materials, and Vertex Color info will be ignored.

Known issues:<br>
	Triangulation of convex polygons works fine, and uses a very simple
fanning algorithm. Convex polygons (i.e., shaped like the letter "U")
require a different algorithm, and will be triagulated incorrectly.

Notes:<br>
	There are a few differences between how Blender & TrueSpace represent
their objects' transformation matrices. Blender simply uses a 4x4 matrix,
and trueSpace splits it into the following two fields.

	For the 'Local Axes' values: The x, y, and z-axis represent a simple
rotation matrix.  This is equivalent to Blender's object matrix before
it was combined with the object's scaling matrix. Dividing each value by
the appropriate scaling factor (and transposing at the same time)
produces the original rotation matrix.

	For the 'Current Position' values:  This is equivalent to Blender's
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
import struct, chunk, os, cStringIO, time

# =======================
# === COB Chunk Class ===
# =======================
class CobChunk(chunk.Chunk):
	def __init__(self, file, align = 0, bigendian = 0, inclheader = 0): #$ COB
		self.closed = 0
		self.align = align	# whether to align to word (2-byte) boundaries
		if bigendian:
			strflag = '>'
		else:
			strflag = '<'
		self.file = file
		self.chunkname = file.read(4)
		if len(self.chunkname) < 4:
			raise EOFError
		self.major_ver, = struct.unpack(strflag+'h', file.read(2))      #$ COB
		self.minor_ver, = struct.unpack(strflag+'h', file.read(2))      #$ COB
		self.chunk_id,	= struct.unpack(strflag+'l', file.read(4))      #$ COB
		self.parent_id, = struct.unpack(strflag+'l', file.read(4))      #$ COB
		try:
			self.chunksize = struct.unpack(strflag+'l', file.read(4))[0]
		except struct.error:
			raise EOFError
		if inclheader:
			self.chunksize = self.chunksize - 20						#$ COB
		self.size_read = 0
		try:
			self.offset = self.file.tell()
		except:
			self.seekable = 0
		else:
			self.seekable = 1

# ============================
# === Read COB File Header ===
# ============================
def read_header(file):
	magic,	 = struct.unpack("<9s", file.read(9))
	version, = struct.unpack("<6s", file.read(6))
	format,  = struct.unpack("<1c", file.read(1))
	endian,  = struct.unpack("<2s", file.read(2))
	misc,	 = struct.unpack("13s", file.read(13))
	newline, = struct.unpack("<1B", file.read(1))
	return format

# ========================================
# === Read PolH (Polygonal Data) Chunk ===
# ========================================
def read_polh(chunk):
	data = cStringIO.StringIO(chunk.read())
	oname = read_ObjectName(data)
	local = read_LocalAxes(data)
	crpos = read_CurrentPosition(data)
	verts = read_VertexList(data)
	uvcoords = read_UVCoords(data)
	faces, facesuv = read_FaceList(data, chunk)
	return verts, faces, oname, facesuv, uvcoords

# === Read Object Name ===
def read_ObjectName(data):
	dupecount, namelen = struct.unpack("<hh", data.read(4))
	objname = data.read(namelen)
	if objname == '': objname = 'NoName'
	if dupecount > 0: objname = objname + ', ' + `dupecount`
	return objname

# === Read Local Axes ===
def read_LocalAxes(data):
	location = struct.unpack("<fff", data.read(12))
	rotation_matrix=[]
	for i in range(3):
		row = struct.unpack("<fff", data.read(12))
		#print "% f % f % f" % row
		rotation_matrix.append(list(row))
	#print
	rotation_matrix = meshtools.transpose(rotation_matrix)

# === Read Current Position ===
def read_CurrentPosition(data):
	transformation_matrix=[]
	for i in range(3):
		row = struct.unpack("<ffff", data.read(16))
		#print "% f % f % f % f" % row
		transformation_matrix.append(list(row))
	#print

# === Read Vertex List ===
def read_VertexList(data):
	verts = []
	numverts, = struct.unpack("<l", data.read(4))
	for i in range(numverts):
		if not i%100 and meshtools.show_progress:
			Blender.Window.DrawProgressBar(float(i)/numverts, "Reading Verts")
		x, y, z = struct.unpack("<fff", data.read(12))
		verts.append((y, -x, z))
	return verts

# === Read UV Vertex List ===
def read_UVCoords(data):
	uvcoords = []
	numuvcoords, = struct.unpack("<l", data.read(4))
	for i in range(numuvcoords):
		if not i%100 and meshtools.show_progress:
			Blender.Window.DrawProgressBar(float(i)/numuvcoords, "Reading UV Coords")
		uv = struct.unpack("<ff", data.read(8))
		uvcoords.append(uv)

	#print "num uvcoords:", len(uvcoords)
	#for i in range(len(uvcoords)): print "%.4f, %.4f" % uvcoords[i]
	return uvcoords

# === Read Face List ===
def read_FaceList(data, chunk):
	faces = []				   ; facesuv = []
	numfaces, = struct.unpack("<l", data.read(4))
	for i in range(numfaces):
		if not i%100 and meshtools.show_progress:
			Blender.Window.DrawProgressBar(float(i)/numfaces, "Reading Faces")

		face_flags, numfaceverts = struct.unpack("<Bh", data.read(3))

		if (face_flags & 0x08) == 0x08:
			print "face #" + `i-1` + " contains a hole."
			pass
		else:
			data.read(2)  # Material Index

		facev = []			   ; faceuv = []
		for j in range(numfaceverts):
			index, uvidx = struct.unpack("<ll", data.read(8))
			facev.append(index); faceuv.append(uvidx)
		facev.reverse() 	   ; faceuv.reverse()
		faces.append(facev)    ; facesuv.append(faceuv)

	if chunk.minor_ver == 6:
		DrawFlags, RadiosityQuality = struct.unpack("<lh", data.read(6))
	if chunk.minor_ver == 8:
		DrawFlags, = struct.unpack("<l", data.read(4))

	return faces			   , facesuv

# =============================
# === Read trueSpace Format ===
# =============================
def read(filename):
	start = time.clock()
	file = open(filename, "rb")

	# === COB header ===
	if read_header(file) == 'A':
		print "Can't read ASCII format"
		return

	while 1:
		try:
			cobchunk = CobChunk(file)
		except EOFError:
			break
		if cobchunk.chunkname == "PolH":
			verts, faces, objname, facesuv, uvcoords = read_polh(cobchunk)
			meshtools.create_mesh(verts, faces, objname, facesuv, uvcoords)

			'''
			object = Blender.Object.GetSelected()
			obj = Blender.Object.Get(objname)
			obj.loc = location
			obj.rot = meshtools.mat2euler(rotation_matrix)
			obj.size = (transformation_matrix[0][0]/rotation_matrix[0][0],
						transformation_matrix[1][1]/rotation_matrix[1][1],
						transformation_matrix[2][2]/rotation_matrix[2][2])

			'''
		else:
			cobchunk.skip()

	Blender.Window.DrawProgressBar(1.0, '')  # clear progressbar
	file.close()
	end = time.clock()
	seconds = " in %.2f %s" % (end-start, "seconds")
	message = "Successfully imported " + os.path.basename(filename) + seconds
	meshtools.print_boxed(message)
	#print "objname :", objname
	#print "numverts:", len(verts)
	#print "numfaces:", len(faces)

def fs_callback(filename):
	read(filename)

Blender.Window.FileSelector(fs_callback, "Import COB")

