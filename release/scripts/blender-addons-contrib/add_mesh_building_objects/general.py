# Stairbuilder - General
#
# General is an object for creating meshes given the verts and faces.
#   Stair Type (typ):
#       - id1 = Freestanding staircase
#       - id2 = Housed-open staircase
#       - id3 = Box staircase
#       - id4 = Circular staircase
# 
# Paul "BrikBot" Marshall
# Created: September 19, 2011
# Last Modified: January 29, 2011
# Homepage (blog): http://post.darkarsenic.com/
#                       //blog.darkarsenic.com/
#
# Coded in IDLE, tested in Blender 2.61.
# Search for "@todo" to quickly find sections that need work.
#
# ##### BEGIN GPL LICENSE BLOCK #####
#
#  Stairbuilder is for quick stair generation.
#  Copyright (C) 2011  Paul Marshall
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
from bpy_extras import object_utils
from math import atan
from mathutils import Vector

class General:
    def __init__(self,rise,run,N):
        self.stop=float(N)*Vector([run,0,rise])
        self.slope=rise/run
        self.angle=atan(self.slope)
        #identical quads for all objects except stringer
        self.faces=[[0,1,3,2],[0,1,5,4],[0,2,6,4],[4,5,7,6],[2,3,7,6],[1,3,7,5]]

    def Make_mesh(self, verts, faces, name):        
        # Create new mesh
        mesh = bpy.data.meshes.new(name)

        # Make a mesh from a list of verts/edges/faces.
        mesh.from_pydata(verts, [], faces)

        # Set mesh to use auto smoothing:
        mesh.use_auto_smooth = True

        # Update mesh geometry after adding stuff.
        mesh.update()

        return object_utils.object_data_add(bpy.context, mesh, operator=None)
